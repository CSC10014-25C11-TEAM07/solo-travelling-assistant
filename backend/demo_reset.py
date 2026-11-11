"""Reset an explicitly marked test SQLite database from Bảo 04's MOCK bundle.

This is a local testing utility, never a production HTTP endpoint. It reuses the
team's account/itinerary/proposal schema and leaves other accounts untouched.
"""

from contextlib import closing, contextmanager
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3

import auth
import adapt_store
import itinerary_store as store
from data_handoff import load_mock, mock_snapshot

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DEFAULT_DATABASE = ROOT / ".test-data" / "tan-demo.test.sqlite3"
PURPOSE = "solo-travelling-assistant/mock-reset/v1"
DEMO_USER_ID = "MOCK-TAN-USER"
DEMO_USERNAME = "mock_tan_demo"
# Public, synthetic credentials for the isolated test database only.
DEMO_PASSWORD = "MOCK-only-test-password-2026"
SCENARIOS = ("T06", "T08", "T13", "T15")


class ResetError(ValueError):
    pass


def fingerprint(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class DemoBundle:
    dataset_version: str
    dataset_fingerprint: str
    snapshot_path: str
    catalog_path: str
    scenario: str
    route: dict
    snapshot: dict


def load_bundle(days=4, scenario="T06", data_dir=DATA_DIR):
    """Validate the chosen complete snapshot and its scenario-specific catalog."""
    if days not in (3, 4) or scenario not in SCENARIOS:
        raise ResetError("Chọn chuyến 3/4 ngày và ca T06/T08/T13/T15.")
    data_dir = Path(data_dir).resolve()
    sources = {}

    def read(relative):
        path = (data_dir / relative).resolve()
        if not path.is_relative_to(data_dir):
            raise ResetError("Đường dẫn fixture phải nằm trong bộ dữ liệu.")
        raw = path.read_text(encoding="utf-8-sig")
        sources[str(path.relative_to(data_dir))] = hashlib.sha256(raw.encode()).hexdigest()
        return json.loads(raw)

    manifest = read("handoff/manifest.json")
    routes = read(manifest["mock_routes"])
    route = next((r for r in routes if r["route_id"] == f"MOCK-{days}D"), None)
    case = next((c for c in read(manifest["scenarios"]) if c["test_id"] == scenario), None)
    if route is None or case is None:
        raise ResetError(f"Thiếu cấu hình tuyến MOCK-{days}D hoặc ca {scenario}.")
    if route["data_status"] != "MOCK" or case["data_status"] != "MOCK":
        raise ResetError("Công cụ chỉ nhận bộ MOCK.")
    snapshot = read(route["snapshot"])
    catalog_path = case["catalog"]
    read(f"{catalog_path}/places.json")
    read(f"{catalog_path}/travel_times.json")
    catalog = load_mock(data_dir / catalog_path)
    report = mock_snapshot(route, snapshot, catalog)
    if not report["passed"]:
        raise ResetError("Snapshot MOCK không hợp lệ: " + "; ".join(report["errors"]))
    if snapshot["status"] != "CURRENT" or snapshot["version"] != 1:
        raise ResetError("Snapshot ban đầu phải là CURRENT version 1.")
    if len(snapshot["days"]) != days:
        raise ResetError("Snapshot không khớp số ngày đã chọn.")
    expected_fields = {
        "itinerary_id", "user_id", "departure_date", "return_date", "departure_time",
        "interests", "min_rest_minutes", "status", "version", "created_at", "confirmed_at", "days",
    }
    if set(snapshot) != expected_fields:
        raise ResetError("Snapshot không khớp cấu trúc lịch; cần đối chiếu với Bảo 06.")
    for day in snapshot["days"]:
        if set(day) != {"day_id", "itinerary_id", "day_number", "date", "end_deadline", "activities"}:
            raise ResetError("Ngày không khớp cấu trúc lưu lịch.")
        for activity in day["activities"]:
            if set(activity) != {
                "activity_id", "day_id", "type", "name", "place_id", "start_time", "end_time",
                "status", "is_optional", "replaces_activity_id", "completed_at",
            }:
                raise ResetError("Hoạt động không khớp cấu trúc lưu lịch.")
            if activity["status"] not in ("PENDING", "DONE"):
                raise ResetError("Snapshot ban đầu không được chứa lịch sử ADAPT.")
    if not isinstance(manifest["dataset_version"], str) or not manifest["dataset_version"]:
        raise ResetError("Thiếu dataset_version.")
    return DemoBundle(manifest["dataset_version"], fingerprint(sources), route["snapshot"],
                      catalog_path, scenario, route, snapshot)


def _connect(database):
    db = sqlite3.connect(database.as_uri() + "?mode=rw", uri=True, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def checked_database(database, *, allow_new=False):
    """Refuse app databases, links, and pre-existing databases without our marker."""
    path = Path(database).expanduser()
    if path.is_symlink():
        raise ResetError("Không reset qua symlink.")
    path = path.resolve()
    if not path.name.endswith(".test.sqlite3") or path == (ROOT / "app.sqlite3").resolve():
        raise ResetError("Chỉ nhận file riêng có đuôi .test.sqlite3; không dùng app.sqlite3.")
    if not path.exists():
        if allow_new:
            return path
        raise ResetError("Cơ sở dữ liệu kiểm thử chưa tồn tại.")
    if not path.is_file() or path.stat().st_nlink != 1:
        raise ResetError("Cơ sở dữ liệu phải là file thường, không có hard link.")
    try:
        with closing(_connect(path)) as db:
            marker = db.execute("SELECT value FROM _demo_reset_meta WHERE key = 'purpose'").fetchone()
            if marker is None or marker["value"] != PURPOSE:
                raise ResetError("File không có dấu nhận diện cơ sở dữ liệu thử.")
    except sqlite3.Error as error:
        raise ResetError("Từ chối file chưa được công cụ khởi tạo làm cơ sở dữ liệu thử.") from error
    return path


@contextmanager
def use_database(database):
    """Bind existing schema initializers to a test file for this CLI process only."""
    original = auth.DB_PATH
    auth.DB_PATH = database
    try:
        yield
    finally:
        auth.DB_PATH = original


def _initialize(database):
    database.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents adopting a file created by another process.
    with database.open("xb"):
        pass
    try:
        with use_database(database):
            auth.init_auth_db()
            auth.init_sessions_db()
            store.initialize()
            adapt_store.initialize()
        with closing(_connect(database)) as db, db:
            db.execute("CREATE TABLE _demo_reset_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("INSERT INTO _demo_reset_meta VALUES ('purpose', ?)", (PURPOSE,))
    except Exception:
        database.unlink()
        raise


def _account(db, user_id):
    if user_id is not None:
        if not db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone():
            raise ResetError("user_id không tồn tại trong cơ sở dữ liệu thử.")
        return user_id
    row = db.execute("SELECT username FROM users WHERE user_id = ?", (DEMO_USER_ID,)).fetchone()
    if row is None:
        if db.execute("SELECT 1 FROM users WHERE username = ?", (DEMO_USERNAME,)).fetchone():
            raise ResetError("Tên tài khoản MOCK đã được dùng bởi user_id khác.")
        db.execute("INSERT INTO users (user_id, username, password_hash) VALUES (?, ?, ?)",
                   (DEMO_USER_ID, DEMO_USERNAME, auth.password_hasher.hash(DEMO_PASSWORD)))
    elif row["username"] != DEMO_USERNAME:
        raise ResetError("Mã tài khoản MOCK đang thuộc tài khoản khác.")
    return DEMO_USER_ID


def _remove_owned(db, user_id):
    inconsistent = db.execute("""
        SELECT 1 FROM adapt_proposals p JOIN itineraries i USING (itinerary_id)
        WHERE p.user_id <> i.user_id AND (p.user_id = ? OR i.user_id = ?)
    """, (user_id, user_id)).fetchone()
    if inconsistent:
        raise ResetError("Đề xuất có quyền sở hữu không nhất quán; chưa reset.")
    db.execute("DELETE FROM adapt_proposals WHERE user_id = ?", (user_id,))
    # Break self-references introduced by rain replacements before deleting history.
    db.execute("""
        UPDATE activities SET replaces_activity_id = NULL WHERE day_id IN (
            SELECT day_id FROM itinerary_days JOIN itineraries USING (itinerary_id) WHERE user_id = ?
        )
    """, (user_id,))
    db.execute("""
        DELETE FROM activities WHERE day_id IN (
            SELECT day_id FROM itinerary_days JOIN itineraries USING (itinerary_id) WHERE user_id = ?
        )
    """, (user_id,))
    db.execute("DELETE FROM itinerary_days WHERE itinerary_id IN (SELECT itinerary_id FROM itineraries WHERE user_id = ?)", (user_id,))
    db.execute("DELETE FROM itineraries WHERE user_id = ?", (user_id,))


def _insert(db, itinerary):
    db.execute("""
        INSERT INTO itineraries (itinerary_id, user_id, departure_date, return_date, departure_time,
            interests, min_rest_minutes, status, version, created_at, confirmed_at)
        VALUES (:itinerary_id, :user_id, :departure_date, :return_date, :departure_time,
            :interests, :min_rest_minutes, :status, :version, :created_at, :confirmed_at)
    """, {**itinerary, "interests": json.dumps(itinerary["interests"])})
    for day in itinerary["days"]:
        db.execute("""
            INSERT INTO itinerary_days (day_id, itinerary_id, day_number, date, end_deadline)
            VALUES (:day_id, :itinerary_id, :day_number, :date, :end_deadline)
        """, day)
        for activity in day["activities"]:
            db.execute("""
                INSERT INTO activities (activity_id, day_id, type, name, place_id, start_time,
                    end_time, status, is_optional, replaces_activity_id, completed_at)
                VALUES (:activity_id, :day_id, :type, :name, :place_id, :start_time,
                    :end_time, :status, :is_optional, :replaces_activity_id, :completed_at)
            """, activity)


def read_current(database, user_id):
    with closing(_connect(checked_database(database))) as db:
        return store.load_itinerary(db, store.current_id(db, user_id), user_id)


def reset_demo(database=DEFAULT_DATABASE, *, days=4, scenario="T06", user_id=None, data_dir=DATA_DIR):
    bundle = load_bundle(days, scenario, data_dir)
    database = checked_database(database, allow_new=True)
    if not database.exists():
        _initialize(database)
    with closing(_connect(database)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        owner = _account(db, user_id)
        expected = deepcopy(bundle.snapshot)
        expected["user_id"] = owner
        for day in expected["days"]:
            day["activities"].sort(key=lambda a: (a["start_time"], a["activity_id"]))
        _remove_owned(db, owner)
        _insert(db, expected)
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise ResetError("Liên kết SQLite không hợp lệ; đã hủy reset.")
        stored = store.load_itinerary(db, store.current_id(db, owner), owner)
        if stored != expected:
            raise ResetError("Lịch đọc lại không khớp snapshot; đã hủy reset.")
        metadata = {
            "dataset_version": bundle.dataset_version,
            "dataset_fingerprint": bundle.dataset_fingerprint,
            "snapshot": bundle.snapshot_path, "catalog": bundle.catalog_path,
            "scenario": scenario, "state_fingerprint": fingerprint(expected),
        }
        db.execute("INSERT OR REPLACE INTO _demo_reset_meta VALUES (?, ?)",
                   (f"owner:{owner}", json.dumps(metadata, ensure_ascii=False, sort_keys=True)))
    # Use a new connection after commit, as a restarted backend would.
    if read_current(database, owner) != expected:
        raise ResetError("Lịch sau commit không khớp snapshot; kiểm tra tác vụ đang ghi đồng thời.")
    return {
        "reset": "PASS", "database": str(database), **metadata,
        "user_id": owner, "itinerary_id": expected["itinerary_id"],
        "status": expected["status"], "version": expected["version"], "day_count": days,
        "activity_count": sum(len(d["activities"]) for d in expected["days"]),
        "target_ids": bundle.route["target_ids"],
        "scope": "MOCK SQLite reset and readback; not Gemini or Android acceptance",
    }
