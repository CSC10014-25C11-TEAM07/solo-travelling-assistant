import sqlite3
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


def create_app(plan_provider=mock_plan, option_validator=None):
    app = FastAPI(title="Solo Travelling Assistant", lifespan=lifespan)
    app.state.plan_provider = plan_provider
    app.state.option_validator = option_validator
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


app = create_app()
