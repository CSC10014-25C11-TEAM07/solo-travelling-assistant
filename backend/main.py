from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from auth import handle_validation_error, init_auth_db, init_sessions_db, router as auth_router
from places_api import router as places_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_auth_db()
    init_sessions_db()
    yield


app = FastAPI(title="Solo Travelling Assistant", lifespan=lifespan)
app.add_exception_handler(RequestValidationError, handle_validation_error)
app.include_router(auth_router)
app.include_router(places_router)


@app.get("/health")
def health():
    return {"status": "ok"}
