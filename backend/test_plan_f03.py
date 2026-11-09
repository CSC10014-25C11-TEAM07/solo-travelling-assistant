import os
import sqlite3
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

import itinerary_store as store
from itinerary_api import APIError
from main import create_app


def resolve_user_id(token):
    if token not in ("TEST-U1", "TEST-U2"):
        raise APIError(401, "INVALID_SESSION", "Phiên không hợp lệ.")
    return token


def run():
    with tempfile.TemporaryDirectory() as directory:
        os.environ["DATABASE_PATH"] = str(Path(directory) / "test.sqlite")
        os.environ["MOCK_PLAN"] = "1"
        store.initialize()
        with store.connect() as db, db:
            db.execute("CREATE TABLE users (user_id TEXT PRIMARY KEY NOT NULL)")
            db.executemany("INSERT INTO users VALUES (?)", [("TEST-U1",), ("TEST-U2",)])
        app = create_app(resolve_user_id=resolve_user_id)
        headers = {"Authorization": "Bearer TEST-U1"}
        other = {"Authorization": "Bearer TEST-U2"}
        payload = {
            "departure_date": "2026-11-09", "return_date": "2026-11-11",
            "departure_time": "08:00", "interests": ["nature"], "min_rest_minutes": 30,
        }
        with TestClient(app) as client:
            assert client.get("/health").json() == {"status": "ok"}
            assert client.get("/api/v1/itineraries/current").status_code == 401
            assert client.get("/api/v1/itineraries/current", headers=headers).json() == {"itinerary": None}
            for invalid in (0, -1, True, "30"):
                response = client.post("/api/v1/itinerary-drafts", json={**payload, "min_rest_minutes": invalid}, headers=headers)
                assert response.status_code == 422, response.text
                assert response.json()["code"] == "VALIDATION_ERROR"
            response = client.post("/api/v1/itinerary-drafts", json=payload, headers=headers)
            assert response.status_code == 201, response.text
            draft = response.json()
            itinerary_id = draft["draft_id"]
            confirm_url = f"/api/v1/itinerary-drafts/{itinerary_id}/confirm"
            assert draft["itinerary"]["version"] == 1
            assert len(draft["itinerary"]["days"]) == 3
            with TestClient(create_app(resolve_user_id=resolve_user_id, plan_provider=lambda payload: [])) as invalid_client:
                invalid = invalid_client.post("/api/v1/itinerary-drafts", json=payload, headers=headers)
                assert invalid.status_code == 502
                assert invalid.json()["code"] == "AI_INVALID_OUTPUT"
            assert client.post(confirm_url, headers=other).status_code == 404
            itinerary = client.post(confirm_url, headers=headers).json()["itinerary"]
            assert client.post(confirm_url, headers=headers).json()["itinerary"] == itinerary
            activities = [day["activities"][0]["activity_id"] for day in itinerary["days"]]
            patch_url = f"/api/v1/itineraries/{itinerary_id}/activities/"
            assert client.patch(patch_url + activities[0], headers=other, json={"status": "DONE", "base_version": 1}).status_code == 404
            def mark_done(activity):
                return client.patch(patch_url + activity, headers=headers, json={"status": "DONE", "base_version": 1})
            with ThreadPoolExecutor(max_workers=2) as executor:
                responses = list(executor.map(mark_done, activities[:2]))
            assert sorted(response.status_code for response in responses) == [200, 409]
            winner = next(index for index, response in enumerate(responses) if response.status_code == 200)
            saved = responses[winner].json()["itinerary"]
            assert saved["version"] == 2
            assert responses[1 - winner].json()["code"] == "STALE_ITINERARY"
            assert mark_done(activities[winner]).json()["itinerary"] == saved
            with store.connect() as db, db:
                db.execute("""
                    CREATE TRIGGER fail_version BEFORE UPDATE OF version ON itineraries
                    BEGIN SELECT RAISE(ABORT, 'test write failure'); END
                """)
            failure = client.patch(patch_url + activities[2], headers=headers, json={"status": "DONE", "base_version": 2})
            assert failure.status_code == 500
            assert client.get("/api/v1/itineraries/current", headers=headers).json()["itinerary"] == saved
            with store.connect() as db, db:
                db.execute("DROP TRIGGER fail_version")
            second = client.post("/api/v1/itinerary-drafts", json={**payload, "return_date": "2026-11-12"}, headers=headers).json()
            assert len(second["itinerary"]["days"]) == 4
            assert client.get("/api/v1/itineraries/current", headers=headers).json()["itinerary"] == saved
            newer = client.post(f"/api/v1/itinerary-drafts/{second['draft_id']}/confirm", headers=headers).json()["itinerary"]
            assert newer["confirmed_at"] > saved["confirmed_at"]
            assert client.post(confirm_url, headers=headers).json()["itinerary"] == saved
            assert mark_done(activities[2]).json()["code"] == "NOT_CURRENT_ITINERARY"
            assert client.get("/api/v1/itineraries/current", headers=other).json() == {"itinerary": None}
        with TestClient(create_app(resolve_user_id=resolve_user_id)) as client:
            assert client.get("/api/v1/itineraries/current", headers=headers).json()["itinerary"] == newer
        with TestClient(create_app()) as client:
            assert client.get("/api/v1/itineraries/current", headers=headers).status_code == 503
        with store.connect() as db:
            assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        print("PASS: validation, 3/4-day drafts, ownership, confirmation replay, concurrent DONE, stale version, persistence, current ordering, auth integration guard")


if __name__ == "__main__":
    run()
