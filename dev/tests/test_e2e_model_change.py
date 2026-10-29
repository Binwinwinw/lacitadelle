"""End-to-end tests for the admin model-change workflow."""

import io
import json
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import citadelle_memory
import login_server
import model_health
from _helpers import api_post, api_test_context, create_test_user, login_as


def _admin(opener, base_url, db_path):
    create_test_user(db_path, "admin", "secret123", role="admin")
    return login_as(opener, base_url, "admin", "secret123")


def test_e2e_full_workflow_admin_changes_model():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        token = _admin(opener, base_url, db_path)
        with io.StringIO() as security_log:
            with tempfile.TemporaryDirectory() as temp_dir:
                model_path = Path(temp_dir) / "model.gguf"
                model_path.write_bytes(b"gguf")
                mirror_path = Path(temp_dir) / "dist" / ".current_model"
                expected_path = str(model_path.resolve())
                citadelle_memory.set_setting(
                    "allowed_models",
                    json.dumps([expected_path]),
                    db_path=db_path,
                )

                with redirect_stderr(security_log):
                    with patch.object(
                        login_server,
                        "CURRENT_MODEL_FILE",
                        mirror_path,
                    ):
                        with api_post(
                            opener,
                            base_url,
                            "/api/admin/model",
                            token,
                            {"model_path": expected_path},
                        ) as response:
                            assert response.code == 200
                            result = json.loads(response.read())

                    assert result["model_path"] == expected_path
                    assert citadelle_memory.get_setting(
                        "current_model_path",
                        db_path=db_path,
                    ) == expected_path
                    assert mirror_path.read_text(encoding="utf-8") == (
                        expected_path + "\n"
                    )
                    assert citadelle_memory.get_setting(
                        "previous_model_path",
                        db_path=db_path,
                    ) is None
                    assert model_health.check_whitelist(
                        expected_path,
                        db_path=db_path,
                    )
                assert (
                    f"[security] Changement modele: admin -> {expected_path}"
                    in security_log.getvalue()
                )

                with redirect_stderr(security_log):
                    restored_path = model_health.restore_previous_model(
                        db_path=db_path,
                        model_file=mirror_path,
                    )
                assert restored_path == model_health.DEFAULT_MODEL_PATH
                assert mirror_path.read_text(encoding="utf-8") == (
                    restored_path + "\n"
                )
                assert "[security] Rollback modele:" in security_log.getvalue()


def test_e2e_whitelist_blocks_unallowed():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        token = _admin(opener, base_url, db_path)
        with tempfile.TemporaryDirectory() as temp_dir:
            allowed_path = Path(temp_dir) / "allowed.gguf"
            rejected_path = Path(temp_dir) / "rejected.gguf"
            old_path = Path(temp_dir) / "old.gguf"
            for path in (allowed_path, rejected_path, old_path):
                path.write_bytes(b"gguf")
            mirror_path = Path(temp_dir) / "dist" / ".current_model"
            old_model_path = str(old_path.resolve())
            citadelle_memory.set_setting(
                "allowed_models",
                json.dumps([str(allowed_path.resolve())]),
                db_path=db_path,
            )
            citadelle_memory.set_setting(
                "current_model_path",
                old_model_path,
                db_path=db_path,
            )
            mirror_path.parent.mkdir(parents=True)
            mirror_path.write_text(old_model_path + "\n", encoding="utf-8")

            with patch.object(
                login_server,
                "CURRENT_MODEL_FILE",
                mirror_path,
            ):
                with api_post(
                    opener,
                    base_url,
                    "/api/admin/model",
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
            ) == old_model_path
            assert mirror_path.read_text(encoding="utf-8") == (
                old_model_path + "\n"
            )
            assert not model_health.check_whitelist(
                str(rejected_path),
                db_path=db_path,
            )


def run_all():
    tests = [
        test_e2e_full_workflow_admin_changes_model,
        test_e2e_whitelist_blocks_unallowed,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
