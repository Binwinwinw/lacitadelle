"""Extraction de texte depuis les documents publics pris en charge."""

from __future__ import annotations

from pathlib import Path

from security_files import can_read


class ExtractTextError(ValueError):
    """Erreur d'extraction ou de format de document."""


def extract_text(path: str | Path) -> str:
    """Extrait le texte brut d'un fichier Markdown, TXT ou PDF.

    Les fichiers sont vérifiés par la politique de sécurité existante. PDF est
    pris en charge uniquement si `pypdf` est déjà disponible localement.
    """
    source = Path(path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {source}")

    allowed, reason = can_read(source, "user")
    if not allowed:
        raise PermissionError(reason)

    suffix = source.suffix.lower()
    if suffix in {".md", ".txt"}:
        try:
            return source.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ExtractTextError(
                f"Le fichier n'est pas encodé en UTF-8 : {source}"
            ) from exc
    if suffix != ".pdf":
        raise ExtractTextError(
            f"Format non supporté : {suffix or '(sans extension)'}"
        )

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ExtractTextError("PDF non supporté (pypdf absent)") from exc

    reader = PdfReader(str(source))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
