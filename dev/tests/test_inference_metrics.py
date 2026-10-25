"""Tests for inference metadata persistence and lifecycle."""

import io
import json
import sqlite3
import sys
import tempfile
import urllib.error
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import citadelle_memory
import login_server


def _prepare_db(db_path: Path) -> None:
    citadelle_memory.init_db(db_path)
    with citadelle_memory._connect(db_path) as conn:
        table = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='inference_metrics'"
        ).fetchone()
    assert table is not None
    citadelle_memory.migrate_to_v5(db_path)


def _create_user(db_path: Path, username: str) -> int:
    with citadelle_memory._connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, created_at) VALUES (?, ?)",
            (username, citadelle_memory._utcnow()),
        )
        return cursor.lastrowid


def _create_session(db_path: Path, user_id: int) -> int:
    now = citadelle_memory._utcnow()
    with citadelle_memory._connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO sessions "
            "(user_id, created_at, updated_at) VALUES (?, ?, ?)",
            (user_id, now, now),
        )
        return cursor.lastrowid


def test_record_inference_is_scoped_to_user():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        _prepare_db(db_path)
        alice_id = _create_user(db_path, "alice")
        bob_id = _create_user(db_path, "bob")
        alice_session = _create_session(db_path, alice_id)

        citadelle_memory.record_inference(
            alice_id,
            alice_session,
            duration_ms=37,
            status="ok",
            prompt_tokens=12,
            completion_tokens=4,
            db_path=db_path,
        )
        citadelle_memory.record_inference(
            bob_id,
            None,
            duration_ms=9,
            status="error",
            prompt_tokens=None,
            completion_tokens=None,
            db_path=db_path,
        )

        with citadelle_memory._connect(db_path) as conn:
            alice_rows = conn.execute(
                "SELECT user_id, session_id, duration_ms, status, "
                "prompt_tokens, completion_tokens "
                "FROM inference_metrics WHERE user_id = ?",
                (alice_id,),
            ).fetchall()
            bob_rows = conn.execute(
                "SELECT user_id, session_id, duration_ms, status "
                "FROM inference_metrics WHERE user_id = ?",
                (bob_id,),
            ).fetchall()

        assert [tuple(row) for row in alice_rows] == [
            (alice_id, alice_session, 37, "ok", 12, 4)
        ]
        assert [tuple(row) for row in bob_rows] == [
            (bob_id, None, 9, "error")
        ]


def test_inference_cascade_on_user_delete():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        _prepare_db(db_path)
        user_id = _create_user(db_path, "alice")
        session_id = _create_session(db_path, user_id)
        citadelle_memory.record_inference(
            user_id,
            session_id,
            duration_ms=20,
            status="ok",
            db_path=db_path,
        )

        with citadelle_memory._connect(db_path) as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            count = conn.execute(
                "SELECT COUNT(*) FROM inference_metrics"
            ).fetchone()[0]

        assert count == 0


def test_inference_session_delete_sets_session_null():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        _prepare_db(db_path)
        user_id = _create_user(db_path, "alice")
        session_id = _create_session(db_path, user_id)
        citadelle_memory.record_inference(
            user_id,
            session_id,
            duration_ms=20,
            status="ok",
            db_path=db_path,
        )

        with citadelle_memory._connect(db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            row = conn.execute(
                "SELECT user_id, session_id FROM inference_metrics"
            ).fetchone()

        assert tuple(row) == (user_id, None)


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_call_llamafile_records_usage_without_content_and_is_best_effort():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        _prepare_db(db_path)
        user_id = _create_user(db_path, "alice")
        session_id = _create_session(db_path, user_id)
        payload = {
            "choices": [
                {"message": {"content": "Réponse simulée"}},
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 5},
        }
        messages = [{"role": "user", "content": "Demande simulée"}]

        with patch.object(login_server, "MEMORY_DB_PATH", db_path):
            with patch.object(
                login_server.urllib.request,
                "urlopen",
                return_value=_FakeResponse(payload),
            ):
                result = login_server.call_llamafile(
                    messages,
                    user_id,
                    session_id,
                )

            with citadelle_memory._connect(db_path) as conn:
                row = conn.execute(
                    "SELECT user_id, session_id, duration_ms, status, "
                    "prompt_tokens, completion_tokens, timestamp "
                    "FROM inference_metrics"
                ).fetchone()
                columns = {
                    item["name"]
                    for item in conn.execute(
                        "PRAGMA table_info(inference_metrics)"
                    )
                }

            assert result == "Réponse simulée"
            assert row["user_id"] == user_id
            assert row["session_id"] == session_id
            assert isinstance(row["duration_ms"], int)
            assert row["duration_ms"] >= 0
            assert row["status"] == "ok"
            assert row["prompt_tokens"] == 12
            assert row["completion_tokens"] == 5
            assert row["timestamp"]
            assert "prompt" not in columns
            assert "response" not in columns

            with patch.object(
                login_server.urllib.request,
                "urlopen",
                side_effect=urllib.error.URLError(
                    TimeoutError("simulated timeout")
                ),
            ):
                try:
                    login_server.call_llamafile(
                        messages,
                        user_id,
                        session_id,
                    )
                except login_server.LoginError:
                    pass
                else:
                    raise AssertionError("Timeout should raise LoginError")

            with citadelle_memory._connect(db_path) as conn:
                timeout_row = conn.execute(
                    "SELECT status, prompt_tokens, completion_tokens "
                    "FROM inference_metrics WHERE status = 'timeout'"
                ).fetchone()
            assert tuple(timeout_row) == ("timeout", None, None)

            with patch.object(
                login_server.urllib.request,
                "urlopen",
                return_value=_FakeResponse(payload),
            ), patch.object(
                login_server,
                "record_inference",
                side_effect=sqlite3.OperationalError("unavailable"),
            ), redirect_stderr(io.StringIO()) as stderr:
                result = login_server.call_llamafile(
                    messages,
                    user_id,
                    session_id,
                )

            assert result == "Réponse simulée"
            assert "OperationalError" in stderr.getvalue()
            assert "Demande simulée" not in stderr.getvalue()
            assert "Réponse simulée" not in stderr.getvalue()


def run_all():
    tests = [
        test_record_inference_is_scoped_to_user,
        test_inference_cascade_on_user_delete,
        test_inference_session_delete_sets_session_null,
        test_call_llamafile_records_usage_without_content_and_is_best_effort,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
