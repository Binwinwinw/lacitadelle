import importlib.util
import inspect
import json
import math
import random
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from dev.tools import json_prescan_prototype as prescan

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"


def _nested_arrays(depth: int, value: bytes = b"0") -> bytes:
    return b"[" * depth + value + b"]" * depth


def _nested_objects(depth: int, value: bytes = b"0") -> bytes:
    return b'{"k":' * depth + value + b"}" * depth


def _array_of_empty_arrays(children: int) -> bytes:
    return b"[" + b",".join(b"[]" for _ in range(children)) + b"]"


def _tree_nodes(value: object) -> int:
    if isinstance(value, _ObjectPairs):
        return 1 + sum(_tree_nodes(item) for _, item in value.pairs)
    if isinstance(value, list):
        return 1 + sum(_tree_nodes(item) for item in value)
    if isinstance(value, dict):
        return 1 + sum(_tree_nodes(item) for item in value.values())
    return 1


def _tree_depth(value: object, parent_depth: int = 0) -> int:
    if isinstance(value, _ObjectPairs):
        depth = parent_depth + 1
        return max(
            [depth, *(_tree_depth(item, depth) for _, item in value.pairs)]
        )
    if isinstance(value, (list, dict)):
        depth = parent_depth + 1
        children = value if isinstance(value, list) else value.values()
        return max([depth, *(_tree_depth(item, depth) for item in children)])
    return parent_depth


class _ObjectPairs:
    def __init__(self, pairs):
        self.pairs = pairs


def _preserve_object_pairs(pairs):
    return _ObjectPairs(pairs)


def _load_standalone_probe():
    name = "c0_multiformat_probe_test_copy"
    spec = importlib.util.spec_from_file_location(
        name,
        TOOLS_DIR / "c0_multiformat_probe.py",
    )
    assert spec is not None
    assert spec.loader is not None
    standalone = importlib.util.module_from_spec(spec)
    sys.modules[name] = standalone
    previous_dont_write_bytecode = sys.dont_write_bytecode
    try:
        spec.loader.exec_module(standalone)
    except Exception:
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return name, standalone


@pytest.mark.parametrize(
    ("payload", "expected_nodes", "expected_depth"),
    [
        (b"null", 1, 0),
        (b"true", 1, 0),
        (b"-12.5e+2", 1, 0),
        (b'"text"', 1, 0),
        (b"[]", 1, 1),
        (b"{}", 1, 1),
        (b'{"a":[1,true,null,{"b":"x"}]}', 7, 3),
    ],
)
def test_root_values_report_node_count_and_container_depth(
    payload: bytes,
    expected_nodes: int,
    expected_depth: int,
):
    assert prescan.prescan_json(payload) == (expected_nodes, expected_depth)


@pytest.mark.parametrize("_nested", [_nested_arrays, _nested_objects])
def test_exact_depth_limit_is_accepted_for_arrays_and_objects(_nested):
    payload = _nested(64)

    nodes, depth = prescan.prescan_json(payload)

    assert nodes == 65
    assert depth == 64


@pytest.mark.parametrize("_nested", [_nested_arrays, _nested_objects])
def test_depth_limit_plus_one_is_rejected_for_arrays_and_objects(_nested):
    with pytest.raises(prescan.JsonPreScanError, match="profondeur"):
        prescan.prescan_json(_nested(65))


def test_scanner_handles_deep_input_iteratively():
    assert prescan.prescan_json(_nested_arrays(1500), max_depth=1500) == (
        1501,
        1500,
    )


def test_exact_node_limit_counts_empty_array_children():
    payload = _array_of_empty_arrays(19_999)

    assert len(payload) < 256 * 1024
    assert prescan.prescan_json(payload) == (20_000, 2)


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (b"[1,2]", (3, 1)),
        (b'{"a":1,"b":2}', (3, 1)),
    ],
)
def test_scalar_and_object_node_limits_accept_exact_boundary(payload, expected):
    assert prescan.prescan_json(payload, max_nodes=3) == expected


@pytest.mark.parametrize("payload", [b"[1,2,3]", b'{"a":1,"b":2,"c":3}'])
def test_scalar_and_object_node_limits_reject_boundary_plus_one(payload):
    with pytest.raises(prescan.JsonPreScanError, match="nœuds"):
        prescan.prescan_json(payload, max_nodes=3)


