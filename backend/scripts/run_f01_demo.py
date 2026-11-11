"""Run real registration/login + F01 locally while PR #12 is pending."""

import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auth_integration import auth_snapshot, create_integration_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--auth-ref", default="origin/feat/2-auth-api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--database", type=Path,
                        help="Optional dedicated demo SQLite file; default is temporary")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    try:
        with auth_snapshot(args.auth_ref) as (auth, commit):
            with tempfile.TemporaryDirectory(prefix="f01-demo-") as temporary:
                database = args.database or Path(temporary) / "demo.sqlite3"
                app = create_integration_app(auth, database)
                print(f"Auth snapshot: {args.auth_ref} @ {commit}", flush=True)
                print("Real session validation is enabled; no fixed demo token is accepted.", flush=True)
                print("Accounts are temporary and reset on shutdown." if args.database is None
                      else f"Dedicated demo database: {database.resolve()}", flush=True)
                print(f"Swagger: http://127.0.0.1:{args.port}/docs", flush=True)
                uvicorn.run(app, host=args.host, port=args.port)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        parser.exit(2, f"Cannot read the auth snapshot. Run git fetch origin and check --auth-ref.\n{error}\n")
    except ModuleNotFoundError as error:
        parser.exit(2, f"Missing dependency: {error.name}. Install backend/requirements-integration.txt.\n")


if __name__ == "__main__":
    main()
