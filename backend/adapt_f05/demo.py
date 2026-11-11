"""Explicit MOCK demo. Run: python -m adapt_f05.demo --case rest --ranker mock."""

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

from .catalog import Catalog, RouteDay
from .engine import AdaptEngine
from .models import AdaptError
from .ranking import GeminiRanker, MockRanker, RankingError, RuleRanker

BACKEND = Path(__file__).resolve().parents[1]


def demo_inputs():
    source = json.loads((BACKEND / "data/fixtures/current_v1_day2.json").read_text(encoding="utf-8"))
    # Bảo 04's fixture is explicitly only day 2. Add clearly MOCK padding days
    # to exercise the full snapshot shape; these are NOT an HCMC-Dalat route.
    itinerary = {"itinerary_id": source["itinerary_id"], "user_id": "MOCK-USER", "status": "CURRENT", "version": 1,
                 "departure_date": "2026-11-12", "return_date": "2026-11-14", "departure_time": "06:00",
                 "interests": ["nature", "coffee"], "min_rest_minutes": 60,
                 "created_at": "2026-11-01T00:00:00Z", "confirmed_at": "2026-11-01T00:01:00Z", "days": []}
    for number in (1, 2, 3):
        did = f"MOCK-DAY-{number}"
        day = {"day_id": did, "itinerary_id": itinerary["itinerary_id"], "day_number": number,
               "date": f"2026-11-{11 + number}", "end_deadline": "16:30", "activities": []}
        if number == 2:
            day["activities"] = deepcopy(source["activities"])
        else:
            day["activities"] = [{"activity_id": f"MOCK-PADDING-REST-{number}", "day_id": did, "type": "REST",
                                  "name": "MOCK - ngày đệm kiểm tra bảo toàn, không phải tuyến thật",
                                  "place_id": "MOCK-REST", "start_time": "12:00", "end_time": "13:00",
                                  "status": "PENDING", "is_optional": False, "replaces_activity_id": None, "completed_at": None}]
        itinerary["days"].append(day)
    route = RouteDay("MOCK-DAY-2", "MOCK-GA", "MOCK-END", "08:00", "16:30")
    catalog = Catalog.load(BACKEND / "data/fixtures/mock", [route], mode="MOCK")
    return itinerary, catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("rest", "rain", "no-option"), default="rest")
    parser.add_argument("--ranker", choices=("rules", "mock", "gemini"), default="rules")
    args = parser.parse_args()
    itinerary, catalog = demo_inputs()
    payload = ({"type": "REPLACE_LOCATION", "base_version": 1, "activity_id": "A03", "reason": "RAIN"}
               if args.case == "rain" else {"type": "EXTEND_REST", "base_version": 1, "rest_activity_id": "REST",
                                           "rest_until": "16:30" if args.case == "no-option" else "15:00",
                                           "preferred_keep_activity_id": "A04"})
    ranker = {"rules": RuleRanker, "mock": MockRanker, "gemini": GeminiRanker}[args.ranker]()
    result = AdaptEngine(catalog, ranker=ranker).generate(itinerary, payload)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (AdaptError, RankingError) as error:
        print(json.dumps({"code": error.code, "message": str(error)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
