"""Distribue les appels vers les workflows locaux enregistrés."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path

from paths import get_bundle_dir
from security_files import can_read

if not getattr(sys, "frozen", False):
    project_root = str(Path(__file__).resolve().parents[2])
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from dev.workflows.analyse_md import analyse_md
from dev.workflows.analyse_pdf import analyse_pdf
from dev.workflows.analyse_sql import analyse_sql

WorkflowFunction = Callable[[str, str], str]
WORKFLOW_REGISTRY: dict[str, WorkflowFunction] = {
    "analyse_md": analyse_md,
    "analyse_pdf": analyse_pdf,
    "analyse_sql": analyse_sql,
}
_WORKFLOW_EXTENSIONS = {
    "analyse_md": ".md",
    "analyse_pdf": ".pdf",
    "analyse_sql": ".sql",
}
_ALLOWED_WORKFLOW_DIRECTORIES = (
    Path("dev/docs"),
    Path("dev/tests"),
    Path("dev/tools"),
    Path("dev/workflows"),
)


class UnknownWorkflowError(LookupError):
    """Workflow demandé absent du registre."""


class WorkflowPathError(ValueError):
    """Chemin de document invalide ou non autorisé."""


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def _resolve_workflow_path(path: str, workflow_name: str) -> Path:
    """Résout un fichier du projet et refuse tout chemin hors périmètre."""
    if not isinstance(path, str) or not path.strip():
        raise WorkflowPathError("Chemin non autorisé")

    try:
        bundle_dir = get_bundle_dir().resolve(strict=True)
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = bundle_dir / candidate
        candidate = Path(os.path.abspath(candidate))
    except (OSError, RuntimeError, ValueError):
        raise WorkflowPathError("Chemin non autorisé") from None

    if not any(
        _is_within(candidate, bundle_dir / relative_directory)
        for relative_directory in _ALLOWED_WORKFLOW_DIRECTORIES
    ):
        raise WorkflowPathError("Chemin non autorisé")

    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        raise WorkflowPathError("Chemin non autorisé") from None

    if not resolved.is_file():
        raise WorkflowPathError("Chemin non autorisé")

    allowed = False
    for relative_directory in _ALLOWED_WORKFLOW_DIRECTORIES:
        try:
            allowed_directory = (bundle_dir / relative_directory).resolve(
                strict=True
            )
        except (OSError, RuntimeError):
            continue
        if (
            _is_within(allowed_directory, bundle_dir)
            and _is_within(resolved, allowed_directory)
        ):
            allowed = True
            break
    if not allowed or resolved.suffix.lower() != _WORKFLOW_EXTENSIONS[workflow_name]:
        raise WorkflowPathError("Chemin non autorisé")
    return resolved


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

    source_path = _resolve_workflow_path(path, name)
    workflow_input = str(source_path)
    if name == "analyse_sql":
        allowed, _ = can_read(source_path, "admin")
        if not allowed:
            raise WorkflowPathError("Chemin non autorisé")
        try:
            workflow_input = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            raise WorkflowPathError("Chemin non autorisé") from None

    response = workflow(workflow_input, prompt)
    if not isinstance(response, str):
        raise TypeError("Un workflow doit retourner une réponse texte.")
    return {
        "response": response,
        "metadata": {"workflow": name},
    }
