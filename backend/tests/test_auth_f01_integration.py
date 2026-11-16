"""Regression for the auth/F01 merge: exercise the real main app and lifespan."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import auth
from main import app


class AuthF01IntegrationTests(unittest.TestCase):
    def test_main_register_login_f01_logout_rejects_old_token(self):
        credentials = {
            "username": "f01_merge_regression",
            "password": "temporary-integration-password-only",
        }
        url = "/api/v1/places/recommendations?interests=coffee"
        with tempfile.TemporaryDirectory(prefix="f01-main-check-") as directory:
            # Startup must initialize both auth tables in this isolated database.
            with patch.object(auth, "DB_PATH", Path(directory) / "test.sqlite3"):
                with TestClient(app) as client:
                    self.assertEqual(client.get("/health").json(), {"status": "ok"})
                    self.assertEqual(client.get(url).status_code, 401)
                    registered = client.post("/api/v1/auth/register", json=credentials)
                    self.assertEqual(registered.status_code, 201)
                    login = client.post("/api/v1/auth/login", json=credentials)
                    self.assertEqual(login.status_code, 200)
                    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
                    response = client.get(url, headers=headers)
                    self.assertEqual(response.status_code, 200)
                    self.assertGreater(len(response.json()["places"]), 0)
                    self.assertLessEqual(len(response.json()["places"]), 3)
                    for interests, expected in (
                        (["coffee"], ["P006", "P010", "P011"]),
                        (["nature"], ["P002", "P003", "P004"]),
                        (["nature", "culture"], ["P002", "P001", "P003"]),
                        (["food"], ["P007"]),
                    ):
                        changed = client.get(
                            "/api/v1/places/recommendations",
                            params=[("interests", interest) for interest in interests], headers=headers,
                        )
                        self.assertEqual(changed.status_code, 200)
                        actual = [place["place_id"] for place in changed.json()["places"]]
                        self.assertEqual(actual, expected)
                        self.assertFalse(set(actual) & {"H001", "R001", "R002", "R003"})
                    cleared = client.get("/api/v1/places/recommendations", headers=headers)
                    self.assertEqual(cleared.status_code, 422)
                    self.assertEqual(cleared.json()["field"], "interests")
                    invalid = client.get(
                        "/api/v1/places/recommendations?interests=invalid", headers=headers,
                    )
                    self.assertEqual(invalid.status_code, 422)
                    self.assertEqual(invalid.json()["code"], "VALIDATION_ERROR")
                    self.assertEqual(invalid.json()["field"], "interests")
                    self.assertEqual(
                        client.post("/api/v1/auth/logout", headers=headers).status_code, 200,
                    )
                    revoked = client.get(url, headers=headers)
                    self.assertEqual(revoked.status_code, 401)
                    self.assertEqual(revoked.json()["code"], "INVALID_SESSION")


if __name__ == "__main__":
    unittest.main()
