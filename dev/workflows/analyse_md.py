"""Workflow local d'analyse d'un fichier Markdown avec retrieval FTS5."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from nodes.extract_text import extract_text
from nodes.index_fts5 import index_fts5, search_fts5
from workflow_engine import NodeModel, NodeOut, SharedContext, Workflow


def _build_prompt(context: SharedContext, top_n: int) -> str:
    """Recherche les passages demandés et les ajoute au prompt utilisateur."""
    passages = search_fts5(
        context.data["conn"],
        context.data["prompt"],
        top_n=top_n,
    )
    if not passages:
        raise ValueError("Aucun passage correspondant trouvé dans le document.")
    context.set("passages", passages)
    excerpts = "\n\n".join(
        f"[{passage['path']}]\n{passage['content']}"
        for passage in passages
    )
    return (
        "Réponds uniquement à partir des passages ci-dessous. Pour chaque nom, "
        "note ou recommandation demandé, reprends la valeur exacte si elle "
        "apparaît; n'invente pas de note ni de contrainte.\n\n"
        f"Question : {context.data['prompt']}\n\n"
        f"Passages pertinents :\n{excerpts}"
    )


def analyse_md(
    path: str | Path,
    prompt: str,
    *,
    conn: sqlite3.Connection | None = None,
    model_path: str | Path | None = None,
    top_n: int = 20,
    timeout: int = 180,
) -> str:
    """Analyse un fichier `.md` à partir des passages FTS5 et du modèle local.

    Une base SQLite en mémoire est créée par défaut et fermée à la fin de
    l'appel. Une connexion fournie par l'appelant reste sous son contrôle.
    Le retrieval prend jusqu'à 20 passages et le modèle dispose de 180 secondes
    par défaut pour répondre aux documents longs.
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
                "model_prompt",
                lambda context: _build_prompt(context, top_n),
            ),
            NodeModel(
                "model",
                "model_prompt",
                "answer",
                timeout=timeout,
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
