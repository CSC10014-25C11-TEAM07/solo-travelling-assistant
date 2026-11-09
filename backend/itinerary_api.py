import os
from datetime import date, datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

import itinerary_store as store

router = APIRouter(prefix="/api/v1")
bearer = HTTPBearer(auto_error=False)


class APIError(Exception):
    def __init__(self, status, code, message):
        self.status = status
        self.code = code
        self.message = message


def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    import auth
    from fastapi.responses import JSONResponse
    import json
    result = auth.session_response(credentials)
    if isinstance(result, JSONResponse):
        body = json.loads(result.body)
        raise APIError(result.status_code, body["code"], body["message"])
    return result["user_id"]



class DraftInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    departure_date: date
    return_date: date
    departure_time: str = Field(pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
    interests: list[Literal["nature", "coffee", "culture", "food"]] = Field(min_length=1)
    min_rest_minutes: StrictInt = Field(gt=0)

    @field_validator("departure_date", "return_date", mode="before")
    @classmethod
    def validate_date(cls, value):
        if not isinstance(value, str):
            raise ValueError("Ngày phải theo YYYY-MM-DD.")
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError("Ngày phải theo YYYY-MM-DD.")
        return parsed

    @model_validator(mode="after")
    def validate_trip(self):
        if (self.return_date - self.departure_date).days not in (2, 3):
            raise ValueError("Chuyến đi cần đúng 3 hoặc 4 ngày.")
        return self


class ActivityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["DONE"]
    base_version: StrictInt = Field(ge=1)


def mock_plan(request):
    if os.environ.get("MOCK_PLAN") != "1":
        raise APIError(503, "AI_UNAVAILABLE", "Logic F02 đang chờ tích hợp.")
    # MOCK storage fixture. Nhật replaces this provider with validated F02 output.
    start = datetime.strptime(request.departure_time, "%H:%M")
    end = start + timedelta(minutes=request.min_rest_minutes)
    if end.date() != start.date():
        raise APIError(422, "NO_FEASIBLE_ITINERARY", "Khoảng nghỉ vượt quá ngày.")
    return [
        {
            "date": (request.departure_date + timedelta(days=number)).isoformat(),
            "end_deadline": "23:59",
            "activities": [{
                "type": "REST",
                "name": "MOCK — Nghỉ thử luồng lưu lịch",
                "start_time": request.departure_time,
                "end_time": end.strftime("%H:%M"),
                "is_optional": False,
            }],
        }
        for number in range((request.return_date - request.departure_date).days + 1)
    ]


def validate_plan(payload, days):
    expected_dates = [
        (payload.departure_date + timedelta(days=number)).isoformat()
        for number in range((payload.return_date - payload.departure_date).days + 1)
    ]
    try:
        if [day["date"] for day in days] != expected_dates:
            raise ValueError("Missing or incorrect dates")
        for day in days:
            deadline = datetime.strptime(day["end_deadline"], "%H:%M")
            first_start = payload.departure_time if day["date"] == expected_dates[0] else "00:00"
            previous_end = datetime.strptime(first_start, "%H:%M")
            rest_minutes = 0
            if not day["activities"]:
                raise ValueError("Empty day")
            for activity in day["activities"]:
                start = datetime.strptime(activity["start_time"], "%H:%M")
                end = datetime.strptime(activity["end_time"], "%H:%M")
                if start < previous_end or end <= start or end > deadline:
                    raise ValueError("Invalid activity times")
                if activity["type"] not in ("REST", "TRAVEL", "VISIT"):
                    raise ValueError("Unknown activity type")
                if activity["type"] == "VISIT" and not activity.get("place_id"):
                    raise ValueError("Missing place")
                if not isinstance(activity["name"], str) or not activity["name"]:
                    raise ValueError("Missing name")
                if type(activity["is_optional"]) is not bool:
                    raise ValueError("Invalid optional flag")
                if activity["type"] == "REST":
                    rest_minutes += int((end - start).total_seconds() / 60)
                previous_end = end
            if rest_minutes < payload.min_rest_minutes:
                raise ValueError("Insufficient daily rest")
    except (KeyError, TypeError, ValueError):
        raise APIError(502, "AI_INVALID_OUTPUT", "Lịch tạo ra chưa đáp ứng cấu trúc hoặc thời gian.") from None


def owned(db, itinerary_id, user_id):
    itinerary = store.load_itinerary(db, itinerary_id, user_id)
    if itinerary is None:
        raise APIError(404, "NOT_FOUND", "Không tìm thấy lịch.")
    return itinerary


@router.post("/itinerary-drafts", status_code=201)
def create_draft(payload: DraftInput, request: Request, user_id=Depends(current_user)):
    days = request.app.state.plan_provider(payload)
    validate_plan(payload, days)
    with store.connect() as db, db:
        itinerary = store.save_draft(db, user_id, payload, days)
    return {"draft_id": itinerary["itinerary_id"], "itinerary": itinerary}


@router.post("/itinerary-drafts/{draft_id}/confirm")
def confirm_draft(draft_id: str, user_id=Depends(current_user)):
    with store.connect() as db, db:
        db.execute("BEGIN IMMEDIATE")
        itinerary = owned(db, draft_id, user_id)
        if itinerary["status"] == "DRAFT":
            payload = DraftInput(**{key: itinerary[key] for key in DraftInput.model_fields})
            validate_plan(payload, itinerary["days"])
            store.confirm(db, itinerary)
        itinerary = owned(db, draft_id, user_id)
    return {"itinerary": itinerary}


@router.get("/itineraries/current")
def get_current(user_id=Depends(current_user)):
    with store.connect() as db, db:
        itinerary_id = store.current_id(db, user_id)
        itinerary = store.load_itinerary(db, itinerary_id, user_id) if itinerary_id else None
    return {"itinerary": itinerary}


@router.patch("/itineraries/{itinerary_id}/activities/{activity_id}")
def complete_activity(
    itinerary_id: str, activity_id: str, payload: ActivityUpdate,
    user_id=Depends(current_user),
):
    with store.connect() as db, db:
        db.execute("BEGIN IMMEDIATE")
        itinerary = owned(db, itinerary_id, user_id)
        if store.current_id(db, user_id) != itinerary_id:
            raise APIError(409, "NOT_CURRENT_ITINERARY", "Hãy tải lại lịch hiện hành.")
        activity = db.execute("""
            SELECT a.* FROM activities a
            JOIN itinerary_days d ON d.day_id = a.day_id
            WHERE a.activity_id = ? AND d.itinerary_id = ?
        """, (activity_id, itinerary_id)).fetchone()
        if activity is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy hoạt động.")
        if activity["status"] in ("DROPPED", "REPLACED"):
            raise APIError(409, "ACTIVITY_NOT_ACTIVE", "Hoạt động đã bỏ hoặc thay thế.")
        if activity["status"] != "DONE":
            if itinerary["version"] != payload.base_version:
                raise APIError(409, "STALE_ITINERARY", "Lịch đã thay đổi. Hãy tải lại.")
            db.execute(
                "UPDATE activities SET status = 'DONE', completed_at = ? WHERE activity_id = ?",
                (store.utc_now(), activity_id),
            )
            db.execute(
                "UPDATE itineraries SET version = version + 1 WHERE itinerary_id = ?",
                (itinerary_id,),
            )
        itinerary = owned(db, itinerary_id, user_id)
    return {"itinerary": itinerary}
