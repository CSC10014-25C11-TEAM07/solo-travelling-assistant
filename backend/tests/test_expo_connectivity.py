import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import create_app


class ExpoConnectivityTests(unittest.TestCase):
    def test_web_preflights_and_auth_error_are_readable(self):
        with patch.dict(os.environ):
            os.environ.pop("EXPO_WEB_ORIGINS", None)
            client = TestClient(create_app())
        for origin in ("http://localhost:8081", "http://127.0.0.1:8081"):
            for method, path in (
                ("POST", "/api/v1/auth/register"),
                ("POST", "/api/v1/auth/login"),
                ("GET", "/api/v1/itineraries/current"),
                ("PATCH", "/api/v1/itineraries/test/activities/test"),
            ):
                with self.subTest(origin=origin, method=method, path=path):
                    response = client.options(path, headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": method,
                        "Access-Control-Request-Headers": "content-type, authorization",
                    })
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.headers["access-control-allow-origin"], origin)
            response = client.get("/api/v1/auth/me", headers={"Origin": origin})
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.headers["access-control-allow-origin"], origin)

    def test_custom_web_origin_and_native_access(self):
        origin = "http://192.168.1.20:8082"
        with patch.dict(os.environ, EXPO_WEB_ORIGINS=f"http://localhost:8082, {origin}"):
            client = TestClient(create_app())
        self.assertEqual(client.get("/health", headers={"Origin": origin})
                         .headers["access-control-allow-origin"], origin)
        for other in ("https://other.example", "http://192.168.1.20:8081"):
            preflight = client.options("/api/v1/auth/login", headers={
                "Origin": other, "Access-Control-Request-Method": "POST",
            })
            self.assertEqual(preflight.status_code, 400)
            self.assertNotIn("access-control-allow-origin", preflight.headers)
        self.assertEqual(client.get("/health").json(), {"status": "ok"})
