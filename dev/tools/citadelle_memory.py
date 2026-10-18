#!/usr/bin/env python3
"""citadelle_memory : couche SQLite pour la mémoire des conversations.

Une seule base : citadelle_data/memory.db (à la racine du projet).
Trois tables : users, sessions, messages.

Voir dev/docs/MEMORY_CONTRACT.md pour le schéma détaillé.
La 4e table (lacitadelle) est documentée pour la V2, non implémentée.

Aucune dépendance externe. Python 3.10+ requis.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

# Chemin de la base (à la racine du projet, à côté de dist/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CITADELLE_DATA_DIR = PROJECT_ROOT / "citadelle_data"
DB_PATH = CITADELLE_DATA_DIR / "memory.db"

# Utilisateur par défaut
DEFAULT_USERNAME = "lacitadelle"

# Schéma SQL V1
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
"""


class MemoryError_(Exception):
    """Erreur attendue de la couche mémoire."""


def _utcnow() -> str:
    """Retourne l'horodatage UTC au format ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Contexte de connexion SQLite avec fermeture garantie."""
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | None = None) -> None:
    """Initialise la base et crée les tables si absentes."""
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


def ensure_default_user(db_path: Path | None = None) -> int:
    """Crée l'utilisateur par défaut s'il n'existe pas. Retourne son id."""
    init_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (DEFAULT_USERNAME,),
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO users (username, created_at) VALUES (?, ?)",
            (DEFAULT_USERNAME, _utcnow()),
        )
        return cur.lastrowid


def create_session(
    title: str | None = None,
    db_path: Path | None = None,
) -> int:
    """Crée une nouvelle session pour l'utilisateur par défaut."""
    user_id = ensure_default_user(db_path)
    now = _utcnow()
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO sessions (user_id, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, title, now, now),
        )
        return cur.lastrowid


def add_message(
    session_id: int,
    role: str,
    content: str,
    metadata: dict | None = None,
    db_path: Path | None = None,
) -> int:
    """Ajoute un message à une session. Retourne son id.

    role doit être 'user', 'assistant' ou 'system'.
    """
    if role not in ("user", "assistant", "system"):
        raise MemoryError_(f"role invalide : {role}")
    now = _utcnow()
    meta_json = json.dumps(metadata) if metadata else None
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at, metadata) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, now, meta_json),
        )
        # Mettre à jour updated_at de la session
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (now, session_id),
        )
        return cur.lastrowid


def get_messages(
    session_id: int,
    limit: int | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Récupère les messages d'une session, ordonnés par created_at.

    Si limit est fourni, retourne les N derniers messages (les plus
    récents), dans l'ordre chronologique.
    """
    with _connect(db_path) as conn:
        if limit is not None:
            rows = conn.execute(
                "SELECT * FROM ("
                "  SELECT * FROM messages WHERE session_id = ? "
                "  ORDER BY created_at DESC LIMIT ?"
                ") ORDER BY created_at ASC",
                (session_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? "
                "ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]


def list_sessions(db_path: Path | None = None) -> list[dict[str, Any]]:
    """Liste toutes les sessions de l'utilisateur par défaut."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT s.*, "
            "  (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) as message_count "
            "FROM sessions s ORDER BY s.updated_at DESC",
        ).fetchall()
        return [dict(row) for row in rows]


def delete_session(session_id: int, db_path: Path | None = None) -> None:
    """Supprime une session et tous ses messages (CASCADE)."""
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))