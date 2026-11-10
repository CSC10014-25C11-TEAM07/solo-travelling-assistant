"""Checks for the shared data standard and the executable handoff bundle."""

from pathlib import Path
import json
import importlib.util
from contextlib import redirect_stdout
from io import StringIO
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from place_models import Place, TravelTime

ROOT = Path(__file__).resolve().parents[2]


def complete_place():
    return {
        "place_id": "TEST-PLACE", "name": "Test", "area": "DALAT",
        "interests": ["coffee"], "environment": "INDOOR", "visit_duration_minutes": 45,
        "opening_hours": {"timezone": "Asia/Ho_Chi_Minh", "weekly": {
            d: [{"start": "08:00", "end": "17:00"}]
            for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")}},
        "image_url": None, "source_url": "https://example.com/venue",
        "checked_at": "2026-11-10T00:00:00Z", "data_status": "VERIFIED",
    }


class SharedStandardTests(unittest.TestCase):
    def test_complete_verified_place_is_accepted(self):
        self.assertEqual(Place.model_validate(complete_place()).data_status, "VERIFIED")

    def test_legacy_sourced_label_is_not_accepted(self):
        raw = complete_place()
        raw["data_status"] = "SOURCED"
        with self.assertRaises(ValidationError):
            Place.model_validate(raw)

    def test_unknown_environment_requires_unverified_intake(self):
        raw = complete_place()
        raw.update(environment=None, data_status="UNVERIFIED")
        self.assertIsNone(Place.model_validate(raw).environment)
        raw["data_status"] = "VERIFIED"
        with self.assertRaises(ValidationError):
            Place.model_validate(raw)

    def test_only_shared_area_codes_are_accepted(self):
        raw = complete_place()
        raw["data_status"] = "MOCK"
        for area in ("HCMC", "DALAT", "EN_ROUTE"):
            raw["area"] = area
            self.assertEqual(Place.model_validate(raw).area, area)
        raw["area"] = "DALAT_CENTER"
        with self.assertRaises(ValidationError):
            Place.model_validate(raw)

    def test_checked_at_must_be_utc(self):
        raw = complete_place()
        raw.update(data_status="UNVERIFIED", checked_at="2026-11-10T07:00:00+07:00")
        with self.assertRaises(ValidationError):
            Place.model_validate(raw)

    def test_verified_leg_requires_source_and_time(self):
        raw = {"travel_time_id": None, "from_place_id": "A", "to_place_id": "B",
               "duration_minutes": 17, "source_url": "https://example.com/route",
               "checked_at": "2026-11-10T00:00:00Z", "data_status": "VERIFIED"}
        self.assertEqual(TravelTime.model_validate(raw).duration_minutes, 17)
        raw["source_url"] = None
        with self.assertRaises(ValidationError):
            TravelTime.model_validate(raw)


class HandoffCommandTests(unittest.TestCase):
    def run_audit(self, directory=None, *extra):
        command = [sys.executable, str(ROOT / "backend/scripts/audit_data_handoff.py")]
        if directory is not None:
            command.extend(["--data-dir", str(directory)])
        result = subprocess.run(command + list(extra), capture_output=True, text=True, timeout=15)
        self.assertNotEqual(result.returncode, 2, result.stderr)
        return result, json.loads(result.stdout)

    def test_shipped_mock_routes_and_all_scenarios_pass(self):
        result, report = self.run_audit()
        self.assertEqual(result.returncode, 0, report)
        self.assertEqual([r["day_count"] for r in report["mock_routes"]], [3, 4])
        self.assertTrue(all(r["passed"] for r in report["mock_routes"]), report)
        self.assertEqual([c["test_id"] for c in report["scenarios"]], ["T06", "T08", "T13", "T15"])
        self.assertTrue(all(c["passed"] for c in report["scenarios"]), report)

    def test_source_routes_report_unknowns_instead_of_claiming_ready(self):
        result, report = self.run_audit()
        self.assertEqual(result.returncode, 0)
        self.assertEqual([r["day_count"] for r in report["source_routes"]], [3, 4])
        self.assertTrue(all(not r["ready_for_real_plan"] for r in report["source_routes"]))
        issues = [g for r in report["source_routes"] for g in r["gaps"]]
        self.assertTrue(any(g["code"] == "UNKNOWN_VISIT_DURATION" and g["place_id"] == "P010" for g in issues))
        self.assertTrue(any(g["code"] == "UNVERIFIED_LEG" and g["from_place_id"] == "H001" for g in issues))
        self.assertTrue(any(g["code"] == "LOWER_BOUND_LATE" for g in issues))

    def test_missing_either_rain_leg_fails_the_handoff(self):
        for pair in [("MOCK-REST", "MOCK-INDOOR"), ("MOCK-INDOOR", "MOCK-A04")]:
            with self.subTest(pair=pair), tempfile.TemporaryDirectory() as temporary:
                data = Path(temporary) / "data"
                shutil.copytree(ROOT / "backend/data", data)
                path = data / "fixtures/mock/travel_times.json"
                legs = json.loads(path.read_text())
                path.write_text(json.dumps([x for x in legs if (x["from_place_id"], x["to_place_id"]) != pair]))
                result, report = self.run_audit(data)
                self.assertEqual(result.returncode, 1)
                rain = next(c for c in report["scenarios"] if c["test_id"] == "T13")
                self.assertFalse(rain["passed"])
                missing = next(e for e in rain["paths"][0]["data_errors"] if e["code"] == "MISSING_LEG")
                self.assertEqual((missing["from_place_id"], missing["to_place_id"]), pair)

    def test_t15_fails_if_an_open_indoor_candidate_leaks_in(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "data"
            shutil.copytree(ROOT / "backend/data", data)
            path = data / "fixtures/scenarios.json"
            scenarios = json.loads(path.read_text())
            next(c for c in scenarios if c["test_id"] == "T15")["catalog"] = "fixtures/mock"
            path.write_text(json.dumps(scenarios))
            result, report = self.run_audit(data)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(next(c for c in report["scenarios"] if c["test_id"] == "T15")["passed"])

    def test_missing_required_scenario_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "data"
            shutil.copytree(ROOT / "backend/data", data)
            path = data / "fixtures/scenarios.json"
            cases = json.loads(path.read_text())
            path.write_text(json.dumps([c for c in cases if c["test_id"] != "T13"]))
            result, report = self.run_audit(data)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(report["checks_passed"])

    def test_present_scenario_without_its_paths_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "data"
            shutil.copytree(ROOT / "backend/data", data)
            path = data / "fixtures/scenarios.json"
            cases = json.loads(path.read_text())
            next(c for c in cases if c["test_id"] == "T06")["checked_paths"] = []
            path.write_text(json.dumps(cases))
            result, report = self.run_audit(data)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(report["checks_passed"])

    def test_snapshot_rest_shortfall_is_not_silently_passed(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "data"
            shutil.copytree(ROOT / "backend/data", data)
            path = data / "fixtures/current_v1_3day.json"
            itinerary = json.loads(path.read_text())
            itinerary["days"][0]["activities"][1]["end_time"] = "08:30"
            path.write_text(json.dumps(itinerary))
            result, report = self.run_audit(data)
            self.assertEqual(result.returncode, 1)
            self.assertIn("REST_SHORTFALL", json.dumps(report))


class CollectorReviewTests(unittest.TestCase):
    def test_successful_provider_reply_does_not_auto_verify_a_candidate_endpoint(self):
        spec = importlib.util.spec_from_file_location("collector_under_test", ROOT / "backend/scripts/collect_travel_times.py")
        collector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(collector)
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json={
            "trip": {"status": 0, "summary": {"time": 61, "length": 1.2}}}, request=request))
        client = httpx.Client(transport=transport)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            pairs = Path(temporary) / "pairs.json"
            pairs.write_text(json.dumps([{"from_place_id": "H001", "to_place_id": "R003"}]))
            argv = ["collect_travel_times.py", "--pairs", str(pairs), "--output-dir", str(output)]
            with patch.object(sys, "argv", argv), patch.object(collector.httpx, "Client", return_value=client), redirect_stdout(StringIO()):
                collector.main()
            leg = json.loads((output / "travel_times.json").read_text())[0]
            self.assertEqual(leg["duration_minutes"], 2)
            self.assertEqual(leg["data_status"], "UNVERIFIED")
