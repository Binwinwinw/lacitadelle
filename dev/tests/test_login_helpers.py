"""Tests unitaires pour les helpers de session et cookies."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from login_server import (
    SESSIONS,
    SESSION_COOKIE_NAME,
    clear_cookie_token,
    create_session_token,
    get_user_from_token,
    read_cookie_token,
    revoke_session,
    set_cookie_token,
)


def make_fake_handler(cookie_header=None):
    handler = MagicMock()
    handler.headers = {"Cookie": cookie_header} if cookie_header else {}
    return handler


def test_create_session_token():
    SESSIONS.clear()
    token = create_session_token(1)
    assert len(token) >= 32
    assert SESSIONS[token] == 1


def test_create_revokes_old():
    SESSIONS.clear()
    old = create_session_token(1)
    new = create_session_token(1)
    assert old not in SESSIONS
    assert new in SESSIONS


def test_get_user_from_token():
    SESSIONS.clear()
    token = create_session_token(42)
    assert get_user_from_token(token) == 42
    assert get_user_from_token("invalid") is None


def test_revoke_session():
    SESSIONS.clear()
    token = create_session_token(42)
    revoke_session(token)
    assert get_user_from_token(token) is None


def test_read_cookie_none():
    handler = make_fake_handler()
    assert read_cookie_token(handler) is None


def test_read_cookie_valid():
    SESSIONS.clear()
    token = create_session_token(42)
    handler = make_fake_handler(f"{SESSION_COOKIE_NAME}={token}")
    assert read_cookie_token(handler) == token


def test_set_cookie_token():
    SESSIONS.clear()
    token = create_session_token(42)
    handler = MagicMock()
    set_cookie_token(handler, token)
    args, _ = handler.send_header.call_args
    assert args[0] == "Set-Cookie"
    assert token in args[1]
    assert "HttpOnly" in args[1]
    assert "SameSite=Strict" in args[1]
    assert "Path=/" in args[1]


def test_clear_cookie_token():
    handler = MagicMock()
    clear_cookie_token(handler)
    args, _ = handler.send_header.call_args
    assert "Max-Age=0" in args[1]


def run_all():
    tests = [
        test_create_session_token,
        test_create_revokes_old,
        test_get_user_from_token,
        test_revoke_session,
        test_read_cookie_none,
        test_read_cookie_valid,
        test_set_cookie_token,
        test_clear_cookie_token,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()