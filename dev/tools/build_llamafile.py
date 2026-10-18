#!/usr/bin/env python3
"""build_llamafile : fabrique un fichier .llamafile autonome.

Orchestre l'assemblage du runtime llamafile-thin, du modèle GGUF
Qwen3-1.7B Q4_K_M et d'un fichier .args, via zipalign.

Voir dev/tools/BUILD_SCRIPT_CONTRACT.md pour le contrat complet.

Usage :
    python dev/tools/build_llamafile.py

Aucune dépendance externe. Python 3.10+ requis.

Note Windows : zipalign doit être copié sous le nom zipalign.exe
avant invocation. Le script gère cette copie automatiquement.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# Import des fonctions bootstrap réutilisables
from bootstrap import (
    load_config as bootstrap_load_config,
    process_asset,
    BootstrapError,
    VENDOR_DIR,
)

# Chemins
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
DIST_TMP_DIR = DIST_DIR / "_tmp" / "citadelle"
FINAL_LLAMAFILE = DIST_DIR / "citadelle.llamafile"

# Noms d'assets attendus
RUNTIME_NAME = "llamafile-thin"
ZIPALIGN_NAME = "zipalign"
MODEL_NAME = "qwen3-1.7b-q4km"

# Codes de sortie
EXIT_OK = 0
EXIT_ASSET_FAILED = 1
EXIT_CONFIG_ERROR = 2
EXIT_BUILD_ERROR = 3

# Paramètres du .args (contenu acté dans BUILD_LLAMAFILE.md)
ARGS_CONTENT = [
    "-m /zip/Qwen3-1.7B-Q4_K_M.gguf",
    "--port 8080",
    "-c 4096",
    "--temp 0.7",
    "-t 4",
]


class BuildError(Exception):
    """Erreur attendue du build (asset manquant, zipalign échoué, etc.).

    Les BuildError sont signalées à l'utilisateur sans traceback.
    """


def load_config() -> dict[str, Any]:
    """Charge la config via bootstrap.load_config. Délègue, pas de duplication."""
    return bootstrap_load_config()


def ensure_asset(name: str, meta: dict[str, Any]) -> Path:
    """Vérifie que l'asset est présent, le télécharge si absent.

    Délègue à bootstrap.process_asset (pas de duplication de la logique
    de téléchargement/réparation/checksum).

    Returns:
        Le chemin du fichier dans VENDOR_DIR.
    """
    process_asset(name, meta)
    return VENDOR_DIR / meta["filename"]


def create_args_file(output_path: Path) -> None:
    """Crée le fichier .args avec le contenu acté.

    Le fichier DOIT s'appeler exactement .args (nom de base préservé
    dans l'archive zipalign).

    Args:
        output_path: chemin exact où écrire le fichier .args. Le caller
            décide de l'emplacement.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(ARGS_CONTENT) + "\n"
    output_path.write_text(content, encoding="utf-8")


def build_llamafile(
    runtime_path: Path,
    zipalign_path: Path,
    gguf_path: Path,
    args_path: Path,
    output_path: Path,
) -> None:
    """Assemble le .llamafile final via zipalign.

    Responsabilités :
      1. Copier le runtime vers output_path (base exécutable).
      2. Copier zipalign_path vers un zipalign.exe temporaire si Windows.
      3. Invoquer zipalign -j0 <output> <gguf> <args>.
      4. Vérifier que output_path existe et a une taille > runtime seul.
      5. Lever BuildError en cas d'échec.

    Raises:
        BuildError: si un fichier manque ou si zipalign échoue.
    """
    raise NotImplementedError("build_llamafile à implémenter (tâche suivante)")


def main() -> int:
    """Point d'entrée. Retourne le code de sortie."""
    raise NotImplementedError("main à implémenter (tâche suivante)")


if __name__ == "__main__":
    sys.exit(main())