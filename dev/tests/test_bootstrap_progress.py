"""Tests for bootstrap download progress output."""

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import bootstrap


class TTYStringIO(io.StringIO):
    def isatty(self):
        return True


def make_response(chunks, content_length=None):
    response = MagicMock()
    response.read.side_effect = [*chunks, b""]
    response.headers = (
        {"Content-Length": str(content_length)} if content_length is not None else {}
    )
    response.__enter__.return_value = response
    return response


def test_progress_tty(tmp_path):
    output = TTYStringIO()
    response = make_response([b"abc", b"def"], 6)

    with (
        patch.object(bootstrap.urllib.request, "urlopen", return_value=response),
        patch.object(bootstrap.sys, "stdout", output),
    ):
        bootstrap.download("https://example.invalid/model", tmp_path / "model")

    rendered = output.getvalue()
    assert "\r" in rendered
    assert "100%" in rendered
    assert all(ord(char) < 128 for char in rendered)
    assert (tmp_path / "model").read_bytes() == b"abcdef"

    error_output = TTYStringIO()
    error_response = MagicMock()
    error_response.headers = {"Content-Length": "6"}
    error_response.read.side_effect = [b"abc", OSError("connection dropped")]
    error_response.__enter__.return_value = error_response
    error_dest = tmp_path / "failed-model"
    with (
        patch.object(
            bootstrap.urllib.request,
            "urlopen",
            return_value=error_response,
        ),
        patch.object(bootstrap.sys, "stdout", error_output),
    ):
        try:
            bootstrap.download("https://example.invalid/model", error_dest)
        except bootstrap.BootstrapError:
            pass
        else:
            raise AssertionError("download should fail")
    assert error_output.getvalue().endswith("\r")
    assert not error_dest.exists()


def test_progress_non_tty(tmp_path):
    output = io.StringIO()
    response = make_response([b"abc", b"def"])

    with (
        patch.object(bootstrap.urllib.request, "urlopen", return_value=response),
        patch.object(bootstrap.sys, "stdout", output),
        patch.object(bootstrap.time, "monotonic", side_effect=[0, 0, 1, 6, 7]),
    ):
        bootstrap.download("https://example.invalid/model", tmp_path / "model")

    rendered = output.getvalue()
    assert "\r" not in rendered
    assert "%" not in rendered
    assert len(rendered.splitlines()) == 2
    assert "6 o" in rendered
