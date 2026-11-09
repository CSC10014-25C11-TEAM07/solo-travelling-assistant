"""Run F01 against an explicit, pinned snapshot of the team's pending auth code.

This is a development integration harness, not an alternate authentication scheme.
Only use refs from the trusted project repository after fetching/reviewing them.
"""

from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
import subprocess
import sys
import types

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from places_api import router as places_router

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def auth_snapshot(ref: str):
    def git(*arguments):
        result = subprocess.run(
            ["git", *arguments], cwd=ROOT, check=True, capture_output=True,
            encoding="utf-8-sig", timeout=15,
        )
        return result.stdout

    commit = git("rev-parse", "--verify", f"{ref}^{{commit}}").strip()
    source = git("show", f"{commit}:backend/auth.py")
    module = types.ModuleType("auth")
    module.__file__ = str(ROOT / "backend" / "auth.py")
    previous = sys.modules.get("auth")
    sys.modules["auth"] = module
    try:
        exec(compile(source, f"<project auth {commit}>", "exec"), module.__dict__)
        required = ("router", "session_response", "init_auth_db", "init_sessions_db",
                    "handle_validation_error")
        if any(not hasattr(module, attribute) for attribute in required):
            raise ValueError("The selected auth snapshot does not expose the agreed interface")
        yield module, commit
    finally:
        if previous is None:
            sys.modules.pop("auth", None)
        else:
            sys.modules["auth"] = previous


def create_integration_app(auth, database: Path) -> FastAPI:
    auth.DB_PATH = database

    @asynccontextmanager
    async def lifespan(_app):
        database.parent.mkdir(parents=True, exist_ok=True)
        auth.init_auth_db()
        auth.init_sessions_db()
        yield

    app = FastAPI(
        title="Solo Travelling Assistant — F01 integration",
        description="F01 + code tài khoản thật từ một snapshot Git. Dữ liệu demo chưa phải bản nghiệm thu.",
        lifespan=lifespan,
    )
    app.add_exception_handler(RequestValidationError, auth.handle_validation_error)
    app.include_router(auth.router)
    app.include_router(places_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
