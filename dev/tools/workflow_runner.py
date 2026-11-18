"""Distribue les appels vers les workflows locaux enregistrés."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

if not getattr(sys, "frozen", False):
    project_root = str(Path(__file__).resolve().parents[2])
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from dev.workflows.analyse_md import analyse_md

WorkflowFunction = Callable[[str, str], str]
WORKFLOW_REGISTRY: dict[str, WorkflowFunction] = {
    "analyse_md": analyse_md,
}


class UnknownWorkflowError(LookupError):
    """Workflow demandé absent du registre."""


def run_workflow_by_name(name: str, path: str, prompt: str) -> dict[str, object]:
    """Exécute un workflow enregistré et retourne sa réponse et ses métadonnées.

    Le résultat destiné à l'API contient toujours une réponse texte et un
    dictionnaire de métadonnées identifiant le workflow exécuté.
    """
    if not isinstance(name, str) or not name.strip():
        raise UnknownWorkflowError("Nom de workflow invalide.")
    try:
        workflow = WORKFLOW_REGISTRY[name]
    except KeyError:
        raise UnknownWorkflowError(f"Workflow inconnu : {name}") from None

    response = workflow(path, prompt)
    if not isinstance(response, str):
        raise TypeError("Un workflow doit retourner une réponse texte.")
    return {
        "response": response,
        "metadata": {"workflow": name},
    }
