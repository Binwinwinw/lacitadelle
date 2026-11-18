"""Indexation et recherche de passages documentaires avec SQLite FTS5."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

DEFAULT_CHUNK_SIZE = 1000


def _ensure_table(conn: sqlite3.Connection) -> None:
    """Crée la table virtuelle FTS5 si elle n'existe pas."""
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5("
        "content, path UNINDEXED, metadata UNINDEXED)"
    )


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
    chunks = [
        content[offset : offset + chunk_size]
        for offset in range(0, len(content), chunk_size)
    ]
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

    terms = re.findall(r"\w+", query, flags=re.UNICODE)
    if not terms:
        return []
    match_query = " OR ".join(f'"{term}"' for term in terms)
    rows = conn.execute(
        "SELECT content, path, metadata FROM documents_fts "
        "WHERE documents_fts MATCH ? ORDER BY rank LIMIT ?",
        (match_query, top_n),
    ).fetchall()
    return [
        {
            "content": content,
            "path": path,
            "metadata": json.loads(metadata),
        }
        for content, path, metadata in rows
    ]
