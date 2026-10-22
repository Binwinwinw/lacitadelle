"""Tests de l'expiration serveur et du cookie de session."""

import sys
import time
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import login_server
from _helpers import SESSION_COOKIE_NAME, api_test_context, open_no_redirect


def clear_sessions():
    login_server.SESSIONS.clear()
    login_server.MUST_CHANGE.clear()
    login_server.SESSION_EXPIRY.clear()


def test_session_expired():
    clear_sessions()
    token = login_server.create_session_token(user_id=1)
    login_server.SESSION_EXPIRY[token] = time.time() - 1

    assert login_server.is_session_valid(token) is False
    assert token not in login_server.SESSIONS
    assert token not in login_server.MUST_CHANGE
    assert token not in login_server.SESSION_EXPIRY

    with api_test_context() as (base_url, opener, _):
        token = login_server.create_session_token(user_id=1)
        login_server.SESSION_EXPIRY[token] = time.time() - 1
        request = urllib.request.Request(
            f"{base_url}/api/sessions",
            headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"},
        )
        with open_no_redirect(opener, request) as response:
            assert response.code == 401
        assert token not in login_server.SESSIONS
        assert token not in login_server.SESSION_EXPIRY


def test_session_not_expired():
    clear_sessions()
    token = login_server.create_session_token(user_id=2)

    assert login_server.is_session_valid(token) is True
    assert login_server.SESSION_EXPIRY[token] > time.time()

    handler = MagicMock()
    login_server.set_cookie_token(handler, token)
    cookie = handler.send_header.call_args.args[1]
    assert "Max-Age=86400" in cookie


def test_create_replaces_old_and_clears_expiry():
    clear_sessions()
    old = login_server.create_session_token(user_id=3)
    new = login_server.create_session_token(user_id=3)

    assert old not in login_server.SESSIONS
    assert old not in login_server.MUST_CHANGE
    assert old not in login_server.SESSION_EXPIRY
    assert new in login_server.SESSIONS
    assert new in login_server.SESSION_EXPIRY


def test_invalid_token():
    clear_sessions()

    assert login_server.is_session_valid("invalid") is False
    assert login_server.is_session_valid(None) is False


def run_all():
    tests = [
        test_session_expired,
        test_session_not_expired,
        test_create_replaces_old_and_clears_expiry,
        test_invalid_token,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
