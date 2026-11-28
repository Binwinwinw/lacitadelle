"""Extraction de texte depuis les documents publics pris en charge."""

from __future__ import annotations

from pathlib import Path

from security_files import can_read, classify_file

CHAT_DOCUMENT_EXTENSIONS = {".md", ".txt", ".sql"}
MAX_MARKDOWN_BYTES = 256 * 1024
MAX_MARKDOWN_CHARS = 200_000


class ExtractTextError(ValueError):
    """Erreur d'extraction ou de format de document."""


class DocumentLimitError(ExtractTextError):
    """Un document dépasse une limite d'import."""


def extract_markdown_document(
    path: str | Path,
    user_role: str,
) -> tuple[str, dict[str, str | int]]:
    """Lit un document téléversé après contrôle des limites et des droits."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {source}")
    suffix = source.suffix.lower()
    if suffix not in CHAT_DOCUMENT_EXTENSIONS:
        raise ExtractTextError(
            "Seuls les fichiers .md, .txt et .sql sont pris en charge."
        )

    size_bytes = source.stat().st_size
    if size_bytes > MAX_MARKDOWN_BYTES:
        raise DocumentLimitError("Le fichier dépasse la limite de 256 KiB.")

    classification = classify_file(source)
    allowed, reason = can_read(source, user_role)
    if not allowed:
        raise PermissionError(reason)

    try:
        content = source.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        message = (
            "Le fichier Markdown doit être encodé en UTF-8."
            if suffix == ".md"
            else "Le fichier doit être encodé en UTF-8."
        )
        raise ExtractTextError(message) from exc
    if not content.strip() or "\x00" in content:
        raise ExtractTextError("Le fichier est vide ou contient des données binaires.")
    if len(content) > MAX_MARKDOWN_CHARS:
        raise DocumentLimitError("Le document dépasse 200 000 caractères.")

    return content, {
        "file_name": source.name,
        "classification": classification,
        "size_bytes": size_bytes,
        "characters": len(content),
    }


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
