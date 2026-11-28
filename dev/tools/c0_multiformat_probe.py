#!/usr/bin/env python3
"""C0A autonome : pré-scan JSON, worker spawn et mesures synthétiques.

Ce fichier est volontairement autonome et ne doit pas importer le code produit.
Le scanner est dupliqué depuis json_prescan_prototype.py; un test compare les
deux copies pour détecter leur divergence.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import ctypes
import hashlib
import importlib.util
import io
import json
import math
import multiprocessing as mp
import os
import platform
import random
import statistics
import struct
import subprocess
import sys
import tempfile
import threading
import time
import tracemalloc
from dataclasses import dataclass
from multiprocessing.process import BaseProcess
from pathlib import Path
from subprocess import Popen
from typing import Any

DEFAULT_MAX_DEPTH = 64
DEFAULT_MAX_NODES = 20_000
CANDIDATE_MAX_NUMBER_CHARS = 1_000
MAX_INPUT_BYTES = 256 * 1024
MAX_RESPONSE_BYTES = 512
WORKER_TIMEOUT_SECONDS = 5.0
GLOBAL_TIMEOUT_SECONDS = 900.0
MEASURE_ITERATIONS = 20
ISOLATION_MEASURE_ITERATIONS = 5
REQUEST_HEADER = struct.Struct("!BII")

MODE_PING = 0
MODE_JSON = 1
MODE_CSV = 2
MODE_HANG = 3
MODE_ERROR = 4
MODE_OVERSIZE = 5
MODE_CSV_LIMIT = 6
MODE_CPU_HANG = 7
MODE_CLOSE = 8


def _nested_arrays(depth: int, value: bytes = b"0") -> bytes:
    return b"[" * depth + value + b"]" * depth


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


CHECKS: list[tuple[str, bool | None, str]] = []
MEASUREMENTS: list[dict[str, Any]] = []
MEASUREMENT_FAILURES: list[str] = []
ORPHAN_PIDS: list[int] = []
ACTIVE_PROCESSES: list[BaseProcess] = []
ACTIVE_SUBPROCESSES: list[Popen[str]] = []
ACTIVE_LOCK = threading.Lock()
TEMP_DIR: tempfile.TemporaryDirectory[str] | None = None
START_TIME = 0.0


class ProbeError(RuntimeError):
    """Une vérification C0A n’a pas satisfait son critère d’arrêt."""


def _register_process(process: BaseProcess) -> None:
    with ACTIVE_LOCK:
        ACTIVE_PROCESSES.append(process)


def _unregister_process(process: BaseProcess) -> None:
    with ACTIVE_LOCK:
        if process in ACTIVE_PROCESSES:
            ACTIVE_PROCESSES.remove(process)


def _register_subprocess(process: subprocess.Popen[str]) -> None:
    with ACTIVE_LOCK:
        ACTIVE_SUBPROCESSES.append(process)


def _unregister_subprocess(process: subprocess.Popen[str]) -> None:
    with ACTIVE_LOCK:
        if process in ACTIVE_SUBPROCESSES:
            ACTIVE_SUBPROCESSES.remove(process)


def _stop_process(process: BaseProcess) -> bool:
    if process.pid is None:
        return False
    if process.is_alive():
        process.terminate()
        process.join(timeout=1.0)
    if process.is_alive():
        process.kill()
        process.join(timeout=1.0)
    alive = process.is_alive()
    if alive and process.pid is not None:
        ORPHAN_PIDS.append(process.pid)
    return alive


def _stop_subprocess(process: subprocess.Popen[str]) -> bool:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1.0)
    alive = process.poll() is None
    if alive:
        ORPHAN_PIDS.append(process.pid)
    return alive


def _stop_all_processes() -> None:
    with ACTIVE_LOCK:
        processes = list(ACTIVE_PROCESSES)
        subprocesses = list(ACTIVE_SUBPROCESSES)
    for process in processes:
        try:
            _stop_process(process)
        except (OSError, ValueError):
            if process.pid is not None:
                ORPHAN_PIDS.append(process.pid)
    for process in subprocesses:
        try:
            _stop_subprocess(process)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            ORPHAN_PIDS.append(process.pid)


def _check_prescan() -> str:
    cases = (
        (b"null", (1, 0)),
        (b"[]", (1, 1)),
        (b"{}", (1, 1)),
        (b'{"x":[1,true,null]}', (5, 2)),
    )
    for payload, expected in cases:
        actual = prescan_json(payload)
        if actual != expected:
            raise AssertionError(f"{payload!r}: {actual} != {expected}")

    for depth in (64,):
        if prescan_json(b"[" * depth + b"0" + b"]" * depth) != (
            depth + 1,
            depth,
        ):
            raise AssertionError(f"Profondeur tableau {depth} incorrecte.")
        if prescan_json(b'{"k":' * depth + b"0" + b"}" * depth) != (
            depth + 1,
            depth,
        ):
            raise AssertionError(f"Profondeur objet {depth} incorrecte.")
    for payload in (
        b"[" * 65 + b"0" + b"]" * 65,
        b'{"k":' * 65 + b"0" + b"}" * 65,
    ):
        try:
            prescan_json(payload)
        except JsonPreScanError:
            pass
        else:
            raise AssertionError("Profondeur 65 acceptée.")

    exact_nodes = b"[" + b",".join(b"[]" for _ in range(19_999)) + b"]"
    over_nodes = b"[" + b",".join(b"[]" for _ in range(20_000)) + b"]"
    if prescan_json(exact_nodes) != (20_000, 2):
        raise AssertionError("La limite exacte de nœuds CSV/JSON diffère.")
    exact_number = b"1" + b"0" * (CANDIDATE_MAX_NUMBER_CHARS - 1)
    if len(str(load_json_bounded(exact_number)[0])) != CANDIDATE_MAX_NUMBER_CHARS:
        raise AssertionError("La limite exacte de littéral numérique diffère.")
    loads = json.loads

    def forbidden_loads(*args, **kwargs):
        raise AssertionError(
            "json.loads appelé avant le refus de limite "
            f"(args={len(args)}, kwargs={len(kwargs)})."
        )

    json.loads = forbidden_loads
    try:
        over_limit_payloads = (
            ("nœuds", over_nodes),
            ("profondeur tableau", _nested_arrays(65)),
            ("profondeur objet", b'{"k":' * 65 + b"0" + b"}" * 65),
            (
                "littéral numérique",
                b"1" + b"0" * CANDIDATE_MAX_NUMBER_CHARS,
            ),
            ("entier de 5000 chiffres", b"1" + b"0" * 4_999),
        )
        for label, payload in over_limit_payloads:
            try:
                load_json_bounded(payload)
            except JsonPreScanError:
                continue
            raise AssertionError(f"Dépassement accepté: {label}.")
    finally:
        json.loads = loads

    expected_string = 'brackets ] } { and escaped quote: " and slash \\'
    string_payload = json.dumps([expected_string]).encode("utf-8")
    if load_json_bounded(string_payload)[0] != [expected_string]:
        raise AssertionError("Guillemets ou délimiteurs de chaîne mal lus.")
    unicode_payload = rb'{"s":"\u0041\uD83D\uDE00"}'
    if load_json_bounded(unicode_payload)[0] != {"s": "A😀"}:
        raise AssertionError("Paire de substituts Unicode mal lue.")

    large_payload = (
        b'{"s":"' + b"x" * (256 * 1024 - 16) + b'"}'
    )
    if len(large_payload) >= 256 * 1024:
        raise AssertionError("Chaîne de test supérieure au plafond d’octets.")
    if load_json_bounded(large_payload)[1:] != (2, 1):
        raise AssertionError("La longue chaîne modifie les comptes structurels.")

    bom_payload = b"\xef\xbb\xbf" + b'{"ok":true}'
    if load_json_bounded(bom_payload) != ({"ok": True}, 2, 1):
        raise AssertionError("Un BOM UTF-8 initial n’a pas été retiré.")

    invalid_inputs = (
        b"\xef\xbb\xbf\xef\xbb\xbf{}",
        b'"\xff"',
        b"{}{}",
        b"[",
        b'{"x":0',
        b"[0}",
        b'{"x" 0}',
        b"[1,]",
        b'{"x":1,}',
        rb'"\u0G00"',
        b'"unfinished',
        b"NaN",
        b"Infinity",
        b"-Infinity",
    )
    for payload in invalid_inputs:
        try:
            prescan_json(payload)
        except JsonPreScanError:
            pass
        else:
            raise AssertionError(f"Entrée invalide acceptée : {payload[:60]!r}")
    try:
        load_json_bounded(b"1e9999")
    except JsonPreScanError:
        pass
    else:
        raise AssertionError("Un flottant non fini a été accepté.")

    duplicate = b'{"same":1,"same":2}'
    if prescan_json(duplicate) != (3, 1):
        raise AssertionError("Le pré-scan doit compter les valeurs syntaxiques.")
    try:
        load_json_bounded(duplicate)
    except JsonPreScanError as exc:
        if "dupliquée" not in str(exc):
            raise AssertionError("Erreur de clé dupliquée inattendue.") from exc
    else:
        raise AssertionError("Le prototype accepte une clé JSON dupliquée.")

    rng = random.Random(20261125)

    def make_value(depth: int = 0):
        if depth >= 5 or rng.random() < 0.35:
            return rng.choice(
                [
                    None,
                    True,
                    False,
                    rng.randint(-10_000, 10_000),
                    rng.random(),
                    "quotes \" slash \\ braces []{}",
                ]
            )
        if rng.random() < 0.5:
            return [make_value(depth + 1) for _ in range(rng.randrange(4))]
        return {
            f"key_{index}": make_value(depth + 1)
            for index in range(rng.randrange(4))
        }

    def tree_nodes(value: Any) -> int:
        if isinstance(value, list):
            return 1 + sum(tree_nodes(item) for item in value)
        if isinstance(value, dict):
            return 1 + sum(tree_nodes(item) for item in value.values())
        return 1

    def tree_depth(value: Any, parent_depth: int = 0) -> int:
        if isinstance(value, (list, dict)):
            depth = parent_depth + 1
            children = value if isinstance(value, list) else value.values()
            return max([depth, *(tree_depth(item, depth) for item in children)])
        return parent_depth

    for _ in range(100):
        payload = json.dumps(make_value(), ensure_ascii=True).encode("utf-8")
        decoded = json.loads(payload)
        nodes, depth = prescan_json(payload, max_depth=100, max_nodes=10_000)
        if nodes < tree_nodes(decoded) or depth < tree_depth(decoded):
            raise AssertionError(
                f"Pré-scan sous-compté: nodes={nodes}, depth={depth}."
            )
    return "frontières, échappements, invalides, limite pré-loads, graine=20261125"


def _parse_request(request: bytes) -> tuple[int, int, int, bytes]:
    if len(request) < REQUEST_HEADER.size:
        raise ValueError("Requête worker tronquée.")
    mode, max_depth, max_nodes = REQUEST_HEADER.unpack(
        request[:REQUEST_HEADER.size]
    )
    return mode, max_depth, max_nodes, request[REQUEST_HEADER.size:]


def _csv_stats(payload: bytes) -> tuple[int, int, int]:
    text = payload.decode("utf-8", errors="strict")
    rows = 0
    cells = 0
    max_field = 0
    for row in csv.reader(io.StringIO(text, newline=""), strict=True):
        rows += 1
        cells += len(row)
        if row:
            max_field = max(max_field, *(len(cell) for cell in row))
    return rows, cells, max_field


def _rejection_name(exc: Exception) -> str:
    if isinstance(exc, csv.Error):
        return "csv.Error"
    if isinstance(exc, JsonPreScanError):
        return "JsonPreScanError"
    return type(exc).__name__


def _worker_entry(connection) -> None:
    try:
        request = connection.recv_bytes(MAX_INPUT_BYTES + REQUEST_HEADER.size)
        mode, max_depth, max_nodes, payload = _parse_request(request)
        if mode == MODE_PING:
            response = b"OK|PING"
        elif mode == MODE_HANG:
            connection.recv_bytes(MAX_INPUT_BYTES + REQUEST_HEADER.size)
            response = b"OK|UNBLOCKED"
        elif mode == MODE_CPU_HANG:
            while True:
                pass
        elif mode == MODE_CLOSE:
            return
        elif mode == MODE_ERROR:
            raise RuntimeError("exception worker de test")
        elif mode == MODE_OVERSIZE:
            connection.send_bytes(b"x" * (MAX_RESPONSE_BYTES + 1))
            return
        elif mode == MODE_CSV_LIMIT:
            import csv as worker_csv

            old_limit = worker_csv.field_size_limit()
            worker_csv.field_size_limit(12345)
            response = (
                f"CSVLIMIT|{old_limit}|{worker_csv.field_size_limit()}"
            ).encode("ascii")
        elif mode in {MODE_JSON, MODE_CSV}:
            started = time.perf_counter_ns()
            tracemalloc.start()
            try:
                if mode == MODE_JSON:
                    value, nodes, depth = load_json_bounded(
                        payload,
                        max_depth=max_depth,
                        max_nodes=max_nodes,
                    )
                    result = (
                        f"JSON|{nodes}|{depth}|{type(value).__name__}"
                    )
                else:
                    rows, cells, max_field = _csv_stats(payload)
                    result = f"CSV|{rows}|{cells}|{max_field}"
            except Exception as exc:
                _, peak = tracemalloc.get_traced_memory()
                elapsed_ns = time.perf_counter_ns() - started
                response = (
                    f"ERR|{_rejection_name(exc)}|{elapsed_ns}|{peak}"
                ).encode("ascii")
            else:
                _, peak = tracemalloc.get_traced_memory()
                elapsed_ns = time.perf_counter_ns() - started
                response = f"{result}|{elapsed_ns}|{peak}".encode("ascii")
            finally:
                tracemalloc.stop()
        else:
            raise ValueError("Mode worker inconnu.")

        if len(response) > MAX_RESPONSE_BYTES:
            raise ValueError("Résultat worker non borné.")
        connection.send_bytes(response)
    except Exception as exc:
        with contextlib.suppress(OSError):
            connection.send_bytes(f"ERR|{type(exc).__name__}".encode("ascii"))
    finally:
        connection.close()


@dataclass(frozen=True)
class WorkerResult:
    response: bytes | None
    elapsed: float
    pid: int | None
    timed_out: bool = False
    oversized_rejected: bool = False
    orphan: bool = False


def _encode_request(mode: int, payload: bytes = b"") -> bytes:
    if len(payload) > MAX_INPUT_BYTES:
        raise ProbeError(f"Entrée worker trop grande: {len(payload)} octets.")
    return REQUEST_HEADER.pack(mode, DEFAULT_MAX_DEPTH, DEFAULT_MAX_NODES) + payload


def _call_worker(
    mode: int,
    payload: bytes = b"",
    *,
    timeout: float = WORKER_TIMEOUT_SECONDS,
    expect_timeout: bool = False,
    expect_oversize: bool = False,
) -> WorkerResult:
    context = mp.get_context("spawn")
    parent_connection, child_connection = context.Pipe(duplex=True)
    process = context.Process(
        target=_worker_entry,
        args=(child_connection,),
        name="citadelle-c0a-worker",
    )
    request = _encode_request(mode, payload)
    _register_process(process)
    started = time.perf_counter()
    timed_out = False
    oversized_rejected = False
    response = None
    pid = None
    started_process = False
    try:
        process.start()
        started_process = True
        pid = process.pid
        child_connection.close()
        parent_connection.send_bytes(request)
        if not parent_connection.poll(timeout):
            timed_out = True
            _stop_process(process)
        else:
            try:
                response = parent_connection.recv_bytes(MAX_RESPONSE_BYTES)
            except EOFError as exc:
                raise ProbeError(
                    f"Worker {pid} a fermé le tube sans résultat (EOF)."
                ) from exc
            except OSError as exc:
                if expect_oversize:
                    oversized_rejected = True
                else:
                    raise ProbeError(
                        f"Erreur de réception du worker {pid}: {exc}"
                    ) from exc
            process.join(timeout=1.0)
            if process.is_alive():
                _stop_process(process)
                raise ProbeError(
                    f"Worker {pid} a répondu mais n’a pas terminé."
                )
            if process.exitcode != 0 and not oversized_rejected:
                raise ProbeError(
                    f"Worker {pid} terminé avec le code {process.exitcode}."
                )
    finally:
        parent_connection.close()
        child_connection.close()
        if started_process and process.is_alive():
            _stop_process(process)
        _unregister_process(process)
        if started_process and not process.is_alive():
            process.close()
    elapsed = time.perf_counter() - started
    orphan = bool(pid in ORPHAN_PIDS)
    if timed_out and not expect_timeout:
        raise ProbeError(f"Worker {pid} a dépassé {timeout:.1f} s.")
    if expect_timeout and not timed_out:
        raise ProbeError("Le worker bloqué n’a pas été arrêté par le délai.")
    if oversized_rejected and not expect_oversize:
        raise ProbeError("Le parent a reçu un résultat worker trop grand.")
    if expect_oversize and not oversized_rejected:
        raise ProbeError("Le parent n’a pas rejeté le résultat trop grand.")
    return WorkerResult(
        response,
        elapsed,
        pid,
        timed_out,
        oversized_rejected,
        orphan,
    )


def _check_worker_proofs() -> str:
    valid = _call_worker(MODE_JSON, b'{"ok":[1,2]}')
    if valid.response is None or len(valid.response) > MAX_RESPONSE_BYTES:
        raise AssertionError("Réponse normale absente ou non bornée.")
    fields = valid.response.decode("ascii").split("|")
    if fields[0] != "JSON" or fields[1:3] != ["4", "2"]:
        raise AssertionError(f"Réponse JSON worker inattendue: {fields!r}")

    exception = _call_worker(MODE_ERROR)
    if exception.response != b"ERR|RuntimeError":
        raise AssertionError(f"Exception non contrôlée: {exception.response!r}")

    try:
        _call_worker(MODE_OVERSIZE)
    except ProbeError as exc:
        if "Erreur de réception" not in str(exc):
            raise
    else:
        raise AssertionError("Une réponse trop grande n’a pas échoué clairement.")
    oversized = _call_worker(MODE_OVERSIZE, expect_oversize=True)
    if oversized.orphan:
        raise AssertionError(f"Enfant orphelin après dépassement: {oversized.pid}")

    try:
        _call_worker(MODE_CLOSE)
    except ProbeError as exc:
        if "fermé" not in str(exc) and "EOF" not in str(exc):
            raise
    else:
        raise AssertionError("La fermeture du tube sans réponse n’a pas échoué.")

    import csv as parent_csv

    parent_limit = parent_csv.field_size_limit()
    field_result = _call_worker(MODE_CSV_LIMIT)
    if field_result.response is None:
        raise AssertionError("Réponse de field_size_limit absente.")
    values = field_result.response.decode("ascii").split("|")
    if len(values) != 3 or values[0] != "CSVLIMIT":
        raise AssertionError(f"Valeurs worker CSV inattendues: {values!r}")
    if int(values[1]) != parent_limit or int(values[2]) != 12345:
        raise AssertionError(f"Valeurs worker CSV inattendues: {values!r}")
    if parent_csv.field_size_limit() != parent_limit:
        raise AssertionError("field_size_limit enfant modifié dans le parent.")

    timeout_result = _call_worker(
        MODE_HANG,
        timeout=WORKER_TIMEOUT_SECONDS,
        expect_timeout=True,
    )
    if timeout_result.orphan:
        raise AssertionError(
            f"Enfant orphelin après délai: {timeout_result.pid}"
        )
    cpu_timeout = _call_worker(
        MODE_CPU_HANG,
        timeout=WORKER_TIMEOUT_SECONDS,
        expect_timeout=True,
    )
    if cpu_timeout.orphan:
        raise AssertionError(
            f"Enfant orphelin après boucle CPU: {cpu_timeout.pid}"
        )
    if not 4.75 <= timeout_result.elapsed <= WORKER_TIMEOUT_SECONDS + 2.0:
        raise AssertionError(
            f"Délai mesuré hors tolérance: {timeout_result.elapsed:.3f} s."
        )
    if not 4.75 <= cpu_timeout.elapsed <= WORKER_TIMEOUT_SECONDS + 2.0:
        raise AssertionError(
            f"Délai boucle CPU hors tolérance: {cpu_timeout.elapsed:.3f} s."
        )

    active = mp.active_children()
    if active:
        pids = [child.pid for child in active]
        for child in active:
            _stop_process(child)
        raise AssertionError(f"Enfant(s) encore actif(s): {pids!r}")
    return (
        f"spawn; délai {timeout_result.elapsed:.3f} s; "
        f"boucle CPU terminée en {cpu_timeout.elapsed:.3f} s; "
        "EOF/OSError contrôlés, réponse bornée, CSV isolé"
    )


def _run_check(name: str, action) -> bool:
    try:
        detail = action()
    except Exception as exc:
        CHECKS.append((name, False, f"{type(exc).__name__}: {exc}"))
        print(f"[ÉCHEC] {name}: {type(exc).__name__}: {exc}", flush=True)
        return False
    CHECKS.append((name, True, str(detail)))
    print(f"[RÉUSSI] {name}: {detail}", flush=True)
    return True


def _skip_check(name: str, detail: str) -> None:
    CHECKS.append((name, None, detail))
    print(f"[SKIP] {name}: {detail}", flush=True)


def _write_isolation_harness() -> tuple[Path, Path]:
    if TEMP_DIR is None:
        raise ProbeError("Répertoire temporaire absent pour le test d’isolation.")
    directory = Path(TEMP_DIR.name) / "isolation"
    directory.mkdir(parents=True, exist_ok=True)
    worker_path = directory / "light_worker.py"
    main_path = directory / "fake_main.py"
    worker_path.write_text(
        """import json
