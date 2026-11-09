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


if __name__ == "__main__":
    unittest.main(verbosity=2)
