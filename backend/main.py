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


def create_app(plan_provider=mock_plan, option_validator=None, *, catalog_provider=None):
    app = FastAPI(title="Solo Travelling Assistant", lifespan=lifespan)
    app.state.plan_provider = plan_provider
    app.state.option_validator = option_validator
    app.state.catalog_provider = catalog_provider
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
    from f05_provider import make_catalog_provider

    database = Path(os.environ.get("ADAPT_MOCK_DB", str(DEFAULT_DATABASE)))
    days = int(os.environ.get("ADAPT_MOCK_DAYS", "4"))
    scenario = os.environ.get("ADAPT_MOCK_SCENARIO", "T06")
    bundle = load_bundle(days, scenario)
    auth.DB_PATH = checked_database(database)
    provider = make_catalog_provider(
        DATA_DIR / bundle.catalog_path, {days: bundle.route}, mode="MOCK"
    )
    return create_app(catalog_provider=provider)


app = configured_app()
