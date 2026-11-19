"""Tests de la route API workflow réservée aux administrateurs."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

login_server = importlib.import_module("login_server")
from _helpers import api_post, api_test_context, create_test_user, login_as


API_PATH = "/api/workflow/run"


def _admin(opener, base_url, db_path):
    create_test_user(db_path, "admin", "secret123", role="admin")
    return login_as(opener, base_url, "admin", "secret123")


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


@pytest.mark.parametrize(
    ("workflow_name", "source"),
    [
        ("analyse_pdf", "dev/docs/document.pdf"),
        ("analyse_sql", "dev/tests/query.sql"),
    ],
)
def test_post_workflow_run_dispatches_extended_workflows(
    workflow_name,
    source,
):
    with api_test_context() as (base_url, opener, db_path):
        token = _admin(opener, base_url, db_path)
        expected = {
            "response": f"{workflow_name}: {source} / Analyse",
            "metadata": {"workflow": workflow_name},
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
                    "workflow": workflow_name,
                    "path": source,
                    "prompt": "Analyse",
                },
            ) as response:
                assert response.code == 200
                result = json.loads(response.read().decode("utf-8"))
        run_workflow.assert_called_once_with(workflow_name, source, "Analyse")

    assert result == expected


def test_post_workflow_run_rejects_path_outside_allowed_directories(tmp_path):
    outside_path = tmp_path / "document.md"
    outside_path.write_text("# Private", encoding="utf-8")

    with api_test_context() as (base_url, opener, db_path):
        token = _admin(opener, base_url, db_path)
        with api_post(
            opener,
            base_url,
            API_PATH,
            token,
            {
                "workflow": "analyse_md",
                "path": str(outside_path),
                "prompt": "Analyse",
            },
        ) as response:
            assert response.code == 400
            assert json.loads(response.read().decode("utf-8")) == {
                "error": "Chemin non autorisé"
            }
