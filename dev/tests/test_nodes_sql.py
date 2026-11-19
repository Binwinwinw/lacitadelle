"""Tests des nœuds SQL en lecture seule et de recherche Web non configurée."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from nodes.query_sql import query_sql
from nodes.search_web import search_web


def test_query_sql_returns_select_rows_as_dicts():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE items (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO items VALUES (?, ?)", (1, "Nexxus"))

    rows = query_sql(
        conn,
        "SELECT name FROM items WHERE id = ?",
        (1,),
    )

    assert rows == [{"name": "Nexxus"}]
    conn.close()


def test_query_sql_refuses_non_select_and_preserves_data():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE items (id INTEGER)")
    conn.execute("INSERT INTO items VALUES (1)")

    with pytest.raises(
        ValueError,
        match="Seules les requêtes SELECT sont autorisées",
    ):
        query_sql(conn, "DELETE FROM items")

    assert conn.execute("SELECT id FROM items").fetchall() == [(1,)]
    conn.close()


def test_search_web_reports_unconfigured_offline_api():
    with pytest.raises(
        NotImplementedError,
        match="API web non configurée \\(hors ligne\\)",
    ):
        search_web("La Citadelle")
