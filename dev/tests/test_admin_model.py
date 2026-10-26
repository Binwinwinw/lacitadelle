"""Tests for the admin model-path configuration route."""

import json
import sys
import tempfile
from pathlib import Path
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import citadelle_memory
from _helpers import (
    SESSION_COOKIE_NAME,
    api_test_context,
    create_test_user,
    login_as,
    open_no_redirect,
)


def _post_model(opener, base_url, token, payload):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else b""
    request = Request(
        f"{base_url}/api/admin/model",
        data=body,
        headers=headers,
        method="POST",
    )
    return open_no_redirect(opener, request)


def _create_admin(db_path: Path) -> str:
    create_test_user(
        db_path,
        "admin",
        "secret123",
        role="admin",
    )
    return "admin"


def test_set_model_requires_admin():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        with _post_model(
            opener,
            base_url,
            None,
            {"model_path": "model.gguf"},
        ) as response:
            assert response.code == 401

        create_test_user(db_path, "alice", "secret123")
        user_token = login_as(opener, base_url, "alice", "secret123")
        with _post_model(
            opener,
            base_url,
            user_token,
            {"model_path": "model.gguf"},
        ) as response:
            assert response.code == 403


def test_set_model_valid_path_saves_resolved_path():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        token = login_as(opener, base_url, admin, "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "model.gguf"
            model_path.write_bytes(b"gguf")

            with _post_model(
                opener,
                base_url,
                token,
                {"model_path": str(model_path)},
            ) as response:
                assert response.code == 200
                result = json.loads(response.read())

            expected_path = str(model_path.resolve())
            assert result == {
                "model_path": expected_path,
                "size_bytes": 4,
                "applied": True,
                "message": (
                    "Chemin enregistré. Le modèle sera chargé après le test "
                    "de chargement et le redémarrage du lot 11d."
                ),
            }
            assert citadelle_memory.get_setting(
                "current_model_path",
                db_path=db_path,
            ) == expected_path


def test_set_model_invalid_path():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        token = login_as(opener, base_url, admin, "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.gguf"
            with _post_model(
                opener,
                base_url,
                token,
                {"model_path": str(missing_path)},
            ) as response:
                assert response.code == 400

        assert citadelle_memory.get_setting(
            "current_model_path",
            db_path=db_path,
        ) is None


def test_set_model_invalid_extension():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        token = login_as(opener, base_url, admin, "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            text_path = Path(temp_dir) / "model.txt"
            text_path.write_text("not a GGUF", encoding="utf-8")
            with _post_model(
                opener,
                base_url,
                token,
                {"model_path": str(text_path)},
            ) as response:
                assert response.code == 400

        assert citadelle_memory.get_setting(
            "current_model_path",
            db_path=db_path,
        ) is None


def test_set_model_rejects_empty_file():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        token = login_as(opener, base_url, admin, "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_path = Path(temp_dir) / "empty.gguf"
            empty_path.touch()
            with _post_model(
                opener,
                base_url,
                token,
                {"model_path": str(empty_path)},
            ) as response:
                assert response.code == 400

        assert citadelle_memory.get_setting(
            "current_model_path",
            db_path=db_path,
        ) is None


def run_all():
    tests = [
        test_set_model_requires_admin,
        test_set_model_valid_path_saves_resolved_path,
        test_set_model_invalid_path,
        test_set_model_invalid_extension,
        test_set_model_rejects_empty_file,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
