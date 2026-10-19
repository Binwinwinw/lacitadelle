"""Tests unitaires pour les helpers HTTP."""

import io
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import login_server
from login_server import (
    WEB_DIR,
    error_response,
    json_response,
    redirect,
    serve_static,
)


def make_handler():
    handler = MagicMock()
    handler.wfile = io.BytesIO()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.send_error = MagicMock()
    return handler


def test_redirect():
    handler = make_handler()
    redirect(handler, "/login")
    handler.send_response.assert_called_once_with(302)
    handler.send_header.assert_called_once_with("Location", "/login")
    handler.end_headers.assert_called_once()


def test_json_response():
    handler = make_handler()
    json_response(handler, {"greeting": "café"}, 200)
    body = handler.wfile.getvalue()
    assert json.loads(body.decode("utf-8")) == {"greeting": "café"}
    assert "café".encode("utf-8") in body
    handler.send_response.assert_called_once_with(200)
    headers = {call.args[0]: call.args[1] for call in handler.send_header.call_args_list}
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert headers["Content-Length"] == str(len(body))
    handler.end_headers.assert_called_once()


def test_error_response():
    handler = make_handler()
    error_response(handler, "Erreur test", 400)
    assert json.loads(handler.wfile.getvalue().decode("utf-8")) == {
        "error": "Erreur test"
    }
    handler.send_response.assert_called_once_with(400)


def test_serve_static_ok():
    content_types = {
        "login.html": "text/html; charset=utf-8",
        "style.css": "text/css; charset=utf-8",
        "chat.js": "application/javascript; charset=utf-8",
    }
    for filename, content_type in content_types.items():
        handler = make_handler()
        serve_static(handler, filename)
        body = handler.wfile.getvalue()
        assert body == (WEB_DIR / filename).read_bytes()
        handler.send_response.assert_called_once_with(200)
        headers = {
            call.args[0]: call.args[1]
            for call in handler.send_header.call_args_list
        }
        assert headers["Content-Type"] == content_type
        assert headers["Content-Length"] == str(len(body))
        handler.end_headers.assert_called_once()

    with tempfile.TemporaryDirectory() as temp_dir:
        binary_file = Path(temp_dir) / "payload.bin"
        binary_file.write_bytes(b"binary")
        with patch.object(login_server, "WEB_DIR", Path(temp_dir)):
            handler = make_handler()
            serve_static(handler, binary_file.name)
        headers = {
            call.args[0]: call.args[1]
            for call in handler.send_header.call_args_list
        }
        assert headers["Content-Type"] == "application/octet-stream"
        assert handler.wfile.getvalue() == b"binary"


def test_serve_static_404():
    handler = make_handler()
    serve_static(handler, "nonexistent_file.txt")
    handler.send_error.assert_called_once_with(404)


def run_all():
    tests = [
        test_redirect,
        test_json_response,
        test_error_response,
        test_serve_static_ok,
        test_serve_static_404,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()