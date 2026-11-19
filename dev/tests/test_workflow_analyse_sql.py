"""Test du workflow SQL sur une base SQLite temporaire."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflows"))

import citadelle_memory
import workflow_engine
from analyse_sql import analyse_sql


def test_analyse_sql_queries_database_and_calls_model(tmp_path, monkeypatch):
    db_path = tmp_path / "workflow.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO items VALUES (1, 'Nexxus')")
    conn.commit()
    conn.close()
    monkeypatch.setattr(citadelle_memory, "DB_PATH", db_path)
    calls = []

    def fake_call_model(prompt, model_path, timeout):
        calls.append((prompt, model_path, timeout))
        return "Nexxus"

    monkeypatch.setattr(workflow_engine, "call_model", fake_call_model)

    result = analyse_sql(
        "SELECT name FROM items WHERE id = 1",
        "Quel est le nom ?",
    )

    assert result == "Nexxus"
    assert len(calls) == 1
    assert "Nexxus" in calls[0][0]
    assert calls[0][2] == 180
    with sqlite3.connect(db_path) as check_conn:
        assert check_conn.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 1
