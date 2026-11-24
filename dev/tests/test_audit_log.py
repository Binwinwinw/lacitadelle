import importlib
import json
import sqlite3
import sys
import urllib.request
from contextlib import closing
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(TESTS_DIR.parent / "tools"))

citadelle_memory = importlib.import_module("citadelle_memory")
test_helpers = importlib.import_module("_helpers")
login_server = test_helpers.login_server
SESSION_COOKIE_NAME = test_helpers.SESSION_COOKIE_NAME
api_test_context = test_helpers.api_test_context
api_post = test_helpers.api_post
login_as = test_helpers.login_as
open_no_redirect = test_helpers.open_no_redirect
create_test_user = test_helpers.create_test_user


def _delete_document_http(opener, base_url: str, token: str, document_id: int):
    csrf_token = login_server.csrf_token_for_session(token)
    assert csrf_token is not None
    request = urllib.request.Request(
        f"{base_url}/api/chat/document/{document_id}",
        headers={
            "Cookie": f"{SESSION_COOKIE_NAME}={token}",
            "X-CSRF-Token": csrf_token,
        },
        method="DELETE",
    )
    return open_no_redirect(opener, request)


def _prepare_v11_database(db_path: Path) -> tuple[int, int]:
    citadelle_memory.migrate_to_v3(db_path)
    citadelle_memory.migrate_to_v4(db_path)
    citadelle_memory.migrate_to_v5(db_path)
    citadelle_memory.migrate_to_v6(db_path)
    citadelle_memory.migrate_to_v8(db_path)
    citadelle_memory.migrate_to_v9(db_path)
    citadelle_memory.migrate_to_v10(db_path)
    citadelle_memory.migrate_to_v11(db_path)
    user_id = create_test_user(db_path, "audit-user", "secret123")
    session_id = citadelle_memory.create_session_for_user(
        user_id,
        db_path=db_path,
    )
    return user_id, session_id


def test_document_delete_writes_redacted_audit_row(tmp_path):
    db_path = tmp_path / "audit.db"
    user_id, session_id = _prepare_v11_database(db_path)
    metadata = {"file_name": "audit.md", "classification": "public"}
    document_id = citadelle_memory.add_conversation_document(
        user_id,
        session_id,
        "do not retain this content",
        metadata,
        db_path=db_path,
    )
    assert document_id is not None

    citadelle_memory.migrate_to_v12(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "DELETE FROM conversation_documents WHERE id = ?",
            (document_id,),
        )
        rows = conn.execute(
            "SELECT table_name, action, row_id, user_id, session_id, old_data "
            "FROM audit_log"
        ).fetchall()

    assert len(rows) == 1
    table_name, action, row_id, logged_user_id, logged_session_id, old_data = rows[0]
    archived = json.loads(old_data)
    assert (table_name, action, row_id, logged_user_id, logged_session_id) == (
        "conversation_documents",
        "DELETE",
        document_id,
        user_id,
        session_id,
    )
    assert archived["id"] == document_id
    assert archived["session_id"] == session_id
    assert archived["user_id"] == user_id
    assert archived["metadata"] == metadata
    assert archived["content_redacted"] is True
    assert "content" not in archived


def test_session_delete_writes_audit_row_with_deleted_fields(tmp_path):
    db_path = tmp_path / "audit-session.db"
    user_id, session_id = _prepare_v11_database(db_path)
    citadelle_memory.migrate_to_v12(db_path)

    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        rows = conn.execute(
            "SELECT table_name, action, row_id, user_id, session_id, old_data "
            "FROM audit_log"
        ).fetchall()

    assert len(rows) == 1
    table_name, action, row_id, logged_user_id, logged_session_id, old_data = rows[0]
    archived = json.loads(old_data)
    assert (table_name, action, row_id, logged_user_id, logged_session_id) == (
        "sessions",
        "DELETE",
        session_id,
        user_id,
        session_id,
    )
    assert archived["id"] == session_id
    assert archived["user_id"] == user_id
    assert "created_at" in archived
    assert "updated_at" in archived


