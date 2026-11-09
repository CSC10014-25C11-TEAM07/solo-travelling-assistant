"""Offline preview only: runs the F01 ranking without an HTTP/authentication server."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from place_catalog import DATA_DIR, PlaceCatalog
from place_models import INTEREST_LABELS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("interests", nargs="+", choices=INTEREST_LABELS)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--include-mock", action="store_true")
    args = parser.parse_args()
    catalog = PlaceCatalog.load(args.data_dir)
    print(json.dumps(catalog.recommend(args.interests, include_mock=args.include_mock),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