import sys


def _report():
    selected = (
        "__main__",
        "__mp_main__",
        "http.server",
        "light_worker",
        "sqlite3",
    )
    return {
        "loaded_modules": sorted(name for name in selected if name in sys.modules),
        "module_count": len(sys.modules),
        "sqlite3": "sqlite3" in sys.modules,
        "http.server": "http.server" in sys.modules,
        "worker_module": __name__,
    }


def report(connection):
    connection.send_bytes(json.dumps(_report(), sort_keys=True).encode("ascii"))
    connection.close()


if __name__ == "__main__" and sys.argv[1:] == ["--report"]:
    print(json.dumps(_report(), sort_keys=True), flush=True)
""",
        encoding="utf-8",
        newline="\n",
    )
    main_path.write_text(
        """import http.server
import json
import multiprocessing as mp
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from light_worker import report


def _spawn():
    context = mp.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=report, args=(child,))
    started = time.perf_counter()
    try:
        process.start()
        child.close()
        if not parent.poll(45):
            raise RuntimeError("spawn worker did not report")
        result = json.loads(parent.recv_bytes(4096))
        process.join(timeout=5)
        if process.is_alive():
            raise RuntimeError("spawn worker did not exit")
        if process.exitcode != 0:
            raise RuntimeError("spawn worker exit code was not zero")
        return {
            "modules": result,
            "startup_ms": (time.perf_counter() - started) * 1000,
            "child_alive": process.is_alive(),
        }
    finally:
        parent.close()
        child.close()
        if process.pid is not None:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join(timeout=5)
            process.close()


