import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import login_server
import security_files

PROMPT_FILE = Path(login_server.PROMPT_FILE)


def test_system_prompt_loaded_and_missing_file_fallback(tmp_path, monkeypatch):
    prompt = login_server.load_system_prompt("model.gguf", "alice", 12)
    assert prompt
    assert "Tu es Nexxus" in prompt

    monkeypatch.setattr(login_server, "PROMPT_FILE", tmp_path / "missing.txt")
    fallback = login_server.load_system_prompt("model.gguf", "alice", 12)
    assert "Tu es Nexxus" in fallback
    assert "model.gguf" in fallback
    assert "alice" in fallback


def test_system_prompt_substitutes_model_name():
    prompt = login_server.load_system_prompt(
        "Qwen3-4B-Q4_K_M.gguf",
        "alice",
        12,
    )
    assert "- Modèle actif : Qwen3-4B-Q4_K_M.gguf" in prompt
    assert "{model_name}" not in prompt


def test_system_prompt_substitutes_date_username_and_session():
    with patch.object(login_server, "datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 10, 31, 20, 17)
        prompt = login_server.load_system_prompt("model.gguf", "alice", 42)

    assert "Date actuelle : 2026-10-31 20:17" in prompt
    assert "Nom de l'utilisateur : alice" in prompt
    assert "Session : 42" in prompt


def test_extract_model_name_from_settings():
    with patch.object(
        login_server,
        "get_setting",
        return_value="/models/test-model.gguf",
    ):
        assert login_server.extract_model_name() == "test-model.gguf"

    with patch.object(login_server, "get_setting", return_value=None):
        assert login_server.extract_model_name() == "Qwen3-4B-Q4_K_M.gguf"


def test_classify_file_public_extensions(tmp_path):
    for filename in ("notes.txt", "guide.md", "data.csv"):
        path = tmp_path / filename
        path.write_text("contenu", encoding="utf-8")
        assert security_files.classify_file(path) == security_files.FilePolicy.PUBLIC


def test_classify_file_sensitive_extensions(tmp_path):
    for filename in (".env", "settings.ini", "memory.sqlite"):
        path = tmp_path / filename
        path.write_text("contenu", encoding="utf-8")
        assert (
            security_files.classify_file(path)
            == security_files.FilePolicy.SENSITIVE
        )

    disguised_archive = tmp_path / "notes.txt"
    disguised_archive.write_bytes(b"PK\x03\x04" + b"\x00" * 8)
    assert (
        security_files.classify_file(disguised_archive)
        == security_files.FilePolicy.SENSITIVE
    )


def test_classify_file_critical_extensions_and_magic_bytes(tmp_path):
    for filename in ("program.exe", "library.dll", "script.sh", "private.pem"):
        path = tmp_path / filename
        path.write_bytes(b"not inspected for critical extensions")
        assert (
            security_files.classify_file(path)
            == security_files.FilePolicy.CRITICAL
        )

    disguised_binary = tmp_path / "notes.txt"
    disguised_binary.write_bytes(b"\x7fELF" + b"\x00" * 8)
    assert (
        security_files.classify_file(disguised_binary)
        == security_files.FilePolicy.CRITICAL
    )


def test_can_read_public_for_any_role(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("public", encoding="utf-8")

    assert security_files.can_read(path, "user") == (
        True,
        "Accès public autorisé.",
    )


def test_can_read_sensitive_admin_only(tmp_path):
    path = tmp_path / ".env"
    path.write_text("secret", encoding="utf-8")

    allowed, reason = security_files.can_read(path, "user")
    assert not allowed
    assert "administrateurs" in reason
    assert security_files.can_read(path, "admin") == (
        True,
        "Accès administrateur.",
    )


def test_can_never_read_critical_file(tmp_path):
    path = tmp_path / "program.exe"
    path.write_bytes(b"MZ" + b"\x00" * 8)

    for role in ("user", "admin"):
        allowed, reason = security_files.can_read(path, role)
        assert not allowed
        assert "interdite" in reason


def test_prompt_forbids_flattery():
    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    assert "INTERDIT" in prompt
    assert "Je suis ravi de vous aider" in prompt
    assert "Quelle excellente question" in prompt
    assert "Commence directement par la réponse" in prompt


def test_prompt_distinguishes_philosophy():
    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    assert "philosophiques, existentielles ou générales" in prompt
    assert "Quel est le sens de la vie ?" in prompt


def test_prompt_mentions_local_llamafile_api():
    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    assert "llamafile" in prompt
    assert "http://127.0.0.1:8080" in prompt
    assert "/v1/models" in prompt
