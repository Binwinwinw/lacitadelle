import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import citadelle_memory
import lancer
import model_health


def test_v7_seeds_verified_integrated_gguf_on_first_install(tmp_path, monkeypatch):
    db_path = tmp_path / "memory.db"
    model_path = tmp_path / "Qwen3-1.7B-Q4_K_M.gguf"
    model_path.write_bytes(b"integrated gguf fixture")
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    config_path = (
        Path(__file__).resolve().parents[2]
        / "dev"
        / "tools"
        / "llamafile_config.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert citadelle_memory.SHA256_INTEGRATED_MODEL_GGUF == config["assets"][
        "qwen3-1.7b-q4km"
    ]["sha256"]
    monkeypatch.setattr(
        citadelle_memory,
        "SHA256_INTEGRATED_MODEL_GGUF",
        digest,
    )

    assert citadelle_memory.migrate_to_v7(db_path, model_path)
    assert citadelle_memory.get_setting(
        "current_model_path",
        db_path=db_path,
    ) is None
    assert json.loads(
        citadelle_memory.get_setting("allowed_models", db_path=db_path)
    ) == [str(model_path.resolve())]
    with citadelle_memory._connect(db_path) as conn:
        assert conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='settings'"
        ).fetchone() is not None


def test_v7_is_idempotent(tmp_path, monkeypatch):
    db_path = tmp_path / "memory.db"
    model_path = tmp_path / "Qwen3-1.7B-Q4_K_M.gguf"
    model_path.write_bytes(b"integrated gguf fixture")
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    citadelle_memory.migrate_to_v6(db_path)
    citadelle_memory.set_setting("allowed_models", "[]", db_path=db_path)
    monkeypatch.setattr(
        citadelle_memory,
        "SHA256_INTEGRATED_MODEL_GGUF",
        digest,
    )

    assert citadelle_memory.migrate_to_v7(db_path, model_path)
    assert not citadelle_memory.migrate_to_v7(db_path, model_path)
    assert json.loads(
        citadelle_memory.get_setting("allowed_models", db_path=db_path)
    ) == [str(model_path.resolve())]


def test_v7_does_not_whitelist_a_missing_integrated_gguf(tmp_path):
    db_path = tmp_path / "memory.db"
    missing_model = tmp_path / "missing.gguf"

    assert not citadelle_memory.migrate_to_v7(db_path, missing_model)
    assert citadelle_memory.get_setting(
        "allowed_models",
        db_path=db_path,
    ) is None