def _subprocess(worker_executable):
    if worker_executable:
        command = [worker_executable, "--report"]
    else:
        command = [
            sys.executable,
            str(Path(__file__).with_name("light_worker.py")),
            "--report",
        ]
    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        stdout, stderr = process.communicate(timeout=45)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        raise RuntimeError("dedicated subprocess worker timed out")
    if process.returncode != 0:
        raise RuntimeError(
            "dedicated subprocess worker failed: " + stderr[-300:]
        )
    result = json.loads(stdout.strip().splitlines()[-1])
    return {
        "modules": result,
        "startup_ms": (time.perf_counter() - started) * 1000,
        "child_alive": process.poll() is None,
    }


def main():
    mode = sys.argv[1]
    if mode == "spawn":
        result = _spawn()
    elif mode == "subprocess":
        worker_executable = sys.argv[2] if len(sys.argv) > 2 else None
        result = _subprocess(worker_executable)
    else:
        raise ValueError("unknown isolation mode")
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    mp.freeze_support()
    main()
""",
        encoding="utf-8",
        newline="\n",
    )
    return main_path, worker_path


def _run_external(
    command: list[str],
    *,
    timeout: float,
    cwd: Path,
) -> tuple[int, str, str]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    _register_subprocess(process)
    try:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            _stop_subprocess(process)
            process.communicate()
            raise ProbeError(
                f"Processus auxiliaire dépassé après {timeout:.0f} s."
            ) from exc
    finally:
        if process.poll() is None:
            _stop_subprocess(process)
        _unregister_subprocess(process)
    return process.returncode, stdout, stderr


def _run_isolation_harness(
    mode: str,
    *,
    main_executable: Path | None = None,
    worker_executable: Path | None = None,
) -> dict[str, Any]:
    main_path, _ = _write_isolation_harness()
    if main_executable is None:
        command = [sys.executable, str(main_path), mode]
    else:
        command = [str(main_executable), mode]
    if worker_executable is not None:
        command.append(str(worker_executable))
    result, stdout, _ = _run_external(
        command,
        timeout=60.0,
        cwd=main_path.parent,
    )
    if result != 0:
        raise ProbeError(f"Isolation {mode}: processus terminé avec code {result}.")
    try:
        return json.loads(stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise ProbeError(f"Isolation {mode}: sortie JSON absente ou invalide.") from exc


def _check_isolation_architecture(
    mode: str,
    *,
    main_executable: Path | None = None,
    worker_executable: Path | None = None,
) -> str:
    expected_imports = mode == "spawn"
    results = []
    for _ in range(ISOLATION_MEASURE_ITERATIONS):
        result = _run_isolation_harness(
            mode,
            main_executable=main_executable,
            worker_executable=worker_executable,
        )
        modules = result["modules"]
        if modules["sqlite3"] != expected_imports:
            raise ProbeError(
                f"{mode}: présence sqlite3 inattendue ({modules['sqlite3']})."
            )
        if modules["http.server"] != expected_imports:
            raise ProbeError(
                f"{mode}: présence http.server inattendue "
                f"({modules['http.server']})."
            )
        if result["child_alive"]:
            raise ProbeError(f"{mode}: processus worker encore actif.")
        results.append(result)
    startup_times = [result["startup_ms"] for result in results]
    startup_median, startup_max = statistics.median(startup_times), max(
        startup_times
    )
    modules = results[-1]["modules"]
    return (
        f"modules enfant={modules['loaded_modules']} "
        f"(modules totaux={modules['module_count']}); "
        f"démarrage médiane/max={startup_median:.3f}/"
        f"{startup_max:.3f} ms sur {ISOLATION_MEASURE_ITERATIONS} mesures; "
        "enfant terminé"
    )


def _build_frozen_executable(
    script_path: Path,
    name: str,
    build_dir: Path,
) -> Path:
    dist = build_dir / f"{name}-dist"
    work = build_dir / f"{name}-work"
    spec = build_dir / f"{name}-spec"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--name",
        name,
        "--distpath",
        str(dist),
        "--workpath",
        str(work),
        "--specpath",
        str(spec),
        str(script_path),
    ]
    returncode, _, _ = _run_external(
        command,
        timeout=300.0,
        cwd=script_path.parent,
    )
    if returncode != 0:
        raise ProbeError(f"PyInstaller {name}: code de sortie {returncode}.")
    executable = dist / (name + (".exe" if os.name == "nt" else ""))
    if not executable.is_file():
        raise ProbeError(f"PyInstaller {name}: exécutable absent.")
    return executable


def _check_frozen_isolation() -> str:
    if importlib.util.find_spec("PyInstaller") is None:
        return "non testable sans installation (PyInstaller absent)"
    if TEMP_DIR is None:
        raise ProbeError("Répertoire temporaire absent pour PyInstaller.")
    try:
        from PyInstaller import __version__ as pyinstaller_version
    except ImportError as exc:
        raise ProbeError("PyInstaller détecté mais non importable.") from exc
    main_path, worker_path = _write_isolation_harness()
    build_dir = Path(TEMP_DIR.name) / "frozen"
    build_dir.mkdir(parents=True, exist_ok=True)
    failures = []
    try:
        main_executable = _build_frozen_executable(
            main_path,
            "c0a-isolation-main",
            build_dir,
        )
    except Exception as exc:
        main_executable = None
        failures.append(f"main build: {type(exc).__name__}")
    try:
        worker_executable = _build_frozen_executable(
            worker_path,
            "c0a-isolation-worker",
            build_dir,
        )
    except Exception as exc:
        worker_executable = None
        failures.append(f"worker build: {type(exc).__name__}")

    results = []
    if main_executable is not None:
        try:
            results.append(
                "Comparaison spawn figé (non isolé attendu): "
                + _check_isolation_architecture(
                    "spawn",
                    main_executable=main_executable,
                )
            )
        except Exception as exc:
            failures.append(f"frozen spawn: {type(exc).__name__}")
        if worker_executable is not None:
            try:
                results.append(
                    "Comparaison subprocess figé (isolé attendu): "
                    + _check_isolation_architecture(
                        "subprocess",
                        main_executable=main_executable,
                        worker_executable=worker_executable,
                    )
                )
            except Exception as exc:
                failures.append(f"frozen subprocess: {type(exc).__name__}")
        else:
            failures.append("frozen subprocess: worker exécutable absent")
    else:
        failures.append("frozen spawn: exécutable principal absent")
    details = (
        f"PyInstaller {pyinstaller_version}; " + "; ".join(results + failures)
    )
    if failures:
        raise ProbeError(details)
    return details


def _build_measurement_cases() -> list[tuple[str, str, bytes, bool]]:
    cases = [
        (
            "csv_5000_lignes_1_colonne",
            "csv",
            b"value\n" + b"\n".join(str(i).encode("ascii") for i in range(5000)),
            False,
        ),
        (
            "csv_100_colonnes",
            "csv",
            ",".join(f"c{i}" for i in range(100)).encode("ascii") + b"\n",
            False,
        ),
        (
            "csv_20000_cellules",
            "csv",
            b"\n".join(
                b",".join(b"x" for _ in range(100))
                for _ in range(200)
            ),
            False,
        ),
        (
            "csv_champ_64KiB",
            "csv",
            b"header\n" + b"x" * (64 * 1024) + b"\n",
            False,
        ),
        (
            "csv_proche_256KiB",
            "csv",
            b"h\n" + b"\n".join(b"x" * 50_000 for _ in range(5)),
            False,
        ),
        (
            "csv_virgules_256KiB_une_ligne",
            "csv",
            b"," * MAX_INPUT_BYTES,
            False,
        ),
        (
            "csv_131000_lignes_un_caractere",
            "csv",
            b"x\n" * 131_000,
            False,
        ),
        (
            "csv_champ_multiligne_256KiB_rejete",
            "csv",
            b'"' + b"x\n" * ((MAX_INPUT_BYTES - 2) // 2) + b'"',
            True,
        ),
        (
            "csv_100_colonnes_300_lignes",
            "csv",
            (b",".join(b"x" for _ in range(100)) + b"\n") * 300,
            False,
        ),
        (
            "json_profondeur_64",
            "json",
            _nested_arrays(64),
            False,
        ),
        (
            "json_20000_noeuds",
            "json",
            b"[" + b",".join(b"[]" for _ in range(19_999)) + b"]",
            False,
        ),
        (
            "json_chaine_longue",
            "json",
            json.dumps({"s": "x" * 200_000}).encode("utf-8"),
            False,
        ),
        (
            "json_proche_256KiB",
            "json",
            b'"' + b"x" * (MAX_INPUT_BYTES - 2) + b'"',
            False,
        ),
        (
            "json_20000_flottants_rejete",
            "json",
            b"[" + b",".join(b"1.0" for _ in range(20_000)) + b"]",
            True,
        ),
        (
            "json_20000_objets_cles_longues_rejete",
            "json",
            b"[" + b",".join(b'{"longer":0}' for _ in range(20_000)) + b"]",
            True,
        ),
        (
            "json_128000_scalaires_rejete_20001",
            "json",
            b"[" + b",".join(b"0" for _ in range(128_000)) + b"]",
            True,
        ),
    ]
    for name, _, payload, _ in cases:
        if len(payload) > MAX_INPUT_BYTES:
            raise ProbeError(f"{name}: entrée supérieure à 256 KiB.")
    return cases


def _parse_in_process(kind: str, payload: bytes) -> tuple[int, int, int]:
    if kind == "json":
        _, nodes, depth = load_json_bounded(payload)
        return nodes, depth, 0
    if kind == "csv":
        return _csv_stats(payload)
    raise ProbeError(f"Type de mesure inconnu: {kind}")


def _parse_worker_metrics(
    response: bytes,
    kind: str,
) -> tuple[int, str | None]:
    fields = response.decode("ascii").split("|")
    if kind == "json" and len(fields) == 6 and fields[0] == "JSON":
        return int(fields[5]), None
    if kind == "csv" and len(fields) == 6 and fields[0] == "CSV":
        return int(fields[5]), None
    if len(fields) == 4 and fields[0] == "ERR":
        return int(fields[3]), fields[1]
    raise ProbeError(f"Réponse de mesure inattendue: {fields!r}")


def _measure_in_process(
    kind: str,
    payload: bytes,
    expect_rejection: bool,
) -> tuple[list[float], list[int], str | None]:
    durations = []
    peaks = []
    observed_rejection = None
    for iteration in range(MEASURE_ITERATIONS + 1):
        rejection = None
        tracemalloc.start()
        try:
            started = time.perf_counter()
            try:
                _parse_in_process(kind, payload)
            except (JsonPreScanError, csv.Error) as exc:
                rejection = _rejection_name(exc)
        finally:
            elapsed = time.perf_counter() - started
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        if bool(rejection) != expect_rejection:
            raise ProbeError(
                f"Résultat inattendu pour {kind}: rejet={rejection!r}."
            )
        if observed_rejection is not None and rejection != observed_rejection:
            raise ProbeError("Le type de rejet varie entre les mesures.")
        observed_rejection = rejection
        if iteration:
            durations.append(elapsed)
            peaks.append(peak)
    return durations, peaks, observed_rejection


def _measure_worker(
    kind: str,
    payload: bytes,
    expect_rejection: bool,
) -> tuple[list[float], list[int], str | None]:
    durations = []
    peaks = []
    mode = MODE_JSON if kind == "json" else MODE_CSV
    observed_rejection = None
    for iteration in range(MEASURE_ITERATIONS + 1):
        result = _call_worker(mode, payload)
        if result.response is None or result.orphan:
            raise ProbeError(f"Worker de mesure non valide: {result!r}")
        peak, rejection = _parse_worker_metrics(result.response, kind)
        if bool(rejection) != expect_rejection:
            raise ProbeError(
                f"Résultat worker inattendu pour {kind}: "
                f"rejet={rejection!r}."
            )
        if observed_rejection is not None and rejection != observed_rejection:
            raise ProbeError("Le type de rejet worker varie entre les mesures.")
        observed_rejection = rejection
        if iteration:
            durations.append(result.elapsed)
            peaks.append(peak)
    return durations, peaks, observed_rejection


def _median_max(values: list[float]) -> tuple[float, float]:
    return statistics.median(values), max(values)


def _run_measurements() -> str:
    cases = _build_measurement_cases()
    MEASUREMENT_FAILURES.clear()
    startup_times = []
    try:
        for iteration in range(MEASURE_ITERATIONS + 1):
            result = _call_worker(MODE_PING)
            if result.response != b"OK|PING" or result.orphan:
                raise ProbeError("Échec du worker ping de mesure.")
            if iteration:
                startup_times.append(result.elapsed)
    except Exception as exc:
        failure = f"spawn/ping: {type(exc).__name__}: {exc}"
        MEASUREMENT_FAILURES.append(failure)
    startup_summary = "non mesuré"
    if startup_times:
        startup_median, startup_max = _median_max(startup_times)
        startup_summary = (
            f"spawn/ping sonde légère (pas le serveur) médiane/max "
            f"{startup_median:.3f}/{startup_max:.3f} s"
        )

    for name, kind, payload, expect_rejection in cases:
        in_result = None
        worker_result = None
        try:
            in_result = _measure_in_process(kind, payload, expect_rejection)
        except Exception as exc:
            failure = (
                f"{name} in-process: {type(exc).__name__}: {exc}"
            )
            MEASUREMENT_FAILURES.append(failure)
        try:
            worker_result = _measure_worker(kind, payload, expect_rejection)
        except Exception as exc:
            failure = f"{name} worker: {type(exc).__name__}: {exc}"
            MEASUREMENT_FAILURES.append(failure)
        if in_result is None or worker_result is None:
            continue
        in_durations, in_peaks, in_rejection = in_result
        worker_durations, worker_peaks, worker_rejection = worker_result
        if in_rejection != worker_rejection:
            failure = (
                f"Le rejet diverge entre processus pour {name}: "
                f"{in_rejection!r} != {worker_rejection!r}."
            )
            MEASUREMENT_FAILURES.append(failure)
        in_median, in_max = _median_max(in_durations)
        worker_median, worker_max = _median_max(worker_durations)
        MEASUREMENTS.append(
            {
                "name": name,
                "in_median_ms": in_median * 1000,
                "in_max_ms": in_max * 1000,
                "in_peak_bytes": max(in_peaks),
                "worker_median_ms": worker_median * 1000,
                "worker_max_ms": worker_max * 1000,
                "worker_peak_bytes": max(worker_peaks),
                "iterations": MEASURE_ITERATIONS,
                "rejection": in_rejection,
            }
        )
    if MEASUREMENT_FAILURES:
        raise ProbeError(
            f"{len(MEASUREMENT_FAILURES)} échec(s) de mesure; "
            "les autres scénarios ont été poursuivis."
        )
    return (
        f"{len(cases)} scénarios × {MEASURE_ITERATIONS} après "
        f"écartement du premier essai; {startup_summary}"
    )


def _run_smoke() -> None:
    _run_check(
        "Pré-scan smoke",
        lambda: (
            "nœuds/profondeur="
            + repr(prescan_json(b'{"smoke":[1,true]}'))
        ),
    )

    def worker_smoke() -> str:
        result = _call_worker(MODE_JSON, b'{"smoke":[1,true]}')
        if result.response is None or not result.response.startswith(b"JSON|"):
            raise AssertionError(f"Réponse worker absente: {result.response!r}")
        if len(result.response) > MAX_RESPONSE_BYTES:
            raise AssertionError("Réponse worker trop grande.")
        return f"spawn PID {result.pid}, réponse {len(result.response)} octets"

    _run_check("Worker spawn smoke", worker_smoke)


def _run_full(*, include_frozen: bool = False) -> None:
    _run_check("Pré-scan JSON adverse", _check_prescan)
    _run_check("Worker spawn et protections", _check_worker_proofs)
    _run_check(
        "Comparaison spawn source (non isolé attendu)",
        lambda: _check_isolation_architecture("spawn"),
    )
    _run_check(
        "Comparaison subprocess source (isolé attendu)",
        lambda: _check_isolation_architecture("subprocess"),
    )
    if platform.system() == "Windows" or include_frozen:
        _run_check(
            "Comparaison PyInstaller figée",
            _check_frozen_isolation,
        )
    else:
        _skip_check(
            "Comparaison PyInstaller figée",
            "hors Windows; utilisez --frozen pour l’inclure",
        )
    _run_check("Mesures synthétiques", _run_measurements)


def _global_timeout() -> None:
    print(
        f"[ÉCHEC] Délai global de {GLOBAL_TIMEOUT_SECONDS:.0f} s dépassé.",
        flush=True,
    )
    _stop_all_processes()
    if TEMP_DIR is not None:
        try:
            TEMP_DIR.cleanup()
        except OSError as exc:
            print(f"[ÉCHEC] Nettoyage temporaire : {exc}", flush=True)
    _emit_report("complet", forced_failure=True)
    os._exit(124)


def _script_sha256() -> str:
    source = Path(__file__)
    if not source.is_file() and getattr(sys, "frozen", False):
        source = Path(sys.executable)
    return hashlib.sha256(source.read_bytes()).hexdigest()


def _physical_memory_bytes() -> int | None:
    if platform.system() == "Windows":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys)
        return None
    sysconf = getattr(os, "sysconf", None)
    if sysconf is None:
        return None
    try:
        return int(sysconf("SC_PAGE_SIZE") * sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, ValueError):
        return None


def _clean_field(value: str) -> str:
    return value.replace("|", "/").replace(";", ",").replace("\n", " ")


def _emit_report(mode: str, forced_failure: bool = False) -> bool:
    elapsed = max(0.0, time.perf_counter() - START_TIME)
    try:
        children = mp.active_children()
    except (AssertionError, RuntimeError):
        children = []
    for child in children:
        if child.pid is not None and child.pid not in ORPHAN_PIDS:
            ORPHAN_PIDS.append(child.pid)
    with ACTIVE_LOCK:
        subprocesses = list(ACTIVE_SUBPROCESSES)
    for process in subprocesses:
        if process.poll() is None and process.pid not in ORPHAN_PIDS:
            ORPHAN_PIDS.append(process.pid)
    success = (
        not forced_failure
        and all(ok is not False for _, ok, _ in CHECKS)
        and not MEASUREMENT_FAILURES
        and not ORPHAN_PIDS
    )
    status = "RÉUSSI" if success else "ÉCHEC"
    system = f"{platform.system()} {platform.release()}".strip()
    processor = platform.processor() or platform.machine() or "inconnu"
    memory = _physical_memory_bytes()
    memory_text = "inconnu" if memory is None else f"{memory / (1024 ** 3):.2f}"
    interpreter = f"<répertoire masqué>/{Path(sys.executable).name}"
    digest = _script_sha256()

    print("\n=== Résumé C0A ===", flush=True)
    print(f"Mode : {mode}", flush=True)
    print(f"Système : {system}", flush=True)
    print(f"Python : {platform.python_version()} ({interpreter})", flush=True)
    python_supported = sys.version_info >= (3, 10)
    if not python_supported:
        print(
            "AVERTISSEMENT : Python est inférieur au minimum requis 3.10.",
            flush=True,
        )
    print(
        f"Processeur : {processor}; cœurs logiques : {os.cpu_count()}; "
        f"mémoire physique : {memory_text} GiB",
        flush=True,
    )
    print(f"SHA-256 du script : {digest}", flush=True)
    for name, ok, detail in CHECKS:
        display_status = "SKIP" if ok is None else "RÉUSSI" if ok else "ÉCHEC"
        print(f"[{display_status}] {name}: {detail}", flush=True)
    if MEASUREMENTS:
        print(
            "Mesures (20 essais après écartement du premier) : pics "
            "tracemalloc, pas mémoire résidente.",
            flush=True,
        )
        for item in MEASUREMENTS:
            outcome = (
                f"rejet attendu ({item['rejection']})"
                if item["rejection"]
                else "accepté"
            )
            print(
                f"  {item['name']}: {outcome}; inproc médiane/max "
                f"{item['in_median_ms']:.3f}/{item['in_max_ms']:.3f} ms; "
                f"pic {item['in_peak_bytes']} B; worker médiane/max "
                f"{item['worker_median_ms']:.3f}/"
                f"{item['worker_max_ms']:.3f} ms; "
                f"pic enfant {item['worker_peak_bytes']} B",
                flush=True,
            )
    for failure in MEASUREMENT_FAILURES:
        print(f"[ÉCHEC] Mesure {failure}", flush=True)
    print(
        "Orphelin(s) : "
        + (
            ", ".join(str(pid) for pid in sorted(set(ORPHAN_PIDS)))
            if ORPHAN_PIDS
            else "aucun"
        ),
        flush=True,
    )
    print(f"Durée totale : {elapsed:.3f} s", flush=True)
    check_text = ",".join(
        f"{name}={'SKIP' if ok is None else 'OK' if ok else 'FAIL'}"
        for name, ok, _ in CHECKS
    ) or "none"
    measures = ",".join(
        f"{item['name']}:outcome="
        f"{'rejected_' + item['rejection'] if item['rejection'] else 'accepted'},"
        f"in_ms={item['in_median_ms']:.3f}/"
        f"{item['in_max_ms']:.3f},in_peak_B={item['in_peak_bytes']},"
        f"worker_ms={item['worker_median_ms']:.3f}/"
        f"{item['worker_max_ms']:.3f},worker_peak_B="
        f"{item['worker_peak_bytes']}"
        for item in MEASUREMENTS
    ) or "not-run"
    orphans = ",".join(str(pid) for pid in sorted(set(ORPHAN_PIDS))) or "none"
    print("\nBloc à copier :", flush=True)
    print(
        f"C0A|status={status}|mode={mode}|system={_clean_field(system)}|"
        f"python={platform.python_version()}|python_path={interpreter}|"
        f"python_supported={str(python_supported).lower()}|"
        f"cpu={_clean_field(processor)}|logical_cpus={os.cpu_count()}|"
        f"ram_GiB={memory_text}|sha256={digest}|checks={check_text}|"
        f"measures={measures}|orphans={orphans}|duration_s={elapsed:.3f}",
        flush=True,
    )
    print(status, flush=True)
    return success


def main(argv: list[str] | None = None) -> int:
    global START_TIME, TEMP_DIR
    parser = argparse.ArgumentParser(
        description="Pré-scan JSON et worker C0A, autonome et stdlib."
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="preuve courte de démarrage worker, destinée au test PyInstaller",
    )
    parser.add_argument(
        "--frozen",
        action="store_true",
        help="inclut le contrôle PyInstaller hors Windows",
    )
    args = parser.parse_args(argv)
    START_TIME = time.perf_counter()
    TEMP_DIR = tempfile.TemporaryDirectory(prefix="citadelle-c0a-")
    watchdog = threading.Timer(GLOBAL_TIMEOUT_SECONDS, _global_timeout)
    watchdog.daemon = True
    watchdog.start()
    try:
        if args.smoke:
            _run_smoke()
            mode = "smoke"
        else:
            _run_full(include_frozen=args.frozen)
            mode = "complet"
    except Exception as exc:
        if not CHECKS or CHECKS[-1][1] is not False:
            CHECKS.append(
                ("arrêt sûr", False, f"{type(exc).__name__}: {exc}")
            )
        print(f"[ARRÊT] {type(exc).__name__}: {exc}", flush=True)
        mode = "smoke" if args.smoke else "complet"
    finally:
        watchdog.cancel()
        watchdog.join(timeout=0.2)
        _stop_all_processes()
        if TEMP_DIR is not None:
            try:
                TEMP_DIR.cleanup()
            except OSError as exc:
                CHECKS.append(("nettoyage temporaire", False, str(exc)))
    return 0 if _emit_report(mode) else 1


if __name__ == "__main__":
    mp.freeze_support()
    raise SystemExit(main())
