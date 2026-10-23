#!/usr/bin/env python3
"""Crée l'archive ZIP autonome de La Citadelle pour les utilisateurs."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEV_DIR = PROJECT_ROOT / "dev"
ARCHIVE_PATH = PROJECT_ROOT / "lacitadelle-distribution.zip"

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_ARCHIVE_SIZE = 5 * 1024 * 1024
EXCLUDED_DIRS = {
    ".git",
    ".github",
    ".idea",
    ".memory",
    ".pytest_cache",
    ".vscode",
    "__pycache__",
}
EXCLUDED_SUFFIXES = {".exe", ".gguf", ".pyc", ".pyo"}
README_CONTENT = (
    "1. Extrayez cette archive dans un dossier accessible en ecriture.\n"
    "2. Lancez install.bat (Python et Internet requis au premier lancement).\n"
    "3. Lancez lancer.bat pour demarrer La Citadelle.\n"
)


def collect_files() -> list[tuple[Path, str]]:
    """Retourne les fichiers du paquet et leurs chemins dans l'archive."""
    files: list[tuple[Path, str]] = []

    for filename in ("install.bat", "lancer.bat"):
        path = PROJECT_ROOT / filename
        if not path.is_file():
            raise FileNotFoundError(f"Fichier requis absent : {path}")
        files.append((path, filename))

    for current, directories, filenames in os.walk(DEV_DIR):
        directories[:] = sorted(
            name for name in directories if name not in EXCLUDED_DIRS
        )
        for filename in sorted(filenames):
            path = Path(current) / filename
            if path.is_symlink() or not path.is_file():
                continue

            relative_path = path.relative_to(PROJECT_ROOT)
            suffix = path.suffix.lower()
            if suffix in EXCLUDED_SUFFIXES:
                continue
            if path.stat().st_size > MAX_FILE_SIZE:
                continue

            files.append((path, relative_path.as_posix()))

    return sorted(files, key=lambda item: item[1])


def main() -> int:
    files = collect_files()
    with zipfile.ZipFile(
        ARCHIVE_PATH,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path, archive_name in files:
            archive.write(path, archive_name)
        archive.writestr("LISEZMOI.txt", README_CONTENT)

    archive_size = ARCHIVE_PATH.stat().st_size
    if archive_size >= MAX_ARCHIVE_SIZE:
        ARCHIVE_PATH.unlink()
        raise SystemExit(
            f"ERREUR : archive trop volumineuse ({archive_size} octets; "
            f"limite {MAX_ARCHIVE_SIZE} octets)."
        )

    print(
        f"Archive creee : {ARCHIVE_PATH.name} "
        f"({len(files) + 1} fichiers, {archive_size} octets)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
