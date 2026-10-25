"""Tests for the aggregated inference indicators endpoint."""

import json
import sys
from datetime import datetime, timedelta, timezone
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


def _insert_metric(
    db_path: Path,
    user_id: int,
    duration_ms: int,
    status: str,
    completion_tokens: int | None,
    timestamp: str | None = None,
) -> None:
    with citadelle_memory._connect(db_path) as conn:
        conn.execute(
            "INSERT INTO inference_metrics "
            "(user_id, timestamp, duration_ms, status, completion_tokens) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                user_id,
                timestamp or citadelle_memory._utcnow(),
                duration_ms,
                status,
                completion_tokens,
            ),
        )


def test_indicators_requires_auth():
    with api_test_context() as (base_url, opener, db_path):
        _prepare_metrics(db_path)
        with _api_get(opener, base_url, "/api/indicators") as response:
            assert response.code == 401


def test_indicators_admin_aggregates_all_metrics():
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
        _insert_metric(db_path, alice_id, 1000, "ok", 10)
        _insert_metric(db_path, bob_id, 2000, "ok", 40)
        _insert_metric(db_path, bob_id, 3000, "error", None)
        token = login_as(opener, base_url, "admin", "secret123")
        login_as(opener, base_url, "alice", "secret123")
        login_as(opener, base_url, "bob", "secret123")

        with _api_get(
            opener,
            base_url,
            "/api/indicators?window=24h",
            token,
        ) as response:
            assert response.code == 200
            data = json.loads(response.read())

        assert data == {
            "window": "24h",
            "total_inferences": 3,
            "tokens_per_second_avg": 16.67,
            "latency_avg_ms": 2000.0,
            "latency_p95_ms": 3000,
            "error_rate": 0.333,
            "active_sessions": 3,
            "avg_time_per_request_ms": 2000.0,
        }
        with _api_get(opener, base_url, "/admin", token) as response:
            admin_page = response.read().decode("utf-8")
        assert 'id="admin-indicators-heading"' in admin_page
        assert 'id="admin-total-inferences"' in admin_page
        assert 'id="admin-average-request-time"' in admin_page
        assert "setInterval(loadIndicators, 5000)" in admin_page


def test_indicators_user_filters_metrics_and_active_sessions():
    with api_test_context() as (base_url, opener, db_path):
        _prepare_metrics(db_path)
        alice_id = create_test_user(db_path, "alice", "secret123")
        bob_id = create_test_user(db_path, "bob", "secret123")
        _insert_metric(db_path, alice_id, 1000, "ok", 20)
        _insert_metric(db_path, alice_id, 3000, "error", None)
        _insert_metric(db_path, bob_id, 1000, "ok", 100)
        alice_token = login_as(opener, base_url, "alice", "secret123")
        login_as(opener, base_url, "bob", "secret123")

        with _api_get(
            opener,
            base_url,
            "/api/indicators",
            alice_token,
        ) as response:
            assert response.code == 200
            data = json.loads(response.read())

        assert data["total_inferences"] == 2
        assert data["tokens_per_second_avg"] == 20.0
        assert data["latency_avg_ms"] == 2000.0
        assert data["latency_p95_ms"] == 3000
        assert data["error_rate"] == 0.5
        assert data["active_sessions"] == 1
        with _api_get(opener, base_url, "/settings", alice_token) as response:
            settings_page = response.read().decode("utf-8")
        assert 'id="user-indicators-heading"' in settings_page
        assert 'id="user-indicators-tbody"' in settings_page
        assert "setInterval(loadIndicators, 5000)" in settings_page


def test_indicators_window_and_invalid_window_default():
    with api_test_context() as (base_url, opener, db_path):
        _prepare_metrics(db_path)
        user_id = create_test_user(
            db_path,
            "admin",
            "secret123",
            role="admin",
        )
        now = datetime.now(timezone.utc)
        _insert_metric(
            db_path,
            user_id,
            100,
            "ok",
            1,
            (now - timedelta(days=20)).isoformat(),
        )
        _insert_metric(
            db_path,
            user_id,
            200,
            "ok",
            2,
            (now - timedelta(days=5)).isoformat(),
        )
        _insert_metric(db_path, user_id, 300, "ok", 3, now.isoformat())
        token = login_as(opener, base_url, "admin", "secret123")

        with _api_get(
            opener,
            base_url,
            "/api/indicators?window=7d",
            token,
        ) as response:
            seven_days = json.loads(response.read())
        with _api_get(
            opener,
            base_url,
            "/api/indicators?window=30d",
            token,
        ) as response:
            thirty_days = json.loads(response.read())
        with _api_get(
            opener,
            base_url,
            "/api/indicators?window=invalid",
            token,
        ) as response:
            default_window = json.loads(response.read())

        assert seven_days["window"] == "7d"
        assert seven_days["total_inferences"] == 2
        assert thirty_days["window"] == "30d"
        assert thirty_days["total_inferences"] == 3
        assert default_window["window"] == "24h"
        assert default_window["total_inferences"] == 1


def test_indicators_has_no_sensitive_fields_and_handles_empty_data():
    with api_test_context() as (base_url, opener, db_path):
        _prepare_metrics(db_path)
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")

        with _api_get(
            opener,
            base_url,
            "/api/indicators",
            token,
        ) as response:
            assert response.code == 200
            data = json.loads(response.read())

        assert not {"prompt", "response", "password"} & data.keys()
        assert data["total_inferences"] == 0
        assert data["tokens_per_second_avg"] is None
        assert data["latency_avg_ms"] == 0
        assert data["latency_p95_ms"] == 0
        assert data["error_rate"] == 0
        assert data["avg_time_per_request_ms"] == 0


def run_all():
    tests = [
        test_indicators_requires_auth,
        test_indicators_admin_aggregates_all_metrics,
        test_indicators_user_filters_metrics_and_active_sessions,
        test_indicators_window_and_invalid_window_default,
        test_indicators_has_no_sensitive_fields_and_handles_empty_data,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
