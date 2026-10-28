"""Verify the model exposed by a local llamafile server."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

from citadelle_memory import get_setting, set_setting

DEFAULT_MODEL_PATH = str(
    Path("dev")
    / "tools"
    / "vendor"
    / "llamafile"
    / "Qwen3-1.7B-Q4_K_M.gguf"
)
CURRENT_MODEL_FILE = (
    Path(__file__).resolve().parents[2] / "dist" / ".current_model"
)
DEFAULT_BASE_URL = "http://127.0.0.1:8080"


def _normalize_path(path: str) -> str:
    return os.path.normcase(os.path.normpath(path)).replace("\\", "/")


def check_model_loaded(
    expected_path: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 60,
) -> tuple[bool, str]:
    """Return whether /v1/models reports the expected model path."""
    url = f"{base_url.rstrip('/')}/v1/models"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if getattr(response, "status", 200) != 200:
                return False, "http_error"
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError:
        return False, "http_error"
    except (TimeoutError, socket.timeout):
        return False, "timeout"
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (TimeoutError, socket.timeout)):
            return False, "timeout"
        return False, "http_error"
    except OSError:
        return False, "http_error"
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, "mismatch"

    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return False, "mismatch"
    model_id = data[0].get("id")
    if not isinstance(model_id, str) or not expected_path.strip():
        return False, "mismatch"

    expected = _normalize_path(expected_path)
    loaded = _normalize_path(model_id)
    if (
        expected == loaded
        or expected.rsplit("/", 1)[-1] == loaded.rsplit("/", 1)[-1]
    ):
        return True, "ok"
    return False, "mismatch"


def restore_previous_model(
    db_path: Path | None = None,
    model_file: Path | None = None,
) -> str:
    """Restore the prior model path, or the default when no prior is recorded."""
    previous_path = get_setting("previous_model_path", db_path=db_path)
    model_path = previous_path or DEFAULT_MODEL_PATH
    target = model_file or CURRENT_MODEL_FILE
    try:
        previous_mirror = target.read_bytes()
    except FileNotFoundError:
        previous_mirror = None
    target.parent.mkdir(parents=True, exist_ok=True)
    mirror_write_started = False
    try:
        mirror_write_started = True
        target.write_text(model_path + "\n", encoding="utf-8")
        set_setting("current_model_path", model_path, db_path=db_path)
    except (OSError, sqlite3.Error):
        if mirror_write_started:
            try:
                if previous_mirror is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_bytes(previous_mirror)
            except OSError as restore_exc:
                sys.stderr.write(
                    "[model] Rollback mirror restoration failed "
                    f"({type(restore_exc).__name__})\n"
                )
                raise
        raise
    return model_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check", metavar="MODEL_PATH")
    actions.add_argument("--rollback", action="store_true")
    args = parser.parse_args(argv)

    if args.rollback:
        try:
            model_path = restore_previous_model()
        except (OSError, sqlite3.Error) as exc:
            print(
                f"Rollback impossible ({type(exc).__name__}).",
                file=sys.stderr,
            )
            return 2
        print(f"Chemin de rollback enregistré : {model_path}")
        return 0

    loaded, status = check_model_loaded(args.check)
    print(status)
    return 0 if loaded else 1


if __name__ == "__main__":
    sys.exit(main())
