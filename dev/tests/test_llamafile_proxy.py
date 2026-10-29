"""Tests for authenticated, same-origin llamafile proxy routes."""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock, patch

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(TESTS_DIR.parent / "tools"))

import login_server
from _helpers import (
    SESSION_COOKIE_NAME,
    api_test_context,
    create_test_user,
    login_as,
    open_no_redirect,
)


def test_lancer_allows_only_the_local_web_origin_for_llamafile():
    launcher = Path(__file__).resolve().parents[2] / "lancer.bat"
    content = launcher.read_text(encoding="utf-8")

    assert "--cors-origins http://localhost:8081" in content
    assert "--cors-origins http://localhost:8081," not in content


def _upstream_response(payload: bytes):
    response = MagicMock()
    response.status = 200
    response.getcode.return_value = 200
    response.headers = {"Content-Type": "application/json"}
    response.__enter__.return_value = response
    response.read.return_value = payload
    return response


def _api_get(opener, base_url: str, path: str, token: str):
    request = urllib.request.Request(
        f"{base_url}{path}",
        headers={
            "Cookie": f"{SESSION_COOKIE_NAME}={token}",
            "Origin": "https://untrusted.example",
        },
    )
    return open_no_redirect(opener, request)


def test_llamafile_models_proxy_requires_auth_and_forwards_without_cors():
    with api_test_context() as (base_url, opener, db_path):
        response = open_no_redirect(
            opener,
            urllib.request.Request(
                f"{base_url}/api/llamafile/v1/models"
            ),
        )
        assert response.code == 401
        response.close()

        create_test_user(db_path, "proxy-user", "secret123")
        token = login_as(opener, base_url, "proxy-user", "secret123")
        payload = b'{"data":[{"id":"qwen3-1.7b"}]}'
        upstream = _upstream_response(payload)
        with patch.object(
            login_server.urllib.request,
            "urlopen",
            return_value=upstream,
        ) as urlopen:
            response = _api_get(
                opener,
                base_url,
                "/api/llamafile/v1/models",
                token,
            )
            assert response.code == 200
            assert response.read() == payload
            assert "Access-Control-Allow-Origin" not in response.headers
            response.close()

        request = urlopen.call_args.args[0]
        assert request.full_url == login_server.LLAMAFILE_MODELS_URL
        assert request.get_method() == "GET"
        assert urlopen.call_args.kwargs["timeout"] == 60


def test_llamafile_completion_proxy_forwards_json_but_not_authorization():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "proxy-user", "secret123")
        token = login_as(opener, base_url, "proxy-user", "secret123")
        payload = json.dumps(
            {"model": "qwen3-1.7b", "messages": []}
        ).encode("utf-8")
        upstream = _upstream_response(b'{"choices":[]}')
        with patch.object(
            login_server.urllib.request,
            "urlopen",
            return_value=upstream,
        ) as urlopen:
            request = urllib.request.Request(
                f"{base_url}/api/llamafile/v1/chat/completions",
                data=payload,
                headers={
                    "Cookie": f"{SESSION_COOKIE_NAME}={token}",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer client-token",
                },
                method="POST",
            )
            response = open_no_redirect(opener, request)
            assert response.code == 200
            assert response.read() == b'{"choices":[]}'
            response.close()

        upstream_request = urlopen.call_args.args[0]
        assert upstream_request.full_url == login_server.LLAMAFILE_URL
        assert upstream_request.get_method() == "POST"
        assert upstream_request.data == payload
        assert upstream_request.get_header("Content-type") == "application/json"
        assert upstream_request.get_header("Authorization") is None


def test_llamafile_proxy_returns_502_when_runtime_is_unavailable():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "proxy-user", "secret123")
        token = login_as(opener, base_url, "proxy-user", "secret123")
        with patch.object(
            login_server.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            response = _api_get(
                opener,
                base_url,
                "/api/llamafile/v1/models",
                token,
            )
            assert response.code == 502
            assert json.loads(response.read()) == {
                "error": "Serveur de modèle indisponible"
            }
            response.close()
