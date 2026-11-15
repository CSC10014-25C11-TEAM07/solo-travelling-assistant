"""Offline dataset checks, not a PLAN/ADAPT generator or persistence implementation."""

from datetime import date, timedelta
import json
from pathlib import Path

from place_catalog import PlaceCatalog, MissingTravelTime
from place_models import DAYS, TimeWindow
from source_readiness import source_route, source_replacements


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def minutes(value):
    require(isinstance(value, str), "INVALID_CLOCK")
    TimeWindow.valid_time(value)
    h, m = map(int, value.split(":"))
    return h * 60 + m


def clock(value):
    return f"{value // 60:02d}:{value % 60:02d}"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_mock(directory):
    catalog = PlaceCatalog.load(directory)
    require(all(x.data_status == "MOCK" for x in catalog.places.values()), "MIXED_DATA: mock places")
    require(all(x.data_status == "MOCK" for x in catalog.travel_times.values()), "MIXED_DATA: mock legs")
    return catalog


def window_contains(place, when, start, end):
    windows = place.opening_hours.weekly[DAYS[date.fromisoformat(when).weekday()]]
    return windows is not None and any(minutes(w.start) <= start < end <= minutes(w.end) for w in windows)


def mock_snapshot(route, snapshot, catalog):
    errors = []
    try:
        days = snapshot["days"]
        require(len(days) in (3, 4) and len(days) == len(route["days"]), "DAY_COUNT")
        require(snapshot["min_rest_minutes"] > 0, "REST_REQUIREMENT")
        require((date.fromisoformat(snapshot["return_date"]) - date.fromisoformat(snapshot["departure_date"])).days + 1 == len(days), "DATE_RANGE")
        seen = set()
        previous_end_place = None
        for number, (day, config) in enumerate(zip(days, route["days"]), 1):
            require(day["day_number"] == number and config["day_number"] == number, "DAY_ORDER")
            require(day["date"] == str(date.fromisoformat(snapshot["departure_date"]) + timedelta(days=number - 1)), "DAY_DATE")
            require(day["day_id"] == config["day_id"] and day["itinerary_id"] == snapshot["itinerary_id"], "DAY_ID")
            require(day["end_deadline"] == config["end_deadline"], "DEADLINE_MISMATCH")
            if previous_end_place is not None:
                require(config["start_place_id"] == previous_end_place, "MISSING_OVERNIGHT_CONNECTION")
            current = config["start_place_id"]
            catalog.places[current]
            active = [a for a in day["activities"] if a["status"] in ("PENDING", "DONE")]
            prior_end = minutes(config["start_time"])
            rest = 0
            for index, activity in enumerate(active):
                aid = activity["activity_id"]
                require(aid not in seen and activity["day_id"] == day["day_id"], f"ACTIVITY_ID: {aid}")
                seen.add(aid)
                start, end = minutes(activity["start_time"]), minutes(activity["end_time"])
                require(prior_end <= start < end, f"OVERLAP_OR_TIME: {aid}")
                if activity["type"] == "TRAVEL":
                    destination = next((a["place_id"] for a in active[index + 1:]
                                        if a["type"] != "TRAVEL"), config["end_place_id"])
                    duration = catalog.get_travel_time(current, destination, allow_mock=True)
                    require(duration > 0 and end - start == duration, f"TRAVEL_DURATION: {current} -> {destination}")
                    current = destination
                else:
                    require(activity["place_id"] == current, f"MISSING_TRAVEL_TO: {aid}")
                    place = catalog.places[current]
                    require(window_contains(place, day["date"], start, end), f"CLOSED_OR_UNKNOWN: {aid}")
                    if activity["type"] == "VISIT":
                        require(end - start == place.visit_duration_minutes, f"VISIT_DURATION: {aid}")
                    elif activity["type"] == "REST":
                        rest += end - start
                    else:
                        raise ValueError(f"ACTIVITY_TYPE: {aid}")
                prior_end = end
            require(current == config["end_place_id"], "MISSING_FINAL_LEG")
            require(prior_end <= minutes(config["end_deadline"]), "END_DEADLINE")
            require(rest >= snapshot["min_rest_minutes"], f"REST_SHORTFALL: {day['day_id']} {rest}")
            previous_end_place = current
        require(catalog.places[previous_end_place].area == "HCMC", "FINAL_DAY_NOT_HCMC")
    except (ValueError, KeyError, TypeError, MissingTravelTime) as error:
        errors.append(str(error))
    return {"route_id": route["route_id"], "day_count": len(snapshot["days"]), "passed": not errors, "errors": errors}


