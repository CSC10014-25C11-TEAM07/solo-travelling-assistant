"""Validate the handoff dataset without SQLite or external API credentials."""

import argparse
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from place_catalog import DATA_DIR, PlaceCatalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    try:
        catalog = PlaceCatalog.load(args.data_dir)
    except (ValueError, OSError) as error:
        parser.exit(1, f"INVALID: {error}\n")
    print(f"VALID: {len(catalog.places)} places; {len(catalog.travel_times)} directed legs")
    print("Place status:", dict(Counter(p.data_status for p in catalog.places.values())))
    print("Travel status:", dict(Counter(t.data_status for t in catalog.travel_times.values())))
    print("Schema valid does not mean real-world information has been verified.")


if __name__ == "__main__":
    main()
