"""Regressions for TASK17 buffer, REST hours and anchor access; no network/SQLite."""

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapt_f05.catalog import Catalog, RouteDay, minutes
from adapt_f05.demo import demo_inputs
from adapt_f05.engine import AdaptEngine, validate_candidate
from adapt_f05.models import AdaptError
from adapt_f05.ranking import RuleRanker
from f05_provider import make_catalog_provider
from itinerary_api import APIError, DraftInput
from plan_f02 import PlanProvider

DATA = Path(__file__).resolve().parents[1] / "data"
WEEK = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
RAIN = {"type": "REPLACE_LOCATION", "base_version": 1, "activity_id": "A03", "reason": "RAIN"}
REST = {"type": "EXTEND_REST", "base_version": 1, "rest_activity_id": "REST", "rest_until": "15:00"}


class CountingRanker(RuleRanker):
    def __init__(self):
        self.calls = 0

    def rank(self, context):
        self.calls += 1
        return super().rank(context)


def hours(start="07:00", end="18:00"):
    return {"timezone": "Asia/Ho_Chi_Minh", "weekly": {
        day: [{"start": start, "end": end}] for day in WEEK}}


class PlanConstraintTests(unittest.TestCase):
    def setUp(self):
        # Controlled test records, explicitly MOCK; never promote source data.
        places = [{"place_id": key, "name": key, "data_status": "MOCK",
                   "opening_hours": hours(), "visit_duration_minutes": None} for key in ("A", "R")]
        legs = [{"from_place_id": a, "to_place_id": b, "duration_minutes": 10,
                 "data_status": "MOCK"} for a, b in (("A", "R"), ("R", "A"))]
        self.catalog = Catalog(places, legs, [], mode="MOCK")
        self.templates = {3: {"route_id": "SYNTHETIC-3D", "data_status": "MOCK", "days": [
            {"start_place_id": "A", "end_place_id": "A", "start_time": "09:00",
             "end_deadline": "10:35", "stops": [{"type": "REST", "place_id": "R", "duration_minutes": 60}]}
            for _ in range(3)]}}
        self.ranker = CountingRanker()
        self.request = DraftInput(departure_date="2026-11-17", return_date="2026-11-19",
                                  departure_time="08:00", interests=["nature"], min_rest_minutes=60)

    def run_plan(self):
        return PlanProvider(self.catalog, self.templates, ranker=self.ranker)(self.request)

    def test_buffer_is_reserved_separately_from_rest(self):
        self.assertEqual(self.run_plan()[0]["activities"][-1]["end_time"], "10:20")
        self.templates[3]["buffer_minutes"] = 30
        with self.assertRaises(APIError) as error:
            self.run_plan()
        self.assertEqual(error.exception.code, "NO_FEASIBLE_ITINERARY")
        self.assertEqual(self.ranker.calls, 1)
        # Exact deadline with the full buffer succeeds, no artificial REST added.
        for day in self.templates[3]["days"]:
            day["end_deadline"] = "10:50"
        result = self.run_plan()
        self.assertEqual(result[0]["activities"][-1]["end_time"], "10:20")
        rest = [a for a in result[0]["activities"] if a["type"] == "REST"]
        self.assertEqual(sum(minutes(a["end_time"]) - minutes(a["start_time"]) for a in rest), 60)

    def test_bad_buffers_are_data_errors_before_ai(self):
        for value in (-1, True, 1.5, "30", None, 1440):
            with self.subTest(value=value):
                self.templates[3]["buffer_minutes"] = value
                with self.assertRaises(APIError) as error:
                    self.run_plan()
                self.assertEqual(error.exception.code, "DATA_INCOMPLETE")
        self.assertEqual(self.ranker.calls, 0)

    def test_closed_and_unknown_rest_hours_are_distinct(self):
        for value, code in (([], "NO_FEASIBLE_ITINERARY"), (None, "DATA_INCOMPLETE")):
            self.catalog.places["R"]["opening_hours"]["weekly"]["tue"] = value
            with self.subTest(value=value), self.assertRaises(APIError) as error:
                self.run_plan()
            self.assertEqual(error.exception.code, code)
        self.assertEqual(self.ranker.calls, 0)

    def test_rest_waits_until_open_and_wait_does_not_count_as_rest(self):
        self.catalog.places["R"]["opening_hours"] = hours("09:30", "18:00")
        for day in self.templates[3]["days"]:
            day["end_deadline"] = "11:00"
        rest = self.run_plan()[0]["activities"][1]
        self.assertEqual((rest["start_time"], rest["end_time"]), ("09:30", "10:30"))

    def test_rest_cannot_cross_lunch_closure(self):
        self.catalog.places["R"]["opening_hours"]["weekly"]["tue"] = [
            {"start": "08:00", "end": "09:30"}, {"start": "10:00", "end": "18:00"}]
        with self.assertRaises(APIError) as error:
            self.run_plan()
        self.assertEqual(error.exception.code, "NO_FEASIBLE_ITINERARY")
        self.assertEqual(self.ranker.calls, 0)

    def test_departure_waits_for_access_but_end_anchor_must_be_open_on_arrival(self):
        for day in self.templates[3]["days"]:
            day.update(start_time="06:00", end_deadline="10:35")
        self.request.departure_time = "06:00"
        self.assertEqual(self.run_plan()[0]["activities"][0]["start_time"], "07:00")
        self.catalog.places["A"]["opening_hours"] = hours("07:00", "08:00")
        with self.assertRaises(APIError) as error:
            self.run_plan()
        self.assertEqual(error.exception.code, "NO_FEASIBLE_ITINERARY")

    def test_closed_or_unknown_anchor_does_not_assume_all_day_access(self):
        for value, code in (([], "NO_FEASIBLE_ITINERARY"), (None, "DATA_INCOMPLETE")):
            self.catalog.places["A"]["opening_hours"]["weekly"]["tue"] = value
            with self.subTest(value=value), self.assertRaises(APIError) as error:
                self.run_plan()
            self.assertEqual(error.exception.code, code)
        self.assertEqual(self.ranker.calls, 0)


