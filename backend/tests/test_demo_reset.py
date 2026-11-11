"""MOCK reset persistence, account isolation, rollback, and real F03/F06 routes.

F05 is called as a domain module with RuleRanker. No Gemini, network, Android,
production database, or overridden authentication is used.
"""

from contextlib import closing
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

import auth
import itinerary_store as store
from adapt_f05 import AdaptEngine, Catalog
from adapt_f05.catalog import RouteDay
from adapt_f05.handoff import prepare_proposal, validate_stored_option
from adapt_f05.ranking import RuleRanker
from adapt_store import save_proposal
from demo_reset import (
    DATA_DIR, DEMO_PASSWORD, DEMO_USERNAME, DEMO_USER_ID, ResetError,
    load_bundle, read_current, reset_demo,
)
from main import create_app

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "backend/scripts/reset_demo.py"


class ResetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tan-reset-")
        self.addCleanup(self.temporary.cleanup)
        self.database = Path(self.temporary.name) / "demo.test.sqlite3"

    def connection(self):
        db = sqlite3.connect(self.database)
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def run_cli(self, days=4, scenario="T06"):
        result = subprocess.run(
            [sys.executable, "-X", "utf8", str(SCRIPT), "--database", str(self.database),
             "--days", str(days), "--scenario", scenario],
            cwd=self.temporary.name, capture_output=True, text=True, encoding="utf-8",
            timeout=20, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(DEMO_PASSWORD, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_one_command_twice_restores_exact_three_and_four_day_snapshots(self):
        for days in (3, 4):
            with self.subTest(days=days):
                first = self.run_cli(days)
                before = read_current(self.database, DEMO_USER_ID)
                second = self.run_cli(days)
                self.assertEqual(first, second)
                self.assertEqual(read_current(self.database, DEMO_USER_ID), before)
                self.assertEqual((before["status"], before["version"], len(before["days"])),
                                 ("CURRENT", 1, days))
                expected = deepcopy(load_bundle(days).snapshot)
                expected["user_id"] = DEMO_USER_ID
                self.assertEqual(before, expected)
                with closing(self.connection()) as db:
                    self.assertEqual(db.execute("SELECT count(*) FROM itineraries").fetchone()[0], 1)
                    self.assertEqual(db.execute("SELECT count(*) FROM activities").fetchone()[0],
                                     sum(len(d["activities"]) for d in expected["days"]))
                    self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_t15_selects_separate_catalog_without_deleting_referenced_places(self):
        report = self.run_cli(scenario="T15")
        self.assertEqual(report["catalog"], "fixtures/mock-no-replacement")
        current = read_current(self.database, DEMO_USER_ID)
        day_three = current["days"][2]
        self.assertTrue(any(a["place_id"] == "MOCK-INDOOR" for a in day_three["activities"]))
        catalog = json.loads((DATA_DIR / report["catalog"] / "places.json").read_text())
        self.assertEqual(next(p for p in catalog if p["place_id"] == "MOCK-INDOOR")["environment"], "MIXED")

    def test_unmarked_existing_database_is_refused_without_changes(self):
        with closing(self.connection()) as db, db:
            db.execute("CREATE TABLE untouched (value TEXT)")
            db.execute("INSERT INTO untouched VALUES ('keep')")
        before = self.database.read_bytes()
        with self.assertRaises(ResetError):
            reset_demo(self.database)
        self.assertEqual(self.database.read_bytes(), before)

    def test_app_name_symlink_and_hardlink_are_refused(self):
        protected = Path(self.temporary.name) / "app.sqlite3"
        protected.write_bytes(b"do not touch")
        with self.assertRaises(ResetError):
            reset_demo(protected)
        self.assertEqual(protected.read_bytes(), b"do not touch")
        reset_demo(self.database)
        alias = Path(self.temporary.name) / "alias.test.sqlite3"
        alias.symlink_to(self.database)
        with self.assertRaises(ResetError):
            reset_demo(alias)
        alias.unlink()
        os.link(self.database, alias)
        with self.assertRaises(ResetError):
            reset_demo(alias)

    def test_invalid_fixture_is_refused_before_database_creation(self):
        with patch("demo_reset.load_bundle", side_effect=ResetError("fixture invalid")):
            with self.assertRaises(ResetError):
                reset_demo(self.database)
        self.assertFalse(self.database.exists())

    def test_unknown_owner_does_not_erase_existing_demo(self):
        reset_demo(self.database)
        before = read_current(self.database, DEMO_USER_ID)
        with self.assertRaises(ResetError):
            reset_demo(self.database, user_id="missing-user")
        self.assertEqual(read_current(self.database, DEMO_USER_ID), before)

    def test_failed_insert_rolls_back_schedule_and_proposal_cleanup(self):
        reset_demo(self.database)
        with closing(self.connection()) as db, db:
            db.execute("UPDATE itineraries SET version = 2")
            db.execute("UPDATE activities SET end_time = '15:00' WHERE activity_id = 'MOCK4D-REST'")
            db.execute("""
                INSERT INTO adapt_proposals (proposal_id, itinerary_id, user_id, base_version, payload)
                VALUES ('keep-on-failure', 'MOCK4D-CURRENT', ?, 2, '{}')
            """, (DEMO_USER_ID,))
            db.execute("""
                CREATE TRIGGER fail_reset BEFORE INSERT ON activities
                WHEN NEW.activity_id = 'MOCK4D-A03'
                BEGIN SELECT RAISE(ABORT, 'simulated storage failure'); END
            """)
        before = read_current(self.database, DEMO_USER_ID)
        with self.assertRaises(sqlite3.IntegrityError):
            reset_demo(self.database)
        self.assertEqual(read_current(self.database, DEMO_USER_ID), before)
        with closing(self.connection()) as db, db:
            self.assertEqual(db.execute("SELECT count(*) FROM adapt_proposals").fetchone()[0], 1)
            db.execute("DROP TRIGGER fail_reset")
        reset_demo(self.database)
        self.assertEqual(read_current(self.database, DEMO_USER_ID)["version"], 1)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tan-reset-api-")
        self.addCleanup(self.temporary.cleanup)
        self.database = Path(self.temporary.name) / "api.test.sqlite3"
        self.binding = patch.object(auth, "DB_PATH", self.database)
        self.binding.start()
        self.addCleanup(self.binding.stop)

    def catalog(self, bundle):
        routes = [RouteDay(**{k: d[k] for k in (
            "day_id", "start_place_id", "end_place_id", "start_time", "end_deadline"
        )}) for d in bundle.route["days"]]
        return Catalog.load(DATA_DIR / bundle.catalog_path, routes, mode="MOCK")

    def login(self, client, username=DEMO_USERNAME, password=DEMO_PASSWORD):
        response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    def current(self, client, headers):
        response = client.get("/api/v1/itineraries/current", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["itinerary"]

    def proposal(self, bundle, catalog, itinerary):
        cases = json.loads((DATA_DIR / "fixtures/scenarios.json").read_text())
        payload = deepcopy(next(c for c in cases if c["test_id"] == bundle.scenario)["trigger"])
        payload["base_version"] = itinerary["version"]
        targets = bundle.route["target_ids"]
        if payload["type"] == "EXTEND_REST":
            payload.update(rest_activity_id=targets["rest_activity_id"],
                           preferred_keep_activity_id=targets["preferred_keep_activity_id"])
        else:
            payload["activity_id"] = targets["rain_activity_id"]
        result = AdaptEngine(catalog, ranker=RuleRanker()).generate(itinerary, payload)
        public, stored = prepare_proposal(result, itinerary, catalog)
        save_proposal(stored, itinerary["user_id"])
        return public

    def test_reset_after_real_accept_removes_history_decisions_and_preserves_session(self):
        for days in (3, 4):
            for scenario in ("T06", "T13"):
                with self.subTest(days=days, scenario=scenario):
                    initial_report = reset_demo(self.database, days=days, scenario=scenario)
                    bundle = load_bundle(days, scenario)
                    catalog = self.catalog(bundle)
                    app = create_app(option_validator=lambda trip, option: validate_stored_option(trip, option, catalog))
                    with TestClient(app) as client:
                        headers = self.login(client)
                        baseline = self.current(client, headers)
                        proposal = self.proposal(bundle, catalog, baseline)
                        self.assertEqual(self.current(client, headers), baseline)
                        option = proposal["options"][0]
                        body = {"decision": "ACCEPT", "option_id": option["option_id"]}
                        url = f'/api/v1/adapt-proposals/{proposal["proposal_id"]}/decision'
                        accepted = client.post(url, headers=headers, json=body)
                        self.assertEqual(accepted.status_code, 200, accepted.text)
                        changed = accepted.json()["itinerary"]
                        self.assertEqual(changed["version"], 2)
                        rows = {a["activity_id"]: a for d in changed["days"] for a in d["activities"]}
                        old_rows = {a["activity_id"]: a for d in baseline["days"] for a in d["activities"]}
                        self.assertTrue(any(a["type"] == "TRAVEL" and a["status"] == "REPLACED" for a in rows.values()))
                        self.assertGreater(len(rows), len(old_rows))
                        for aid, row in old_rows.items():
                            if row["status"] == "DONE":
                                self.assertEqual(rows[aid], row)
                        self.assertEqual(client.post(url, headers=headers, json=body).json(), accepted.json())
                        reset_report = reset_demo(self.database, days=days, scenario=scenario)
                        self.assertEqual(reset_report["state_fingerprint"], initial_report["state_fingerprint"])
                        self.assertEqual(self.current(client, headers), baseline)
                        self.assertEqual(client.post(url, headers=headers, json=body).status_code, 404)
                        with store.connect() as db:
                            self.assertEqual(db.execute("SELECT count(*) FROM adapt_proposals WHERE user_id = ?", (DEMO_USER_ID,)).fetchone()[0], 0)
                            self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
                    # New app/lifespan + existing session must read the same saved baseline.
                    with TestClient(create_app()) as restarted:
                        self.assertEqual(self.current(restarted, headers), baseline)

    def test_reject_and_empty_options_preserve_v1_and_are_cleaned_by_reset(self):
        for scenario, expected_options in (("T06", 2), ("T08", 0), ("T13", 1), ("T15", 0)):
            with self.subTest(scenario=scenario):
                reset_demo(self.database, scenario=scenario)
                bundle = load_bundle(scenario=scenario)
                with TestClient(create_app()) as client:
                    headers = self.login(client)
                    baseline = self.current(client, headers)
                    proposal = self.proposal(bundle, self.catalog(bundle), baseline)
                    self.assertEqual(len(proposal["options"]), expected_options)
                    if not expected_options:
                        self.assertTrue(proposal["no_option_reason"])
                    url = f'/api/v1/adapt-proposals/{proposal["proposal_id"]}/decision'
                    response = client.post(url, headers=headers, json={"decision": "REJECT"})
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(response.json()["itinerary"], baseline)
                    self.assertEqual(client.post(url, headers=headers, json={"decision": "REJECT"}).json(), response.json())
                    reset_demo(self.database, scenario=scenario)
                    self.assertEqual(self.current(client, headers), baseline)
                    self.assertEqual(client.post(url, headers=headers, json={"decision": "REJECT"}).status_code, 404)

    def test_reset_after_f03_and_newer_trip_preserves_other_owner_and_token(self):
        reset_demo(self.database)
        bundle = load_bundle()
        with TestClient(create_app(plan_provider=lambda _: deepcopy(bundle.snapshot["days"]))) as client:
            headers = self.login(client)
            baseline = self.current(client, headers)
            target = bundle.route["target_ids"]["rain_activity_id"]
            response = client.patch(f'/api/v1/itineraries/{baseline["itinerary_id"]}/activities/{target}',
                                    headers=headers, json={"status": "DONE", "base_version": 1})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["itinerary"]["version"], 2)
            registration = client.post("/api/v1/auth/register", json={
                "username": "other_test_owner", "password": "another-mock-only-password",
            })
            self.assertEqual(registration.status_code, 201)
            other_id = registration.json()["user_id"]
            other_headers = self.login(client, "other_test_owner", "another-mock-only-password")
            payload = {key: baseline[key] for key in (
                "departure_date", "return_date", "departure_time", "interests", "min_rest_minutes"
            )}
            # Both owners get a later confirmed trip; reset must only remove ours.
            for current_headers in (headers, other_headers):
                draft = client.post("/api/v1/itinerary-drafts", headers=current_headers, json=payload)
                self.assertEqual(draft.status_code, 201, draft.text)
                confirm = client.post(f'/api/v1/itinerary-drafts/{draft.json()["draft_id"]}/confirm',
                                      headers=current_headers, json={})
                self.assertEqual(confirm.status_code, 200, confirm.text)
            other_baseline = self.current(client, other_headers)
            other_proposal = {"proposal_id": "other-owner-proposal", "itinerary_id": other_baseline["itinerary_id"],
                              "type": "EXTEND_REST", "base_version": 1, "options": [], "no_option_reason": "MOCK"}
            save_proposal(other_proposal, other_id)
            reset_demo(self.database)
            self.assertEqual(self.current(client, headers), baseline)
            self.assertEqual(self.current(client, other_headers), other_baseline)
            with store.connect() as db:
                self.assertEqual(db.execute("SELECT count(*) FROM adapt_proposals WHERE user_id = ?", (other_id,)).fetchone()[0], 1)

    def test_can_map_snapshot_to_an_existing_test_account(self):
        reset_demo(self.database)
        with TestClient(create_app()) as client:
            registration = client.post("/api/v1/auth/register", json={
                "username": "mapped_test_owner", "password": "mapped-mock-only-password",
            })
            owner = registration.json()["user_id"]
            # The fixture IDs are already in use by the default owner: refuse to steal them.
            before = read_current(self.database, DEMO_USER_ID)
            with self.assertRaises(sqlite3.IntegrityError):
                reset_demo(self.database, user_id=owner)
            self.assertEqual(read_current(self.database, DEMO_USER_ID), before)
            # Another duration has a disjoint set of IDs and can be seeded for this owner.
            reset_demo(self.database, days=3, user_id=owner)
            mapped = self.current(client, self.login(client, "mapped_test_owner", "mapped-mock-only-password"))
            self.assertEqual(mapped["user_id"], owner)
            self.assertEqual(len(mapped["days"]), 3)
            self.assertEqual(read_current(self.database, DEMO_USER_ID), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
