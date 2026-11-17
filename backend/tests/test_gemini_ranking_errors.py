"""Gemini boundary regressions: deterministic fake transport, no network or key."""

import io
import json
import socket
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapt_f05.ranking import GeminiRanker, RankingError, checked_ranking


CONTEXT = {"request": {}, "interests": [], "candidates": [
    {"candidate_id": "allowed", "facts": {"VALID": "Python checked", "TRADEOFF": "Unchanged"}}
]}
OUTPUT = {"rankings": [{"candidate_id": "allowed", "reason_codes": ["VALID"],
                         "tradeoff_code": "TRADEOFF"}]}


def envelope(output=OUTPUT, **extra):
    return {"candidates": [{"finishReason": "STOP", "content": {"parts": [
        {"text": json.dumps(output)}]}}], **extra}


def response(value):
    return io.BytesIO(json.dumps(value).encode())


class GeminiRankingErrorTests(unittest.TestCase):
    def provider(self, opener):
        return GeminiRanker(api_key="NOT-A-REAL-KEY", model="fake-test-model", opener=opener)

    def test_non_object_rows_and_invented_facts_fail_closed(self):
        invalid = [None, 1, [], "allowed", {"candidate_id": ["allowed"],
            "reason_codes": ["VALID"], "tradeoff_code": "TRADEOFF"},
            {"candidate_id": "allowed", "reason_codes": ["INVENTED"], "tradeoff_code": "TRADEOFF"},
            {"candidate_id": "allowed", "reason_codes": [["VALID"]], "tradeoff_code": "TRADEOFF"}]
        for row in invalid:
            with self.subTest(row=row), self.assertRaises(RankingError) as caught:
                checked_ranking({"rankings": [row]}, CONTEXT)
            self.assertEqual(caught.exception.code, "AI_INVALID_OUTPUT")

    def test_url_wrapped_timeout_is_timeout_not_unavailable(self):
        def opener(*args, **kwargs):
            raise URLError(socket.timeout("private upstream detail"))

        provider = self.provider(opener)
        with self.assertRaises(RankingError) as caught:
            provider.rank(CONTEXT)
        self.assertEqual((caught.exception.code, caught.exception.status), ("AI_TIMEOUT", 504))
        self.assertEqual(provider.audit["failure_code"], "AI_TIMEOUT")
        self.assertEqual(provider.audit["outcome"], "ERROR")
        self.assertGreaterEqual(provider.audit["latency_ms"], 0)
        self.assertNotIn("private", str(caught.exception) + json.dumps(provider.audit))

    def test_failure_resets_success_metadata_without_leaking_provider_body(self):
        attempts = []

        def opener(*args, **kwargs):
            attempts.append(True)
            if len(attempts) == 1:
                return response(envelope(usageMetadata={"totalTokenCount": 12}))
            raise HTTPError("https://example.invalid/NOT-A-REAL-KEY", 429,
                            "private upstream detail", {"secret": "NOT-A-REAL-KEY"},
                            io.BytesIO(b"private upstream detail"))

        provider = self.provider(opener)
        self.assertEqual(provider.rank(CONTEXT), OUTPUT)
        self.assertEqual(provider.audit["usage"], {"totalTokenCount": 12})
        with self.assertRaises(RankingError) as caught:
            provider.rank(CONTEXT)
        self.assertEqual(provider.audit["usage"], {})
        self.assertEqual(provider.audit["http_status"], 429)
        self.assertEqual(provider.audit["outcome"], "ERROR")
        self.assertEqual(provider.audit["failure_code"], "AI_UNAVAILABLE")
        self.assertEqual(len(attempts), 2)  # No hidden retries.
        evidence = str(caught.exception) + json.dumps(provider.audit)
        self.assertNotIn("NOT-A-REAL-KEY", evidence)
        self.assertNotIn("private", evidence)

    def test_success_after_failure_clears_error_metadata(self):
        provider = self.provider(lambda *args, **kwargs: response({}))
        with self.assertRaises(RankingError):
            provider.rank(CONTEXT)
        provider.opener = lambda *args, **kwargs: response(envelope())
        self.assertEqual(provider.rank(CONTEXT), OUTPUT)
        self.assertEqual(provider.audit["outcome"], "SUCCESS")
        self.assertNotIn("failure_code", provider.audit)
        self.assertNotIn("http_status", provider.audit)

    def test_malformed_envelopes_record_failure_without_uncaught_shape_errors(self):
        for value in (None, [], "text", {}, {"candidates": [None]},
                      {"candidates": [{"finishReason": "STOP", "content": {"parts": [None]}}]},
                      envelope({"rankings": [None]})):
            with self.subTest(value=value):
                provider = self.provider(lambda *args, **kwargs: response(value))
                with self.assertRaises(RankingError) as caught:
                    provider.rank(CONTEXT)
                self.assertEqual(caught.exception.code, "AI_INVALID_OUTPUT")
                self.assertEqual(provider.audit["failure_code"], "AI_INVALID_OUTPUT")
                self.assertEqual(provider.audit["outcome"], "ERROR")
                self.assertIn("latency_ms", provider.audit)

    def test_usage_is_numeric_allowlist_even_when_model_output_is_invalid(self):
        value = envelope({"rankings": []}, usageMetadata={
            "promptTokenCount": 12, "candidatesTokenCount": True, "totalTokenCount": -4,
            "unexpected": "NOT-A-REAL-KEY"})
        provider = self.provider(lambda *args, **kwargs: response(value))
        with self.assertRaises(RankingError):
            provider.rank(CONTEXT)
        self.assertEqual(provider.audit["usage"], {"promptTokenCount": 12})
        self.assertNotIn("NOT-A-REAL-KEY", json.dumps(provider.audit))

    def test_optional_malformed_usage_does_not_invalidate_checked_ranking(self):
        for usage in (None, [], "unknown"):
            with self.subTest(usage=usage):
                provider = self.provider(lambda *args, **kwargs: response(envelope(usageMetadata=usage)))
                self.assertEqual(provider.rank(CONTEXT), OUTPUT)
                self.assertEqual(provider.audit["usage"], {})

    def test_oversized_or_non_stop_response_is_not_accepted(self):
        for raw in (b"x" * 262145, json.dumps({"candidates": [{"finishReason": "MAX_TOKENS"}]}).encode()):
            with self.subTest(size=len(raw)):
                provider = self.provider(lambda *args, **kwargs: io.BytesIO(raw))
                with self.assertRaises(RankingError) as caught:
                    provider.rank(CONTEXT)
                self.assertEqual(caught.exception.code, "AI_INVALID_OUTPUT")
                self.assertEqual(provider.audit["outcome"], "ERROR")


if __name__ == "__main__":
    unittest.main()
