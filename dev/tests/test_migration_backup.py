import sqlite3
import sys
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import citadelle_memory


def test_migration_creates_backup_when_data_exists(tmp_path):
    db_path = tmp_path / "test.db"
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "CREATE TABLE messages (id INTEGER PRIMARY KEY, content TEXT)"
        )
        conn.execute(
            "INSERT INTO messages (content) VALUES (?)",
            ("ancien message",),
        )
        conn.commit()

    citadelle_memory.migrate_to_v3(db_path)

    backups = list(tmp_path.glob("*.backup-*"))
    assert len(backups) == 1
    with closing(sqlite3.connect(backups[0])) as backup:
        assert backup.execute(
            "SELECT content FROM messages"
        ).fetchone() == ("ancien message",)


def test_migration_no_backup_when_empty(tmp_path):
    db_path = tmp_path / "empty.db"
    with closing(sqlite3.connect(db_path)):
        pass

    citadelle_memory.migrate_to_v3(db_path)

    assert list(tmp_path.glob("*.backup-*")) == []
