"""Exécution de requêtes SQLite en lecture seule pour les workflows locaux."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence


def query_sql(
    conn: sqlite3.Connection,
    sql: str,
    params: Sequence[object] | Mapping[str, object] | None = None,
) -> list[dict[str, object]]:
    """Exécute une requête commençant par SELECT et retourne ses lignes.

    Les paramètres sont transmis séparément à SQLite; aucune autre instruction
    SQL n'est acceptée.
    """
    if not isinstance(sql, str) or not sql.lstrip().upper().startswith("SELECT"):
        raise ValueError("Seules les requêtes SELECT sont autorisées")

    cursor = conn.execute(sql, params if params is not None else ())
    columns = [column[0] for column in cursor.description or ()]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
