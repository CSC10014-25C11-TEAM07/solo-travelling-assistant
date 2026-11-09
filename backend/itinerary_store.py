import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent


def database_path():
    configured = os.environ.get("DATABASE_PATH")
    return Path(configured).resolve() if configured else ROOT / "data" / "app.sqlite"


@contextmanager
def connect():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
    finally:
        db.close()


def initialize():
    with connect() as db:
        db.executescript((ROOT / "itinerary_schema.sql").read_text(encoding="utf-8-sig"))


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def new_id():
    return str(uuid4())


def load_itinerary(db, itinerary_id, user_id):
    row = db.execute(
        "SELECT * FROM itineraries WHERE itinerary_id = ? AND user_id = ?",
        (itinerary_id, user_id),
    ).fetchone()
    if row is None:
        return None
    itinerary = dict(row)
    itinerary["interests"] = json.loads(itinerary["interests"])
    days = db.execute(
        "SELECT * FROM itinerary_days WHERE itinerary_id = ? ORDER BY day_number",
        (itinerary_id,),
    ).fetchall()
    itinerary["days"] = []
    for row in days:
        day = dict(row)
        activities = db.execute(
            "SELECT * FROM activities WHERE day_id = ? ORDER BY start_time, activity_id",
            (day["day_id"],),
        ).fetchall()
        day["activities"] = []
        for activity_row in activities:
            activity = dict(activity_row)
            activity["is_optional"] = bool(activity["is_optional"])
            day["activities"].append(activity)
        itinerary["days"].append(day)
    return itinerary


def current_id(db, user_id):
    row = db.execute("""
        SELECT itinerary_id FROM itineraries
        WHERE user_id = ? AND status = 'CURRENT'
        ORDER BY confirmed_at DESC LIMIT 1
    """, (user_id,)).fetchone()
    return row["itinerary_id"] if row else None


def save_draft(db, user_id, request, days):
    itinerary_id = new_id()
    db.execute("""
        INSERT INTO itineraries (
            itinerary_id, user_id, departure_date, return_date, departure_time,
            interests, min_rest_minutes, status, version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'DRAFT', 1, ?)
    """, (
        itinerary_id, user_id, request.departure_date.isoformat(),
        request.return_date.isoformat(), request.departure_time,
        json.dumps(request.interests), request.min_rest_minutes, utc_now(),
    ))
    for number, planned_day in enumerate(days, 1):
        day_id = new_id()
        db.execute("""
            INSERT INTO itinerary_days
                (day_id, itinerary_id, day_number, date, end_deadline)
            VALUES (?, ?, ?, ?, ?)
        """, (day_id, itinerary_id, number, planned_day["date"], planned_day["end_deadline"]))
        for activity in planned_day["activities"]:
            db.execute("""
                INSERT INTO activities (
                    activity_id, day_id, type, name, place_id,
                    start_time, end_time, status, is_optional
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
            """, (
                new_id(), day_id, activity["type"], activity["name"],
                activity.get("place_id"), activity["start_time"],
                activity["end_time"], activity["is_optional"],
            ))
    return load_itinerary(db, itinerary_id, user_id)


def confirm(db, itinerary):
    # Caller holds BEGIN IMMEDIATE, so confirmations serialize across connections.
    latest = db.execute(
        "SELECT MAX(confirmed_at) FROM itineraries WHERE user_id = ?",
        (itinerary["user_id"],),
    ).fetchone()[0]
    timestamp = datetime.now(timezone.utc)
    if latest:
        timestamp = max(timestamp, datetime.fromisoformat(latest) + timedelta(microseconds=1))
    db.execute("""
        UPDATE itineraries SET status = 'CURRENT', confirmed_at = ?
        WHERE itinerary_id = ?
    """, (timestamp.isoformat(timespec="microseconds"), itinerary["itinerary_id"]))
