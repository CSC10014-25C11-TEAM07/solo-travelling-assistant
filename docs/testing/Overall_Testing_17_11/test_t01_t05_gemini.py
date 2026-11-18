"""Run T01-T05 over TestClient, with live Gemini for F02 and MOCK routes.

Run from anywhere with the repository backend dependencies installed.
API key and model are read from the current process environment.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
from unittest.mock import patch

sys.dont_write_bytecode = True


class CheckFailed(Exception):
    pass


def check(condition, message):
    if not condition:
        raise CheckFailed(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run(repo, output):
    sys.path.insert(0, str(repo / "backend"))
    # Avoid initializing the separately configured ADAPT demo app at import time.
    os.environ.pop("ADAPT_MODE", None)
    from fastapi.testclient import TestClient
    import auth
    from main import create_app
    from adapt_f05.catalog import Catalog, RouteDay
    from adapt_f05.ranking import GeminiRanker
    from itinerary_api import validate_plan, DraftInput
    from plan_f02 import PlanProvider, mock_templates
    from place_catalog import PlaceCatalog

    data = repo / "backend/data"
    routes = read_json(data / "handoff/routes_mock.json")
    snapshots = {route["route_id"]: read_json(data / route["snapshot"]) for route in routes}
    templates = mock_templates(routes, snapshots)
    route_days = [
        RouteDay(**{key: day[key] for key in RouteDay.__dataclass_fields__})
        for route in routes for day in route["days"]
    ]
    catalog = Catalog.load(data / "fixtures/mock", route_days, mode="MOCK")
    f01_catalog = PlaceCatalog.load()

    class AuditedGemini(GeminiRanker):
        def __init__(self):
            super().__init__()
            self.calls = []

        def rank(self, context):
            record = {"trip_days": context["request"]["trip_days"], "status": "STARTED"}
            self.calls.append(record)
            try:
                result = super().rank(context)
            except Exception as error:
                record.update(status="ERROR", code=getattr(error, "code", "UNEXPECTED_ERROR"))
                raise
            record.update(status="PASS", **self.audit)
            return result

    ranker = AuditedGemini()
    provider = PlanProvider(catalog, templates, ranker=ranker)
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "scope": "API/TestClient + SQLite + live Gemini F02; device UI pending",
        "entry_point": "create_app(plan_provider=PlanProvider(...)); isolated test wiring",
        "plan_dataset": "MOCK",
        "f01_dataset": "backend/data catalog; original record labels retained",
        "dataset_version": read_json(data / "handoff/manifest.json")["dataset_version"],
        "model": ranker.model,
        "python": sys.version,
        "cases": [],
        "gemini_calls": ranker.calls,
    }
    paths = [
        repo / "backend/main.py", repo / "backend/plan_f02.py",
        repo / "backend/adapt_f05/ranking.py", data / "handoff/routes_mock.json",
        data / "fixtures/mock/places.json", data / "fixtures/mock/travel_times.json",
        data / "places.json", data / "travel_times.json",
    ] + [data / route["snapshot"] for route in routes]
    report["file_sha256"] = {
        str(path.relative_to(repo)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }

    state = {"drafts": []}
    credentials = {"username": "tan_live_" + secrets.token_hex(4),
                   "password": secrets.token_urlsafe(24)}

    def response(client, method, url, expected, **kwargs):
        result = getattr(client, method)(url, **kwargs)
        body = result.json()
        code = body.get("code", "")
        check(result.status_code == expected,
              f"{method.upper()} {url}: HTTP {result.status_code}, code={code}, expected {expected}")
        return body

    def run_case(name, action):
        item = {"id": name, "status": "RUNNING"}
        report["cases"].append(item)
        try:
            item["evidence"] = action()
            item["status"] = "PASS"
        except CheckFailed as error:
            item.update(status="FAIL", reason=str(error))
        except Exception as error:
            # Exception text may contain transport details. Record only its type.
            item.update(status="ERROR", error_type=type(error).__name__)
        print(name, item["status"], flush=True)

    with tempfile.TemporaryDirectory(prefix="tan-live-plan-") as directory:
        with patch.object(auth, "DB_PATH", Path(directory) / "test.sqlite3"):
            def app():
                return create_app(plan_provider=provider)

            with TestClient(app()) as client:
                def t01():
                    response(client, "post", "/api/v1/auth/register", 201, json=credentials)
                    duplicate = response(client, "post", "/api/v1/auth/register", 409, json=credentials)
                    check(duplicate["code"] == "USERNAME_TAKEN", "Duplicate username code mismatch")
                    wrong = response(client, "post", "/api/v1/auth/login", 401,
                                     json={**credentials, "password": "wrong-password-for-testing"})
                    check(wrong["code"] == "INVALID_CREDENTIALS", "Wrong password code mismatch")
                    login = response(client, "post", "/api/v1/auth/login", 200, json=credentials)
                    state["headers"] = {"Authorization": "Bearer " + login["access_token"]}
                    return {"register": 201, "duplicate": 409, "wrong_password": 401, "login": 200}

                def headers():
                    check("headers" in state, "T01 login required")
                    return state["headers"]

                def t02():
                    observed = {}
                    for interest in ("coffee", "nature"):
                        result = response(client, "get", "/api/v1/places/recommendations", 200,
                                          params={"interests": interest}, headers=headers())
                        places = result["places"]
                        check(1 <= len(places) <= 3, "Expected 1-3 recommendations")
                        for place in places:
                            check(interest in f01_catalog.places[place["place_id"]].interests,
                                  "Recommendation does not match interest")
                        observed[interest] = [place["place_id"] for place in places]
                    check(observed["coffee"] != observed["nature"], "Suggestions did not change")
                    return observed

                def payload(count):
                    return {"departure_date": "2026-11-12", "return_date": f"2026-11-{11 + count}",
                            "departure_time": "06:00", "interests": ["nature", "coffee"],
                            "min_rest_minutes": 60}

                def t03():
                    evidence = []
                    for count in (3, 4):
                        before = len(ranker.calls)
                        draft = response(client, "post", "/api/v1/itinerary-drafts", 201,
                                         json=payload(count), headers=headers())
                        itinerary = draft["itinerary"]
                        check(len(itinerary["days"]) == count, "Wrong trip length")
                        validate_plan(DraftInput(**payload(count)), itinerary["days"])
                        check(itinerary["status"] == "DRAFT", "Wrong draft status")
                        check(len(ranker.calls) == before + 1 and ranker.calls[-1]["status"] == "PASS",
                              "Successful live Gemini call missing")
                        state["drafts"].append(draft)
                        evidence.append({"trip_days": count, "itinerary": itinerary})
                    return evidence

                def t04():
                    before = len(ranker.calls)
                    missing = payload(3)
                    del missing["return_date"]
                    for invalid in (missing, {**payload(3), "return_date": "2026-11-11"}):
                        body = response(client, "post", "/api/v1/itinerary-drafts", 422,
                                        json=invalid, headers=headers())
                        check(body["code"] == "VALIDATION_ERROR", "Validation code mismatch")
                    check(len(ranker.calls) == before, "Invalid input called Gemini")
                    return {"missing_return_date": 422, "return_before_departure": 422,
                            "gemini_calls": 0}

                run_case("T01", t01)
                run_case("T02", t02)
                run_case("T03", t03)
                run_case("T04", t04)

                def t05():
                    check(len(state["drafts"]) == 2, "T03 must create both 3D and 4D drafts")
                    current = response(client, "get", "/api/v1/itineraries/current", 200,
                                       headers=headers())
                    check(current["itinerary"] is None, "Draft was saved as current before confirmation")
                    saved = []
                    for draft in state["drafts"]:
                        confirmed = response(client, "post",
                                             f"/api/v1/itinerary-drafts/{draft['draft_id']}/confirm", 200,
                                             json={}, headers=headers())["itinerary"]
                        check(confirmed["status"] == "CURRENT", "Confirmation did not save CURRENT")
                        activity = confirmed["days"][0]["activities"][0]
                        updated = response(client, "patch",
                                           f"/api/v1/itineraries/{confirmed['itinerary_id']}/activities/{activity['activity_id']}",
                                           200, json={"status": "DONE", "base_version": confirmed["version"]},
                                           headers=headers())["itinerary"]
                        check(updated["version"] == confirmed["version"] + 1, "Version not incremented")
                        changed = next(a for day in updated["days"] for a in day["activities"]
                                       if a["activity_id"] == activity["activity_id"])
                        check(changed["status"] == "DONE" and changed["completed_at"], "DONE not stored")
                        with TestClient(app()) as reopened:
                            loaded = response(reopened, "get", "/api/v1/itineraries/current", 200,
                                              headers=headers())["itinerary"]
                        check(loaded == updated, "Reopened app did not return the stored itinerary")
                        saved.append({"trip_days": len(loaded["days"]), "itinerary": loaded})
                    return {"reopen": "new app instance and same SQLite/session", "saved": saved}

                run_case("T05", t05)

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["passed"] = all(case["status"] == "PASS" for case in report["cases"])
    output.mkdir(parents=True, exist_ok=False)
    (output / "T01-T05-results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Evidence:", output / "T01-T05-results.json")
    return 0 if report["passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not os.environ.get("GEMINI_API_KEY") or not os.environ.get("GEMINI_MODEL"):
        parser.error("Set GEMINI_API_KEY and GEMINI_MODEL in this terminal before running.")
    repo = args.repo.resolve()
    if not (repo / "backend/main.py").is_file():
        parser.error("--repo must point to the repository root.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = args.output or Path(__file__).resolve().parent / "runs" / stamp
    if output.exists():
        parser.error("Output directory must be new.")
    return run(repo, output)


if __name__ == "__main__":
    raise SystemExit(main())
