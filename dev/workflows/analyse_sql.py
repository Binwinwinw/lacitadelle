"""Workflow d'analyse SQL en lecture seule avec le modèle local."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import citadelle_memory
from nodes.query_sql import query_sql
from workflow_engine import NodeModel, NodeOut, SharedContext, Workflow


def _connect_read_only() -> sqlite3.Connection:
    """Ouvre la base de La Citadelle avec le mode SQLite lecture seule."""
    database_uri = f"{Path(citadelle_memory.DB_PATH).resolve().as_uri()}?mode=ro"
    return sqlite3.connect(database_uri, uri=True)


def _query_and_build_prompt(context: SharedContext) -> str:
    """Exécute la requête validée et prépare les résultats pour le modèle."""
    rows = query_sql(context.data["conn"], context.data["sql"])
    context.set("rows", rows)
    return (
        "Réponds uniquement à partir des résultats SQL ci-dessous. "
        "N'invente pas de valeurs.\n\n"
        f"Question : {context.data['prompt']}\n\n"
        f"Requête SQL :\n{context.data['sql']}\n\n"
        f"Résultats :\n{json.dumps(rows, ensure_ascii=False, default=str)}"
    )


def analyse_sql(
    sql: str,
    prompt: str,
    *,
    conn: sqlite3.Connection | None = None,
    model_path: str | Path | None = None,
    timeout: int = 180,
) -> str:
    """Analyse une requête SELECT sur la base de La Citadelle.

    L'API du dispatcher transmet la requête SQL dans son argument `path`.
    Sans connexion fournie, la base configurée est ouverte en mode read-only.
    """
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("sql doit être une chaîne non vide.")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt doit être une chaîne non vide.")

    owns_connection = conn is None
    connection = conn if conn is not None else _connect_read_only()
    workflow = Workflow(
        [
            NodeOut("query_sql", _query_and_build_prompt),
            NodeModel(
                "model",
                "query_sql",
                "answer",
                timeout=timeout,
                model_path=str(model_path) if model_path is not None else None,
            ),
            NodeOut(
                "format",
                lambda context: context.data["answer"].strip(),
            ),
        ]
    )
    try:
        result = workflow.run(
            {"sql": sql, "prompt": prompt, "conn": connection}
        )
        return result.data["format"]
    finally:
        if owns_connection:
            connection.close()
