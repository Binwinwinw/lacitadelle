"""Tests du dispatcher AIWorkflow et de son confinement de chemins."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
workflow_runner = importlib.import_module("workflow_runner")


def test_run_workflow_by_name_accepts_file_in_allowed_directory(monkeypatch):
    calls = []

    def fake_workflow(path, prompt):
        calls.append((path, prompt))
        return f"{path}: {prompt}"

    monkeypatch.setitem(
        workflow_runner.WORKFLOW_REGISTRY,
        "analyse_md",
        fake_workflow,
    )
    source = "dev/docs/ARCHITECTURE.md"
    expected_path = str(
        (Path(__file__).resolve().parents[2] / source).resolve()
    )

    result = workflow_runner.run_workflow_by_name(
        "analyse_md",
        source,
        "Summarize",
    )

    assert calls == [(expected_path, "Summarize")]
    assert result == {
        "response": f"{expected_path}: Summarize",
        "metadata": {"workflow": "analyse_md"},
    }


def test_run_workflow_by_name_rejects_file_outside_allowed_directories(
    tmp_path,
):
    outside_path = tmp_path / "document.md"
    outside_path.write_text("# Outside", encoding="utf-8")

    with pytest.raises(ValueError, match="^Chemin non autorisé$"):
        workflow_runner.run_workflow_by_name(
            "analyse_md",
            str(outside_path),
            "Summarize",
        )


def test_run_sql_workflow_reads_query_file_contents(monkeypatch, tmp_path):
    bundle_dir = tmp_path
    queries_dir = bundle_dir / "dev" / "tests"
    queries_dir.mkdir(parents=True)
    query_path = queries_dir / "query.sql"
    query_path.write_text("SELECT 1", encoding="utf-8")
    calls = []

    def fake_workflow(sql, prompt):
        calls.append((sql, prompt))
        return "ok"

    monkeypatch.setattr(workflow_runner, "get_bundle_dir", lambda: bundle_dir)
    monkeypatch.setitem(
        workflow_runner.WORKFLOW_REGISTRY,
        "analyse_sql",
        fake_workflow,
    )

    result = workflow_runner.run_workflow_by_name(
        "analyse_sql",
        "dev/tests/query.sql",
        "Analyse",
    )

    assert calls == [("SELECT 1", "Analyse")]
    assert result["response"] == "ok"
