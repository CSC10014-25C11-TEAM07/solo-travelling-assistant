"""Collect a small, directed batch of motorcycle estimates from the public demo.

Writes to a separate output directory; never changes the shipped dataset in place.
For application traffic or larger collections, use a hosted/self-hosted provider.
"""

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time

import httpx

DATA = Path(__file__).resolve().parents[1] / "data"
ENDPOINT = "https://valhalla1.openstreetmap.de/route"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coordinates", type=Path, default=DATA / "place_coordinates.json")
    parser.add_argument("--pairs", type=Path, default=DATA / "travel_times.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    pairs = json.loads(args.pairs.read_text(encoding="utf-8"))
    coordinates = {p["place_id"]: p for p in json.loads(args.coordinates.read_text(encoding="utf-8"))}
    if not 1 <= len(pairs) <= 20:
        parser.error("Use 1–20 directed legs for this small public-demo collection")
    targets = [args.output_dir / name for name in ("travel_times.json", "travel_time_evidence.json")]
    if any(path.exists() for path in targets):
        parser.error("Output files already exist; choose a new directory")
    seen = set()
    for pair in pairs:
        key = (pair["from_place_id"], pair["to_place_id"])
        if key in seen or key[0] == key[1] or any(p not in coordinates for p in key):
            parser.error(f"Duplicate, same-place or missing-coordinate leg: {key}")
        seen.add(key)
    legs, evidence = [], []
    headers = {"User-Agent": "SoloTravellingAssistant-StudentDataset/0.1",
               "X-Client-Id": "solo-travelling-assistant-student-dataset"}
    with httpx.Client(timeout=25, headers=headers) as client:
        for index, pair in enumerate(pairs):
            if index:
                time.sleep(1.2)
            origin, destination = pair["from_place_id"], pair["to_place_id"]
            request = {
                "locations": [{"lat": coordinates[p]["latitude"],
                               "lon": coordinates[p]["longitude"]} for p in (origin, destination)],
                "costing": "motorcycle",
                "costing_options": {"motorcycle": {"use_highways": 0, "use_tolls": 0}},
                "units": "kilometers",
            }
            response = client.get(ENDPOINT, params={"json": json.dumps(request, separators=(",", ":"))})
            response.raise_for_status()
            trip = response.json()["trip"]
            if trip["status"] != 0 or not math.isfinite(trip["summary"]["time"]) or trip["summary"]["time"] <= 0:
                raise ValueError(f"No valid route for {origin} → {destination}")
            checked = datetime.now(timezone.utc).isoformat()
            legs.append({"travel_time_id": None, "from_place_id": origin,
                         "to_place_id": destination,
                         "duration_minutes": math.ceil(trip["summary"]["time"] / 60),
                         "source_url": str(response.request.url), "checked_at": checked,
                         "data_status": "SOURCED"})
            evidence.append({"from_place_id": origin, "to_place_id": destination,
                             "summary": trip["summary"], "costing": "motorcycle",
                             "provider": "Valhalla FOSSGIS demo / OpenStreetMap",
                             "checked_at": checked,
                             "duration_basis": "ceil(summary.time / 60); model estimate, not real-time or measured travel",
                             "docs_url": "https://valhalla.github.io/valhalla/api/route/api-reference/"})
            print(f"{origin} → {destination}: {legs[-1]['duration_minutes']} estimated minutes")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path, content in zip(targets, (legs, evidence)):
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(legs)} estimates to {args.output_dir}; review before copying into backend/data.")


if __name__ == "__main__":
    main()
