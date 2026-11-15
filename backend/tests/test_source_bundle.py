"""Source handoff exports review material without touching SQLite or source files."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from place_catalog import DATA_DIR, PlaceCatalog

SCRIPT = DATA_DIR.parent / "scripts/prepare_source_bundle.py"


class SourceBundleTests(unittest.TestCase):
    def run_export(self, output, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--output-dir", str(output), *args],
                              capture_output=True, text=True, timeout=15)

    def test_minimum_bundle_keeps_labels_and_all_referenced_points(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "source"
            result = self.run_export(target)
            self.assertEqual(result.returncode, 0, result.stderr)
            catalog = PlaceCatalog.load(target)
            original = PlaceCatalog.load()
            self.assertEqual(set(catalog.places), {"H001", "R003", "P001", "P005", "P008", "P009", "P010", "P011"})
            for pid, place in catalog.places.items():
                self.assertEqual(place, original.places[pid])
                self.assertNotEqual(place.data_status, "MOCK")
            for pair, leg in catalog.travel_times.items():
                self.assertEqual(leg, original.travel_times[pair])
                self.assertNotEqual(leg.data_status, "MOCK")
            report = json.loads((target / "readiness.json").read_text())
            self.assertTrue(all(not route["ready_for_real_plan"] for route in report["source_routes"]))
            self.assertTrue(all(not case["ready_for_real_adapt"] for case in report["source_adapt_checks"]))
            self.assertTrue((target / "travel_time_evidence.json").exists())
            self.assertTrue((target / "source_checks.json").exists())
            self.assertTrue((target / "place_coordinates.json").exists())
            summary = json.loads(result.stdout)
            self.assertEqual(summary["mode"], "REVIEW_ONLY")
            self.assertFalse(summary["ready_for_real_plan"])

    def test_existing_directory_is_rejected_without_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "source"
            target.mkdir()
            marker = target / "keep.txt"
            marker.write_text("keep")
            result = self.run_export(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("OUTPUT_EXISTS", result.stderr)
            self.assertEqual(list(target.iterdir()), [marker])
            self.assertEqual(marker.read_text(), "keep")

    def test_source_subdirectory_cannot_receive_an_export(self):
        target = DATA_DIR / "forbidden-generated-output"
        self.assertFalse(target.exists())
        result = self.run_export(target)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OUTPUT_OVERLAPS_SOURCE", result.stderr)
        self.assertFalse(target.exists())

    def test_dangling_symlink_output_is_not_followed(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "link"
            destination = Path(temporary) / "must-not-create"
            target.symlink_to(destination, target_is_directory=True)
            result = self.run_export(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("OUTPUT_EXISTS", result.stderr)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
