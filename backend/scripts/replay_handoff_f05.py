"""Replay the four handoff cases on full 3/4-day snapshots with merged F05.

Uses RuleRanker and explicitly MOCK data. No HTTP, database writes or live AI.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adapt_f05 import AdaptEngine, AdaptError, Catalog
from adapt_f05.catalog import RouteDay
from adapt_f05.handoff import prepare_proposal, validate_stored_option
from adapt_f05.ranking import RuleRanker
from data_handoff import load_mock, mock_snapshot, read, require
from place_catalog import DATA_DIR

EXPECTED_COUNTS = {"T06": 2, "T08": 0, "T13": 1, "T15": 0}


def replay(directory):
    manifest = read(directory / "handoff/manifest.json")
    routes = read(directory / manifest["mock_routes"])
    cases = read(directory / manifest["scenarios"])
    require(sorted(len(route["days"]) for route in routes) == [3, 4], "MOCK_ROUTE_COVERAGE")
    require(sorted(case["test_id"] for case in cases) == sorted(EXPECTED_COUNTS), "SCENARIO_COVERAGE")
    runs = []
    for route in routes:
        snapshot = read(directory / route["snapshot"])
        ids = route["target_ids"]
        route_days = [RouteDay(**{key: day[key] for key in RouteDay.__dataclass_fields__}) for day in route["days"]]
        for case in cases:
            trip = deepcopy(snapshot)
            before = deepcopy(trip)
            payload = deepcopy(case["trigger"])
            payload["base_version"] = trip["version"]
            for field, target in (("rest_activity_id", "rest_activity_id"),
                                  ("activity_id", "rain_activity_id"),
                                  ("preferred_keep_activity_id", "preferred_keep_activity_id")):
                if field in payload:
                    payload[field] = ids[target]
            run = {"route_id": route["route_id"], "test_id": case["test_id"],
                   "catalog": case["catalog"], "passed": False, "errors": []}
            try:
                catalog = Catalog.load(directory / case["catalog"], route_days, mode="MOCK")
                independent = load_mock(directory / case["catalog"])
                original_audit = mock_snapshot(route, trip, independent)
                require(original_audit["passed"], f"INVALID_BASE_SNAPSHOT: {original_audit['errors']}")
                result = AdaptEngine(catalog, ranker=RuleRanker()).generate(trip, payload)
                public, stored = prepare_proposal(result, trip, catalog)
                # Same JSON round trip as a persistence boundary; no claim of SQLite/F06.
                stored = json.loads(json.dumps(stored))
                run.update(option_count=len(public["options"]),
                           end_times=[candidate.estimated_end_time for candidate in result.candidates],
                           original_unchanged=trip == before,
                           stored_options_valid=all(validate_stored_option(trip, option, catalog) for option in stored["options"]),
                           no_option_reason=public["no_option_reason"],
                           done_and_other_days_preserved=True, independent_snapshots_valid=True)
                require(run["option_count"] == EXPECTED_COUNTS[case["test_id"]], "OPTION_COUNT")
                require(run["original_unchanged"], "SOURCE_MUTATED")
                require(run["stored_options_valid"], "STORED_OPTION_INVALID")
                require(all(end == "16:15" for end in run["end_times"]), "END_TIME")
                if not public["options"]:
                    require(bool(public["no_option_reason"]), "MISSING_NO_OPTION_REASON")
                if case["test_id"] == "T06":
                    require({tuple(c.dropped_ids) for c in result.candidates} ==
                            {(ids["rain_activity_id"],), (ids["preferred_keep_activity_id"],)}, "DROP_COVERAGE")
                for candidate in result.candidates:
                    proposed = {**trip, "days": candidate.proposed_days}
                    checked = mock_snapshot(route, proposed, independent)
                    run["independent_snapshots_valid"] &= checked["passed"]
                    require(checked["passed"], f"INVALID_PROPOSED_SNAPSHOT: {checked['errors']}")
                    by_id = {a["activity_id"]: a for day in candidate.proposed_days for a in day["activities"]}
                    for day in before["days"]:
                        after = next(d for d in candidate.proposed_days if d["day_id"] == day["day_id"])
                        if day["day_id"] != ids["day_id"]:
                            run["done_and_other_days_preserved"] &= day == after
                        for activity in day["activities"]:
                            if activity["status"] == "DONE":
                                run["done_and_other_days_preserved"] &= by_id.get(activity["activity_id"]) == activity
                    require(run["done_and_other_days_preserved"], "DONE_OR_OTHER_DAY_CHANGED")
                    if case["test_id"] == "T13":
                        require(candidate.replacement_place_id == "MOCK-INDOOR", "RAIN_REPLACEMENT")
                        edges = [change["after_edge"] for change in candidate.travel_changes if change["after_edge"]]
                        require(["MOCK-REST", "MOCK-INDOOR"] in edges and ["MOCK-INDOOR", "MOCK-A04"] in edges,
                                "RAIN_EDGE_COVERAGE")
                run["passed"] = True
            except (AdaptError, ValueError, KeyError, TypeError) as error:
                run["errors"].append(str(error))
                run.setdefault("original_unchanged", trip == before)
            runs.append(run)
    implementation = Path(__file__).resolve().parents[1] / "adapt_f05"
    fixture_paths = {manifest["mock_routes"], manifest["scenarios"]}
    fixture_paths.update(route["snapshot"] for route in routes)
    for case in cases:
        fixture_paths.update(f"{case['catalog']}/{name}" for name in ("places.json", "travel_times.json"))
    return {"dataset_version": manifest["dataset_version"], "mode": "MOCK_DATA_RULE_RANKER",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "checks_passed": len(runs) == 8 and all(run["passed"] for run in runs),
            "implementation_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in sorted(implementation.glob("*.py"))},
            "fixture_sha256": {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                               for name in sorted(fixture_paths)},
            "runs": runs,
            "not_verified": ["public HTTP API", "SQLite/F06 transactions and restart", "Gemini/live AI", "Expo Go/device", "real routes"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = replay(args.data_dir)
    except (OSError, ValueError, KeyError, TypeError) as error:
        report = {"checks_passed": False, "errors": [str(error)]}
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
