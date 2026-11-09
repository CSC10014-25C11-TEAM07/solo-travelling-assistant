"""Dataset v0.1 proposals; field names follow the 2026-11-06 team contract."""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Interest = Literal["nature", "coffee", "culture", "food"]
Environment = Literal["INDOOR", "OUTDOOR", "MIXED", "UNKNOWN"]
DataStatus = Literal["SOURCED", "MOCK", "UNVERIFIED"]
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
INTEREST_LABELS = {
    "nature": "thiên nhiên",
    "coffee": "cà phê",
    "culture": "văn hóa, tham quan",
    "food": "ẩm thực",
}


class DatasetModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TimeWindow(DatasetModel):
    start: str
    end: str

    @field_validator("start", "end")
    @classmethod
    def valid_time(cls, value):
        if not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", value):
            raise ValueError("Use HH:mm in Vietnam local time")
        return value

    @model_validator(mode="after")
    def ordered(self):
        if self.start >= self.end:
            raise ValueError("Split overnight opening hours across calendar days")
        return self


class OpeningHours(DatasetModel):
    timezone: Literal["Asia/Ho_Chi_Minh"]
    weekly: dict[str, list[TimeWindow] | None]

    @field_validator("weekly")
    @classmethod
    def valid_week(cls, value):
        if set(value) != set(DAYS):
            raise ValueError("weekly must contain mon through sun; null means unknown")
        for intervals in value.values():
            if intervals is None:
                continue
            previous_end = "00:00"
            for interval in intervals:
                if interval.start < previous_end:
                    raise ValueError("Opening intervals must be ordered and not overlap")
                previous_end = interval.end
        return value


def checked_timestamp(value):
    if value is not None:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("checked_at must include a timezone")
    return value


def source_url(value):
    if value is not None and not value.startswith(("https://", "http://")):
        raise ValueError("Expected an HTTP(S) source URL")
    return value


class Place(DatasetModel):
    place_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    area: str = Field(min_length=1)
    interests: list[Interest]
    environment: Environment
    visit_duration_minutes: int | None = Field(ge=1)
    opening_hours: OpeningHours
    image_url: str | None
    source_url: str | None
    checked_at: str | None
    data_status: DataStatus

    _checked = field_validator("checked_at")(checked_timestamp)
    _source = field_validator("source_url", "image_url")(source_url)

    @model_validator(mode="after")
    def consistent_source(self):
        if len(self.interests) != len(set(self.interests)):
            raise ValueError("Duplicate interest tags")
        if self.data_status == "SOURCED":
            if not self.source_url or not self.checked_at:
                raise ValueError("SOURCED records need a source and checked_at")
            if self.environment == "UNKNOWN" or self.visit_duration_minutes is None:
                raise ValueError("Incomplete places must remain UNVERIFIED")
            if any(value is None for value in self.opening_hours.weekly.values()):
                raise ValueError("Unknown weekly hours require UNVERIFIED status")
        return self


class TravelTime(DatasetModel):
    # null on delivery: SQLite generates the identifier when importing.
    travel_time_id: str | None
    from_place_id: str = Field(min_length=1)
    to_place_id: str = Field(min_length=1)
    duration_minutes: int = Field(ge=0)
    source_url: str | None
    checked_at: str | None
    data_status: DataStatus

    _checked = field_validator("checked_at")(checked_timestamp)
    _source = field_validator("source_url")(source_url)

    @model_validator(mode="after")
    def consistent_leg(self):
        same_place = self.from_place_id == self.to_place_id
        if same_place != (self.duration_minutes == 0):
            raise ValueError("Only same-place legs may have zero duration")
        if self.data_status == "SOURCED" and (not self.source_url or not self.checked_at):
            raise ValueError("SOURCED travel times need a source and checked_at")
        return self