class AdaptConstraintTests(unittest.TestCase):
    def setUp(self):
        self.trip, self.catalog = demo_inputs()
        self.before = deepcopy(self.trip)
        self.ranker = CountingRanker()

    def generate(self, payload):
        return AdaptEngine(self.catalog, ranker=self.ranker, allow_ai_fallback=False).generate(self.trip, payload)

    def test_rain_reserves_buffer_before_ranking_and_buffer_change_invalidates_option(self):
        candidate = self.generate(RAIN).candidates[0]
        self.assertTrue(validate_candidate(self.trip, candidate, self.catalog))
        self.catalog.buffer_minutes_by_day["MOCK-DAY-2"] = 30
        self.assertFalse(validate_candidate(self.trip, candidate, self.catalog))
        result = self.generate(RAIN)
        self.assertEqual(result.candidates, [])
        self.assertEqual(self.ranker.calls, 1)
        self.assertIn("dự phòng", result.no_option_reason)
        self.assertEqual(self.trip, self.before)

    def test_rest_may_drop_more_visits_to_keep_buffer(self):
        self.catalog.buffer_minutes_by_day["MOCK-DAY-2"] = 30
        result = self.generate(REST)
        self.assertTrue(result.candidates)
        for candidate in result.candidates:
            self.assertLessEqual(minutes(candidate.estimated_end_time) + 30, minutes("16:30"))
            self.assertTrue(validate_candidate(self.trip, candidate, self.catalog))

    def test_extended_rest_cannot_move_its_start_or_cross_closure(self):
        self.catalog.places["MOCK-REST"]["opening_hours"] = hours("07:00", "14:30")
        result = self.generate(REST)
        self.assertEqual(result.candidates, [])
        self.assertEqual(self.ranker.calls, 0)
        self.assertEqual(self.trip, self.before)

    def test_rain_rechecks_unchanged_pending_rest_prefix(self):
        self.catalog.places["MOCK-REST"]["opening_hours"]["weekly"]["fri"] = []
        result = self.generate(RAIN)
        self.assertEqual(result.candidates, [])
        self.assertEqual(self.ranker.calls, 0)

    def test_end_anchor_must_allow_arrival(self):
        self.catalog.places["MOCK-END"]["opening_hours"] = hours("07:00", "16:00")
        result = self.generate(RAIN)
        self.assertEqual(result.candidates, [])
        self.assertEqual(self.ranker.calls, 0)
        self.assertIn("tiếp cận", result.no_option_reason)

    def test_done_rows_are_history_even_if_catalog_hours_changed(self):
        self.catalog.places["MOCK-GA"]["opening_hours"]["weekly"]["fri"] = []
        result = self.generate(RAIN)
        self.assertTrue(result.candidates)
        done = {a["activity_id"]: a for day in self.trip["days"] for a in day["activities"] if a["status"] == "DONE"}
        for candidate in result.candidates:
            actual = {a["activity_id"]: a for day in candidate.proposed_days for a in day["activities"] if a["status"] == "DONE"}
            self.assertEqual(actual, done)
        self.assertEqual(self.trip, self.before)

    def test_catalog_provider_binds_route_buffer_to_real_day_ids(self):
        routes = json.loads((DATA / "handoff/routes_mock.json").read_text(encoding="utf-8"))
        route = routes[0]
        trip = json.loads((DATA / route["snapshot"]).read_text(encoding="utf-8"))
        original = make_catalog_provider(DATA / "fixtures/mock", {3: route}, mode="MOCK")(trip)
        route["buffer_minutes"] = 30
        configured = make_catalog_provider(DATA / "fixtures/mock", {3: route}, mode="MOCK")(trip)
        self.assertEqual(configured.buffer_minutes_by_day, {day["day_id"]: 30 for day in trip["days"]})
        self.assertNotEqual(configured.version, original.version)
        for bad in (-1, True, "30"):
            route["buffer_minutes"] = bad
            with self.assertRaises(AdaptError):
                make_catalog_provider(DATA / "fixtures/mock", {3: route}, mode="MOCK")(trip)

    def test_catalog_rejects_buffer_for_unknown_day(self):
        with self.assertRaises(AdaptError):
            Catalog([], [], [], mode="MOCK", buffer_minutes_by_day={"unknown": 30})


if __name__ == "__main__":
    unittest.main()
