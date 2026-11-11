"""Bounded, deterministic scheduling; the ranker never controls times or IDs."""

from collections import defaultdict, deque
from copy import deepcopy
from datetime import date, timedelta
from itertools import combinations
from uuid import UUID, uuid4, uuid5

from pydantic import ValidationError

from .catalog import Catalog, clock, fingerprint, minutes
from .models import REQUEST, AdaptError, AdaptResult, Candidate, RainRequest, RestRequest
from .ranking import RankingError, RuleRanker, checked_ranking

ACTIVE = {"PENDING", "DONE"}
ACTIVITY_FIELDS = {"activity_id", "day_id", "type", "name", "place_id", "start_time", "end_time",
                   "status", "is_optional", "replaces_activity_id", "completed_at"}


def active(day):
    return sorted((a for a in day["activities"] if a["status"] in ACTIVE),
                  key=lambda a: (a["start_time"], a["activity_id"]))


def validate_snapshot(itinerary):
    """Structural checks only. Historical DONE values are never rewritten."""
    try:
        if itinerary["status"] != "CURRENT":
            raise AdaptError("NOT_CURRENT_ITINERARY", "ADAPT cần lịch CURRENT.", status=409)
        if type(itinerary["version"]) is not int or itinerary["version"] < 1:
            raise ValueError("version")
        minimum = itinerary["min_rest_minutes"]
        if type(minimum) is not int or minimum <= 0:
            raise ValueError("min_rest_minutes")
        first, last = date.fromisoformat(itinerary["departure_date"]), date.fromisoformat(itinerary["return_date"])
        if first.isoformat() != itinerary["departure_date"] or last.isoformat() != itinerary["return_date"]:
            raise ValueError("dates must use YYYY-MM-DD")
        count = (last - first).days + 1
        if count not in (3, 4) or len(itinerary["days"]) != count:
            raise ValueError("days: cần toàn bộ lịch 3/4 ngày, không dùng fixture một ngày trực tiếp")
        ids, day_ids = set(), set()
        for number, day in enumerate(itinerary["days"], 1):
            if (not day["day_id"] or day["day_id"] in day_ids or day["day_number"] != number
                    or day["date"] != (first + timedelta(days=number - 1)).isoformat()
                    or day["itinerary_id"] != itinerary["itinerary_id"]):
                raise ValueError("day metadata")
            day_ids.add(day["day_id"])
            deadline = minutes(day["end_deadline"])
            for a in day["activities"]:
                if (set(a) != ACTIVITY_FIELDS or not isinstance(a["activity_id"], str)
                        or not a["activity_id"] or a["activity_id"] in ids or a["day_id"] != day["day_id"]
                        or a["type"] not in ("VISIT", "REST", "TRAVEL")
                        or a["status"] not in ("PENDING", "DONE", "DROPPED", "REPLACED")
                        or type(a["is_optional"]) is not bool
                        or not isinstance(a["name"], str) or not a["name"]
                        or (a["type"] == "VISIT" and (not isinstance(a["place_id"], str) or not a["place_id"]))
                        or minutes(a["start_time"]) >= minutes(a["end_time"])):
                    raise ValueError(f"activity {a.get('activity_id')}")
                ids.add(a["activity_id"])
                if a["status"] == "PENDING" and a["completed_at"] is not None:
                    raise ValueError("PENDING completed_at")
            end, rest = -1, 0
            for a in active(day):
                start, finish = minutes(a["start_time"]), minutes(a["end_time"])
                if start < end or finish > deadline:
                    raise ValueError(f"Chồng giờ/vượt hạn ngày {day['day_id']}")
                end = finish
                if a["type"] == "REST":
                    rest += finish - start
            if rest < minimum:
                raise ValueError(f"Thiếu tổng nghỉ trong ngày {day['day_id']}")
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, AdaptError):
            raise
        raise AdaptError("DATA_INCOMPLETE", f"Lịch đầu vào chưa đủ/không đúng chuẩn: {error}.") from None


