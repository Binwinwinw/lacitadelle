"""Tests d'intégration pour POST /api/sessions/{id}/messages."""

import importlib
import json
import sys
import urllib.request
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

citadelle_memory = importlib.import_module("citadelle_memory")
login_server = importlib.import_module("login_server")
api_sessions_tests = importlib.import_module("test_api_sessions")
api_test_context = api_sessions_tests.api_test_context
api_post = api_sessions_tests.api_post
login_as = api_sessions_tests.login_as
open_no_redirect = api_sessions_tests.open_no_redirect
SESSION_COOKIE_NAME = login_server.SESSION_COOKIE_NAME


def api_post_message(opener, base_url, token, session_id, body):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    request = urllib.request.Request(
        f"{base_url}/api/sessions/{session_id}/messages",
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    return open_no_redirect(opener, request)


def create_session(opener, base_url, token):
    with api_post(
        opener,
        base_url,
        "/api/sessions",
        token,
        {"title": "Test"},
    ) as response:
        return json.loads(response.read().decode("utf-8"))["session_id"]


def test_post_message_ok():
    with api_test_context() as (base_url, opener, db_path):
        token = login_as(opener, base_url, "alice")
        session_id = create_session(opener, base_url, token)
        with patch.object(login_server, "call_llamafile", return_value="Bonjour!") as call:
            response = api_post_message(
                opener,
                base_url,
                token,
                session_id,
                {"content": "Salut"},
            )
        with response:
            assert response.code == 201
            result = json.loads(response.read().decode("utf-8"))
        assert result["assistant_message"] == {
            "role": "assistant",
            "content": "Bonjour!",
        }
        sent_messages = call.call_args.args[0]
        assert sent_messages[0] == {
            "role": "system",
            "content": login_server.SYSTEM_PROMPT,
        }
        assert sent_messages[-1] == {"role": "user", "content": "Salut"}

        user_id = login_server.SESSIONS[token]
        stored = citadelle_memory.get_messages_for_user(
            user_id,
            session_id,
            db_path=db_path,
        )
        assert [(message["role"], message["content"]) for message in stored] == [
            ("user", "Salut"),
            ("assistant", "Bonjour!"),
        ]


def test_post_message_no_auth():
    with api_test_context() as (base_url, opener, _):
        with patch.object(login_server, "call_llamafile") as call:
            response = api_post_message(
                opener,
                base_url,
                None,
                1,
                {"content": "Salut"},
            )
        with response:
            assert response.code == 401
        call.assert_not_called()


def test_post_message_other_user():
    with api_test_context() as (base_url, opener, _):
        alice_token = login_as(opener, base_url, "alice")
        bob_token = login_as(opener, base_url, "bob")
        session_id = create_session(opener, base_url, alice_token)
        with patch.object(login_server, "call_llamafile") as call:
            response = api_post_message(
                opener,
                base_url,
                bob_token,
                session_id,
                {"content": "Salut"},
            )
        with response:
            assert response.code == 404
        call.assert_not_called()


def test_post_message_empty_content():
    with api_test_context() as (base_url, opener, _):
        token = login_as(opener, base_url, "alice")
        session_id = create_session(opener, base_url, token)
        with patch.object(login_server, "call_llamafile") as call:
            response = api_post_message(
                opener,
                base_url,
                token,
                session_id,
                {"content": "   "},
            )
        with response:
            assert response.code == 400
        call.assert_not_called()


def test_post_message_llamafile_error():
    with api_test_context() as (base_url, opener, db_path):
        token = login_as(opener, base_url, "alice")
        session_id = create_session(opener, base_url, token)
        with patch.object(
            login_server,
            "call_llamafile",
            side_effect=login_server.LoginError("llamafile down"),
        ):
            response = api_post_message(
                opener,
                base_url,
                token,
                session_id,
                {"content": "Salut"},
            )
        with response:
            assert response.code == 502
            result = json.loads(response.read().decode("utf-8"))
        assert "llamafile down" in result["error"]
        assert citadelle_memory.get_messages_for_user(
            login_server.SESSIONS[token],
            session_id,
            db_path=db_path,
        ) == []


def run_all():
    tests = [
        test_post_message_ok,
        test_post_message_no_auth,
        test_post_message_other_user,
        test_post_message_empty_content,
        test_post_message_llamafile_error,
    ]
    passed = 0
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
        passed += 1
    print(f"ALL {passed} TESTS PASSED")


if __name__ == "__main__":
    run_all()
