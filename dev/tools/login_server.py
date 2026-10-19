#!/usr/bin/env python3
"""login_server : proxy Python local pour le login multi-utilisateurs V2.

Sert les pages de login et de chat, gère les cookies de session,
filtre les conversations par user_id, et proxy les requêtes de chat
vers llamafile (localhost:8080).

Voir dev/docs/LOGIN_CONTRACT.md pour l'architecture complète.

Usage :
    python dev/tools/login_server.py

Port par défaut : 8081 (loopback uniquement).

Aucune dépendance externe. Python 3.10+ requis.
"""

from __future__ import annotations

import json
import re
import secrets
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citadelle_memory import (
    DB_PATH as MEMORY_DB_PATH,
    add_message,
    create_session,
    create_session_for_user,
    ensure_default_user,
    get_messages,
    get_messages_for_user,
    get_session_for_user,
    init_db,
    list_sessions,
    list_sessions_for_user,
)

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8081
LLAMAFILE_URL = "http://127.0.0.1:8080/v1/chat/completions"
WEB_DIR = Path(__file__).resolve().parent / "web"
MAX_CONTEXT_MESSAGES = 15
SYSTEM_PROMPT = "Tu es Lacitadelle, un assistant IA local. Réponds en français."
SESSION_COOKIE_NAME = "lacitadelle_session"
HTTP_TIMEOUT = 120
SQLITE_TIMEOUT = 5.0
SESSION_MSG_RE = re.compile(r"^/api/sessions/(\d+)/messages$")

# Le contenu est perdu au redémarrage du proxy, conformément au contrat V2.
SESSIONS: dict[str, int] = {}


class LoginError(Exception):
    """Erreur attendue du serveur de login."""


def _get_db_connection() -> sqlite3.Connection:
    """Ouvre une connexion SQLite à memory.db (configurable pour tests)."""
    MEMORY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(MEMORY_DB_PATH), timeout=SQLITE_TIMEOUT)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_session_token(user_id: int) -> str:
    """Crée un token opaque et remplace l'ancien token de l'utilisateur."""
    for existing_token, existing_user_id in list(SESSIONS.items()):
        if existing_user_id == user_id:
            del SESSIONS[existing_token]
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = user_id
    return token


def get_user_from_token(token: str) -> int | None:
    """Retourne le user_id associé au token, ou None si le token est invalide."""
    return SESSIONS.get(token)


def revoke_session(token: str) -> None:
    """Révoque un token de session."""
    SESSIONS.pop(token, None)


def read_cookie_token(handler: BaseHTTPRequestHandler) -> str | None:
    """Extrait le token de session depuis les cookies de la requête."""
    cookie_header = handler.headers.get("Cookie")
    if not cookie_header:
        return None
    cookie = SimpleCookie()
    try:
        cookie.load(cookie_header)
    except Exception:
        return None
    morsel = cookie.get(SESSION_COOKIE_NAME)
    if morsel is None:
        return None
    return morsel.value or None


def set_cookie_token(handler: BaseHTTPRequestHandler, token: str) -> None:
    """Envoie le cookie de session HTTP-only, SameSite=Strict et Path=/."""
    cookie = SimpleCookie()
    cookie[SESSION_COOKIE_NAME] = token
    cookie[SESSION_COOKIE_NAME]["httponly"] = True
    cookie[SESSION_COOKIE_NAME]["samesite"] = "Strict"
    cookie[SESSION_COOKIE_NAME]["path"] = "/"
    handler.send_header("Set-Cookie", cookie[SESSION_COOKIE_NAME].OutputString())


def clear_cookie_token(handler: BaseHTTPRequestHandler) -> None:
    """Expire le cookie de session."""
    cookie = SimpleCookie()
    cookie[SESSION_COOKIE_NAME] = ""
    cookie[SESSION_COOKIE_NAME]["max-age"] = 0
    cookie[SESSION_COOKIE_NAME]["httponly"] = True
    cookie[SESSION_COOKIE_NAME]["samesite"] = "Strict"
    cookie[SESSION_COOKIE_NAME]["path"] = "/"
    handler.send_header("Set-Cookie", cookie[SESSION_COOKIE_NAME].OutputString())


def get_authenticated_user_id(handler: BaseHTTPRequestHandler) -> int | None:
    """Retourne le user_id si le cookie est valide, sinon None."""
    token = read_cookie_token(handler)
    if token is None:
        return None
    return get_user_from_token(token)


def redirect(handler: BaseHTTPRequestHandler, location: str) -> None:
    """Envoie une redirection HTTP 302."""
    handler.send_response(HTTPStatus.FOUND)
    handler.send_header("Location", location)
    handler.end_headers()


def json_response(
    handler: BaseHTTPRequestHandler,
    data: Any,
    status: int = HTTPStatus.OK,
) -> None:
    """Envoie une réponse JSON."""
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def error_response(
    handler: BaseHTTPRequestHandler,
    message: str,
    status: int = HTTPStatus.BAD_REQUEST,
) -> None:
    """Envoie une erreur JSON."""
    json_response(handler, {"error": message}, status)


def serve_static(handler: BaseHTTPRequestHandler, filename: str) -> None:
    """Sert un fichier statique depuis WEB_DIR."""
    file_path = WEB_DIR / filename
    if not file_path.is_file():
        handler.send_error(HTTPStatus.NOT_FOUND)
        return
    content = file_path.read_bytes()
    content_type = {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
    }.get(file_path.suffix, "application/octet-stream")
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(content)))
    handler.end_headers()
    handler.wfile.write(content)


def handle_get_login(handler: BaseHTTPRequestHandler) -> None:
    """GET /login : affiche la page de login."""
    serve_static(handler, "login.html")


