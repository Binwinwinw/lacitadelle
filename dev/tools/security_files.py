"""Politique de classification et d'autorisation des fichiers.

PUBLIC : lecture autorisée.
SENSITIVE : administrateur uniquement, avec journal d'audit.
CRITICAL : lecture interdite, y compris aux administrateurs.

Ce module ne lit ni ne transmet le contenu des fichiers.
"""

import logging
from pathlib import Path

logger = logging.getLogger("security.files")

PUBLIC_EXTENSIONS = {
    ".txt", ".md", ".log", ".csv", ".json", ".yaml", ".yml",
    ".pdf", ".docx", ".odt", ".xlsx", ".ods", ".pptx", ".odp",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff",
    ".py", ".js", ".html",
}

SENSITIVE_EXTENSIONS = {
    ".env", ".ini", ".conf", ".cfg", ".token", ".apikey",
    ".crt", ".cer", ".sqlite", ".db", ".zip", ".tar", ".gz",
    ".tgz", ".bz2",
}

CRITICAL_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".bat", ".cmd",
    ".sh", ".ps1", ".vbs", ".key", ".pem", ".pfx", ".p12",
    ".jks", ".credentials", ".htpasswd",
}

CRITICAL_MAGIC_BYTES = {
    b"MZ": "DOS/PE executable",
    b"\x7fELF": "ELF binary",
    b"\xca\xfe\xba\xbe": "Mach-O fat binary",
    b"\xcf\xfa\xed\xfe": "Mach-O 64-bit",
}

SENSITIVE_MAGIC_BYTES = {
    b"SQLite format 3\x00": "SQLite database",
    b"PK\x03\x04": "ZIP archive",
    b"\x1f\x8b": "GZIP archive",
    b"BZh": "BZIP2 archive",
}
PUBLIC_ARCHIVE_EXTENSIONS = {".docx", ".odt", ".xlsx", ".ods", ".pptx", ".odp"}


class FilePolicy:
    PUBLIC = "public"
    SENSITIVE = "sensitive"
    CRITICAL = "critical"


def _is_sensitive_name(name: str) -> bool:
    return name == ".env" or name.startswith(".env.") or name == ".apikey"


def classify_file(path: Path) -> str:
    """Classifie sans divulguer le contenu; les erreurs d'accès sont prudentes."""
    name = path.name.lower()
    suffix = path.suffix.lower()

    if suffix in CRITICAL_EXTENSIONS or name in CRITICAL_EXTENSIONS:
        return FilePolicy.CRITICAL

    try:
        with path.open("rb") as file:
            header = file.read(8)
    except OSError:
        return FilePolicy.SENSITIVE

    if any(header.startswith(magic) for magic in CRITICAL_MAGIC_BYTES):
        return FilePolicy.CRITICAL
    for magic in SENSITIVE_MAGIC_BYTES:
        if header.startswith(magic):
            if magic == b"PK\x03\x04" and suffix in PUBLIC_ARCHIVE_EXTENSIONS:
                break
            return FilePolicy.SENSITIVE
    if (
        _is_sensitive_name(name)
        or name in SENSITIVE_EXTENSIONS
        or suffix in SENSITIVE_EXTENSIONS
    ):
        return FilePolicy.SENSITIVE
    if suffix in PUBLIC_EXTENSIONS:
        return FilePolicy.PUBLIC
    return FilePolicy.SENSITIVE


def can_read(path: Path, user_role: str) -> tuple[bool, str]:
    """Retourne si la politique autorise le contenu à être lu."""
    level = classify_file(path)
    audit_path = str(path)

    if level == FilePolicy.CRITICAL:
        logger.warning(
            "security.files.critical_refused path=%r role=%r",
            audit_path,
            user_role,
        )
        return (
            False,
            "Fichier critique : lecture interdite (même pour un administrateur).",
        )

    if level == FilePolicy.SENSITIVE:
        if user_role != "admin":
            logger.warning(
                "security.files.sensitive_refused path=%r role=%r",
                audit_path,
                user_role,
            )
            return False, "Fichier sensible : accès réservé aux administrateurs."
        logger.info(
            "security.files.sensitive_granted path=%r role=%r",
            audit_path,
            user_role,
        )
        return True, "Accès administrateur."

    return True, "Accès public autorisé."
