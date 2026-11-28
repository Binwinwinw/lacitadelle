"""Prototype isolé de pré-scan JSON; non utilisé par le code de production.

La validation des caractères décodés depuis ``\\u0000``/``\\u007f`` et des
substituts isolés comme ``\\ud800`` est hors périmètre et reportée à C4.
"""

from __future__ import annotations

import json
import math

DEFAULT_MAX_DEPTH = 64
DEFAULT_MAX_NODES = 20_000
CANDIDATE_MAX_NUMBER_CHARS = 1_000


class JsonPreScanError(ValueError):
    """Le texte JSON ne respecte pas la syntaxe ou une limite du prototype."""


def _prescan_text(
    text: str,
    max_depth: int,
    max_nodes: int,
) -> tuple[int, int]:
    if max_depth < 0 or max_nodes < 0:
        raise ValueError("Les limites doivent être positives ou nulles.")

    length = len(text)
    index = 0
    nodes = 0
    maximum_depth = 0
    stack: list[tuple[str, str]] = []

    def fail(message: str) -> None:
        raise JsonPreScanError(f"{message} à la position {index}.")

    def skip_whitespace() -> None:
        nonlocal index
        while index < length and text[index] in " \t\r\n":
            index += 1

    def scan_string() -> None:
        nonlocal index
        if index >= length or text[index] != '"':
            fail("Chaîne JSON attendue")
        index += 1
        while index < length:
            char = text[index]
            if char == '"':
                index += 1
                return
            if ord(char) < 0x20:
                fail("Caractère de contrôle non échappé")
            if char != "\\":
                index += 1
                continue
            index += 1
            if index >= length:
                fail("Échappement incomplet")
            escaped = text[index]
            if escaped in '"\\/bfnrt':
                index += 1
                continue
            if escaped != "u":
                fail("Échappement JSON invalide")
            index += 1
            if index + 4 > length or any(
                digit not in "0123456789abcdefABCDEF"
                for digit in text[index:index + 4]
            ):
                fail("Échappement Unicode invalide")
            index += 4
        fail("Chaîne JSON non terminée")

    def parse_number() -> None:
        nonlocal index
        number_start = index

        def advance() -> None:
            nonlocal index
            index += 1
            if index - number_start > CANDIDATE_MAX_NUMBER_CHARS:
                fail("Littéral numérique trop long")

        def consume_digits() -> None:
            while index < length and "0" <= text[index] <= "9":
                advance()

        if text[index] == "-":
            advance()
            if index >= length:
                fail("Nombre JSON incomplet")
        if text[index] == "0":
            advance()
            if index < length and text[index].isdigit():
                fail("Zéro initial interdit dans un nombre JSON")
        elif "1" <= text[index] <= "9":
            advance()
            consume_digits()
        else:
            fail("Nombre JSON invalide")
        if index < length and text[index] == ".":
            advance()
            start = index
            consume_digits()
            if index == start:
                fail("Fraction JSON incomplète")
        if index < length and text[index] in "eE":
            advance()
            if index < length and text[index] in "+-":
                advance()
            start = index
            consume_digits()
            if index == start:
                fail("Exposant JSON incomplet")

    def parse_value() -> None:
        nonlocal index, nodes, maximum_depth
        skip_whitespace()
        if index >= length:
            fail("Valeur JSON attendue")
        nodes += 1
        if nodes > max_nodes:
            fail("Limite de nœuds dépassée")
        char = text[index]
        if char == "{":
            depth = len(stack) + 1
            if depth > max_depth:
                fail("Limite de profondeur dépassée")
            maximum_depth = max(maximum_depth, depth)
            index += 1
            stack.append(("object", "key_or_end"))
            return
        if char == "[":
            depth = len(stack) + 1
            if depth > max_depth:
                fail("Limite de profondeur dépassée")
            maximum_depth = max(maximum_depth, depth)
            index += 1
            stack.append(("array", "value_or_end"))
            return
        if char == '"':
            scan_string()
            return
        if char in "tfn":
            literal = {"t": "true", "f": "false", "n": "null"}[char]
            if text[index:index + len(literal)] != literal:
                fail("Littéral JSON invalide")
            index += len(literal)
            return
        if char == "-" or "0" <= char <= "9":
            parse_number()
            return
        fail("Valeur JSON invalide")

    skip_whitespace()
    if index >= length:
        fail("Texte JSON vide")
    parse_value()

    while stack:
        skip_whitespace()
        if index >= length:
            fail("Conteneur JSON non terminé")
        kind, state = stack[-1]
        char = text[index]
        if kind == "object":
            if state == "key_or_end" and char == "}":
                index += 1
                stack.pop()
            elif state in {"key_or_end", "key"}:
                if char != '"':
                    fail("Clé d’objet JSON attendue")
                scan_string()
                stack[-1] = ("object", "colon")
            elif state == "colon":
                if char != ":":
                    fail("Deux-points attendu après la clé")
                index += 1
                stack[-1] = ("object", "value")
            elif state == "value":
                stack[-1] = ("object", "comma_or_end")
                parse_value()
            elif state == "comma_or_end":
                if char == ",":
                    index += 1
                    stack[-1] = ("object", "key")
                elif char == "}":
                    index += 1
                    stack.pop()
                else:
                    fail("Virgule ou accolade fermante attendue")
            else:
                fail("État d’objet JSON invalide")
        elif state == "value_or_end" and char == "]":
            index += 1
            stack.pop()
        elif state in {"value_or_end", "value"}:
            stack[-1] = ("array", "comma_or_end")
            parse_value()
        elif state == "comma_or_end":
            if char == ",":
                index += 1
                stack[-1] = ("array", "value")
            elif char == "]":
                index += 1
                stack.pop()
            else:
                fail("Virgule ou crochet fermant attendu")
        else:
            fail("État de tableau JSON invalide")

    skip_whitespace()
    if index != length:
        fail("Données après la valeur JSON racine")
    return nodes, maximum_depth


def _decode_utf8(data: bytes) -> str:
    if not isinstance(data, bytes):
        raise TypeError("Le pré-scan attend des octets.")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise JsonPreScanError("Encodage UTF-8 invalide.") from exc
    return text[1:] if text.startswith("\ufeff") else text


def prescan_json(
    data: bytes,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_nodes: int = DEFAULT_MAX_NODES,
) -> tuple[int, int]:
    """Retourne (nœuds, profondeur max) avant toute construction de l’arbre."""
    return _prescan_text(_decode_utf8(data), max_depth, max_nodes)


def load_json_bounded(
    data: bytes,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_nodes: int = DEFAULT_MAX_NODES,
) -> tuple[object, int, int]:
    """Pré-scane avant json.loads et refuse les nombres flottants non finis."""
    text = _decode_utf8(data)
    nodes, depth = _prescan_text(text, max_depth, max_nodes)

    def parse_constant(value: str) -> object:
        raise JsonPreScanError(f"Constante JSON non standard : {value}.")

    def parse_finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise JsonPreScanError("Nombre flottant non fini.")
        return parsed

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise JsonPreScanError(f"Clé JSON dupliquée : {key!r}.")
            result[key] = value
        return result

    try:
        parsed = json.loads(
            text,
            parse_constant=parse_constant,
            parse_float=parse_finite_float,
            object_pairs_hook=reject_duplicate_keys,
        )
    except JsonPreScanError:
        raise
    except Exception as exc:
        raise JsonPreScanError("Échec du décodage JSON.") from exc
    return parsed, nodes, depth
