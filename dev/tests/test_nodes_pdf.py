"""Tests du nœud d'extraction PDF."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from nodes.extract_pdf import extract_pdf


def test_extract_pdf_rejects_non_pdf_extension(tmp_path):
    path = tmp_path / "notes.md"
    path.write_text("Markdown", encoding="utf-8")

    with pytest.raises(ValueError, match="Format PDF attendu"):
        extract_pdf(path)


def test_extract_pdf_uses_pypdf_or_reports_missing_dependency(tmp_path):
    path = tmp_path / "document.pdf"
    if importlib.util.find_spec("pypdf") is None:
        path.write_bytes(b"%PDF-1.4")
        with pytest.raises(
            ImportError,
            match="pypdf non installé, PDF non supporté",
        ):
            extract_pdf(path)
        return

    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with path.open("wb") as file:
        writer.write(file)

    assert extract_pdf(path) == ""