def test_session_delete_audits_cascaded_document_delete(tmp_path):
    db_path = tmp_path / "audit-cascade.db"
    user_id, session_id = _prepare_v11_database(db_path)
    document_id = citadelle_memory.add_conversation_document(
        user_id,
        session_id,
        "do not retain this content",
        {"file_name": "cascade.md"},
        db_path=db_path,
    )
    assert document_id is not None
    citadelle_memory.migrate_to_v13(db_path)

    citadelle_memory.delete_session(session_id, db_path=db_path)

    with closing(sqlite3.connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT table_name, row_id, user_id, session_id, old_data "
            "FROM audit_log"
        ).fetchall()

    assert {
        (table_name, row_id, logged_user_id, logged_session_id)
        for table_name, row_id, logged_user_id, logged_session_id, _ in rows
    } == {
        ("conversation_documents", document_id, user_id, session_id),
        ("sessions", session_id, user_id, session_id),
    }
    document_audit = next(
        old_data
        for table_name, _, _, _, old_data in rows
        if table_name == "conversation_documents"
    )
    archived = json.loads(document_audit)
    assert archived["content_redacted"] is True
    assert "content" not in archived


def test_v12_migration_is_idempotent_and_preserves_existing_rows(tmp_path):
    db_path = tmp_path / "audit-migration.db"
    user_id, session_id = _prepare_v11_database(db_path)
    citadelle_memory.add_message(
        session_id,
        "user",
        "message préexistant",
        db_path=db_path,
    )
    document_id = citadelle_memory.add_conversation_document(
        user_id,
        session_id,
        "document préexistant",
        {"file_name": "existing.md"},
        db_path=db_path,
    )
    assert document_id is not None

    citadelle_memory.migrate_to_v12(db_path)
    citadelle_memory.migrate_to_v13(db_path)
    citadelle_memory.migrate_to_v13(db_path)

    with closing(sqlite3.connect(db_path)) as conn:
        trigger_count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type = 'trigger' AND name IN ("
            "'audit_conversation_documents_delete', "
            "'audit_sessions_delete')"
        ).fetchone()[0]
        audit_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(audit_log)")
        }
        message = conn.execute(
            "SELECT content FROM messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        document = conn.execute(
            "SELECT content FROM conversation_documents WHERE id = ?",
            (document_id,),
        ).fetchone()

    assert trigger_count == 2
    assert "actor_id" in audit_columns
    assert message == ("message préexistant",)
    assert document == ("document préexistant",)


def test_document_delete_records_authenticated_actor_and_direct_sql_is_unknown():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v13(db_path)
        user_id = create_test_user(
            db_path,
            "audit-admin",
            "secret123",
            role="admin",
        )
        session_id = citadelle_memory.create_session_for_user(
            user_id,
            db_path=db_path,
        )
        document_id = citadelle_memory.add_conversation_document(
            user_id,
            session_id,
            "authenticated delete test",
            {"file_name": "api.md"},
            db_path=db_path,
        )
        assert document_id is not None
        token = login_as(opener, base_url, "audit-admin", "secret123")

        response = _delete_document_http(
            opener,
            base_url,
            token,
            document_id,
        )
        assert response.code == 200
        response.close()

        direct_document_id = citadelle_memory.add_conversation_document(
            user_id,
            session_id,
            "direct SQL delete test",
            {"file_name": "direct.md"},
            db_path=db_path,
        )
        assert direct_document_id is not None
        with closing(sqlite3.connect(db_path)) as conn:
            conn.execute(
                "DELETE FROM conversation_documents WHERE id = ?",
                (direct_document_id,),
            )
            audit_rows = conn.execute(
                "SELECT row_id, user_id, session_id, actor_id "
                "FROM audit_log ORDER BY id"
            ).fetchall()

    assert audit_rows == [
        (document_id, user_id, session_id, user_id),
        (direct_document_id, user_id, session_id, None),
    ]


def test_admin_user_delete_records_actor_for_cascaded_rows():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v13(db_path)
        actor_id = create_test_user(
            db_path,
            "audit-admin",
            "secret123",
            role="admin",
        )
        owner_id = create_test_user(db_path, "audit-owner", "secret123")
        session_id = citadelle_memory.create_session_for_user(
            owner_id,
            db_path=db_path,
        )
        document_id = citadelle_memory.add_conversation_document(
            owner_id,
            session_id,
            "cascade actor test",
            {"file_name": "cascade.md"},
            db_path=db_path,
        )
        assert document_id is not None
        token = login_as(opener, base_url, "audit-admin", "secret123")

        response = api_post(
            opener,
            base_url,
            f"/api/admin/users/{owner_id}/delete",
            token,
        )
        assert response.code == 200
        response.close()

        with closing(sqlite3.connect(db_path)) as conn:
            audit_rows = conn.execute(
                "SELECT table_name, row_id, user_id, session_id, actor_id "
                "FROM audit_log ORDER BY id"
            ).fetchall()

    assert set(audit_rows) == {
        (
            "conversation_documents",
            document_id,
            owner_id,
            session_id,
            actor_id,
        ),
        ("sessions", session_id, owner_id, session_id, actor_id),
    }
