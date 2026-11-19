"""Test du workflow PDF avec extraction et modèle isolés."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflows"))

import analyse_pdf as workflow_module
import workflow_engine
from analyse_pdf import analyse_pdf
from workflow_engine import WorkflowError


def test_analyse_pdf_extracts_indexes_searches_and_calls_model(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "report.pdf"
    path.write_bytes(b"%PDF-1.4")
    extracted = "La surface du projet est de 42 metres carres."
    calls = []

    def fake_call_model(prompt, model_path, timeout):
        calls.append((prompt, model_path, timeout))
        return "La surface est de 42 metres carres."

    monkeypatch.setattr(workflow_module, "extract_pdf", lambda _: extracted)
    monkeypatch.setattr(workflow_engine, "call_model", fake_call_model)
    conn = sqlite3.connect(":memory:")

    result = analyse_pdf(path, "Quelle est la surface ?", conn=conn)

    assert result == "La surface est de 42 metres carres."
    assert len(calls) == 1
    assert "42 metres carres" in calls[0][0]
    assert calls[0][2] == 180
    conn.close()


def test_analyse_pdf_surfaces_clear_error_when_pypdf_is_missing(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "report.pdf"
    path.write_bytes(b"%PDF-1.4")

    def missing_pdf(_):
        raise ImportError("pypdf non installé, PDF non supporté")

    monkeypatch.setattr(workflow_module, "extract_pdf", missing_pdf)

    with pytest.raises(
        WorkflowError,
        match="pypdf non installé, PDF non supporté",
    ):
        analyse_pdf(path, "Résumé")
