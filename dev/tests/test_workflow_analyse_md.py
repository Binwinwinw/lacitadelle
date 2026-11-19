"""Test de bout en bout du workflow d'analyse Markdown."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflows"))

import workflow_engine
import analyse_md as analyse_md_module
from analyse_md import analyse_md


def test_analyse_md_extracts_indexes_searches_and_calls_model(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "notes.md"
    path.write_text(
        "# Local retrieval\nAIWorkflow searches this document with FTS5.\n\n"
        "Unrelated paragraph should stay out of the retrieval result.",
        encoding="utf-8",
    )
    model_calls = []
    search_calls = []

    def fake_call_model(prompt, model_path, timeout):
        model_calls.append((prompt, model_path, timeout))
        return "Analysis from the matching passage."

    original_search = analyse_md_module.search_fts5

    def record_search(conn, query, top_n=5):
        search_calls.append(top_n)
        return original_search(conn, query, top_n=top_n)

    monkeypatch.setattr(workflow_engine, "call_model", fake_call_model)
    monkeypatch.setattr(analyse_md_module, "search_fts5", record_search)

    result = analyse_md(path, "Explain FTS5", model_path="current.gguf")

    assert result == "Analysis from the matching passage."
    assert search_calls == [20]
    assert len(model_calls) == 1
    assert "Explain FTS5" in model_calls[0][0]
    assert "reprends la valeur exacte" in model_calls[0][0]
    assert "searches this document with FTS5" in model_calls[0][0]
    assert "Unrelated paragraph" not in model_calls[0][0]
    assert model_calls[0][1:] == ("current.gguf", 180)
