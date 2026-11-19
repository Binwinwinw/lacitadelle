"""Workflow d'analyse PDF avec retrieval local SQLite FTS5."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from nodes.extract_pdf import extract_pdf
from nodes.index_fts5 import index_fts5, search_fts5
from workflow_engine import NodeModel, NodeOut, SharedContext, Workflow


def _build_prompt(context: SharedContext, top_n: int) -> str:
    """Recherche les passages PDF et les ajoute au prompt utilisateur."""
    passages = search_fts5(
        context.data["conn"],
        context.data["prompt"],
        top_n=top_n,
    )
    if not passages:
        raise ValueError("Aucun passage correspondant trouvé dans le PDF.")
    context.set("passages", passages)
    excerpts = "\n\n".join(
        f"[{passage['path']}]\n{passage['content']}"
        for passage in passages
    )
    return (
        "Réponds uniquement à partir des passages ci-dessous. "
        "Reprends exactement les valeurs qu'ils contiennent.\n\n"
        f"Question : {context.data['prompt']}\n\n"
        f"Passages pertinents :\n{excerpts}"
    )


def analyse_pdf(
    path: str | Path,
    prompt: str,
    *,
    conn: sqlite3.Connection | None = None,
    model_path: str | Path | None = None,
    top_n: int = 20,
    timeout: int = 180,
) -> str:
    """Extrait, indexe et analyse un PDF avec le modèle local.

    Une connexion FTS5 en mémoire est créée par défaut. Si pypdf n'est pas
    installé, le nœud d'extraction signale explicitement que le PDF n'est pas
    pris en charge.
    """
    source = Path(path)
    if source.suffix.lower() != ".pdf":
        raise ValueError("Le workflow analyse_pdf exige un fichier .pdf.")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt doit être une chaîne non vide.")

    owns_connection = conn is None
    connection = conn if conn is not None else sqlite3.connect(":memory:")
    workflow = Workflow(
        [
            NodeOut(
                "text",
                lambda context: extract_pdf(context.data["path"]),
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
