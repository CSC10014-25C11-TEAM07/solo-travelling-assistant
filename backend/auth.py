import re
import sqlite3
from contextlib import closing
from pathlib import Path
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import HashingError, InvalidHashError, VerificationError, VerifyMismatchError
from argon2.low_level import Type
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StrictStr

router = APIRouter(prefix="/api/v1/auth", tags=["Tài khoản"])
DB_PATH = Path(__file__).with_name("app.sqlite3")
USERNAME_PATTERN = re.compile(r"[a-z0-9_]{3,30}")
password_hasher = PasswordHasher(
    time_cost=2, memory_cost=19456, parallelism=1, type=Type.ID
)


class RegisterInput(BaseModel):
    username: StrictStr
    password: StrictStr


def connect():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_auth_db():
    with closing(connect()) as db, db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)


def error(status, code, message, field=None):
    content = {"code": code, "message": message}
    if field is not None:
        content["field"] = field
    return JSONResponse(status_code=status, content=content)


def invalid(field=None):
    messages = {
        "username": "Tên đăng nhập cần 3–30 ký tự, gồm chữ a–z, số hoặc dấu gạch dưới.",
        "password": "Mật khẩu cần từ 15 đến 128 ký tự.",
    }
    return error(422, "VALIDATION_ERROR", messages.get(field, "Dữ liệu gửi lên không hợp lệ."), field)


def handle_validation_error(_request, exc: RequestValidationError):
    location = exc.errors()[0]["loc"]
    if len(location) == 2 and location[0] == "body" and location[1] in ("username", "password"):
        return invalid(location[1])
    return invalid()


@router.post("/register", status_code=201)
def register(payload: RegisterInput):
    username = payload.username.strip().lower()
    if not USERNAME_PATTERN.fullmatch(username):
        return invalid("username")

    password = payload.password
    if not 15 <= len(password) <= 128:
        return invalid("password")

    try:
        password_bytes = password.encode("utf-8")
    except UnicodeEncodeError:
        return invalid("password")

    user_id = str(uuid4())
    try:
        password_hash = password_hasher.hash(password_bytes)
        with closing(connect()) as db, db:
            result = db.execute(
                """
                INSERT INTO users (user_id, username, password_hash)
                VALUES (?, ?, ?)
                ON CONFLICT(username) DO NOTHING
                """,
                (user_id, username, password_hash),
            )
            if result.rowcount == 0:
                return error(409, "USERNAME_TAKEN", "Tên đăng nhập đã được sử dụng.", "username")
    except (HashingError, sqlite3.Error):
        return error(500, "SERVER_ERROR", "Hệ thống đang gặp lỗi. Vui lòng thử lại.")

    return {"user_id": user_id, "username": username}


def init_sessions_db():
    with closing(connect()) as db, db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY NOT NULL,
                user_id TEXT NOT NULL REFERENCES users(user_id),
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)


@router.post("/login")
def login(payload: RegisterInput):
    username = payload.username.strip().lower()
    invalid_credentials = "Tên đăng nhập hoặc mật khẩu không đúng."

    if not USERNAME_PATTERN.fullmatch(username) or not 15 <= len(payload.password) <= 128:
        return error(401, "INVALID_CREDENTIALS", invalid_credentials)

    try:
        password_bytes = payload.password.encode("utf-8")
    except UnicodeEncodeError:
        return error(401, "INVALID_CREDENTIALS", invalid_credentials)

    try:
        with closing(connect()) as db, db:
            user = db.execute(
                "SELECT user_id, username, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()

            if user is None:
                return error(401, "INVALID_CREDENTIALS", invalid_credentials)

            user_id, saved_username, password_hash = user
            password_hasher.verify(password_hash, password_bytes)

            token = token_urlsafe(32)
            created_at = datetime.now(timezone.utc)
            expires_at = created_at + timedelta(days=7)
            db.execute(
                """
                INSERT INTO sessions (token_hash, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (sha256(token.encode("ascii")).hexdigest(), user_id,
                 created_at.isoformat(), expires_at.isoformat()),
            )
    except VerifyMismatchError:
        return error(401, "INVALID_CREDENTIALS", invalid_credentials)
    except (sqlite3.Error, InvalidHashError, VerificationError):
        return error(500, "SERVER_ERROR", "Hệ thống đang gặp lỗi. Vui lòng thử lại.")

    return {
        "access_token": token,
        "user": {"user_id": user_id, "username": saved_username},
    }


bearer = HTTPBearer(auto_error=False)


def session_response(credentials, *, revoke=False):
    if credentials is None:
        return error(401, "AUTH_REQUIRED", "Vui lòng đăng nhập.")

    token_hash = sha256(credentials.credentials.encode("utf-8")).hexdigest()

    try:
        with closing(connect()) as db, db:
            session = db.execute(
                """
                SELECT users.user_id, users.username, sessions.expires_at
                FROM sessions
                JOIN users ON users.user_id = sessions.user_id
                WHERE sessions.token_hash = ?
                """,
                (token_hash,),
            ).fetchone()

            if session is None:
                return error(401, "INVALID_SESSION", "Phiên đăng nhập không hợp lệ.")

            user_id, username, expires_at = session
            if datetime.fromisoformat(expires_at) <= datetime.now(timezone.utc):
                return error(401, "SESSION_EXPIRED", "Phiên đăng nhập đã hết hạn.")

            if revoke:
                db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
                return {"message": "Đã đăng xuất."}

            return {"user_id": user_id, "username": username}
    except (sqlite3.Error, ValueError):
        return error(500, "SERVER_ERROR", "Hệ thống đang gặp lỗi. Vui lòng thử lại.")


@router.get("/me")
def me(credentials=Depends(bearer)):
    return session_response(credentials)


@router.post("/logout")
def logout(credentials=Depends(bearer)):
    return session_response(credentials, revoke=True)
