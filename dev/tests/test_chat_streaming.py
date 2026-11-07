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
from _helpers import (
    SESSION_COOKIE_NAME,
    api_post,
    api_test_context,
    create_test_user,
    login_as,
)


class _FakeSseResponse:
    def __init__(self, events):
        self.lines = [
            f"data: {json.dumps(event)}\n\n".encode("utf-8")
            for event in events
        ]
        self.lines.append(b"data: [DONE]\n\n")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def __iter__(self):
        return iter(self.lines)


def _call_stream(events, *, session_id=None, on_chunk=None):
    response = _FakeSseResponse(events)
    with (
        patch.object(login_server.urllib.request, "urlopen", return_value=response) as urlopen,
        patch.object(login_server, "record_inference"),
    ):
        result = login_server.call_llamafile(
            [{"role": "user", "content": "Salut"}],
            user_id=1,
            session_id=session_id,
            stream=True,
            on_chunk=on_chunk,
        )
    return result, urlopen


def test_stream_relays_content_only_and_ignores_reasoning():
    chunks = []
    events = [
        {"choices": [{"delta": {"reasoning_content": "secret"}}]},
        {"choices": [{"delta": {"role": "assistant", "content": None}}]},
        {
            "choices": [{
                "delta": {
                    "content": "Bonjour",
                    "reasoning_content": "not for the client",
                }
            }]
        },
        {"choices": [{"delta": {"content": " le monde"}}]},
        {"choices": [{"delta": {"content": "!"}}]},
    ]

    result, urlopen = _call_stream(events, on_chunk=chunks.append)

    assert chunks == ["Bonjour", " le monde", "!"]
    assert result == "Bonjour le monde!"
    payload = json.loads(urlopen.call_args.args[0].data)
    assert payload["stream"] is True
    assert "reasoning_content" not in "".join(chunks)


def test_stream_accumulates_only_delta_content():
    events = [
        {"choices": [{"delta": {"reasoning_content": "hidden"}}]},
        {"choices": [{"delta": {"content": "un"}}]},
        {"choices": [{"delta": {"content": " deux"}}]},
        {"choices": [{"delta": {"content": " trois"}}]},
    ]

    result, _ = _call_stream(events)

    assert result == "un deux trois"
    assert "hidden" not in result


def test_stream_saves_complete_assistant_message_once_at_done():
    events = []
    response = _FakeSseResponse([
        {"choices": [{"delta": {"content": "Bonjour"}}]},
        {"choices": [{"delta": {"content": "!"}}]},
    ])

    def save_message(session_id, role, content):
        events.append(("saved", role, content))

    with (
        patch.object(
            login_server.urllib.request,
            "urlopen",
            return_value=response,
        ),
        patch.object(login_server, "record_inference"),
        patch.object(login_server, "add_message", side_effect=save_message) as add_message,
    ):
        result = login_server.call_llamafile(
            [{"role": "user", "content": "Salut"}],
            user_id=1,
            session_id=42,
            stream=True,
            on_chunk=lambda chunk: events.append(("chunk", chunk)),
        )

    assert result == "Bonjour!"
    add_message.assert_called_once_with(42, "assistant", "Bonjour!")
    assert events == [
        ("chunk", "Bonjour"),
        ("chunk", "!"),
        ("saved", "assistant", "Bonjour!"),
    ]


def _create_session(opener, base_url, token):
    with api_post(
        opener,
        base_url,
        "/api/sessions",
        token,
        {"title": "Streaming test"},
    ) as response:
        assert response.code == 201
        return json.loads(response.read().decode("utf-8"))["session_id"]


def _post_message(opener, base_url, token, session_id, body):
    request = urllib.request.Request(
        f"{base_url}/api/sessions/{session_id}/messages",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Cookie": f"{SESSION_COOKIE_NAME}={token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    from _helpers import open_no_redirect

    return open_no_redirect(opener, request)


def test_post_stream_false_keeps_json_response():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        session_id = _create_session(opener, base_url, token)
        with patch.object(
            login_server,
            "call_llamafile",
            return_value="Réponse complète",
        ) as call:
            response = _post_message(
                opener,
                base_url,
                token,
                session_id,
                {"content": "Salut", "stream": False},
            )

        with response:
            assert response.code == 201
            assert response.headers["Content-Type"] == "application/json; charset=utf-8"
            body = json.loads(response.read().decode("utf-8"))
        assert body == {
            "assistant_message": {
                "role": "assistant",
                "content": "Réponse complète",
            }
        }
        assert "stream" not in call.call_args.kwargs


def test_post_stream_true_returns_sse_headers_and_delta():
    with api_test_context() as (base_url, opener, db_path):
        user_id = create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        session_id = _create_session(opener, base_url, token)

        def fake_stream(messages, user_id, session_id, *, stream, on_chunk):
            assert stream is True
            on_chunk("Bonjour")
            on_chunk("!")
            login_server.add_message(session_id, "assistant", "Bonjour!")
            return "Bonjour!"

        with patch.object(login_server, "call_llamafile", side_effect=fake_stream):
            response = _post_message(
                opener,
                base_url,
                token,
                session_id,
                {"content": "Salut", "stream": True},
            )
            with response:
                assert response.code == 200
                assert response.headers["Content-Type"] == (
                    "text/event-stream; charset=utf-8"
                )
                assert response.headers["Cache-Control"] == "no-cache"
                assert response.headers["X-Accel-Buffering"] == "no"
                body = response.read().decode("utf-8")

        assert 'data: {"status": "thinking"}' in body
        assert 'data: {"delta": "Bonjour"}' in body
        assert 'data: {"delta": "!"}' in body
        assert 'data: {"done": true, "content": "Bonjour!"}' in body
        assert "reasoning_content" not in body
        stored = citadelle_memory.get_messages_for_user(
            user_id,
            session_id,
            db_path=db_path,
        )
        assert [(message["role"], message["content"]) for message in stored] == [
            ("user", "Salut"),
            ("assistant", "Bonjour!"),
        ]
