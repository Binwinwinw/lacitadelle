# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller one-file configuration for La Citadelle."""

from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parents[2]
TOOLS_DIR = PROJECT_ROOT / "dev" / "tools"

analysis = Analysis(
    [str(TOOLS_DIR / "lancer.py")],
    pathex=[str(TOOLS_DIR)],
    binaries=[],
    datas=[
        (str(TOOLS_DIR / "prompts"), "dev/tools/prompts"),
        (str(TOOLS_DIR / "web"), "dev/tools/web"),
        (str(TOOLS_DIR / "llamafile_config.json"), "dev/tools"),
    ],
    hiddenimports=[
        "bootstrap",
        "citadelle_memory",
        "login_server",
        "model_health",
        "paths",
        "security_files",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "pytest"],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="LaCitadelle",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
