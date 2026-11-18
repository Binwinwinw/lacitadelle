"""Appel texte au modèle llamafile déjà actif."""

from __future__ import annotations

from pathlib import Path

from client import chat_with_llamafile


def call_model(
    prompt: str,
    model_path: str | Path | None = None,
    timeout: int = 60,
) -> str:
    """Envoie un prompt texte à l'API locale et retourne la réponse."""
    if not isinstance(prompt, str):
        raise TypeError("prompt doit être une chaîne.")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout <= 0:
        raise ValueError("timeout doit être un entier strictement positif.")
    model = str(model_path) if model_path is not None else None
    if model is not None and not model.strip():
        raise ValueError("model_path ne peut pas être vide.")
    return chat_with_llamafile(
        [{"role": "user", "content": prompt}],
        model=model,
        timeout=timeout,
    )
