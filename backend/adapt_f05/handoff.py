"""F05 public preview and server-side records for the F06 validator."""

from copy import deepcopy
from uuid import uuid4

from .engine import validate_candidate
from .models import AdaptError, AdaptResult, Candidate


def to_api_v1(result: AdaptResult, itinerary, catalog):
    """Build the public response; its IDs become usable after the server saves it."""
    if result.base_version != itinerary["version"] or result.itinerary_id != itinerary["itinerary_id"]:
        raise AdaptError("STALE_ITINERARY", "Lịch đã thay đổi trước bước lưu đề xuất.", status=409)
    if result.dataset_version != catalog.version:
        raise AdaptError("DATA_INCOMPLETE", "Dataset đã thay đổi; cần tạo lại phương án.")
    options = []
    for candidate in result.candidates:
        if not validate_candidate(itinerary, candidate, catalog):
            raise AdaptError("PROPOSAL_NO_LONGER_VALID", "Phương án không còn hợp lệ.", status=409)
        options.append({"option_id": candidate.candidate_id, "changes": deepcopy(candidate.changes),
                        "travel_changes": deepcopy(candidate.travel_changes),
                        "proposed_days": deepcopy(candidate.proposed_days), "reason": candidate.reason,
                        "tradeoff": candidate.tradeoff, "estimated_end_time": candidate.estimated_end_time})
    return {"proposal_id": str(uuid4()), "itinerary_id": result.itinerary_id, "type": result.type,
            "base_version": result.base_version, "options": options, "no_option_reason": result.no_option_reason}


def prepare_proposal(result: AdaptResult, itinerary, catalog):
    """Return (public response, stored proposal) with the same proposal and option IDs."""
    public = to_api_v1(result, itinerary, catalog)
    stored = deepcopy(public)
    for option, candidate in zip(stored["options"], result.candidates, strict=True):
        option["_validation"] = {
            "request": deepcopy(candidate.request),
            "dropped_ids": list(candidate.dropped_ids),
            "replacement_place_id": candidate.replacement_place_id,
            "dataset_version": candidate.dataset_version,
            "base_fingerprint": candidate.base_fingerprint,
            "facts": dict(candidate.facts),
        }
    return public, stored


def validate_stored_option(itinerary, option, catalog):
    """Recheck a server-stored option against the latest CURRENT and catalog."""
    try:
        metadata = option["_validation"]
        candidate = Candidate(
            candidate_id=option["option_id"],
            request=metadata["request"],
            dropped_ids=metadata["dropped_ids"],
            replacement_place_id=metadata["replacement_place_id"],
            proposed_days=option["proposed_days"],
            changes=option["changes"],
            travel_changes=option["travel_changes"],
            estimated_end_time=option["estimated_end_time"],
            dataset_version=metadata["dataset_version"],
            base_fingerprint=metadata["base_fingerprint"],
            facts=metadata["facts"],
        )
    except (KeyError, TypeError):
        return False
    return validate_candidate(itinerary, candidate, catalog)
