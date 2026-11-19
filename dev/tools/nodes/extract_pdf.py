"""Extraction de texte depuis un fichier PDF public avec pypdf local."""

from __future__ import annotations

from pathlib import Path

from security_files import can_read


def extract_pdf(path: str | Path) -> str:
    """Extrait et joint le texte des pages d'un PDF.

    Le fichier est vérifié par la politique existante avant lecture. Aucune
    dépendance n'est téléchargée : si pypdf est absent, une erreur explicite
    est levée.
    """
    source = Path(path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {source}")
    if source.suffix.lower() != ".pdf":
        raise ValueError("Format PDF attendu.")

    allowed, reason = can_read(source, "user")
    if not allowed:
        raise PermissionError(reason)

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ImportError(
            "pypdf non installé, PDF non supporté"
        ) from exc

    reader = PdfReader(str(source))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
