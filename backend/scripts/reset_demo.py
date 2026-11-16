"""Restore CURRENT v1 in a dedicated test SQLite file with one command."""

import argparse
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from demo_reset import DEFAULT_DATABASE, SCENARIOS, reset_demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE,
                        help="Dedicated *.test.sqlite3 file; existing unmarked files are refused")
    parser.add_argument("--days", type=int, choices=(3, 4), default=4)
    parser.add_argument("--scenario", choices=SCENARIOS, default="T06")
    parser.add_argument("--user-id", help="Existing account in this test database; default creates a MOCK account")
    args = parser.parse_args()
    try:
        result = reset_demo(args.database, days=args.days, scenario=args.scenario, user_id=args.user_id)
    except (ValueError, KeyError, StopIteration, OSError, sqlite3.Error) as error:
        print(json.dumps({"reset": "FAIL", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
