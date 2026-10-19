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
import secrets
import sys
import urllib.error
import urllib.request
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citadelle_memory import (
    add_message,
    create_session,
    ensure_default_user,
    get_messages,
    init_db,
    list_sessions,
)

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8081
LLAMAFILE_URL = "http://127.0.0.1:8080/v1/chat/completions"
WEB_DIR = Path(__file__).resolve().parent / "web"
MAX_CONTEXT_MESSAGES = 15
SYSTEM_PROMPT = "Tu es Lacitadelle, un assistant IA local. Réponds en français."
SESSION_COOKIE_NAME = "lacitadelle_session"
HTTP_TIMEOUT = 120

# Le contenu est perdu au redémarrage du proxy, conformément au contrat V2.
SESSIONS: dict[str, int] = {}


class LoginError(Exception):
    """Erreur attendue du serveur de login."""


def create_session_token(user_id: int) -> str:
    """Crée un token opaque et remplace l'ancien token de l'utilisateur."""
    raise NotImplementedError("create_session_token à implémenter")


def get_user_from_token(token: str) -> int | None:
    """Retourne le user_id associé au token, ou None si le token est invalide."""
    raise NotImplementedError("get_user_from_token à implémenter")


def revoke_session(token: str) -> None:
    """Révoque un token de session."""
    raise NotImplementedError("revoke_session à implémenter")


def read_cookie_token(handler: BaseHTTPRequestHandler) -> str | None:
    """Extrait le token de session depuis les cookies de la requête."""
    raise NotImplementedError("read_cookie_token à implémenter")


def set_cookie_token(handler: BaseHTTPRequestHandler, token: str) -> None:
    """Envoie le cookie de session HTTP-only, SameSite=Strict et Path=/."""
    raise NotImplementedError("set_cookie_token à implémenter")


def clear_cookie_token(handler: BaseHTTPRequestHandler) -> None:
    """Expire le cookie de session."""
    raise NotImplementedError("clear_cookie_token à implémenter")


def redirect(handler: BaseHTTPRequestHandler, location: str) -> None:
    """Envoie une redirection HTTP 302."""
    raise NotImplementedError("redirect à implémenter")


def json_response(
    handler: BaseHTTPRequestHandler,
    data: Any,
    status: int = HTTPStatus.OK,
) -> None:
    """Envoie une réponse JSON."""
    raise NotImplementedError("json_response à implémenter")


def error_response(
    handler: BaseHTTPRequestHandler,
    message: str,
    status: int = HTTPStatus.BAD_REQUEST,
) -> None:
    """Envoie une erreur JSON."""
    raise NotImplementedError("error_response à implémenter")


def serve_static(handler: BaseHTTPRequestHandler, filename: str) -> None:
    """Sert un fichier statique depuis WEB_DIR."""
    raise NotImplementedError("serve_static à implémenter")


def handle_get_login(handler: BaseHTTPRequestHandler) -> None:
    """GET /login : affiche la page de login."""
    raise NotImplementedError("handle_get_login à implémenter")


def handle_post_login(handler: BaseHTTPRequestHandler) -> None:
    """POST /login : crée ou charge un utilisateur et ouvre sa session."""
    raise NotImplementedError("handle_post_login à implémenter")


def handle_post_logout(handler: BaseHTTPRequestHandler) -> None:
    """POST /logout : révoque la session et expire le cookie."""
    raise NotImplementedError("handle_post_logout à implémenter")


def handle_get_index(handler: BaseHTTPRequestHandler) -> None:
    """GET / : affiche le chat authentifié ou redirige vers le login."""
    raise NotImplementedError("handle_get_index à implémenter")


def handle_get_api_sessions(
    handler: BaseHTTPRequestHandler,
    user_id: int,
) -> None:
    """GET /api/sessions : liste les sessions de l'utilisateur."""
    raise NotImplementedError("handle_get_api_sessions à implémenter")


def handle_post_api_sessions(
    handler: BaseHTTPRequestHandler,
    user_id: int,
) -> None:
    """POST /api/sessions : crée une session pour l'utilisateur."""
    raise NotImplementedError("handle_post_api_sessions à implémenter")


def handle_get_messages(
    handler: BaseHTTPRequestHandler,
    user_id: int,
    session_id: int,
) -> None:
    """GET /api/sessions/{id}/messages : liste les messages de la session."""
    raise NotImplementedError("handle_get_messages à implémenter")


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
            elif path == "/api/sessions" or (
                path.startswith("/api/sessions/") and path.endswith("/messages")
            ):
                raise NotImplementedError("Routes API non encore implémentées")
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
            elif path == "/api/sessions" or (
                path.startswith("/api/sessions/") and path.endswith("/messages")
            ):
                raise NotImplementedError("Routes API non encore implémentées")
            else:
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