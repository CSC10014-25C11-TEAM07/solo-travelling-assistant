"""Readiness must account for venue windows, visits and every directed leg."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_handoff import source_route
from place_catalog import PlaceCatalog
from place_models import DAYS, Place, TravelTime


def inputs():
    places = []
    for pid, area in (("H", "HCMC"), ("A", "DALAT"), ("B", "DALAT")):
        places.append(Place.model_validate({
            "place_id": pid, "name": pid, "area": area, "interests": ["culture"],
            "environment": "INDOOR", "visit_duration_minutes": 60,
            "opening_hours": {"timezone": "Asia/Ho_Chi_Minh", "weekly": {
                d: [{"start": "06:00", "end": "20:00"}] for d in DAYS}},
            "image_url": None, "source_url": "https://example.com/venue",
            "checked_at": "2026-11-15T00:00:00Z", "data_status": "VERIFIED"}))
    legs = [TravelTime.model_validate({
        "travel_time_id": None, "from_place_id": a, "to_place_id": b,
        "duration_minutes": 15, "source_url": "https://example.com/route",
        "checked_at": "2026-11-15T00:00:00Z", "data_status": "VERIFIED"})
        for a, b in (("H", "A"), ("A", "H"), ("A", "B"), ("B", "A"))]
    route = {"route_id": "TEST-3D", "data_status": "VERIFIED",
             "departure_date": "2026-12-14", "return_date": "2026-12-16",
             "min_rest_minutes": 60, "limitations": [], "days": []}
    for n, sequence in enumerate((["H", "A"], ["A", "B", "A"], ["A", "H"]), 1):
        route["days"].append({
            "day_id": f"D{n}", "day_number": n, "date": f"2026-12-{13+n}",
            "start_place_id": sequence[0], "end_place_id": sequence[-1],
            "start_time": "08:00", "end_deadline": "17:00", "place_sequence": sequence,
            "visit_place_ids": ["B"] if n == 2 else [],
            "rest_stops": [{"place_id": "A", "duration_minutes": 60}]})
    return route, PlaceCatalog(places, legs)


class SourceReadinessTests(unittest.TestCase):
    def codes(self, result):
        return {gap["code"] for gap in result["gaps"]}

    def test_complete_route_reports_earliest_visit_rest_and_travel_schedule(self):
        route, catalog = inputs()
        result = source_route(route, catalog)
        self.assertTrue(result["ready_for_real_plan"], result)
        day = result["days"][1]
        self.assertEqual(day["conditional_earliest_finish"], "10:30")
        self.assertEqual(day["known_visit_minutes"], 60)
        self.assertEqual([a["type"] for a in day["earliest_schedule"]], ["REST", "TRAVEL", "VISIT", "TRAVEL"])

    def test_visits_are_included_before_calling_a_route_ready(self):
        route, catalog = inputs()
        route["days"][1]["end_deadline"] = "10:00"
        result = source_route(route, catalog)
        self.assertFalse(result["ready_for_real_plan"], result)
        self.assertIn("LOWER_BOUND_LATE", self.codes(result))

    def test_waits_for_next_window_without_counting_wait_as_rest(self):
        route, catalog = inputs()
        raw = catalog.places["B"].model_dump()
        raw["opening_hours"]["weekly"]["tue"] = [
            {"start": "08:00", "end": "09:00"}, {"start": "13:00", "end": "17:00"}]
        # Assignment must go through Pydantic so this fixture stays realistic.
        catalog.places["B"] = Place.model_validate(raw)
        route["days"][1]["end_deadline"] = "14:00"
        result = source_route(route, catalog)
        self.assertFalse(result["ready_for_real_plan"], result)
        self.assertIn("SCHEDULE_LATE", self.codes(result))
        self.assertEqual(result["days"][1]["conditional_earliest_finish"], "14:15")

    def test_closed_rest_venue_blocks_readiness(self):
        route, catalog = inputs()
        catalog.places["A"].opening_hours.weekly["tue"] = []
        result = source_route(route, catalog)
        self.assertFalse(result["ready_for_real_plan"], result)
        self.assertIn("NO_REST_WINDOW", self.codes(result))

    def test_rest_or_visit_cannot_be_outside_the_route(self):
        for field, value in (("rest_stops", [{"place_id": "H", "duration_minutes": 60}]),
                             ("visit_place_ids", ["H"])):
            route, catalog = inputs()
            route["days"][1][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "STOP_OUTSIDE_ROUTE"):
                source_route(route, catalog)

    def test_missing_return_leg_not_filled_by_reverse(self):
        route, catalog = inputs()
        del catalog.travel_times[("B", "A")]
        result = source_route(route, catalog)
        self.assertFalse(result["ready_for_real_plan"])
        self.assertIn({"code": "MISSING_LEG", "day_id": "D2", "from_place_id": "B", "to_place_id": "A"}, result["gaps"])
        self.assertIsNone(result["days"][1]["conditional_earliest_finish"])

    def test_wrong_dates_or_date_range_are_rejected(self):
        for field in ("date", "return_date"):
            route, catalog = inputs()
            if field == "date":
                route["days"][1]["date"] = "2026-12-16"
            else:
                route["return_date"] = "2026-12-17"
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "SOURCE_DATE"):
                source_route(route, catalog)

    def test_explicit_route_limitations_do_not_disappear_with_verified_label(self):
        route, catalog = inputs()
        route["limitations"] = ["No lodging connectors yet"]
        result = source_route(route, catalog)
        self.assertFalse(result["ready_for_real_plan"], result)
        self.assertIn("UNRESOLVED_ROUTE_LIMITATION", self.codes(result))

    def test_rain_checks_all_edges_including_final_endpoint(self):
        from source_readiness import source_replacements
        _, catalog = inputs()
        case = {"check_id": "RAIN-LAST", "replacement_place_id": "B",
                "place_sequence": ["A", "B", "H"]}
        report, = source_replacements([case], catalog)
        self.assertFalse(report["ready_for_real_adapt"])
        self.assertEqual(report["missing_pairs"], [{"from_place_id": "B", "to_place_id": "H"}])
        self.assertEqual(len(report["legs"]), 2)

    def test_rain_mixed_venue_is_not_an_indoor_replacement(self):
        from source_readiness import source_replacements
        _, catalog = inputs()
        catalog.places["B"].environment = "MIXED"
        report, = source_replacements([{"check_id": "RAIN", "replacement_place_id": "B",
                                       "place_sequence": ["A", "B", "A"]}], catalog)
        self.assertFalse(report["ready_for_real_adapt"])
        self.assertIn("REPLACEMENT_NOT_INDOOR", self.codes(report))


if __name__ == "__main__":
    unittest.main()
