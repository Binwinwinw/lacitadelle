#!/usr/bin/env python3
"""Build a one-file, platform-native La Citadelle executable."""

from __future__ import annotations

import platform
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SPEC_FILE = PROJECT_ROOT / "dev" / "tools" / "packaging" / "build.spec"
REQUIREMENTS_FILE = SPEC_FILE.with_name("requirements.txt")
OUTPUT_DIR = PROJECT_ROOT / "dist" / "release"


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(REQUIREMENTS_FILE),
            ],
            check=True,
        )


def main() -> int:
    system = platform.system()
    if system not in {"Windows", "Linux", "Darwin"}:
        print(f"ERREUR : système non pris en charge pour le build : {system}")
        return 1

    ensure_pyinstaller()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lacitadelle-pyinstaller-") as work_dir:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                str(SPEC_FILE),
                "--distpath",
                str(OUTPUT_DIR),
                "--workpath",
                work_dir,
                "--noconfirm",
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )

    executable = OUTPUT_DIR / (
        "LaCitadelle.exe" if system == "Windows" else "LaCitadelle"
    )
    if not executable.is_file():
        print(f"ERREUR : exécutable attendu absent : {executable}")
        return 1

    print(
        f"OK : {executable} "
        f"({executable.stat().st_size / (1024 * 1024):.1f} Mo)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
