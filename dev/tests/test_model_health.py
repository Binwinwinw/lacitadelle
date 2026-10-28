"""Tests for llamafile model readiness and identity checks."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import model_health


def _response(model_id: str):
    response = MagicMock()
    response.status = 200
    response.__enter__.return_value = response
    response.read.return_value = json.dumps(
        {"data": [{"id": model_id}]}
    ).encode("utf-8")
    return response


def test_health_check_ok():
    expected = r"C:\models\Qwen3.gguf"
    with patch(
        "model_health.urllib.request.urlopen",
        side_effect=[
            _response("C:/models/Qwen3.gguf"),
            _response("Qwen3.gguf"),
        ],
    ) as urlopen:
        assert model_health.check_model_loaded(expected) == (True, "ok")
        assert model_health.check_model_loaded(expected) == (True, "ok")
    assert urlopen.call_args.args[0] == "http://127.0.0.1:8080/v1/models"


def test_health_check_mismatch():
    with patch(
        "model_health.urllib.request.urlopen",
        return_value=_response("C:/models/other.gguf"),
    ):
        assert model_health.check_model_loaded(
            r"C:\models\Qwen3.gguf"
        ) == (False, "mismatch")


def test_health_check_timeout():
    with patch(
        "model_health.urllib.request.urlopen",
        side_effect=TimeoutError(),
    ):
        assert model_health.check_model_loaded(
            r"C:\models\Qwen3.gguf"
        ) == (False, "timeout")


def test_health_check_http_error():
    error = HTTPError(
        "http://127.0.0.1:8080/v1/models",
        500,
        "server error",
        hdrs=None,
        fp=None,
    )
    with patch(
        "model_health.urllib.request.urlopen",
        side_effect=error,
    ):
        assert model_health.check_model_loaded(
            r"C:\models\Qwen3.gguf"
        ) == (False, "http_error")


def run_all():
    tests = [
        test_health_check_ok,
        test_health_check_mismatch,
        test_health_check_timeout,
        test_health_check_http_error,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
