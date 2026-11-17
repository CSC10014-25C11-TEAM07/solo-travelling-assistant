import json
import os
import sqlite3
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import auth
import itinerary_store as store
from itinerary_api import APIError, mock_plan, router as itinerary_router
from places_api import router as places_router
from adapt_api import router as adapt_router


@asynccontextmanager
async def lifespan(app):
    auth.init_auth_db()
    auth.init_sessions_db()
    store.initialize()
    from adapt_store import initialize
    initialize()
    yield


def create_app(plan_provider=mock_plan, option_validator=None, *, catalog_provider=None, gemini_adapt=False):
    app = FastAPI(title="Solo Travelling Assistant", lifespan=lifespan)
    app.state.plan_provider = plan_provider
    app.state.option_validator = option_validator
    app.state.catalog_provider = catalog_provider
    app.state.gemini_adapt = gemini_adapt
    app.include_router(auth.router)
    app.include_router(places_router)
    app.include_router(itinerary_router)
    app.include_router(adapt_router)

    @app.exception_handler(APIError)
    async def api_error(request: Request, error: APIError):
        return JSONResponse(
            status_code=error.status,
            content={"code": error.code, "message": error.message},
        )

    app.add_exception_handler(RequestValidationError, auth.handle_validation_error)

    @app.exception_handler(sqlite3.Error)
    async def storage_error(request: Request, error: sqlite3.Error):
        return JSONResponse(
            status_code=500,
            content={"code": "SERVER_ERROR", "message": "Không thể lưu hoặc đọc dữ liệu."},
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


def configured_app():
    if os.environ.get("ADAPT_MODE") != "MOCK":
        return create_app()

    from demo_reset import DATA_DIR, DEFAULT_DATABASE, checked_database, load_bundle
    from adapt_f05.catalog import Catalog
    from adapt_f05.ranking import RuleRanker
    from f05_provider import make_catalog_provider, make_option_validator
    from plan_f02 import PlanProvider, mock_templates

    database = Path(os.environ.get("ADAPT_MOCK_DB", str(DEFAULT_DATABASE)))
    days = int(os.environ.get("ADAPT_MOCK_DAYS", "4"))
    scenario = os.environ.get("ADAPT_MOCK_SCENARIO", "T06")
    bundle = load_bundle(days, scenario)
    auth.DB_PATH = checked_database(database)
    routes = json.loads((DATA_DIR / "handoff/routes_mock.json").read_text(encoding="utf-8-sig"))
    snapshots = {
        route["route_id"]: json.loads((DATA_DIR / route["snapshot"]).read_text(encoding="utf-8-sig"))
        for route in routes
    }
    catalog_path = DATA_DIR / bundle.catalog_path
    provider = make_catalog_provider(
        catalog_path, {len(route["days"]): route for route in routes}, mode="MOCK"
    )
    ranker = os.environ.get("STA_RANKER", "RULES")
    if ranker not in ("RULES", "GEMINI"):
        raise ValueError("STA_RANKER must be RULES or GEMINI")
    gemini = ranker == "GEMINI"
    plan = PlanProvider(
        Catalog.load(catalog_path, [], mode="MOCK"),
        mock_templates(routes, snapshots),
        ranker=None if gemini else RuleRanker(),
    )
    return create_app(
        plan_provider=plan, catalog_provider=provider,
        option_validator=make_option_validator(provider), gemini_adapt=gemini,
    )


app = configured_app()
