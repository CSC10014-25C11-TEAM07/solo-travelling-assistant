"""Conservative offline source-data audit; never a replacement for F02/F05."""

from datetime import date, timedelta

from place_models import DAYS, TimeWindow


def require(condition, code):
    if not condition:
        raise ValueError(code)


def minutes(value):
    TimeWindow.valid_time(value)
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def clock(value):
    # Keep >24h visible as a lower bound; never wrap an infeasible day to 00:xx.
    return f"{value // 60:02d}:{value % 60:02d}"


def place_gaps(place, common):
    gaps = []
    if place.data_status != "VERIFIED":
        gaps.append({"code": "UNVERIFIED_PLACE", **common})
    if place.environment is None:
        gaps.append({"code": "UNKNOWN_ENVIRONMENT", **common})
    return gaps


def directed_legs(sequence, catalog, common):
    legs, gaps = [], []
    for origin, destination in zip(sequence, sequence[1:]):
        if origin == destination:
            continue
        pair = {"from_place_id": origin, "to_place_id": destination}
        leg = catalog.travel_times.get((origin, destination))
        legs.append({**pair, "duration_minutes": leg.duration_minutes if leg else None,
                     "data_status": leg.data_status if leg else None})
        if leg is None:
            gaps.append({"code": "MISSING_LEG", **common, **pair})
        elif leg.data_status != "VERIFIED":
            gaps.append({"code": "UNVERIFIED_LEG", **common, **pair})
    return legs, gaps


def ordered_stops(day):
    """REST/VISIT operations in the same order as the source-day audit."""
    visits, rests, result = set(day["visit_place_ids"]), {
        r["place_id"]: r["duration_minutes"] for r in day["rest_stops"]}, []
    for pid in day["place_sequence"]:
        if pid in visits:
            result.append({"type": "VISIT", "place_id": pid})
            visits.remove(pid)
        if pid in rests:
            result.append({"type": "REST", "place_id": pid, "duration_minutes": rests.pop(pid)})
    return result


def stop_sequence(day, stops):
    sequence = [day["start_place_id"]]
    for pid in [s["place_id"] for s in stops] + [day["end_place_id"]]:
        if pid != sequence[-1]:
            sequence.append(pid)
    return sequence


def schedule_day(day, catalog):
    """Earliest schedule, with separate VISIT/REST; unknown inputs stop timing."""
    now, schedule, gaps = minutes(day["start_time"]), [], []
    visited, rested = set(), set()
    rests = {r["place_id"]: r["duration_minutes"] for r in day["rest_stops"]}
    weekday = DAYS[date.fromisoformat(day["date"]).weekday()]
    current = day["place_sequence"][0]
    for pid in day["place_sequence"]:
        if pid != current:
            leg = catalog.travel_times.get((current, pid))
            if leg is None:
                now = None
            if now is not None:
                schedule.append({"type": "TRAVEL", "from_place_id": current, "to_place_id": pid,
                                 "start_time": clock(now), "end_time": clock(now + leg.duration_minutes)})
                now += leg.duration_minutes
            current = pid
        place = catalog.places[pid]
        operations = []
        if pid in day["visit_place_ids"] and pid not in visited:
            visited.add(pid)
            operations.append(("VISIT", place.visit_duration_minutes))
        if pid in rests and pid not in rested:
            rested.add(pid)
            operations.append(("REST", rests[pid]))
        for kind, duration in operations:
            common = {"day_id": day["day_id"], "place_id": pid}
            windows = place.opening_hours.weekly[weekday]
            if duration is None:
                gaps.append({"code": "UNKNOWN_VISIT_DURATION", **common})
            if windows is None:
                gaps.append({"code": "UNKNOWN_REST_ACCESS" if kind == "REST" else "UNKNOWN_OPENING_HOURS",
                             "weekday": weekday, **common})
            elif not windows:
                gaps.append({"code": f"NO_{kind}_WINDOW", "weekday": weekday, **common})
            if now is None or duration is None or windows is None or not windows:
                now = None
                continue
            slot = next(((max(now, minutes(w.start)), max(now, minutes(w.start)) + duration)
                         for w in windows if max(now, minutes(w.start)) + duration <= minutes(w.end)), None)
            if slot is None:
                gaps.append({"code": f"NO_{kind}_WINDOW", "arrival": clock(now), **common})
                now = None
                continue
            start, end = slot
            if start > now:
                schedule.append({"type": "WAIT", "place_id": pid,
                                 "start_time": clock(now), "end_time": clock(start)})
            schedule.append({"type": kind, "place_id": pid,
                             "start_time": clock(start), "end_time": clock(end)})
            now = end
    return now, schedule, gaps


