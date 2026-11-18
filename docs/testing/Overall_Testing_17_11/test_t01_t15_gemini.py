"""T01-T15 API integration runner. Live Gemini, explicit MOCK travel data.

Requires test_t01_t05_gemini.py in the same directory. Runs against in-process
FastAPI apps with explicit provider injection, separate from main.app wiring.
"""

import argparse
from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from unittest.mock import patch

from test_t01_t05_gemini import CheckFailed, check, read_json, run as run_plan

sys.dont_write_bytecode = True


def run_adapt(repo, output):
    sys.path.insert(0, str(repo / "backend"))
    os.environ.pop("ADAPT_MODE", None)
    from fastapi.testclient import TestClient
    import auth
    import adapt_api
    from main import create_app
    from demo_reset import reset_demo, load_bundle, DATA_DIR, DEMO_USERNAME, DEMO_PASSWORD
    from f05_provider import make_catalog_provider, make_option_validator
    from adapt_f05.engine import AdaptEngine
    from adapt_f05.ranking import GeminiRanker, RankingError

    report = {"scope": "T06-T15 API/TestClient; live Gemini ranking; MOCK 4D fixtures",
              "wiring": "Test-only injection of GeminiRanker into adapt_api.AdaptEngine",
              "cases": [], "gemini_calls": [], "fixture_days": 4}
    state = {"case": "setup"}

    class AuditedGemini(GeminiRanker):
        def rank(self, context):
            record = {"case": state["case"], "status": "STARTED"}
            report["gemini_calls"].append(record)
            try:
                result = super().rank(context)
            except Exception as error:
                record.update(status="ERROR", code=getattr(error, "code", "UNEXPECTED_ERROR"))
                raise
            record.update(status="PASS", **self.audit)
            return result

    ranker = AuditedGemini()

    def request(client, method, url, status=200, **kwargs):
        result = getattr(client, method)(url, headers=state["headers"], **kwargs)
        body = result.json()
        check(result.status_code == status,
              f"{method.upper()} {url}: HTTP {result.status_code}, code={body.get('code', '')}, expected {status}")
        return body

    def current(client):
        return request(client, "get", "/api/v1/itineraries/current")["itinerary"]

    def activities(itinerary):
        return {a["activity_id"]: a for day in itinerary["days"] for a in day["activities"]}

    def rest_payload(baseline, until="15:00", preferred=None):
        return {"type": "EXTEND_REST", "base_version": baseline["version"],
                "rest_activity_id": state["bundle"].route["target_ids"]["rest_activity_id"],
                "rest_until": until, "preferred_keep_activity_id": preferred}

    def rain_payload(baseline):
        return {"type": "REPLACE_LOCATION", "base_version": baseline["version"],
                "activity_id": state["bundle"].route["target_ids"]["rain_activity_id"], "reason": "RAIN"}

    def propose(client, baseline, payload, *, expect_options=True):
        before = len(report["gemini_calls"])
        proposal = request(client, "post",
                           f"/api/v1/itineraries/{baseline['itinerary_id']}/adapt-proposals",
                           201, json=payload)
        check(current(client) == baseline, "Viewing proposal changed CURRENT")
        if expect_options:
            check(bool(proposal["options"]), "Expected feasible options")
            calls = report["gemini_calls"][before:]
            check(len(calls) == 1 and calls[0]["status"] == "PASS", "Live Gemini success missing")
        else:
            check(not proposal["options"] and bool(proposal["no_option_reason"]), "Expected empty options with reason")
            check(len(report["gemini_calls"]) == before, "Zero candidates unexpectedly called Gemini")
        return proposal

    def decision(client, proposal, value, option=None, status=200):
        payload = {"decision": value}
        if option is not None:
            payload["option_id"] = option["option_id"]
        return request(client, "post", f"/api/v1/adapt-proposals/{proposal['proposal_id']}/decision",
                       status, json=payload)

    def assert_applied(baseline, updated, option):
        check(updated["version"] == baseline["version"] + 1, "ACCEPT version mismatch")
        old, new = activities(baseline), activities(updated)
        for key, activity in old.items():
            if activity["status"] == "DONE":
                check(new.get(key) == activity, "DONE activity changed")
        expected_days = deepcopy(option["proposed_days"])
        actual_days = deepcopy(updated["days"])
        for days in (expected_days, actual_days):
            for day in days:
                day["activities"].sort(key=lambda a: a["activity_id"])
        check(actual_days == expected_days, "Stored itinerary differs from selected option")

    def case(name, action):
        state["case"] = name
        item = {"id": name}
        report["cases"].append(item)
        try:
            item["evidence"] = action()
            item["status"] = "PASS"
        except CheckFailed as error:
            item.update(status="FAIL", reason=str(error))
        except Exception as error:
            item.update(status="ERROR", error_type=type(error).__name__)
        print(name, item["status"], flush=True)

    with tempfile.TemporaryDirectory(prefix="tan-live-adapt-") as directory:
        database = Path(directory) / "demo.test.sqlite3"
        with patch.object(auth, "DB_PATH", database), patch.object(
            adapt_api, "AdaptEngine",
            side_effect=lambda catalog: AdaptEngine(catalog, ranker=ranker, allow_ai_fallback=False),
        ):
            def app():
                bundle = state["bundle"]
                provider = make_catalog_provider(DATA_DIR / bundle.catalog_path, {4: bundle.route}, mode="MOCK")
                return create_app(catalog_provider=provider, option_validator=make_option_validator(provider))

            @contextmanager
            def seed(scenario="T06"):
                reset_demo(database, days=4, scenario=scenario)
                state["bundle"] = load_bundle(4, scenario)
                with TestClient(app()) as client:
                    login = client.post("/api/v1/auth/login", json={
                        "username": DEMO_USERNAME, "password": DEMO_PASSWORD})
                    check(login.status_code == 200, "Seed account login failed")
                    state["headers"] = {"Authorization": "Bearer " + login.json()["access_token"]}
                    yield client

            def t06():
                with seed() as client:
                    baseline = current(client)
                    proposal = propose(client, baseline, rest_payload(baseline))
                    for option in proposal["options"]:
                        check(option["estimated_end_time"] <= "16:30", "End deadline exceeded")
                        check(any(c["change_type"] == "DROP" for c in option["changes"]), "DROP missing")
                    return proposal

            def t07():
                evidence = []
                with seed() as client:
                    baseline = current(client)
                    ids = state["bundle"].route["target_ids"]
                    for preferred in (ids["rain_activity_id"], ids["preferred_keep_activity_id"]):
                        proposal = propose(client, baseline, rest_payload(baseline, preferred=preferred))
                        check(len(proposal["options"]) == 2, "Fixture must offer both choices")
                        first = {a["activity_id"]: a for day in proposal["options"][0]["proposed_days"]
                                 for a in day["activities"]}
                        check(first[preferred]["status"] == "PENDING", "First option did not preserve preferred activity")
                        check(bool(proposal["options"][0]["reason"]), "Explanation missing")
                        evidence.append({"preferred_keep_activity_id": preferred, "proposal": proposal})
                return evidence

            def t08():
                with seed("T08") as client:
                    baseline = current(client)
                    return propose(client, baseline, rest_payload(baseline, until="16:30"), expect_options=False)

            def rejection(scenario, rain=False):
                with seed(scenario) as client:
                    baseline = current(client)
                    proposal = propose(client, baseline, rain_payload(baseline) if rain else rest_payload(baseline))
                    result = decision(client, proposal, "REJECT")
                    check(result["itinerary"] == baseline and current(client) == baseline, "REJECT changed schedule")
                    check(decision(client, proposal, "REJECT") == result, "REJECT replay differs")
                    return {"proposal": proposal, "decision": result}

            def acceptance(rain=False):
                with seed("T13" if rain else "T06") as client:
                    baseline = current(client)
                    proposal = propose(client, baseline, rain_payload(baseline) if rain else rest_payload(baseline))
                    option = proposal["options"][0]
                    result = decision(client, proposal, "ACCEPT", option)
                    assert_applied(baseline, result["itinerary"], option)
                    if rain:
                        old_id = state["bundle"].route["target_ids"]["rain_activity_id"]
                        check(activities(result["itinerary"])[old_id]["status"] == "REPLACED", "Old visit not replaced")
                        replacement = next(a for a in activities(result["itinerary"]).values()
                                           if a["replaces_activity_id"] == old_id)
                        catalog = app().state.catalog_provider(result["itinerary"])
                        check(catalog.place(replacement["place_id"])["environment"] == "INDOOR", "Replacement is not indoor")
                    check(decision(client, proposal, "ACCEPT", option) == result, "ACCEPT replay differs")
                    with TestClient(app()) as reopened:
                        check(current(reopened) == result["itinerary"], "Reopen differs from ACCEPT result")
                    return {"proposal": proposal, "decision": result, "reopen": "PASS"}

            def t11():
                with seed() as client:
                    baseline = current(client)
                    proposal = propose(client, baseline, rest_payload(baseline))
                    done = next(a for a in activities(baseline).values() if a["status"] == "PENDING")
                    updated = request(client, "patch",
                                      f"/api/v1/itineraries/{baseline['itinerary_id']}/activities/{done['activity_id']}",
                                      json={"status": "DONE", "base_version": baseline["version"]})["itinerary"]
                    error = decision(client, proposal, "ACCEPT", proposal["options"][0], 409)
                    check(error["code"] == "STALE_PROPOSAL", "Wrong stale proposal error")
                    check(current(client) == updated, "Stale proposal overwrote CURRENT")
                    return {"error": error, "version": updated["version"]}

            def t12():
                with seed() as client:
                    baseline = current(client)
                    with patch.object(ranker, "rank", side_effect=RankingError("AI_TIMEOUT", "Injected timeout", 504)):
                        error = request(client, "post",
                                        f"/api/v1/itineraries/{baseline['itinerary_id']}/adapt-proposals",
                                        504, json=rest_payload(baseline))
                    check(error["code"] == "AI_TIMEOUT" and current(client) == baseline, "AI failure changed schedule")
                    proposal = propose(client, baseline, rest_payload(baseline))
                    original_apply = adapt_api.apply_days

                    def fail_after_write(*args):
                        original_apply(*args)
                        raise sqlite3.OperationalError("Injected storage failure")

                    with patch.object(adapt_api, "apply_days", side_effect=fail_after_write):
                        storage_error = decision(client, proposal, "ACCEPT", proposal["options"][0], 500)
                    check(current(client) == baseline, "Storage failure was not rolled back")
                    retried = decision(client, proposal, "ACCEPT", proposal["options"][0])
                    assert_applied(baseline, retried["itinerary"], proposal["options"][0])
                    return {"fault_injection": True, "ai_timeout": error, "storage_error": storage_error,
                            "rollback": "PASS", "retry_version": retried["itinerary"]["version"]}

            def t15():
                with seed("T15") as client:
                    baseline = current(client)
                    return propose(client, baseline, rain_payload(baseline), expect_options=False)

            for name, action in (
                ("T06", t06), ("T07", t07), ("T08", t08),
                ("T09", lambda: rejection("T06")), ("T10", acceptance),
                ("T11", t11), ("T12", t12), ("T13", lambda: acceptance(True)),
                ("T14", lambda: rejection("T13", True)), ("T15", t15),
            ):
                case(name, action)

    output.mkdir(parents=True, exist_ok=False)
    (output / "T06-T15-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not os.environ.get("GEMINI_API_KEY") or not os.environ.get("GEMINI_MODEL"):
        parser.error("Set GEMINI_API_KEY and GEMINI_MODEL in this terminal.")
    repo = args.repo.resolve()
    if not (repo / "backend/main.py").is_file():
        parser.error("--repo must point to the repository root.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = args.output or Path(__file__).resolve().parent / "runs" / stamp
    if output.exists():
        parser.error("Output must be a new directory.")
    output.mkdir(parents=True)
    run_plan(repo, output / "plan")
    plan = read_json(output / "plan/T01-T05-results.json")
    adapt = run_adapt(repo, output / "adapt")
    summary = {"finished_at": datetime.now(timezone.utc).isoformat(),
               "scope": "API/TestClient; explicitly wired live Gemini; MOCK routes; mobile UI pending",
               "cases": [{"id": item["id"], "status": item["status"]}
                         for item in plan["cases"] + adapt["cases"]],
               "gemini_calls": len(plan["gemini_calls"]) + len(adapt["gemini_calls"])}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Results:", output)
    return 0 if all(item["status"] == "PASS" for item in summary["cases"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
