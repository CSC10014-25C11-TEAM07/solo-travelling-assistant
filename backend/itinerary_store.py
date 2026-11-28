import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent


@contextmanager
def connect():
    from auth import connect as auth_connect
    db = auth_connect()
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout = 15000")
    try:
        yield db
    finally:
        db.close()


def initialize():
    with connect() as db, db:
        db.executescript((ROOT / "itinerary_schema.sql").read_text(encoding="utf-8-sig"))
        db.execute("BEGIN IMMEDIATE")
        columns = {row["name"] for row in db.execute("PRAGMA table_info(itinerary_days)")}
        if "enforce_end_deadline" not in columns:
            db.execute("ALTER TABLE itinerary_days ADD COLUMN enforce_end_deadline "
                       "INTEGER NOT NULL DEFAULT 1 CHECK (enforce_end_deadline IN (0, 1))")


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
    if db.execute("SELECT 1 FROM demo_samples WHERE itinerary_id = ?", (itinerary_id,)).fetchone():
        itinerary["is_demo_sample"] = True
    itinerary["interests"] = json.loads(itinerary["interests"])
    days = db.execute(
        "SELECT * FROM itinerary_days WHERE itinerary_id = ? ORDER BY day_number",
        (itinerary_id,),
    ).fetchall()
    itinerary["days"] = []
    for row in days:
        day = dict(row)
        if day.pop("enforce_end_deadline") == 0:
            day["enforce_end_deadline"] = False
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
        SELECT i.itinerary_id FROM itineraries i
        LEFT JOIN demo_samples s ON s.itinerary_id = i.itinerary_id
        WHERE i.user_id = ? AND i.status = 'CURRENT' AND (s.active IS NULL OR s.active = 1)
        ORDER BY COALESCE(s.active, 0) DESC, i.confirmed_at DESC LIMIT 1
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
                (day_id, itinerary_id, day_number, date, end_deadline, enforce_end_deadline)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (day_id, itinerary_id, number, planned_day["date"], planned_day["end_deadline"],
              planned_day.get("enforce_end_deadline", True)))
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
    db.execute("UPDATE demo_samples SET active = 0 WHERE user_id = ? AND active = 1",
               (itinerary["user_id"],))
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
