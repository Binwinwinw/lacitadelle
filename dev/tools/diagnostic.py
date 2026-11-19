"""GPU, runtime and recent-log diagnostics for the local application."""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from citadelle_memory import DB_PATH, get_setting
from paths import get_bundle_dir, get_user_data_dir, is_frozen

LOG_SOURCES = frozenset({"llama", "login", "app"})
_SENSITIVE_LOG_PATTERN = re.compile(
    r"token|password|passwd|secret|bearer|authorization|mot\s+de\s+passe",
    re.IGNORECASE,
)


def _log_path(source: str) -> Path:
    if source == "llama":
        if is_frozen():
            return get_user_data_dir() / "proxy.log"
        return get_bundle_dir() / "dist" / "proxy.log"
    if source in {"login", "app"}:
        return DB_PATH.parent / f"{source}.log"
    raise ValueError("Source de log invalide.")


def _read_tail(path: Path, lines: int) -> list[str]:
    """Lit les dernières lignes en remontant depuis la fin du fichier."""
    blocks = []
    newline_count = 0
    with path.open("rb") as log_file:
        position = log_file.seek(0, 2)
        while position > 0 and newline_count <= lines:
            block_size = min(4096, position)
            position -= block_size
            log_file.seek(position)
            block = log_file.read(block_size)
            blocks.append(block)
            newline_count += block.count(b"\n")

    content = b"".join(reversed(blocks))
    return [
        line.decode("utf-8", errors="replace")
        for line in content.splitlines()[-lines:]
    ]


def get_recent_logs(source: str, lines: int = 100) -> list[str]:
    """Retourne les dernières lignes autorisées après masquage des secrets."""
    if not isinstance(source, str) or source not in LOG_SOURCES:
        raise ValueError("Source de log invalide.")
    if isinstance(lines, bool) or not isinstance(lines, int) or not 1 <= lines <= 1000:
        raise ValueError("lines doit être compris entre 1 et 1000.")

    try:
        recent_lines = _read_tail(_log_path(source), lines)
    except FileNotFoundError:
        return []
    return [
        "[REDACTED]" if _SENSITIVE_LOG_PATTERN.search(line) else line
        for line in recent_lines
    ]


def get_gpu_status() -> dict[str, object]:
    """Retourne les GPU NVIDIA détectés par `nvidia-smi`."""
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return {"available": False, "reason": "nvidia-smi absent"}

    command = [
        executable,
        "--query-gpu=name,memory.used,memory.total,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError("Impossible d'exécuter nvidia-smi.") from exc
    if result.returncode != 0:
        raise RuntimeError(f"nvidia-smi a échoué ({result.returncode}).")

    gpus: list[dict[str, object]] = []
    for row in csv.reader(io.StringIO(result.stdout), skipinitialspace=True):
        if not row:
            continue
        if len(row) != 4:
            raise RuntimeError("Sortie nvidia-smi invalide.")
        name, used, total, utilization = (field.strip() for field in row)
        try:
            gpu = {
                "name": name,
                "vram_used_mb": int(float(used)),
                "vram_total_mb": int(float(total)),
                "utilization_pct": int(float(utilization)),
            }
        except ValueError as exc:
            raise RuntimeError("Valeurs GPU nvidia-smi invalides.") from exc
        gpus.append(gpu)

    if not gpus:
        return {"available": False, "reason": "aucun GPU détecté"}
    return {"available": True, "gpus": gpus}


def get_llama_gpu_layers() -> dict[str, int | bool | str | None]:
    """Retourne le dernier compteur de couches llama.cpp offloadées sur GPU."""
    pattern = re.compile(r"offloaded\s+(\d+)/(\d+)\s+layers to GPU", re.I)
    for line in reversed(get_recent_logs("llama", lines=1000)):
        match = pattern.search(line)
        if match is None:
            continue
        offloaded, total = (int(value) for value in match.groups())
        return {
            "offloaded": offloaded,
            "total": total,
            "on_gpu": offloaded > 0 and offloaded == total,
            "raw_line": line,
        }
    return {
        "offloaded": None,
        "total": None,
        "on_gpu": None,
        "raw_line": None,
    }


def _get_runtime_uptime() -> int | None:
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8080/v1/models",
            timeout=1,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (
        OSError,
        TimeoutError,
        urllib.error.URLError,
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return None

    models = payload.get("data") if isinstance(payload, dict) else None
    created = models[0].get("created") if isinstance(models, list) and models else None
    if isinstance(created, bool) or not isinstance(created, (int, float)):
        return None
    return max(0, int(time.time() - created))


def get_runtime_status() -> dict[str, object]:
    """Retourne l'état du port llamafile, le modèle configuré et son uptime."""
    try:
        with socket.create_connection(("127.0.0.1", 8080), timeout=0.5):
            port_open = True
    except OSError:
        port_open = False

    current_model = get_setting("current_model_path", db_path=DB_PATH)
    return {
        "port_8080_open": port_open,
        "current_model": current_model or "",
        "uptime_seconds": _get_runtime_uptime() if port_open else None,
    }
