#!/usr/bin/env python3
"""Bootstrap : télécharge et vérifie les binaires llamafile.

Lit dev/tools/llamafile_config.json, télécharge les assets marqués
required=true, vérifie leur SHA-256, les stocke dans
dev/tools/vendor/llamafile/. Échoue proprement en cas d'erreur.

Voir dev/tools/BOOTSTRAP_CONTRACT.md pour le contrat complet.

Usage :
    python dev/tools/bootstrap.py

Aucune dépendance externe. Python 3.10+ requis.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# Chemins (relatifs au fichier, pas au cwd)
TOOLS_DIR = Path(__file__).resolve().parent
CONFIG_PATH = TOOLS_DIR / "llamafile_config.json"
VENDOR_DIR = TOOLS_DIR / "vendor" / "llamafile"

# Paramètres
CHUNK_SIZE = 64 * 1024
HTTP_TIMEOUT = 60
SHA256_LEN = 64

# Codes de sortie
EXIT_OK = 0
EXIT_ASSET_FAILED = 1
EXIT_CONFIG_ERROR = 2


class BootstrapError(Exception):
    """Erreur attendue du bootstrap (config, réseau, checksum).

    Les BootstrapError sont signalées à l'utilisateur sans traceback.
    Les autres exceptions indiquent un bug de programmation.
    """


def load_config() -> dict[str, Any]:
    """Charge et valide la configuration JSON.

    Voir BOOTSTRAP_CONTRACT.md, section « Contrat de la configuration ».

    Raises:
        BootstrapError: si le fichier est absent, invalide, ou viole le schéma.
    """
    raise NotImplementedError("load_config à implémenter")


def compute_sha256(path: Path) -> str:
    """Calcule le SHA-256 d'un fichier en streaming.

    Retourne la représentation hexadécimale en minuscules.
    Compatible Python 3.10 (pas de hashlib.file_digest).
    """
    raise NotImplementedError("compute_sha256 à implémenter")


def verify_sha256(path: Path, expected: str) -> None:
    """Vérifie le SHA-256 d'un fichier.

    Raises:
        BootstrapError: si le checksum ne correspond pas.
    """
    raise NotImplementedError("verify_sha256 à implémenter")


def download(url: str, dest: Path) -> None:
    """Télécharge `url` vers `dest` en streaming.

    Écrit vers le chemin exact fourni (le caller est responsable du
    temporaire et de la publication atomique).

    Raises:
        BootstrapError: sur HTTPError, URLError, ou timeout.
    """
    raise NotImplementedError("download à implémenter")


def process_asset(name: str, meta: dict[str, Any]) -> None:
    """Traite un asset : télécharge si absent, vérifie le checksum.

    Cycle :
      1. Fichier final présent + checksum OK → rien à faire.
      2. Fichier final présent + checksum KO → BootstrapError.
      3. Fichier final absent → télécharger vers temporaire,
         vérifier, publier atomiquement.

    Raises:
        BootstrapError: sur tout échec.
    """
    raise NotImplementedError("process_asset à implémenter")


def main() -> int:
    """Point d'entrée. Retourne le code de sortie."""
    raise NotImplementedError("main à implémenter")


if __name__ == "__main__":
    sys.exit(main())