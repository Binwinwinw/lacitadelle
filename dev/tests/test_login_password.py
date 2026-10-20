"""Tests pour POST /login avec mot de passe."""

import importlib
import sqlite3
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from http.cookies import SimpleCookie
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
def login_context():
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


def create_user(
    db_path: Path,
    username: str,
    password: str,
    must_change: int = 0,
    is_active: int = 1,
) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role, is_active, "
            "must_change_password, created_at, last_login_at) "
            "VALUES (?, ?, 'user', ?, ?, ?, NULL)",
            (
                username,
                citadelle_memory.hash_password(password),
                is_active,
                must_change,
                citadelle_memory._utcnow(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def post_login(opener, base_url: str, username: str, password: str):
    request = urllib.request.Request(
        f"{base_url}/login",
        data=urlencode({"username": username, "password": password}).encode(
            "utf-8"
        ),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    return open_no_redirect(opener, request)


def test_login_ok():
    with login_context() as (base_url, db_path):
        create_user(db_path, "alice", "secret123")
        opener = urllib.request.build_opener(NoRedirect())
        response = post_login(opener, base_url, "alice", "secret123")
        assert response.code == 302
        assert response.headers.get("Location") == "/"
        cookie = SimpleCookie()
        cookie.load(response.headers.get("Set-Cookie", ""))
        token = cookie[login_server.SESSION_COOKIE_NAME].value
        assert login_server.SESSIONS[token] > 0
        assert login_server.MUST_CHANGE[token] is False


def test_login_wrong_password():
    with login_context() as (base_url, db_path):
        create_user(db_path, "alice", "secret123")
        opener = urllib.request.build_opener(NoRedirect())
        wrong = post_login(opener, base_url, "alice", "wrong")
        unknown = post_login(opener, base_url, "unknown", "wrong")
        assert wrong.code == 401
        assert unknown.code == 401
        assert wrong.read() == unknown.read()


def test_login_inactive_user():
    with login_context() as (base_url, db_path):
        create_user(db_path, "alice", "secret123", is_active=0)
        opener = urllib.request.build_opener(NoRedirect())
        response = post_login(opener, base_url, "alice", "secret123")
        assert response.code == 401


def test_login_must_change_password():
    with login_context() as (base_url, db_path):
        create_user(db_path, "alice", "secret123", must_change=1)
        opener = urllib.request.build_opener(NoRedirect())
        response = post_login(opener, base_url, "alice", "secret123")
        assert response.code == 302
        assert response.headers.get("Location") == "/change-password"
        cookie = SimpleCookie()
        cookie.load(response.headers.get("Set-Cookie", ""))
        token = cookie[login_server.SESSION_COOKIE_NAME].value
        assert login_server.MUST_CHANGE[token] is True


def run_all():
    tests = [
        test_login_ok,
        test_login_wrong_password,
        test_login_inactive_user,
        test_login_must_change_password,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()