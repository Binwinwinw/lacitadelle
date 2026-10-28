"""HTTP contract tests for the model section in settings."""

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


def _get_model(opener, base_url, token=None):
    headers = {}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    request = Request(f"{base_url}/api/settings/model", headers=headers)
    return open_no_redirect(opener, request)


def _post_model(opener, base_url, token=None):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Cookie"] = f"{SESSION_COOKIE_NAME}={token}"
    request = Request(
        f"{base_url}/api/admin/model",
        data=json.dumps({"model_path": "model.gguf"}).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    return open_no_redirect(opener, request)


def test_settings_serves_model_form_to_authenticated_user():
    with api_test_context() as (base_url, opener, db_path):
        create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        request = Request(
            f"{base_url}/settings",
            headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"},
        )

        with opener.open(request, timeout=5) as response:
            page = response.read().decode("utf-8")

        assert 'id="model-section"' in page
        assert 'id="model-form"' in page
        assert 'id="model-section" class="settings-section"' in page
        assert 'aria-labelledby="model-heading" hidden>' in page
        assert "modelSection.hidden = !isAdmin;" in page


def test_get_model_setting_is_admin_only_and_returns_saved_path():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)

        with _get_model(opener, base_url) as response:
            assert response.code == 401

        create_test_user(db_path, "alice", "secret123")
        user_token = login_as(opener, base_url, "alice", "secret123")
        with _get_model(opener, base_url, user_token) as response:
            assert response.code == 403

        create_test_user(db_path, "admin", "secret123", role="admin")
        admin_token = login_as(opener, base_url, "admin", "secret123")
        citadelle_memory.set_setting(
            "current_model_path",
            "C:/models/model.gguf",
            db_path=db_path,
        )

        with _get_model(opener, base_url, admin_token) as response:
            assert response.code == 200
            assert json.loads(response.read()) == {
                "current_model_path": "C:/models/model.gguf"
            }


def test_post_model_still_requires_admin():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v6(db_path)

        with _post_model(opener, base_url) as response:
            assert response.code == 401

        create_test_user(db_path, "alice", "secret123")
        user_token = login_as(opener, base_url, "alice", "secret123")
        with _post_model(opener, base_url, user_token) as response:
            assert response.code == 403


def run_all():
    tests = [
        test_settings_serves_model_form_to_authenticated_user,
        test_get_model_setting_is_admin_only_and_returns_saved_path,
        test_post_model_still_requires_admin,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
