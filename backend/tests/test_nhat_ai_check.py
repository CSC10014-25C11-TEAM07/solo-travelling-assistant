"""Offline tests of the evidence runner. No real Gemini requests."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nhat_ai_check as check
from adapt_f05.ranking import RankingError


class EvidenceTests(unittest.TestCase):
    def test_mock_run_covers_both_lengths_and_never_calls_network(self):
        with patch.object(check, "GeminiRanker", side_effect=AssertionError("NETWORK_FORBIDDEN")), redirect_stdout(io.StringIO()):
            report = check.build_report("mock")
        self.assertTrue(report["checks_passed"], report["runs"])
        self.assertEqual(len(report["runs"]), 10)
        self.assertEqual(report["ai_mode"], "MOCK_AI")
        self.assertEqual(report["data_mode"], "MOCK")
        self.assertEqual(report["ai_calls"], 6)
        for run in report["runs"]:
            self.assertEqual(run["ai_calls"], 0 if "NO_" in run["case"] else 1)
            self.assertTrue(all(v for v in run["checks"].values() if v is not None))
            if "NO_" in run["case"]:
                self.assertIsNone(run["checks"]["independent_schedule"])
                self.assertFalse(run["ai_succeeded"])
        self.assertTrue(report["fixture_sha256"])
        self.assertTrue(report["implementation_sha256"])

    def test_provider_failure_stops_next_calls_and_omits_secret_exception(self):
        secret = "SECRET-MUST-NOT-APPEAR"
        class Broken:
            mode = "GEMINI"
            audit = {}
            def rank(self, context):
                raise RankingError("AI_TIMEOUT", secret, 504)
        with patch.object(check, "GeminiRanker", return_value=Broken()) as factory, redirect_stdout(io.StringIO()):
            report = check.build_report("gemini", credentials={"api_key": secret, "model": "test"})
        self.assertFalse(report["checks_passed"])
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(report["ai_calls"], 1)
        self.assertEqual(report["runs"][0]["error_code"], "AI_TIMEOUT")
        self.assertFalse(report["runs"][0]["ai_succeeded"])
        self.assertTrue(all(r["status"] == "NOT_RUN" for r in report["runs"][1:]))
        self.assertNotIn(secret, json.dumps(report))

    def test_explicit_env_file_is_read_without_export_or_interpolation(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"GEMINI_API_KEY": "old"}):
            path = Path(directory) / ".env"
            path.write_text('GEMINI_API_KEY="TEST-${UNCHANGED}"\nGEMINI_MODEL=test-model\n', encoding="utf-8-sig")
            values = check.load_credentials(path)
            self.assertEqual(values, {"api_key": "TEST-${UNCHANGED}", "model": "test-model"})
            self.assertEqual(os.environ["GEMINI_API_KEY"], "old")

    def test_missing_credentials_do_not_call_model_or_create_pass_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            output = Path(directory) / "evidence.json"
            with patch.object(check, "build_report") as run, redirect_stdout(io.StringIO()):
                self.assertEqual(check.main(["--mode", "gemini", "--output", str(output)]), 2)
            run.assert_not_called()
            self.assertFalse(output.exists())

    def test_existing_evidence_is_not_overwritten_or_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evidence.json"
            output.write_text("preserve", encoding="utf-8")
            with patch.object(check, "build_report") as run, redirect_stdout(io.StringIO()), patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit):
                    check.main(["--mode", "mock", "--output", str(output)])
            run.assert_not_called()
            self.assertEqual(output.read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
