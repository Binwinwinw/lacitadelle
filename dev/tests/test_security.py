"""Security tests for V3.1 session, CSRF, and rate-limit controls."""

import json
import sys
import urllib.error
import urllib.request
from http.cookies import SimpleCookie
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(TESTS_DIR.parent / "tools"))

import citadelle_memory
import login_server
from _helpers import (
    SESSION_COOKIE_NAME,
    api_post,
    api_test_context,
    create_test_user,
    login_as,
    open_no_redirect,
)


def _raw_open(opener, request):
    try:
        return opener.open(request, timeout=5)
    except urllib.error.HTTPError as response:
        return response


def _post_login(opener, base_url: str, forwarded_proto: str | None = None):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if forwarded_proto is not None:
        headers["X-Forwarded-Proto"] = forwarded_proto
    request = urllib.request.Request(
        f"{base_url}/login",
        data=urlencode(
            {"username": "alice", "password": "secret123"}
        ).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    return open_no_redirect(opener, request)


def test_cookie_secure_flag_tracks_forwarded_https():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")

        with _post_login(opener, base_url, "https") as response:
            assert response.code == 302
            secure_cookie = SimpleCookie()
            secure_cookie.load(response.headers["Set-Cookie"])
            assert secure_cookie[SESSION_COOKIE_NAME]["secure"]

        with _post_login(opener, base_url) as response:
            assert response.code == 302
            local_cookie = SimpleCookie()
            local_cookie.load(response.headers["Set-Cookie"])
            assert not local_cookie[SESSION_COOKIE_NAME]["secure"]


def test_csrf_rejects_missing_token():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        session_token = login_as(opener, base_url, "alice", "secret123")
        request = urllib.request.Request(
            f"{base_url}/settings/preferences",
            data=json.dumps(
                {"theme": "dark", "font_size": "large"}
            ).encode("utf-8"),
            headers={
                "Cookie": f"{SESSION_COOKIE_NAME}={session_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with _raw_open(opener, request) as response:
            assert response.code == 403
            assert json.loads(response.read()) == {
                "error": "CSRF token invalid"
            }


def test_csrf_accepts_valid_token():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v4(db_path)
        citadelle_memory.migrate_to_v5(db_path)
        citadelle_memory.migrate_to_v6(db_path)
        create_test_user(db_path, "alice", "secret123")
        session_token = login_as(opener, base_url, "alice", "secret123")
        csrf_token = login_server.csrf_token_for_session(session_token)
        assert csrf_token is not None
        request = urllib.request.Request(
            f"{base_url}/settings/preferences",
            data=json.dumps(
                {"theme": "dark", "font_size": "large"}
            ).encode("utf-8"),
            headers={
                "Cookie": f"{SESSION_COOKIE_NAME}={session_token}",
                "Content-Type": "application/json",
                "X-CSRF-Token": csrf_token,
            },
            method="POST",
        )

        with open_no_redirect(opener, request) as response:
            assert response.code == 200
            assert json.loads(response.read())["theme"] == "dark"


def test_rate_limit_login_blocks_sixth_attempt():
    with api_test_context() as (base_url, opener, _):
        statuses = []
        for _ in range(6):
            request = urllib.request.Request(
                f"{base_url}/login",
                data=urlencode(
                    {"username": "unknown", "password": "wrong"}
                ).encode("utf-8"),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with open_no_redirect(opener, request) as response:
                statuses.append(response.code)

        assert statuses == [401, 401, 401, 401, 401, 429]


def test_rate_limits_chat_and_admin_per_ip():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v4(db_path)
        citadelle_memory.migrate_to_v5(db_path)
        citadelle_memory.migrate_to_v6(db_path)
        create_test_user(db_path, "alice", "secret123")
        session_token = login_as(opener, base_url, "alice", "secret123")
        with api_post(
            opener,
            base_url,
            "/api/sessions",
            session_token,
            {"title": "Load test"},
        ) as response:
            session_id = json.loads(response.read())["session_id"]

        statuses = []
        with patch.object(login_server, "call_llamafile", return_value="reply"):
            for _ in range(31):
                with api_post(
                    opener,
                    base_url,
                    f"/api/sessions/{session_id}/messages",
                    session_token,
                    {"content": "hello"},
                ) as response:
                    statuses.append(response.code)

        assert statuses[:30] == [201] * 30
        assert statuses[30] == 429

        create_test_user(db_path, "admin-user", "secret123", role="admin")
        admin_token = login_as(opener, base_url, "admin-user", "secret123")
        admin_statuses = []
        for _ in range(11):
            request = urllib.request.Request(
                f"{base_url}/api/admin/users",
                headers={
                    "Cookie": f"{SESSION_COOKIE_NAME}={admin_token}",
                },
            )
            with open_no_redirect(opener, request) as response:
                admin_statuses.append(response.code)

        assert admin_statuses[:10] == [200] * 10
        assert admin_statuses[10] == 429
