"""Source cases must audit changed REST/RAIN days without inventing a CURRENT."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_handoff import audit
from place_catalog import DATA_DIR
from place_models import Place, TravelTime
from source_bundle import export_source_bundle
from test_source_readiness import inputs


class SourceScenarioTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data = Path(self.temporary.name) / "data"
        shutil.copytree(DATA_DIR, self.data)
        route, catalog = inputs()
        catalog.places["B"].environment = "MIXED"
        candidate = catalog.places["B"].model_dump()
        candidate.update(place_id="C", name="Indoor candidate", environment="INDOOR", visit_duration_minutes=45)
        catalog.places["C"] = Place.model_validate(candidate)
        legs = list(catalog.travel_times.values())
        for origin, destination in (("A", "C"), ("C", "A")):
            raw = legs[0].model_dump()
            raw.update(from_place_id=origin, to_place_id=destination, duration_minutes=10)
            legs.append(TravelTime.model_validate(raw))
        self.write("places.json", [p.model_dump() for p in catalog.places.values()])
        self.write("travel_times.json", [leg.model_dump() for leg in legs])
        four = deepcopy(route)
        four.update(route_id="TEST-4D", return_date="2026-12-17")
        four["days"].insert(2, deepcopy(four["days"][1]))
        for number, day in enumerate(four["days"], 1):
            day.update(day_id=f"F{number}", day_number=number, date=f"2026-12-{13+number}")
        route["days"][1]["end_deadline"] = "10:45"
        self.write("handoff/routes_source.json", [route, four])
        self.write("handoff/source_adapt_checks.json", [{
            "check_id": "INDOOR-C", "replacement_place_id": "C", "place_sequence": ["A", "C", "A"]}])
        self.cases = []
        for rid, did in (("TEST-3D", "D2"), ("TEST-4D", "F2")):
            self.cases.extend([
                {"case_id": f"REST-{rid}", "route_id": rid, "day_id": did,
                 "type": "EXTEND_REST", "rest_place_id": "A", "extra_rest_minutes": 30},
                {"case_id": f"RAIN-{rid}", "route_id": rid, "day_id": did,
                 "type": "REPLACE_LOCATION", "reason": "RAIN",
                 "visit_place_id": "B", "replacement_place_id": "C"}])
        manifest = json.loads((self.data / "handoff/manifest.json").read_text())
        manifest["source_scenarios"] = "handoff/source_scenarios.json"
        self.write("handoff/manifest.json", manifest)
        self.write("handoff/source_scenarios.json", self.cases)

    def write(self, name, value):
        (self.data / name).write_text(json.dumps(value, ensure_ascii=False) + "\n")

    def results(self):
        report = audit(self.data)
        cases = report.get("source_scenarios")
        self.assertIsNotNone(cases, "Audit ignored the configured source REST/RAIN cases")
        return {case["case_id"]: case for case in cases}

    def test_extra_rest_is_included_before_reporting_time_coverage(self):
        case = self.results()["REST-TEST-3D"]
        self.assertEqual(case["baseline"]["conditional_earliest_finish"], "10:30")
        self.assertEqual(case["changed"]["conditional_earliest_finish"], "11:00")
        self.assertFalse(case["source_data_complete"])
        self.assertIn("SCHEDULE_LATE", {g["code"] for g in case["gaps"]})

    def test_rain_recomputes_both_directed_legs_without_mutating_other_cases(self):
        cases = self.results()
        for rid in ("TEST-3D", "TEST-4D"):
            case = cases[f"RAIN-{rid}"]
            self.assertEqual(case["baseline"]["conditional_earliest_finish"], "10:30")
            self.assertEqual(case["changed"]["conditional_earliest_finish"], "10:05")
            self.assertEqual([(leg["from_place_id"], leg["to_place_id"]) for leg in case["changed"]["legs"]],
                             [("A", "C"), ("C", "A")])
            self.assertTrue(case["source_data_complete"], case["gaps"])
            self.assertFalse(case["ready_for_real_adapt"])

    def test_missing_incoming_or_outgoing_replacement_leg_stays_missing(self):
        original = json.loads((self.data / "travel_times.json").read_text())
        for pair in (("A", "C"), ("C", "A")):
            self.write("travel_times.json", [leg for leg in original
                       if (leg["from_place_id"], leg["to_place_id"]) != pair])
            case = self.results()["RAIN-TEST-4D"]
            with self.subTest(pair=pair):
                self.assertFalse(case["source_data_complete"])
                self.assertIsNone(case["changed"]["conditional_earliest_finish"])
                self.assertTrue(any(g["code"] == "MISSING_LEG" and
                                    (g["from_place_id"], g["to_place_id"]) == pair for g in case["gaps"]))

    def test_mixed_replacement_is_not_accepted_as_indoor(self):
        places = json.loads((self.data / "places.json").read_text())
        next(p for p in places if p["place_id"] == "C")["environment"] = "MIXED"
        self.write("places.json", places)
        case = self.results()["RAIN-TEST-4D"]
        self.assertFalse(case["source_data_complete"])
        self.assertIn("REPLACEMENT_NOT_INDOOR", {g["code"] for g in case["gaps"]})

    def test_both_triggers_are_required_for_each_trip_length(self):
        self.write("handoff/source_scenarios.json", self.cases[:-1])
        with self.assertRaisesRegex(ValueError, "SOURCE_SCENARIO_COVERAGE"):
            audit(self.data)

    def test_extra_rest_requires_positive_integer_and_a_real_rest_stop(self):
        for value in (-1, 0, True, 2.5, "30"):
            cases = deepcopy(self.cases)
            cases[0]["extra_rest_minutes"] = value
            self.write("handoff/source_scenarios.json", cases)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "SOURCE_EXTRA_REST"):
                audit(self.data)
        cases = deepcopy(self.cases)
        cases[0]["rest_place_id"] = "B"
        self.write("handoff/source_scenarios.json", cases)
        with self.assertRaisesRegex(ValueError, "SOURCE_REST_TARGET"):
            audit(self.data)

    def test_export_includes_both_source_triggers_and_their_replacement(self):
        # C is referenced only by the new scenario input, not the legacy path check.
        self.write("handoff/source_adapt_checks.json", [{
            "check_id": "LEGACY-B", "replacement_place_id": "B", "place_sequence": ["A", "B", "A"]}])
        output = Path(self.temporary.name) / "export"
        export_source_bundle(self.data, output)
        self.assertTrue((output / "source_scenarios.json").exists())
        places = json.loads((output / "places.json").read_text())
        self.assertIn("C", {p["place_id"] for p in places})
        cases = json.loads((output / "source_scenarios.json").read_text())
        self.assertEqual(cases, self.cases)
        readiness = json.loads((output / "readiness.json").read_text())
        results = {c["case_id"]: c for c in readiness["source_scenarios"]}
        self.assertEqual(results["REST-TEST-3D"]["changed"]["conditional_earliest_finish"], "11:00")


if __name__ == "__main__":
    unittest.main()