def test_any_limit_plus_one_is_rejected_before_json_loads():
    over_limit_payloads = (
        (_array_of_empty_arrays(20_000), "nœuds"),
        (_nested_arrays(65), "profondeur"),
        (_nested_objects(65), "profondeur"),
    )
    loads = patch.object(prescan.json, "loads")

    with loads as json_loads:
        for payload, limit_name in over_limit_payloads:
            with pytest.raises(
                prescan.JsonPreScanError,
                match=limit_name,
            ):
                prescan.load_json_bounded(payload)

    json_loads.assert_not_called()


def test_json_loads_is_called_only_after_the_pre_scan(monkeypatch):
    payload = b'{"items":[1,2,3]}'
    real_loads = json.loads
    calls = []

    def tracked_loads(text, **kwargs):
        calls.append(text)
        return real_loads(text, **kwargs)

    monkeypatch.setattr(prescan.json, "loads", tracked_loads)

    value, nodes, depth = prescan.load_json_bounded(payload)

    assert isinstance(value, dict)
    assert value == {"items": [1, 2, 3]}
    assert (nodes, depth) == (5, 2)
    assert calls == ['{"items":[1,2,3]}']


def test_brackets_braces_and_escaped_quotes_inside_strings_are_not_structure():
    expected = 'brackets ] } { and backslash-quote: \\"'
    payload = json.dumps([expected]).encode("utf-8")

    assert prescan.load_json_bounded(payload) == ([expected], 2, 1)


def test_standard_string_escapes_and_raw_non_ascii_keys_are_supported():
    payload = b'{"caf\xc3\xa9":"\\/\\b\\f\\n\\r\\t"}'

    value, nodes, depth = prescan.load_json_bounded(payload)

    assert value == {"café": "/\b\f\n\r\t"}
    assert (nodes, depth) == (2, 1)


def test_whitespace_and_newlines_between_all_elements_are_supported():
    payload = b'{ \n "liste" : [ \n 1 , \n { "clef" : true } \n ] , \n "vide" : { } \n }'

    value, nodes, depth = prescan.load_json_bounded(payload)

    assert value == {"liste": [1, {"clef": True}], "vide": {}}
    assert (nodes, depth) == (6, 3)


def test_raw_control_character_inside_string_is_rejected():
    with pytest.raises(prescan.JsonPreScanError, match="contrôle"):
        prescan.load_json_bounded(b'"raw\x01control"')


def test_unicode_escapes_and_surrogate_pair_are_scanned_and_decoded():
    payload = rb'{"s":"\u0041\uD83D\uDE00"}'

    value, nodes, depth = prescan.load_json_bounded(payload)

    assert value == {"s": "A😀"}
    assert (nodes, depth) == (2, 1)


def test_escaped_backslash_before_quote_is_consumed_correctly():
    expected = 'backslash then quote: \\"'
    payload = json.dumps(expected).encode("utf-8")

    assert prescan.load_json_bounded(payload)[0] == expected


def test_long_string_under_candidate_file_size_is_accepted():
    prefix = b'{"text":"'
    suffix = b'"}'
    payload = prefix + b"x" * (256 * 1024 - len(prefix) - len(suffix) - 1) + suffix

    assert len(payload) < 256 * 1024
    value, nodes, depth = prescan.load_json_bounded(payload)

    assert isinstance(value, dict)
    assert len(value["text"]) > 250_000
    assert (nodes, depth) == (2, 1)


@pytest.mark.parametrize(
    "payload",
    [
        b'"\xff"',
        b"{}{}",
        b"[",
        b'{"x":0',
        b"[0}",
        b'{"x" 0}',
        b"[1,]",
        b'{"x":1,}',
        b'"bad\\u0G00"',
        b'"unclosed',
    ],
)
def test_invalid_utf8_trailing_data_and_bad_syntax_are_rejected(payload):
    with pytest.raises(prescan.JsonPreScanError):
        prescan.prescan_json(payload)


def test_one_initial_utf8_bom_is_removed():
    payload = b"\xef\xbb\xbf" + b'{"ok":true}'

    assert prescan.prescan_json(payload) == (2, 1)
    assert prescan.load_json_bounded(payload) == ({"ok": True}, 2, 1)


