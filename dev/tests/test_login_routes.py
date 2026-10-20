"""Tests unitaires et d'intégration pour les routes login/logout."""

import io
import importlib
import sqlite3
import sys
import tempfile
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

citadelle_memory = importlib.import_module("citadelle_memory")
login_server = importlib.import_module("login_server")
from _helpers import (
    SESSION_COOKIE_NAME,
    api_test_context,
    create_test_user,
    login_as,
    open_no_redirect,
)

SESSIONS = login_server.SESSIONS
handle_get_index = login_server.handle_get_index
handle_get_login = login_server.handle_get_login
handle_post_login = login_server.handle_post_login
handle_post_logout = login_server.handle_post_logout


def make_handler(body: bytes = b"", cookie: str | None = None):
    handler = MagicMock()
    handler.headers = {"Content-Length": str(len(body))}
    if cookie:
        handler.headers["Cookie"] = cookie
    handler.rfile = io.BytesIO(body)
    handler.wfile = io.BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.send_error = MagicMock()
    return handler


def get_sent_cookie(handler) -> str | None:
    for call in handler.send_header.call_args_list:
        name, value = call.args
        if name == "Set-Cookie":
            return value
    return None


def test_get_login_serves_static():
    handler = make_handler()
    with patch.object(login_server, "serve_static") as serve_static:
        handle_get_login(handler)
    serve_static.assert_called_once_with(handler, "login.html")


def test_post_login_creates_user():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        citadelle_memory.migrate_to_v3(db_path)
        create_test_user(db_path, "alice", "secret123")
        with patch.object(login_server, "MEMORY_DB_PATH", db_path):
            SESSIONS.clear()
            handler = make_handler(b"username=alice&password=secret123")
            handle_post_login(handler)
            cookie = get_sent_cookie(handler)
            assert cookie is not None
            assert SESSION_COOKIE_NAME in cookie
            assert len(SESSIONS) == 1
            conn = sqlite3.connect(str(db_path))
            try:
                row = conn.execute(
                    "SELECT id FROM users WHERE username = ?",
                    ("alice",),
                ).fetchone()
            finally:
                conn.close()
            assert row is not None


def test_post_login_empty_username():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        citadelle_memory.migrate_to_v3(db_path)
        with patch.object(login_server, "MEMORY_DB_PATH", db_path):
            handler = make_handler(b"username=&password=secret123")
            handle_post_login(handler)
            handler.send_response.assert_called_once_with(401)


def test_post_login_reuses_existing_user():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        citadelle_memory.migrate_to_v3(db_path)
        create_test_user(db_path, "bob", "secret123")
        with patch.object(login_server, "MEMORY_DB_PATH", db_path):
            SESSIONS.clear()
            handle_post_login(make_handler(b"username=bob&password=secret123"))
            assert len(SESSIONS) == 1
            first_token = next(iter(SESSIONS))
            handle_post_login(make_handler(b"username=bob&password=secret123"))
            assert len(SESSIONS) == 1
            assert first_token not in SESSIONS
            conn = sqlite3.connect(str(db_path))
            try:
                rows = conn.execute(
                    "SELECT id FROM users WHERE username = ?",
                    ("bob",),
                ).fetchall()
            finally:
                conn.close()
            assert len(rows) == 1


def test_post_logout_revokes_token():
    SESSIONS.clear()
    token = login_server.create_session_token(1)
    handler = make_handler(cookie=f"{SESSION_COOKIE_NAME}={token}")
    handle_post_logout(handler)
    assert token not in SESSIONS
    cookie = get_sent_cookie(handler)
    assert cookie is not None
    assert "Max-Age=0" in cookie
    handler.send_response.assert_called_once_with(302)


def test_get_index_unauthenticated():
    SESSIONS.clear()
    handler = make_handler()
    handle_get_index(handler)
    handler.send_response.assert_called_once_with(302)
    handler.send_header.assert_called_once_with("Location", "/login")


def test_get_index_authenticated():
    SESSIONS.clear()
    token = login_server.create_session_token(42)
    handler = make_handler(cookie=f"{SESSION_COOKIE_NAME}={token}")
    with patch.object(login_server, "serve_static") as serve_static:
        handle_get_index(handler)
    serve_static.assert_called_once_with(handler, "chat.html")


def test_integration_login_and_authenticated_index():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "integration_user", "secret123")
        token = login_as(opener, base_url, "integration_user", "secret123")
        request = urllib.request.Request(
            f"{base_url}/",
            headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"},
        )
        with opener.open(request, timeout=5) as response:
            assert response.status == 200
            assert b"La Citadelle - Chat" in response.read()


def test_integration_logout_revokes_cookie():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "logout_user", "secret123")
        token = login_as(opener, base_url, "logout_user", "secret123")
        request = urllib.request.Request(
            f"{base_url}/logout",
            data=b"",
            headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"},
            method="POST",
        )
        response = open_no_redirect(opener, request)
        assert response.code == 302
        assert response.headers.get("Location") == "/login"
        assert "Max-Age=0" in response.headers.get("Set-Cookie", "")
        response.close()
        assert token not in SESSIONS

        request = urllib.request.Request(
            f"{base_url}/",
            headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"},
        )
        response = open_no_redirect(opener, request)
        assert response.code == 302
        assert response.headers.get("Location") == "/login"
        response.close()


def run_all():
    tests = [
        test_get_login_serves_static,
        test_post_login_creates_user,
        test_post_login_empty_username,
        test_post_login_reuses_existing_user,
        test_post_logout_revokes_token,
        test_get_index_unauthenticated,
        test_get_index_authenticated,
        test_integration_login_and_authenticated_index,
        test_integration_logout_revokes_cookie,
    ]
    passed = 0
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
        passed += 1
    print(f"ALL {passed} TESTS PASSED")


if __name__ == "__main__":
    run_all()