def test_v7_rejects_bad_hash_without_whitelisting(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "memory.db"
    model_path = tmp_path / "Qwen3-1.7B-Q4_K_M.gguf"
    model_path.write_bytes(b"tampered gguf fixture")
    monkeypatch.setattr(
        citadelle_memory,
        "SHA256_INTEGRATED_MODEL_GGUF",
        "0" * 64,
    )

    with pytest.raises(ValueError, match="SHA-256"):
        citadelle_memory.migrate_to_v7(db_path, model_path)
    assert citadelle_memory.get_setting(
        "allowed_models",
        db_path=db_path,
    ) is None

    monkeypatch.setattr(citadelle_memory, "DB_PATH", db_path)
    monkeypatch.setattr(
        citadelle_memory,
        "INTEGRATED_MODEL_GGUF",
        model_path,
    )
    assert model_health.main(["--initialize-whitelist"]) == 3
    assert "Initialisation whitelist refusée" in capsys.readouterr().err


def test_v7_preserves_an_existing_whitelist_and_current_model(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "memory.db"
    current_model = tmp_path / "current.gguf"
    current_model.write_bytes(b"current model")
    allowed_models = [str(current_model.resolve())]
    citadelle_memory.migrate_to_v6(db_path)
    citadelle_memory.set_setting(
        "current_model_path",
        str(current_model.resolve()),
        db_path=db_path,
    )
    citadelle_memory.set_setting(
        "allowed_models",
        json.dumps(allowed_models),
        db_path=db_path,
    )
    monkeypatch.setattr(
        citadelle_memory,
        "SHA256_INTEGRATED_MODEL_GGUF",
        "0" * 64,
    )

    assert not citadelle_memory.migrate_to_v7(
        db_path,
        tmp_path / "integrated.gguf",
    )
    assert json.loads(
        citadelle_memory.get_setting("allowed_models", db_path=db_path)
    ) == allowed_models


def test_current_model_gate_and_lancer_default_branch(tmp_path, monkeypatch):
    db_path = tmp_path / "memory.db"
    model_path = tmp_path / "current.gguf"
    model_path.write_bytes(b"current model")
    citadelle_memory.migrate_to_v6(db_path)
    monkeypatch.setattr(citadelle_memory, "DB_PATH", db_path)

    assert model_health.main(["--has-current-model"]) == 1
    citadelle_memory.set_setting(
        "current_model_path",
        str(model_path),
    )
    assert model_health.main(["--has-current-model"]) == 0
    citadelle_memory.set_setting(
        "current_model_path",
        str(tmp_path / "missing.gguf"),
    )
    assert model_health.main(["--has-current-model"]) == 1

    model_file = tmp_path / "dist" / ".current_model"
    model_file.parent.mkdir()
    monkeypatch.setattr(lancer, "CURRENT_MODEL_FILE", model_file)
    monkeypatch.setattr(model_health, "CURRENT_MODEL_FILE", model_file)
    proxy_log = tmp_path / "proxy.log"
    assert lancer.select_model_path(proxy_log) == (
        Path(__file__).resolve().parents[2]
        / "dev"
        / "tools"
        / "vendor"
        / "llamafile"
        / "Qwen3-1.7B-Q4_K_M.gguf"
    )

    model_path.write_bytes(b"current model")
    citadelle_memory.set_setting("current_model_path", str(model_path))
    citadelle_memory.set_setting(
        "allowed_models",
        json.dumps([str(model_path.resolve())]),
    )
    model_file.write_text(str(model_path.resolve()) + "\n", encoding="utf-8")
    assert lancer.select_model_path(proxy_log) == model_path.resolve()


def test_automatic_rollback_refuses_missing_previous_model(
    tmp_path,
    monkeypatch,
    capsys,
):
    db_path = tmp_path / "memory.db"
    marker = tmp_path / "dist" / ".current_model"
    marker.parent.mkdir()
    marker.write_text("unchanged.gguf\n", encoding="utf-8")
    citadelle_memory.migrate_to_v6(db_path)
    monkeypatch.setattr(citadelle_memory, "DB_PATH", db_path)
    monkeypatch.setattr(model_health, "CURRENT_MODEL_FILE", marker)

    assert (
        model_health.get_previous_model_path()
        is model_health.NO_PREVIOUS_MODEL
    )
    assert model_health.main(["--rollback"]) == 3
    assert "[security] rollback refusé : aucun modèle antérieur valide" in (
        capsys.readouterr().err
    )
    assert marker.read_text(encoding="utf-8") == "unchanged.gguf\n"
    assert citadelle_memory.get_setting("current_model_path") is None


def test_automatic_rollback_restores_a_valid_previous_model(tmp_path, monkeypatch):
    db_path = tmp_path / "memory.db"
    previous_model = tmp_path / "previous.gguf"
    previous_model.write_bytes(b"previous model")
    marker = tmp_path / "dist" / ".current_model"
    citadelle_memory.migrate_to_v6(db_path)
    citadelle_memory.set_setting(
        "previous_model_path",
        str(previous_model),
        db_path=db_path,
    )
    monkeypatch.setattr(citadelle_memory, "DB_PATH", db_path)
    monkeypatch.setattr(model_health, "CURRENT_MODEL_FILE", marker)

    assert model_health.main(["--rollback"]) == 0
    assert marker.read_text(encoding="utf-8") == str(previous_model) + "\n"
    assert citadelle_memory.get_setting("current_model_path") == str(
        previous_model
    )
