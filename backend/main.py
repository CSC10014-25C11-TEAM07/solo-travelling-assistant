import sqlite3
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import itinerary_store as store
from itinerary_api import APIError, mock_plan, router


@asynccontextmanager
async def lifespan(app):
    store.initialize()
    yield


def create_app(resolve_user_id=None, plan_provider=mock_plan):
    app = FastAPI(title="Solo Travelling Assistant", lifespan=lifespan)
    app.state.resolve_user_id = resolve_user_id
    app.state.plan_provider = plan_provider
    app.include_router(router)

    @app.exception_handler(APIError)
    async def api_error(request: Request, error: APIError):
        return JSONResponse(
            status_code=error.status,
            content={"code": error.code, "message": error.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"code": "VALIDATION_ERROR", "message": "Dữ liệu không hợp lệ."},
        )

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
