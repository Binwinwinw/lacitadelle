#!/usr/bin/env python3
"""Installateur multiplateforme de La Citadelle."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = PROJECT_ROOT / "dev" / "tools"
SUPPORTED_SYSTEMS = ("Windows", "Linux", "Darwin")

sys.path.insert(0, str(TOOLS_DIR))
import bootstrap


def get_os_key() -> str:
    """Retourne l'OS pris en charge ou signale une erreur explicite."""
    system = platform.system()
    if system not in SUPPORTED_SYSTEMS:
        raise RuntimeError(f"OS non supporté : {system}")
    return system


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    try:
        system = get_os_key()
    except RuntimeError as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 1

    result = bootstrap.main(system=system)
    if result != 0:
        return result

    print("Installation terminée. Lancement de La Citadelle...")
    command = [
        sys.executable,
        str(TOOLS_DIR / "lancer.py"),
        *sys.argv[1:],
    ]
    try:
        return subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
        ).returncode
    except OSError as exc:
        print(f"ERREUR : impossible de lancer La Citadelle : {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
