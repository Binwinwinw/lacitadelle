"""Tests des routes d'administration en lecture seule."""

import json
import sys
from pathlib import Path
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from _helpers import (
    SESSION_COOKIE_NAME,
    api_test_context,
    create_test_user,
    login_as,
    open_no_redirect,
)


def api_get(opener, base_url: str, path: str, token: str | None = None):
    headers = {}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    request = Request(
        f"{base_url}{path}",
        headers=headers,
    )
    return open_no_redirect(opener, request)


def admin_test_context():
    return api_test_context()


def test_get_admin_requires_auth():
    with admin_test_context() as (base_url, opener, _):
        with api_get(opener, base_url, "/admin") as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/login"


def test_get_admin_user_forbidden():
    with admin_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")

        with api_get(opener, base_url, "/admin", token) as response:
            assert response.code == 403

        with api_get(opener, base_url, "/api/me", token) as response:
            user = json.loads(response.read().decode("utf-8"))
        assert user["role"] == "user"


def test_get_admin_admin_ok():
    with admin_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123", role="admin")
        token = login_as(opener, base_url, "alice", "secret123")

        with api_get(opener, base_url, "/admin", token) as response:
            assert response.code == 200
            page = response.read().decode("utf-8")
        assert "Administration" in page
        assert "Utilisateurs" in page

        with api_get(opener, base_url, "/api/me", token) as response:
            current_user = json.loads(response.read().decode("utf-8"))
        assert current_user == {"username": "alice", "role": "admin"}


def test_api_admin_users_requires_auth():
    with admin_test_context() as (base_url, opener, _):
        with api_get(opener, base_url, "/api/admin/users") as response:
            assert response.code == 401
            assert json.loads(response.read().decode("utf-8")) == {
                "error": "Non authentifié"
            }


def test_api_admin_users_user_forbidden():
    with admin_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")

        with api_get(
            opener,
            base_url,
            "/api/admin/users",
            token,
        ) as response:
            assert response.code == 403
            assert json.loads(response.read())["error"] == (
                "Accès réservé à l'administration"
            )


def test_api_admin_users_admin_ok():
    with admin_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "admin", "secret123", role="admin")
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "admin", "secret123")

        with api_get(
            opener,
            base_url,
            "/api/admin/users",
            token,
        ) as response:
            assert response.code == 200
            result = json.loads(response.read().decode("utf-8"))
        assert [user["username"] for user in result["users"]] == [
            "admin",
            "alice",
        ]


def test_api_admin_users_no_password_hash():
    with admin_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "admin", "secret123", role="admin")
        token = login_as(opener, base_url, "admin", "secret123")

        with api_get(
            opener,
            base_url,
            "/api/admin/users",
            token,
        ) as response:
            result = json.loads(response.read().decode("utf-8"))
        assert all("password_hash" not in user for user in result["users"])


def test_api_admin_users_one_admin_active():
    with admin_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "admin", "secret123", role="admin")
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "admin", "secret123")

        with api_get(
            opener,
            base_url,
            "/api/admin/users",
            token,
        ) as response:
            result = json.loads(response.read().decode("utf-8"))
        assert result["summary"]["active_admins"] == 1


def test_must_change_password_blocks_admin():
    with admin_test_context() as (base_url, opener, db_path):
        create_test_user(
            db_path,
            "admin",
            "secret123",
            role="admin",
            must_change=1,
        )
        token = login_as(opener, base_url, "admin", "secret123")

        with api_get(opener, base_url, "/admin", token) as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/change-password"


def run_all():
    tests = [
        test_get_admin_requires_auth,
        test_get_admin_user_forbidden,
        test_get_admin_admin_ok,
        test_api_admin_users_requires_auth,
        test_api_admin_users_user_forbidden,
        test_api_admin_users_admin_ok,
        test_api_admin_users_no_password_hash,
        test_api_admin_users_one_admin_active,
        test_must_change_password_blocks_admin,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
