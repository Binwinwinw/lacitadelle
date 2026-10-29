"""Tests for the admin model-path configuration route."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import citadelle_memory
import login_server
import model_health
from _helpers import (
    SESSION_COOKIE_NAME,
    api_test_context,
    create_test_user,
    login_as,
    open_no_redirect,
)


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


def _post_model(opener, base_url, token, payload):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    request = Request(
        f"{base_url}/api/admin/model",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    return open_no_redirect(opener, request)


def _get_allowed_models(opener, base_url, token):
    headers = {}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    request = Request(
        f"{base_url}/api/settings/allowed_models",
        headers=headers,
    )
    return open_no_redirect(opener, request)


def _post_allowed_models(opener, base_url, token, payload):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    request = Request(
        f"{base_url}/api/settings/allowed_models",
        data=json.dumps(payload).encode("utf-8"),
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
            citadelle_memory.set_setting(
                "allowed_models",
                json.dumps([str(model_path.resolve())]),
                db_path=db_path,
            )

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
                assert json.loads(response.read())["error"] == (
                    "Le fichier GGUF est invalide "
                    "(inexistant, vide ou mauvaise extension)"
                )

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
                assert json.loads(response.read())["error"] == (
                    "Le fichier GGUF est invalide "
                    "(inexistant, vide ou mauvaise extension)"
                )

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
                assert json.loads(response.read())["error"] == (
                    "Le fichier GGUF est invalide "
                    "(inexistant, vide ou mauvaise extension)"
                )

        assert citadelle_memory.get_setting(
            "current_model_path",
            db_path=db_path,
        ) is None


def test_post_mirrors_path_and_first_manual_rollback_uses_default():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        token = login_as(opener, base_url, admin, "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "model.gguf"
            model_path.write_bytes(b"gguf")
            model_file = Path(temp_dir) / "dist" / ".current_model"
            citadelle_memory.set_setting(
                "allowed_models",
                json.dumps([str(model_path.resolve())]),
                db_path=db_path,
            )
            with (
                patch.object(login_server, "CURRENT_MODEL_FILE", model_file),
                patch.object(model_health, "CURRENT_MODEL_FILE", model_file),
            ):
                with _post_model(
                    opener,
                    base_url,
                    token,
                    {"model_path": str(model_path)},
                ) as response:
                    assert response.code == 200

            expected_path = str(model_path.resolve())
            assert citadelle_memory.get_setting(
                "current_model_path",
                db_path=db_path,
            ) == expected_path
            assert citadelle_memory.get_setting(
                "previous_model_path",
                db_path=db_path,
            ) is None
            assert model_file.read_text(encoding="utf-8") == expected_path + "\n"

            restored_path = model_health.restore_previous_model(
                db_path=db_path,
                model_file=model_file,
            )
            assert restored_path == model_health.DEFAULT_MODEL_PATH
            assert citadelle_memory.get_setting(
                "current_model_path",
                db_path=db_path,
            ) == restored_path
            assert model_file.read_text(encoding="utf-8") == restored_path + "\n"


def test_post_updates_previous_model_path_after_prior_post():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        token = login_as(opener, base_url, admin, "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            old_path = Path(temp_dir) / "old.gguf"
            new_path = Path(temp_dir) / "new.gguf"
            latest_path = Path(temp_dir) / "latest.gguf"
            for path in (old_path, new_path, latest_path):
                path.write_bytes(b"gguf")
            citadelle_memory.set_setting(
                "current_model_path",
                str(old_path.resolve()),
                db_path=db_path,
            )
            citadelle_memory.set_setting(
                "allowed_models",
                json.dumps(
                    [str(new_path.resolve()), str(latest_path.resolve())]
                ),
                db_path=db_path,
            )
            model_file = Path(temp_dir) / "dist" / ".current_model"
            with (
                patch.object(login_server, "CURRENT_MODEL_FILE", model_file),
                patch.object(model_health, "CURRENT_MODEL_FILE", model_file),
            ):
                for path in (new_path, latest_path):
                    with _post_model(
                        opener,
                        base_url,
                        token,
                        {"model_path": str(path)},
                    ) as response:
                        assert response.code == 200

            assert citadelle_memory.get_setting(
                "previous_model_path",
                db_path=db_path,
            ) == str(new_path.resolve())
            assert citadelle_memory.get_setting(
                "current_model_path",
                db_path=db_path,
            ) == str(latest_path.resolve())
            assert model_file.read_text(encoding="utf-8") == (
                str(latest_path.resolve()) + "\n"
            )

            restored_path = model_health.restore_previous_model(
                db_path=db_path,
                model_file=model_file,
            )
            assert restored_path == str(new_path.resolve())
            assert citadelle_memory.get_setting(
                "current_model_path",
                db_path=db_path,
            ) == restored_path
            assert model_file.read_text(encoding="utf-8") == restored_path + "\n"


def test_invalid_post_or_write_failure_preserves_model_state():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        token = login_as(opener, base_url, admin, "secret123")
        current_path = r"C:\models\current.gguf"
        previous_path = r"C:\models\previous.gguf"
        citadelle_memory.set_setting(
            "current_model_path",
            current_path,
            db_path=db_path,
        )
        citadelle_memory.set_setting(
            "previous_model_path",
            previous_path,
            db_path=db_path,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            model_file = Path(temp_dir) / ".current_model"
            model_file.write_text(current_path + "\n", encoding="utf-8")
            missing_path = Path(temp_dir) / "missing.gguf"
            valid_path = Path(temp_dir) / "valid.gguf"
            valid_path.write_bytes(b"gguf")
            citadelle_memory.set_setting(
                "allowed_models",
                json.dumps([str(valid_path.resolve())]),
                db_path=db_path,
            )
            original_write_text = Path.write_text

            def fail_mirror_write(target, data, *args, **kwargs):
                if target == model_file:
                    raise OSError("simulated disk failure")
                return original_write_text(target, data, *args, **kwargs)

            with (
                patch.object(login_server, "CURRENT_MODEL_FILE", model_file),
                patch.object(model_health, "CURRENT_MODEL_FILE", model_file),
                patch.object(Path, "write_text", new=fail_mirror_write),
            ):
                with _post_model(
                    opener,
                    base_url,
                    token,
                    {"model_path": str(missing_path)},
                ) as response:
                    assert response.code == 400
                with _post_model(
                    opener,
                    base_url,
                    token,
                    {"model_path": str(valid_path)},
                ) as response:
                    assert response.code == 500

            with patch.object(
                model_health,
                "set_setting",
                side_effect=model_health.sqlite3.OperationalError(
                    "simulated database failure"
                ),
            ):
                try:
                    model_health.restore_previous_model(
                        db_path=db_path,
                        model_file=model_file,
                    )
                except model_health.sqlite3.Error:
                    pass
                else:
                    raise AssertionError("rollback should report database failure")

            assert model_file.read_text(encoding="utf-8") == current_path + "\n"

        assert citadelle_memory.get_setting(
            "current_model_path",
            db_path=db_path,
        ) == current_path
        assert citadelle_memory.get_setting(
            "previous_model_path",
            db_path=db_path,
        ) == previous_path


def test_post_rejects_when_whitelist_empty():
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
                assert response.code == 400
                assert "aucun modèle autorisé" in json.loads(
                    response.read()
                )["error"].lower()

        assert citadelle_memory.get_setting(
            "current_model_path",
            db_path=db_path,
        ) is None


def test_post_accepts_path_in_whitelist():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        token = login_as(opener, base_url, admin, "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            allowed_path = Path(temp_dir) / "allowed.gguf"
            other_path = Path(temp_dir) / "other.gguf"
            allowed_path.write_bytes(b"gguf")
            other_path.write_bytes(b"gguf")
            allowed_path_variant = str(allowed_path.resolve()).replace(
                "\\",
                "/",
            )
            citadelle_memory.set_setting(
                "allowed_models",
                json.dumps(
                    [allowed_path_variant, str(other_path.resolve())]
                ),
                db_path=db_path,
            )

            with _post_model(
                opener,
                base_url,
                token,
                {"model_path": str(allowed_path)},
            ) as response:
                assert response.code == 200

            assert citadelle_memory.get_setting(
                "current_model_path",
                db_path=db_path,
            ) == str(allowed_path.resolve())


def test_post_rejects_path_not_in_whitelist():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        token = login_as(opener, base_url, admin, "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            allowed_path = Path(temp_dir) / "allowed.gguf"
            rejected_path = Path(temp_dir) / "rejected.gguf"
            allowed_path.write_bytes(b"gguf")
            rejected_path.write_bytes(b"gguf")
            citadelle_memory.set_setting(
                "allowed_models",
                json.dumps([str(allowed_path.resolve())]),
                db_path=db_path,
            )

            with _post_model(
                opener,
                base_url,
                token,
                {"model_path": str(rejected_path)},
            ) as response:
                assert response.code == 400
                assert "ce modèle n'est pas autorisé" in json.loads(
                    response.read()
                )["error"].lower()

        assert citadelle_memory.get_setting(
            "current_model_path",
            db_path=db_path,
        ) is None


def test_post_rejects_invalid_path_regardless_of_whitelist():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        token = login_as(opener, base_url, admin, "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "missing.gguf"
            citadelle_memory.set_setting(
                "allowed_models",
                json.dumps([str(invalid_path)]),
                db_path=db_path,
            )

            with _post_model(
                opener,
                base_url,
                token,
                {"model_path": str(invalid_path)},
            ) as response:
                assert response.code == 400
                assert "le fichier gguf est invalide" in json.loads(
                    response.read()
                )["error"].lower()


def test_get_allowed_models_returns_list():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        admin_token = login_as(opener, base_url, admin, "secret123")
        create_test_user(db_path, "alice", "secret123")
        user_token = login_as(opener, base_url, "alice", "secret123")

        with _get_allowed_models(opener, base_url, None) as response:
            assert response.code == 401
        with _get_allowed_models(opener, base_url, user_token) as response:
            assert response.code == 403
        with _get_allowed_models(
            opener,
            base_url,
            admin_token,
        ) as response:
            assert response.code == 200
            assert json.loads(response.read()) == {"models": []}

        models = [r"C:\models\one.gguf", r"C:\models\two.gguf"]
        citadelle_memory.set_setting(
            "allowed_models",
            json.dumps(models),
            db_path=db_path,
        )
        with _get_allowed_models(
            opener,
            base_url,
            admin_token,
        ) as response:
            assert response.code == 200
            assert json.loads(response.read()) == {"models": models}


def test_post_allowed_models_validates_and_saves_paths():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        admin = _create_admin(db_path)
        token = login_as(opener, base_url, admin, "secret123")
        create_test_user(db_path, "alice", "secret123")
        user_token = login_as(opener, base_url, "alice", "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "model.gguf"
            text_path = Path(temp_dir) / "model.txt"
            empty_path = Path(temp_dir) / "empty.gguf"
            missing_path = Path(temp_dir) / "missing.gguf"
            model_path.write_bytes(b"gguf")
            text_path.write_text("not a GGUF", encoding="utf-8")
            empty_path.touch()

            with _post_allowed_models(
                opener,
                base_url,
                None,
                {"models": [str(model_path)]},
            ) as response:
                assert response.code == 401

            with _post_allowed_models(
                opener,
                base_url,
                user_token,
                {"models": [str(model_path)]},
            ) as response:
                assert response.code == 403

            with _post_allowed_models(
                opener,
                base_url,
                token,
                {"models": [str(model_path)]},
            ) as response:
                assert response.code == 200
                expected_models = [str(model_path.resolve())]
                assert json.loads(response.read()) == {
                    "models": expected_models
                }

            assert citadelle_memory.get_setting(
                "allowed_models",
                db_path=db_path,
            ) == json.dumps(expected_models)

            for invalid_path in (missing_path, text_path, empty_path):
                with _post_allowed_models(
                    opener,
                    base_url,
                    token,
                    {"models": [str(invalid_path)]},
                ) as response:
                    assert response.code == 400
                    assert "gguf" in json.loads(response.read())["error"].lower()
                assert citadelle_memory.get_setting(
                    "allowed_models",
                    db_path=db_path,
                ) == json.dumps(expected_models)


def run_all():
    tests = [
        test_set_model_requires_admin,
        test_set_model_valid_path_saves_resolved_path,
        test_set_model_invalid_path,
        test_set_model_invalid_extension,
        test_set_model_rejects_empty_file,
        test_post_mirrors_path_and_first_manual_rollback_uses_default,
        test_post_updates_previous_model_path_after_prior_post,
        test_invalid_post_or_write_failure_preserves_model_state,
        test_post_rejects_when_whitelist_empty,
        test_post_accepts_path_in_whitelist,
        test_post_rejects_path_not_in_whitelist,
        test_post_rejects_invalid_path_regardless_of_whitelist,
        test_get_allowed_models_returns_list,
        test_post_allowed_models_validates_and_saves_paths,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
