"""Tests pour la page de réglages et les préférences utilisateur."""

import importlib
import json
import sqlite3
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

citadelle_memory = importlib.import_module("citadelle_memory")
from _helpers import (
    SESSION_COOKIE_NAME,
    api_post,
    api_test_context,
    create_test_user,
    login_as,
    open_no_redirect,
)


@contextmanager
def settings_test_context():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v4(db_path)
        yield base_url, opener, db_path


def api_get(opener, base_url: str, path: str, token: str | None = None):
    headers = {}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    return open_no_redirect(
        opener,
        Request(f"{base_url}{path}", headers=headers),
    )


def test_get_settings_requires_auth():
    with settings_test_context() as (base_url, opener, _):
        with api_get(opener, base_url, "/settings") as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/login"


def test_get_settings_ok():
    with settings_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")

        with api_get(opener, base_url, "/settings", token) as response:
            assert response.code == 200
            page = response.read().decode("utf-8")
        assert "Réglages" in page
        assert "Préférences" in page

        with api_get(opener, base_url, "/api/preferences", token) as response:
            preferences = json.loads(response.read().decode("utf-8"))
        assert preferences == {
            "username": "alice",
            "theme": "light",
            "font_size": "normal",
        }


def test_get_settings_must_change_password():
    with settings_test_context() as (base_url, opener, db_path):
        create_test_user(
            db_path,
            "alice",
            "secret123",
            must_change=1,
        )
        token = login_as(opener, base_url, "alice", "secret123")

        with api_get(opener, base_url, "/settings", token) as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/change-password"


def test_post_preferences_ok():
    with settings_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")

        with api_post(
            opener,
            base_url,
            "/settings/preferences",
            token,
            {"theme": "dark", "font_size": "large"},
        ) as response:
            assert response.code == 200
            assert json.loads(response.read().decode("utf-8")) == {
                "saved": True,
                "theme": "dark",
                "font_size": "large",
            }

        with api_get(opener, base_url, "/api/preferences", token) as response:
            preferences = json.loads(response.read().decode("utf-8"))
        assert preferences["theme"] == "dark"
        assert preferences["font_size"] == "large"


def test_post_preferences_invalid_theme():
    with settings_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")

        with api_post(
            opener,
            base_url,
            "/settings/preferences",
            token,
            {"theme": "system", "font_size": "normal"},
        ) as response:
            assert response.code == 400
            assert json.loads(response.read().decode("utf-8")) == {
                "error": "Thème invalide"
            }


def test_post_preferences_invalid_font_size():
    with settings_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")

        with api_post(
            opener,
            base_url,
            "/settings/preferences",
            token,
            {"theme": "dark", "font_size": "huge"},
        ) as response:
            assert response.code == 400
            assert json.loads(response.read().decode("utf-8")) == {
                "error": "Taille de texte invalide"
            }


def test_post_preferences_requires_auth():
    with settings_test_context() as (base_url, opener, _):
        request = Request(
            f"{base_url}/settings/preferences",
            data=json.dumps(
                {"theme": "dark", "font_size": "large"}
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with open_no_redirect(opener, request) as response:
            assert response.code == 401
            assert json.loads(response.read().decode("utf-8")) == {
                "error": "Non authentifié"
            }


def test_preferences_migration_idempotent():
    with tempfile.TemporaryDirectory() as temp_dir:
        v1_db_path = Path(temp_dir) / "v1.db"
        citadelle_memory.init_db(v1_db_path)
        citadelle_memory.migrate_to_v4(v1_db_path)
        citadelle_memory.migrate_to_v4(v1_db_path)

        v3_db_path = Path(temp_dir) / "v3.db"
        citadelle_memory.migrate_to_v3(v3_db_path)
        citadelle_memory.migrate_to_v4(v3_db_path)
        citadelle_memory.migrate_to_v4(v3_db_path)

        for db_path in (v1_db_path, v3_db_path):
            conn = sqlite3.connect(str(db_path))
            try:
                tables = conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table' AND name = 'preferences'"
                ).fetchall()
                columns = {
                    row[1]
                    for row in conn.execute(
                        "PRAGMA table_info(preferences)"
                    ).fetchall()
                }
            finally:
                conn.close()
            assert len(tables) == 1
            assert {
                "user_id",
                "theme",
                "font_size",
                "updated_at",
            } <= columns


def test_preferences_per_user():
    with settings_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        create_test_user(db_path, "bob", "secret123")
        alice_token = login_as(opener, base_url, "alice", "secret123")
        bob_token = login_as(opener, base_url, "bob", "secret123")

        with api_post(
            opener,
            base_url,
            "/settings/preferences",
            alice_token,
            {"theme": "dark", "font_size": "small"},
        ) as response:
            assert response.code == 200
            response.read()
        with api_post(
            opener,
            base_url,
            "/settings/preferences",
            bob_token,
            {"theme": "light", "font_size": "large"},
        ) as response:
            assert response.code == 200
            response.read()

        with api_get(opener, base_url, "/api/preferences", alice_token) as response:
            alice_preferences = json.loads(response.read().decode("utf-8"))
        with api_get(opener, base_url, "/api/preferences", bob_token) as response:
            bob_preferences = json.loads(response.read().decode("utf-8"))
        assert (alice_preferences["theme"], alice_preferences["font_size"]) == (
            "dark",
            "small",
        )
        assert (bob_preferences["theme"], bob_preferences["font_size"]) == (
            "light",
            "large",
        )
