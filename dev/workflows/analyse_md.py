"""Workflow local d'analyse Markdown, en contexte complet ou via FTS5."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from nodes.extract_text import extract_text
from nodes.index_fts5 import index_fts5, search_fts5
from workflow_engine import NodeModel, NodeOut, SharedContext, Workflow


def _build_prompt(prompt: str, content: str, source_label: str) -> str:
    """Construit le prompt à partir du document ou des passages récupérés."""
    return (
        "Réponds uniquement à partir du contenu ci-dessous. Pour chaque nom, "
        "note ou recommandation demandé, reprends la valeur exacte si elle "
        "apparaît; n'invente pas de note ni de contrainte.\n\n"
        f"Question : {prompt}\n\n{source_label} :\n{content}"
    )


def _build_retrieval_prompt(context: SharedContext, top_n: int) -> str:
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
    return _build_prompt(
        context.data["prompt"],
        excerpts,
        "Passages pertinents",
    )


def analyse_md(
    path: str | Path,
    prompt: str,
    *,
    conn: sqlite3.Connection | None = None,
    model_path: str | Path | None = None,
    top_n: int = 20,
    timeout: int = 180,
    use_retrieval: bool = False,
) -> str:
    """Analyse un fichier `.md` avec le document complet ou le retrieval FTS5.

    Une base SQLite en mémoire est créée par défaut et fermée à la fin de
    l'appel. Une connexion fournie par l'appelant reste sous son contrôle.
    Le document complet est envoyé par défaut; pour un document de plus de
    200 000 caractères, passer `use_retrieval=True` pour limiter le contexte
    aux `top_n` passages FTS5.
    """
    source = Path(path)
    if source.suffix.lower() != ".md":
        raise ValueError("Le workflow analyse_md exige un fichier .md.")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt doit être une chaîne non vide.")
    if not isinstance(use_retrieval, bool):
        raise TypeError("use_retrieval doit être un booléen.")

    owns_connection = conn is None
    connection = conn or sqlite3.connect(":memory:")
    nodes = [
        NodeOut(
            "read_full_document",
            lambda context: extract_text(context.data["path"]),
        )
    ]
    if use_retrieval:
        nodes.extend(
            [
                NodeOut(
                    "indexed_chunks",
                    lambda context: index_fts5(
                        context.data["conn"],
                        context.data["path"],
                        context.data["read_full_document"],
                    ),
                ),
                NodeOut(
                    "model_prompt",
                    lambda context: _build_retrieval_prompt(context, top_n),
                ),
            ]
        )
    else:
        nodes.append(
            NodeOut(
                "model_prompt",
                lambda context: _build_prompt(
                    context.data["prompt"],
                    context.data["read_full_document"],
                    "Document complet",
                ),
            )
        )
    nodes.append(
        NodeModel(
            "model",
            "model_prompt",
            "answer",
            timeout=timeout,
            model_path=str(model_path) if model_path is not None else None,
        )
    )
    workflow = Workflow(nodes)
    try:
        result = workflow.run(
            {"path": str(source), "prompt": prompt, "conn": connection}
        )
        return result.data["answer"]
    finally:
        if owns_connection:
            connection.close()
