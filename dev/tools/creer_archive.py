#!/usr/bin/env python3
"""Crée l'archive ZIP autonome de La Citadelle pour les utilisateurs."""

from __future__ import annotations

import os
import shutil
import stat
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARCHIVE_PATH = PROJECT_ROOT / "lacitadelle-distribution.zip"

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_ARCHIVE_SIZE = 5 * 1024 * 1024
EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".vscode",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "backup",
    "backups",
    "build",
    "citadelle_data",
    "dist",
    "release-build",
    "system-commandline-sentinel-files",
}
EXCLUDED_SUFFIXES = {
    ".dll",
    ".dylib",
    ".exe",
    ".gguf",
    ".key",
    ".llamafile",
    ".log",
    ".p12",
    ".pem",
    ".pfx",
    ".pyc",
    ".pyo",
    ".safetensors",
    ".so",
    ".zip",
}
EXCLUDED_NAMES = {
    "llamafile-linux",
    "llamafile-macos",
}
README_CONTENT = (
    "1. Extract this archive to a writable folder.\n"
    "2. Run install.bat (Windows), install.sh (Linux), or install.command (macOS).\n"
    "   Python 3.10+ and Internet are required for the first installation.\n"
    "3. Use lancer.bat, lancer.sh, or lancer.command to start La Citadelle.\n"
)
ROOT_WRAPPERS = (
    "install.bat",
    "install.sh",
    "install.command",
    "lancer.bat",
    "lancer.sh",
    "lancer.command",
)


def collect_files() -> list[tuple[Path, str]]:
    """Retourne les fichiers du paquet et leurs chemins dans l'archive."""
    files: list[tuple[Path, str]] = []

    for filename in ROOT_WRAPPERS:
        path = PROJECT_ROOT / filename
        if not path.is_file():
            raise FileNotFoundError(f"Fichier requis absent : {path}")

    for current, directories, filenames in os.walk(PROJECT_ROOT):
        directories[:] = sorted(
            name
            for name in directories
            if name not in EXCLUDED_DIRS
            and not (Path(current) / name).is_symlink()
        )
        for filename in sorted(filenames):
            path = Path(current) / filename
            if path.is_symlink() or not path.is_file():
                continue

            relative_path = path.relative_to(PROJECT_ROOT)
            suffix = path.suffix.lower()
            if (
                suffix in EXCLUDED_SUFFIXES
                or filename.lower() in EXCLUDED_NAMES
                or filename.lower().startswith(".env")
                or filename.lower().endswith("thin")
            ):
                continue
            if path.stat().st_size > MAX_FILE_SIZE:
                continue

            files.append((path, relative_path.as_posix()))

    return sorted(files, key=lambda item: item[1])


def add_file(archive: zipfile.ZipFile, path: Path, archive_name: str) -> None:
    """Ajoute un fichier en préservant les droits Unix des wrappers shell."""
    if path.suffix not in {".sh", ".command"}:
        archive.write(path, archive_name)
        return

    info = zipfile.ZipInfo.from_file(path, archive_name)
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o755) << 16
    with path.open("rb") as source, archive.open(info, "w") as destination:
        shutil.copyfileobj(source, destination)


def main() -> int:
    files = collect_files()
    with zipfile.ZipFile(
        ARCHIVE_PATH,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path, archive_name in files:
            add_file(archive, path, archive_name)
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
