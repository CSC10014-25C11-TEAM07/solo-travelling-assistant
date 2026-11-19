"""Bounded F02 provider. The caller supplies the catalog and route templates."""

from copy import deepcopy
from datetime import timedelta
from itertools import islice, permutations, product

from adapt_f05.catalog import checked_buffer, clock, minutes
from adapt_f05.models import AdaptError
from adapt_f05.ranking import GeminiRanker, RankingError, checked_ranking
from itinerary_api import APIError


class PlanProvider:
    """Callable compatible with create_app(plan_provider=...).

    Each template has start/end place, start/deadline and a list of fixed
    REST/VISIT stops. Adjacent visits can be reordered, never across a rest.
    """

    def __init__(self, catalog, templates, ranker=None):
        self.catalog = catalog
        self.templates = deepcopy(templates)
        self.ranker = ranker

    def __call__(self, request):
        try:
            return self.generate(request)
        except AdaptError as error:
            raise APIError(error.status, error.code, error.message) from error
        except RankingError as error:
            raise APIError(error.status, error.code, str(error)) from error

    def generate(self, request):
        days_count = (request.return_date - request.departure_date).days + 1
        route = self.templates.get(days_count)
        if not route or len(route["days"]) != days_count:
            raise AdaptError("DATA_INCOMPLETE", f"Thiếu cấu hình tuyến {days_count} ngày.")
        if route["data_status"] != self.catalog.mode:
            raise AdaptError("DATA_INCOMPLETE", f"Tuyến {route.get('route_id')} là {route['data_status']}, cần {self.catalog.mode}.")
        if route["days"][0]["start_place_id"] != route["days"][-1]["end_place_id"]:
            raise AdaptError("DATA_INCOMPLETE", "Tuyến đi/về phải kết thúc tại điểm xuất phát.")
        checked_buffer(route.get("buffer_minutes", 0))

        alternatives = []
        diagnostics = []
        for number, config in enumerate(route["days"]):
            variants = []
            for stops in self._variants(config["stops"]):
                try:
                    variants.append(self._schedule(request, config, stops, number))
                except AdaptError as error:
                    diagnostics.append(error)
            if not variants:
                error = next((e for e in diagnostics if e.code == "DATA_INCOMPLETE"), None)
                if error:
                    raise error
                raise AdaptError("NO_FEASIBLE_ITINERARY", f"Ngày {number + 1} không có lịch hợp lệ trong phạm vi tìm kiếm.")
            alternatives.append(variants)

        plans = list(islice(product(*alternatives), 8))
        context = {
            "request": {"trip_days": days_count, "departure_time": request.departure_time,
                        "min_rest_minutes": request.min_rest_minutes},
            "interests": list(request.interests),
            "candidates": [],
        }
        for index, plan in enumerate(plans):
            visits = [a["name"] for day in plan for a in day["activities"] if a["type"] == "VISIT"]
            context["candidates"].append({
                "candidate_id": str(index),
                "facts": {"VALID": "Địa điểm theo thứ tự: " + ", ".join(visits),
                          "TRADEOFF": "Các giờ và chặng đã được Python kiểm tra."},
            })
        ranker = self.ranker or GeminiRanker()
        ranking = checked_ranking(ranker.rank(context), context)
        return deepcopy(list(plans[int(ranking[0]["candidate_id"])]))

    @staticmethod
    def _variants(stops):
        groups, pending = [], []
        for stop in stops:
            if stop["type"] == "VISIT":
                pending.append(stop)
                if len(pending) > 4:
                    raise AdaptError("DATA_INCOMPLETE", "Một nhóm VISIT vượt giới hạn 4 điểm.")
            elif stop["type"] == "REST":
                if pending:
                    groups.append(list(permutations(pending)))
                    pending = []
                groups.append([(stop,)])
            else:
                raise AdaptError("DATA_INCOMPLETE", "Mẫu tuyến chỉ nhận REST và VISIT.")
        if pending:
            groups.append(list(permutations(pending)))
        if not groups:
            raise AdaptError("DATA_INCOMPLETE", "Mẫu tuyến thiếu điểm nghỉ và tham quan.")
        for index, combination in enumerate(product(*groups)):
            if index >= 24:
                break
            yield [stop for group in combination for stop in group]

    def _schedule(self, request, config, stops, number):
        if number and config["start_place_id"] != self.templates[
                (request.return_date - request.departure_date).days + 1]["days"][number - 1]["end_place_id"]:
            raise AdaptError("DATA_INCOMPLETE", f"Điểm đầu ngày {number + 1} không khớp điểm cuối ngày trước.")
        start = minutes(config["start_time"])
        cursor = max(start, minutes(request.departure_time)) if number == 0 else start
        deadline = minutes(config["end_deadline"])
        date = (request.departure_date + timedelta(days=number)).isoformat()
        previous = config["start_place_id"]
        cursor = self.catalog.access_time(previous, date, cursor, allow_wait=True)
        route = self.templates[(request.return_date - request.departure_date).days + 1]
        buffer = checked_buffer(route.get("buffer_minutes", 0))
        activities, rest = [], 0

        def travel(destination):
            nonlocal cursor, previous
            duration = self.catalog.travel(previous, destination)
            if duration:
                finish = cursor + duration
                origin_name = self.catalog.place(previous)["name"]
                destination_name = self.catalog.place(destination)["name"]
                activities.append({"type": "TRAVEL", "name": f"Di chuyển {origin_name} → {destination_name}",
                                   "place_id": None, "start_time": clock(cursor), "end_time": clock(finish),
                                   "is_optional": False})
                cursor = finish
            previous = destination

        for stop in stops:
            place = self.catalog.place(stop["place_id"])
            travel(stop["place_id"])
            if stop["type"] == "VISIT":
                begin, end = self.catalog.visit_slot(stop["place_id"], date, cursor)
                optional = bool(stop.get("is_optional", True))
            else:
                duration = stop.get("duration_minutes")
                if type(duration) is not int or duration <= 0:
                    raise AdaptError("DATA_INCOMPLETE", f"Thiếu thời lượng nghỉ tại {stop['place_id']}.")
                begin, end = self.catalog.activity_slot(stop["place_id"], date, cursor, duration)
                optional = False
                rest += duration
            activities.append({"type": stop["type"], "name": place["name"], "place_id": stop["place_id"],
                               "start_time": clock(begin), "end_time": clock(end), "is_optional": optional})
            cursor = end
        arrives_at_end = previous != config["end_place_id"]
        travel(config["end_place_id"])
        if arrives_at_end:
            self.catalog.access_time(config["end_place_id"], date, cursor)
        if rest < request.min_rest_minutes:
            raise AdaptError("NO_FEASIBLE_ITINERARY", f"Ngày {number + 1} chỉ có {rest} phút nghỉ.")
        if cursor + buffer > deadline:
            raise AdaptError("NO_FEASIBLE_ITINERARY", f"Ngày {number + 1} về {clock(cursor)}, không còn {buffer} phút dự phòng trước {config['end_deadline']}.")
        return {"date": date, "end_deadline": config["end_deadline"], "activities": activities}


def mock_templates(routes, snapshots):
    """Build explicit MOCK templates from Bảo 04's handoff without altering it."""
    result = {}
    for route in routes:
        if route["data_status"] != "MOCK":
            raise AdaptError("DATA_INCOMPLETE", "Chỉ dùng fixture MOCK cho mock_templates.")
        snapshot = snapshots[route["route_id"]]
        days = []
        for config, fixture in zip(route["days"], snapshot["days"], strict=True):
            stops = []
            for activity in fixture["activities"]:
                if activity["type"] in ("REST", "VISIT"):
                    stop = {"type": activity["type"], "place_id": activity["place_id"],
                            "is_optional": activity["is_optional"]}
                    if stop["type"] == "REST":
                        stop["duration_minutes"] = minutes(activity["end_time"]) - minutes(activity["start_time"])
                    stops.append(stop)
            days.append({**config, "stops": stops})
        result[len(days)] = {"route_id": route["route_id"], "data_status": "MOCK", "days": days,
                             "buffer_minutes": checked_buffer(route.get("buffer_minutes", 0))}
    return result
