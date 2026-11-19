"""Tests for admin GPU/runtime diagnostics and redacted log tails."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

diagnostic = importlib.import_module("diagnostic")
login_server = importlib.import_module("login_server")
from _helpers import (  # noqa: E402
    api_test_context,
    create_test_user,
    login_as,
    open_no_redirect,
)


def _admin(opener, base_url, db_path):
    create_test_user(db_path, "admin", "secret123", role="admin")
    return login_as(opener, base_url, "admin", "secret123")


def _api_get(opener, base_url, path, token):
    request = urllib.request.Request(
        f"{base_url}{path}",
        headers={
            "Cookie": f"{login_server.SESSION_COOKIE_NAME}={token}",
        },
    )
    return open_no_redirect(opener, request)


def test_get_gpu_status_reports_missing_nvidia_smi(monkeypatch):
    def find_binary(name):
        assert name == "nvidia-smi"
        return None

    monkeypatch.setattr(diagnostic.shutil, "which", find_binary)

    assert diagnostic.get_gpu_status() == {
        "available": False,
        "reason": "nvidia-smi absent",
    }


def test_get_gpu_status_parses_nvidia_smi_csv(monkeypatch):
    def find_binary(name):
        assert name == "nvidia-smi"
        return "nvidia-smi"

    def run_command(args, **kwargs):
        assert args[0] == "nvidia-smi"
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["timeout"] == 5
        return subprocess.CompletedProcess(
            args,
            0,
            stdout="NVIDIA Test GPU, 2048, 8192, 73\n",
            stderr="",
        )

    monkeypatch.setattr(diagnostic.shutil, "which", find_binary)
    monkeypatch.setattr(diagnostic.subprocess, "run", run_command)

    assert diagnostic.get_gpu_status() == {
        "available": True,
        "gpus": [
            {
                "name": "NVIDIA Test GPU",
                "vram_used_mb": 2048,
                "vram_total_mb": 8192,
                "utilization_pct": 73,
            }
        ],
    }


def test_get_llama_gpu_layers_reports_full_offload(monkeypatch):
    def read_logs(source, lines):
        assert source == "llama"
        assert lines == 1000
        return ["llama: offloaded 33/33 layers to GPU"]

    monkeypatch.setattr(diagnostic, "get_recent_logs", read_logs)

    assert diagnostic.get_llama_gpu_layers() == {
        "offloaded": 33,
        "total": 33,
        "on_gpu": True,
        "raw_line": "llama: offloaded 33/33 layers to GPU",
    }


def test_get_llama_gpu_layers_reports_cpu_mode(monkeypatch):
    def read_logs(source, lines):
        assert source == "llama"
        assert lines == 1000
        return ["llama: offloaded 0/33 layers to GPU"]

    monkeypatch.setattr(diagnostic, "get_recent_logs", read_logs)

    assert diagnostic.get_llama_gpu_layers() == {
        "offloaded": 0,
        "total": 33,
        "on_gpu": False,
        "raw_line": "llama: offloaded 0/33 layers to GPU",
    }


def test_get_llama_gpu_layers_reports_partial_offload(monkeypatch):
    def read_logs(source, lines):
        assert source == "llama"
        assert lines == 1000
        return ["llama: offloaded 12/33 layers to GPU"]

    monkeypatch.setattr(diagnostic, "get_recent_logs", read_logs)

    result = diagnostic.get_llama_gpu_layers()

    assert result["offloaded"] == 12
    assert result["total"] == 33
    assert result["on_gpu"] is False


def test_get_llama_gpu_layers_returns_unknown_without_a_matching_line(
    monkeypatch,
):
    def read_logs(source, lines):
        assert source == "llama"
        assert lines == 1000
        return ["runtime started"]

    monkeypatch.setattr(diagnostic, "get_recent_logs", read_logs)

    assert diagnostic.get_llama_gpu_layers() == {
        "offloaded": None,
        "total": None,
        "on_gpu": None,
        "raw_line": None,
    }


def test_get_runtime_status_reports_closed_port_and_model(monkeypatch):
    def closed_port(address, timeout):
        assert address == ("127.0.0.1", 8080)
        assert timeout == 0.5
        raise ConnectionRefusedError()

    def current_model(key, default=None, db_path=None):
        assert key == "current_model_path"
        assert default is None
        assert db_path == diagnostic.DB_PATH
        return "Qwen3.5-9B.gguf"

    monkeypatch.setattr(diagnostic.socket, "create_connection", closed_port)
    monkeypatch.setattr(diagnostic, "get_setting", current_model)

    result = diagnostic.get_runtime_status()

    assert result == {
        "port_8080_open": False,
        "current_model": "Qwen3.5-9B.gguf",
        "uptime_seconds": None,
    }


def test_get_recent_logs_returns_tail_and_redacts_sensitive_lines(
    monkeypatch,
    tmp_path,
):
    log_path = tmp_path / "login.log"
    log_path.write_text(
        "old line\npassword=example-value\nvisible line\n"
        "access_token=example-token\nlast line\n",
        encoding="utf-8",
    )

    def resolve_log_path(source):
        assert source == "llama"
        return log_path

    monkeypatch.setattr(diagnostic, "_log_path", resolve_log_path)

    assert diagnostic.get_recent_logs("llama", lines=4) == [
        "[REDACTED]",
        "visible line",
        "[REDACTED]",
        "last line",
    ]


def test_get_recent_logs_returns_empty_list_for_missing_file(
    monkeypatch,
    tmp_path,
):
    missing_path = tmp_path / "missing.log"

    def resolve_log_path(source):
        assert source == "app"
        return missing_path

    monkeypatch.setattr(diagnostic, "_log_path", resolve_log_path)

    assert diagnostic.get_recent_logs("app") == []


def test_get_api_diagnostic_returns_status_for_admin(monkeypatch):
    expected = {
        "gpu": {"available": False, "reason": "nvidia-smi absent"},
        "llama_layers": {
            "offloaded": None,
            "total": None,
            "on_gpu": None,
            "raw_line": None,
        },
        "runtime": {
            "port_8080_open": False,
            "current_model": "model.gguf",
            "uptime_seconds": None,
        },
    }
    monkeypatch.setattr(login_server, "get_gpu_status", lambda: expected["gpu"])
    monkeypatch.setattr(
        login_server,
        "get_llama_gpu_layers",
        lambda: expected["llama_layers"],
    )
    monkeypatch.setattr(
        login_server,
        "get_runtime_status",
        lambda: expected["runtime"],
    )

    with api_test_context() as (base_url, opener, db_path):
        token = _admin(opener, base_url, db_path)
        with _api_get(opener, base_url, "/api/diagnostic", token) as response:
            assert response.code == 200
            assert json.loads(response.read().decode("utf-8")) == expected


def test_get_api_diagnostic_rejects_non_admin():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        with _api_get(opener, base_url, "/api/diagnostic", token) as response:
            assert response.code == 403


def test_get_api_diagnostic_logs_returns_lines_for_admin(monkeypatch):
    monkeypatch.setattr(
        login_server,
        "get_recent_logs",
        lambda source, lines: [f"{source}:{lines}"],
    )

    with api_test_context() as (base_url, opener, db_path):
        token = _admin(opener, base_url, db_path)
        path = "/api/diagnostic/logs?source=llama&lines=2"
        with _api_get(opener, base_url, path, token) as response:
            assert response.code == 200
            assert json.loads(response.read().decode("utf-8")) == {
                "source": "llama",
                "lines": ["llama:2"],
            }


def test_get_api_diagnostic_logs_rejects_invalid_source():
    with api_test_context() as (base_url, opener, db_path):
        token = _admin(opener, base_url, db_path)
        path = "/api/diagnostic/logs?source=secrets&lines=2"
        with _api_get(opener, base_url, path, token) as response:
            assert response.code == 400


def test_get_api_diagnostic_logs_rejects_out_of_range_lines():
    with api_test_context() as (base_url, opener, db_path):
        token = _admin(opener, base_url, db_path)
        path = "/api/diagnostic/logs?source=llama&lines=1001"
        with _api_get(opener, base_url, path, token) as response:
            assert response.code == 400


def test_diagnostic_page_is_admin_only():
    with api_test_context() as (base_url, opener, db_path):
        admin_token = _admin(opener, base_url, db_path)
        with _api_get(opener, base_url, "/diagnostic", admin_token) as response:
            assert response.code == 200
            assert "Diagnostic GPU" in response.read().decode("utf-8")

        create_test_user(db_path, "alice", "secret123")
        user_token = login_as(opener, base_url, "alice", "secret123")
        with _api_get(opener, base_url, "/diagnostic", user_token) as response:
            assert response.code == 403
