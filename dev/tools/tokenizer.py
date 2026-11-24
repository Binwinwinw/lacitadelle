"""Comptage de tokens avec repli approximatif pour les modèles locaux."""

import importlib


def count_tokens(text: str, model: str) -> int:
    """Compte les tokens si tiktoken reconnaît le modèle, sinon estime.

    Les noms de modèles GGUF locaux ne sont généralement pas reconnus par
    tiktoken. Dans ce cas, ou si tiktoken n'est pas installé, le fallback
    `len(text) // 4` reste une approximation et ne reproduit pas le tokenizer
    du modèle.

    Args:
        text: Texte à estimer.
        model: Identifiant de modèle accepté par tiktoken, si disponible.

    Returns:
        Nombre de tokens encodés ou nombre approximatif via le fallback.
    """
    try:
        tiktoken = importlib.import_module("tiktoken")
    except ImportError:
        return len(text) // 4

    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        return len(text) // 4
    return len(encoding.encode(text))
