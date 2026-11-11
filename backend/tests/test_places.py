import importlib
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app
from place_catalog import DATA_DIR, MissingTravelTime, PlaceCatalog
from place_models import DAYS, Place, TravelTime
from places_api import authenticate, get_catalog


def place(identifier, interests, status="MOCK"):
    return Place.model_validate({
        "place_id": identifier, "name": "MOCK " + identifier,
        "area": "DALAT", "interests": interests, "environment": "INDOOR",
        "visit_duration_minutes": 45,
        "opening_hours": {"timezone": "Asia/Ho_Chi_Minh", "weekly": {
            day: [{"start": "08:00", "end": "18:00"}] for day in DAYS}},
        "image_url": None, "source_url": None, "checked_at": None,
        "data_status": status,
    })


def leg(origin, destination, minutes=15):
    return TravelTime.model_validate({
        "travel_time_id": None, "from_place_id": origin, "to_place_id": destination,
        "duration_minutes": minutes, "source_url": None, "checked_at": None,
        "data_status": "MOCK",
    })


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.catalog = PlaceCatalog([
            place("B", ["nature"]), place("A", ["nature", "coffee"]),
            place("C", ["coffee"]), place("D", ["culture"]),
        ], [])

    def test_any_match_rank_multiple_first_and_cap_three(self):
        result = self.catalog.recommend(["nature", "coffee"], include_mock=True)["places"]
        self.assertEqual([item["place_id"] for item in result], ["A", "B", "C"])
        self.assertIn("thiên nhiên và cà phê", result[0]["reason"])

    def test_duplicate_query_interests_do_not_boost_a_score(self):
        self.assertEqual(self.catalog.recommend(["coffee", "nature"], include_mock=True),
                         self.catalog.recommend(["nature", "coffee", "coffee"], include_mock=True))

    def test_one_result_and_no_match(self):
        self.assertEqual(len(self.catalog.recommend(["culture"], include_mock=True)["places"]), 1)
        self.assertEqual(self.catalog.recommend(["food"], include_mock=True), {"places": []})

    def test_mock_data_is_excluded_by_default(self):
        self.assertEqual(self.catalog.recommend(["nature"]), {"places": []})

    def test_change_preferences_changes_results(self):
        self.assertNotEqual(self.catalog.recommend(["coffee"], include_mock=True),
                            self.catalog.recommend(["culture"], include_mock=True))


class APITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        get_catalog.cache_clear()

    def test_missing_or_wrong_auth_scheme_requires_login(self):
        for headers in ({}, {"Authorization": "Basic abc"}):
            with self.subTest(headers=headers):
                response = self.client.get("/api/v1/places/recommendations?interests=nature", headers=headers)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json()["code"], "AUTH_REQUIRED")

    def test_arbitrary_bearer_is_not_accepted_when_auth_is_not_merged(self):
        real_import = importlib.import_module
        def unavailable(name):
            if name == "auth":
                raise ModuleNotFoundError("No auth", name="auth")
            return real_import(name)
        with patch("places_api.import_module", side_effect=unavailable):
            response = self.client.get("/api/v1/places/recommendations?interests=nature",
                                       headers={"Authorization": "Bearer arbitrary"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "AUTH_NOT_READY")

    def test_session_validation_failure_is_propagated(self):
        module = types.SimpleNamespace(session_response=lambda _credentials: JSONResponse(
            status_code=401, content={"code": "INVALID_SESSION", "message": "Invalid"}))
        with patch("places_api.import_module", return_value=module):
            response = self.client.get("/api/v1/places/recommendations?interests=nature",
                                       headers={"Authorization": "Bearer invalid"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "INVALID_SESSION")

    def test_missing_and_invalid_interests_have_contract_error(self):
        app.dependency_overrides[authenticate] = lambda: {"user_id": "TEST-ONLY"}
        for query in ("", "?interests=", "?interests=Nature", "?interests=nature,coffee",
                      "?interests=food&interests=unknown"):
            with self.subTest(query=query):
                response = self.client.get("/api/v1/places/recommendations" + query)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["code"], "VALIDATION_ERROR")
                self.assertEqual(response.json()["field"], "interests")

    def test_success_matches_exact_public_shape(self):
        app.dependency_overrides[authenticate] = lambda: {"user_id": "TEST-ONLY"}
        response = self.client.get("/api/v1/places/recommendations?interests=nature&interests=coffee")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"places"})
        self.assertLessEqual(len(response.json()["places"]), 3)
        self.assertGreater(len(response.json()["places"]), 0)
        for item in response.json()["places"]:
            self.assertEqual(set(item), {"place_id", "name", "image_url", "reason"})
            self.assertIsNone(item["image_url"])

    def test_success_uses_session_verifier(self):
        module = types.SimpleNamespace(session_response=lambda _credentials: {"user_id": "TEST-ONLY"})
        with patch("places_api.import_module", return_value=module):
            response = self.client.get("/api/v1/places/recommendations?interests=culture",
                                       headers={"Authorization": "Bearer test-token"})
        self.assertEqual(response.status_code, 200)

    def test_no_matches_is_200_and_empty_list(self):
        app.dependency_overrides[authenticate] = lambda: {"user_id": "TEST-ONLY"}
        app.dependency_overrides[get_catalog] = lambda: PlaceCatalog([], [])
        response = self.client.get("/api/v1/places/recommendations?interests=food")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"places": []})

    def test_health_still_works(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class DataIntegrityTests(unittest.TestCase):
    def test_duplicate_or_orphan_records_are_rejected(self):
        with self.assertRaises(ValueError):
            PlaceCatalog([place("A", []), place("A", [])], [])
        with self.assertRaises(ValueError):
            PlaceCatalog([place("A", [])], [leg("A", "UNKNOWN")])
        with self.assertRaises(ValueError):
            PlaceCatalog([place("A", []), place("B", [])], [leg("A", "B"), leg("A", "B")])

    def test_missing_direction_is_not_assumed_or_zero(self):
        catalog = PlaceCatalog([place("A", []), place("B", [])], [leg("A", "B", 17)])
        self.assertEqual(catalog.get_travel_time("A", "A"), 0)
        self.assertEqual(catalog.get_travel_time("A", "B", allow_mock=True), 17)
        for origin, destination in (("B", "A"), ("UNKNOWN", "UNKNOWN"), ("A", "UNKNOWN")):
            with self.assertRaises(MissingTravelTime):
                catalog.get_travel_time(origin, destination, allow_mock=True)
        with self.assertRaises(MissingTravelTime):
            catalog.get_travel_time("A", "B")

    def test_unverified_leg_cannot_be_used_for_planning(self):
        item = leg("A", "B").model_copy(update={"data_status": "UNVERIFIED"})
        catalog = PlaceCatalog([place("A", []), place("B", [])], [item])
        with self.assertRaises(MissingTravelTime):
            catalog.get_travel_time("A", "B", allow_mock=True)

    def test_zero_and_negative_travel_times_are_rejected(self):
        for origin, destination, minutes in (("A", "B", 0), ("A", "A", 5), ("A", "B", -1)):
            with self.assertRaises(ValidationError):
                leg(origin, destination, minutes)

    def test_verified_claim_requires_complete_information(self):
        with self.assertRaises(ValidationError):
            place("A", ["culture"], "VERIFIED")

    def test_hours_reject_overlap_or_invalid_times(self):
        for intervals in (
            [{"start": "08:00", "end": "07:00"}],
            [{"start": "25:00", "end": "26:00"}],
            [{"start": "08:00", "end": "12:00"}, {"start": "11:00", "end": "17:00"}],
        ):
            raw = place("A", []).model_dump()
            raw["opening_hours"]["weekly"]["mon"] = intervals
            with self.assertRaises(ValidationError):
                Place.model_validate(raw)

    def test_shipped_catalog_and_mock_fixtures_load_independently(self):
        real = PlaceCatalog.load()
        mock = PlaceCatalog.load(DATA_DIR / "fixtures" / "mock")
        self.assertTrue(real.places)
        self.assertTrue(real.travel_times)
        self.assertTrue(all(p.data_status != "MOCK" for p in real.places.values()))
        self.assertTrue(all(p.data_status == "MOCK" for p in mock.places.values()))
        self.assertTrue(set(real.places).isdisjoint(mock.places))


class FixtureTests(unittest.TestCase):
    def test_rest_demo_arithmetic_and_infeasible_case(self):
        catalog = PlaceCatalog.load(DATA_DIR / "fixtures" / "mock")
        travel = lambda a, b: catalog.get_travel_time(a, b, allow_mock=True)
        rest, a, b, end = "MOCK-REST", "MOCK-A03", "MOCK-A04", "MOCK-END"
        keep_both = 15 * 60 + travel(rest, a) + 45 + travel(a, b) + 45 + travel(b, end)
        keep_a = 15 * 60 + travel(rest, a) + 45 + travel(a, end)
        keep_b = 15 * 60 + travel(rest, b) + 45 + travel(b, end)
        self.assertEqual(keep_both, 17 * 60 + 15)
        self.assertEqual(keep_a, 16 * 60 + 15)
        self.assertEqual(keep_b, 16 * 60 + 15)
        self.assertGreater(16 * 60 + 30 + travel(rest, end), 16 * 60 + 30)

    def test_rain_fixture_has_valid_and_closed_indoor_candidates(self):
        catalog = PlaceCatalog.load(DATA_DIR / "fixtures" / "mock")
        open_place = catalog.places["MOCK-INDOOR"]
        closed_place = catalog.places["MOCK-CLOSED"]
        self.assertEqual(open_place.environment, "INDOOR")
        self.assertTrue(all(open_place.opening_hours.weekly.values()))
        self.assertTrue(all(intervals == [] for intervals in closed_place.opening_hours.weekly.values()))
        scenarios = json.loads((DATA_DIR / "fixtures" / "scenarios.json").read_text(encoding="utf-8"))
        self.assertEqual({s["test_id"] for s in scenarios}, {"T06", "T08", "T13", "T15"})


if __name__ == "__main__":
    unittest.main()
