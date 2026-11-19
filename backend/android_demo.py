"""Account-owned practice itineraries using the published Android route catalog."""
from datetime import datetime, timedelta, timezone
from copy import deepcopy
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

import itinerary_store as store
from adapt_f05.ranking import RuleRanker
from itinerary_api import APIError, DraftInput, current_user, validate_plan
from plan_f02 import PlanProvider

router = APIRouter(prefix="/api/v1/demo-itineraries", tags=["Lịch mẫu Android"])


class CurrentSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    itinerary_id: str | None
    version: Annotated[int, Field(strict=True, ge=1)] | None


def check_selection(db, owner, selection):
    current = store.current_id(db, owner)
    version = db.execute("SELECT version FROM itineraries WHERE itinerary_id = ?", (current,)).fetchone()
    if (current, version[0] if version else None) != (selection.itinerary_id, selection.version):
        raise APIError(409, "STALE_ITINERARY", "Lịch đã đổi. Hãy tải lại trước khi mở hoặc đóng lịch mẫu.")


@router.post("", status_code=201)
def load_sample(selection: CurrentSelection, request: Request, owner=Depends(current_user)):
    provider = request.app.state.plan_provider
    today = datetime.now(timezone(timedelta(hours=7))).date()
    payload = DraftInput(departure_date=(today - timedelta(days=1)).isoformat(),
                         return_date=(today + timedelta(days=1)).isoformat(),
                         departure_time="06:00", min_rest_minutes=60, interests=["nature", "culture"])
    # The button loads a reproducible sample, independent of quota. Personal PLAN
    # and all ADAPT requests keep their configured Gemini ranker.
    # Two 60-minute visits after lunch give a real choice of which to keep if
    # the traveller rests until 15:00. Freeze that sequence only in this sample.
    route = deepcopy(provider.templates[3])
    for day in route["days"]:
        variants = [day["stops"], *day.pop("alternative_stops", [])]
        day["stops"] = variants[day.get("sample_variant", 0)]
    days = PlanProvider(provider.catalog, {3: route}, RuleRanker())(payload)
    validate_plan(payload, days)
    with store.connect() as db, db:
        db.execute("BEGIN IMMEDIATE")
        check_selection(db, owner, selection)
        trip = store.save_draft(db, owner, payload, days)
        store.confirm(db, trip)
        sample_id = trip["itinerary_id"]
        db.execute("INSERT INTO demo_samples VALUES (?, ?, 1)", (sample_id, owner))
        first, second = trip["days"][:2]
        lunch = next(a for a in second["activities"] if a["type"] == "REST")
        db.execute("""UPDATE activities SET status = 'DONE', completed_at = ?
                      WHERE day_id = ? OR (day_id = ? AND end_time <= ?)""",
                   (store.utc_now(), first["day_id"], second["day_id"], lunch["start_time"]))
        return {"itinerary": store.load_itinerary(db, sample_id, owner)}


@router.post("/close")
def close_sample(selection: CurrentSelection, owner=Depends(current_user)):
    with store.connect() as db, db:
        db.execute("BEGIN IMMEDIATE")
        check_selection(db, owner, selection)
        db.execute("UPDATE demo_samples SET active = 0 WHERE user_id = ? AND active = 1", (owner,))
        current = store.current_id(db, owner)
        return {"itinerary": store.load_itinerary(db, current, owner) if current else None}
