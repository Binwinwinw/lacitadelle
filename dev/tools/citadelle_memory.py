#!/usr/bin/env python3
"""citadelle_memory : couche SQLite pour la mémoire des conversations.

Une seule base : citadelle_data/memory.db (à la racine du projet).
Tables principales : users, sessions, messages, preferences et
inference_metrics.

Voir dev/docs/MEMORY_CONTRACT.md pour le schéma détaillé.
La table historique `lacitadelle` est documentée pour la V2, non implémentée.

Aucune dépendance externe. Python 3.10+ requis.
"""

from __future__ import annotations

import json
import hashlib
import hmac
import os
import secrets
import sqlite3
import string
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

# Chemin de la base (à la racine du projet, à côté de dist/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CITADELLE_DATA_DIR = PROJECT_ROOT / "citadelle_data"
DB_PATH = CITADELLE_DATA_DIR / "memory.db"
INTEGRATED_MODEL_GGUF = (
    PROJECT_ROOT
    / "dev"
    / "tools"
    / "vendor"
    / "llamafile"
    / "Qwen3-1.7B-Q4_K_M.gguf"
)
SHA256_INTEGRATED_MODEL_GGUF = (
    "16da7ba1721b1620fa843e0978badd3d93756274fd209a01874b37e29750e207"
)

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

SCRYPT_N = 16384
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_SALT_BYTES = 16
SCRYPT_HASH_BYTES = 32

SCHEMA_V3_SQL = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user','admin')),
    is_active INTEGER NOT NULL DEFAULT 1,
    must_change_password INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    last_login_at TEXT
);

CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
"""

SCHEMA_PREFERENCES_SQL = """
CREATE TABLE IF NOT EXISTS preferences (
    user_id INTEGER PRIMARY KEY,
    theme TEXT NOT NULL DEFAULT 'light'
        CHECK (theme IN ('light', 'dark')),
    font_size TEXT NOT NULL DEFAULT 'normal'
        CHECK (font_size IN ('small', 'normal', 'large')),
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

SCHEMA_INFERENCE_METRICS_SQL = """
CREATE TABLE IF NOT EXISTS inference_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id INTEGER,
    timestamp TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ok','error','timeout')),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
);
"""

SCHEMA_SETTINGS_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def _users_has_password_hash(conn: sqlite3.Connection) -> bool:
    """Détecte si le schéma V3 est déjà appliqué."""
    rows = conn.execute("PRAGMA table_info(users)").fetchall()
    return any(row["name"] == "password_hash" for row in rows)


def migrate_to_v3(db_path: Path | None = None) -> None:
    """Remplace le schéma V2 par V3, en supprimant toutes les données."""
    with _connect(db_path) as conn:
        if _users_has_password_hash(conn):
            return
        conn.execute("PRAGMA foreign_keys = OFF")
        try:
            conn.executescript(
                "BEGIN;"
                "DROP TABLE IF EXISTS messages;"
                "DROP TABLE IF EXISTS sessions;"
                "DROP TABLE IF EXISTS users;"
                + SCHEMA_V3_SQL
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.execute("PRAGMA foreign_keys = ON")


def hash_password(password: str) -> str:
    """Hash scrypt avec les paramètres V3."""
    if not isinstance(password, str) or not password:
        raise ValueError("Mot de passe vide")
    salt = os.urandom(SCRYPT_SALT_BYTES)
    password_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_HASH_BYTES,
    )
    return (
        f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}$"
        f"{salt.hex()}${password_hash.hex()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Vérifie un hash scrypt V3; rejette les formats ou paramètres invalides."""
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False
    parts = stored_hash.split("$")
    if len(parts) != 6 or parts[0] != "scrypt":
        return False
    try:
        n, r, p = map(int, parts[1:4])
        salt = bytes.fromhex(parts[4])
        expected = bytes.fromhex(parts[5])
    except ValueError:
        return False
    if (
        (n, r, p) != (SCRYPT_N, SCRYPT_R, SCRYPT_P)
        or len(salt) != SCRYPT_SALT_BYTES
        or len(expected) != SCRYPT_HASH_BYTES
    ):
        return False
    try:
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected),
        )
    except (ValueError, MemoryError):
        return False
    return hmac.compare_digest(actual, expected)


def generate_strong_password(length: int = 16) -> str:
    """Génère un mot de passe contenant les quatre catégories requises."""
    if not isinstance(length, int) or length < 16:
        raise ValueError("Longueur minimale : 16")
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*"
    alphabet = lowercase + uppercase + digits + symbols
    password_chars = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(symbols),
    ]
    password_chars.extend(
        secrets.choice(alphabet) for _ in range(length - 4)
    )
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


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


def migrate_to_v4(db_path: Path | None = None) -> None:
    """Ajoute la table des préférences utilisateur de façon idempotente."""
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA_PREFERENCES_SQL)


def migrate_to_v5(db_path: Path | None = None) -> None:
    """Ajoute la table des métadonnées d'inférence de façon idempotente."""
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA_INFERENCE_METRICS_SQL)


def migrate_to_v6(db_path: Path | None = None) -> None:
    """Ajoute la table des paramètres runtime de façon idempotente."""
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA_SETTINGS_SQL)


