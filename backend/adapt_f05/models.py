"""Internal domain types, deliberately separate from the frozen public API V1."""

from dataclasses import asdict, dataclass, field
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, TypeAdapter

Clock = Annotated[str, Field(pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")]
Identifier = Annotated[str, Field(min_length=1, max_length=200)]


class AdaptError(ValueError):
    def __init__(self, code: str, message: str, *, status: int = 422):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status

    def to_dict(self):
        return {"code": self.code, "message": self.message}


class RestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    type: Literal["EXTEND_REST"]
    base_version: StrictInt = Field(ge=1)
    rest_activity_id: Identifier
    rest_until: Clock
    preferred_keep_activity_id: Identifier | None = None


class RainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    type: Literal["REPLACE_LOCATION"]
    base_version: StrictInt = Field(ge=1)
    activity_id: Identifier
    reason: Literal["RAIN"]


REQUEST = TypeAdapter(Annotated[RestRequest | RainRequest, Field(discriminator="type")])


@dataclass
class Candidate:
    candidate_id: str
    request: dict
    dropped_ids: list[str]
    replacement_place_id: str | None
    proposed_days: list[dict]
    changes: list[dict]
    # TRAVEL changes are separate from DROP/REPLACE_LOCATION for visits.
    travel_changes: list[dict]
    estimated_end_time: str
    dataset_version: str
    base_fingerprint: str
    facts: dict[str, str] = field(default_factory=dict)
    reason: str = ""
    tradeoff: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class AdaptResult:
    itinerary_id: str
    type: str
    base_version: int
    dataset_version: str
    data_mode: str
    candidates: list[Candidate]
    no_option_reason: str | None
    diagnostics: list[dict]
    ranking: dict
    # Explicitly not a persisted proposal_id/option_id suitable for ACCEPT.
    contract: str = "F05_DOMAIN_PREVIEW_V1"

    def to_dict(self):
        return asdict(self)
