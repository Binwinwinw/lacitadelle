"""Tests pour hash_password, verify_password et generate_strong_password."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from citadelle_memory import (
    SCRYPT_HASH_BYTES,
    SCRYPT_N,
    SCRYPT_P,
    SCRYPT_R,
    SCRYPT_SALT_BYTES,
    generate_strong_password,
    hash_password,
    verify_password,
)


def test_hash_format():
    stored_hash = hash_password("secret123!")
    parts = stored_hash.split("$")
    assert len(parts) == 6
    assert parts[0] == "scrypt"
    assert int(parts[1]) == SCRYPT_N
    assert int(parts[2]) == SCRYPT_R
    assert int(parts[3]) == SCRYPT_P
    assert len(bytes.fromhex(parts[4])) == SCRYPT_SALT_BYTES
    assert len(bytes.fromhex(parts[5])) == SCRYPT_HASH_BYTES


def test_verify_ok():
    stored_hash = hash_password("secret123!")
    assert verify_password("secret123!", stored_hash) is True


def test_verify_wrong_password():
    stored_hash = hash_password("secret123!")
    assert verify_password("wrong", stored_hash) is False


def test_verify_invalid_format():
    assert verify_password("x", "not-a-valid-hash") is False
    assert verify_password("x", "scrypt$16384$8$1$zz$zz") is False
    assert verify_password("x", "scrypt$999999999$8$1$00$00") is False


def test_hash_random_salt():
    assert hash_password("same") != hash_password("same")


def test_generate_strong_password_length():
    assert len(generate_strong_password(16)) == 16


def test_generate_strong_password_categories():
    password = generate_strong_password(16)
    assert any(char.islower() for char in password)
    assert any(char.isupper() for char in password)
    assert any(char.isdigit() for char in password)
    assert any(char in "!@#$%^&*" for char in password)


def test_generate_strong_password_min_length():
    try:
        generate_strong_password(15)
        assert False, "Devrait lever ValueError"
    except ValueError:
        pass


def run_all():
    tests = [
        test_hash_format,
        test_verify_ok,
        test_verify_wrong_password,
        test_verify_invalid_format,
        test_hash_random_salt,
        test_generate_strong_password_length,
        test_generate_strong_password_categories,
        test_generate_strong_password_min_length,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()