"""Tests unitaires pour les helpers SQLite filtrés par user_id."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from citadelle_memory import (
    add_message,
    create_session,
    get_messages,
    get_messages_for_user,
    get_session_for_user,
    init_db,
    list_sessions_for_user,
)


def _create_user(db_path: Path, username: str) -> int:
    """Crée un utilisateur et retourne son id."""
    init_db(db_path)
    from citadelle_memory import _connect, _utcnow

    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row:
            return row["id"]
        cursor = conn.execute(
            "INSERT INTO users (username, created_at) VALUES (?, ?)",
            (username, _utcnow()),
        )
        return cursor.lastrowid


def _create_session_for_user(db_path: Path, user_id: int, title: str) -> int:
    """Crée une session pour un utilisateur spécifique."""
    from citadelle_memory import _connect, _utcnow

    now = _utcnow()
    with _connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO sessions (user_id, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, title, now, now),
        )
        return cursor.lastrowid


def test_list_sessions_for_user_empty():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        init_db(db_path)
        assert list_sessions_for_user(999, db_path=db_path) == []


def test_list_sessions_for_user_isolated():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        alice = _create_user(db_path, "alice")
        bob = _create_user(db_path, "bob")
        alice_session = _create_session_for_user(db_path, alice, "Alice chat")
        bob_session = _create_session_for_user(db_path, bob, "Bob chat")
        add_message(alice_session, "user", "Alice question", db_path=db_path)
        add_message(alice_session, "assistant", "Alice answer", db_path=db_path)
        add_message(bob_session, "user", "Bob question", db_path=db_path)

        alice_sessions = list_sessions_for_user(alice, db_path=db_path)
        assert len(alice_sessions) == 1
        assert alice_sessions[0]["id"] == alice_session
        assert alice_sessions[0]["title"] == "Alice chat"
        assert alice_sessions[0]["message_count"] == 2

        bob_sessions = list_sessions_for_user(bob, db_path=db_path)
        assert len(bob_sessions) == 1
        assert bob_sessions[0]["id"] == bob_session
        assert bob_sessions[0]["message_count"] == 1


def test_get_session_for_user_own():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        alice = _create_user(db_path, "alice")
        session_id = _create_session_for_user(db_path, alice, "Test")
        result = get_session_for_user(alice, session_id, db_path=db_path)
        assert result is not None
        assert result["id"] == session_id
        assert result["user_id"] == alice


def test_get_session_for_user_other():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        alice = _create_user(db_path, "alice")
        bob = _create_user(db_path, "bob")
        session_id = _create_session_for_user(db_path, alice, "Alice session")
        assert get_session_for_user(bob, session_id, db_path=db_path) is None
        assert get_session_for_user(bob, 999, db_path=db_path) is None


def test_get_messages_for_user_isolated():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        alice = _create_user(db_path, "alice")
        bob = _create_user(db_path, "bob")
        session_id = _create_session_for_user(db_path, alice, "Alice")
        add_message(session_id, "user", "Question Alice", db_path=db_path)
        add_message(session_id, "assistant", "Réponse Alice", db_path=db_path)

        alice_messages = get_messages_for_user(alice, session_id, db_path=db_path)
        assert len(alice_messages) == 2
        assert alice_messages[0]["content"] == "Question Alice"
        assert get_messages_for_user(bob, session_id, db_path=db_path) == []
        assert get_messages_for_user(alice, 999, db_path=db_path) == []


def test_get_messages_for_user_limit():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        alice = _create_user(db_path, "alice")
        session_id = _create_session_for_user(db_path, alice, "Test")
        for index in range(5):
            add_message(session_id, "user", f"msg{index}", db_path=db_path)
        recent = get_messages_for_user(
            alice,
            session_id,
            limit=2,
            db_path=db_path,
        )
        assert len(recent) == 2
        assert recent[0]["content"] == "msg3"
        assert recent[1]["content"] == "msg4"


def run_all():
    tests = [
        test_list_sessions_for_user_empty,
        test_list_sessions_for_user_isolated,
        test_get_session_for_user_own,
        test_get_session_for_user_other,
        test_get_messages_for_user_isolated,
        test_get_messages_for_user_limit,
    ]
    passed = 0
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
        passed += 1
    print(f"ALL {passed} TESTS PASSED")


if __name__ == "__main__":
    run_all()
