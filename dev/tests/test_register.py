"""Tests pour POST /register."""

import importlib
import json
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

citadelle_memory = importlib.import_module("citadelle_memory")
login_server = importlib.import_module("login_server")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        return None


def open_no_redirect(opener, request):
    try:
        return opener.open(request, timeout=5)
    except urllib.error.HTTPError as response:
        return response


@contextmanager
def register_context():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        with (
            patch.object(login_server, "MEMORY_DB_PATH", db_path),
            patch.object(citadelle_memory, "DB_PATH", db_path),
        ):
            citadelle_memory.migrate_to_v3(db_path)
            login_server.SESSIONS.clear()
            login_server.MUST_CHANGE.clear()
            server = HTTPServer(("127.0.0.1", 0), login_server.RequestHandler)
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                yield f"http://127.0.0.1:{port}", db_path
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
                login_server.SESSIONS.clear()
                login_server.MUST_CHANGE.clear()


def post_register(opener, base_url: str, **fields):
    request = urllib.request.Request(
        f"{base_url}/register",
        data=urlencode(fields).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    return open_no_redirect(opener, request)


def get_user(db_path: Path, username: str) -> dict | None:
    import sqlite3

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def test_register_ok():
    with register_context() as (base_url, db_path):
        opener = urllib.request.build_opener(NoRedirect())
        with opener.open(f"{base_url}/register", timeout=5) as response:
            assert response.code == 200
            assert b'action="/register"' in response.read()
        response = post_register(
            opener,
            base_url,
            username="alice",
            password="secret123",
            password_confirm="secret123",
        )
        assert response.code == 302
        assert response.headers.get("Location") == "/login"
        user = get_user(db_path, "alice")
        assert user is not None
        assert user["role"] == "admin"
        assert user["must_change_password"] == 0
        assert user["password_hash"].startswith("scrypt$")

        response = post_register(
            opener,
            base_url,
            username="bob",
            password="secret123",
            password_confirm="secret123",
        )
        assert response.code == 302
        assert get_user(db_path, "bob")["role"] == "user"


def test_register_invalid_username():
    with register_context() as (base_url, _):
        opener = urllib.request.build_opener(NoRedirect())
        response = post_register(
            opener,
            base_url,
            username="a",
            password="secret123",
            password_confirm="secret123",
        )
        assert response.code == 400


def test_register_short_password():
    with register_context() as (base_url, _):
        opener = urllib.request.build_opener(NoRedirect())
        response = post_register(
            opener,
            base_url,
            username="alice",
            password="short",
            password_confirm="short",
        )
        assert response.code == 400


def test_register_password_mismatch():
    with register_context() as (base_url, _):
        opener = urllib.request.build_opener(NoRedirect())
        response = post_register(
            opener,
            base_url,
            username="alice",
            password="secret123",
            password_confirm="different",
        )
        assert response.code == 400


def test_register_username_exists():
    with register_context() as (base_url, _):
        opener = urllib.request.build_opener(NoRedirect())
        post_register(
            opener,
            base_url,
            username="alice",
            password="secret123",
            password_confirm="secret123",
        )
        response = post_register(
            opener,
            base_url,
            username="alice",
            password="other123",
            password_confirm="other123",
        )
        assert response.code == 400
        assert json.loads(response.read().decode("utf-8"))["error"] == "Nom déjà utilisé"


def run_all():
    tests = [
        test_register_ok,
        test_register_invalid_username,
        test_register_short_password,
        test_register_password_mismatch,
        test_register_username_exists,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()