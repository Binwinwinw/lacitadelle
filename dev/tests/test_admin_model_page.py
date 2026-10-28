"""HTTP tests for the dedicated admin model page."""

import json
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
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


def _request(opener, base_url, path, token=None, form=None):
    headers = {}
    data = None
    method = "GET"
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    if form is not None:
        data = urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        method = "POST"
    request = Request(
        f"{base_url}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    return open_no_redirect(opener, request)


def test_model_page_requires_admin():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)

        with _request(opener, base_url, "/admin/model") as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/login"
        with _request(
            opener,
            base_url,
            "/admin/model",
            form={"model_path": "model.gguf"},
        ) as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/login"

        create_test_user(db_path, "alice", "secret123")
        user_token = login_as(opener, base_url, "alice", "secret123")
        with _request(
            opener,
            base_url,
            "/admin/model",
            user_token,
        ) as response:
            assert response.code == 403
        with _request(
            opener,
            base_url,
            "/admin/model",
            user_token,
            {"model_path": "model.gguf"},
        ) as response:
            assert response.code == 403

        create_test_user(db_path, "admin", "secret123", role="admin")
        admin_token = login_as(opener, base_url, "admin", "secret123")
        with _request(
            opener,
            base_url,
            "/admin/model",
            admin_token,
        ) as response:
            assert response.code == 200
            page = response.read().decode("utf-8")
        assert 'id="model-form"' in page
        assert 'id="model-current"' in page


def test_model_page_displays_current_path():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        create_test_user(db_path, "admin", "secret123", role="admin")
        token = login_as(opener, base_url, "admin", "secret123")

        with _request(
            opener,
            base_url,
            "/admin/model",
            token,
        ) as response:
            page = response.read().decode("utf-8")
        assert "Aucun modèle configuré" in page
        assert 'fetch("/api/settings/model"' in page

        citadelle_memory.set_setting(
            "current_model_path",
            "C:/models/model.gguf",
            db_path=db_path,
        )
        with _request(
            opener,
            base_url,
            "/api/settings/model",
            token,
        ) as response:
            assert response.code == 200
            assert json.loads(response.read()) == {
                "current_model_path": "C:/models/model.gguf"
            }


def test_model_page_post_saves_valid_path():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        create_test_user(db_path, "admin", "secret123", role="admin")
        token = login_as(opener, base_url, "admin", "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "model.gguf"
            model_path.write_bytes(b"gguf")

            with _request(
                opener,
                base_url,
                "/admin/model",
                token,
                {"model_path": str(model_path)},
            ) as response:
                assert response.code == 302
                assert response.headers.get("Location") == "/admin/model?saved=1"

            assert citadelle_memory.get_setting(
                "current_model_path",
                db_path=db_path,
            ) == str(model_path.resolve())


def test_model_page_post_rejects_missing_file_without_setting_path():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        create_test_user(db_path, "admin", "secret123", role="admin")
        token = login_as(opener, base_url, "admin", "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.gguf"
            with _request(
                opener,
                base_url,
                "/admin/model",
                token,
                {"model_path": str(missing_path)},
            ) as response:
                assert response.code == 302
                error = parse_qs(
                    urlparse(response.headers["Location"]).query
                )["error"][0]
                assert "introuvable" in error

        assert citadelle_memory.get_setting(
            "current_model_path",
            db_path=db_path,
        ) is None


def test_model_page_post_rejects_invalid_extension_without_setting_path():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)
        create_test_user(db_path, "admin", "secret123", role="admin")
        token = login_as(opener, base_url, "admin", "secret123")
        with tempfile.TemporaryDirectory() as temp_dir:
            text_path = Path(temp_dir) / "model.txt"
            text_path.write_text("not a GGUF", encoding="utf-8")
            with _request(
                opener,
                base_url,
                "/admin/model",
                token,
                {"model_path": str(text_path)},
            ) as response:
                assert response.code == 302
                error = parse_qs(
                    urlparse(response.headers["Location"]).query
                )["error"][0]
                assert "Extension .gguf requise" == error

        assert citadelle_memory.get_setting(
            "current_model_path",
            db_path=db_path,
        ) is None


def run_all():
    tests = [
        test_model_page_requires_admin,
        test_model_page_displays_current_path,
        test_model_page_post_saves_valid_path,
        test_model_page_post_rejects_missing_file_without_setting_path,
        test_model_page_post_rejects_invalid_extension_without_setting_path,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
