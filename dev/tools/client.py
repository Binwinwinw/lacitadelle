#!/usr/bin/env python3
"""Client REPL de La Citadelle, connecté à un serveur llamafile existant.

Le client ne lance jamais le serveur. Il utilise la mémoire SQLite V1
pour persister les sessions et les messages.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any

import citadelle_memory as memory

LLAMAFILE_URL = "http://127.0.0.1:8080/v1/chat/completions"
LLAMAFILE_HEALTH_URL = "http://127.0.0.1:8080/v1/models"
MODEL_NAME = "LLaMA_CPP"
SYSTEM_PROMPT = "Tu es La Citadelle, un assistant local. Réponds en français de façon claire et concise."
MAX_CONTEXT_MESSAGES = 15
HTTP_TIMEOUT = 60


class ClientError(Exception):
    """Erreur attendue lors d'une requête au serveur llamafile."""


def check_server() -> bool:
    """Vérifie que le serveur llamafile répond sans lancer de processus."""
    try:
        with urllib.request.urlopen(
            LLAMAFILE_HEALTH_URL,
            timeout=HTTP_TIMEOUT,
        ):
            return True
    except urllib.error.HTTPError as error:
        print(
            f"Serveur llamafile indisponible (HTTP {error.code}) : "
            f"{LLAMAFILE_HEALTH_URL}",
            file=sys.stderr,
        )
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        reason = getattr(error, "reason", error)
        print(
            f"Serveur llamafile indisponible ({reason}). "
            "Lancez-le séparément avant le client.",
            file=sys.stderr,
        )
    return False


def chat_with_llamafile(messages: list[dict[str, str]]) -> str:
    """Envoie une conversation non-streaming et retourne la réponse."""
    body = json.dumps(
        {"model": MODEL_NAME, "messages": messages, "stream": False}
    ).encode("utf-8")
    request = urllib.request.Request(
        LLAMAFILE_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer no-key",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            result = json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()
        raise ClientError(
            f"Erreur HTTP {error.code} du serveur llamafile"
            + (f" : {detail}" if detail else "")
        ) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        reason = getattr(error, "reason", error)
        raise ClientError(f"Connexion au serveur llamafile impossible : {reason}") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ClientError("Réponse JSON invalide du serveur llamafile") from error

    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ClientError("Réponse chat incomplète du serveur llamafile") from error
    if not isinstance(content, str):
        raise ClientError("Le serveur llamafile a retourné une réponse vide")
    return content


def build_messages_for_context(session_id: int) -> list[dict[str, str]]:
    """Construit le prompt système suivi des N derniers messages."""
    history = memory.get_messages(session_id, limit=MAX_CONTEXT_MESSAGES)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(
        {"role": row["role"], "content": row["content"]}
        for row in history
    )
    return messages


def make_title_from_message(message: str) -> str:
    """Produit le titre d'une session à partir de son premier message."""
    title = message.strip()
    if not title:
        return "Nouvelle conversation"
    if len(title) > 50:
        return title[:50] + "..."
    return title


def run_repl() -> bool:
    """Lance le REPL si le serveur répond; retourne False s'il est absent."""
    if not check_server():
        return False

    session_id: int | None = None
    print("La Citadelle. Commandes : /new, /list, /load <id>, /quit")
    while True:
        try:
            user_input = input("Vous > ").strip()
        except EOFError:
            print()
            return True

        if not user_input:
            continue
        if user_input == "/quit":
            return True
        if user_input == "/new":
            session_id = None
            print("Nouvelle conversation.")
            continue
        if user_input == "/list":
            sessions = memory.list_sessions()
            if not sessions:
                print("Aucune conversation.")
            else:
                for session in sessions:
                    title = session["title"] or "Nouvelle conversation"
                    print(
                        f"{session['id']}: {title} "
                        f"({session['message_count']} messages)"
                    )
            continue
        if user_input.startswith("/load"):
            parts = user_input.split(maxsplit=1)
            if len(parts) != 2:
                print("Usage : /load <id>")
                continue
            try:
                requested_id = int(parts[1])
            except ValueError:
                print("L'identifiant de session doit être un entier.")
                continue
            session = next(
                (
                    item
                    for item in memory.list_sessions()
                    if item["id"] == requested_id
                ),
                None,
            )
            if session is None:
                print(f"Session introuvable : {requested_id}")
                continue
            session_id = requested_id
            print(f"Session {session_id} chargée : {session['title'] or 'Nouvelle conversation'}")
            continue
        if user_input.startswith("/"):
            print("Commande inconnue. Utilisez /new, /list, /load <id> ou /quit.")
            continue

        if session_id is None:
            session_id = memory.create_session(
                title=make_title_from_message(user_input)
            )
        memory.add_message(session_id, "user", user_input)
        try:
            answer = chat_with_llamafile(
                build_messages_for_context(session_id)
            )
        except ClientError as error:
            print(f"Erreur : {error}", file=sys.stderr)
            continue
        memory.add_message(session_id, "assistant", answer)
        print(f"Citadelle > {answer}")


def main() -> int:
    """Point d'entrée du client. Ne lance pas llamafile."""
    return 0 if run_repl() else 1


if __name__ == "__main__":
    sys.exit(main())