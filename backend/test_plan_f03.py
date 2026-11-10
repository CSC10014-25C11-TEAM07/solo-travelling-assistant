import copy
import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

import auth
import itinerary_store as store
from adapt_store import save_proposal
from main import create_app


class PlanAdaptTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database_patch = patch.object(auth, "DB_PATH", Path(self.directory.name) / "test.sqlite3")
        self.database_patch.start()
        self.environment = patch.dict(os.environ, {"MOCK_PLAN": "1"})
        self.environment.start()
        # This validator is only for MOCK storage tests. Production uses Nhật's F05 checker.
        self.app = create_app(option_validator=lambda itinerary, option: True)
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.headers = self.register("owner_test")
        self.other = self.register("other_test")
        self.payload = {
            "departure_date": "2026-11-09", "return_date": "2026-11-11",
            "departure_time": "08:00", "interests": ["nature"], "min_rest_minutes": 30,
        }

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.environment.stop()
        self.database_patch.stop()
        self.directory.cleanup()

    def register(self, username):
        credentials = {"username": username, "password": "temporary-integration-password-only"}
        self.assertEqual(self.client.post("/api/v1/auth/register", json=credentials).status_code, 201)
        response = self.client.post("/api/v1/auth/login", json=credentials)
        self.assertEqual(response.status_code, 200)
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    def draft(self, **changes):
        response = self.client.post("/api/v1/itinerary-drafts", json={**self.payload, **changes}, headers=self.headers)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["itinerary"]

    def confirm(self, itinerary):
        response = self.client.post(f"/api/v1/itinerary-drafts/{itinerary['itinerary_id']}/confirm", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["itinerary"]

    def current(self):
        return self.client.get("/api/v1/itineraries/current", headers=self.headers).json()["itinerary"]

    def complete(self, itinerary, day=0, version=None):
        activity = itinerary["days"][day]["activities"][0]
        return self.client.patch(
            f"/api/v1/itineraries/{itinerary['itinerary_id']}/activities/{activity['activity_id']}",
            headers=self.headers,
            json={"status": "DONE", "base_version": version or itinerary["version"]},
        )

    def proposal(self, itinerary, options=True):
        days = copy.deepcopy(itinerary["days"])
        days[0]["activities"][0]["end_time"] = "09:00"
        proposal = {
            "proposal_id": str(uuid4()), "itinerary_id": itinerary["itinerary_id"],
            "type": "EXTEND_REST", "base_version": itinerary["version"],
            "options": [{
                "option_id": str(uuid4()), "proposed_days": days,
                "changes": [], "reason": "MOCK", "tradeoff": "MOCK",
                "estimated_end_time": "09:00",
            }] if options else [],
            "no_option_reason": None if options else "MOCK — no option",
        }
        save_proposal(proposal, itinerary["user_id"])
        return proposal

    def decision(self, proposal, decision="ACCEPT", headers=None, option_id=None):
        body = {"decision": decision}
        if decision == "ACCEPT":
            body["option_id"] = option_id or proposal["options"][0]["option_id"]
        return self.client.post(
            f"/api/v1/adapt-proposals/{proposal['proposal_id']}/decision",
            headers=headers or self.headers, json=body,
        )

    def test_plan_validation_and_auth(self):
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        self.assertIsNone(self.current())
        self.assertEqual(self.client.get("/api/v1/itineraries/current").status_code, 401)
        invalid = {"Authorization": "Bearer invalid"}
        self.assertEqual(self.client.get("/api/v1/itineraries/current", headers=invalid).json()["code"], "INVALID_SESSION")
        for changes in ({"min_rest_minutes": 0}, {"min_rest_minutes": True}, {"min_rest_minutes": "30"}, {"return_date": "2026-11-10"}, {"interests": []}):
            response = self.client.post("/api/v1/itinerary-drafts", json={**self.payload, **changes}, headers=self.headers)
            self.assertEqual(response.status_code, 422)
        self.assertEqual(len(self.draft()["days"]), 3)
        self.assertEqual(len(self.draft(return_date="2026-11-12")["days"]), 4)
        self.client.post("/api/v1/auth/logout", headers=self.headers)
        self.assertEqual(self.client.get("/api/v1/itineraries/current", headers=self.headers).json()["code"], "INVALID_SESSION")

    def test_confirm_current_persistence_and_ownership(self):
        draft = self.draft()
        response = self.client.post(f"/api/v1/itinerary-drafts/{draft['itinerary_id']}/confirm", headers=self.other)
        self.assertEqual(response.status_code, 404)
        itinerary = self.confirm(draft)
        self.assertEqual(self.confirm(draft), itinerary)
        self.assertEqual(self.draft()["status"], "DRAFT")
        self.assertEqual(self.current(), itinerary)
        newer = self.confirm(self.draft())
        self.assertGreater(newer["confirmed_at"], itinerary["confirmed_at"])
        self.assertEqual(self.confirm(draft), itinerary)
        self.assertEqual(self.complete(itinerary).json()["code"], "NOT_CURRENT_ITINERARY")
        with TestClient(create_app()) as restarted:
            self.assertEqual(restarted.get("/api/v1/itineraries/current", headers=self.headers).json()["itinerary"], newer)

    def test_done_concurrency_replay_and_rollback(self):
        itinerary = self.confirm(self.draft())
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda day: self.complete(itinerary, day), (0, 1)))
        self.assertEqual(sorted(response.status_code for response in responses), [200, 409])
        winner = next(i for i, response in enumerate(responses) if response.status_code == 200)
        saved = responses[winner].json()["itinerary"]
        self.assertEqual(saved["version"], 2)
        self.assertEqual(self.complete(itinerary, winner).json()["itinerary"], saved)
        self.assertEqual(responses[1 - winner].json()["code"], "STALE_ITINERARY")
        with store.connect() as db, db:
            db.execute("CREATE TRIGGER fail_write BEFORE UPDATE OF version ON itineraries BEGIN SELECT RAISE(ABORT, 'forced failure'); END")
        response = self.complete(saved, 2)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(self.current(), saved)

    def test_accept_replay_and_conflicting_decision(self):
        itinerary = self.confirm(self.draft())
        proposal = self.proposal(itinerary)
        self.assertEqual(self.decision(proposal, headers=self.other).status_code, 404)
        self.assertEqual(self.decision(proposal, option_id="unknown").json()["code"], "INVALID_OPTION")
        accepted = self.decision(proposal)
        self.assertEqual(accepted.status_code, 200, accepted.text)
        result = accepted.json()
        self.assertEqual(result["itinerary"]["version"], 2)
        self.assertEqual(result["itinerary"]["days"][0]["activities"][0]["end_time"], "09:00")
        self.complete(result["itinerary"], 1)
        self.assertEqual(self.decision(proposal).json(), result)
        self.assertEqual(self.decision(proposal, "REJECT").json()["code"], "PROPOSAL_ALREADY_DECIDED")

    def test_stale_proposal_reject_and_empty_options(self):
        itinerary = self.confirm(self.draft())
        proposal = self.proposal(itinerary)
        saved = self.complete(itinerary, 1).json()["itinerary"]
        self.assertEqual(self.decision(proposal).json()["code"], "STALE_PROPOSAL")
        rejected = self.decision(proposal, "REJECT")
        self.assertEqual(rejected.json()["itinerary"], saved)
        self.assertEqual(self.decision(proposal, "REJECT").json(), rejected.json())
        empty = self.proposal(saved, options=False)
        self.assertEqual(self.decision(empty, "REJECT").status_code, 200)

    def test_done_preservation_and_invalid_option(self):
        itinerary = self.confirm(self.draft())
        saved = self.complete(itinerary, 0).json()["itinerary"]
        proposal = self.proposal(saved)
        response = self.decision(proposal)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "PROPOSAL_NO_LONGER_VALID")
        self.assertEqual(self.current(), saved)

    def test_accept_failure_rolls_back_decision_and_schedule(self):
        itinerary = self.confirm(self.draft())
        proposal = self.proposal(itinerary)
        with store.connect() as db, db:
            db.execute("CREATE TRIGGER fail_decision BEFORE UPDATE OF decision ON adapt_proposals BEGIN SELECT RAISE(ABORT, 'forced failure'); END")
        self.assertEqual(self.decision(proposal).status_code, 500)
        self.assertEqual(self.current(), itinerary)
        with store.connect() as db, db:
            self.assertIsNone(db.execute("SELECT decision FROM adapt_proposals WHERE proposal_id = ?", (proposal["proposal_id"],)).fetchone()[0])
            db.execute("DROP TRIGGER fail_decision")
        self.assertEqual(self.decision(proposal).status_code, 200)

    def test_accept_concurrent_requests_apply_once(self):
        itinerary = self.confirm(self.draft())
        proposal = self.proposal(itinerary)
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: self.decision(proposal), (0, 1)))
        self.assertEqual([response.status_code for response in responses], [200, 200])
        self.assertEqual(responses[0].json(), responses[1].json())
        self.assertEqual(self.current()["version"], 2)

    def test_accept_needs_real_constraint_validator(self):
        itinerary = self.confirm(self.draft())
        proposal = self.proposal(itinerary)
        self.app.state.option_validator = None
        self.assertEqual(self.decision(proposal).status_code, 503)
        self.assertEqual(self.current(), itinerary)


    def route(self):
        itinerary = self.confirm(self.draft())
        day_id = itinerary["days"][0]["day_id"]

        def activity(activity_id, kind, place, start, end, status="PENDING", optional=False):
            return {
                "activity_id": activity_id, "day_id": day_id, "type": kind,
                "name": "MOCK " + activity_id, "place_id": place,
                "start_time": start, "end_time": end, "status": status,
                "is_optional": optional, "replaces_activity_id": None,
                "completed_at": "2026-11-09T01:30:00Z" if status == "DONE" else None,
            }

        rows = [
            activity("MOCK-OA", "TRAVEL", None, "08:00", "08:15", "DONE"),
            activity("MOCK-A", "VISIT", "MOCK-A", "08:15", "08:30", "DONE"),
            activity("MOCK-REST", "REST", "MOCK-A", "08:30", "09:00"),
            activity("MOCK-AB", "TRAVEL", None, "09:00", "09:15"),
            activity("MOCK-B", "VISIT", "MOCK-B", "09:15", "09:45", optional=True),
            activity("MOCK-BC", "TRAVEL", None, "09:45", "10:00"),
            activity("MOCK-C", "VISIT", "MOCK-C", "10:00", "10:30"),
        ]
        with store.connect() as db, db:
            db.execute("DELETE FROM activities WHERE day_id = ?", (day_id,))
            for row in rows:
                db.execute("""
                    INSERT INTO activities (
                        activity_id, day_id, type, name, place_id, start_time,
                        end_time, status, is_optional, replaces_activity_id, completed_at
                    ) VALUES (
                        :activity_id, :day_id, :type, :name, :place_id, :start_time,
                        :end_time, :status, :is_optional, :replaces_activity_id, :completed_at
                    )
                """, row)
        return self.current()

    def reroute_proposal(self, itinerary, rain=False, same_place=False):
        proposal = self.proposal(itinerary)
        # Replace the generic storage fixture with a full route snapshot.
        days = copy.deepcopy(itinerary["days"])
        rows = {a["activity_id"]: a for a in days[0]["activities"]}
        rows["MOCK-AB"]["status"] = "REPLACED"
        rows["MOCK-BC"]["status"] = "REPLACED"
        if rain:
            rows["MOCK-B"]["status"] = "REPLACED"
            indoor = {**rows["MOCK-B"], "activity_id": "MOCK-INDOOR",
                      "name": "MOCK indoor", "place_id": "MOCK-INDOOR",
                      "status": "PENDING", "replaces_activity_id": "MOCK-B"}
            first = {**rows["MOCK-AB"], "activity_id": "MOCK-A-INDOOR",
                     "status": "PENDING"}
            second = {**rows["MOCK-BC"], "activity_id": "MOCK-INDOOR-C",
                      "status": "PENDING"}
            rows.update({a["activity_id"]: a for a in (indoor, first, second)})
        else:
            rows["MOCK-B"]["status"] = "DROPPED"
            rows["MOCK-REST"]["end_time"] = "09:30"
            rows["MOCK-C"].update(start_time="09:45", end_time="10:15")
            if same_place:
                rows["MOCK-C"].update(start_time="09:30", end_time="10:00")
            else:
                rows["MOCK-AC"] = {
                    **rows["MOCK-AB"], "activity_id": "MOCK-AC",
                    "name": "MOCK A to C", "start_time": "09:30",
                    "end_time": "09:45", "status": "PENDING",
                }
        days[0]["activities"] = sorted(rows.values(), key=lambda a: (a["start_time"], a["activity_id"]))
        # Fresh proposal ID; the earlier generic fixture remains undecided.
        proposal["proposal_id"] = str(uuid4())
        proposal["type"] = "REPLACE_LOCATION" if rain else "EXTEND_REST"
        proposal["options"][0]["proposed_days"] = days
        proposal["options"][0]["estimated_end_time"] = "10:30" if rain else "10:15"
        save_proposal(proposal, itinerary["user_id"])
        return proposal

    def test_rest_drop_keeps_old_travel_and_accept_replay_has_no_duplicate(self):
        itinerary = self.route()
        proposal = self.reroute_proposal(itinerary)
        self.assertEqual(self.current(), itinerary)
        response = self.decision(proposal)
        self.assertEqual(response.status_code, 200, response.text)
        saved = response.json()["itinerary"]
        rows = {a["activity_id"]: a for a in saved["days"][0]["activities"]}
        self.assertEqual(rows["MOCK-B"]["status"], "DROPPED")
        self.assertEqual(rows["MOCK-AB"]["status"], "REPLACED")
        self.assertEqual(rows["MOCK-BC"]["status"], "REPLACED")
        self.assertEqual(rows["MOCK-AC"]["status"], "PENDING")
        self.assertIsNone(rows["MOCK-AC"]["replaces_activity_id"])
        original = {a["activity_id"]: a for a in itinerary["days"][0]["activities"]}
        self.assertEqual(rows["MOCK-OA"], original["MOCK-OA"])
        self.assertEqual(rows["MOCK-AB"], {**original["MOCK-AB"], "status": "REPLACED"})
        self.assertEqual(saved["version"], itinerary["version"] + 1)
        self.assertEqual(self.decision(proposal).json(), response.json())
        self.assertEqual(self.current(), saved)
        with store.connect() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM activities WHERE activity_id = 'MOCK-AC'").fetchone()[0], 1)
        with TestClient(create_app()) as restarted:
            self.assertEqual(restarted.get("/api/v1/itineraries/current", headers=self.headers).json()["itinerary"], saved)

    def test_rain_replacement_keeps_travel_history(self):
        itinerary = self.route()
        proposal = self.reroute_proposal(itinerary, rain=True)
        response = self.decision(proposal)
        self.assertEqual(response.status_code, 200, response.text)
        rows = {a["activity_id"]: a for a in response.json()["itinerary"]["days"][0]["activities"]}
        for activity_id in ("MOCK-B", "MOCK-AB", "MOCK-BC"):
            self.assertEqual(rows[activity_id]["status"], "REPLACED")
        self.assertEqual(rows["MOCK-INDOOR"]["replaces_activity_id"], "MOCK-B")
        for activity_id in ("MOCK-A-INDOOR", "MOCK-INDOOR-C"):
            self.assertEqual(rows[activity_id]["status"], "PENDING")
        active = [a["activity_id"] for a in rows.values() if a["status"] in ("PENDING", "DONE")]
        self.assertNotIn("MOCK-AB", active)
        self.assertNotIn("MOCK-BC", active)
        self.assertEqual(self.current(), response.json()["itinerary"])
        self.assertEqual(self.decision(proposal).json(), response.json())

    def test_reject_rest_and_rain_leave_route_unchanged(self):
        itinerary = self.route()
        for rain in (False, True):
            proposal = self.reroute_proposal(itinerary, rain=rain)
            rejected = self.decision(proposal, "REJECT")
            self.assertEqual(rejected.status_code, 200, rejected.text)
            self.assertEqual(rejected.json()["itinerary"], itinerary)
            self.assertEqual(self.current(), itinerary)
            self.assertEqual(self.decision(proposal, "REJECT").json(), rejected.json())

    def test_reschedule_keeps_travel_ids(self):
        itinerary = self.route()
        proposal = self.proposal(itinerary)
        days = copy.deepcopy(itinerary["days"])
        for activity in days[0]["activities"]:
            if activity["activity_id"] == "MOCK-AB":
                activity.update(start_time="09:01", end_time="09:14")
        proposal["proposal_id"] = str(uuid4())
        proposal["options"][0]["proposed_days"] = days
        save_proposal(proposal, itinerary["user_id"])
        response = self.decision(proposal)
        self.assertEqual(response.status_code, 200, response.text)
        ids = [a["activity_id"] for a in response.json()["itinerary"]["days"][0]["activities"]]
        self.assertEqual(set(ids), {a["activity_id"] for a in itinerary["days"][0]["activities"]})

    def test_no_one_to_one_travel_replacement_required(self):
        itinerary = self.route()
        with store.connect() as db, db:
            db.execute("UPDATE activities SET place_id = 'MOCK-A' WHERE activity_id = 'MOCK-C'")
        itinerary = self.current()
        proposal = self.reroute_proposal(itinerary, same_place=True)
        response = self.decision(proposal)
        self.assertEqual(response.status_code, 200, response.text)
        rows = response.json()["itinerary"]["days"][0]["activities"]
        pending_travel = [a for a in rows if a["type"] == "TRAVEL" and a["status"] == "PENDING"]
        self.assertEqual(pending_travel, [])

    def test_pending_travel_cannot_be_dropped_and_done_cannot_change(self):
        itinerary = self.route()
        for activity_id, change in (
            ("MOCK-AB", {"status": "DROPPED"}),
            ("MOCK-OA", {"status": "REPLACED"}),
            ("MOCK-OA", {"end_time": "08:16"}),
            ("MOCK-AB", {"start_time": "09:01"}),
        ):
            proposal = self.reroute_proposal(itinerary)
            for activity in proposal["options"][0]["proposed_days"][0]["activities"]:
                if activity["activity_id"] == activity_id:
                    activity.update(change)
            proposal["proposal_id"] = str(uuid4())
            save_proposal(proposal, itinerary["user_id"])
            response = self.decision(proposal)
            self.assertEqual(response.status_code, 409, response.text)
            self.assertEqual(response.json()["code"], "PROPOSAL_NO_LONGER_VALID")
            self.assertEqual(self.current(), itinerary)

    def test_reroute_failure_rolls_back_new_travel_and_history(self):
        itinerary = self.route()
        proposal = self.reroute_proposal(itinerary)
        with store.connect() as db, db:
            db.execute("CREATE TRIGGER fail_route BEFORE UPDATE OF decision ON adapt_proposals BEGIN SELECT RAISE(ABORT, 'forced failure'); END")
        self.assertEqual(self.decision(proposal).status_code, 500)
        self.assertEqual(self.current(), itinerary)
        with store.connect() as db, db:
            self.assertIsNone(db.execute("SELECT 1 FROM activities WHERE activity_id = 'MOCK-AC'").fetchone())
            db.execute("DROP TRIGGER fail_route")
        self.assertEqual(self.decision(proposal).status_code, 200)



if __name__ == "__main__":
    unittest.main(verbosity=2)
