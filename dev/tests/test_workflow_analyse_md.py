"""Test de bout en bout du workflow d'analyse Markdown."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflows"))

import workflow_engine
import analyse_md as analyse_md_module
from analyse_md import analyse_md


def test_analyse_md_uses_fts5_when_requested(
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

    result = analyse_md(
        path,
        "Explain FTS5",
        model_path="current.gguf",
        use_retrieval=True,
    )

    assert result == "Analysis from the matching passage."
    assert search_calls == [20]
    assert len(model_calls) == 1
    assert "Explain FTS5" in model_calls[0][0]
    assert "reprends la valeur exacte" in model_calls[0][0]
    assert "searches this document with FTS5" in model_calls[0][0]
    assert "Unrelated paragraph" not in model_calls[0][0]
    assert model_calls[0][1:] == ("current.gguf", 180)


def test_analyse_md_passes_full_short_document_by_default(tmp_path, monkeypatch):
    path = tmp_path / "whole-document.md"
    document = (
        "# Architecture\n\n"
        "The first paragraph describes the workflow.\n\n"
        "The final marker must also reach the model."
    )
    path.write_text(document, encoding="utf-8")
    model_prompts = []

    def fake_call_model(prompt, model_path, timeout):
        model_prompts.append(prompt)
        return "Full document analysis."

    def unexpected_fts(*args, **kwargs):
        raise AssertionError("FTS5 must not run by default.")

    monkeypatch.setattr(workflow_engine, "call_model", fake_call_model)
    monkeypatch.setattr(analyse_md_module, "index_fts5", unexpected_fts)
    monkeypatch.setattr(analyse_md_module, "search_fts5", unexpected_fts)

    result = analyse_md(path, "Summarize the architecture.")

    assert result == "Full document analysis."
    assert len(model_prompts) == 1
    assert document in model_prompts[0]
    assert "Document complet" in model_prompts[0]


def test_analyse_md_use_retrieval_false_passes_full_document(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "explicitly-full.md"
    document = "# Short document\n\nIts complete text must reach the model."
    path.write_text(document, encoding="utf-8")
    model_prompts = []

    def fake_call_model(prompt, model_path, timeout):
        model_prompts.append(prompt)
        return "Full document analysis."

    def unexpected_fts(*args, **kwargs):
        raise AssertionError("FTS5 must stay disabled when use_retrieval=False.")

    monkeypatch.setattr(workflow_engine, "call_model", fake_call_model)
    monkeypatch.setattr(analyse_md_module, "index_fts5", unexpected_fts)
    monkeypatch.setattr(analyse_md_module, "search_fts5", unexpected_fts)

    result = analyse_md(
        path,
        "Summarize the document.",
        use_retrieval=False,
    )

    assert result == "Full document analysis."
    assert len(model_prompts) == 1
    assert document in model_prompts[0]
