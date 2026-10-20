"""Tests d'intégration pour les routes API sessions/messages."""

import importlib
import json
import sys
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

citadelle_memory = importlib.import_module("citadelle_memory")
login_server = importlib.import_module("login_server")
from _helpers import (
    NoRedirect,
    api_post,
    api_test_context,
    create_test_user,
    login_as,
    open_no_redirect,
)
SESSION_COOKIE_NAME = login_server.SESSION_COOKIE_NAME


def api_get(opener, base_url: str, path: str, token: str | None = None):
    headers = {}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    request = urllib.request.Request(f"{base_url}{path}", headers=headers)
    return open_no_redirect(opener, request)


def test_api_sessions_requires_auth():
    handler = MagicMock()
    handler.headers = {}
    assert login_server.get_authenticated_user_id(handler) is None

    with api_test_context() as (base_url, opener, _):
        with api_get(opener, base_url, "/api/sessions") as response:
            assert response.code == 401
            assert json.loads(response.read().decode("utf-8")) == {
                "error": "Non authentifié"
            }


def test_api_sessions_list_empty():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        with api_get(opener, base_url, "/api/sessions", token) as response:
            assert response.code == 200
            assert json.loads(response.read().decode("utf-8"))["sessions"] == []


def test_api_sessions_create_and_list():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        with api_post(
            opener,
            base_url,
            "/api/sessions",
            token,
            {"title": "Test 1"},
        ) as response:
            assert response.code == 201
            created = json.loads(response.read().decode("utf-8"))
        assert created["title"] == "Test 1"

        with api_get(opener, base_url, "/api/sessions", token) as response:
            sessions = json.loads(response.read().decode("utf-8"))["sessions"]
        assert len(sessions) == 1
        assert sessions[0]["id"] == created["session_id"]
        assert sessions[0]["title"] == "Test 1"


def test_api_sessions_isolation():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        create_test_user(db_path, "bob", "secret123")
        alice_token = login_as(opener, base_url, "alice", "secret123")
        bob_token = login_as(opener, base_url, "bob", "secret123")
        with api_post(
            opener, base_url, "/api/sessions", alice_token, {"title": "Alice"}
        ):
            pass
        with api_post(
            opener, base_url, "/api/sessions", bob_token, {"title": "Bob"}
        ):
            pass

        with api_get(opener, base_url, "/api/sessions", alice_token) as response:
            alice_sessions = json.loads(response.read().decode("utf-8"))["sessions"]
        with api_get(opener, base_url, "/api/sessions", bob_token) as response:
            bob_sessions = json.loads(response.read().decode("utf-8"))["sessions"]
        assert [session["title"] for session in alice_sessions] == ["Alice"]
        assert [session["title"] for session in bob_sessions] == ["Bob"]


def test_api_messages_get_own():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        with api_post(
            opener, base_url, "/api/sessions", token, {"title": "T"}
        ) as response:
            session_id = json.loads(response.read().decode("utf-8"))["session_id"]
        citadelle_memory.add_message(
            session_id,
            "user",
            "Hello",
            db_path=db_path,
        )

        with api_get(
            opener,
            base_url,
            f"/api/sessions/{session_id}/messages",
            token,
        ) as response:
            assert response.code == 200
            messages = json.loads(response.read().decode("utf-8"))["messages"]
        assert len(messages) == 1
        assert messages[0]["content"] == "Hello"


def test_api_messages_other_user_404():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        create_test_user(db_path, "bob", "secret123")
        alice_token = login_as(opener, base_url, "alice", "secret123")
        bob_token = login_as(opener, base_url, "bob", "secret123")
        with api_post(
            opener, base_url, "/api/sessions", alice_token, {"title": "T"}
        ) as response:
            session_id = json.loads(response.read().decode("utf-8"))["session_id"]

        with api_get(
            opener,
            base_url,
            f"/api/sessions/{session_id}/messages",
            bob_token,
        ) as response:
            assert response.code == 404
            assert json.loads(response.read().decode("utf-8")) == {
                "error": "Session introuvable"
            }


def run_all():
    tests = [
        test_api_sessions_requires_auth,
        test_api_sessions_list_empty,
        test_api_sessions_create_and_list,
        test_api_sessions_isolation,
        test_api_messages_get_own,
        test_api_messages_other_user_404,
    ]
    passed = 0
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
        passed += 1
    print(f"ALL {passed} TESTS PASSED")


if __name__ == "__main__":
    run_all()