def test_double_initial_utf8_bom_is_rejected():
    with pytest.raises(prescan.JsonPreScanError):
        prescan.load_json_bounded(b"\xef\xbb\xbf\xef\xbb\xbf{}")


@pytest.mark.parametrize("payload", [b"NaN", b"Infinity", b"-Infinity"])
def test_non_json_constants_are_rejected(payload):
    with pytest.raises(prescan.JsonPreScanError):
        prescan.load_json_bounded(payload)


def test_float_overflow_that_decodes_to_infinity_is_rejected():
    with pytest.raises(prescan.JsonPreScanError, match="fini"):
        prescan.load_json_bounded(b"1e9999")


@pytest.mark.parametrize(
    "payload",
    [b'{"same":1,"same":2}', rb'{"same":1,"\u0073ame":2}'],
)
def test_load_json_bounded_rejects_duplicate_keys_after_decoding(payload):
    with pytest.raises(prescan.JsonPreScanError, match="dupliqu"):
        prescan.load_json_bounded(payload)


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (b"-0", 0),
        (b"1E+2", 100.0),
    ],
)
def test_valid_number_forms_are_accepted(payload, expected):
    assert prescan.load_json_bounded(payload)[0] == expected


@pytest.mark.parametrize("payload", [b"01", b"+1", b".5", b"1."])
def test_invalid_number_forms_are_rejected(payload):
    with pytest.raises(prescan.JsonPreScanError):
        prescan.load_json_bounded(payload)


def test_numeric_literal_candidate_accepts_exact_limit():
    payload = b"1" + b"0" * (prescan.CANDIDATE_MAX_NUMBER_CHARS - 1)

    value, nodes, depth = prescan.load_json_bounded(payload)

    assert len(str(value)) == prescan.CANDIDATE_MAX_NUMBER_CHARS
    assert (nodes, depth) == (1, 0)


@pytest.mark.parametrize("digit_count", [1001, 5000])
def test_numeric_literal_candidate_rejects_long_integers_before_json_loads(
    digit_count,
):
    payload = b"1" + b"0" * (digit_count - 1)
    with (
        patch.object(prescan.json, "loads") as json_loads,
        pytest.raises(prescan.JsonPreScanError, match="numérique"),
    ):
        prescan.load_json_bounded(payload)
    json_loads.assert_not_called()


def test_json_loads_value_error_is_wrapped_with_original_cause(monkeypatch):
    original = ValueError("integer conversion failed")

    def fail_loads(*args, **kwargs):
        raise original

    monkeypatch.setattr(prescan.json, "loads", fail_loads)

    with pytest.raises(prescan.JsonPreScanError) as error:
        prescan.load_json_bounded(b"1")

    assert error.value.__cause__ is original


def test_fixed_seed_valid_documents_have_exact_tree_counts():
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

    for _ in range(100):
        payload = json.dumps(make_value(), ensure_ascii=True).encode("utf-8")
        decoded = json.loads(payload)
        nodes, depth = prescan.prescan_json(
            payload,
            max_depth=100,
            max_nodes=10_000,
        )

        assert (nodes, depth) == (_tree_nodes(decoded), _tree_depth(decoded))