def handle_post_login(handler: BaseHTTPRequestHandler) -> None:
    """POST /login : crée ou charge un utilisateur et ouvre sa session."""
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except (TypeError, ValueError):
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    if content_length <= 0 or content_length > 1024:
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    raw_body = handler.rfile.read(content_length).decode("utf-8", errors="replace")
    params = parse_qs(raw_body)
    username = params.get("username", [""])[0].strip()
    if not username or len(username) > 50:
        error_response(
            handler,
            "Nom d'utilisateur invalide",
            HTTPStatus.BAD_REQUEST,
        )
        return

    conn = _get_db_connection()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row:
            user_id = int(row["id"])
        else:
            created_at = datetime.now(timezone.utc).isoformat()
            cursor = conn.execute(
                "INSERT INTO users (username, created_at) VALUES (?, ?)",
                (username, created_at),
            )
            conn.commit()
            if cursor.lastrowid is None:
                raise LoginError("Impossible de récupérer l'identifiant utilisateur")
            user_id = cursor.lastrowid
    finally:
        conn.close()

    token = create_session_token(user_id)
    handler.send_response(HTTPStatus.FOUND)
    set_cookie_token(handler, token)
    handler.send_header("Location", "/")
    handler.end_headers()


def handle_post_logout(handler: BaseHTTPRequestHandler) -> None:
    """POST /logout : révoque la session et expire le cookie."""
    token = read_cookie_token(handler)
    if token:
        revoke_session(token)
    handler.send_response(HTTPStatus.FOUND)
    clear_cookie_token(handler)
    handler.send_header("Location", "/login")
    handler.end_headers()


def handle_get_index(handler: BaseHTTPRequestHandler) -> None:
    """GET / : affiche le chat authentifié ou redirige vers le login."""
    token = read_cookie_token(handler)
    user_id = get_user_from_token(token) if token else None
    if user_id is None:
        redirect(handler, "/login")
        return
    serve_static(handler, "chat.html")


def handle_get_api_sessions(
    handler: BaseHTTPRequestHandler,
) -> None:
    """GET /api/sessions : liste les sessions de l'utilisateur."""
    user_id = get_authenticated_user_id(handler)
    if user_id is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return
    sessions = list_sessions_for_user(user_id)
    json_response(handler, {"sessions": sessions})


def handle_post_api_sessions(
    handler: BaseHTTPRequestHandler,
) -> None:
    """POST /api/sessions : crée une session pour l'utilisateur."""
    user_id = get_authenticated_user_id(handler)
    if user_id is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except (TypeError, ValueError):
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    if content_length < 0 or content_length > 4096:
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return

    title: str | None = None
    if content_length:
        raw_body = handler.rfile.read(content_length).decode("utf-8", errors="replace")
        try:
            body = json.loads(raw_body) if raw_body.strip() else {}
        except json.JSONDecodeError:
            body = {}
        if isinstance(body, dict):
            title_raw = body.get("title")
            if isinstance(title_raw, str) and title_raw.strip():
                title = title_raw.strip()[:100]

    session_id = create_session_for_user(user_id, title)
    json_response(
        handler,
        {"session_id": session_id, "title": title},
        HTTPStatus.CREATED,
    )


def handle_get_messages(
    handler: BaseHTTPRequestHandler,
    session_id: int,
) -> None:
    """GET /api/sessions/{id}/messages : liste les messages de la session."""
    user_id = get_authenticated_user_id(handler)
    if user_id is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return
    if get_session_for_user(user_id, session_id) is None:
        error_response(handler, "Session introuvable", HTTPStatus.NOT_FOUND)
        return
    messages = get_messages_for_user(user_id, session_id)
    json_response(handler, {"messages": messages})


def handle_post_message(
    handler: BaseHTTPRequestHandler,
    user_id: int,
    session_id: int,
) -> None:
    """POST /api/sessions/{id}/messages : envoie un message au modèle."""
    raise NotImplementedError("handle_post_message à implémenter")


class RequestHandler(BaseHTTPRequestHandler):
    """Handler HTTP ; les routes connues répondent 501 tant qu'elles sont des stubs."""

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/login":
                handle_get_login(self)
            elif path == "/":
                handle_get_index(self)
            elif path == "/style.css":
                serve_static(self, "style.css")
            elif path == "/chat.js":
                serve_static(self, "chat.js")
            elif path == "/api/sessions":
                handle_get_api_sessions(self)
            else:
                match = SESSION_MSG_RE.match(path)
                if match:
                    handle_get_messages(self, int(match.group(1)))
                else:
                    self.send_error(HTTPStatus.NOT_FOUND)
        except NotImplementedError:
            self.send_error(HTTPStatus.NOT_IMPLEMENTED)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/login":
                handle_post_login(self)
            elif path == "/logout":
                handle_post_logout(self)
            elif path == "/api/sessions":
                handle_post_api_sessions(self)
            else:
                match = SESSION_MSG_RE.match(path)
                if match:
                    raise NotImplementedError("POST messages non encore implémenté")
                self.send_error(HTTPStatus.NOT_FOUND)
        except NotImplementedError:
            self.send_error(HTTPStatus.NOT_IMPLEMENTED)

    def log_message(self, format: str, *args: Any) -> None:
        """Écrit le journal HTTP avec un préfixe propre au proxy."""
        sys.stderr.write(f"[proxy] {self.address_string()} - {format % args}\n")


def main() -> int:
    """Démarre le serveur local ; les routes restent toutes non implémentées."""
    server = HTTPServer((PROXY_HOST, PROXY_PORT), RequestHandler)
    print(f"Proxy La Citadelle démarré sur http://{PROXY_HOST}:{PROXY_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())