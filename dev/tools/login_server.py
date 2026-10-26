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
import math
import re
import secrets
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
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
    ensure_admin_exists,
    generate_strong_password,
    get_messages,
    get_messages_for_user,
    get_preferences,
    get_session_for_user,
    hash_password,
    init_db,
    list_sessions,
    list_sessions_for_user,
    migrate_to_v3,
    migrate_to_v4,
    migrate_to_v5,
    migrate_to_v6,
    record_inference,
    set_preferences,
    verify_password,
)

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8081
LLAMAFILE_URL = "http://127.0.0.1:8080/v1/chat/completions"
WEB_DIR = Path(__file__).resolve().parent / "web"
MAX_CONTEXT_MESSAGES = 15
SYSTEM_PROMPT = "Tu es Lacitadelle, un assistant IA local. Réponds en français."
SESSION_COOKIE_NAME = "lacitadelle_session"
SESSION_TTL_SECONDS = 86400
HTTP_TIMEOUT = 120
SQLITE_TIMEOUT = 5.0
MAX_POST_BODY_SIZE = 1_048_576
SESSION_MSG_RE = re.compile(r"^/api/sessions/(\d+)/messages$")
ADMIN_USER_ACTION_RE = re.compile(
    r"^/api/admin/users/(\d+)/(deactivate|activate|promote|demote|delete|reset-password)$"
)
USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_-]{3,50}$")
ADMIN_USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EXEMPT_PATHS_WHEN_MUST_CHANGE = {
    "/change-password",
    "/logout",
    "/login",
    "/register",
    "/style.css",
    "/chat.js",
    "/login.html",
    "/register.html",
    "/change-password.html",
}

# Le contenu est perdu au redémarrage du proxy, conformément au contrat V2.
SESSIONS: dict[str, int] = {}
MUST_CHANGE: dict[str, bool] = {}
SESSION_EXPIRY: dict[str, float] = {}


class LoginError(Exception):
    """Erreur attendue du serveur de login."""


def generate_temp_password() -> str:
    """Génère un mot de passe temporaire cryptographiquement sûr de 16 caractères."""
    return generate_strong_password(16)


def _get_db_connection() -> sqlite3.Connection:
    """Ouvre une connexion SQLite à memory.db (configurable pour tests)."""
    MEMORY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(MEMORY_DB_PATH), timeout=SQLITE_TIMEOUT)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_session_token(user_id: int, must_change: bool = False) -> str:
    """Crée un token opaque et remplace l'ancien token de l'utilisateur."""
    for existing_token, existing_user_id in list(SESSIONS.items()):
        if existing_user_id == user_id:
            revoke_session(existing_token)
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = user_id
    MUST_CHANGE[token] = must_change
    SESSION_EXPIRY[token] = time.time() + SESSION_TTL_SECONDS
    return token


def is_session_valid(token: str | None) -> bool:
    """Vérifie que le token existe et n'a pas expiré côté serveur."""
    if token is None:
        return False
    if token not in SESSIONS:
        revoke_session(token)
        return False
    if SESSION_EXPIRY.get(token, 0) <= time.time():
        revoke_session(token)
        return False
    return True


def get_user_from_token(token: str | None) -> int | None:
    """Retourne le user_id associé au token, ou None si le token est invalide."""
    if not is_session_valid(token):
        return None
    return SESSIONS.get(token)


def revoke_session(token: str) -> None:
    """Révoque un token de session."""
    SESSIONS.pop(token, None)
    MUST_CHANGE.pop(token, None)
    SESSION_EXPIRY.pop(token, None)


def must_change_required(token: str | None) -> bool:
    """Indique si le token est restreint au changement de mot de passe."""
    return MUST_CHANGE.get(token, False) if is_session_valid(token) else False


def check_must_change_gate(
    handler: BaseHTTPRequestHandler,
    token: str | None,
    path: str,
) -> bool:
    """Bloque les routes d'une session qui doit changer son mot de passe."""
    if token is not None and not is_session_valid(token):
        token = None
    if path in EXEMPT_PATHS_WHEN_MUST_CHANGE or not must_change_required(token):
        return False
    if path.startswith("/api/"):
        error_response(
            handler,
            "Changement de mot de passe requis",
            HTTPStatus.FORBIDDEN,
        )
    else:
        redirect(handler, "/change-password")
    return True


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
    cookie[SESSION_COOKIE_NAME]["max-age"] = SESSION_TTL_SECONDS
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
    return get_user_from_token(token)


