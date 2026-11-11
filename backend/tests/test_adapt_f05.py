"""F05 invariants and leader's T06/T08/T13/T15; all data/AI is explicitly MOCK."""

import io
import json
import sys
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adapt_f05 import AdaptEngine, AdaptError, Catalog, validate_candidate
from adapt_f05.demo import demo_inputs
from adapt_f05.engine import active, validate_snapshot
from adapt_f05.handoff import prepare_proposal, to_api_v1, validate_stored_option
from adapt_f05.ranking import GeminiRanker, MockRanker, RankingError, RuleRanker

REST = {"type": "EXTEND_REST", "base_version": 1, "rest_activity_id": "REST", "rest_until": "15:00"}
RAIN = {"type": "REPLACE_LOCATION", "base_version": 1, "activity_id": "A03", "reason": "RAIN"}


class AdaptTests(unittest.TestCase):
    def setUp(self):
        self.trip, self.catalog = demo_inputs()

    def generate(self, payload=None, **kwargs):
        return AdaptEngine(self.catalog, **kwargs).generate(self.trip, payload or REST)

    def activity(self, aid, days=None):
        return next(a for d in (days or self.trip["days"]) for a in d["activities"] if a["activity_id"] == aid)

    def assert_code(self, code, fn):
        with self.assertRaises(AdaptError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def test_t06_two_options_exact_times_and_no_mutation(self):
        before = deepcopy(self.trip)
        result = self.generate()
        self.assertEqual({tuple(c.dropped_ids) for c in result.candidates}, {("A03",), ("A04",)})
        self.assertEqual([c.estimated_end_time for c in result.candidates], ["16:15", "16:15"])
        self.assertEqual(self.trip, before)
        for c in result.candidates:
            self.assertTrue(validate_candidate(self.trip, c, self.catalog))
            self.assertEqual(self.activity("REST", c.proposed_days)["end_time"], "15:00")
            dropped = c.dropped_ids[0]
            self.assertEqual(self.activity(dropped, c.proposed_days), {**self.activity(dropped), "status": "DROPPED"})
            retired_ids = ("TRAVEL-1", "TRAVEL-2") if dropped == "A03" else ("TRAVEL-2", "TRAVEL-3")
            for aid in retired_ids:
                self.assertEqual(self.activity(aid, c.proposed_days), {**self.activity(aid), "status": "REPLACED"})
            self.assertEqual({t["activity_id"] for t in c.travel_changes if t["operation"] == "REPLACE"}, set(retired_ids))
            added, = [t for t in c.travel_changes if t["operation"] == "ADD"]
            expected_edge = ["MOCK-REST", "MOCK-A04"] if dropped == "A03" else ["MOCK-A03", "MOCK-END"]
            self.assertEqual(added["after_edge"], expected_edge)
            self.assertEqual(added["after"]["status"], "PENDING")
            self.assertIsNone(added["after"]["replaces_activity_id"])
            for aid in ("A01", "A02"):
                self.assertEqual(self.activity(aid), self.activity(aid, c.proposed_days))
            self.assertEqual(c.proposed_days[0], before["days"][0])
            self.assertEqual(c.proposed_days[2], before["days"][2])

    def test_keep_all_when_feasible(self):
        result = self.generate(REST | {"rest_until": "14:15"})
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].dropped_ids, [])
        self.assertEqual(result.candidates[0].estimated_end_time, "16:30")
        legs = result.candidates[0].travel_changes
        self.assertEqual({leg["activity_id"] for leg in legs}, {"TRAVEL-1", "TRAVEL-2", "TRAVEL-3"})
        for leg in legs:
            self.assertEqual(leg["operation"], "RESCHEDULE")
            self.assertEqual(leg["before_edge"], leg["after_edge"])
            self.assertEqual(leg["before"]["activity_id"], leg["after"]["activity_id"])

    def test_repeated_edges_keep_each_leg_id_when_only_times_change(self):
        day = self.trip["days"][1]
        day["end_deadline"] = "19:00"
        route = self.catalog.routes[day["day_id"]]
        self.catalog.routes[day["day_id"]] = replace(route, end_deadline="19:00")
        for pid in ("MOCK-A03", "MOCK-A04"):
            self.catalog.places[pid]["opening_hours"]["weekly"]["fri"] = [{"start": "08:00", "end": "19:00"}]
        self.catalog.travel_times[("MOCK-A04", "MOCK-A03")] = {
            **self.catalog.travel_times[("MOCK-A03", "MOCK-A04")],
            "from_place_id": "MOCK-A04", "to_place_id": "MOCK-A03",
        }
        self.activity("TRAVEL-3").update(start_time="18:00", end_time="18:15")
        day["activities"].extend([
            {**self.activity("TRAVEL-2"), "activity_id": "BACK", "start_time": "16:00", "end_time": "16:15"},
            {**self.activity("A03"), "activity_id": "A03-B", "start_time": "16:15", "end_time": "17:00"},
            {**self.activity("TRAVEL-2"), "activity_id": "TRAVEL-2B", "start_time": "17:00", "end_time": "17:15"},
            {**self.activity("A04"), "activity_id": "A04-B", "start_time": "17:15", "end_time": "18:00"},
        ])
        option, = self.generate(REST | {"rest_until": "14:15"}).candidates
        self.assertEqual({leg["operation"] for leg in option.travel_changes}, {"RESCHEDULE"})
        for aid, expected in (("TRAVEL-2", "15:15"), ("TRAVEL-2B", "17:15")):
            self.assertEqual(self.activity(aid, option.proposed_days)["start_time"], expected)

    def test_t08_return_leg_makes_rest_until_deadline_impossible(self):
        result = self.generate(REST | {"rest_until": "16:30"})
        self.assertEqual(result.candidates, [])
        self.assertTrue(result.no_option_reason)
        self.assertEqual(self.trip["version"], 1)
        self.assertEqual(self.activity("REST")["end_time"], "14:00")
        self.assertEqual(result.ranking["mode"], "NOT_CALLED")

    def test_t13_indoor_new_link_and_both_travel_legs(self):
        c = self.generate(RAIN).candidates[0]
        self.assertEqual(c.replacement_place_id, "MOCK-INDOOR")
        old = self.activity("A03", c.proposed_days)
        self.assertEqual(old["status"], "REPLACED")
        new = next(a for d in c.proposed_days for a in d["activities"] if a["replaces_activity_id"] == "A03")
        self.assertNotEqual(new["activity_id"], "A03")
        self.assertEqual((new["status"], new["start_time"], new["end_time"]), ("PENDING", "14:15", "15:00"))
        self.assertEqual(c.estimated_end_time, "16:15")
        self.assertEqual(self.activity("REST", c.proposed_days), self.activity("REST"))
        edges = [t["after_edge"] for t in c.travel_changes if t["after_edge"]]
        self.assertIn(["MOCK-REST", "MOCK-INDOOR"], edges)
        self.assertIn(["MOCK-INDOOR", "MOCK-A04"], edges)
        for aid in ("TRAVEL-1", "TRAVEL-2"):
            self.assertEqual(self.activity(aid, c.proposed_days), {**self.activity(aid), "status": "REPLACED"})
        self.assertEqual(self.activity("TRAVEL-3", c.proposed_days), self.activity("TRAVEL-3"))

    def test_t15_closed_only_candidate(self):
        self.catalog.places["MOCK-INDOOR"]["opening_hours"]["weekly"]["fri"] = []
        result = self.generate(RAIN)
        self.assertEqual(result.candidates, [])
        self.assertIn("đóng cửa", result.no_option_reason)

    def test_anchor_only_places_not_replacement_attractions(self):
        result = self.generate(RAIN)
        self.assertEqual([c.replacement_place_id for c in result.candidates], ["MOCK-INDOOR"])

    def test_keep_preference_baseline(self):
        result = self.generate(REST | {"preferred_keep_activity_id": "A04"})
        self.assertEqual(result.candidates[0].dropped_ids, ["A03"])
        self.assertIn("KEEP", result.candidates[0].facts)

    def test_mandatory_visits_never_drop(self):
        self.activity("A03")["is_optional"] = False
        self.activity("A04")["is_optional"] = False
        self.assertEqual(self.generate().candidates, [])

    def test_done_target_rejected(self):
        self.assert_code("ACTIVITY_NOT_ACTIVE", lambda: self.generate(RAIN | {"activity_id": "A01"}))

    def test_done_after_target_kept_by_rejecting_unsupported_reorder(self):
        self.activity("A04").update(status="DONE", completed_at="2026-11-13T09:00:00Z")
        self.assert_code("NO_FEASIBLE_ITINERARY", lambda: self.generate())

    def test_rain_cannot_rebuild_done_inbound_travel(self):
        self.activity("TRAVEL-1").update(status="DONE", completed_at="2026-11-13T07:15:00Z")
        before = deepcopy(self.trip)
        self.assert_code("NO_FEASIBLE_ITINERARY", lambda: self.generate(RAIN))
        self.assertEqual(self.trip, before)

    def test_stale_version_and_not_current(self):
        self.assert_code("STALE_ITINERARY", lambda: self.generate(REST | {"base_version": 2}))
        self.trip["status"] = "DRAFT"
        self.assert_code("NOT_CURRENT_ITINERARY", lambda: self.generate())

    def test_invalid_request_variants(self):
        for payload in (REST | {"base_version": True}, REST | {"base_version": "1"},
                        REST | {"rest_until": "24:00"}, REST | {"rest_until": "14:00"},
                        REST | {"unknown": 1}, REST | {"preferred_keep_activity_id": "A01"},
                        RAIN | {"reason": "SUN"}):
            with self.subTest(payload=payload):
                self.assert_code("VALIDATION_ERROR", lambda: self.generate(payload))

    def test_missing_target_and_anchor(self):
        self.assert_code("NOT_FOUND", lambda: self.generate(REST | {"rest_activity_id": "missing"}))
        self.activity("REST")["place_id"] = None
        self.assert_code("DATA_INCOMPLETE", lambda: self.generate())

    def test_daily_rest_is_sum_not_per_block(self):
        self.activity("REST")["end_time"] = "13:30"
        half = deepcopy(self.activity("REST"))
        half.update(activity_id="REST-HALF", start_time="12:00", end_time="12:30", place_id="MOCK-TEMPLE")
        self.trip["days"][1]["activities"].append(half)
        result = self.generate()
        self.assertTrue(result.candidates)
        self.assertEqual(self.activity("REST-HALF", result.candidates[0].proposed_days), half)

    def test_waiting_does_not_count_as_rest(self):
        self.activity("REST")["end_time"] = "13:30"
        self.assert_code("DATA_INCOMPLETE", lambda: self.generate())

    def test_missing_forward_leg_not_inferred_from_reverse(self):
        leg = self.catalog.travel_times.pop(("MOCK-REST", "MOCK-INDOOR"))
        leg.update(from_place_id="MOCK-INDOOR", to_place_id="MOCK-REST")
        self.catalog.travel_times[("MOCK-INDOOR", "MOCK-REST")] = leg
        result = self.generate(RAIN)
        self.assertEqual(result.candidates, [])
        self.assertTrue(any("MOCK-REST -> MOCK-INDOOR" in e["message"] for e in result.diagnostics))

    def test_outgoing_leg_checked_after_rain_replacement(self):
        self.catalog.travel_times.pop(("MOCK-INDOOR", "MOCK-A04"))
        result = self.generate(RAIN)
        self.assertEqual(result.candidates, [])
        self.assertIn("MOCK-INDOOR -> MOCK-A04", result.no_option_reason)

    def test_drop_uses_direct_return_leg_not_old_travel_sum(self):
        result = self.generate()
        c = next(c for c in result.candidates if c.dropped_ids == ["A04"])
        added = [t for t in c.travel_changes if t["after_edge"] == ["MOCK-A03", "MOCK-END"]]
        self.assertEqual(len(added), 1)
        self.assertEqual((added[0]["after"]["start_time"], added[0]["after"]["end_time"]), ("16:00", "16:15"))

    def test_missing_route_and_deadline_mismatch(self):
        route = self.catalog.routes.pop("MOCK-DAY-2")
        self.assert_code("DATA_INCOMPLETE", lambda: self.generate())
        self.catalog.routes[route.day_id] = replace(route, end_deadline="20:00")
        self.assert_code("DATA_INCOMPLETE", lambda: self.generate())

    def test_unknown_hours_and_missing_duration(self):
        place = self.catalog.places["MOCK-INDOOR"]
        for field in ("hours", "duration"):
            with self.subTest(field=field):
                original = deepcopy(place)
                if field == "hours":
                    place["opening_hours"]["weekly"]["fri"] = None
                else:
                    place["visit_duration_minutes"] = None
                result = self.generate(RAIN)
                self.assertEqual(result.candidates, [])
                self.assertTrue(any(d["code"] == "DATA_INCOMPLETE" for d in result.diagnostics))
                self.catalog.places["MOCK-INDOOR"] = place = original

    def test_finish_at_closing_time_allowed(self):
        self.catalog.places["MOCK-INDOOR"]["opening_hours"]["weekly"]["fri"] = [{"start":"14:15", "end":"15:00"}]
        self.assertEqual(self.generate(RAIN).candidates[0].estimated_end_time, "16:15")

    def test_visit_cannot_straddle_lunch_break_or_shrink(self):
        self.catalog.places["MOCK-INDOOR"]["opening_hours"]["weekly"]["fri"] = [
            {"start":"14:00", "end":"14:30"}, {"start":"15:00", "end":"15:30"}]
        self.assertEqual(self.generate(RAIN).candidates, [])

    def test_wait_for_next_opening_window(self):
        self.catalog.places["MOCK-INDOOR"]["opening_hours"]["weekly"]["fri"] = [{"start":"14:30", "end":"17:00"}]
        c = self.generate(RAIN).candidates[0]
        replacement = next(a for a in active(c.proposed_days[1]) if a["place_id"] == "MOCK-INDOOR")
        self.assertEqual((replacement["start_time"], replacement["end_time"]), ("14:30", "15:15"))
        self.assertEqual(c.estimated_end_time, "16:30")

    def test_mixed_and_unknown_not_used_for_rain(self):
        for env in ("MIXED", "UNKNOWN", "OUTDOOR"):
            self.catalog.places["MOCK-INDOOR"]["environment"] = env
            self.assertEqual(self.generate(RAIN).candidates, [])

    def test_unverified_and_legacy_sourced_are_not_verified(self):
        for status in ("UNVERIFIED", "SOURCED", "VERIFIED"):
            self.catalog.places["MOCK-INDOOR"]["data_status"] = status
            self.assertEqual(self.generate(RAIN).candidates, [])  # MOCK mode cannot mix real data either.
        self.catalog.mode = "VERIFIED"
        self.assert_code("DATA_INCOMPLETE", lambda: self.generate())

    def test_unknown_and_same_place_travel(self):
        self.assertEqual(self.catalog.travel("MOCK-REST", "MOCK-REST"), 0)
        self.assert_code("DATA_INCOMPLETE", lambda: self.catalog.travel("missing", "missing"))

    def test_duplicate_ids_overlaps_and_invalid_durations_rejected(self):
        original = deepcopy(self.trip)
        for mutation in (lambda: self.trip["days"][1]["activities"].append(deepcopy(self.activity("A03"))),
                         lambda: self.activity("A03").update(start_time="13:45"),
                         lambda: self.activity("REST").update(end_time="13:00")):
            self.trip = deepcopy(original)
            mutation()
            self.assert_code("DATA_INCOMPLETE", lambda: self.generate())

    def test_historical_rows_preserved(self):
        history = deepcopy(self.activity("A03"))
        history.update(activity_id="HISTORY", status="DROPPED")
        self.trip["days"][1]["activities"].append(history)
        for c in self.generate().candidates:
            self.assertEqual(self.activity("HISTORY", c.proposed_days), history)

    def test_four_day_snapshot_keeps_other_days(self):
        self.trip["return_date"] = "2026-11-15"
        day = deepcopy(self.trip["days"][2])
        day.update(day_id="MOCK-DAY-4", day_number=4, date="2026-11-15")
        day["activities"][0].update(activity_id="MOCK-PADDING-REST-4", day_id=day["day_id"])
        self.trip["days"].append(day)
        self.assertEqual(self.generate().candidates[0].proposed_days[3], day)

    def test_revalidation_rejects_stale_snapshot_or_dataset(self):
        c = self.generate().candidates[0]
        changed = deepcopy(self.trip)
        changed["version"] += 1
        self.assertFalse(validate_candidate(changed, c, self.catalog))
        self.catalog.travel_times[("MOCK-REST", "MOCK-A04")]["duration_minutes"] += 1
        self.assertFalse(validate_candidate(self.trip, c, self.catalog))

    def test_revalidation_rejects_tampered_output(self):
        original = self.generate().candidates[0]
        mutations = [lambda c: self.activity("A01", c.proposed_days).update(end_time="09:00"),
                     lambda c: self.activity("REST", c.proposed_days).update(end_time="14:00"),
                     lambda c: c.proposed_days[0].update(date="2026-11-11"),
                     lambda c: c.travel_changes.clear(), lambda c: c.changes.clear(),
                     lambda c: setattr(c, "estimated_end_time", "15:00")]
        for mutation in mutations:
            c = deepcopy(original)
            mutation(c)
            self.assertFalse(validate_candidate(self.trip, c, self.catalog))

    def test_mock_ranker_changes_order_only_and_is_labelled(self):
        result = self.generate(REST | {"preferred_keep_activity_id": "A04"}, ranker=MockRanker())
        self.assertEqual(result.ranking["mode"], "MOCK_AI")
        self.assertEqual(result.candidates[0].dropped_ids, ["A04"])
        self.assertTrue(all(validate_candidate(self.trip, c, self.catalog) for c in result.candidates))

    def test_hallucinated_id_falls_back_once(self):
        class BadRanker:
            mode = "TEST_DOUBLE"
            calls = 0
            def rank(self, context):
                self.calls += 1
                output = RuleRanker().rank(context)
                output["rankings"][0]["candidate_id"] = "invented-id"
                return output
        ranker = BadRanker()
        result = self.generate(ranker=ranker)
        self.assertEqual(ranker.calls, 1)
        self.assertEqual(result.ranking["mode"], "RULE_FALLBACK")
        self.assertEqual(result.ranking["failure_code"], "AI_INVALID_OUTPUT")

    def test_ai_cannot_invent_explanation_or_change_times(self):
        class BadRanker(RuleRanker):
            def rank(self, context):
                output = super().rank(context)
                output["rankings"][0]["reason_codes"] = ["NEW_FAKE_FACT"]
                return output
        self.assert_code("AI_INVALID_OUTPUT", lambda: self.generate(ranker=BadRanker(), allow_ai_fallback=False))

    def test_ai_timeout_fallback_and_strict_error(self):
        class TimeoutRanker:
            mode = "TEST_DOUBLE"
            def rank(self, context):
                raise RankingError("AI_TIMEOUT", "Timeout", 504)
        self.assertEqual(self.generate(ranker=TimeoutRanker()).ranking["failure_code"], "AI_TIMEOUT")
        self.assert_code("AI_TIMEOUT", lambda: self.generate(ranker=TimeoutRanker(), allow_ai_fallback=False))

    def test_search_budget_explicit(self):
        self.assert_code("SEARCH_LIMIT", lambda: self.generate(max_optional_visits=1))

    def test_preference_cannot_force_an_infeasible_option(self):
        self.catalog.travel_times[("MOCK-REST", "MOCK-A04")]["duration_minutes"] = 90
        result = self.generate(REST | {"preferred_keep_activity_id": "A04"})
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].dropped_ids, ["A04"])

    def test_existing_rest_after_target_is_preserved_and_not_shortened(self):
        self.trip["days"][1]["end_deadline"] = "18:00"
        route = self.catalog.routes["MOCK-DAY-2"]
        self.catalog.routes[route.day_id] = replace(route, end_deadline="18:00")
        extra = deepcopy(self.activity("REST"))
        extra.update(activity_id="REST-AFTER", place_id="MOCK-A03", start_time="15:00", end_time="15:10")
        # Existing TRAVEL-2 starts 15:10, keeping the source snapshot nonoverlapping.
        self.activity("TRAVEL-2")["start_time"] = "15:10"
        self.trip["days"][1]["activities"].append(extra)
        c = self.generate().candidates[0]
        after = self.activity("REST-AFTER", c.proposed_days)
        self.assertEqual((after["start_time"], after["end_time"]), ("16:00", "16:10"))

    def test_unverified_travel_never_filled_by_mock(self):
        self.catalog.travel_times[("MOCK-REST", "MOCK-INDOOR")]["data_status"] = "UNVERIFIED"
        self.assertEqual(self.generate(RAIN).candidates, [])

    def test_zero_or_negative_travel_between_different_places_rejected(self):
        for duration in (0, -1, True):
            self.catalog.travel_times[("MOCK-REST", "MOCK-INDOOR")]["duration_minutes"] = duration
            self.assertEqual(self.generate(RAIN).candidates, [])

    def test_no_ai_call_when_no_candidate(self):
        class MustNotRun:
            mode = "TEST_DOUBLE"
            def rank(self, context):
                raise AssertionError("AI must not be called")
        self.assertEqual(self.generate(REST | {"rest_until":"16:30"}, ranker=MustNotRun()).candidates, [])

    def test_export_travel_and_revalidate_after_storage_round_trip(self):
        for payload in (REST, RAIN):
            with self.subTest(payload=payload):
                public, stored = prepare_proposal(self.generate(payload), self.trip, self.catalog)
                stored = json.loads(json.dumps(stored))
                self.assertEqual(public["proposal_id"], stored["proposal_id"])
                for preview, option in zip(public["options"], stored["options"], strict=True):
                    self.assertEqual(preview, {k: v for k, v in option.items() if k != "_validation"})
                    self.assertNotIn("_validation", preview)
                    self.assertEqual({leg["operation"] for leg in preview["travel_changes"]} - {"RESCHEDULE"},
                                     {"ADD", "REPLACE"})
                    for leg in preview["travel_changes"]:
                        if leg["operation"] == "REPLACE":
                            self.assertIsNone(leg["after_edge"])
                            self.assertEqual(leg["after"], {**leg["before"], "status": "REPLACED"})
                    self.assertTrue(validate_stored_option(self.trip, option, self.catalog))
                    self.assertFalse(validate_stored_option(self.trip, preview, self.catalog))

    def test_stored_option_rejects_tampered_leg_and_newer_data(self):
        _, stored = prepare_proposal(self.generate(RAIN), self.trip, self.catalog)
        option, = stored["options"]
        tampered = deepcopy(option)
        leg = next(leg for leg in tampered["travel_changes"] if leg["operation"] == "ADD")
        leg["after_edge"][0] = "UNKNOWN"
        self.assertFalse(validate_stored_option(self.trip, tampered, self.catalog))
        self.assertFalse(validate_stored_option({**self.trip, "version": 2}, option, self.catalog))
        self.catalog.places["MOCK-INDOOR"]["opening_hours"]["weekly"]["fri"] = []
        self.assertFalse(validate_stored_option(self.trip, option, self.catalog))

    def test_empty_proposal_can_be_exported_but_not_implicitly_saved(self):
        result = self.generate(REST | {"rest_until":"16:30"})
        proposal = to_api_v1(result, self.trip, self.catalog)
        self.assertEqual(set(proposal), {"proposal_id", "itinerary_id", "type", "base_version", "options", "no_option_reason"})
        self.assertEqual(proposal["options"], [])
        self.assertEqual(self.trip["version"], 1)


