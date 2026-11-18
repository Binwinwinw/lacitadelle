"""Workflow local d'analyse d'un fichier Markdown avec retrieval FTS5."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from nodes.extract_text import extract_text
from nodes.index_fts5 import index_fts5, search_fts5
from workflow_engine import NodeModel, NodeOut, SharedContext, Workflow


def _build_prompt(context: SharedContext) -> str:
    """Ajoute les passages retrouvés à la question de l'utilisateur."""
    passages = context.data["passages"]
    if not passages:
        raise ValueError("Aucun passage correspondant trouvé dans le document.")
    excerpts = "\n\n".join(
        f"[{passage['path']}]\n{passage['content']}"
        for passage in passages
    )
    return f"{context.data['prompt']}\n\nPassages pertinents :\n{excerpts}"


def analyse_md(
    path: str | Path,
    prompt: str,
    *,
    conn: sqlite3.Connection | None = None,
    model_path: str | Path | None = None,
) -> str:
    """Analyse un fichier `.md` à partir des passages FTS5 et du modèle local.

    Une base SQLite en mémoire est créée par défaut et fermée à la fin de
    l'appel. Une connexion fournie par l'appelant reste sous son contrôle.
    """
    source = Path(path)
    if source.suffix.lower() != ".md":
        raise ValueError("Le workflow analyse_md exige un fichier .md.")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt doit être une chaîne non vide.")

    owns_connection = conn is None
    connection = conn or sqlite3.connect(":memory:")
    workflow = Workflow(
        [
            NodeOut(
                "text",
                lambda context: extract_text(context.data["path"]),
            ),
            NodeOut(
                "indexed_chunks",
                lambda context: index_fts5(
                    context.data["conn"],
                    context.data["path"],
                    context.data["text"],
                ),
            ),
            NodeOut(
                "passages",
                lambda context: search_fts5(
                    context.data["conn"],
                    context.data["prompt"],
                ),
            ),
            NodeModel(
                "answer",
                _build_prompt,
                model_path=str(model_path) if model_path is not None else None,
            ),
        ]
    )
    try:
        result = workflow.run(
            {"path": str(source), "prompt": prompt, "conn": connection}
        )
        return result.data["answer"]
    finally:
        if owns_connection:
            connection.close()
