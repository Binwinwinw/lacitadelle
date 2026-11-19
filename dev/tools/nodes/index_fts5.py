"""Indexation et recherche de passages documentaires avec SQLite FTS5."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

DEFAULT_CHUNK_SIZE = 500
_IRREGULAR_PLURALS = {
    "animaux": "animal",
    "chevaux": "cheval",
    "journaux": "journal",
    "oiseaux": "oiseau",
    "travaux": "travail",
}


def _ensure_table(conn: sqlite3.Connection) -> None:
    """Crée la table virtuelle FTS5 si elle n'existe pas."""
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5("
        "content, path UNINDEXED, metadata UNINDEXED)"
    )


def chunk_by_paragraph(content: str, max_chars: int = 500) -> list[str]:
    """Découpe le texte par paragraphes en respectant une longueur maximale."""
    if not isinstance(content, str):
        raise TypeError("content doit être une chaîne.")
    if isinstance(max_chars, bool) or not isinstance(max_chars, int) or max_chars <= 0:
        raise ValueError("max_chars doit être un entier strictement positif.")

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\r?\n[ \t]*\r?\n+", content)
        if paragraph.strip()
    ]
    chunks = []
    for paragraph in paragraphs:
        while len(paragraph) > max_chars:
            split_at = max(
                paragraph.rfind(" ", 0, max_chars + 1),
                paragraph.rfind("\n", 0, max_chars + 1),
                paragraph.rfind("\t", 0, max_chars + 1),
            )
            if split_at <= 0:
                split_at = max_chars
            chunks.append(paragraph[:split_at].strip())
            paragraph = paragraph[split_at:].strip()
        if paragraph:
            chunks.append(paragraph)
    return chunks


def index_fts5(
    conn: sqlite3.Connection,
    path: str | Path,
    content: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> int:
    """Indexe le contenu par chunks sans valider la transaction de l'appelant."""
    if not isinstance(content, str):
        raise TypeError("content doit être une chaîne.")
    if (
        isinstance(chunk_size, bool)
        or not isinstance(chunk_size, int)
        or chunk_size <= 0
    ):
        raise ValueError("chunk_size doit être un entier strictement positif.")
    if not isinstance(conn, sqlite3.Connection):
        raise TypeError("conn doit être une connexion SQLite.")

    source_path = str(path)
    chunks = chunk_by_paragraph(content, max_chars=chunk_size)
    owns_transaction = not conn.in_transaction
    if owns_transaction:
        conn.execute("BEGIN")
    conn.execute("SAVEPOINT workflow_index_fts5")
    try:
        _ensure_table(conn)
        conn.execute(
            "DELETE FROM documents_fts WHERE path = ?", (source_path,)
        )
        conn.executemany(
            "INSERT INTO documents_fts (content, path, metadata) "
            "VALUES (?, ?, ?)",
            [
                (
                    chunk,
                    source_path,
                    json.dumps({"chunk": index}, ensure_ascii=False),
                )
                for index, chunk in enumerate(chunks)
            ],
        )
        conn.execute("RELEASE workflow_index_fts5")
    except sqlite3.Error:
        conn.execute("ROLLBACK TO workflow_index_fts5")
        conn.execute("RELEASE workflow_index_fts5")
        if owns_transaction:
            conn.rollback()
        raise
    return len(chunks)


def normalize_query(query: str) -> str:
    """Ajoute aux termes les formes singulières courantes pour FTS5."""
    if not isinstance(query, str):
        raise TypeError("query doit être une chaîne.")

    terms = re.findall(r"\w+", query, flags=re.UNICODE)
    variants = []
    for term in terms:
        variants.append(term)
        irregular_singular = _IRREGULAR_PLURALS.get(term.casefold())
        if irregular_singular is not None:
            variants.append(irregular_singular)
        elif len(term) > 3 and term.casefold().endswith("s"):
            variants.append(term[:-1])
    return " ".join(dict.fromkeys(variants))


def rerank(
    results: list[dict[str, object]],
    query: str,
) -> list[dict[str, object]]:
    """Classe les résultats par BM25 avec un bonus pour l'expression exacte."""
    query_phrase = " ".join(query.casefold().split())

    def relevance(result: dict[str, object]) -> float:
        raw_bm25_score = result.get("_bm25", 0.0)
        if isinstance(raw_bm25_score, bool) or not isinstance(
            raw_bm25_score, (int, float)
        ):
            raise TypeError("_bm25 doit être un nombre.")
        bm25_score = float(raw_bm25_score)
        title = Path(str(result.get("path", ""))).stem.casefold()
        content = str(result.get("content", "")).casefold()
        exact_match = query_phrase and (
            query_phrase in title or query_phrase in content
        )
        # FTS5 BM25 is negative; negating it makes higher relevance sort first.
        return -bm25_score + (1.0 if exact_match else 0.0)

    return [
        {key: value for key, value in result.items() if key != "_bm25"}
        for result in sorted(results, key=relevance, reverse=True)
    ]


def search_fts5(
    conn: sqlite3.Connection,
    query: str,
    top_n: int = 5,
) -> list[dict[str, object]]:
    """Retourne les meilleurs passages FTS5 pour les mots de la requête."""
    if not isinstance(query, str):
        raise TypeError("query doit être une chaîne.")
    if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n <= 0:
        raise ValueError("top_n doit être un entier strictement positif.")

    terms = normalize_query(query).split()
    if not terms:
        return []
    match_query = " OR ".join(f'"{term}"' for term in terms)
    rows = conn.execute(
        "SELECT content, path, metadata, bm25(documents_fts) "
        "FROM documents_fts WHERE documents_fts MATCH ? ORDER BY rank",
        (match_query,),
    ).fetchall()
    results = [
        {
            "content": content,
            "path": path,
            "metadata": json.loads(metadata),
            "_bm25": bm25_score,
        }
        for content, path, metadata, bm25_score in rows
    ]
    return rerank(results, query)[:top_n]
