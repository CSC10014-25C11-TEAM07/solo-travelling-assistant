"""Read-only adapter for Leader's 2026-11-09 data standard.

Does not alter Bảo 04's older Place models or silently promote SOURCED to VERIFIED.
"""

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from .models import AdaptError


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def minutes(value: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value):
        raise AdaptError("VALIDATION_ERROR", f"Giờ không hợp lệ: {value!r}; cần HH:mm.")
    h, m = map(int, value.split(":"))
    return h * 60 + m


def clock(value: int) -> str:
    if not 0 <= value < 1440:
        raise AdaptError("NO_FEASIBLE_ITINERARY", "Phương án vượt phạm vi cùng ngày.")
    return f"{value // 60:02d}:{value % 60:02d}"


@dataclass(frozen=True)
class RouteDay:
    day_id: str
    start_place_id: str
    end_place_id: str
    start_time: str
    end_deadline: str


class Catalog:
    def __init__(self, places: list[dict], travel_times: list[dict], routes: list[RouteDay],
                 *, mode: str = "VERIFIED"):
        if mode not in ("VERIFIED", "MOCK"):
            raise ValueError("mode must explicitly be VERIFIED or MOCK")
        self.mode = mode
        self.places = self._unique(deepcopy(places), lambda p: p["place_id"], "place_id")
        self.travel_times = self._unique(deepcopy(travel_times),
                                        lambda p: (p["from_place_id"], p["to_place_id"]), "chặng")
        self.routes = self._unique(list(routes), lambda r: r.day_id, "day_id cấu hình tuyến")
        for r in self.routes.values():
            if minutes(r.start_time) >= minutes(r.end_deadline):
                raise AdaptError("DATA_INCOMPLETE", f"Cấu hình giờ tuyến sai: {r.day_id}.")
    @property
    def version(self):
        # Recompute even if an integration test or loader changes an in-memory record.
        return fingerprint({"places": sorted(self.places.values(), key=lambda p: p["place_id"]),
                            "travel_times": sorted(self.travel_times.values(), key=lambda t: (t["from_place_id"], t["to_place_id"])),
                            "routes": [asdict(self.routes[k]) for k in sorted(self.routes)], "mode": self.mode})

    @staticmethod
    def _unique(items, key, label):
        result = {}
        for item in items:
            k = key(item)
            if k in result or not k:
                raise AdaptError("DATA_INCOMPLETE", f"Mã trống hoặc trùng: {label} {k}.")
            result[k] = item
        return result

    @classmethod
    def load(cls, directory: Path, routes: list[RouteDay], *, mode="VERIFIED"):
        return cls(json.loads((directory / "places.json").read_text(encoding="utf-8-sig")),
                   json.loads((directory / "travel_times.json").read_text(encoding="utf-8-sig")),
                   routes, mode=mode)

    def _usable(self, record, label):
        if record.get("data_status") != self.mode:
            raise AdaptError("DATA_INCOMPLETE", f"{label}: cần {self.mode}, đang là {record.get('data_status')}. "
                             "Có nguồn/SOURCED chưa đồng nghĩa VERIFIED.")
        if self.mode == "VERIFIED":
            try:
                timestamp = datetime.fromisoformat(record["checked_at"].replace("Z", "+00:00"))
                valid = timestamp.utcoffset() == timedelta(0)
                valid = valid and str(record["source_url"]).startswith(("https://", "http://"))
            except (KeyError, TypeError, ValueError, AttributeError):
                valid = False
            if not valid:
                raise AdaptError("DATA_INCOMPLETE", f"{label}: thiếu nguồn hoặc thời điểm kiểm tra UTC.")

    def place(self, place_id):
        place = self.places.get(place_id)
        if not place:
            raise AdaptError("DATA_INCOMPLETE", f"Thiếu địa điểm {place_id!r}.")
        self._usable(place, f"Địa điểm {place_id}")
        return place

    def travel(self, origin, destination):
        self.place(origin)
        self.place(destination)
        if origin == destination:
            return 0
        record = self.travel_times.get((origin, destination))
        if not record:
            raise AdaptError("DATA_INCOMPLETE", f"Thiếu chặng có hướng {origin} -> {destination}.")
        self._usable(record, f"Chặng {origin} -> {destination}")
        duration = record.get("duration_minutes")
        if type(duration) is not int or duration <= 0:
            raise AdaptError("DATA_INCOMPLETE", f"Thời lượng chặng {origin} -> {destination} không hợp lệ.")
        return duration

    def visit_slot(self, place_id, day_date, earliest):
        place = self.place(place_id)
        duration = place.get("visit_duration_minutes")
        if type(duration) is not int or duration <= 0:
            raise AdaptError("DATA_INCOMPLETE", f"Thiếu thời lượng chuẩn của {place_id}.")
        hours = place.get("opening_hours") or {}
        if hours.get("timezone") != "Asia/Ho_Chi_Minh":
            raise AdaptError("DATA_INCOMPLETE", f"Giờ mở cửa {place_id} thiếu múi giờ Việt Nam.")
        weekday = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")[date.fromisoformat(day_date).weekday()]
        intervals = (hours.get("weekly") or {}).get(weekday)
        if intervals is None:
            raise AdaptError("DATA_INCOMPLETE", f"Chưa biết giờ mở cửa {place_id} vào {weekday}.")
        previous = -1
        windows = []
        for interval in intervals:
            start, end = minutes(interval["start"]), minutes(interval["end"])
            if start >= end or start < previous:
                raise AdaptError("DATA_INCOMPLETE", f"Khoảng mở cửa {place_id} sai hoặc chồng lấn.")
            previous = end
            windows.append((start, end))
        for start, end in windows:
            proposed_start = max(earliest, start)
            if proposed_start + duration <= end:
                return proposed_start, proposed_start + duration
        raise AdaptError("NO_FEASIBLE_ITINERARY", f"{place_id} đóng cửa hoặc không đủ {duration} phút tham quan.")
