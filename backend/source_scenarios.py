"""Offline source-data probes for both ADAPT triggers, never F05 proposals."""

from copy import deepcopy

from source_readiness import ordered_stops, require, source_route, stop_sequence


def source_scenarios(cases, routes, catalog):
    by_id = {r["route_id"]: r for r in routes}
    required = {(rid, kind) for rid in by_id for kind in ("EXTEND_REST", "REPLACE_LOCATION")}
    require(len(by_id) == len(routes) and len(cases) == len(required) and
            len({c["case_id"] for c in cases}) == len(cases) and
            {(c["route_id"], c["type"]) for c in cases} == required, "SOURCE_SCENARIO_COVERAGE")
    baselines = {rid: source_route(route, catalog) for rid, route in by_id.items()}
    reports = []
    for case in cases:
        rid, did = case["route_id"], case["day_id"]
        route = deepcopy(by_id[rid])
        matching = [day for day in route["days"] if day["day_id"] == did]
        require(len(matching) == 1, "SOURCE_SCENARIO_DAY")
        day = matching[0]
        stops = ordered_stops(day)
        require(stop_sequence(day, stops) == day["place_sequence"], "SOURCE_STOPS_PATH_MISMATCH")
        original_rest = sum(r["duration_minutes"] for r in day["rest_stops"])
        candidate_gaps = []
        if case["type"] == "EXTEND_REST":
            extra = case["extra_rest_minutes"]
            require(type(extra) is int and extra > 0, "SOURCE_EXTRA_REST")
            target = [r for r in day["rest_stops"] if r["place_id"] == case["rest_place_id"]]
            require(len(target) == 1, "SOURCE_REST_TARGET")
            target[0]["duration_minutes"] += extra
            day["stops"] = ordered_stops(day)
        else:
            require(case["reason"] == "RAIN", "SOURCE_RAIN_REASON")
            target, replacement = case["visit_place_id"], case["replacement_place_id"]
            require(target in day["visit_place_ids"], "SOURCE_RAIN_TARGET")
            require(replacement in catalog.places and replacement not in day["place_sequence"],
                    "SOURCE_RAIN_REPLACEMENT")
            for stop in stops:
                if stop["type"] == "VISIT" and stop["place_id"] == target:
                    stop["place_id"] = replacement
            day["visit_place_ids"] = [replacement if pid == target else pid for pid in day["visit_place_ids"]]
            day["place_sequence"] = stop_sequence(day, stops)
            day["stops"] = stops
            if catalog.places[replacement].environment != "INDOOR":
                candidate_gaps.append({"code": "REPLACEMENT_NOT_INDOOR", "place_id": replacement})
        changed = source_route(route, catalog)
        baseline = baselines[rid]
        gaps = [{"phase": phase, **gap} for phase, result in (("baseline", baseline), ("changed", changed))
                for gap in result["gaps"] if gap.get("day_id", did) == did]
        gaps.extend(candidate_gaps)
        reports.append({
            "case_id": case["case_id"], "route_id": rid, "day_id": did, "type": case["type"],
            "baseline_rest_minutes": original_rest,
            "changed_rest_minutes": sum(r["duration_minutes"] for r in day["rest_stops"]),
            "baseline": next(d for d in baseline["days"] if d["day_id"] == did),
            "changed": next(d for d in changed["days"] if d["day_id"] == did),
            "changed_place_sequence": day["place_sequence"], "gaps": gaps,
            "source_data_complete": not gaps, "ready_for_real_adapt": False,
            "scope": "Rà dữ liệu/ngân sách của ngày nguồn trước và sau thay đổi. Chưa có CURRENT, activity_id, DONE hay thời điểm trigger thật; không phải phương án F05/AI/ACCEPT."})
    return reports
