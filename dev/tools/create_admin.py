#!/usr/bin/env python3
"""create_admin : crée le premier compte admin en CLI.

À lancer après la migration V3, avant tout autre utilisateur.
Le mot de passe généré est affiché une seule fois sur stdout.

Usage :
    python dev/tools/create_admin.py
    python dev/tools/create_admin.py --db path/to/memory.db

Aucune dépendance externe. Python 3.10+ requis.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from citadelle_memory import (
    DB_PATH,
    generate_strong_password,
    hash_password,
    migrate_to_v3,
)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{3,50}$")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _has_admin(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM users WHERE role = 'admin' LIMIT 1"
    ).fetchone()
    return row is not None


def _username_exists(conn: sqlite3.Connection, username: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,)
    ).fetchone()
    return row is not None


def create_first_admin(
    username: str,
    db_path: Path,
) -> tuple[bool, str, str | None]:
    """Crée le premier admin. Retourne (success, message, password_or_None)."""
    if not isinstance(username, str) or not USERNAME_RE.fullmatch(username):
        return (
            False,
            "Nom d'utilisateur invalide (3-50 chars, alphanumérique "
            "+ tiret/underscore uniquement).",
            None,
        )

    migrate_to_v3(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN IMMEDIATE")
        if _has_admin(conn):
            return (
                False,
                "Un admin existe déjà. Utilisez /admin/users pour gérer les comptes.",
                None,
            )
        if _username_exists(conn, username):
            return (
                False,
                f"Le nom d'utilisateur '{username}' est déjà pris.",
                None,
            )

        password = generate_strong_password(16)
        password_hash = hash_password(password)
        conn.execute(
            "INSERT INTO users "
            "(username, password_hash, role, is_active, "
            "must_change_password, created_at, last_login_at) "
            "VALUES (?, ?, 'admin', 1, 1, ?, NULL)",
            (username, password_hash, _now_utc()),
        )
        conn.commit()
        return True, "Admin créé avec succès.", password
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Crée le premier admin de La Citadelle."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help=f"Chemin de la base SQLite (défaut : {DB_PATH}).",
    )
    parser.add_argument(
        "--username",
        type=str,
        default=None,
        help="Nom d'utilisateur (si absent, demandé interactivement).",
    )
    args = parser.parse_args(argv)

    username = args.username
    if username is None:
        try:
            username = input("Nom d'utilisateur : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAnnulé.", file=sys.stderr)
            return 1

    try:
        success, message, password = create_first_admin(username, args.db)
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 1
    if not success:
        print(f"ERREUR : {message}", file=sys.stderr)
        return 1

    print("=" * 38)
    print("ADMIN CRÉÉ")
    print("=" * 38)
    print(f"Username : {username}")
    print(f"Password : {password}")
    print()
    print("⚠️ NOTEZ CE MOT DE PASSE. Il ne sera plus jamais affiché.")
    print("⚠️ Vous devrez le changer à la première connexion.")
    print("=" * 38)
    return 0


if __name__ == "__main__":
    sys.exit(main())