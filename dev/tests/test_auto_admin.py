"""Tests de l'auto-création de l'administrateur initial."""

import io
import sqlite3
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import citadelle_memory
import login_server


def _initialize_db(db_path: Path) -> None:
    citadelle_memory.migrate_to_v3(db_path)
    citadelle_memory.migrate_to_v4(db_path)


def _insert_admin(db_path: Path, username: str, is_active: int) -> None:
    with citadelle_memory._connect(db_path) as conn:
        conn.execute(
            "INSERT INTO users "
            "(username, password_hash, role, is_active, "
            "must_change_password, created_at, last_login_at) "
            "VALUES (?, ?, 'admin', ?, 0, ?, NULL)",
            (
                username,
                citadelle_memory.hash_password("test-password"),
                is_active,
                citadelle_memory._utcnow(),
            ),
        )


class _StubHTTPServer:
    def __init__(self, address, handler):
        self.address = address
        self.handler = handler

    def serve_forever(self) -> None:
        return

    def server_close(self) -> None:
        return


def _run_main(db_path: Path) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with (
        patch.object(citadelle_memory, "DB_PATH", db_path),
        patch.object(login_server, "MEMORY_DB_PATH", db_path),
        patch.object(login_server, "HTTPServer", _StubHTTPServer),
        redirect_stdout(stdout),
        redirect_stderr(stderr),
    ):
        result = login_server.main()
    return result, stdout.getvalue(), stderr.getvalue()


def test_ensure_admin_creates_superadmin():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        _initialize_db(db_path)

        created, username, password, message = (
            citadelle_memory.ensure_admin_exists(db_path)
        )

        assert created is True
        assert username == "superadmin"
        assert password is not None
        assert len(password) == 16
        assert message == "Admin 'superadmin' créé."
        with citadelle_memory._connect(db_path) as conn:
            admin = conn.execute(
                "SELECT role, is_active, must_change_password, password_hash "
                "FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            assert admin["role"] == "admin"
            assert admin["is_active"] == 1
            assert admin["must_change_password"] == 1
            assert citadelle_memory.verify_password(
                password,
                admin["password_hash"],
            )


def test_ensure_admin_skips_if_active_admin_exists():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        _initialize_db(db_path)
        _insert_admin(db_path, "existing_admin", is_active=1)

        result = citadelle_memory.ensure_admin_exists(db_path)

        assert result == (
            False,
            "existing_admin",
            None,
            "Admin existant : existing_admin",
        )
        with citadelle_memory._connect(db_path) as conn:
            assert conn.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0] == 1


def test_ensure_admin_ignores_inactive_admin():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        _initialize_db(db_path)
        _insert_admin(db_path, "inactive_admin", is_active=0)

        created, username, password, _ = (
            citadelle_memory.ensure_admin_exists(db_path)
        )

        assert created is True
        assert username == "superadmin"
        assert password is not None
        with citadelle_memory._connect(db_path) as conn:
            admins = conn.execute(
                "SELECT username, is_active FROM users WHERE role = 'admin' "
                "ORDER BY username"
            ).fetchall()
        assert [(row["username"], row["is_active"]) for row in admins] == [
            ("inactive_admin", 0),
            ("superadmin", 1),
        ]


def test_main_prints_once_reports_existing_admin_and_continues_on_error():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"

        result, first_output, first_error = _run_main(db_path)
        assert result == 0
        assert "[ADMIN] Admin 'superadmin' créé." in first_output
        password_lines = [
            line for line in first_output.splitlines()
            if line.startswith("[ADMIN] Mot de passe superadmin : ")
        ]
        assert len(password_lines) == 1
        printed_password = password_lines[0].split(" : ", 1)[1]
        assert len(printed_password) == 16
        assert first_error == ""

        result, existing_output, existing_error = _run_main(db_path)
        assert result == 0
        assert "[ADMIN] Admin existant : superadmin" in existing_output
        assert "Mot de passe superadmin" not in existing_output
        assert existing_error == ""

        with patch.object(
            login_server,
            "ensure_admin_exists",
            side_effect=sqlite3.OperationalError("database is locked"),
        ) as ensure_admin:
            result, error_output, error_message = _run_main(db_path)
        assert result == 0
        assert ensure_admin.call_count == 1
        assert error_output.startswith("Proxy La Citadelle démarré")
        assert "[ADMIN] ERREUR" in error_message
        assert "create_admin.py --username superadmin" in error_message


def run_all():
    tests = [
        test_ensure_admin_creates_superadmin,
        test_ensure_admin_skips_if_active_admin_exists,
        test_ensure_admin_ignores_inactive_admin,
        test_main_prints_once_reports_existing_admin_and_continues_on_error,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
