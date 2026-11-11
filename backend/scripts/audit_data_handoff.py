"""Validate handoff fixtures and report unresolved source-route data offline."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_handoff import audit
from place_catalog import DATA_DIR


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = audit(args.data_dir)
    except (ValueError, KeyError, TypeError, OSError) as error:
        report = {"checks_passed": False, "errors": [str(error)]}
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["checks_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