def migrate_to_v7(
    db_path: Path | None = None,
    integrated_model_path: Path | None = None,
) -> bool:
    """Initialise la whitelist de première installation avec le GGUF vérifié."""
    migrate_to_v6(db_path)
    current_model = get_setting("current_model_path", db_path=db_path)
    if current_model:
        try:
            if Path(current_model).is_file():
                return False
        except (OSError, ValueError):
            pass

    model_path = integrated_model_path or INTEGRATED_MODEL_GGUF
    if not model_path.is_file():
        return False

    digest = hashlib.sha256()
    with model_path.open("rb") as model_file:
        for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != SHA256_INTEGRATED_MODEL_GGUF:
        raise ValueError("SHA-256 invalide pour le GGUF intégré.")

    raw_models = get_setting("allowed_models", db_path=db_path)
    if raw_models is not None:
        try:
            models = json.loads(raw_models)
        except json.JSONDecodeError as exc:
            raise ValueError("La whitelist de modèles est invalide.") from exc
        if not isinstance(models, list):
            raise ValueError("La whitelist de modèles doit être une liste.")
        if models:
            return False

    set_setting(
        "allowed_models",
        json.dumps([str(model_path.resolve())]),
        db_path=db_path,
    )
    return True


def get_setting(
    key: str,
    default: str | None = None,
    db_path: Path | None = None,
) -> str | None:
    """Retourne un paramètre, ou sa valeur par défaut s'il est absent."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
        ).fetchone()
    return row["value"] if row is not None else default


def set_setting(
    key: str,
    value: str,
    db_path: Path | None = None,
) -> None:
    """Crée ou met à jour un paramètre runtime."""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO settings (key, value, updated_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET "
            "value = excluded.value, "
            "updated_at = excluded.updated_at",
            (key, value, _utcnow()),
        )


def record_inference(
    user_id: int,
    session_id: int | None,
    duration_ms: int,
    status: str,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    db_path: Path | None = None,
) -> None:
    """Enregistre uniquement les métadonnées non sensibles d'une inférence."""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO inference_metrics "
            "(user_id, session_id, timestamp, duration_ms, status, "
            "prompt_tokens, completion_tokens) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                session_id,
                _utcnow(),
                duration_ms,
                status,
                prompt_tokens,
                completion_tokens,
            ),
        )


def init_db(db_path: Path | None = None) -> None:
    """Initialise la base et crée les tables si absentes."""
    with _connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
    migrate_to_v4(db_path)
    migrate_to_v5(db_path)
    migrate_to_v6(db_path)


def get_preferences(
    conn: sqlite3.Connection,
    user_id: int,
) -> dict[str, str]:
    """Retourne les préférences du user, ou les valeurs par défaut."""
    row = conn.execute(
        "SELECT theme, font_size FROM preferences WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return {"theme": "light", "font_size": "normal"}
    return dict(row)


def set_preferences(
    conn: sqlite3.Connection,
    user_id: int,
    theme: str,
    font_size: str,
) -> None:
    """Crée ou met à jour les préférences d'un user."""
    if theme not in ("light", "dark"):
        raise ValueError("Thème invalide")
    if font_size not in ("small", "normal", "large"):
        raise ValueError("Taille de texte invalide")
    conn.execute(
        "INSERT INTO preferences (user_id, theme, font_size, updated_at) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET "
        "theme = excluded.theme, "
        "font_size = excluded.font_size, "
        "updated_at = excluded.updated_at",
        (user_id, theme, font_size, _utcnow()),
    )


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


def ensure_admin_exists(
    db_path: Path | None = None,
) -> tuple[bool, str, str | None, str]:
    """Crée le compte admin initial s'il n'existe aucun admin actif."""
    with _connect(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        admin = conn.execute(
            "SELECT username FROM users "
            "WHERE role = 'admin' AND is_active = 1 LIMIT 1"
        ).fetchone()
        if admin is not None:
            username = admin["username"]
            return False, username, None, f"Admin existant : {username}"

        username = "superadmin"
        password = generate_strong_password()
        conn.execute(
            "INSERT INTO users "
            "(username, password_hash, role, is_active, "
            "must_change_password, created_at, last_login_at) "
            "VALUES (?, ?, 'admin', 1, 1, ?, NULL)",
            (username, hash_password(password), _utcnow()),
        )
        return True, username, password, "Admin 'superadmin' créé."


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


def list_sessions_for_user(
    user_id: int,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Liste les sessions appartenant à un utilisateur donné."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT s.*, "
            "  (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) "
            "  AS message_count "
            "FROM sessions s "
            "WHERE s.user_id = ? "
            "ORDER BY s.updated_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def get_session_for_user(
    user_id: int,
    session_id: int,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """Retourne la session si elle appartient à l'utilisateur, sinon None.

    Ne révèle pas l'existence d'une session appartenant à un autre user.
    """
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def get_messages_for_user(
    user_id: int,
    session_id: int,
    limit: int | None = None,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Récupère les messages d'une session si elle appartient à l'utilisateur.

    Retourne [] si la session n'existe pas ou appartient à un autre user.
    """
    if get_session_for_user(user_id, session_id, db_path) is None:
        return []
    return get_messages(session_id, limit=limit, db_path=db_path)


def create_session_for_user(
    user_id: int,
    title: str | None = None,
    db_path: Path | None = None,
) -> int:
    """Crée une session pour un user_id donné.

    Contrairement à create_session (V1), ne crée pas d'utilisateur
    par défaut : l'utilisateur doit exister.
    """
    now = _utcnow()
    with _connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO sessions (user_id, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, title, now, now),
        )
        if cursor.lastrowid is None:
            raise MemoryError_("Impossible de récupérer l'identifiant de session")
        return cursor.lastrowid