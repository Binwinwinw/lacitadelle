"""Tests de la route API workflow réservée aux administrateurs."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

login_server = importlib.import_module("login_server")
workflow_runner = importlib.import_module("workflow_runner")
from _helpers import api_post, api_test_context, create_test_user, login_as


API_PATH = "/api/workflow/run"


def _admin(opener, base_url, db_path):
    create_test_user(db_path, "admin", "secret123", role="admin")
    return login_as(opener, base_url, "admin", "secret123")


def test_run_workflow_by_name_wraps_response_and_metadata(monkeypatch):
    monkeypatch.setitem(
        workflow_runner.WORKFLOW_REGISTRY,
        "analyse_md",
        lambda path, prompt: f"{path}: {prompt}",
    )

    result = workflow_runner.run_workflow_by_name(
        "analyse_md",
        "document.md",
        "Summarize",
    )

    assert result == {
        "response": "document.md: Summarize",
        "metadata": {"workflow": "analyse_md"},
    }


def test_post_workflow_run_returns_response_for_admin():
    with api_test_context() as (base_url, opener, db_path):
        token = _admin(opener, base_url, db_path)
        expected = {
            "response": "Analysis complete",
            "metadata": {"workflow": "analyse_md"},
        }
        with patch.object(
            login_server,
            "run_workflow_by_name",
            return_value=expected,
        ) as run_workflow:
            with api_post(
                opener,
                base_url,
                API_PATH,
                token,
                {
                    "workflow": "analyse_md",
                    "path": "document.md",
                    "prompt": "Summarize",
                },
            ) as response:
                assert response.code == 200
                assert json.loads(response.read().decode("utf-8")) == expected

        run_workflow.assert_called_once_with(
            "analyse_md",
            "document.md",
            "Summarize",
        )


def test_post_workflow_run_unknown_workflow_returns_404():
    with api_test_context() as (base_url, opener, db_path):
        token = _admin(opener, base_url, db_path)

        with api_post(
            opener,
            base_url,
            API_PATH,
            token,
            {"workflow": "missing", "path": "document.md", "prompt": "Summarize"},
        ) as response:
            assert response.code == 404
            assert json.loads(response.read().decode("utf-8")) == {
                "error": "Workflow inconnu : missing"
            }


def test_post_workflow_run_invalid_body_returns_400():
    with api_test_context() as (base_url, opener, db_path):
        token = _admin(opener, base_url, db_path)

        with api_post(
            opener,
            base_url,
            API_PATH,
            token,
            {"workflow": "analyse_md", "path": 123, "prompt": "Summarize"},
        ) as response:
            assert response.code == 400


def test_post_workflow_run_requires_admin():
    body = {
        "workflow": "analyse_md",
        "path": "document.md",
        "prompt": "Summarize",
    }
    with api_test_context() as (base_url, opener, db_path):
        with api_post(opener, base_url, API_PATH, "", body) as response:
            assert response.code == 401

        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        with api_post(opener, base_url, API_PATH, token, body) as response:
            assert response.code == 403


def test_post_workflow_run_internal_error_returns_500():
    with api_test_context() as (base_url, opener, db_path):
        token = _admin(opener, base_url, db_path)
        with patch.object(
            login_server,
            "run_workflow_by_name",
            side_effect=RuntimeError("internal detail"),
        ):
            with api_post(
                opener,
                base_url,
                API_PATH,
                token,
                {
                    "workflow": "analyse_md",
                    "path": "document.md",
                    "prompt": "Summarize",
                },
            ) as response:
                assert response.code == 500
                result = json.loads(response.read().decode("utf-8"))
        assert "internal detail" not in result["error"]
