"""Read-only catalogue shared by F01 and future PLAN/ADAPT integration."""

import json
from pathlib import Path

from place_models import INTEREST_LABELS, Place, TravelTime

DATA_DIR = Path(__file__).with_name("data")


class MissingTravelTime(LookupError):
    pass


class PlaceCatalog:
    def __init__(self, places: list[Place], travel_times: list[TravelTime]):
        self.places = {place.place_id: place for place in places}
        if len(self.places) != len(places):
            raise ValueError("Duplicate place_id")
        self.travel_times = {}
        for leg in travel_times:
            if leg.from_place_id not in self.places or leg.to_place_id not in self.places:
                raise ValueError("Travel time refers to an unknown place_id")
            key = (leg.from_place_id, leg.to_place_id)
            if key in self.travel_times:
                raise ValueError(f"Duplicate directed travel time: {key}")
            self.travel_times[key] = leg

    @classmethod
    def load(cls, directory: Path = DATA_DIR):
        places = json.loads((directory / "places.json").read_text(encoding="utf-8"))
        legs = json.loads((directory / "travel_times.json").read_text(encoding="utf-8"))
        return cls(
            [Place.model_validate(item) for item in places],
            [TravelTime.model_validate(item) for item in legs],
        )

    def recommend(self, interests: list[str], *, include_mock: bool = False):
        selected = set(interests)
        if not selected or not selected <= INTEREST_LABELS.keys():
            raise ValueError("Missing or invalid interests")
        candidates = [
            place for place in self.places.values()
            if selected.intersection(place.interests)
            and (include_mock or place.data_status != "MOCK")
        ]
        candidates.sort(key=lambda place: (
            -len(selected.intersection(place.interests)), place.place_id,
        ))
        result = []
        for place in candidates[:3]:
            matching = [INTEREST_LABELS[key] for key in INTEREST_LABELS
                        if key in selected and key in place.interests]
            result.append({
                "place_id": place.place_id,
                "name": place.name,
                "image_url": place.image_url,
                "reason": f"Phù hợp với sở thích {' và '.join(matching)} của bạn.",
            })
        return {"places": result}

    def get_travel_time(self, from_id: str, to_id: str, *, allow_mock: bool = False) -> int:
        if from_id not in self.places or to_id not in self.places:
            raise MissingTravelTime(f"Unknown place: {from_id} → {to_id}")
        if from_id == to_id:
            return 0
        leg = self.travel_times.get((from_id, to_id))
        if (leg is None or leg.data_status == "UNVERIFIED"
                or (leg.data_status == "MOCK" and not allow_mock)):
            raise MissingTravelTime(f"Chưa đủ dữ liệu chặng {from_id} → {to_id}")
        return leg.duration_minutes
