import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA = Path(__file__).with_name("itinerary_schema.sql")


def connect(path):
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def write_mock(path):
    with closing(connect(path)) as db:
        # Test-only stand-in for the account table owned by Đăng.
        db.execute("CREATE TABLE users (user_id TEXT PRIMARY KEY NOT NULL)")
        db.executescript(SCHEMA.read_text(encoding="utf-8"))
        with db:
            db.executemany("INSERT INTO users VALUES (?)", [("MOCK-U1",), ("MOCK-U2",)])
            db.execute("""
                INSERT INTO itineraries (
                    itinerary_id, user_id, departure_date, return_date,
                    departure_time, interests, min_rest_minutes, status,
                    created_at, confirmed_at
                ) VALUES (
                    'MOCK-I1', 'MOCK-U1', '2026-11-09', '2026-11-11',
                    '08:00', '["nature"]', 30, 'CURRENT',
                    '2026-11-06T14:00:00Z', '2026-11-06T14:01:00Z'
                )
            """)
            db.executemany("""
                INSERT INTO itinerary_days
                    (day_id, itinerary_id, day_number, date, end_deadline)
                VALUES (?, 'MOCK-I1', ?, ?, '16:30')
            """, [(f"MOCK-D{day}", day, f"2026-11-{day + 8:02d}") for day in range(1, 4)])
            db.execute("""
                INSERT INTO activities (
                    activity_id, day_id, type, name, start_time, end_time,
                    status, is_optional
                ) VALUES (
                    'MOCK-A1', 'MOCK-D1', 'REST', 'MOCK rest', '12:00',
                    '12:30', 'PENDING', 0
                )
            """)
        try:
            with db:
                db.execute("""
                    INSERT INTO itinerary_days VALUES
                        ('MOCK-ORPHAN', 'UNKNOWN', 1, '2026-11-09', '16:30')
                """)
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorcode != sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
                raise
        else:
            raise AssertionError("Foreign key did not reject an orphan day")
        try:
            with db:
                db.execute("""
                    INSERT INTO itineraries (
                        itinerary_id, user_id, departure_date, return_date,
                        departure_time, interests, min_rest_minutes, status,
                        created_at, confirmed_at
                    ) VALUES (
                        'MOCK-ZERO-REST', 'MOCK-U1', '2026-11-09', '2026-11-11',
                        '08:00', '["nature"]', 0, 'DRAFT',
                        '2026-11-06T14:00:00Z', NULL
                    )
                """)
        except sqlite3.IntegrityError as error:
            if error.sqlite_errorcode != sqlite3.SQLITE_CONSTRAINT_CHECK:
                raise
            if "min_rest_minutes" not in str(error):
                raise
        else:
            raise AssertionError("CHECK did not reject min_rest_minutes = 0")
        assert db.execute(
            "SELECT 1 FROM itineraries WHERE itinerary_id = 'MOCK-ZERO-REST'"
        ).fetchone() is None
    print("MOCK written. Foreign key and zero rest checks passed.")


def read_mock(path):
    with closing(connect(path)) as db:
        query = """
            SELECT itinerary_id, version
            FROM itineraries
            WHERE user_id = ? AND status = 'CURRENT'
            ORDER BY confirmed_at DESC
            LIMIT 1
        """
        assert db.execute(query, ("MOCK-U1",)).fetchone() == ("MOCK-I1", 1)
        assert db.execute(query, ("MOCK-U2",)).fetchone() is None
        assert db.execute("""
            SELECT day_id FROM itinerary_days WHERE itinerary_id = ? ORDER BY day_number
        """, ("MOCK-I1",)).fetchall() == [("MOCK-D1",), ("MOCK-D2",), ("MOCK-D3",)]
        assert db.execute("""
            SELECT status FROM activities WHERE day_id = ?
        """, ("MOCK-D1",)).fetchall() == [("PENDING",)]
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    print("MOCK read after restart. Owner filtering and stored rows passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("write", "read"))
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.action == "write":
        if args.path.exists():
            parser.error("Choose a new path for the MOCK database")
        write_mock(args.path)
    else:
        if not args.path.is_file():
            parser.error("Write the MOCK database first")
        read_mock(args.path)

