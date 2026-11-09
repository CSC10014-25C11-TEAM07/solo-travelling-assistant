"""Fail-closed bridge proposal for Bảo 06; not automatically wired into main.py."""

from copy import deepcopy
from uuid import uuid4

from .engine import validate_candidate
from .models import AdaptError, AdaptResult


def to_api_v1(result: AdaptResult, itinerary, catalog):
    """Export only previews expressible by the existing V1 change contract.

    Never silently omit travel_changes. Bảo 06 must own saving the returned
    proposal inside the authenticated service, then revalidate at F06.
    """
    if result.base_version != itinerary["version"] or result.itinerary_id != itinerary["itinerary_id"]:
        raise AdaptError("STALE_ITINERARY", "Lịch đã thay đổi trước bước lưu đề xuất.", status=409)
    if result.dataset_version != catalog.version:
        raise AdaptError("DATA_INCOMPLETE", "Dataset đã thay đổi; cần tạo lại phương án.")
    options = []
    for candidate in result.candidates:
        if not validate_candidate(itinerary, candidate, catalog):
            raise AdaptError("PROPOSAL_NO_LONGER_VALID", "Phương án không còn hợp lệ.", status=409)
        if candidate.travel_changes:
            raise AdaptError("INTEGRATION_NOT_READY", "Cần Bảo 06/Leader chốt biểu diễn và lưu thay đổi TRAVEL trước khi xuất API V1.", status=503)
        options.append({"option_id": candidate.candidate_id, "changes": deepcopy(candidate.changes),
                        "proposed_days": deepcopy(candidate.proposed_days), "reason": candidate.reason,
                        "tradeoff": candidate.tradeoff, "estimated_end_time": candidate.estimated_end_time})
    return {"proposal_id": str(uuid4()), "itinerary_id": result.itinerary_id, "type": result.type,
            "base_version": result.base_version, "options": options, "no_option_reason": result.no_option_reason}
