"""Helpers partagés pour les tests HTTP et SQLite.

Centralise les redirections, les comptes de test, les logins et le contexte HTTP.
"""

import importlib
import json
import sqlite3
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from http.cookies import SimpleCookie
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

citadelle_memory = importlib.import_module("citadelle_memory")
login_server = importlib.import_module("login_server")
SESSION_COOKIE_NAME = login_server.SESSION_COOKIE_NAME


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Empêche urllib de suivre les redirections HTTP."""

    def redirect_request(self, request, file, code, message, headers, new_url):
        return None


def open_no_redirect(opener, request):
    """Retourne aussi les réponses HTTP d'erreur au lieu de lever HTTPError."""
    try:
        return opener.open(request, timeout=5)
    except urllib.error.HTTPError as response:
        return response


def create_test_user(
    db_path: Path,
    username: str,
    password: str,
    role: str = "user",
    must_change: int = 0,
    is_active: int = 1,
) -> int:
    """Insère un compte V3 de test et retourne son identifiant."""
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "INSERT INTO users "
            "(username, password_hash, role, is_active, "
            "must_change_password, created_at, last_login_at) "
            "VALUES (?, ?, ?, ?, ?, ?, NULL)",
            (
                username,
                citadelle_memory.hash_password(password),
                role,
                is_active,
                must_change,
                citadelle_memory._utcnow(),
            ),
        )
        conn.commit()
        if cursor.lastrowid is None:
            raise sqlite3.DatabaseError("Impossible de récupérer l'identifiant")
        return cursor.lastrowid
    finally:
        conn.close()


def login_as(opener, base_url: str, username: str, password: str) -> str:
    """S'authentifie par HTTP et retourne le cookie de session."""
    request = urllib.request.Request(
        f"{base_url}/login",
        data=urlencode({"username": username, "password": password}).encode(
            "utf-8"
        ),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    response = open_no_redirect(opener, request)
    assert response.code == 302, f"Login failed: {response.code}"
    location = response.headers.get("Location", "")
    assert location in ("/", "/change-password"), (
        f"Unexpected Location: {location}"
    )
    cookie = SimpleCookie()
    cookie.load(response.headers.get("Set-Cookie", ""))
    response.close()
    assert SESSION_COOKIE_NAME in cookie, "Session cookie missing"
    return cookie[SESSION_COOKIE_NAME].value


def api_post(opener, base_url: str, path: str, token: str, body: dict | None = None):
    """Envoie une requête JSON authentifiée à une route API."""
    data = json.dumps(body).encode("utf-8") if body is not None else b""
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers={
            "Cookie": f"{SESSION_COOKIE_NAME}={token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    return open_no_redirect(opener, request)


@contextmanager
def api_test_context():
    """Démarre un proxy HTTP temporaire sur une base SQLite migrée en V3."""
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
                opener = urllib.request.build_opener(NoRedirect())
                yield f"http://127.0.0.1:{port}", opener, db_path
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
                login_server.SESSIONS.clear()
                login_server.MUST_CHANGE.clear()


login_context = api_test_context
