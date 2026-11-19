"""Tests de chunking, normalisation et reranking FTS5."""

from __future__ import annotations

import sqlite3

from dev.tools.nodes.index_fts5 import (
    chunk_by_paragraph,
    index_fts5,
    normalize_query,
    rerank,
    search_fts5,
)


def test_chunk_by_paragraph_keeps_lines_and_separates_paragraphs() -> None:
    content = "# Intro\nFirst line.\nSecond line.\n\n## Next\nThird line."

    assert chunk_by_paragraph(content) == [
        "# Intro\nFirst line.\nSecond line.",
        "## Next\nThird line.",
    ]


def test_chunk_by_paragraph_caps_long_paragraphs() -> None:
    paragraph = "word " * 120

    chunks = chunk_by_paragraph(paragraph, max_chars=50)

    assert len(chunks) > 1
    assert all(len(chunk) <= 50 for chunk in chunks)
    assert " ".join(chunks) == paragraph.strip()


def test_index_fts5_stores_one_chunk_per_paragraph() -> None:
    conn = sqlite3.connect(":memory:")
    content = "# First\nFirst paragraph.\n\n# Second\nSecond paragraph."

    count = index_fts5(conn, "notes.md", content)
    chunks = [
        row[0]
        for row in conn.execute(
            "SELECT content FROM documents_fts ORDER BY rowid"
        )
    ]

    assert count == 2
    assert chunks == ["# First\nFirst paragraph.", "# Second\nSecond paragraph."]
    conn.close()


def test_index_fts5_chunks_long_markdown_by_paragraph() -> None:
    conn = sqlite3.connect(":memory:")
    long_paragraph = "# Intro\n" + "First paragraph line. " * 40
    content = f"{long_paragraph}\n\n# Next\nFinal paragraph."

    count = index_fts5(conn, "long.md", content)
    chunks = [
        row[0]
        for row in conn.execute(
            "SELECT content FROM documents_fts ORDER BY rowid"
        )
    ]

    assert count == 3
    assert all(len(chunk) <= 500 for chunk in chunks)
    assert chunks[0].startswith("# Intro\n")
    assert chunks[-1] == "# Next\nFinal paragraph."
    conn.close()


def test_normalize_query_keeps_irregular_and_regular_plural_variants() -> None:
    assert normalize_query("chevaux champions") == (
        "chevaux cheval champions champion"
    )


def test_search_fts5_matches_irregular_plural_to_singular() -> None:
    conn = sqlite3.connect(":memory:")
    index_fts5(conn, "animals.md", "Un cheval traverse la prairie.")

    results = search_fts5(conn, "chevaux")

    assert len(results) == 1
    content = results[0]["content"]
    assert isinstance(content, str)
    assert "cheval" in content
    conn.close()


def test_rerank_uses_bm25_and_exact_title_or_chunk_bonus() -> None:
    results = [
        {
            "content": "Nothing exact here.",
            "path": "bm25.md",
            "metadata": {},
            "_bm25": -0.8,
        },
        {
            "content": "No matching phrase.",
            "path": "title-match.md",
            "metadata": {},
            "_bm25": -0.01,
        },
        {
            "content": "The title-match phrase is in this chunk.",
            "path": "chunk.md",
            "metadata": {},
            "_bm25": -0.02,
        },
        {
            "content": "The strongest BM25 passage.",
            "path": "strong.md",
            "metadata": {},
            "_bm25": -1.2,
        },
    ]

    ranked = rerank(results, "title-match")

    assert [result["path"] for result in ranked] == [
        "strong.md",
        "chunk.md",
        "title-match.md",
        "bm25.md",
    ]
    assert all("_bm25" not in result for result in ranked)
