"""Tests isolés des nœuds outil AIWorkflow."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from nodes.call_model import call_model
from nodes.extract_text import ExtractTextError, extract_text
from nodes.index_fts5 import index_fts5, search_fts5


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("notes.md", "# Notes\nTexte local."),
        ("notes.txt", "Texte local."),
    ],
)
def test_extract_text_reads_markdown_and_text(tmp_path, filename, content):
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")

    assert extract_text(path) == content


def test_extract_text_reports_missing_pypdf(tmp_path, monkeypatch):
    path = tmp_path / "document.pdf"
    path.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setitem(sys.modules, "pypdf", None)

    with pytest.raises(
        ExtractTextError,
        match=r"PDF non supporté \(pypdf absent\)",
    ):
        extract_text(path)


def test_extract_text_refuses_sensitive_content(tmp_path):
    path = tmp_path / "renamed.md"
    path.write_bytes(b"SQLite format 3\x00secret")

    with pytest.raises(PermissionError, match="Fichier sensible"):
        extract_text(path)


def test_index_fts5_and_search_return_relevant_passages():
    conn = sqlite3.connect(":memory:")
    count = index_fts5(
        conn,
        "notes.md",
        "The local workflow uses FTS5 for document retrieval.",
    )

    results = search_fts5(conn, "FTS5 retrieval")

    assert count == 1
    assert results == [
        {
            "content": "The local workflow uses FTS5 for document retrieval.",
            "path": "notes.md",
            "metadata": {"chunk": 0},
        }
    ]
    conn.close()


def test_index_fts5_splits_content_into_configured_chunks():
    conn = sqlite3.connect(":memory:")

    assert index_fts5(conn, "long.txt", "abcdefghij", chunk_size=4) == 3
    assert [
        row[0]
        for row in conn.execute(
            "SELECT content FROM documents_fts ORDER BY rowid"
        )
    ] == ["abcd", "efgh", "ij"]
    conn.close()


def test_index_fts5_leaves_transaction_control_to_caller():
    conn = sqlite3.connect(":memory:")

    index_fts5(conn, "notes.md", "transactional content")

    assert conn.in_transaction
    conn.rollback()
    assert conn.execute(
        "SELECT name FROM sqlite_master WHERE name = 'documents_fts'"
    ).fetchone() is None
    conn.close()


def test_search_fts5_rejects_nonpositive_top_n():
    conn = sqlite3.connect(":memory:")
    index_fts5(conn, "notes.md", "searchable content")

    with pytest.raises(ValueError, match="top_n"):
        search_fts5(conn, "searchable", top_n=0)
    conn.close()


def test_search_fts5_returns_at_most_requested_top_n():
    conn = sqlite3.connect(":memory:")
    for index in range(25):
        index_fts5(conn, f"doc-{index}.md", f"needle passage {index}")

    results = search_fts5(conn, "needle", top_n=20)

    assert len(results) == 20
    conn.close()


def test_search_fts5_matches_plural_query_to_singular_term():
    conn = sqlite3.connect(":memory:")
    index_fts5(conn, "models.md", "Ornith is a champion with a score of 5/5.")

    results = search_fts5(conn, "champions")

    assert len(results) == 1
    assert "Ornith" in results[0]["content"]
    conn.close()


@pytest.mark.parametrize(
    ("model_path", "expected_model"),
    [(None, "LLaMA_CPP"), ("model.gguf", "model.gguf")],
)
def test_call_model_posts_to_local_openai_compatible_api(
    model_path,
    expected_model,
):
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = json.dumps(
        {"choices": [{"message": {"content": "local answer"}}]}
    ).encode("utf-8")
    with patch("client.urllib.request.urlopen", return_value=response) as urlopen:
        assert call_model(
            "Summarize this",
            model_path,
            timeout=33,
        ) == "local answer"

    request = urlopen.call_args.args[0]
    payload = json.loads(request.data)
    assert request.full_url == "http://127.0.0.1:8080/v1/chat/completions"
    assert payload["model"] == expected_model
    assert payload["messages"] == [
        {"role": "user", "content": "Summarize this"}
    ]
    assert urlopen.call_args.kwargs["timeout"] == 33
