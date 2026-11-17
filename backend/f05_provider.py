"""Integration helpers for Bảo 06's catalog_provider and option_validator."""

from adapt_f05.engine import AdaptEngine
from adapt_f05.catalog import Catalog, RouteDay, checked_buffer
from adapt_f05.handoff import prepare_proposal, validate_stored_option
from adapt_f05.models import AdaptError
from adapt_f05.ranking import GeminiRanker, RankingError
from itinerary_api import APIError


def make_catalog_provider(data_directory, routes_by_days, *, mode):
    """Load fresh data and bind configured route days to stored itinerary IDs."""
    if mode not in ("MOCK", "VERIFIED"):
        raise ValueError("mode must be MOCK or VERIFIED")

    def load(itinerary):
        days = itinerary["days"]
        route = routes_by_days.get(len(days))
        if not route or route.get("data_status") != mode or len(route.get("days", [])) != len(days):
            raise AdaptError("DATA_INCOMPLETE", f"Thiếu tuyến {len(days)} ngày được cấu hình {mode}.")
        mappings = []
        buffer = checked_buffer(route.get("buffer_minutes", 0))
        for number, (day, configured) in enumerate(zip(days, route["days"], strict=True), 1):
            if day["day_number"] != number or day["end_deadline"] != configured["end_deadline"]:
                raise AdaptError("DATA_INCOMPLETE", f"Hạn hoặc số thứ tự ngày {number} không khớp tuyến.")
            mappings.append(RouteDay(day_id=day["day_id"], start_place_id=configured["start_place_id"],
                                     end_place_id=configured["end_place_id"], start_time=configured["start_time"],
                                     end_deadline=configured["end_deadline"]))
        try:
            return Catalog.load(data_directory, mappings, mode=mode,
                                buffer_minutes_by_day={day.day_id: buffer for day in mappings})
        except AdaptError:
            raise
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise AdaptError("DATA_INCOMPLETE", f"Không nạp được catalog {mode}: {type(error).__name__}.") from None

    return load


def create_proposal(itinerary, payload, catalog_provider, ranker_factory=GeminiRanker):
    """Return public and server-only records. The caller must save before replying."""
    try:
        catalog = catalog_provider(itinerary)
        # Construct the ranker lazily: a zero-option result needs no model call.
        class LazyRanker:
            mode = "GEMINI"

            def rank(self, context):
                self.delegate = ranker_factory()
                result = self.delegate.rank(context)
                self.audit = getattr(self.delegate, "audit", {})
                return result

        engine = AdaptEngine(catalog, ranker=LazyRanker(), allow_ai_fallback=False)
        result = engine.generate(itinerary, payload)
        return prepare_proposal(result, itinerary, catalog)
    except AdaptError as error:
        raise APIError(error.status, error.code, error.message) from error
    except RankingError as error:
        raise APIError(error.status, error.code, str(error)) from error


def make_option_validator(catalog_provider):
    """Bind the fresh catalog loader to the callback expected by F06."""
    def validate(itinerary, option):
        try:
            return validate_stored_option(itinerary, option, catalog_provider(itinerary))
        except (AdaptError, KeyError, ValueError):
            return False

    return validate
