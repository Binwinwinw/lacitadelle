#!/usr/bin/env python3
"""Lanceur unifié multiplateforme."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from contextlib import redirect_stderr
from pathlib import Path
from queue import Empty, Queue

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = PROJECT_ROOT / "dev" / "tools"
RUNTIME_OPTIONS = (
    "--server",
    "--host",
    "127.0.0.1",
    "--port",
    "8080",
    "--nologo",
    "--log-timestamps",
    "--cors-origins",
    "http://localhost:8081",
)
MODEL_HEALTH_SCRIPT = TOOLS_DIR / "model_health.py"
PROXY_SCRIPT = TOOLS_DIR / "login_server.py"
CURRENT_MODEL_FILE = PROJECT_ROOT / "dist" / ".current_model"
PROXY_LOG = PROJECT_ROOT / "dist" / "proxy.log"
DEFAULT_MODEL = (
    Path("dev")
    / "tools"
    / "vendor"
    / "llamafile"
    / "Qwen3-1.7B-Q4_K_M.gguf"
)
RUNTIME_URL = "http://127.0.0.1:8080/v1/models"
PROXY_URL = "http://127.0.0.1:8081/login"
APP_URL = "http://localhost:8081"

sys.path.insert(0, str(TOOLS_DIR))
import model_health


class LauncherError(Exception):
    """Erreur de démarrage présentable à l'utilisateur."""


def get_runtime_binary() -> Path:
    system = platform.system()
    if system == "Windows":
        return PROJECT_ROOT / "dist" / "llamafile.exe"
    if system == "Linux":
        return PROJECT_ROOT / "dist" / "llamafile-linux"
    if system == "Darwin":
        return PROJECT_ROOT / "dist" / "llamafile-macos"
    raise RuntimeError(f"OS non supporté : {system}")


def _run_model_health(args: list[str], proxy_log: Path | None = None) -> int:
    if proxy_log is None:
        return model_health.main(args)
    with proxy_log.open("a", encoding="utf-8") as log_file:
        with redirect_stderr(log_file):
            return model_health.main(args)


def _read_current_model() -> Path | None:
    try:
        value = CURRENT_MODEL_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _default_model(*, check_whitelist: bool, proxy_log: Path) -> Path:
    model_path = PROJECT_ROOT / DEFAULT_MODEL
    if not model_path.is_file():
        raise LauncherError(f"Le modèle par défaut est introuvable : {model_path}")
    if check_whitelist and _run_model_health(
        ["--check-whitelist", str(model_path)],
        proxy_log,
    ) != 0:
        raise LauncherError("Le modèle par défaut n'est pas dans la whitelist.")
    print(f"Utilisation du modèle par défaut : {model_path}")
    return model_path


def select_model_path(proxy_log: Path = PROXY_LOG) -> Path:
    state = _run_model_health(["--has-current-model"], proxy_log)
    if state == 2:
        raise LauncherError("Impossible de lire l'état du modèle configuré.")
    if state == 1:
        return _default_model(check_whitelist=False, proxy_log=proxy_log)
    if state != 0:
        raise LauncherError(f"État du modèle inattendu : code {state}.")

    model_path = _read_current_model()
    if (
        model_path is not None
        and model_path.is_file()
        and _run_model_health(
            ["--check-whitelist", str(model_path)],
            proxy_log,
        ) == 0
    ):
        return model_path

    print("Modèle configuré invalide ou non autorisé; tentative de rollback...")
    rollback_status = _run_model_health(["--rollback"], proxy_log)
    if rollback_status == 0:
        model_path = _read_current_model()
        if (
            model_path is not None
            and model_path.is_file()
            and _run_model_health(
                ["--check-whitelist", str(model_path)],
                proxy_log,
            ) == 0
        ):
            print(f"Modèle restauré : {model_path}")
            return model_path

    return _default_model(check_whitelist=True, proxy_log=proxy_log)


def _endpoint_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return getattr(response, "status", 200) == 200
    except (OSError, TimeoutError, urllib.error.URLError):
        return False


def _forward_proxy_output(
    stream,
    output_queue: Queue[str | None],
) -> None:
    for line in stream:
        output_queue.put(line)
    output_queue.put(None)


