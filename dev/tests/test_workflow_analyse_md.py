"""Test de bout en bout du workflow d'analyse Markdown."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflows"))

import workflow_engine
from analyse_md import analyse_md


def test_analyse_md_extracts_indexes_searches_and_calls_model(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "notes.md"
    path.write_text(
        "# Local retrieval\nAIWorkflow searches this document with FTS5.",
        encoding="utf-8",
    )
    calls = []

    def fake_call_model(prompt, model_path):
        calls.append((prompt, model_path))
        return "Analysis from the matching passage."

    monkeypatch.setattr(workflow_engine, "call_model", fake_call_model)

    result = analyse_md(path, "Explain FTS5", model_path="current.gguf")

    assert result == "Analysis from the matching passage."
    assert len(calls) == 1
    assert "Explain FTS5" in calls[0][0]
    assert "searches this document with FTS5" in calls[0][0]
    assert calls[0][1] == "current.gguf"
