"""Run the shipped full snapshots through merged F05, not hand-written output."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from place_catalog import DATA_DIR

SCRIPT = DATA_DIR.parent / "scripts/replay_handoff_f05.py"


class HandoffReplayTests(unittest.TestCase):
    def run_replay(self, directory=DATA_DIR):
        result = subprocess.run([sys.executable, str(SCRIPT), "--data-dir", str(directory)],
                                capture_output=True, text=True, timeout=20)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return result, json.loads(result.stdout)

    def test_all_four_cases_replay_on_full_three_and_four_day_snapshots(self):
        result, report = self.run_replay()
        self.assertEqual(result.returncode, 0, report)
        self.assertTrue(report["checks_passed"])
        self.assertEqual(report["mode"], "MOCK_DATA_RULE_RANKER")
        expected = {("MOCK-3D", "T06"): 2, ("MOCK-3D", "T08"): 0,
                    ("MOCK-3D", "T13"): 1, ("MOCK-3D", "T15"): 0,
                    ("MOCK-4D", "T06"): 2, ("MOCK-4D", "T08"): 0,
                    ("MOCK-4D", "T13"): 1, ("MOCK-4D", "T15"): 0}
        self.assertEqual({(r["route_id"], r["test_id"]): r["option_count"] for r in report["runs"]}, expected)
        for run in report["runs"]:
            self.assertTrue(run["passed"], run)
            self.assertTrue(run["original_unchanged"])
            self.assertTrue(run["done_and_other_days_preserved"])
            self.assertTrue(run["stored_options_valid"])
            self.assertTrue(run["independent_snapshots_valid"])
            self.assertTrue(all(end == "16:15" for end in run["end_times"]))

    def test_missing_outgoing_rain_leg_cannot_be_reported_as_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "data"
            shutil.copytree(DATA_DIR, data)
            path = data / "fixtures/mock/travel_times.json"
            legs = json.loads(path.read_text())
            path.write_text(json.dumps([leg for leg in legs if
                                       (leg["from_place_id"], leg["to_place_id"]) != ("MOCK-INDOOR", "MOCK-A04")]))
            result, report = self.run_replay(data)
            self.assertEqual(result.returncode, 1, report)
            self.assertFalse(report["checks_passed"])
            self.assertTrue(all(not r["passed"] for r in report["runs"] if r["test_id"] == "T13"))


if __name__ == "__main__":
    unittest.main()
