"""F02 provider integration with fixed fixtures and a fake model."""

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapt_f05.catalog import Catalog, RouteDay
from adapt_f05.ranking import RuleRanker, RankingError
from adapt_f05.demo import demo_inputs
from f05_provider import create_proposal, make_catalog_provider, make_option_validator
from itinerary_api import APIError, DraftInput, validate_plan
from plan_f02 import PlanProvider, mock_templates

DATA = Path(__file__).resolve().parents[1] / "data"


def read(path):
    return json.loads((DATA / path).read_text(encoding="utf-8-sig"))


class FakeModel(RuleRanker):
    mode = "MOCK_AI"

    def __init__(self):
        self.calls = 0

    def rank(self, context):
        self.calls += 1
        return super().rank(context)


class PlanProviderTests(unittest.TestCase):
    def setUp(self):
        routes = read("handoff/routes_mock.json")
        snapshots = {route["route_id"]: read(route["snapshot"]) for route in routes}
        self.templates = mock_templates(routes, snapshots)
        route_days = [RouteDay(**{key: row[key] for key in RouteDay.__dataclass_fields__})
                      for route in routes for row in route["days"]]
        self.catalog = Catalog.load(DATA / "fixtures/mock", route_days, mode="MOCK")
        self.model = FakeModel()
        self.provider = PlanProvider(self.catalog, self.templates, ranker=self.model)

    def request(self, days):
        return DraftInput(departure_date="2026-11-12", return_date=f"2026-11-{11 + days}",
                          departure_time="06:00", interests=["coffee", "nature"], min_rest_minutes=60)

    def test_three_and_four_day_provider_contract(self):
        for count in (3, 4):
            with self.subTest(days=count):
                request = self.request(count)
                result = self.provider(request)
                validate_plan(request, result)
                self.assertEqual(len(result), count)
                self.assertTrue(any(a["type"] == "VISIT" for day in result for a in day["activities"]))
                for day in result:
                    self.assertTrue(any(a["type"] == "REST" for a in day["activities"]))
                    self.assertTrue(any(a["type"] == "TRAVEL" for a in day["activities"]))
                    self.assertNotIn("day_id", day)
        self.assertEqual(self.model.calls, 2)

    def test_missing_directed_leg_does_not_infer_reverse_or_call_ai(self):
        self.catalog.travel_times.pop(("MOCK-HCM", "MOCK-ROAD-REST"))
        with self.assertRaises(APIError) as error:
            self.provider(self.request(3))
        self.assertEqual(error.exception.code, "DATA_INCOMPLETE")
        self.assertIn("MOCK-HCM -> MOCK-ROAD-REST", error.exception.message)
        self.assertEqual(self.model.calls, 0)

    def test_insufficient_rest_and_deadline_are_not_relaxed(self):
        for field in ("rest", "deadline"):
            with self.subTest(field=field):
                templates = deepcopy(self.templates)
                if field == "rest":
                    templates[3]["days"][0]["stops"][0]["duration_minutes"] = 30
                else:
                    templates[3]["days"][0]["end_deadline"] = "07:00"
                with self.assertRaises(APIError) as error:
                    PlanProvider(self.catalog, templates, ranker=self.model)(self.request(3))
                self.assertEqual(error.exception.code, "NO_FEASIBLE_ITINERARY")

    def test_ai_failure_and_invalid_output_are_not_mocked(self):
        class Broken:
            def rank(self, context):
                raise RankingError("AI_TIMEOUT", "timeout", 504)

        with self.assertRaises(APIError) as error:
            PlanProvider(self.catalog, self.templates, ranker=Broken())(self.request(3))
        self.assertEqual(error.exception.code, "AI_TIMEOUT")

        class Invented:
            def rank(self, context):
                return {"rankings": [{"candidate_id": "invented", "reason_codes": ["VALID"],
                                      "tradeoff_code": "TRADEOFF"}]}

        with self.assertRaises(APIError) as error:
            PlanProvider(self.catalog, self.templates, ranker=Invented())(self.request(3))
        self.assertEqual(error.exception.code, "AI_INVALID_OUTPUT")

    def test_unverified_route_and_venue_are_refused(self):
        templates = deepcopy(self.templates)
        templates[3]["data_status"] = "UNVERIFIED"
        with self.assertRaises(APIError) as error:
            PlanProvider(self.catalog, templates, ranker=self.model)(self.request(3))
        self.assertEqual(error.exception.code, "DATA_INCOMPLETE")
        self.catalog.places["MOCK-ROAD-REST"]["data_status"] = "UNVERIFIED"
        with self.assertRaises(APIError) as error:
            self.provider(self.request(3))
        self.assertIn("MOCK-ROAD-REST", error.exception.message)

    def test_f05_callback_uses_strict_model_and_fresh_catalog(self):
        trip, catalog = demo_inputs()
        payload = {"type": "REPLACE_LOCATION", "base_version": 1, "activity_id": "A03", "reason": "RAIN"}
        model = FakeModel()
        public, stored = create_proposal(trip, payload, lambda current: catalog, lambda: model)
        self.assertEqual(model.calls, 1)
        self.assertEqual(public["proposal_id"], stored["proposal_id"])
        validator = make_option_validator(lambda current: catalog)
        self.assertTrue(validator(trip, stored["options"][0]))
        self.assertFalse(validator(trip, public["options"][0]))
        catalog.places["MOCK-INDOOR"]["opening_hours"]["weekly"]["fri"] = []
        self.assertFalse(validator(trip, stored["options"][0]))

    def test_f05_catalog_maps_stored_ids_and_rejects_deadline_drift(self):
        routes = read("handoff/routes_mock.json")
        trip = read(routes[0]["snapshot"])
        provider = make_catalog_provider(DATA / "fixtures/mock", {3: routes[0]}, mode="MOCK")
        catalog = provider(trip)
        self.assertEqual(catalog.routes[trip["days"][1]["day_id"]].end_place_id, "MOCK-END")
        trip["days"][1]["end_deadline"] = "23:59"
        with self.assertRaises(ValueError):
            provider(trip)

    def test_f05_model_failure_propagates_without_fallback(self):
        trip, catalog = demo_inputs()
        payload = {"type": "REPLACE_LOCATION", "base_version": 1, "activity_id": "A03", "reason": "RAIN"}
        class Broken:
            def rank(self, context):
                raise RankingError("AI_TIMEOUT", "timeout", 504)
        with self.assertRaises(APIError) as error:
            create_proposal(trip, payload, lambda current: catalog, Broken)
        self.assertEqual((error.exception.code, error.exception.status), ("AI_TIMEOUT", 504))

    def test_provider_runs_via_public_draft_api(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from fastapi.testclient import TestClient
        import auth
        from main import create_app

        with TemporaryDirectory() as directory, patch.object(auth, "DB_PATH", Path(directory) / "test.sqlite3"):
            with TestClient(create_app(plan_provider=self.provider)) as client:
                credentials = {"username": "plan_test", "password": "temporary-password-123"}
                self.assertEqual(client.post("/api/v1/auth/register", json=credentials).status_code, 201)
                login = client.post("/api/v1/auth/login", json=credentials)
                headers = {"Authorization": "Bearer " + login.json()["access_token"]}
                payload = {"departure_date": "2026-11-12", "return_date": "2026-11-14",
                           "departure_time": "06:00", "interests": ["nature"], "min_rest_minutes": 60}
                response = client.post("/api/v1/itinerary-drafts", json=payload, headers=headers)
                self.assertEqual(response.status_code, 201, response.text)
                draft = response.json()
                self.assertEqual(draft["draft_id"], draft["itinerary"]["itinerary_id"])
                response = client.post(f"/api/v1/itinerary-drafts/{draft['draft_id']}/confirm", headers=headers)
                self.assertEqual(response.status_code, 200, response.text)
                current = client.get("/api/v1/itineraries/current", headers=headers).json()["itinerary"]
                self.assertEqual(len(current["days"]), 3)
                self.assertEqual(current["status"], "CURRENT")


if __name__ == "__main__":
    unittest.main()