def require_admin(handler: BaseHTTPRequestHandler) -> int | None:
    """Vérifie en base le rôle admin et répond en cas d'accès refusé."""
    path = urlparse(handler.path).path
    is_api = path.startswith("/api/")
    token = read_cookie_token(handler)
    user_id = get_user_from_token(token)
    if user_id is None:
        if is_api:
            error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        else:
            redirect(handler, "/login")
        return None

    conn = _get_db_connection()
    try:
        user = conn.execute(
            "SELECT role, is_active FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if user is None or user["is_active"] != 1:
        if token is not None:
            revoke_session(token)
        if is_api:
            error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        else:
            redirect(handler, "/login")
        return None
    if user["role"] != "admin":
        if is_api:
            error_response(
                handler,
                "Accès réservé à l'administration",
                HTTPStatus.FORBIDDEN,
            )
        else:
            handler.send_error(HTTPStatus.FORBIDDEN)
        return None
    return user_id


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


def _read_post_body(handler: BaseHTTPRequestHandler, content_length: int) -> bytes:
    body = getattr(handler, "_post_body", None)
    if isinstance(body, bytes):
        return body
    return handler.rfile.read(content_length)


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


def handle_get_register(handler: BaseHTTPRequestHandler) -> None:
    """GET /register : affiche la page d'inscription."""
    serve_static(handler, "register.html")


def handle_get_change_password(handler: BaseHTTPRequestHandler) -> None:
    """GET /change-password : affiche le formulaire de changement."""
    serve_static(handler, "change-password.html")


def handle_get_settings(handler: BaseHTTPRequestHandler) -> None:
    """GET /settings : affiche les réglages de l'utilisateur connecté."""
    if get_authenticated_user_id(handler) is None:
        redirect(handler, "/login")
        return
    serve_static(handler, "settings.html")


def handle_get_admin(handler: BaseHTTPRequestHandler) -> None:
    """GET /admin : sert la vue admin en lecture seule."""
    if require_admin(handler) is None:
        return
    serve_static(handler, "admin.html")


def handle_get_api_me(handler: BaseHTTPRequestHandler) -> None:
    """GET /api/me : retourne le nom et le rôle de la session courante."""
    user_id = get_authenticated_user_id(handler)
    if user_id is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return
    token = read_cookie_token(handler)
    conn = _get_db_connection()
    try:
        user = conn.execute(
            "SELECT username, role, is_active FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    if user is None or user["is_active"] != 1:
        if token is not None:
            revoke_session(token)
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return
    json_response(handler, {"username": user["username"], "role": user["role"]})


def handle_get_api_admin_users(handler: BaseHTTPRequestHandler) -> None:
    """GET /api/admin/users : liste les comptes sans données secrètes."""
    if require_admin(handler) is None:
        return
    conn = _get_db_connection()
    try:
        users = [
            dict(row)
            for row in conn.execute(
                "SELECT id, username, role, is_active, must_change_password, "
                "created_at, last_login_at FROM users ORDER BY id"
            ).fetchall()
        ]
    finally:
        conn.close()
    json_response(
        handler,
        {
            "users": users,
            "summary": {
                "user_count": len(users),
                "active_admins": sum(
                    user["role"] == "admin" and user["is_active"] == 1
                    for user in users
                ),
                "disabled_users": sum(user["is_active"] != 1 for user in users),
            },
        },
    )


def get_user_role(user_id: int) -> str | None:
    """Retourne le rôle actuel d'un compte actif."""
    conn = _get_db_connection()
    try:
        user = conn.execute(
            "SELECT role FROM users WHERE id = ? AND is_active = 1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    return user["role"] if user is not None else None


def handle_get_api_logs_tail(handler: BaseHTTPRequestHandler) -> None:
    """Retourne les dernières métriques accessibles au compte authentifié."""
    user_id = get_authenticated_user_id(handler)
    if user_id is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return

    role = get_user_role(user_id)
    if role is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return

    requested_lines = parse_qs(urlparse(handler.path).query).get("lines", ["50"])[0]
    try:
        lines = int(requested_lines)
    except ValueError:
        lines = 50
    lines = max(1, min(lines, 500))

    query = (
        "SELECT im.id, im.timestamp, u.username, s.title AS session_title, "
        "im.duration_ms, im.status, im.prompt_tokens, im.completion_tokens "
        "FROM inference_metrics AS im "
        "JOIN users AS u ON u.id = im.user_id "
        "LEFT JOIN sessions AS s ON s.id = im.session_id "
    )
    params: tuple[int, ...]
    if role == "admin":
        params = (lines,)
    else:
        query += "WHERE im.user_id = ? "
        params = (user_id, lines)
    query += "ORDER BY im.timestamp DESC, im.id DESC LIMIT ?"

    conn = _get_db_connection()
    try:
        logs = [
            dict(row)
            for row in conn.execute(query, params).fetchall()
        ]
    finally:
        conn.close()
    json_response(handler, {"logs": logs})


def handle_get_api_indicators(handler: BaseHTTPRequestHandler) -> None:
    """Retourne les indicateurs d'inférence de la fenêtre sélectionnée."""
    user_id = get_authenticated_user_id(handler)
    if user_id is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return

    role = get_user_role(user_id)
    if role is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return

    requested_window = parse_qs(urlparse(handler.path).query).get(
        "window",
        ["24h"],
    )[0]
    window_seconds = {
        "24h": 24 * 60 * 60,
        "7d": 7 * 24 * 60 * 60,
        "30d": 30 * 24 * 60 * 60,
    }
    if requested_window not in window_seconds:
        requested_window = "24h"
    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(seconds=window_seconds[requested_window])
    ).isoformat()

    query = (
        "SELECT duration_ms, status, completion_tokens "
        "FROM inference_metrics WHERE timestamp >= ?"
    )
    params: tuple[Any, ...] = (cutoff,)
    if role != "admin":
        query += " AND user_id = ?"
        params = (cutoff, user_id)

    conn = _get_db_connection()
    try:
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    durations = [row["duration_ms"] for row in rows]
    ordered_durations = sorted(durations)
    total = len(rows)
    errors = sum(row["status"] != "ok" for row in rows)
    token_rows = [
        row for row in rows
        if (
            row["status"] == "ok"
            and row["completion_tokens"] is not None
            and row["duration_ms"] > 0
        )
    ]
    token_duration_ms = sum(row["duration_ms"] for row in token_rows)
    tokens_per_second = (
        round(
            sum(row["completion_tokens"] for row in token_rows)
            / (token_duration_ms / 1000),
            2,
        )
        if token_duration_ms
        else None
    )
    now = time.time()
    active_sessions = sum(
        token in SESSIONS
        and expiry > now
        and (role == "admin" or SESSIONS[token] == user_id)
        for token, expiry in SESSION_EXPIRY.items()
    )
    average_duration = (
        round(sum(durations) / total, 1)
        if total
        else 0
    )
    p95_duration = (
        ordered_durations[math.ceil(0.95 * total) - 1]
        if total
        else 0
    )

    json_response(
        handler,
        {
            "window": requested_window,
            "total_inferences": total,
            "tokens_per_second_avg": tokens_per_second,
            "latency_avg_ms": average_duration,
            "latency_p95_ms": p95_duration,
            "error_rate": round(errors / total, 3) if total else 0,
            "active_sessions": active_sessions,
            "avg_time_per_request_ms": average_duration,
        },
    )


def count_active_admins(conn: sqlite3.Connection) -> int:
    """Retourne le nombre d'administrateurs actifs."""
    return conn.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1"
    ).fetchone()[0]


def handle_post_api_admin_user_promote(
    handler: BaseHTTPRequestHandler,
    user_id: int,
) -> None:
    """POST /api/admin/users/{id}/promote : transfère le rôle admin."""
    admin_id = require_admin(handler)
    if admin_id is None:
        return

    conn = _get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        admin = conn.execute(
            "SELECT role, is_active FROM users WHERE id = ?",
            (admin_id,),
        ).fetchone()
        target = conn.execute(
            "SELECT username, role, is_active FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if target is None:
            error_response(handler, "Utilisateur introuvable", HTTPStatus.NOT_FOUND)
            return
        if admin is None or admin["role"] != "admin" or admin["is_active"] != 1:
            error_response(handler, "Admin non actif", HTTPStatus.FORBIDDEN)
            return
        if target["role"] == "admin":
            error_response(
                handler,
                "Cet utilisateur est déjà admin",
                HTTPStatus.BAD_REQUEST,
            )
            return
        if target["is_active"] != 1:
            error_response(
                handler,
                "Un utilisateur désactivé ne peut pas être promu",
                HTTPStatus.BAD_REQUEST,
            )
            return
        if count_active_admins(conn) != 1:
            error_response(
                handler,
                "Le transfert exige exactement un admin actif",
                HTTPStatus.CONFLICT,
            )
            return

        conn.execute(
            "DELETE FROM messages WHERE session_id IN "
            "(SELECT id FROM sessions WHERE user_id = ?)",
            (admin_id,),
        )
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (admin_id,))
        conn.execute(
            "UPDATE users SET role = 'user' WHERE id = ?",
            (admin_id,),
        )
        conn.execute(
            "UPDATE users SET role = 'admin' WHERE id = ?",
            (user_id,),
        )
        conn.commit()
        username = target["username"]
    finally:
        conn.close()

    for token, session_user_id in list(SESSIONS.items()):
        if session_user_id == admin_id:
            revoke_session(token)
    json_response(
        handler,
        {
            "id": user_id,
            "username": username,
            "role": "admin",
            "message": (
                f"Rôle admin transféré à {username}; votre compte devient user."
            ),
        },
    )


def handle_post_api_admin_user_demote(
    handler: BaseHTTPRequestHandler,
    user_id: int,
) -> None:
    """POST /api/admin/users/{id}/demote."""
    admin_id = require_admin(handler)
    if admin_id is None:
        return

    conn = _get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        user = conn.execute(
            "SELECT username, role, is_active FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            error_response(handler, "Utilisateur introuvable", HTTPStatus.NOT_FOUND)
            return
        if user["role"] != "admin":
            error_response(
                handler,
                "Cet utilisateur n'est pas admin",
                HTTPStatus.BAD_REQUEST,
            )
            return
        if user_id == admin_id:
            error_response(
                handler,
                "Impossible de se rétrograder soi-même",
                HTTPStatus.FORBIDDEN,
            )
            return
        if user["is_active"] == 1 and count_active_admins(conn) <= 1:
            error_response(
                handler,
                "Impossible de rétrograder le dernier admin actif",
                HTTPStatus.FORBIDDEN,
            )
            return

        conn.execute(
            "DELETE FROM messages WHERE session_id IN "
            "(SELECT id FROM sessions WHERE user_id = ?)",
            (user_id,),
        )
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.execute(
            "UPDATE users SET role = 'user' WHERE id = ?",
            (user_id,),
        )
        conn.commit()
        username = user["username"]
    finally:
        conn.close()

    for token, session_user_id in list(SESSIONS.items()):
        if session_user_id == user_id:
            revoke_session(token)
    json_response(
        handler,
        {
            "id": user_id,
            "username": username,
            "role": "user",
            "message": "Utilisateur rétrogradé",
        },
    )


def handle_post_api_admin_user_delete(
    handler: BaseHTTPRequestHandler,
    user_id: int,
) -> None:
    """POST /api/admin/users/{id}/delete : supprime un compte."""
    admin_id = require_admin(handler)
    if admin_id is None:
        return

    conn = _get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        user = conn.execute(
            "SELECT username, role, is_active FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            error_response(handler, "Utilisateur introuvable", HTTPStatus.NOT_FOUND)
            return
        if user_id == admin_id:
            error_response(
                handler,
                "Impossible de se supprimer soi-même",
                HTTPStatus.FORBIDDEN,
            )
            return
        if user["role"] == "admin" and user["is_active"] == 1:
            if count_active_admins(conn) <= 1:
                error_response(
                    handler,
                    "Impossible de supprimer le dernier admin actif",
                    HTTPStatus.FORBIDDEN,
                )
                return

        username = user["username"]
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()

    for token, session_user_id in list(SESSIONS.items()):
        if session_user_id == user_id:
            revoke_session(token)
    json_response(
        handler,
        {"id": user_id, "username": username, "deleted": True},
    )


def handle_post_api_admin_user_reset_password(
    handler: BaseHTTPRequestHandler,
    user_id: int,
) -> None:
    """POST /api/admin/users/{id}/reset-password."""
    if require_admin(handler) is None:
        return

    conn = _get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        user = conn.execute(
            "SELECT username FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            error_response(handler, "Utilisateur introuvable", HTTPStatus.NOT_FOUND)
            return

        temp_password = generate_strong_password()
        conn.execute(
            "UPDATE users SET password_hash = ?, must_change_password = 1 "
            "WHERE id = ?",
            (hash_password(temp_password), user_id),
        )
        conn.commit()
        username = user["username"]
    finally:
        conn.close()

    for token, session_user_id in list(SESSIONS.items()):
        if session_user_id == user_id:
            revoke_session(token)
    json_response(
        handler,
        {
            "id": user_id,
            "username": username,
            "temp_password": temp_password,
            "message": (
                "Mot de passe réinitialisé. L'utilisateur devra le changer "
                "à sa prochaine connexion."
            ),
        },
    )


def handle_post_api_admin_user_deactivate(
    handler: BaseHTTPRequestHandler,
    user_id: int,
) -> None:
    """POST /api/admin/users/{id}/deactivate."""
    admin_id = require_admin(handler)
    if admin_id is None:
        return

    conn = _get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        user = conn.execute(
            "SELECT role, is_active FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            error_response(handler, "Utilisateur introuvable", HTTPStatus.NOT_FOUND)
            return
        if user_id == admin_id:
            error_response(
                handler,
                "Auto-désactivation interdite",
                HTTPStatus.FORBIDDEN,
            )
            return
        if user["role"] == "admin" and user["is_active"] == 1:
            active_admins = conn.execute(
                "SELECT COUNT(*) FROM users "
                "WHERE role = 'admin' AND is_active = 1"
            ).fetchone()[0]
            if active_admins <= 1:
                error_response(
                    handler,
                    "Impossible de désactiver le dernier admin actif",
                    HTTPStatus.FORBIDDEN,
                )
                return

        conn.execute(
            "DELETE FROM messages WHERE session_id IN "
            "(SELECT id FROM sessions WHERE user_id = ?)",
            (user_id,),
        )
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?",
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()

    for token, session_user_id in list(SESSIONS.items()):
        if session_user_id == user_id:
            revoke_session(token)
    json_response(handler, {"message": "Utilisateur désactivé"})


def handle_post_api_admin_user_activate(
    handler: BaseHTTPRequestHandler,
    user_id: int,
) -> None:
    """POST /api/admin/users/{id}/activate."""
    if require_admin(handler) is None:
        return

    conn = _get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        user = conn.execute(
            "SELECT id FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            error_response(handler, "Utilisateur introuvable", HTTPStatus.NOT_FOUND)
            return
        conn.execute(
            "UPDATE users SET is_active = 1 WHERE id = ?",
            (user_id,),
        )
        conn.commit()
    finally:
        conn.close()

    json_response(handler, {"message": "Utilisateur réactivé"})


def handle_post_api_admin_users_create(handler: BaseHTTPRequestHandler) -> None:
    """POST /api/admin/users : crée un utilisateur avec un mot de passe temporaire."""
    if require_admin(handler) is None:
        return
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except (TypeError, ValueError):
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    if content_length <= 0 or content_length > 4096:
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    try:
        payload = json.loads(
            _read_post_body(handler, content_length).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError):
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    if not isinstance(payload, dict):
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    username = payload.get("username")
    if not isinstance(username, str):
        error_response(
            handler,
            "Nom d'utilisateur invalide",
            HTTPStatus.BAD_REQUEST,
        )
        return
    username = username.strip()
    if not ADMIN_USERNAME_REGEX.fullmatch(username):
        error_response(
            handler,
            "Nom d'utilisateur invalide",
            HTTPStatus.BAD_REQUEST,
        )
        return

    conn = _get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute(
            "SELECT 1 FROM users WHERE username = ? LIMIT 1",
            (username,),
        ).fetchone():
            error_response(
                handler,
                "Nom d'utilisateur déjà pris",
                HTTPStatus.CONFLICT,
            )
            return
        temp_password = generate_temp_password()
        cursor = conn.execute(
            "INSERT INTO users "
            "(username, password_hash, role, is_active, "
            "must_change_password, created_at, last_login_at) "
            "VALUES (?, ?, 'user', 1, 1, ?, NULL)",
            (
                username,
                hash_password(temp_password),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        if cursor.lastrowid is None:
            raise sqlite3.DatabaseError("Impossible de récupérer l'identifiant")
        user_id = cursor.lastrowid
    finally:
        conn.close()

    json_response(
        handler,
        {
            "id": user_id,
            "username": username,
            "temp_password": temp_password,
            "message": (
                "Utilisateur créé. Le mot de passe temporaire ne sera plus affiché."
            ),
        },
        HTTPStatus.CREATED,
    )


def handle_post_login(handler: BaseHTTPRequestHandler) -> None:
    """POST /login : vérifie le mot de passe et ouvre une session."""
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except (TypeError, ValueError):
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    if content_length <= 0 or content_length > 4096:
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    raw_body = _read_post_body(handler, content_length).decode(
        "utf-8", errors="replace"
    )
    params = parse_qs(raw_body)
    username = params.get("username", [""])[0].strip()
    password = params.get("password", [""])[0]
    if not username or not password:
        error_response(handler, "Identifiants invalides", HTTPStatus.UNAUTHORIZED)
        return

    conn = _get_db_connection()
    try:
        row = conn.execute(
            "SELECT id, password_hash, is_active, must_change_password "
            "FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if (
            row is None
            or row["is_active"] != 1
            or not verify_password(password, row["password_hash"])
        ):
            error_response(handler, "Identifiants invalides", HTTPStatus.UNAUTHORIZED)
            return
        user_id = int(row["id"])
        must_change = bool(row["must_change_password"])
        conn.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), user_id),
        )
        conn.commit()
    finally:
        conn.close()

    token = create_session_token(user_id, must_change=must_change)
    handler.send_response(HTTPStatus.FOUND)
    set_cookie_token(handler, token)
    handler.send_header(
        "Location",
        "/change-password" if must_change else "/",
    )
    handler.end_headers()


def handle_post_register(handler: BaseHTTPRequestHandler) -> None:
    """POST /register : crée un utilisateur et redirige vers /login."""
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except (TypeError, ValueError):
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    if content_length <= 0 or content_length > 4096:
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    raw_body = _read_post_body(handler, content_length).decode(
        "utf-8", errors="replace"
    )
    params = parse_qs(raw_body)
    username = params.get("username", [""])[0].strip()
    password = params.get("password", [""])[0]
    password_confirm = params.get("password_confirm", [""])[0]

    if not USERNAME_REGEX.fullmatch(username):
        error_response(
            handler,
            "Nom d'utilisateur invalide",
            HTTPStatus.BAD_REQUEST,
        )
        return
    if len(password) < 8:
        error_response(
            handler,
            "Mot de passe trop court (min 8)",
            HTTPStatus.BAD_REQUEST,
        )
        return
    if password != password_confirm:
        error_response(handler, "Mots de passe différents", HTTPStatus.BAD_REQUEST)
        return

    conn = _get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute(
            "SELECT 1 FROM users WHERE username = ? LIMIT 1",
            (username,),
        ).fetchone():
            error_response(handler, "Nom déjà utilisé", HTTPStatus.BAD_REQUEST)
            return
        has_admin = conn.execute(
            "SELECT 1 FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()
        role = "user" if has_admin else "admin"
        conn.execute(
            "INSERT INTO users "
            "(username, password_hash, role, is_active, "
            "must_change_password, created_at, last_login_at) "
            "VALUES (?, ?, ?, 1, 0, ?, NULL)",
            (
                username,
                hash_password(password),
                role,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    redirect(handler, "/login")


def handle_post_change_password(handler: BaseHTTPRequestHandler) -> None:
    """POST /change-password : vérifie et remplace le mot de passe."""
    token = read_cookie_token(handler)
    user_id = get_user_from_token(token) if token else None
    if token is None or user_id is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except (TypeError, ValueError):
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    if content_length <= 0 or content_length > 4096:
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    raw_body = _read_post_body(handler, content_length).decode(
        "utf-8", errors="replace"
    )
    params = parse_qs(raw_body)
    old_password = params.get("old_password", [""])[0]
    new_password = params.get("new_password", [""])[0]
    new_password_confirm = params.get("new_password_confirm", [""])[0]

    if len(new_password) < 8:
        error_response(
            handler,
            "Mot de passe trop court (min 8)",
            HTTPStatus.BAD_REQUEST,
        )
        return
    if new_password != new_password_confirm:
        error_response(handler, "Mots de passe différents", HTTPStatus.BAD_REQUEST)
        return
    if new_password == old_password:
        error_response(
            handler,
            "Nouveau mot de passe identique à l'ancien",
            HTTPStatus.BAD_REQUEST,
        )
        return

    conn = _get_db_connection()
    try:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if row is None or not verify_password(old_password, row["password_hash"]):
            error_response(
                handler,
                "Ancien mot de passe incorrect",
                HTTPStatus.UNAUTHORIZED,
            )
            return
        conn.execute(
            "UPDATE users SET password_hash = ?, must_change_password = 0 "
            "WHERE id = ?",
            (hash_password(new_password), user_id),
        )
        conn.commit()
    finally:
        conn.close()

    MUST_CHANGE[token] = False
    redirect(handler, "/")


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


def handle_get_preferences(handler: BaseHTTPRequestHandler) -> None:
    """GET /api/preferences : retourne le nom et les préférences du user."""
    user_id = get_authenticated_user_id(handler)
    if user_id is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return
    conn = _get_db_connection()
    try:
        user = conn.execute(
            "SELECT username FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
            return
        preferences = get_preferences(conn, user_id)
    finally:
        conn.close()
    json_response(
        handler,
        {"username": user["username"], **preferences},
    )


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
        raw_body = _read_post_body(handler, content_length).decode(
            "utf-8", errors="replace"
        )
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


def handle_post_settings_preferences(
    handler: BaseHTTPRequestHandler,
) -> None:
    """POST /settings/preferences : valide et enregistre les préférences."""
    user_id = get_authenticated_user_id(handler)
    if user_id is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except (TypeError, ValueError):
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    if content_length <= 0 or content_length > 4096:
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    try:
        body = json.loads(
            _read_post_body(handler, content_length).decode("utf-8")
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        error_response(handler, "JSON invalide", HTTPStatus.BAD_REQUEST)
        return
    if not isinstance(body, dict):
        error_response(handler, "Corps invalide", HTTPStatus.BAD_REQUEST)
        return
    theme = body.get("theme")
    font_size = body.get("font_size")
    if theme not in ("light", "dark"):
        error_response(handler, "Thème invalide", HTTPStatus.BAD_REQUEST)
        return
    if font_size not in ("small", "normal", "large"):
        error_response(
            handler,
            "Taille de texte invalide",
            HTTPStatus.BAD_REQUEST,
        )
        return
    conn = _get_db_connection()
    try:
        if conn.execute(
            "SELECT 1 FROM users WHERE id = ?",
            (user_id,),
        ).fetchone() is None:
            error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
            return
        set_preferences(conn, user_id, theme, font_size)
        conn.commit()
    finally:
        conn.close()
    json_response(
        handler,
        {"saved": True, "theme": theme, "font_size": font_size},
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


def call_llamafile(
    messages: list[dict],
    user_id: int,
    session_id: int | None,
) -> str:
    """POST vers llamafile et retourne le contenu assistant.

    Isolé pour être mockable dans les tests d'intégration HTTP.

    Raises:
        LoginError: sur erreur réseau, HTTP ou réponse invalide.
    """
    started = time.monotonic()
    status = "error"
    prompt_tokens = None
    completion_tokens = None
    try:
        payload = {
            "model": "qwen3-1.7b",
            "messages": messages,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            LLAMAFILE_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=HTTP_TIMEOUT,
            ) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise LoginError(f"Erreur HTTP llamafile : {exc.code}") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                status = "timeout"
            raise LoginError(f"Erreur réseau llamafile : {exc.reason}") from exc
        except TimeoutError as exc:
            status = "timeout"
            raise LoginError(f"Erreur réseau llamafile : {exc}") from exc
        except OSError as exc:
            raise LoginError(f"Erreur réseau llamafile : {exc}") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise LoginError(f"Réponse llamafile invalide : {exc}") from exc

        usage = (
            response_data.get("usage")
            if isinstance(response_data, dict)
            else None
        )
        if isinstance(usage, dict):
            value = usage.get("prompt_tokens")
            if (
                isinstance(value, int)
                and not isinstance(value, bool)
                and value >= 0
            ):
                prompt_tokens = value
            value = usage.get("completion_tokens")
            if (
                isinstance(value, int)
                and not isinstance(value, bool)
                and value >= 0
            ):
                completion_tokens = value

        try:
            content = response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LoginError(f"Réponse llamafile inattendue : {exc}") from exc
        if not isinstance(content, str) or not content.strip():
            raise LoginError("Réponse llamafile vide ou invalide")
        status = "ok"
        return content
    finally:
        duration_ms = max(0, int((time.monotonic() - started) * 1000))
        try:
            record_inference(
                user_id=user_id,
                session_id=session_id,
                duration_ms=duration_ms,
                status=status,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                db_path=MEMORY_DB_PATH,
            )
        except Exception as exc:
            try:
                sys.stderr.write(
                    "[metrics] Inference metric not recorded "
                    f"({type(exc).__name__})\n"
                )
            except OSError:
                pass


def handle_post_message(
    handler: BaseHTTPRequestHandler,
    session_id: int,
) -> None:
    """POST /api/sessions/{id}/messages : envoie un message au modèle."""
    user_id = get_authenticated_user_id(handler)
    if user_id is None:
        error_response(handler, "Non authentifié", HTTPStatus.UNAUTHORIZED)
        return
    if get_session_for_user(user_id, session_id) is None:
        error_response(handler, "Session introuvable", HTTPStatus.NOT_FOUND)
        return
    try:
        content_length = int(handler.headers.get("Content-Length", "0"))
    except (TypeError, ValueError):
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    if content_length <= 0 or content_length > 8192:
        error_response(handler, "Requête invalide", HTTPStatus.BAD_REQUEST)
        return
    raw_body = _read_post_body(handler, content_length).decode(
        "utf-8", errors="replace"
    )
    try:
        body = json.loads(raw_body) if raw_body.strip() else {}
    except json.JSONDecodeError:
        error_response(handler, "JSON invalide", HTTPStatus.BAD_REQUEST)
        return
    if not isinstance(body, dict):
        error_response(handler, "Corps invalide", HTTPStatus.BAD_REQUEST)
        return
    content = body.get("content")
    if not isinstance(content, str) or not content.strip():
        error_response(handler, "Contenu vide", HTTPStatus.BAD_REQUEST)
        return
    content = content.strip()
    if len(content) > 4000:
        error_response(
            handler,
            "Contenu trop long (max 4000)",
            HTTPStatus.BAD_REQUEST,
        )
        return

    history = get_messages_for_user(user_id, session_id, limit=MAX_CONTEXT_MESSAGES)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(
        {"role": message["role"], "content": message["content"]}
        for message in history
    )
    messages.append({"role": "user", "content": content})

    try:
        response_text = call_llamafile(messages, user_id, session_id)
    except LoginError as exc:
        error_response(
            handler,
            f"Erreur du modèle : {exc}",
            HTTPStatus.BAD_GATEWAY,
        )
        return

    add_message(session_id, "user", content)
    add_message(session_id, "assistant", response_text)
    json_response(
        handler,
        {"assistant_message": {"role": "assistant", "content": response_text}},
        HTTPStatus.CREATED,
    )


class RequestHandler(BaseHTTPRequestHandler):
    """Gère l'authentification, le chat et l'administration en lecture seule."""

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if check_must_change_gate(self, read_cookie_token(self), path):
            return
        try:
            if path == "/login":
                handle_get_login(self)
            elif path == "/register":
                handle_get_register(self)
            elif path == "/change-password":
                handle_get_change_password(self)
            elif path == "/settings":
                handle_get_settings(self)
            elif path == "/admin":
                handle_get_admin(self)
            elif path == "/":
                handle_get_index(self)
            elif path == "/login.html":
                serve_static(self, "login.html")
            elif path == "/register.html":
                serve_static(self, "register.html")
            elif path == "/change-password.html":
                serve_static(self, "change-password.html")
            elif path == "/style.css":
                serve_static(self, "style.css")
            elif path == "/chat.js":
                serve_static(self, "chat.js")
            elif path == "/api/sessions":
                handle_get_api_sessions(self)
            elif path == "/api/preferences":
                handle_get_preferences(self)
            elif path == "/api/me":
                handle_get_api_me(self)
            elif path == "/api/admin/users":
                handle_get_api_admin_users(self)
            elif path == "/api/logs/tail":
                handle_get_api_logs_tail(self)
            elif path == "/api/indicators":
                handle_get_api_indicators(self)
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
            content_length = int(self.headers.get("Content-Length", "0"))
        except (TypeError, ValueError):
            error_response(self, "Requête invalide", HTTPStatus.BAD_REQUEST)
            self.close_connection = True
            return
        if content_length < 0:
            error_response(self, "Requête invalide", HTTPStatus.BAD_REQUEST)
            self.close_connection = True
            return
        if content_length > MAX_POST_BODY_SIZE:
            error_response(
                self,
                "Requête trop volumineuse",
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            )
            self.close_connection = True
            return
        self._post_body = self.rfile.read(content_length)
        if len(self._post_body) != content_length:
            error_response(self, "Requête incomplète", HTTPStatus.BAD_REQUEST)
            self.close_connection = True
            return
        if check_must_change_gate(self, read_cookie_token(self), path):
            return
        try:
            if path == "/login":
                handle_post_login(self)
            elif path == "/register":
                handle_post_register(self)
            elif path == "/change-password":
                handle_post_change_password(self)
            elif path == "/settings/preferences":
                handle_post_settings_preferences(self)
            elif path == "/api/admin/users":
                handle_post_api_admin_users_create(self)
            elif path == "/logout":
                handle_post_logout(self)
            elif path == "/api/sessions":
                handle_post_api_sessions(self)
            else:
                admin_user_action = ADMIN_USER_ACTION_RE.fullmatch(path)
                if admin_user_action:
                    user_id = int(admin_user_action.group(1))
                    action = admin_user_action.group(2)
                    if action == "deactivate":
                        handle_post_api_admin_user_deactivate(self, user_id)
                    elif action == "activate":
                        handle_post_api_admin_user_activate(self, user_id)
                    elif action == "promote":
                        handle_post_api_admin_user_promote(self, user_id)
                    elif action == "demote":
                        handle_post_api_admin_user_demote(self, user_id)
                    elif action == "reset-password":
                        handle_post_api_admin_user_reset_password(self, user_id)
                    else:
                        handle_post_api_admin_user_delete(self, user_id)
                else:
                    match = SESSION_MSG_RE.match(path)
                    if match:
                        handle_post_message(self, int(match.group(1)))
                    else:
                        self.send_error(HTTPStatus.NOT_FOUND)
        except NotImplementedError:
            self.send_error(HTTPStatus.NOT_IMPLEMENTED)

    def log_message(self, format: str, *args: Any) -> None:
        """Écrit le journal HTTP avec un préfixe propre au proxy."""
        sys.stderr.write(f"[proxy] {self.address_string()} - {format % args}\n")


def main() -> int:
    """Migre la base V3 puis démarre le serveur local."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    SESSIONS.clear()
    MUST_CHANGE.clear()
    SESSION_EXPIRY.clear()
    try:
        migrate_to_v3()
        migrate_to_v4()
        migrate_to_v5()
        migrate_to_v6()
        created, _, password, message = ensure_admin_exists()
    except (OSError, sqlite3.Error, ValueError, MemoryError) as exc:
        print(
            f"[ADMIN] ERREUR lors de la migration/vérification/création : {exc}",
            file=sys.stderr,
        )
        print(
            "[ADMIN] Action manuelle : python dev/tools/create_admin.py "
            "--username superadmin",
            file=sys.stderr,
        )
    else:
        print(f"[ADMIN] {message}")
        if created and password is not None:
            print(f"[ADMIN] Mot de passe superadmin : {password}")
            print(
                "[ADMIN] Notez ce mot de passe; il ne sera plus affiché."
            )

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