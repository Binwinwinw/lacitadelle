"""Tests for the V6 settings table and helpers."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import citadelle_memory


def test_migrate_to_v6_is_idempotent_and_init_db_applies_it():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"

        citadelle_memory.init_db(db_path)
        citadelle_memory.migrate_to_v6(db_path)
        citadelle_memory.migrate_to_v6(db_path)

        with citadelle_memory._connect(db_path) as conn:
            table = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name = 'settings'"
            ).fetchone()
            columns = [
                row["name"]
                for row in conn.execute("PRAGMA table_info(settings)")
            ]
            row_count = conn.execute(
                "SELECT COUNT(*) FROM settings"
            ).fetchone()[0]

        assert table is not None
        assert columns == ["key", "value", "updated_at"]
        assert row_count == 0


def test_get_setting_returns_default_for_unknown_key():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        citadelle_memory.migrate_to_v6(db_path)

        assert citadelle_memory.get_setting(
            "unknown_key",
            default="fallback",
            db_path=db_path,
        ) == "fallback"
        assert citadelle_memory.get_setting(
            "unknown_key",
            db_path=db_path,
        ) is None


def test_set_get_setting():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        citadelle_memory.migrate_to_v6(db_path)

        citadelle_memory.set_setting(
            "current_model_path",
            "/path/to/model.gguf",
            db_path=db_path,
        )

        assert citadelle_memory.get_setting(
            "current_model_path",
            db_path=db_path,
        ) == "/path/to/model.gguf"


def test_set_setting_upserts_existing_key():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        citadelle_memory.migrate_to_v6(db_path)

        citadelle_memory.set_setting("key", "v1", db_path=db_path)
        citadelle_memory.set_setting("key", "v2", db_path=db_path)

        assert citadelle_memory.get_setting("key", db_path=db_path) == "v2"
        with citadelle_memory._connect(db_path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM settings WHERE key = ?",
                ("key",),
            ).fetchone()[0]
        assert count == 1


def run_all():
    tests = [
        test_migrate_to_v6_is_idempotent_and_init_db_applies_it,
        test_get_setting_returns_default_for_unknown_key,
        test_set_get_setting,
        test_set_setting_upserts_existing_key,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: OK")
    print(f"ALL {len(tests)} TESTS PASSED")


if __name__ == "__main__":
    run_all()
