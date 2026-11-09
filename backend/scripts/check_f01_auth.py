"""Integration smoke check with Đăng's real auth module and a temporary SQLite DB.

Use --auth-ref to test a reviewed Git snapshot of PR #12 before it is merged.
This script never adds a token bypass to the application or writes to app.sqlite3.
"""

import argparse
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile

from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from auth_integration import auth_snapshot, create_integration_app


@contextmanager
def local_auth(path):
    spec = importlib.util.spec_from_file_location("auth", path)
    auth = importlib.util.module_from_spec(spec)
    previous = sys.modules.get("auth")
    sys.modules["auth"] = auth
    try:
        spec.loader.exec_module(auth)
        yield auth, str(path)
    finally:
        if previous is None:
            sys.modules.pop("auth", None)
        else:
            sys.modules["auth"] = previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--auth-file", type=Path)
    source.add_argument("--auth-ref", help="Trusted project Git ref, e.g. origin/feat/2-auth-api")
    args = parser.parse_args()
    path = args.auth_file or BACKEND / "auth.py"
    if args.auth_ref is None and not path.is_file():
        parser.exit(2, "Auth module is not merged yet. See docs/F01-HUONG-DAN-BAO04.md.\n")
    snapshot = auth_snapshot(args.auth_ref) if args.auth_ref else local_auth(path)
    with snapshot as (auth, revision):
        with tempfile.TemporaryDirectory(prefix="f01-auth-check-") as directory:
            app = create_integration_app(auth, Path(directory) / "test.sqlite3")
            url = "/api/v1/places/recommendations?interests=coffee"
            credentials = {"username": "f01_integration_test", "password": "MOCK-password-for-test-only"}
            with TestClient(app) as client:
                assert client.get(url).status_code == 401
                assert client.post("/api/v1/auth/register", json=credentials).status_code == 201
                login = client.post("/api/v1/auth/login", json=credentials)
                assert login.status_code == 200
                headers = {"Authorization": "Bearer " + login.json()["access_token"]}
                response = client.get(url, headers=headers)
                assert response.status_code == 200
                assert 0 < len(response.json()["places"]) <= 3
                invalid = client.get(url, headers={"Authorization": "Bearer invalid-token"})
                assert invalid.status_code == 401 and invalid.json()["code"] == "INVALID_SESSION"
                bad_input = client.get("/api/v1/places/recommendations?interests=invalid", headers=headers)
                assert bad_input.status_code == 422 and bad_input.json()["field"] == "interests"
                assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
                assert client.get(url, headers=headers).status_code == 401
                login = client.post("/api/v1/auth/login", json=credentials)
                headers = {"Authorization": "Bearer " + login.json()["access_token"]}
                with sqlite3.connect(auth.DB_PATH) as db:
                    db.execute("UPDATE sessions SET expires_at = '2000-01-01T00:00:00+00:00'")
                expired = client.get(url, headers=headers)
                assert expired.status_code == 401 and expired.json()["code"] == "SESSION_EXPIRED"
            print("PASS: register → login → F01; invalid/expired/revoked sessions rejected; interests validated.")
            print(f"Auth source: {revision}")
            print("Used real auth code with a temporary SQLite database; no production account or token created.")


if __name__ == "__main__":
    main()
