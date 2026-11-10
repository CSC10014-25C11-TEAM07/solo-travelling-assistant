import json

import itinerary_store as store
from itinerary_api import APIError, owned


def initialize():
    with store.connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS adapt_proposals (
                proposal_id TEXT PRIMARY KEY NOT NULL,
                itinerary_id TEXT NOT NULL REFERENCES itineraries(itinerary_id),
                user_id TEXT NOT NULL REFERENCES users(user_id),
                base_version INTEGER NOT NULL CHECK (base_version >= 1),
                payload TEXT NOT NULL,
                decision TEXT CHECK (decision IN ('ACCEPT', 'REJECT')),
                option_id TEXT,
                result TEXT,
                CHECK ((decision IS NULL AND result IS NULL)
                    OR (decision IS NOT NULL AND result IS NOT NULL))
            );
        """)


def save_proposal(proposal, user_id):
    """F05 calls this before returning its validated, server-generated proposal."""
    if proposal["type"] not in ("EXTEND_REST", "REPLACE_LOCATION"):
        raise ValueError("Unknown proposal type")
    options = proposal["options"]
    option_ids = [option["option_id"] for option in options]
    if len(options) > 2 or len(set(option_ids)) != len(option_ids):
        raise ValueError("Expected up to two uniquely identified options")
    if not options and not proposal.get("no_option_reason"):
        raise ValueError("Empty proposals require a reason")
    with store.connect() as db, db:
        db.execute("BEGIN IMMEDIATE")
        itinerary = owned(db, proposal["itinerary_id"], user_id)
        if store.current_id(db, user_id) != itinerary["itinerary_id"]:
            raise APIError(409, "NOT_CURRENT_ITINERARY", "Hãy tải lại lịch hiện hành.")
        if itinerary["version"] != proposal["base_version"]:
            raise APIError(409, "STALE_ITINERARY", "Lịch đã thay đổi. Hãy tải lại.")
        db.execute("""
            INSERT INTO adapt_proposals (
                proposal_id, itinerary_id, user_id, base_version, payload
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            proposal["proposal_id"], itinerary["itinerary_id"], user_id,
            itinerary["version"], json.dumps(proposal, ensure_ascii=False),
        ))


def apply_days(db, itinerary_id, days):
    # Validation guarantees that existing rows are retained, including history.
    for day in days:
        for activity in day["activities"]:
            db.execute("""
                INSERT INTO activities (
                    activity_id, day_id, type, name, place_id, start_time,
                    end_time, status, is_optional, replaces_activity_id, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(activity_id) DO UPDATE SET
                    name = excluded.name, place_id = excluded.place_id,
                    start_time = excluded.start_time, end_time = excluded.end_time,
                    status = excluded.status, is_optional = excluded.is_optional,
                    replaces_activity_id = excluded.replaces_activity_id,
                    completed_at = excluded.completed_at
            """, (
                activity["activity_id"], day["day_id"], activity["type"],
                activity["name"], activity["place_id"], activity["start_time"],
                activity["end_time"], activity["status"], activity["is_optional"],
                activity["replaces_activity_id"], activity["completed_at"],
            ))
    db.execute(
        "UPDATE itineraries SET version = version + 1 WHERE itinerary_id = ?",
        (itinerary_id,),
    )
