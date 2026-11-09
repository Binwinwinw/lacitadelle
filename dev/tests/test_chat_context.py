import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import citadelle_memory
from _helpers import create_test_user


def _session(tmp_path: Path) -> tuple[int, int, Path]:
    db_path = tmp_path / "context.db"
    citadelle_memory.migrate_to_v3(db_path)
    user_id = create_test_user(db_path, "alice", "secret123")
    session_id = citadelle_memory.create_session_for_user(user_id, db_path=db_path)
    return user_id, session_id, db_path


def test_token_budget_respects_limit(tmp_path):
    user_id, session_id, db_path = _session(tmp_path)
    for index in range(20):
        citadelle_memory.add_message(
            session_id,
            "user" if index % 2 == 0 else "assistant",
            "x" * 1000,
            db_path=db_path,
        )

    result = citadelle_memory.get_messages_for_user_within_token_budget(
        user_id, session_id, max_tokens=2000, db_path=db_path
    )

    assert sum(len(message["content"]) for message in result) <= 2000 * 4


def test_starts_with_user(tmp_path):
    user_id, session_id, db_path = _session(tmp_path)
    for role in ("user", "assistant", "user", "assistant", "user"):
        citadelle_memory.add_message(session_id, role, "x" * 10, db_path=db_path)

    result = citadelle_memory.get_messages_for_user_within_token_budget(
        user_id, session_id, max_tokens=3, db_path=db_path
    )

    assert result[0]["role"] == "user"


def test_recent_messages_kept(tmp_path):
    user_id, session_id, db_path = _session(tmp_path)
    for index in range(10):
        citadelle_memory.add_message(
            session_id,
            "user" if index % 2 == 0 else "assistant",
            f"msg_{index}",
            db_path=db_path,
        )

    result = citadelle_memory.get_messages_for_user_within_token_budget(
        user_id, session_id, max_tokens=3, db_path=db_path
    )

    contents = [message["content"] for message in result]
    assert contents[-1] == "msg_9"
    assert "msg_0" not in contents


def test_empty_session(tmp_path):
    db_path = tmp_path / "context.db"
    citadelle_memory.migrate_to_v3(db_path)
    user_id = create_test_user(db_path, "alice", "secret123")

    result = citadelle_memory.get_messages_for_user_within_token_budget(
        user_id, 999, db_path=db_path
    )

    assert result == []
