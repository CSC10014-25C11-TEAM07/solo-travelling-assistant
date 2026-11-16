"""Prepare source JSON and its blockers in a new folder; never touches SQLite."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from place_catalog import DATA_DIR
from source_bundle import export_source_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = export_source_bundle(args.data_dir, args.output_dir)
    except (ValueError, KeyError, OSError, TypeError) as error:
        parser.exit(1, f"EXPORT_FAILED: {error}\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