class GeminiAdapterTests(unittest.TestCase):
    def setUp(self):
        self.context = {"request": {}, "interests": ["coffee"], "candidates": [
            {"candidate_id":"only-real-id", "facts":{"VALID":"Checked", "END":"16:15", "TRADEOFF":"No drop"}}]}

    def test_success_request_schema_timeout_usage_and_no_key_in_payload(self):
        captured = {}
        def opener(req, timeout):
            captured.update(request=req, timeout=timeout)
            return io.BytesIO(json.dumps({"candidates":[{"finishReason":"STOP", "content":{"parts":[
                {"text":json.dumps(RuleRanker().rank(self.context))}]}}],
                "usageMetadata":{"promptTokenCount":12, "candidatesTokenCount":8, "totalTokenCount":20}}).encode())
        provider = GeminiRanker(api_key="TEST-KEY-NOT-REAL", model="test-model", opener=opener)
        self.assertEqual(provider.rank(self.context), RuleRanker().rank(self.context))
        self.assertEqual(captured["timeout"], 60)
        self.assertNotIn(b"TEST-KEY-NOT-REAL", captured["request"].data)
        self.assertNotIn("TEST-KEY-NOT-REAL", captured["request"].full_url)
        self.assertEqual(provider.audit["usage"]["totalTokenCount"], 20)

    def test_provider_errors_are_sanitized(self):
        errors = [(TimeoutError("secret"),"AI_TIMEOUT"), (URLError("secret"),"AI_UNAVAILABLE"),
                  (ConnectionResetError("secret"),"AI_UNAVAILABLE"),
                  (HTTPError("https://example.invalid",429,"secret",{},None),"AI_UNAVAILABLE")]
        for error, code in errors:
            def opener(*args, **kwargs):
                raise error
            with self.assertRaises(RankingError) as caught:
                GeminiRanker(api_key="TEST", model="test", opener=opener).rank(self.context)
            self.assertEqual(caught.exception.code, code)
            self.assertNotIn("secret", str(caught.exception))

    def test_malformed_or_truncated_output(self):
        for envelope in ({}, [], {"candidates":[None]},
                         {"candidates":[{"finishReason":"STOP","content":{"parts":[None]}}]},
                         {"candidates":[{"finishReason":"MAX_TOKENS"}]},
                         {"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":"not-json"}]}}]}):
            provider = GeminiRanker(api_key="TEST", model="test", opener=lambda *a,**k:io.BytesIO(json.dumps(envelope).encode()))
            with self.assertRaises(RankingError):
                provider.rank(self.context)


if __name__ == "__main__":
    unittest.main(verbosity=2)
