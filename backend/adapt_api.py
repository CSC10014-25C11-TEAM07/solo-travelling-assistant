import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, model_validator

import itinerary_store as store
from adapt_store import apply_days
from itinerary_api import APIError, DraftInput, current_user, owned, validate_plan

router = APIRouter(prefix="/api/v1")


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["ACCEPT", "REJECT"]
    option_id: str | None = None

    @model_validator(mode="after")
    def option_matches_decision(self):
        if self.decision == "ACCEPT" and not self.option_id:
            raise ValueError("ACCEPT requires option_id")
        if self.decision == "REJECT" and self.option_id is not None:
            raise ValueError("REJECT cannot select an option")
        return self


def validate_preservation(db, itinerary, days):
    if len(days) != len(itinerary["days"]):
        raise ValueError("Days must be preserved")
    all_ids = set()
    for original_day, day in zip(itinerary["days"], days):
        for key in ("day_id", "itinerary_id", "date", "day_number", "end_deadline"):
            if day[key] != original_day[key]:
                raise ValueError("Day metadata changed")
        old = {activity["activity_id"]: activity for activity in original_day["activities"]}
        new = {activity["activity_id"]: activity for activity in day["activities"]}
        if len(new) != len(day["activities"]) or all_ids.intersection(new):
            raise ValueError("Duplicate activity ID")
        all_ids.update(new)
        if not old.keys() <= new.keys():
            raise ValueError("Activity history was removed")
        for activity_id, activity in new.items():
            if activity["day_id"] != day["day_id"]:
                raise ValueError("Activity moved to another day")
            if set(activity) != set(original_day["activities"][0]):
                raise ValueError("Invalid activity fields")
            if type(activity["is_optional"]) is not bool:
                raise ValueError("Invalid optional flag")
            if activity_id in old:
                before = old[activity_id]
                if before["status"] != "PENDING" and activity != before:
                    raise ValueError("Completed or historical activity changed")
                if activity["status"] not in ("PENDING", "DROPPED", "REPLACED", before["status"]):
                    raise ValueError("Invalid status transition")
                for key in ("type", "name", "place_id", "is_optional", "replaces_activity_id", "completed_at"):
                    if activity[key] != before[key]:
                        raise ValueError("Original activity metadata changed")
                if activity["status"] == "DROPPED" and (not before["is_optional"] or before["type"] != "VISIT"):
                    raise ValueError("Mandatory activity dropped")
                if activity["status"] == "REPLACED" and before["type"] != "VISIT":
                    raise ValueError("Only visits may be replaced")
            else:
                if activity["status"] != "PENDING" or activity["completed_at"] is not None:
                    raise ValueError("New activity must be pending")
                if db.execute("SELECT 1 FROM activities WHERE activity_id = ?", (activity_id,)).fetchone():
                    raise ValueError("Activity ID belongs to another day")
                replaced = activity["replaces_activity_id"]
                if replaced is not None:
                    if replaced not in old or new[replaced]["status"] != "REPLACED":
                        raise ValueError("Invalid replacement")
        for activity in new.values():
            if activity["status"] == "REPLACED" and activity["activity_id"] in old and old[activity["activity_id"]]["status"] == "PENDING":
                replacements = [item for item in new.values() if item["replaces_activity_id"] == activity["activity_id"]]
                if len(replacements) != 1 or replacements[0]["type"] != "VISIT":
                    raise ValueError("A replaced visit requires one replacement")
    active_days = [
        {**day, "activities": [a for a in day["activities"] if a["status"] in ("PENDING", "DONE")]}
        for day in days
    ]
    payload = DraftInput(**{key: itinerary[key] for key in DraftInput.model_fields})
    validate_plan(payload, active_days)


@router.post("/adapt-proposals/{proposal_id}/decision")
def decide(
    proposal_id: str, payload: DecisionInput, request: Request,
    user_id: Annotated[str, Depends(current_user)],
):
    with store.connect() as db, db:
        db.execute("BEGIN IMMEDIATE")
        proposal = db.execute(
            "SELECT * FROM adapt_proposals WHERE proposal_id = ? AND user_id = ?",
            (proposal_id, user_id),
        ).fetchone()
        if proposal is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy đề xuất.")
        if proposal["decision"] is not None:
            if proposal["decision"] != payload.decision or proposal["option_id"] != payload.option_id:
                raise APIError(409, "PROPOSAL_ALREADY_DECIDED", "Đề xuất đã được xử lý.")
            return json.loads(proposal["result"])
        itinerary = owned(db, proposal["itinerary_id"], user_id)
        if payload.decision == "ACCEPT":
            if store.current_id(db, user_id) != itinerary["itinerary_id"]:
                raise APIError(409, "NOT_CURRENT_ITINERARY", "Hãy tải lại lịch hiện hành.")
            if itinerary["version"] != proposal["base_version"]:
                raise APIError(409, "STALE_PROPOSAL", "Lịch đã thay đổi. Hãy tạo lại đề xuất.")
            option = next(
                (item for item in json.loads(proposal["payload"])["options"] if item["option_id"] == payload.option_id),
                None,
            )
            if option is None:
                raise APIError(422, "INVALID_OPTION", "Phương án không thuộc đề xuất.")
            validator = request.app.state.option_validator
            if validator is None:
                raise APIError(503, "AI_UNAVAILABLE", "Đang chờ bộ kiểm tra ràng buộc F05.")
            try:
                validate_preservation(db, itinerary, option["proposed_days"])
                if not validator(itinerary, option):
                    raise ValueError("F05 constraints failed")
            except (KeyError, IndexError, TypeError, ValueError, APIError):
                raise APIError(409, "PROPOSAL_NO_LONGER_VALID", "Phương án không còn hợp lệ.") from None
            apply_days(db, itinerary["itinerary_id"], option["proposed_days"])
            itinerary = owned(db, itinerary["itinerary_id"], user_id)
        else:
            itinerary = owned(db, store.current_id(db, user_id), user_id)
        result = {
            "proposal_id": proposal_id, "decision": payload.decision,
            "option_id": payload.option_id, "itinerary": itinerary,
        }
        db.execute("""
            UPDATE adapt_proposals SET decision = ?, option_id = ?, result = ?
            WHERE proposal_id = ?
        """, (payload.decision, payload.option_id, json.dumps(result, ensure_ascii=False), proposal_id))
    return result
