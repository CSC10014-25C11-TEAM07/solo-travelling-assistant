"""Offline acceptance using the published real routes and a deterministic AI test double."""
from contextlib import ExitStack
from datetime import date, timedelta
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth
from adapt_f05.ranking import GeminiRanker, MockRanker, RuleRanker
from main import configured_app


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        stack = self.enterContext(ExitStack())
        tmp = stack.enter_context(tempfile.TemporaryDirectory())
        stack.enter_context(patch.object(auth, "DB_PATH", Path(tmp) / "app.sqlite"))
        stack.enter_context(patch.dict(os.environ, ADAPT_MODE="VERIFIED"))
        stack.enter_context(patch.object(GeminiRanker, "__init__", return_value=None))
        self.rank = stack.enter_context(patch.object(GeminiRanker, "rank", autospec=True,
                                                     side_effect=RuleRanker.rank))
        self.app = configured_app()
        self.client = stack.enter_context(TestClient(self.app))
        self.owner = self.headers("android_owner")
        self.other = self.headers("android_other")

    def headers(self, name):
        account = {"username": name, "password": "temporary-acceptance-passphrase"}
        self.assertEqual(self.client.post("/api/v1/auth/register", json=account).status_code, 201)
        response = self.client.post("/api/v1/auth/login", json=account)
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    def post(self, path, body, status=200, headers=None):
        res = self.client.post("/api/v1/" + path, headers=headers or self.owner, json=body)
        self.assertEqual(res.status_code, status, res.text)
        return res.json()

    def current(self, headers=None):
        return self.client.get("/api/v1/itineraries/current", headers=headers or self.owner).json()["itinerary"]

    def plan(self, days, start=date(2026, 12, 14)):
        data = dict(departure_date=start.isoformat(), return_date=(start+timedelta(days=days-1)).isoformat(),
                    departure_time="06:00", min_rest_minutes=60, interests=["nature", "coffee"])
        draft = self.post("itinerary-drafts", data, 201)
        return self.post(f"itinerary-drafts/{draft['draft_id']}/confirm", {})["itinerary"]

    def test_both_lengths_weekdays_preferences_and_persistence(self):
        for start in range(7):
            for count in (3, 4):
                trip = self.plan(count, date(2026,12,14) + timedelta(days=start))
                self.assertEqual(len(trip["days"]), count)
                self.assertEqual(trip["days"][-1]["activities"][-1]["type"], "TRAVEL")
                self.assertIn("Công trường Công xã Paris", trip["days"][-1]["activities"][-1]["name"])
                self.assertTrue(all("MOCK" not in a["name"] for d in trip["days"] for a in d["activities"]))
                contexts = self.rank.call_args.args[-1]
                self.assertGreaterEqual(len(contexts["candidates"]), 2)
                self.assertEqual(contexts["interests"], ["nature", "coffee"])
        with TestClient(configured_app()) as restarted:
            restored = restarted.get("/api/v1/itineraries/current", headers=self.owner).json()["itinerary"]
            self.assertEqual(restored["itinerary_id"], trip["itinerary_id"])
            self.assertEqual(restored["days"], trip["days"])
            self.assertEqual(restored["outdoor_place_ids"], ["P003"])

    def test_accept_reject_replay_and_restore_personal_trip(self):
        personal = self.plan(4)
        selection = dict(itinerary_id=personal["itinerary_id"], version=1)
        for kind in ("EXTEND_REST", "REPLACE_LOCATION"):
            sample = self.post("demo-itineraries", selection, 201)["itinerary"]
            self.assertTrue(sample["is_demo_sample"])
            self.post("demo-itineraries", selection, 409)
            self.assertIsNone(self.current(self.other))
            day = sample["days"][1]
            morning = [a for a in day["activities"] if a["status"] == "DONE"]
            self.assertTrue(morning)
            lunch = next(a for a in day["activities"] if a["type"] == "REST")
            lake = next(a for a in day["activities"] if a["place_id"] == "P003")
            change = ({"rest_activity_id": lunch["activity_id"], "rest_until": "15:00"}
                      if kind == "EXTEND_REST" else {"activity_id": lake["activity_id"], "reason": "RAIN"})
            path = f"itineraries/{sample['itinerary_id']}/adapt-proposals"
            def propose():
                result = self.post(path, dict(type=kind, base_version=1, **change), 201)
                self.assertTrue(result["options"], result)
                return result
            proposal = propose()
            if kind == "EXTEND_REST":
                self.assertEqual(len(proposal["options"]), 2)
            decision = f"adapt-proposals/{proposal['proposal_id']}/decision"
            self.post(decision, {"decision":"REJECT"})
            self.assertEqual(self.current()["days"], sample["days"])
            self.assertEqual(self.current()["version"], 1)
            proposal = propose()
            decision = f"adapt-proposals/{proposal['proposal_id']}/decision"
            choice = {"decision": "ACCEPT", "option_id": proposal["options"][0]["option_id"]}
            self.post(decision, choice)
            self.post(decision, choice)
            saved = self.current()
            self.assertEqual(saved["version"], 2)
            after = saved["days"][1]["activities"]
            self.assertEqual([a for a in after if a["status"]=="DONE"], morning)
            self.assertEqual(saved["days"][0], sample["days"][0])
            self.assertEqual(saved["days"][2], sample["days"][2])
            if kind == "EXTEND_REST":
                self.assertEqual(next(a["end_time"] for a in after if a["type"]=="REST"), "15:00")
                self.assertTrue(any(a["status"]=="DROPPED" for a in after))
            else:
                self.assertTrue(any(a["place_id"]=="P006" and a["status"]=="PENDING" for a in after))
                self.assertTrue(any(a["place_id"]=="P003" and a["status"]=="REPLACED" for a in after))
            self.assertTrue(any(a["type"]=="TRAVEL" and a["status"]=="REPLACED" for a in after))
            self.post("demo-itineraries/close", dict(itinerary_id=saved["itinerary_id"], version=2))
            self.assertEqual(self.current()["itinerary_id"], personal["itinerary_id"])
            self.assertEqual(self.current()["days"], personal["days"])

    def test_requested_activity_stays_first_when_model_reverses_options(self):
        self.rank.side_effect = lambda _ranker, context: MockRanker().rank(context)
        sample = self.post("demo-itineraries", {"itinerary_id": None, "version": None}, 201)["itinerary"]
        day = sample["days"][1]
        lunch = next(a for a in day["activities"] if a["type"] == "REST")
        visits = [a for a in day["activities"] if a["type"] == "VISIT" and a["status"] == "PENDING"]
        self.assertEqual(len(visits), 2)
        for preferred in visits:
            proposal = self.post(f"itineraries/{sample['itinerary_id']}/adapt-proposals", {
                "type": "EXTEND_REST", "base_version": sample["version"],
                "rest_activity_id": lunch["activity_id"], "rest_until": "15:00",
                "preferred_keep_activity_id": preferred["activity_id"],
            }, 201)
            first = proposal["options"][0]
            updated = next(a for d in first["proposed_days"] for a in d["activities"]
                           if a["activity_id"] == preferred["activity_id"])
            self.assertEqual(updated["status"], "PENDING")
            self.assertIn("ưu tiên", first["reason"])

    def test_rain_without_open_indoor_venue_keeps_current_itinerary(self):
        sample = self.post("demo-itineraries", {"itinerary_id": None, "version": None}, 201)["itinerary"]
        lake = next(a for a in sample["days"][1]["activities"] if a["place_id"] == "P003")
        actual_provider = self.app.state.catalog_provider

        def closed_catalog(itinerary):
            catalog = actual_provider(itinerary)
            catalog.places["P006"]["opening_hours"]["weekly"] = {
                day: [] for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
            }
            return catalog

        self.app.state.catalog_provider = closed_catalog
        calls = self.rank.call_count
        result = self.post(f"itineraries/{sample['itinerary_id']}/adapt-proposals", {
            "type": "REPLACE_LOCATION", "base_version": sample["version"],
            "activity_id": lake["activity_id"], "reason": "RAIN",
        }, 201)
        self.assertEqual(result["options"], [])
        self.assertTrue(result["no_option_reason"])
        self.assertEqual(self.rank.call_count, calls)
        saved = self.current()
        self.assertEqual(saved["version"], sample["version"])
        self.assertEqual(saved["days"], sample["days"])
