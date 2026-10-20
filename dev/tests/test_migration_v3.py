"""Tests pour migrate_to_v3."""

import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from citadelle_memory import _connect, _utcnow, migrate_to_v3


def _get_user_columns(db_path: Path) -> list[str]:
    with _connect(db_path) as conn:
        rows = conn.execute("PRAGMA table_info(users)").fetchall()
        return [row["name"] for row in rows]


def _create_v2_database(db_path: Path) -> None:
    with closing(sqlite3.connect(str(db_path))) as conn:
        conn.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "username TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "user_id INTEGER NOT NULL, title TEXT, created_at TEXT NOT NULL, "
            "updated_at TEXT NOT NULL, FOREIGN KEY (user_id) "
            "REFERENCES users(id) ON DELETE CASCADE)"
        )
        conn.execute(
            "CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "session_id INTEGER NOT NULL, role TEXT NOT NULL, "
            "content TEXT NOT NULL, created_at TEXT NOT NULL, metadata TEXT, "
            "FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE)"
        )
        user_cursor = conn.execute(
            "INSERT INTO users (username, created_at) VALUES (?, ?)",
            ("legacy", _utcnow()),
        )
        now = _utcnow()
        session_cursor = conn.execute(
            "INSERT INTO sessions (user_id, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (user_cursor.lastrowid, "Legacy session", now, now),
        )
        conn.execute(
            "INSERT INTO messages "
            "(session_id, role, content, created_at, metadata) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_cursor.lastrowid, "user", "Legacy message", now, None),
        )
        conn.commit()


def test_migration_from_v2():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        _create_v2_database(db_path)

        with patch(
            "citadelle_memory.SCHEMA_V3_SQL",
            "CREATE TABLE users (id INTEGER PRIMARY KEY, password_hash TEXT);"
            "CREATE TABLE sessions (",
        ):
            try:
                migrate_to_v3(db_path)
                assert False, "La migration invalide devait échouer"
            except sqlite3.OperationalError:
                pass
        with _connect(db_path) as conn:
            assert conn.execute("SELECT username FROM users").fetchone()[0] == "legacy"
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1

        migrate_to_v3(db_path)
        cols = _get_user_columns(db_path)
        assert {
            "password_hash",
            "role",
            "is_active",
            "must_change_password",
            "last_login_at",
        }.issubset(cols)
        with _connect(db_path) as conn:
            assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0


def test_migration_idempotent():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        migrate_to_v3(db_path)
        migrate_to_v3(db_path)
        assert "password_hash" in _get_user_columns(db_path)


def test_schema_v3_complete():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        migrate_to_v3(db_path)
        with _connect(db_path) as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name IN ('users','sessions','messages')"
            ).fetchall()
            assert {row["name"] for row in tables} == {
                "users",
                "sessions",
                "messages",
            }
            assert [
                row["name"]
                for row in conn.execute("PRAGMA table_info(sessions)")
            ] == ["id", "user_id", "title", "created_at", "updated_at"]
            assert [
                row["name"]
                for row in conn.execute("PRAGMA table_info(messages)")
            ] == ["id", "session_id", "role", "content", "created_at", "metadata"]
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            try:
                conn.execute(
                    "INSERT INTO users (username, password_hash, role, "
                    "created_at) VALUES (?, ?, ?, ?)",
                    ("u1", "hash", "invalid", _utcnow()),
                )
                assert False, "CHECK doit rejeter role invalide"
            except sqlite3.IntegrityError:
                pass


def run_all():
    tests = [
        test_migration_from_v2,
        test_migration_idempotent,
        test_schema_v3_complete,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()