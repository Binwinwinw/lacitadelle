"""Tests for the authenticated inference logs endpoint."""

import json
import sys
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


def _api_get(opener, base_url, path, token=None):
    headers = {}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    return open_no_redirect(opener, Request(f"{base_url}{path}", headers=headers))


def _prepare_metrics(db_path: Path) -> None:
    citadelle_memory.migrate_to_v5(db_path)


def _record_metric(db_path: Path, user_id: int, status: str = "ok") -> None:
    citadelle_memory.record_inference(
        user_id,
        None,
        duration_ms=12,
        status=status,
        prompt_tokens=8,
        completion_tokens=3,
        db_path=db_path,
    )


def test_logs_tail_requires_auth():
    with api_test_context() as (base_url, opener, db_path):
        _prepare_metrics(db_path)
        with _api_get(opener, base_url, "/api/logs/tail") as response:
            assert response.code == 401


def test_logs_tail_admin_sees_all():
    with api_test_context() as (base_url, opener, db_path):
        _prepare_metrics(db_path)
        create_test_user(
            db_path,
            "admin",
            "secret123",
            role="admin",
        )
        alice_id = create_test_user(db_path, "alice", "secret123")
        bob_id = create_test_user(db_path, "bob", "secret123")
        _record_metric(db_path, alice_id)
        _record_metric(db_path, bob_id)
        token = login_as(opener, base_url, "admin", "secret123")

        with _api_get(
            opener,
            base_url,
            "/api/logs/tail",
            token,
        ) as response:
            assert response.code == 200
            logs = json.loads(response.read())["logs"]

        assert len(logs) == 2
        assert {log["username"] for log in logs} == {"alice", "bob"}
        assert all(log["id"] is not None for log in logs)
        with _api_get(opener, base_url, "/admin", token) as response:
            admin_page = response.read().decode("utf-8")
        assert 'id="logs-panel"' in admin_page
        assert 'id="logs-tbody"' in admin_page
        assert "setInterval(loadLogs, 5000)" in admin_page


def test_logs_tail_user_sees_only_own_metrics():
    with api_test_context() as (base_url, opener, db_path):
        _prepare_metrics(db_path)
        alice_id = create_test_user(db_path, "alice", "secret123")
        bob_id = create_test_user(db_path, "bob", "secret123")
        _record_metric(db_path, alice_id)
        _record_metric(db_path, bob_id)
        token = login_as(opener, base_url, "alice", "secret123")

        with _api_get(
            opener,
            base_url,
            "/api/logs/tail",
            token,
        ) as response:
            assert response.code == 200
            logs = json.loads(response.read())["logs"]

        assert len(logs) == 1
        assert logs[0]["username"] == "alice"
        with _api_get(opener, base_url, "/settings", token) as response:
            settings_page = response.read().decode("utf-8")
        assert 'id="user-logs-section"' in settings_page
        assert 'id="user-logs-tbody"' in settings_page
        assert "setInterval(loadLogs, 5000)" in settings_page


def test_logs_tail_lines_parameter_is_bounded():
    with api_test_context() as (base_url, opener, db_path):
        _prepare_metrics(db_path)
        user_id = create_test_user(db_path, "admin", "secret123", role="admin")
        now = citadelle_memory._utcnow()
        with citadelle_memory._connect(db_path) as conn:
            conn.executemany(
                "INSERT INTO inference_metrics "
                "(user_id, timestamp, duration_ms, status) "
                "VALUES (?, ?, ?, 'ok')",
                [
                    (user_id, now, index)
                    for index in range(501)
                ],
            )
        token = login_as(opener, base_url, "admin", "secret123")

        with _api_get(
            opener,
            base_url,
            "/api/logs/tail?lines=10",
            token,
        ) as response:
            assert response.code == 200
            ten_logs = json.loads(response.read())["logs"]
        with _api_get(
            opener,
            base_url,
            "/api/logs/tail?lines=10000",
            token,
        ) as response:
            assert response.code == 200
            capped_logs = json.loads(response.read())["logs"]

        assert len(ten_logs) == 10
        assert len(capped_logs) == 500


def test_logs_tail_response_has_no_prompt_or_response():
    with api_test_context() as (base_url, opener, db_path):
        _prepare_metrics(db_path)
        user_id = create_test_user(db_path, "alice", "secret123")
        _record_metric(db_path, user_id)
        token = login_as(opener, base_url, "alice", "secret123")

        with _api_get(
            opener,
            base_url,
            "/api/logs/tail",
            token,
        ) as response:
            assert response.code == 200
            logs = json.loads(response.read())["logs"]

        assert logs
        assert all("prompt" not in log and "response" not in log for log in logs)


def run_all():
    tests = [
        test_logs_tail_requires_auth,
        test_logs_tail_admin_sees_all,
        test_logs_tail_user_sees_only_own_metrics,
        test_logs_tail_lines_parameter_is_bounded,
        test_logs_tail_response_has_no_prompt_or_response,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
