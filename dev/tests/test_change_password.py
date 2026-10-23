"""Tests pour POST /change-password et le gating des sessions restreintes."""

import importlib
import json
import sqlite3
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

citadelle_memory = importlib.import_module("citadelle_memory")
login_server = importlib.import_module("login_server")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        return None


def open_no_redirect(opener, request):
    try:
        return opener.open(request, timeout=5)
    except urllib.error.HTTPError as response:
        return response


@contextmanager
def change_context():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        with (
            patch.object(login_server, "MEMORY_DB_PATH", db_path),
            patch.object(citadelle_memory, "DB_PATH", db_path),
        ):
            citadelle_memory.migrate_to_v3(db_path)
            login_server.SESSIONS.clear()
            login_server.MUST_CHANGE.clear()
            server = HTTPServer(("127.0.0.1", 0), login_server.RequestHandler)
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                yield f"http://127.0.0.1:{port}", db_path
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
                login_server.SESSIONS.clear()
                login_server.MUST_CHANGE.clear()


def create_user_with_token(
    db_path: Path,
    username: str = "alice",
    password: str = "old12345",
    must_change: int = 1,
) -> tuple[int, str]:
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, role, is_active, "
            "must_change_password, created_at) "
            "VALUES (?, ?, 'user', 1, ?, ?)",
            (
                username,
                citadelle_memory.hash_password(password),
                must_change,
                citadelle_memory._utcnow(),
            ),
        )
        conn.commit()
        user_id = int(cursor.lastrowid)
    finally:
        conn.close()
    token = login_server.create_session_token(
        user_id, must_change=bool(must_change)
    )
    return user_id, token


def post_change(opener, base_url: str, token: str, **fields):
    request = urllib.request.Request(
        f"{base_url}/change-password",
        data=urlencode(fields).encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": f"{login_server.SESSION_COOKIE_NAME}={token}",
        },
        method="POST",
    )
    return open_no_redirect(opener, request)


def test_change_password_ok():
    with change_context() as (base_url, db_path):
        user_id, token = create_user_with_token(db_path)
        opener = urllib.request.build_opener(NoRedirect())
        with opener.open(
            f"{base_url}/change-password",
            timeout=5,
        ) as response:
            assert response.code == 200
            assert b'action="/change-password"' in response.read()

        with open_no_redirect(
            opener,
            urllib.request.Request(
                f"{base_url}/",
                headers={
                    "Cookie": f"{login_server.SESSION_COOKIE_NAME}={token}"
                },
            ),
        ) as response:
            assert response.code == 302
            assert response.headers.get("Location") == "/change-password"

        with open_no_redirect(
            opener,
            urllib.request.Request(
                f"{base_url}/api/sessions",
                headers={
                    "Cookie": f"{login_server.SESSION_COOKIE_NAME}={token}"
                },
            ),
        ) as response:
            assert response.code == 403
            assert json.loads(response.read())["error"] == (
                "Changement de mot de passe requis"
            )

        conn = sqlite3.connect(str(db_path))
        try:
            now = citadelle_memory._utcnow()
            cursor = conn.execute(
                "INSERT INTO sessions (user_id, title, created_at, updated_at) "
                "VALUES (?, ?, ?, ?)",
                (user_id, "Restricted", now, now),
            )
            session_id = int(cursor.lastrowid)
            conn.commit()
        finally:
            conn.close()
        for method, path, data in (
            ("GET", f"/api/sessions/{session_id}/messages", None),
            ("POST", "/api/sessions", b"{}"),
            ("POST", f"/api/sessions/{session_id}/messages", b"{}"),
        ):
            headers = {"Cookie": f"{login_server.SESSION_COOKIE_NAME}={token}"}
            if data is not None:
                headers["Content-Type"] = "application/json"
            request = urllib.request.Request(
                f"{base_url}{path}", data=data, headers=headers, method=method
            )
            with open_no_redirect(opener, request) as response:
                assert response.code == 403

        response = post_change(
            opener,
            base_url,
            token,
            old_password="old12345",
            new_password="new12345",
            new_password_confirm="new12345",
        )
        assert response.code == 302
        assert response.headers.get("Location") == "/"
        assert login_server.MUST_CHANGE[token] is False
        conn = sqlite3.connect(str(db_path))
        try:
            row = conn.execute(
                "SELECT password_hash, must_change_password "
                "FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        finally:
            conn.close()
        assert row[1] == 0
        assert citadelle_memory.verify_password("new12345", row[0])
        request = urllib.request.Request(
            f"{base_url}/logout",
            data=b"",
            headers={
                "Cookie": f"{login_server.SESSION_COOKIE_NAME}={token}"
            },
            method="POST",
        )
        with open_no_redirect(opener, request) as response:
            assert response.code == 302
        assert token not in login_server.SESSIONS
        assert token not in login_server.MUST_CHANGE


def test_post_body_consumed_before_auth_rejection():
    with change_context() as (base_url, db_path):
        _, token = create_user_with_token(db_path)
        opener = urllib.request.build_opener(NoRedirect())
        for _ in range(100):
            for request_token, path, expected_status, expected_error in (
                (
                    token,
                    "/api/sessions/1/messages",
                    403,
                    "Changement de mot de passe requis",
                ),
                (None, "/api/sessions/1/messages", 401, "Non authentifié"),
            ):
                headers = {"Content-Type": "application/json"}
                if request_token is not None:
                    headers["Cookie"] = (
                        f"{login_server.SESSION_COOKIE_NAME}={request_token}"
                    )
                request = urllib.request.Request(
                    f"{base_url}{path}",
                    data=b"{}",
                    headers=headers,
                    method="POST",
                )
                with open_no_redirect(opener, request) as response:
                    assert response.code == expected_status
                    assert json.loads(response.read())["error"] == expected_error


def test_change_password_old_wrong():
    with change_context() as (base_url, db_path):
        _, token = create_user_with_token(db_path)
        opener = urllib.request.build_opener(NoRedirect())
        response = post_change(
            opener,
            base_url,
            token,
            old_password="wrong123",
            new_password="new12345",
            new_password_confirm="new12345",
        )
        assert response.code == 401


def test_change_password_short():
    with change_context() as (base_url, db_path):
        _, token = create_user_with_token(db_path)
        opener = urllib.request.build_opener(NoRedirect())
        response = post_change(
            opener,
            base_url,
            token,
            old_password="old12345",
            new_password="short",
            new_password_confirm="short",
        )
        assert response.code == 400


def test_change_password_not_required():
    with change_context() as (base_url, db_path):
        _, token = create_user_with_token(db_path, must_change=0)
        opener = urllib.request.build_opener(NoRedirect())
        response = post_change(
            opener,
            base_url,
            token,
            old_password="old12345",
            new_password="new12345",
            new_password_confirm="new12345",
        )
        assert response.code == 403


def run_all():
    tests = [
        test_change_password_ok,
        test_post_body_consumed_before_auth_rejection,
        test_change_password_old_wrong,
        test_change_password_short,
        test_change_password_not_required,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()