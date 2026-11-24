import importlib
import logging
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(TESTS_DIR.parent / "tools"))

citadelle_memory = importlib.import_module("citadelle_memory")
test_helpers = importlib.import_module("_helpers")
create_test_user = test_helpers.create_test_user


def _prepare_v13_database(db_path: Path) -> tuple[int, int]:
    citadelle_memory.migrate_to_v3(db_path)
    citadelle_memory.migrate_to_v4(db_path)
    citadelle_memory.migrate_to_v5(db_path)
    citadelle_memory.migrate_to_v6(db_path)
    citadelle_memory.migrate_to_v8(db_path)
    citadelle_memory.migrate_to_v9(db_path)
    citadelle_memory.migrate_to_v10(db_path)
    citadelle_memory.migrate_to_v11(db_path)
    citadelle_memory.migrate_to_v13(db_path)
    user_id = create_test_user(db_path, "logging-user", "secret123")
    session_id = citadelle_memory.create_session_for_user(
        user_id,
        db_path=db_path,
    )
    return user_id, session_id


def test_document_delete_logs_document_session_and_owner(tmp_path, caplog):
    db_path = tmp_path / "logging-document.db"
    user_id, session_id = _prepare_v13_database(db_path)
    document_id = citadelle_memory.add_conversation_document(
        user_id,
        session_id,
        "private document content",
        {"file_name": "notes.md"},
        db_path=db_path,
    )
    assert document_id is not None

    with caplog.at_level(logging.INFO, logger="citadelle_memory"):
        removed = citadelle_memory.delete_conversation_document_for_user(
            user_id,
            document_id,
            db_path=db_path,
            actor_id=user_id,
        )

    assert removed is True
    assert (
        f"DELETE conversation_documents: id={document_id}, "
        f"session_id={session_id}, user_id={user_id}"
    ) in caplog.text
    assert "private document content" not in caplog.text


def test_session_delete_logs_session_and_owner(tmp_path, caplog):
    db_path = tmp_path / "logging-session.db"
    user_id, session_id = _prepare_v13_database(db_path)

    with caplog.at_level(logging.INFO, logger="citadelle_memory"):
        citadelle_memory.delete_session(
            session_id,
            db_path=db_path,
            actor_id=user_id,
        )

    assert f"DELETE sessions: id={session_id}, user_id={user_id}" in caplog.text