def source_route(route, catalog):
    days, gaps = [], []
    source_days = route["days"]
    buffer = route.get("buffer_minutes", 0)
    require(type(buffer) is int and buffer >= 0, "BUFFER_REQUIREMENT")
    require(len(source_days) in (3, 4), "SOURCE_DAY_COUNT")
    require(type(route["min_rest_minutes"]) is int and route["min_rest_minutes"] > 0, "REST_REQUIREMENT")
    departure = date.fromisoformat(route["departure_date"])
    require((date.fromisoformat(route["return_date"]) - departure).days + 1 == len(source_days), "SOURCE_DATE_RANGE")
    if route["data_status"] != "VERIFIED":
        gaps.append({"code": "ROUTE_NOT_VERIFIED"})
    for limitation in route["limitations"]:
        gaps.append({"code": "UNRESOLVED_ROUTE_LIMITATION", "detail": limitation})
    previous_end, seen_days = None, set()
    for number, day in enumerate(source_days, 1):
        did, sequence = day["day_id"], day["place_sequence"]
        common = {"day_id": did}
        require(did not in seen_days and day["day_number"] == number, "SOURCE_DAY_ORDER")
        seen_days.add(did)
        require(day["date"] == str(departure + timedelta(days=number - 1)), "SOURCE_DATE_ORDER")
        require(sequence and sequence[0] == day["start_place_id"] and sequence[-1] == day["end_place_id"], "SOURCE_ENDPOINTS")
        require(previous_end is None or previous_end == day["start_place_id"], "MISSING_OVERNIGHT_CONNECTION")
        require(minutes(day["start_time"]) < minutes(day["end_deadline"]), "SOURCE_CLOCK_RANGE")
        require(set(day["visit_place_ids"]) <= set(sequence) and
                all(r["place_id"] in sequence for r in day["rest_stops"]), "STOP_OUTSIDE_ROUTE")
        require(len(day["visit_place_ids"]) == len(set(day["visit_place_ids"])), "DUPLICATE_VISIT")
        require(len(day["rest_stops"]) == len({r["place_id"] for r in day["rest_stops"]}), "DUPLICATE_REST_STOP")
        require(all(type(r["duration_minutes"]) is int and r["duration_minutes"] > 0 for r in day["rest_stops"]), "REST_DURATION")
        if "stops" in day:
            declared = [{k: s[k] for k in ("type", "place_id", "duration_minutes") if k in s}
                        for s in day["stops"]]
            require(declared == ordered_stops(day), "SOURCE_STOPS_MISMATCH")
            require(stop_sequence(day, declared) == sequence, "SOURCE_STOPS_PATH_MISMATCH")
        rest = sum(r["duration_minutes"] for r in day["rest_stops"])
        require(rest >= route["min_rest_minutes"], f"REST_SHORTFALL: {did}")
        for pid in dict.fromkeys(sequence):
            gaps.extend(place_gaps(catalog.places[pid], {**common, "place_id": pid}))
        legs, leg_gaps = directed_legs(sequence, catalog, common)
        gaps.extend(leg_gaps)
        complete_legs = all(leg["duration_minutes"] is not None for leg in legs)
        travel_rest = sum(leg["duration_minutes"] for leg in legs) + rest if complete_legs else None
        known_visits = sum(catalog.places[pid].visit_duration_minutes or 0 for pid in day["visit_place_ids"])
        lower = travel_rest + known_visits if travel_rest is not None else None
        required = lower + buffer if lower is not None else None
        lower_finish = minutes(day["start_time"]) + required if required is not None else None
        if lower_finish is not None and lower_finish > minutes(day["end_deadline"]):
            gaps.append({"code": "LOWER_BOUND_LATE", **common,
                         "conditional_earliest_finish": clock(minutes(day["start_time"]) + lower),
                         "conditional_finish_including_buffer": clock(lower_finish),
                         "end_deadline": day["end_deadline"]})
        finish, schedule, slot_gaps = schedule_day(day, catalog)
        finish_with_buffer = finish + buffer if finish is not None else None
        gaps.extend(slot_gaps)
        weekday = DAYS[date.fromisoformat(day["date"]).weekday()]
        for label, pid, when in (("START", day["start_place_id"], minutes(day["start_time"])),
                                 ("END", day["end_place_id"], finish)):
            windows = catalog.places[pid].opening_hours.weekly[weekday]
            anchor = {**common, "place_id": pid, "weekday": weekday}
            if windows is None:
                gaps.append({"code": f"UNKNOWN_{label}_ACCESS", **anchor})
            elif not windows or (when is not None and not any(minutes(w.start) <= when <= minutes(w.end) for w in windows)):
                gaps.append({"code": f"{label}_CLOSED", **anchor})
        if finish_with_buffer is not None and finish_with_buffer > minutes(day["end_deadline"]):
            gaps.append({"code": "SCHEDULE_LATE", **common, "conditional_earliest_finish": clock(finish),
                         "conditional_finish_including_buffer": clock(finish_with_buffer),
                         "end_deadline": day["end_deadline"]})
        days.append({**common, "legs": legs, "travel_rest_lower_bound_minutes": travel_rest,
                     "known_visit_minutes": known_visits, "activity_lower_bound_minutes": lower,
                     "buffer_minutes": buffer, "required_lower_bound_minutes": required,
                     "conditional_lower_bound_finish_including_buffer": clock(lower_finish) if lower_finish is not None else None,
                     "conditional_earliest_finish": clock(finish) if finish is not None else None,
                     "conditional_finish_including_buffer": clock(finish_with_buffer) if finish_with_buffer is not None else None,
                     "earliest_schedule": schedule,
                     "note": "Ước tính có điều kiện; thiếu giờ/thời lượng thì lịch dừng tại đó. Buffer dự phòng riêng trước deadline; WAIT/buffer không tính REST. Cận dưới không phải lịch hợp lệ."})
        previous_end = day["end_place_id"]
    require(catalog.places[source_days[0]["start_place_id"]].area == "HCMC", "SOURCE_FIRST_DAY_NOT_HCMC")
    require(catalog.places[previous_end].area == "HCMC", "SOURCE_FINAL_DAY_NOT_HCMC")
    return {"route_id": route["route_id"], "day_count": len(source_days),
            "ready_for_real_plan": not gaps, "gaps": gaps, "days": days, "limitations": route["limitations"]}


