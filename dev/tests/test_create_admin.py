"""Tests pour create_first_admin."""

import importlib
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

citadelle_memory = importlib.import_module("citadelle_memory")
create_admin = importlib.import_module("create_admin")


def _get_user(db_path: Path, username: str) -> dict | None:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def test_creation_ok():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        success, message, password = create_admin.create_first_admin(
            "alice_admin", db_path
        )
        assert success is True, message
        assert password is not None
        assert len(password) == 16
        user = _get_user(db_path, "alice_admin")
        assert user is not None
        assert user["role"] == "admin"
        assert user["is_active"] == 1
        assert user["must_change_password"] == 1
        assert user["last_login_at"] is None
        assert user["password_hash"].startswith("scrypt$")
        assert citadelle_memory.verify_password(
            password, user["password_hash"]
        ) is True


def test_refus_si_admin_existe():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        citadelle_memory.migrate_to_v3(db_path)
        conn = sqlite3.connect(str(db_path))
        try:
            conn.executemany(
                "INSERT INTO users "
                "(username, password_hash, role, is_active, "
                "must_change_password, created_at) "
                "VALUES (?, ?, 'admin', 1, 0, ?)",
                [
                    (username, "hash", citadelle_memory._utcnow())
                    for username in ("first_admin", "second_admin")
                ],
            )
            conn.commit()
        finally:
            conn.close()
        success, message, password = create_admin.create_first_admin(
            "third_admin", db_path
        )
        assert success is False
        assert "admin existe déjà" in message
        assert password is None


def test_refus_username_invalide():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        success, message, password = create_admin.create_first_admin(
            "a", db_path
        )
        assert success is False
        assert "invalide" in message
        assert password is None


def test_refus_username_existe():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        citadelle_memory.migrate_to_v3(db_path)
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, "
                "is_active, must_change_password, created_at) "
                "VALUES (?, ?, 'user', 1, 0, ?)",
                ("bob", "scrypt$16384$8$1$00$00", citadelle_memory._utcnow()),
            )
            conn.commit()
        finally:
            conn.close()
        success, message, password = create_admin.create_first_admin(
            "bob", db_path
        )
        assert success is False
        assert "déjà pris" in message
        assert password is None


def run_all():
    tests = [
        test_creation_ok,
        test_refus_si_admin_existe,
        test_refus_username_invalide,
        test_refus_username_existe,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()