def _drain_proxy_output(output_queue: Queue[str | None]) -> None:
    while True:
        try:
            line = output_queue.get_nowait()
        except Empty:
            return
        if line is None:
            return
        print(line, end="", flush=True)


def _wait_for_service(
    process: subprocess.Popen,
    url: str,
    label: str,
    timeout: int,
    output_queue: Queue[str | None] | None = None,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if output_queue is not None:
            _drain_proxy_output(output_queue)
        if process.poll() is not None:
            raise LauncherError(f"{label} s'est arrêté pendant son démarrage.")
        if _endpoint_ready(url):
            if output_queue is not None:
                _drain_proxy_output(output_queue)
            print(f"{label} prêt.")
            return
        time.sleep(min(2, max(0, deadline - time.monotonic())))
    raise LauncherError(f"{label} ne répond pas après {timeout} secondes.")


def _stop_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
    except OSError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main() -> int:
    runtime_process = None
    proxy_process = None
    proxy_log_file = None
    proxy_thread = None
    output_queue: Queue[str | None] = Queue()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        system = platform.system()
        binary = get_runtime_binary()
        if not binary.is_file():
            raise LauncherError(
                f"{binary} introuvable. Lancez install.bat, install.sh "
                "ou install.command."
            )
        if system != "Windows" and not os.access(binary, os.X_OK):
            raise LauncherError(
                f"{binary} n'est pas exécutable. Relancez l'installateur "
                "ou appliquez chmod +x."
            )

        PROXY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with PROXY_LOG.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[launcher] Démarrage du proxy; OS={system}\n")

        if _run_model_health(["--initialize-whitelist"], PROXY_LOG) != 0:
            raise LauncherError(
                "Initialisation ou vérification du GGUF intégré impossible."
            )
        model_path = select_model_path()

        print("Démarrage du serveur llamafile (port 8080)...")
        creationflags = (
            getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            if system == "Windows"
            else 0
        )
        runtime_process = subprocess.Popen(
            [
                str(binary),
                "-m",
                str(model_path),
                *RUNTIME_OPTIONS,
            ],
            cwd=PROJECT_ROOT,
            creationflags=creationflags,
        )
        _wait_for_service(runtime_process, RUNTIME_URL, "llamafile", 120)
        if _run_model_health(["--check", str(model_path)]) != 0:
            _run_model_health(["--rollback"], PROXY_LOG)
            raise LauncherError(
                "llamafile n'a pas confirmé le modèle. Chemin précédent "
                "restauré si disponible; relancez lancer.py."
            )

        print("Démarrage du proxy de login (port 8081)...")
        proxy_log_file = PROXY_LOG.open("ab")
        proxy_process = subprocess.Popen(
            [sys.executable, "-u", str(PROXY_SCRIPT)],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=proxy_log_file,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        proxy_thread = threading.Thread(
            target=_forward_proxy_output,
            args=(proxy_process.stdout, output_queue),
            daemon=True,
        )
        proxy_thread.start()
        _wait_for_service(
            proxy_process,
            PROXY_URL,
            "Proxy",
            60,
            output_queue,
        )
        try:
            opened = webbrowser.open(APP_URL)
        except (OSError, webbrowser.Error):
            opened = False
        if not opened:
            print(f"Ouvrez manuellement {APP_URL}.")
        print("La Citadelle est prête. Gardez cette fenêtre ouverte; Ctrl+C arrête les services.")

        while True:
            _drain_proxy_output(output_queue)
            if runtime_process.poll() is not None:
                raise LauncherError("Le serveur llamafile s'est arrêté.")
            if proxy_process.poll() is not None:
                raise LauncherError("Le proxy s'est arrêté.")
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nArrêt des services...")
        return 0
    except (LauncherError, OSError, RuntimeError) as exc:
        print(f"ERREUR : {exc}", file=sys.stderr)
        return 1
    finally:
        _stop_process(proxy_process)
        _stop_process(runtime_process)
        if proxy_thread is not None:
            proxy_thread.join(timeout=1)
        if proxy_process is not None and proxy_process.stdout is not None:
            proxy_process.stdout.close()
        if proxy_log_file is not None:
            proxy_log_file.close()


if __name__ == "__main__":
    raise SystemExit(main())
