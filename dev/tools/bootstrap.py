#!/usr/bin/env python3
"""Bootstrap : télécharge et vérifie les binaires llamafile.

Lit dev/tools/llamafile_config.json, télécharge les assets marqués
required=true, vérifie leur SHA-256, les stocke dans
dev/tools/vendor/llamafile/. Échoue proprement en cas d'erreur.

Usage :
    python dev/tools/bootstrap.py

Aucune dépendance externe. Python 3.10+ recommandé.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Chemins (relatifs à la racine du projet, calculés depuis ce fichier)
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent.parent
CONFIG_PATH = TOOLS_DIR / "llamafile_config.json"
VENDOR_DIR = TOOLS_DIR / "vendor" / "llamafile"

# Taille de bloc pour le calcul du SHA-256 en streaming
CHUNK_SIZE = 64 * 1024


def load_config() -> dict:
    """Charge et valide la configuration JSON."""
    # TODO (étape suivante) — implémentation
    pass


def compute_sha256(path: Path) -> str:
    """Calcule le SHA-256 d'un fichier en streaming."""
    # TODO (étape suivante) — implémentation
    pass


def download(url: str, dest: Path) -> None:
    """Télécharge url vers dest. Échoue proprement si erreur."""
    # TODO (étape suivante) — implémentation
    pass


def verify_sha256(path: Path, expected: str) -> None:
    """Vérifie le SHA-256 d'un fichier. Échoue si mismatch."""
    # TODO (étape suivante) — implémentation
    pass


def process_asset(name: str, meta: dict) -> None:
    """Traite un asset : télécharge si absent, vérifie le checksum."""
    # TODO (étape suivante) — implémentation
    pass


def main() -> int:
    """Point d'entrée. Retourne 0 si succès, non-zéro si échec."""
    # TODO (étape suivante) — implémentation
    return 1


if __name__ == "__main__":
    sys.exit(main())