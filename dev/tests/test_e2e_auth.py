"""Tests e2e auth : parcours complet register → login → chat → logout,
puis parcours must_change_password.

Mocke call_llamafile et utilise les helpers HTTP partagés.
"""

import json
import sqlite3
import sys
import urllib.request
from http.cookies import SimpleCookie
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import login_server
from _helpers import (
    SESSION_COOKIE_NAME,
    api_post,
    api_test_context,
    create_test_user,
    login_as,
    open_no_redirect,
)


def post_form(opener, base_url, path, fields, token=None):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=urlencode(fields).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    return open_no_redirect(opener, request)


def get_with_cookie(opener, base_url, path, token):
    request = urllib.request.Request(
        f"{base_url}{path}",
        headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"},
    )
    return open_no_redirect(opener, request)


def login_with_location(opener, base_url, username, password, location):
    with post_form(
        opener,
        base_url,
        "/login",
        {"username": username, "password": password},
    ) as response:
        assert response.code == 302
        assert response.headers.get("Location") == location
        cookie = SimpleCookie()
        cookie.load(response.headers.get("Set-Cookie", ""))
        assert SESSION_COOKIE_NAME in cookie
        return cookie[SESSION_COOKIE_NAME].value


def test_full_auth_flow():
    with api_test_context() as (base_url, opener, db_path):
        with post_form(
            opener,
            base_url,
            "/register",
            {
                "username": "alice",
                "password": "pass1234",
                "password_confirm": "pass1234",
            },
        ) as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/login"

        conn = sqlite3.connect(str(db_path))
        try:
            row = conn.execute(
                "SELECT role FROM users WHERE username = ?", ("alice",)
            ).fetchone()
        finally:
            conn.close()
        assert row == ("admin",)

        token = login_with_location(
            opener, base_url, "alice", "pass1234", "/"
        )
        with get_with_cookie(opener, base_url, "/", token) as response:
            assert response.code == 200
            assert b"La Citadelle - Chat" in response.read()

        with api_post(
            opener, base_url, "/api/sessions", token, {"title": "Test"}
        ) as response:
            assert response.code == 201
            session_id = json.loads(response.read().decode("utf-8"))[
                "session_id"
            ]

        with get_with_cookie(
            opener, base_url, "/api/sessions", token
        ) as response:
            assert response.code == 200
            sessions = json.loads(response.read().decode("utf-8"))["sessions"]
            assert len(sessions) == 1

        with patch.object(
            login_server,
            "call_llamafile",
            return_value="Bonjour!",
        ) as call:
            with api_post(
                opener,
                base_url,
                f"/api/sessions/{session_id}/messages",
                token,
                {"content": "Salut"},
            ) as response:
                assert response.code == 201
            call.assert_called_once()

        with get_with_cookie(
            opener, base_url, f"/api/sessions/{session_id}/messages", token
        ) as response:
            assert response.code == 200
            messages = json.loads(response.read().decode("utf-8"))["messages"]
            assert [
                (message["role"], message["content"]) for message in messages
            ] == [
                ("user", "Salut"),
                ("assistant", "Bonjour!"),
            ]

        with post_form(opener, base_url, "/logout", {}, token) as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/login"
        assert token not in login_server.SESSIONS
        assert not login_server.SESSIONS

        new_token = login_as(opener, base_url, "alice", "pass1234")
        assert new_token != token
        with get_with_cookie(
            opener, base_url, "/api/sessions", new_token
        ) as response:
            assert response.code == 200
            sessions = json.loads(response.read().decode("utf-8"))["sessions"]
            assert len(sessions) == 1
            assert sessions[0]["id"] == session_id


def test_must_change_password_flow():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(
            db_path, "bob", "temp1234", role="user", must_change=1
        )
        token = login_with_location(
            opener, base_url, "bob", "temp1234", "/change-password"
        )

        with get_with_cookie(opener, base_url, "/", token) as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/change-password"

        with get_with_cookie(
            opener, base_url, "/api/sessions", token
        ) as response:
            assert response.code == 403

        with get_with_cookie(
            opener, base_url, "/change-password", token
        ) as response:
            assert response.code == 200
            assert b"change-password" in response.read()

        with post_form(
            opener,
            base_url,
            "/change-password",
            {
                "old_password": "temp1234",
                "new_password": "new12345",
                "new_password_confirm": "new12345",
            },
            token,
        ) as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/"

        with get_with_cookie(opener, base_url, "/", token) as response:
            assert response.code == 200
        with get_with_cookie(
            opener, base_url, "/api/sessions", token
        ) as response:
            assert response.code == 200

        with post_form(opener, base_url, "/logout", {}, token) as response:
            assert response.code == 302

        with post_form(
            opener,
            base_url,
            "/login",
            {"username": "bob", "password": "temp1234"},
        ) as response:
            assert response.code == 401

        with post_form(
            opener,
            base_url,
            "/login",
            {"username": "bob", "password": "new12345"},
        ) as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/"
            assert SESSION_COOKIE_NAME in response.headers.get("Set-Cookie", "")


def run_all():
    tests = [test_full_auth_flow, test_must_change_password_flow]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