def source_replacements(checks, catalog):
    reports = []
    require(checks and len({c["check_id"] for c in checks}) == len(checks), "SOURCE_ADAPT_COVERAGE")
    for check in checks:
        sequence = check["place_sequence"]
        replacement = check["replacement_place_id"]
        require(len(sequence) >= 3 and sequence[1] == replacement, "SOURCE_ADAPT_SEQUENCE")
        legs, gaps = directed_legs(sequence, catalog, {})
        for pid in dict.fromkeys(sequence):
            place = catalog.places[pid]
            gaps.extend(place_gaps(place, {"place_id": pid}))
            if pid == replacement:
                if place.environment != "INDOOR":
                    gaps.append({"code": "REPLACEMENT_NOT_INDOOR", "place_id": pid})
                if place.visit_duration_minutes is None:
                    gaps.append({"code": "UNKNOWN_VISIT_DURATION", "place_id": pid})
                if any(w is None for w in place.opening_hours.weekly.values()):
                    gaps.append({"code": "UNKNOWN_OPENING_HOURS", "place_id": pid})
        # These describe source coverage, not a complete itinerary/proposal.
        reports.append({"check_id": check["check_id"], "place_sequence": sequence,
                        "replacement_place_id": replacement, "legs": legs, "gaps": gaps,
                        "missing_pairs": [{"from_place_id": g["from_place_id"], "to_place_id": g["to_place_id"]}
                                          for g in gaps if g["code"] == "MISSING_LEG"],
                        "coverage_complete": not gaps, "ready_for_real_adapt": False,
                        "scope": "Kiểm độ phủ nguồn; còn cần lịch hiện hành/giờ cụ thể và F05 kiểm ràng buộc."})
    return reports