class AdaptEngine:
    def __init__(self, catalog: Catalog, *, ranker=None, allow_ai_fallback=True,
                 max_optional_visits=8, max_drops=2, max_indoor_candidates=12):
        self.catalog = catalog
        self.ranker = ranker or RuleRanker()
        self.allow_ai_fallback = allow_ai_fallback
        # Fixed small limits keep enumeration and the prompt affordable.
        if not 0 <= max_optional_visits <= 8 or not 0 <= max_drops <= 2 or not 1 <= max_indoor_candidates <= 12:
            raise ValueError("Unsupported search limits")
        self.max_optional_visits = max_optional_visits
        self.max_drops = max_drops
        self.max_indoor_candidates = max_indoor_candidates

    def _prepare(self, itinerary, request):
        validate_snapshot(itinerary)
        if request.base_version != itinerary["version"]:
            raise AdaptError("STALE_ITINERARY", "Lịch đã đổi; hãy đọc lại phiên bản mới.", status=409)
        target_id = request.rest_activity_id if isinstance(request, RestRequest) else request.activity_id
        found = [(day, a) for day in itinerary["days"] for a in day["activities"] if a["activity_id"] == target_id]
        if not found:
            raise AdaptError("NOT_FOUND", "Không có hoạt động trong lịch này.", status=404)
        day, target = found[0]
        expected_type = "REST" if isinstance(request, RestRequest) else "VISIT"
        if target["status"] != "PENDING" or target["type"] != expected_type:
            raise AdaptError("ACTIVITY_NOT_ACTIVE", "Hoạt động phải đúng loại và còn PENDING.", status=409)
        route = self.catalog.routes.get(day["day_id"])
        if route is None:
            raise AdaptError("DATA_INCOMPLETE", f"Thiếu cấu hình điểm đầu/cuối ngày {day['day_id']}.")
        if route.end_deadline != day["end_deadline"]:
            raise AdaptError("DATA_INCOMPLETE", "Hạn kết thúc lịch không khớp cấu hình tuyến.")
        self.catalog.place(route.start_place_id)
        self.catalog.place(route.end_place_id)
        self.catalog.place(target["place_id"])
        ordered = active(day)
        if minutes(ordered[0]["start_time"]) < minutes(route.start_time):
            raise AdaptError("DATA_INCOMPLETE", "Giờ bắt đầu lịch sớm hơn cấu hình tuyến.")
        for item in ordered:
            if item["place_id"] is not None and item["place_id"] not in self.catalog.places:
                raise AdaptError("DATA_INCOMPLETE", f"Hoạt động {item['activity_id']} tham chiếu điểm không tồn tại.")
        index = next(i for i, a in enumerate(ordered) if a["activity_id"] == target_id)
        if isinstance(request, RestRequest):
            if minutes(request.rest_until) <= minutes(target["end_time"]):
                raise AdaptError("VALIDATION_ERROR", "rest_until phải sau giờ kết thúc khoảng nghỉ đã chọn.")
            if request.preferred_keep_activity_id:
                keep = next((a for a in ordered[index + 1:] if a["activity_id"] == request.preferred_keep_activity_id), None)
                if not keep or keep["status"] != "PENDING" or keep["type"] != "VISIT":
                    raise AdaptError("VALIDATION_ERROR", "Hoạt động ưu tiên phải là VISIT PENDING phía sau trong cùng ngày.")
            anchor_index = index
        else:
            if self.catalog.place(target["place_id"]).get("environment") != "OUTDOOR":
                raise AdaptError("VALIDATION_ERROR", "Đổi vì mưa chỉ nhận VISIT OUTDOOR trong bản đầu.")
            anchor_index = next((i for i in range(index - 1, -1, -1) if ordered[i]["type"] != "TRAVEL"), -1)
        if any(a["status"] == "DONE" for a in ordered[anchor_index + 1:]):
            raise AdaptError("NO_FEASIBLE_ITINERARY", "Phần cần tính lại có hoạt động DONE.")
        return day, target, route, ordered, anchor_index

    def generate(self, itinerary: dict, payload: dict) -> AdaptResult:
        try:
            request = REQUEST.validate_python(payload)
        except ValidationError:
            raise AdaptError("VALIDATION_ERROR", "Yêu cầu ADAPT sai trường, kiểu dữ liệu hoặc định dạng giờ.") from None
        day, target, route, ordered, anchor_index = self._prepare(itinerary, request)
        candidates, diagnostics = [], []
        request_dict = request.model_dump()

        def try_candidate(drops=(), replacement=None):
            try:
                candidates.append(self._build(itinerary, request, drops, replacement, str(uuid4())))
            except AdaptError as error:
                if len(diagnostics) < 40:
                    diagnostics.append({**error.to_dict(), "dropped_ids": list(drops), "replacement_place_id": replacement})

        if isinstance(request, RestRequest):
            optional = sorted(a["activity_id"] for a in ordered[anchor_index + 1:]
                              if a["type"] == "VISIT" and a["status"] == "PENDING" and a["is_optional"])
            if len(optional) > self.max_optional_visits:
                raise AdaptError("SEARCH_LIMIT", "Có quá nhiều VISIT tùy chọn cho phạm vi tìm kiếm bản đầu.")
            for count in range(min(len(optional), self.max_drops) + 1):
                for drops in combinations(optional, count):
                    try_candidate(drops)
                if candidates:  # Never drop extra visits when fewer drops are feasible.
                    break
        else:
            indoor = sorted(p["place_id"] for p in self.catalog.places.values()
                            if p.get("environment") == "INDOOR" and p.get("interests")
                            and p["place_id"] != target["place_id"])
            for place_id in indoor[:self.max_indoor_candidates]:
                try_candidate(replacement=place_id)
            if len(indoor) > self.max_indoor_candidates:
                diagnostics.append({"code": "SEARCH_LIMIT", "message": "Chỉ xét 12 điểm trong nhà đầu tiên theo ID."})
        if not candidates:
            reason = "Không tìm được phương án trong phạm vi tìm kiếm đã giới hạn. "
            # Surface missing data before timing failures; one closed alternative
            # must not conceal an actionable missing directed leg on another.
            messages = list(dict.fromkeys(d["message"] for d in sorted(
                diagnostics, key=lambda d: d["code"] != "DATA_INCOMPLETE")))
            reason += " ".join(messages[:3]) if messages else "Dataset không có điểm trong nhà phù hợp."
            return AdaptResult(itinerary["itinerary_id"], request.type, request.base_version, self.catalog.version,
                               self.catalog.mode, [], reason, diagnostics, {"mode": "NOT_CALLED"})
        candidates.sort(key=lambda c: (bool(isinstance(request, RestRequest) and request.preferred_keep_activity_id in c.dropped_ids),
                                       len(c.dropped_ids), c.estimated_end_time, tuple(c.dropped_ids), c.replacement_place_id or ""))
        context = {"request": request_dict, "interests": list(itinerary.get("interests", [])),
                   "candidates": [{"candidate_id": c.candidate_id, "facts": deepcopy(c.facts)} for c in candidates]}
        try:
            output = self.ranker.rank(deepcopy(context))
            ranking = checked_ranking(output, context)
            audit = {"mode": self.ranker.mode, **getattr(self.ranker, "audit", {})}
        except RankingError as error:
            if not self.allow_ai_fallback:
                raise AdaptError(error.code, str(error), status=error.status) from None
            ranking = checked_ranking(RuleRanker().rank(context), context)
            audit = {"mode": "RULE_FALLBACK", "failure_code": error.code}
        by_id = {c.candidate_id: c for c in candidates}
        selected = []
        for entry in ranking[:2]:
            c = by_id[entry["candidate_id"]]
            c.reason = " ".join(c.facts[code] for code in entry["reason_codes"])
            c.tradeoff = c.facts[entry["tradeoff_code"]]
            if not validate_candidate(itinerary, c, self.catalog):
                raise AdaptError("AI_INVALID_OUTPUT", "Phương án thay đổi sau kiểm tra; không trả kết quả.", status=502)
            selected.append(c)
        return AdaptResult(itinerary["itinerary_id"], request.type, request.base_version, self.catalog.version,
                           self.catalog.mode, selected, None, diagnostics, audit)

    def _build(self, itinerary, request, drops, replacement, candidate_id):
        day, target, route, ordered, anchor_index = self._prepare(itinerary, request)
        drops = set(drops)
        permitted = {a["activity_id"] for a in ordered[anchor_index + 1:]
                     if a["type"] == "VISIT" and a["is_optional"] and a["status"] == "PENDING"}
        if not drops <= permitted or (isinstance(request, RainRequest) and drops):
            raise AdaptError("VALIDATION_ERROR", "Chỉ DROP VISIT tùy chọn phía sau khi nghỉ thêm.")
        if isinstance(request, RainRequest):
            if self.catalog.place(replacement).get("environment") != "INDOOR":
                raise AdaptError("VALIDATION_ERROR", "Điểm thay thế phải INDOOR.")
        elif replacement is not None:
            raise AdaptError("VALIDATION_ERROR", "Nghỉ thêm không được thay địa điểm.")
        namespace = UUID(candidate_id)
        prefix = deepcopy(ordered[:anchor_index + 1])
        if isinstance(request, RestRequest):
            prefix[-1]["end_time"] = request.rest_until
        previous_place = prefix[-1]["place_id"] if prefix else route.start_place_id
        cursor = minutes(prefix[-1]["end_time"]) if prefix else minutes(route.start_time)
        preserved = [deepcopy(a) for a in day["activities"] if a["status"] not in ACTIVE]
        rebuilt = prefix
        old_edges = self._travel_edges(ordered, route)
        suffix_travel = {a["activity_id"]: a for a in ordered[anchor_index + 1:] if a["type"] == "TRAVEL"}
        reusable = defaultdict(deque)
        for aid, row in suffix_travel.items():
            reusable[old_edges[aid]].append(row)
        new_edges = {a["activity_id"]: old_edges[a["activity_id"]] for a in prefix if a["type"] == "TRAVEL"}

        def travel_to(destination):
            nonlocal cursor, previous_place
            duration = self.catalog.travel(previous_place, destination)
            if duration:
                matching = reusable.get((previous_place, destination))
                if matching:
                    row = deepcopy(matching.popleft())
                else:
                    row = {"activity_id": str(uuid5(namespace, f"travel:{len(rebuilt)}:{previous_place}:{destination}")),
                           "day_id": day["day_id"], "type": "TRAVEL", "name": "Di chuyển theo chặng đã kiểm tra",
                           "place_id": None, "status": "PENDING", "is_optional": False,
                           "replaces_activity_id": None, "completed_at": None}
                row.update(start_time=clock(cursor), end_time=clock(cursor + duration))
                new_edges[row["activity_id"]] = (previous_place, destination)
                rebuilt.append(row)
                cursor += duration
            previous_place = destination

        for original in ordered[anchor_index + 1:]:
            if original["type"] == "TRAVEL":
                continue
            row = deepcopy(original)
            if row["activity_id"] in drops:
                row["status"] = "DROPPED"
                preserved.append(row)
                continue
            if isinstance(request, RainRequest) and row["activity_id"] == target["activity_id"]:
                old = deepcopy(row)
                old["status"] = "REPLACED"
                preserved.append(old)
                row.update(activity_id=str(uuid5(namespace, "replacement:" + target["activity_id"])),
                           place_id=replacement, name=self.catalog.place(replacement)["name"],
                           replaces_activity_id=target["activity_id"], completed_at=None, status="PENDING")
            travel_to(row["place_id"])
            earliest = max(cursor, minutes(original["start_time"]))
            if row["type"] == "VISIT":
                start, finish = self.catalog.visit_slot(row["place_id"], day["date"], earliest)
            else:
                duration = minutes(original["end_time"]) - minutes(original["start_time"])
                start, finish = earliest, earliest + duration
            row.update(start_time=clock(start), end_time=clock(finish))
            rebuilt.append(row)
            cursor = finish
        travel_to(route.end_place_id)
        if cursor > minutes(route.end_deadline):
            raise AdaptError("NO_FEASIBLE_ITINERARY", f"Đến điểm kết thúc lúc {clock(cursor)}, vượt hạn {route.end_deadline}.")
        # Retired legs retain their original ID, times and metadata in history.
        for aid, row in suffix_travel.items():
            if aid not in new_edges:
                preserved.append({**row, "status": "REPLACED"})
        proposed_days = deepcopy(itinerary["days"])
        changed_day = next(d for d in proposed_days if d["day_id"] == day["day_id"])
        changed_day["activities"] = sorted(rebuilt + preserved, key=lambda a: (a["start_time"], a["activity_id"]))
        validate_snapshot({**itinerary, "days": proposed_days})
        changes, travel_changes = self._diff(day, changed_day, old_edges, new_edges)
        dropped_names = [a["name"] for a in ordered if a["activity_id"] in drops]
        tradeoff = ("Bỏ: " + ", ".join(dropped_names) + ".") if drops else "Không bỏ hoạt động tham quan nào."
        if replacement:
            tradeoff = "Thay trải nghiệm ngoài trời bằng địa điểm trong nhà; chặng đường vẫn có thể gặp mưa."
        facts = {"VALID": "Đã kiểm tra giờ mở cửa, chặng đi, tổng nghỉ và hạn kết thúc.",
                 "END": f"Đến điểm kết thúc dự kiến lúc {clock(cursor)}, hạn {route.end_deadline}.",
                 "TRADEOFF": tradeoff}
        if isinstance(request, RestRequest):
            facts["REST"] = f"Kéo dài đúng khoảng nghỉ đã chọn đến {request.rest_until}."
            if request.preferred_keep_activity_id and request.preferred_keep_activity_id not in drops:
                facts["KEEP"] = "Giữ được hoạt động người dùng ưu tiên."
        else:
            facts["INDOOR"] = f"Thay bằng {self.catalog.place(replacement)['name']}, trải nghiệm chính trong nhà."
        return Candidate(candidate_id, request.model_dump(), sorted(drops), replacement, proposed_days,
                         changes, travel_changes, clock(cursor), self.catalog.version, fingerprint(itinerary), facts)

    @staticmethod
    def _travel_edges(ordered, route):
        edges, origin = {}, route.start_place_id
        for i, a in enumerate(ordered):
            if a["type"] != "TRAVEL":
                origin = a["place_id"]
                continue
            if i + 1 < len(ordered) and ordered[i + 1]["type"] == "TRAVEL":
                raise AdaptError("DATA_INCOMPLETE", "Hai TRAVEL liên tiếp thiếu điểm neo; cần chuẩn hóa dữ liệu.")
            destination = next((b["place_id"] for b in ordered[i + 1:] if b["type"] != "TRAVEL"), route.end_place_id)
            edges[a["activity_id"]] = (origin, destination)
        return edges

    @staticmethod
    def _diff(before_day, after_day, old_edges, new_edges):
        before = {a["activity_id"]: a for a in before_day["activities"]}
        after = {a["activity_id"]: a for a in after_day["activities"]}
        changes, travel = [], []
        for aid in sorted(before.keys() | after.keys()):
            old, new = before.get(aid), after.get(aid)
            if old == new:
                continue
            if (old or new)["type"] == "TRAVEL":
                if old is None:
                    operation = "ADD"
                elif new["status"] == "REPLACED":
                    operation = "REPLACE"
                else:
                    operation = "RESCHEDULE"
                travel.append({"activity_id": aid, "operation": operation,
                               "before": deepcopy(old), "after": deepcopy(new),
                               "before_edge": list(old_edges[aid]) if aid in old_edges else None,
                               "after_edge": list(new_edges[aid]) if aid in new_edges else None})
            elif old is None:
                # Replacement is represented by the old row's REPLACE_LOCATION change.
                if not new["replaces_activity_id"]:
                    changes.append({"activity_id": aid, "change_type": "ADD", "before": None, "after": deepcopy(new)})
            elif new["status"] == "DROPPED":
                changes.append({"activity_id": aid, "change_type": "DROP", "before": deepcopy(old), "after": None})
            elif new["status"] == "REPLACED":
                replacement = next(a for a in after.values() if a["replaces_activity_id"] == aid and a["status"] == "PENDING")
                changes.append({"activity_id": aid, "change_type": "REPLACE_LOCATION", "before": deepcopy(old), "after": deepcopy(replacement)})
            else:
                kind = "EXTEND_REST" if old["type"] == "REST" and old["end_time"] != new["end_time"] and old["start_time"] == new["start_time"] else "RESCHEDULE"
                changes.append({"activity_id": aid, "change_type": kind, "before": deepcopy(old), "after": deepcopy(new)})
        return changes, travel


def validate_candidate(itinerary: dict, candidate: Candidate, catalog: Catalog) -> bool:
    """Recompute from the trusted stored snapshot and fresh dataset, never from AI times.

    An F06 adapter must load this INTERNAL record server-side. It must not accept
    a candidate or route configuration supplied by the mobile client.
    """
    try:
        if candidate.base_fingerprint != fingerprint(itinerary) or candidate.dataset_version != catalog.version:
            return False
        request = REQUEST.validate_python(candidate.request)
        expected = AdaptEngine(catalog)._build(itinerary, request, candidate.dropped_ids,
                                               candidate.replacement_place_id, candidate.candidate_id)
        return all(getattr(candidate, key) == getattr(expected, key) for key in
                   ("proposed_days", "changes", "travel_changes", "estimated_end_time", "facts"))
    except (AdaptError, ValidationError, KeyError, ValueError, TypeError, AttributeError, IndexError):
        return False
