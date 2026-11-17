"""Nhật's provider acceptance checks: explicit MOCK data and optional live Gemini.

No HTTP app, database, account, mobile or source-route acceptance is claimed.
Run from the repository root; see docs/PLAN-F02-NHAT-HANDOFF.md.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from adapt_f05.ranking import GeminiRanker, MockRanker, RankingError
from data_handoff import load_mock, mock_snapshot
from f05_provider import create_proposal, make_catalog_provider, make_option_validator
from itinerary_api import APIError, DraftInput, validate_plan
from plan_f02 import PlanProvider, mock_templates

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "backend/data"
CASES = tuple(f"F02_{days}D" for days in (3, 4)) + tuple(
    f"F05_{kind}_{days}D" for days in (3, 4)
    for kind in ("REST", "RAIN", "NO_REST_OPTION", "NO_RAIN_OPTION"))
SCENARIOS = {"REST": "T06", "RAIN": "T13", "NO_REST_OPTION": "T08", "NO_RAIN_OPTION": "T15"}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


class CheckFailure(ValueError):
    """Only fixed check codes from this module, never provider-supplied text."""


def require(value, code):
    if not value:
        raise CheckFailure(code)


def load_credentials(path=None):
    """An explicit file overrides these two process vars, never logs the key."""
    if path is None:
        values = os.environ
    else:
        from dotenv import dotenv_values
        values = dotenv_values(path, encoding="utf-8-sig", interpolate=False)
    key, model = values.get("GEMINI_API_KEY"), values.get("GEMINI_MODEL")
    if not key or not model or key == "dan_khoa_cua_ban_vao_day":
        raise RankingError("AI_UNAVAILABLE", "Thiếu GEMINI_API_KEY hoặc GEMINI_MODEL.", 503)
    return {"api_key": key, "model": model}


class ObservedRanker:
    def __init__(self, delegate):
        self.delegate = delegate
        self.mode = delegate.mode
        self.calls = 0

    @property
    def audit(self):
        return getattr(self.delegate, "audit", {})

    def rank(self, context):
        self.calls += 1
        return self.delegate.rank(context)


def planned_snapshot(plan, source):
    """Attach deterministic test-only IDs without writing SQLite."""
    snapshot = deepcopy(source)
    for number, (generated, day) in enumerate(zip(plan, snapshot["days"], strict=True), 1):
        day.update(date=generated["date"], end_deadline=generated["end_deadline"])
        day["activities"] = [dict(activity, activity_id=f"CHECK-{number}-{index}",
                                  day_id=day["day_id"], status="PENDING",
                                  replaces_activity_id=None, completed_at=None)
                             for index, activity in enumerate(generated["activities"])]
    return snapshot


def run_case(case, directory, routes, scenarios, model):
    count = int(case[-2])
    route = next(r for r in routes if len(r["days"]) == count)
    require(route["data_status"] == "MOCK", "HARNESS_REQUIRES_MOCK_ROUTE")
    trip = read(directory / route["snapshot"])
    before = deepcopy(trip)
    if case.startswith("F02"):
        templates = mock_templates([route], {route["route_id"]: trip})
        catalog = make_catalog_provider(directory / route["catalog"], {count: route}, mode="MOCK")(trip)
        request = DraftInput(**{k: trip[k] for k in (
            "departure_date", "return_date", "departure_time", "interests", "min_rest_minutes")})
        plan = PlanProvider(catalog, templates, ranker=model)(request)
        validate_plan(request, plan)
        check = mock_snapshot(route, planned_snapshot(plan, trip), load_mock(directory / route["catalog"]))
        require(check["passed"], "INDEPENDENT_PLAN_CHECK_FAILED")
        require(len(plan) == count and model.calls == 1, "PLAN_COUNT_OR_AI_CALL_COUNT")
        require(trip == before, "INPUT_MUTATED")
        return {"catalog_fingerprint": catalog.version, "day_count": count,
                "day_end_times": [d["activities"][-1]["end_time"] for d in plan],
                "checks": {"independent_schedule": True, "input_unchanged": True},
                "plan": plan}

    kind = case[4:-3]
    scenario = next(s for s in scenarios if s["test_id"] == SCENARIOS[kind])
    payload = deepcopy(scenario["trigger"])
    payload["base_version"] = trip["version"]
    for field, target in (("rest_activity_id", "rest_activity_id"),
                          ("activity_id", "rain_activity_id"),
                          ("preferred_keep_activity_id", "preferred_keep_activity_id")):
        if field in payload:
            payload[field] = route["target_ids"][target]
    loader = make_catalog_provider(directory / scenario["catalog"], {count: route}, mode="MOCK")
    catalog = loader(trip)
    public, stored = create_proposal(trip, payload, loader, lambda: model)
    stored = json.loads(json.dumps(stored))
    expect_empty = kind.startswith("NO_")
    require(len(public["options"]) == (0 if expect_empty else 2 if kind == "REST" else 1), "OPTION_COUNT")
    require(model.calls == (0 if expect_empty else 1), "AI_CALL_COUNT")
    require(trip == before, "INPUT_MUTATED")
    if expect_empty:
        require(bool(public["no_option_reason"]), "NO_OPTION_REASON_MISSING")
    validate = make_option_validator(loader)
    for option in stored["options"]:
        require(validate(trip, option), "STORED_OPTION_INVALID")
        checked = mock_snapshot(route, {**trip, "days": option["proposed_days"]},
                                load_mock(directory / scenario["catalog"]))
        require(checked["passed"], "INDEPENDENT_ADAPT_CHECK_FAILED")
        after = {a["activity_id"]: a for d in option["proposed_days"] for a in d["activities"]}
        for day, changed in zip(trip["days"], option["proposed_days"], strict=True):
            if day["day_id"] != route["target_ids"]["day_id"]:
                require(day == changed, "OTHER_DAY_CHANGED")
            for activity in day["activities"]:
                require(activity["activity_id"] in after, "HISTORY_REMOVED")
                if activity["status"] == "DONE":
                    require(after[activity["activity_id"]] == activity, "DONE_CHANGED")
        require(all(a["status"] != "DROPPED" for a in after.values() if a["type"] == "TRAVEL"), "TRAVEL_DROPPED")
    return {"catalog_fingerprint": catalog.version, "option_count": len(public["options"]),
            "checks": {"input_unchanged": True, "independent_schedule": None if expect_empty else True,
                       "stored_option_revalidated": None if expect_empty else True,
                       "done_and_history_preserved": None if expect_empty else True,
                       "no_option_reason_present": True if expect_empty else None,
                       "ai_not_called": True if expect_empty else None},
            "proposal": public}


def git_value(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8",
                                       stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def build_report(mode, case="all", directory=DATA, credentials=None):
    manifest = read(directory / "handoff/manifest.json")
    routes, scenarios = read(directory / manifest["mock_routes"]), read(directory / manifest["scenarios"])
    fixture_paths = {manifest["mock_routes"], manifest["scenarios"], "handoff/manifest.json"}
    fixture_paths.update(r["snapshot"] for r in routes)
    for folder in {r["catalog"] for r in routes} | {s["catalog"] for s in scenarios}:
        fixture_paths.update(f"{folder}/{name}" for name in ("places.json", "travel_times.json"))
    code_paths = [ROOT / "backend" / name for name in ("plan_f02.py", "f05_provider.py", "nhat_ai_check.py")]
    code_paths += sorted((ROOT / "backend/adapt_f05").glob("*.py"))
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "commit": git_value("rev-parse", "HEAD"),
              "worktree_dirty": bool(git_value("status", "--porcelain")),
              "ai_mode": "GEMINI" if mode == "gemini" else "MOCK_AI", "data_mode": "MOCK",
              "dataset_version": manifest["dataset_version"],
              "fixture_sha256": {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in sorted(fixture_paths)},
              "implementation_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in code_paths},
              "not_verified": ["HTTP app integration", "SQLite/ACCEPT/REJECT/restart", "Expo Go", "VERIFIED source routes"],
              "runs": []}
    failed = False
    for name in CASES if case == "all" else (case,):
        if failed:
            report["runs"].append({"case": name, "status": "NOT_RUN", "reason": "STOPPED_AFTER_FAILURE"})
            continue
        model = None
        started = time.monotonic()
        run = {"case": name, "status": "FAIL"}
        try:
            delegate = GeminiRanker(**(credentials or {})) if mode == "gemini" else MockRanker()
            model = ObservedRanker(delegate)
            run.update(run_case(name, directory, routes, scenarios, model))
            run["status"] = "PASS"
        except (APIError, RankingError) as error:
            run.update(error_code=error.code, http_status=error.status)
        except CheckFailure as error:
            run.update(error_code=str(error))
        except Exception as error:
            # Never record raw provider exceptions, request headers, keys or env files.
            run.update(error_code="CHECK_FAILED", exception_type=type(error).__name__)
        run.update(duration_ms=round((time.monotonic() - started) * 1000),
                   ai_calls=model.calls if model else 0,
                   ai_audit=deepcopy(model.audit) if model else {},
                   ai_used="NOT_CALLED" if not model or not model.calls else report["ai_mode"],
                   ai_succeeded=bool(model and model.calls and (
                       model.audit.get("outcome") == "SUCCESS" if mode == "gemini" else run["status"] == "PASS")))
        report["runs"].append(run)
        failed = run["status"] != "PASS"
        print(f"{name}: {run['status']} ({run['ai_used']}, {run['duration_ms']} ms)", flush=True)
    report["checks_passed"] = all(r["status"] == "PASS" for r in report["runs"])
    report["ai_calls"] = sum(r.get("ai_calls", 0) for r in report["runs"])
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("mock", "gemini"))
    parser.add_argument("--case", default="all", choices=("all", *CASES))
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="New .json file; existing files are not overwritten")
    args = parser.parse_args(argv)
    if args.output.suffix.lower() != ".json" or args.output.exists():
        parser.error("Chọn file .json mới để giữ nguyên bằng chứng cũ.")
    credentials = None
    if args.mode == "gemini":
        if args.env_file is not None and not args.env_file.is_file():
            parser.error("Không tìm thấy file cấu hình.")
        try:
            credentials = load_credentials(args.env_file)
        except (RankingError, OSError):
            print("Chưa có cấu hình Gemini hợp lệ. Không gọi AI; không tạo bằng chứng PASS.")
            return 2
    report = build_report(args.mode, args.case, credentials=credentials)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Evidence: {args.output.resolve()}")
    return 0 if report["checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
