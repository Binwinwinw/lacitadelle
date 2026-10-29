"""Tests for llamafile model readiness and identity checks."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import citadelle_memory
import model_health


@pytest.fixture(autouse=True)
def preserve_current_model_file():
    real_file = Path(__file__).resolve().parents[2] / "dist" / ".current_model"
    backup = real_file.read_bytes() if real_file.exists() else None
    try:
        yield
    finally:
        if backup is not None:
            real_file.write_bytes(backup)
        else:
            real_file.unlink(missing_ok=True)


def _response(model_id: str):
    response = MagicMock()
    response.status = 200
    response.__enter__.return_value = response
    response.read.return_value = json.dumps(
        {"data": [{"id": model_id}]}
    ).encode("utf-8")
    return response


def test_health_check_ok():
    expected = r"C:\models\Qwen3.gguf"
    with patch(
        "model_health.urllib.request.urlopen",
        side_effect=[
            _response("C:/models/Qwen3.gguf"),
            _response("Qwen3.gguf"),
        ],
    ) as urlopen:
        assert model_health.check_model_loaded(expected) == (True, "ok")
        assert model_health.check_model_loaded(expected) == (True, "ok")
    assert urlopen.call_args.args[0] == "http://127.0.0.1:8080/v1/models"


def test_health_check_mismatch():
    with patch(
        "model_health.urllib.request.urlopen",
        return_value=_response("C:/models/other.gguf"),
    ):
        assert model_health.check_model_loaded(
            r"C:\models\Qwen3.gguf"
        ) == (False, "mismatch")


def test_health_check_timeout():
    with patch(
        "model_health.urllib.request.urlopen",
        side_effect=TimeoutError(),
    ):
        assert model_health.check_model_loaded(
            r"C:\models\Qwen3.gguf"
        ) == (False, "timeout")


def test_health_check_http_error():
    error = HTTPError(
        "http://127.0.0.1:8080/v1/models",
        500,
        "server error",
        hdrs=None,
        fp=None,
    )
    with patch(
        "model_health.urllib.request.urlopen",
        side_effect=error,
    ):
        assert model_health.check_model_loaded(
            r"C:\models\Qwen3.gguf"
        ) == (False, "http_error")


def test_check_whitelist_returns_true_for_allowed_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "memory.db"
        model_path = Path(temp_dir) / "allowed.gguf"
        model_path.write_bytes(b"gguf")
        citadelle_memory.migrate_to_v6(db_path)
        citadelle_memory.set_setting(
            "allowed_models",
            json.dumps([str(model_path.resolve()).replace("\\", "/")]),
            db_path=db_path,
        )

        assert model_health.check_whitelist(str(model_path), db_path=db_path)
        with patch.object(model_health, "check_whitelist", return_value=True):
            assert model_health.main(
                ["--check-whitelist", str(model_path)]
            ) == 0


def test_check_whitelist_returns_false_for_unallowed_path():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "memory.db"
        allowed_path = Path(temp_dir) / "allowed.gguf"
        rejected_path = Path(temp_dir) / "rejected.gguf"
        allowed_path.write_bytes(b"gguf")
        rejected_path.write_bytes(b"gguf")
        citadelle_memory.migrate_to_v6(db_path)
        citadelle_memory.set_setting(
            "allowed_models",
            json.dumps([str(allowed_path.resolve())]),
            db_path=db_path,
        )

        assert not model_health.check_whitelist(
            str(rejected_path),
            db_path=db_path,
        )


def test_check_whitelist_empty_returns_false():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "memory.db"
        model_path = Path(temp_dir) / "model.gguf"
        model_path.write_bytes(b"gguf")
        citadelle_memory.migrate_to_v6(db_path)

        assert not model_health.check_whitelist(str(model_path), db_path=db_path)

        citadelle_memory.set_setting("allowed_models", "[]", db_path=db_path)
        assert not model_health.check_whitelist(str(model_path), db_path=db_path)
        with patch.object(model_health, "check_whitelist", return_value=False):
            assert model_health.main(
                ["--check-whitelist", str(model_path)]
            ) == 1


def test_pytest_does_not_pollute_current_model_file():
    real_file = model_health.CURRENT_MODEL_FILE
    if real_file.exists():
        content = real_file.read_text(encoding="ascii").strip()
        assert "Wondershare" not in content
        assert "CreatorTemp" not in content
        assert (
            "tmp" not in content.lower()
            or "dev/tools/vendor" in content.lower()
            or "qwen" in content.lower()
        )


def run_all():
    tests = [
        test_health_check_ok,
        test_health_check_mismatch,
        test_health_check_timeout,
        test_health_check_http_error,
        test_check_whitelist_returns_true_for_allowed_path,
        test_check_whitelist_returns_false_for_unallowed_path,
        test_check_whitelist_empty_returns_false,
        test_pytest_does_not_pollute_current_model_file,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