def test_fixed_seed_byte_mutations_match_json_loads_for_accepted_text():
    seed = 20261126
    rng = random.Random(seed)
    corpus = [
        b'{"value":"abcdefghijklmnopqrst","items":[1,true,null]}',
        b'{"value":"uvwxyzABCDEFGHIJKLMN","items":[2,false,null]}',
        b'{"value":"0123456789abcdefghij","items":[3,true,null]}',
    ]
    mutation_bytes = b'[]{},:"\\0123456789-+.eEtrufalsn'
    structural_bytes = b'[]{},:' + bytes((ord('"'), ord("\\")))

    def reject_non_finite(value: str):
        raise ValueError(f"non-finite value: {value}")

    def parse_finite_float(value: str):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError(f"non-finite float: {value}")
        return parsed

    def preserve_unique_object_pairs(pairs):
        if len(dict(pairs)) != len(pairs):
            raise ValueError("duplicate object key")
        return _preserve_object_pairs(pairs)

    def assert_differential(candidate: bytes, case_number: str):
        decoded = None
        reference_accepts = False
        try:
            decoded = json.loads(
                candidate.decode("utf-8", errors="strict"),
                parse_constant=reject_non_finite,
                parse_float=parse_finite_float,
                object_pairs_hook=preserve_unique_object_pairs,
            )
            reference_accepts = True
        except (UnicodeDecodeError, ValueError):
            pass

        counts = None
        try:
            counts = prescan.prescan_json(
                candidate,
                max_depth=100,
                max_nodes=10_000,
            )
        except Exception as exc:
            if not isinstance(exc, prescan.JsonPreScanError):
                pytest.fail(
                    f"exception inattendue; seed={seed}, case={case_number}, "
                    f"bytes={candidate!r}, cause={type(exc).__name__}: {exc}"
                )
            counts = None
        prescan_accepts = counts is not None

        if reference_accepts and not prescan_accepts:
            pytest.fail(
                f"pré-scan a rejeté un texte accepté par json.loads; "
                f"seed={seed}, case={case_number}, bytes={candidate!r}, "
                "non-finis et clés dupliquées exclus"
            )
        if prescan_accepts and not reference_accepts:
            pytest.fail(
                f"pré-scan a accepté un texte rejeté par json.loads; "
                f"seed={seed}, case={case_number}, bytes={candidate!r}"
            )
        if not reference_accepts:
            return

        expected = (_tree_nodes(decoded), _tree_depth(decoded))
        assert counts == expected, (
            f"comptes divergents; seed={seed}, case={case_number}, "
            f"bytes={candidate!r}, counts={counts}, tree={expected}"
        )

    for corpus_index, candidate in enumerate(corpus):
        assert_differential(candidate, f"corpus-{corpus_index}")

    for case_number in range(2500):
        payload = bytearray(rng.choice(corpus))
        if case_number % 2 == 0:
            positions = [
                index
                for index, value in enumerate(payload)
                if value in structural_bytes
            ]
        else:
            positions = list(range(len(payload)))
        position = rng.choice(positions)
        replacement = rng.choice(mutation_bytes)
        while replacement == payload[position]:
            replacement = rng.choice(mutation_bytes)
        payload[position] = replacement
        candidate = bytes(payload)
        assert_differential(candidate, str(case_number))


def test_standalone_probe_contains_identical_scanner_copy():
    previous_dont_write_bytecode = sys.dont_write_bytecode
    name, standalone = _load_standalone_probe()
    try:
        assert standalone.DEFAULT_MAX_DEPTH == prescan.DEFAULT_MAX_DEPTH
        assert standalone.DEFAULT_MAX_NODES == prescan.DEFAULT_MAX_NODES
        assert (
            standalone.CANDIDATE_MAX_NUMBER_CHARS
            == prescan.CANDIDATE_MAX_NUMBER_CHARS
        )
        for symbol in (
            "JsonPreScanError",
            "_prescan_text",
            "_decode_utf8",
            "prescan_json",
            "load_json_bounded",
        ):
            assert inspect.getsource(getattr(prescan, symbol)) == inspect.getsource(
                getattr(standalone, symbol)
            )
    finally:
        sys.modules.pop(name, None)
        sys.dont_write_bytecode = previous_dont_write_bytecode
    assert sys.dont_write_bytecode is previous_dont_write_bytecode


def test_probe_records_a_failure_and_runs_later_checks(capsys):
    name, standalone = _load_standalone_probe()
    try:
        standalone.CHECKS.clear()

        def fail_check():
            raise RuntimeError("expected test failure")

        assert standalone._run_check("first check", fail_check) is False
        assert standalone._run_check("second check", lambda: "ran") is True
        standalone._skip_check("optional check", "not requested")
        assert standalone.CHECKS == [
            ("first check", False, "RuntimeError: expected test failure"),
            ("second check", True, "ran"),
            ("optional check", None, "not requested"),
        ]
        standalone.CHECKS[:] = [
            ("second check", True, "ran"),
            ("optional check", None, "not requested"),
        ]
        standalone.START_TIME = standalone.time.perf_counter()
        with patch.object(standalone, "_physical_memory_bytes", return_value=None):
            assert standalone._emit_report("complet") is True
    finally:
        sys.modules.pop(name, None)
    output = capsys.readouterr().out
    assert "[ÉCHEC] first check:" in output
    assert "[SKIP] optional check: not requested" in output
    assert "checks=second check=OK,optional check=SKIP" in output