def simulate_path(case, path, catalog):
    current, now = case["departure_place_id"], minutes(path["departure_time"])
    destination = case["end_place_id"]
    try:
        for pid in path["visit_place_ids"]:
            destination = pid
            now += catalog.get_travel_time(current, pid, allow_mock=True)
            place = catalog.places[pid]
            windows = place.opening_hours.weekly[DAYS[date.fromisoformat(case["date"]).weekday()]]
            require(windows is not None and place.visit_duration_minutes is not None, f"DATA_INCOMPLETE: {pid}")
            slot = next(((max(now, minutes(w.start)), max(now, minutes(w.start)) + place.visit_duration_minutes)
                         for w in windows if max(now, minutes(w.start)) + place.visit_duration_minutes <= minutes(w.end)), None)
            if slot is None:
                return {"arrival": None, "feasible": False, "reason": f"CLOSED_OR_TOO_SHORT: {pid}", "data_errors": []}
            now = slot[1]
            current = pid
        destination = case["end_place_id"]
        now += catalog.get_travel_time(current, destination, allow_mock=True)
        return {"arrival": clock(now), "feasible": now <= minutes(case["end_deadline"]), "data_errors": []}
    except MissingTravelTime:
        return {"arrival": None, "feasible": False, "data_errors": [
            {"code": "MISSING_LEG", "from_place_id": current, "to_place_id": destination}]}
    except (ValueError, KeyError, TypeError) as error:
        return {"arrival": None, "feasible": False, "data_errors": [str(error)]}


def mock_case(case, catalog):
    results, errors = [], []
    required = {"T06": {"keep-both", "drop-A03", "drop-A04"}, "T08": {"drop-both"},
                "T13": {"indoor"}, "T15": {"closed-indoor"}}[case["test_id"]]
    paths = case["checked_paths"]
    require(len(paths) == len(required) and {p["path_id"] for p in paths} == required,
            f"SCENARIO_PATH_COVERAGE: {case['test_id']}")
    for path in case["checked_paths"]:
        result = simulate_path(case, path, catalog)
        results.append({"path_id": path["path_id"], **result})
        errors.extend(result["data_errors"])
        if result["arrival"] != path["expected_arrival"] or result["feasible"] != path["expected_feasible"]:
            errors.append(f"UNEXPECTED_PATH_RESULT: {path['path_id']}")
    if case["test_id"] in ("T13", "T15"):
        eligible = []
        for place in catalog.places.values():
            if place.environment == "INDOOR" and place.interests:
                path = {"departure_time": "14:00", "visit_place_ids": [place.place_id, "MOCK-A04"]}
                if simulate_path(case, path, catalog)["feasible"]:
                    eligible.append(place.place_id)
        if case["test_id"] == "T15" and eligible:
            errors.append("OPEN_INDOOR_CANDIDATE: " + ", ".join(eligible))
        if case["test_id"] == "T13" and "MOCK-INDOOR" not in eligible:
            errors.append("NO_VALID_INDOOR_REPLACEMENT")
    return {"test_id": case["test_id"], "catalog": case["catalog"], "passed": not errors, "paths": results, "errors": errors}



def audit(directory):
    manifest = read(directory / "handoff/manifest.json")
    catalog = PlaceCatalog.load(directory)
    mock_routes = []
    routes = read(directory / manifest["mock_routes"])
    require(sorted(len(r["days"]) for r in routes) == [3, 4], "MOCK_ROUTE_COVERAGE")
    for route in routes:
        mock_routes.append(mock_snapshot(route, read(directory / route["snapshot"]), load_mock(directory / route["catalog"])))
    inputs = read(directory / manifest["scenarios"])
    require(sorted(c["test_id"] for c in inputs) == ["T06", "T08", "T13", "T15"], "SCENARIO_COVERAGE")
    cases = [mock_case(case, load_mock(directory / case["catalog"])) for case in inputs]
    sources = read(directory / manifest["source_routes"])
    require(sorted(len(r["days"]) for r in sources) == [3, 4], "SOURCE_ROUTE_COVERAGE")
    source = [source_route(route, catalog) for route in sources]
    return {"dataset_version": manifest["dataset_version"],
            "checks_passed": all(item["passed"] for item in mock_routes + cases),
            "mock_routes": mock_routes, "scenarios": cases, "source_routes": source}
