#!/usr/bin/env python3
"""setup_lacitadelle : fabrique un llamafile en mode external.

Orchestre l'assemblage du runtime llamafile-thin et d'un fichier .args,
via zipalign. Le modèle GGUF reste externe au .llamafile.

Voir dev/tools/BUILD_SCRIPT_CONTRACT.md pour le contrat complet.

Usage :
    python dev/tools/setup_lacitadelle.py

Aucune dépendance externe. Python 3.10+ requis.

Note Windows : zipalign doit être copié sous le nom zipalign.exe
avant invocation. Le script gère cette copie automatiquement.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# Import des fonctions bootstrap réutilisables
from bootstrap import (
    load_config as bootstrap_load_config,
    process_asset,
    BootstrapError,
    VENDOR_DIR,
)


def detect_platform() -> str:
    """Détecte la plateforme d'exécution."""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform in ("darwin", "linux"):
        return "posix"
    else:
        return "unknown"


PLATFORM = detect_platform()

# Chemins
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
DIST_TMP_DIR = DIST_DIR / "_tmp" / "citadelle"
if PLATFORM == "windows":
    FINAL_LLAMAFILE = DIST_DIR / "lacitadelle.llamafile.exe"
else:
    FINAL_LLAMAFILE = DIST_DIR / "lacitadelle.llamafile"

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
    "-m dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf",
    "--server",
    "--port 8080",
    "-c 8192",
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
    3. Invoquer zipalign -j0 <output> <args> sans embarquer le GGUF.
    4. Vérifier que la taille finale reste inférieure à 50 Mo.
    5. Lever BuildError en cas d'échec.

    Raises:
        BuildError: si un fichier manque ou si zipalign échoue.
    """
    # Vérifier la présence de tous les fichiers d'entrée
    for label, path in [
        ("runtime", runtime_path),
        ("zipalign", zipalign_path),
        ("gguf", gguf_path),
        ("args", args_path),
    ]:
        if not path.is_file():
            raise BuildError(f"Fichier {label} manquant : {path}")

    # Créer le dossier de sortie
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Copier le runtime vers output_path (base exécutable)
    try:
        shutil.copy2(runtime_path, output_path)
    except OSError as e:
        raise BuildError(f"Impossible de copier le runtime : {e}") from e

    # Taille du runtime seul (pour vérification post-build)
    runtime_size = output_path.stat().st_size

    # Sous Windows, zipalign doit être appelé avec l'extension .exe
    zipalign_invocation = zipalign_path
    if sys.platform == "win32":
        tmp_zipalign = output_path.parent / "zipalign.exe"
        try:
            shutil.copy2(zipalign_path, tmp_zipalign)
        except OSError as e:
            raise BuildError(
                f"Impossible de copier zipalign en .exe : {e}"
            ) from e
        zipalign_invocation = tmp_zipalign

    # Le GGUF reste externe : seul le fichier .args est embarqué.
    cmd = [
        str(zipalign_invocation),
        "-j0",
        str(output_path),
        str(args_path),
    ]
    print(f"[BUILD] {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, errors="replace"
        )
    except OSError as e:
        raise BuildError(f"Impossible d'exécuter zipalign : {e}") from e

    if result.returncode != 0:
        raise BuildError(
            f"zipalign a échoué (code {result.returncode}) :\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    # Vérifier la taille finale
    if not output_path.is_file():
        raise BuildError(f"Fichier de sortie absent après zipalign : {output_path}")

    final_size = output_path.stat().st_size
    if final_size <= runtime_size:
        raise BuildError(
            f"Taille finale ({final_size}) ≤ runtime seul ({runtime_size}). "
            f"zipalign n'a probablement pas intégré les fichiers."
        )
    if final_size > 50_000_000:
        raise BuildError(
            f"Taille finale ({final_size}) supérieure à la limite du mode external "
            f"(50 000 000 octets). Le GGUF ne doit pas être embarqué."
        )

    print(f"[OK] Build terminé : {output_path} ({final_size} octets)")


def main() -> int:
    """Point d'entrée. Retourne le code de sortie."""
    # 1. Charger la config
    try:
        config = load_config()
    except BootstrapError as e:
        print(f"ERREUR [config] : {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    assets = config["assets"]

    # 2. Vérifier la présence des 3 assets requis
    required_assets = [RUNTIME_NAME, ZIPALIGN_NAME, MODEL_NAME]
    paths = {}
    for name in required_assets:
        if name not in assets:
            print(
                f"ERREUR [config] : asset '{name}' absent de la config",
                file=sys.stderr,
            )
            return EXIT_CONFIG_ERROR
        try:
            paths[name] = ensure_asset(name, assets[name])
        except BootstrapError as e:
            print(f"ERREUR [asset {name}] : {e}", file=sys.stderr)
            return EXIT_ASSET_FAILED

    runtime_path = paths[RUNTIME_NAME]
    zipalign_path = paths[ZIPALIGN_NAME]
    gguf_path = paths[MODEL_NAME]

    # 3. Préparer le dossier temporaire et le fichier .args
    DIST_TMP_DIR.mkdir(parents=True, exist_ok=True)
    args_path = DIST_TMP_DIR / ".args"
    try:
        create_args_file(args_path)
    except OSError as e:
        print(f"ERREUR [args] : {e}", file=sys.stderr)
        return EXIT_BUILD_ERROR

    # 4. Si le fichier final existe déjà, prévenir
    if FINAL_LLAMAFILE.is_file():
        print(f"overwriting existing: {FINAL_LLAMAFILE}")

    # 5. Construire dans un fichier temporaire, puis publier
    tmp_output = DIST_TMP_DIR / f"{FINAL_LLAMAFILE.name}.tmp"
    try:
        build_llamafile(
            runtime_path=runtime_path,
            zipalign_path=zipalign_path,
            gguf_path=gguf_path,
            args_path=args_path,
            output_path=tmp_output,
        )
    except BuildError as e:
        print(f"ERREUR [build] : {e}", file=sys.stderr)
        print(
            f"Fichiers temporaires conservés pour diagnostic : {DIST_TMP_DIR}",
            file=sys.stderr,
        )
        return EXIT_BUILD_ERROR

    # 6. Publier le fichier final (remplacement atomique)
    try:
        if FINAL_LLAMAFILE.is_file():
            FINAL_LLAMAFILE.unlink()
        shutil.move(str(tmp_output), str(FINAL_LLAMAFILE))
        if PLATFORM == "posix":
            os.chmod(FINAL_LLAMAFILE, 0o755)
    except OSError as e:
        print(f"ERREUR [publication] : {e}", file=sys.stderr)
        return EXIT_BUILD_ERROR

    # 7. Nettoyer le dossier temporaire (succès uniquement)
    try:
        shutil.rmtree(DIST_TMP_DIR, ignore_errors=True)
    except OSError:
        pass  # Nettoyage best-effort

    print(f"[SUCCÈS] .llamafile créé : {FINAL_LLAMAFILE}")
    print(f"Taille : {FINAL_LLAMAFILE.stat().st_size} octets")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())