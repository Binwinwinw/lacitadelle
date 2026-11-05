"""Chemins de l'application, de ses ressources et des données utilisateur."""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

APP_NAME = "LaCitadelle"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_user_data_dir() -> Path:
    """Retourne l'emplacement de données standardisé pour l'OS."""
    system = platform.system()
    if system == "Windows":
        base = Path(
            os.environ.get("APPDATA")
            or Path.home() / "AppData" / "Roaming"
        )
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(
            os.environ.get("XDG_DATA_HOME")
            or Path.home() / ".local" / "share"
        )
    return base / APP_NAME


def get_app_dir() -> Path:
    """Retourne le dossier de l'exécutable ou la racine du code source."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def get_bundle_dir() -> Path:
    """Retourne la racine des ressources empaquetées ou du dépôt."""
    if is_frozen():
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if bundle_dir is not None:
            return Path(bundle_dir)
    return Path(__file__).resolve().parents[2]


def get_data_dir() -> Path:
    """Retourne et crée le dossier persistant des données utilisateur."""
    data_dir = get_user_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_assets_dir() -> Path:
    """Retourne et crée le dossier persistant des assets téléchargés."""
    assets_dir = get_data_dir() / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir
