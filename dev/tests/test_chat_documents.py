import importlib
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pytest

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(TESTS_DIR.parent / "tools"))

citadelle_memory = importlib.import_module("citadelle_memory")
login_server = importlib.import_module("login_server")
extract_text = importlib.import_module("nodes.extract_text")
test_helpers = importlib.import_module("_helpers")
SESSION_COOKIE_NAME = test_helpers.SESSION_COOKIE_NAME
api_post = test_helpers.api_post
api_test_context = test_helpers.api_test_context
create_test_user = test_helpers.create_test_user
login_as = test_helpers.login_as
open_no_redirect = test_helpers.open_no_redirect


def _upload(
    opener,
    base_url: str,
    token: str,
    session_id: int,
    filename: str,
    content: bytes,
    *,
    add_csrf: bool = True,
):
    boundary = b"CitadelleBoundary7f5a"
    body = (
        b"--" + boundary + b"\r\n"
        b'Content-Disposition: form-data; name="session_id"\r\n\r\n'
        + str(session_id).encode("ascii")
        + b"\r\n--"
        + boundary
        + b"\r\nContent-Disposition: form-data; name=\"file\"; "
        + f'filename="{filename}"'.encode()
        + b"\r\nContent-Type: text/markdown; charset=utf-8\r\n\r\n"
        + content
        + b"\r\n--"
        + boundary
        + b"--\r\n"
    )
    request = urllib.request.Request(
        f"{base_url}/api/chat/upload",
        data=body,
        headers={
            "Cookie": f"{SESSION_COOKIE_NAME}={token}",
            "Content-Type": (
                "multipart/form-data; boundary="
                + boundary.decode("ascii")
            ),
        },
        method="POST",
    )
    if add_csrf:
        return open_no_redirect(opener, request)
    try:
        return opener.open(request, timeout=5)
    except urllib.error.HTTPError as response:
        return response


def _delete_document(opener, base_url: str, token: str, document_id: int):
    request = urllib.request.Request(
        f"{base_url}/api/chat/document/{document_id}",
        headers={
            "Cookie": f"{SESSION_COOKIE_NAME}={token}",
            "X-CSRF-Token": login_server.csrf_token_for_session(token),
        },
        method="DELETE",
    )
    return open_no_redirect(opener, request)


def _json_response(response) -> dict:
    try:
        return json.loads(response.read().decode("utf-8"))
    finally:
        response.close()


def _new_session(user_id: int, db_path: Path) -> int:
    return citadelle_memory.create_session_for_user(user_id, db_path=db_path)


def test_v11_migration_is_idempotent_and_preserves_existing_messages(tmp_path):
    db_path = tmp_path / "chat-documents.db"
    citadelle_memory.migrate_to_v3(db_path)
    citadelle_memory.migrate_to_v4(db_path)
    citadelle_memory.migrate_to_v5(db_path)
    citadelle_memory.migrate_to_v6(db_path)
    citadelle_memory.migrate_to_v8(db_path)
    citadelle_memory.migrate_to_v9(db_path)
    citadelle_memory.migrate_to_v10(db_path)
    citadelle_memory.set_setting(
        "allowed_models",
        '["keep-this-model.gguf"]',
        db_path=db_path,
    )
    user_id = create_test_user(db_path, "alice", "secret123")
    session_id = _new_session(user_id, db_path)
    citadelle_memory.add_message(
        session_id,
        "user",
        "historique conservé",
        db_path=db_path,
    )

    citadelle_memory.migrate_to_v11(db_path)
    document_id = citadelle_memory.add_conversation_document(
        user_id,
        session_id,
        "document avant répétition migration",
        {"file_name": "notes.md"},
        db_path=db_path,
    )
    citadelle_memory.migrate_to_v11(db_path)

    with closing(sqlite3.connect(db_path)) as conn:
        assert conn.execute(
            "SELECT content FROM messages WHERE session_id = ?",
            (session_id,),
        ).fetchone() == ("historique conservé",)
        assert conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'conversation_documents'"
        ).fetchone() == ("conversation_documents",)
        assert conn.execute(
            "SELECT value FROM settings WHERE key = 'allowed_models'"
        ).fetchone() == ('["keep-this-model.gguf"]',)
        assert conn.execute(
            "SELECT content FROM conversation_documents WHERE id = ?",
            (document_id,),
        ).fetchone() == ("document avant répétition migration",)
        indexes = conn.execute(
            "PRAGMA index_list(conversation_documents)"
        ).fetchall()
        assert any(row[2] == 1 for row in indexes)


def test_markdown_extraction_checks_utf8_size_and_classification(tmp_path):
    markdown = tmp_path / "notes.md"
    markdown.write_bytes("contenu UTF-8 é".encode())

    content, metadata = extract_text.extract_markdown_document(
        markdown,
        "user",
    )

    assert content == "contenu UTF-8 é"
    assert metadata["file_name"] == "notes.md"
    assert metadata["classification"] == "public"

    markdown.write_bytes(b"\xff")
    with pytest.raises(extract_text.ExtractTextError):
        extract_text.extract_markdown_document(markdown, "user")

    markdown.write_bytes(b"x" * 200_001)
    with pytest.raises(extract_text.ExtractTextError):
        extract_text.extract_markdown_document(markdown, "user")


def test_sensitive_markdown_is_admin_only_and_critical_is_refused(tmp_path):
    sensitive = tmp_path / ".env.private.md"
    sensitive.write_text("secret text", encoding="utf-8")

    with pytest.raises(PermissionError):
        extract_text.extract_markdown_document(sensitive, "user")

    content, metadata = extract_text.extract_markdown_document(
        sensitive,
        "admin",
    )
    assert content == "secret text"
    assert metadata["classification"] == "sensitive"

    sensitive.write_bytes(b"MZ executable marker")
    with pytest.raises(PermissionError):
        extract_text.extract_markdown_document(sensitive, "admin")


def test_long_document_uses_bounded_document_scoped_retrieval():
    first_document = (
        "\n\n".join(
            f"Section {index} common body words for this document."
            for index in range(400)
        )
        + "\n\nspecialtarget appears in the final section."
    )
    second_document = "\n\n".join(
        f"Section {index} otherdocument words without the requested term."
        for index in range(400)
    )

    excerpt, is_partial = login_server._build_document_context(
        first_document,
        "specialtarget",
    )
    other_excerpt, other_is_partial = login_server._build_document_context(
        second_document,
        "specialtarget",
    )

    assert is_partial
    assert len(excerpt) <= 6_000
    assert "specialtarget" in excerpt
    assert other_is_partial
    assert "specialtarget" not in other_excerpt


def test_upload_followup_and_reload_reuse_the_conversation_document():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        user_id = create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        session_id = _new_session(user_id, db_path)
        private_text = "Les clés de la Citadelle sont bleues."

        with _upload(
            opener,
            base_url,
            token,
            session_id,
            "notes.md",
            private_text.encode(),
        ) as response:
            assert response.code == 201
            document = _json_response(response)
        assert document["status"] == "attached"

        with patch.object(
            login_server,
            "call_llamafile",
            return_value="Réponse modèle",
        ) as call_model:
            with api_post(
                opener,
                base_url,
                f"/api/sessions/{session_id}/messages",
                token,
                {"content": "Quelle est la couleur des clés ?", "stream": False},
            ) as response:
                assert response.code == 201
            first_prompt = call_model.call_args_list[0][0][0][-1]["content"]
            assert private_text in first_prompt
            assert call_model.call_args_list[0][1]["max_tokens"] == 1024

            with open_no_redirect(
                opener,
                urllib.request.Request(
                    f"{base_url}/api/sessions/{session_id}/messages",
                    headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"},
                ),
            ) as response:
                reloaded_history = _json_response(response)
            assert reloaded_history["document"]["metadata"]["file_name"] == (
                "notes.md"
            )

            with api_post(
                opener,
                base_url,
                f"/api/sessions/{session_id}/messages",
                token,
                {"content": "Rappelle-moi la couleur.", "stream": False},
            ) as response:
                assert response.code == 201
            second_prompt = call_model.call_args_list[1][0][0][-1]["content"]
            assert private_text in second_prompt

        with open_no_redirect(
            opener,
            urllib.request.Request(
                f"{base_url}/api/sessions/{session_id}/messages",
                headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"},
            ),
        ) as response:
            history = _json_response(response)
        assert history["document"]["metadata"]["file_name"] == "notes.md"
        assert len(history["messages"]) == 4
        assert all(
            private_text not in message["content"]
            for message in history["messages"]
        )


def test_second_document_is_rejected_without_replacing_the_first():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        user_id = create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        session_id = _new_session(user_id, db_path)

        first = _upload(
            opener, base_url, token, session_id, "first.md", b"first"
        )
        first_data = _json_response(first)
        second = _upload(
            opener, base_url, token, session_id, "second.md", b"second"
        )

        assert second.code == 409
        second.close()
        with closing(sqlite3.connect(db_path)) as conn:
            row = conn.execute(
                "SELECT id, content FROM conversation_documents "
                "WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        assert row == (first_data["document_id"], "first")


def test_upload_enforces_format_classification_and_size_limits():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        credential = "alice"
        user_id = create_test_user(db_path, "alice", credential)
        cookie = login_as(opener, base_url, "alice", credential)
        session_id = _new_session(user_id, db_path)

        for filename in ("notes.csv", "notes.json", "notes.bin"):
            with _upload(
                opener, base_url, cookie, session_id, filename, b"plain"
            ) as response:
                assert response.code == 415

        for filename, content, expected_status in (
            ("empty.md", b"", 400),
            ("invalid.md", b"\xff", 400),
            ("critical.md", b"MZ executable marker", 403),
            ("oversized.md", b"x" * (256 * 1024 + 1), 413),
            ("too-many-chars.md", b"x" * 200_001, 413),
        ):
            with _upload(
                opener, base_url, cookie, session_id, filename, content
            ) as response:
                assert response.code == expected_status


@pytest.mark.parametrize(
    ("filename", "username", "role"),
    (
        ("notes.md", "alice", "user"),
        ("notes.txt", "alice", "user"),
        ("notes.sql", "admin", "admin"),
    ),
)
def test_chat_text_formats_match_markdown_utf8_bom_and_control_rules(
    filename,
    username,
    role,
):
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        credential = username
        user_id = create_test_user(
            db_path,
            username,
            credential,
            role=role,
        )
        session_cookie = login_as(opener, base_url, username, credential)
        session_id = _new_session(user_id, db_path)

        with _upload(
            opener,
            base_url,
            session_cookie,
            session_id,
            filename,
            b"\xef\xbb\xbftext\x01",
        ) as response:
            assert response.code == 201
            data = _json_response(response)

        assert data["metadata"]["file_name"] == filename
        with closing(sqlite3.connect(db_path)) as conn:
            assert conn.execute(
                "SELECT content FROM conversation_documents WHERE session_id = ?",
                (session_id,),
            ).fetchone() == ("\ufefftext\x01",)

        for content in (b"", b"\xff", b"before\x00after"):
            error_session_id = _new_session(user_id, db_path)
            with _upload(
                opener,
                base_url,
                session_cookie,
                error_session_id,
                filename,
                content,
            ) as response:
                assert response.code == 400


def test_sql_upload_is_admin_only_and_stored_without_execution():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        user_credential = "alice"
        admin_credential = "admin"
        user_id = create_test_user(db_path, "alice", user_credential)
        admin_id = create_test_user(
            db_path,
            "admin",
            admin_credential,
            role="admin",
        )
        user_session = login_as(opener, base_url, "alice", user_credential)
        admin_session = login_as(opener, base_url, "admin", admin_credential)
        user_session_id = _new_session(user_id, db_path)
        admin_session_id = _new_session(admin_id, db_path)
        sql_text = "DROP TABLE users; -- texte uniquement"

        with _upload(
            opener,
            base_url,
            user_session,
            user_session_id,
            "notes.sql",
            sql_text.encode("utf-8"),
        ) as response:
            assert response.code == 403

        with _upload(
            opener,
            base_url,
            admin_session,
            admin_session_id,
            "notes.sql",
            sql_text.encode("utf-8"),
        ) as response:
            assert response.code == 201
            data = _json_response(response)

        assert data["metadata"]["classification"] == "sensitive"
        with closing(sqlite3.connect(db_path)) as conn:
            assert conn.execute(
                "SELECT content FROM conversation_documents WHERE session_id = ?",
                (admin_session_id,),
            ).fetchone() == (sql_text,)
            assert conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name = 'users'"
            ).fetchone() == ("users",)


def test_text_upload_limits_accept_exact_values_and_reject_one_more():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        credential = "alice"
        user_id = create_test_user(db_path, "alice", credential)
        session_cookie = login_as(opener, base_url, "alice", credential)
        max_bytes = extract_text.MAX_MARKDOWN_BYTES
        max_chars = extract_text.MAX_MARKDOWN_CHARS
        byte_exact = ("\U0001F642" * (max_bytes // 4)).encode("utf-8")
        char_exact = b"x" * max_chars

        for content, expected_status in (
            (byte_exact, 201),
            (byte_exact + b"x", 413),
            (char_exact, 201),
            (char_exact + b"x", 413),
        ):
            session_id = _new_session(user_id, db_path)
            with _upload(
                opener,
                base_url,
                session_cookie,
                session_id,
                "notes.txt",
                content,
            ) as response:
                assert response.code == expected_status
                if expected_status == 201:
                    _json_response(response)
                else:
                    response.close()


def test_text_upload_sanitizes_names_and_rejects_colons():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        credential = "alice"
        user_id = create_test_user(db_path, "alice", credential)
        session_cookie = login_as(opener, base_url, "alice", credential)
        session_id = _new_session(user_id, db_path)

        with _upload(
            opener,
            base_url,
            session_cookie,
            session_id,
            "../notes.txt",
            b"plain text",
        ) as response:
            assert response.code == 201
            data = _json_response(response)
        assert data["metadata"]["file_name"] == "notes.txt"

        invalid_session_id = _new_session(user_id, db_path)
        with _upload(
            opener,
            base_url,
            session_cookie,
            invalid_session_id,
            "bad:name.txt",
            b"plain text",
        ) as response:
            assert response.code == 400


def test_upload_requires_authentication_and_csrf():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        user_id = create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        session_id = _new_session(user_id, db_path)

        with _upload(
            opener,
            base_url,
            "",
            session_id,
            "notes.md",
            b"content",
        ) as response:
            assert response.code == 401
        with _upload(
            opener,
            base_url,
            token,
            session_id,
            "notes.md",
            b"content",
            add_csrf=False,
        ) as response:
            assert response.code == 403


def test_admin_can_attach_sensitive_markdown_to_own_conversation():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        admin_id = create_test_user(db_path, "admin", "secret123", role="admin")
        admin_token = login_as(opener, base_url, "admin", "secret123")
        admin_session = _new_session(admin_id, db_path)

        with _upload(
            opener,
            base_url,
            admin_token,
            admin_session,
            ".env.private.md",
            b"private markdown text",
        ) as response:
            assert response.code == 201
            data = _json_response(response)

        assert data["metadata"]["classification"] == "sensitive"


def test_other_users_including_admin_cannot_upload_read_or_remove_document():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        alice_credential = "alice"
        bob_credential = "bob"
        admin_credential = "admin"
        alice_id = create_test_user(db_path, "alice", alice_credential)
        bob_id = create_test_user(db_path, "bob", bob_credential)
        admin_id = create_test_user(
            db_path,
            "admin",
            admin_credential,
            role="admin",
        )
        alice_cookie = login_as(opener, base_url, "alice", alice_credential)
        bob_cookie = login_as(opener, base_url, "bob", bob_credential)
        admin_cookie = login_as(opener, base_url, "admin", admin_credential)
        alice_session = _new_session(alice_id, db_path)
        _new_session(bob_id, db_path)
        _new_session(admin_id, db_path)

        with _upload(
            opener,
            base_url,
            alice_cookie,
            alice_session,
            "notes.md",
            b"private",
        ) as response:
            document_id = _json_response(response)["document_id"]

        for cookie in (bob_cookie, admin_cookie):
            with _upload(
                opener,
                base_url,
                cookie,
                alice_session,
                "other.md",
                b"other",
            ) as response:
                assert response.code == 404
            with _upload(
                opener,
                base_url,
                cookie,
                alice_session,
                "other.txt",
                b"other",
            ) as response:
                assert response.code == 404
            with _delete_document(
                opener,
                base_url,
                cookie,
                document_id,
            ) as response:
                assert response.code == 404
            with open_no_redirect(
                opener,
                urllib.request.Request(
                    f"{base_url}/api/sessions/{alice_session}/messages",
                    headers={"Cookie": f"{SESSION_COOKIE_NAME}={cookie}"},
                ),
            ) as response:
                assert response.code == 404

        with closing(sqlite3.connect(db_path)) as conn:
            assert conn.execute(
                "SELECT COUNT(*) FROM conversation_documents WHERE id = ?",
                (document_id,),
            ).fetchone() == (1,)


def test_removing_document_keeps_history_and_prevents_later_injection():
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        user_id = create_test_user(db_path, "alice", "secret123")
        token = login_as(opener, base_url, "alice", "secret123")
        session_id = _new_session(user_id, db_path)
        private_text = "document secret bleu"
        with _upload(
            opener,
            base_url,
            token,
            session_id,
            "notes.md",
            private_text.encode(),
        ) as response:
            document_id = _json_response(response)["document_id"]

        with patch.object(
            login_server,
            "call_llamafile",
            return_value="Réponse modèle",
        ) as call_model:
            with api_post(
                opener,
                base_url,
                f"/api/sessions/{session_id}/messages",
                token,
                {"content": "Question initiale", "stream": False},
            ) as response:
                assert response.code == 201
            first_prompt = call_model.call_args_list[0][0][0][-1]["content"]
            assert private_text in first_prompt

            with _delete_document(
                opener, base_url, token, document_id
            ) as response:
                assert response.code == 200

            with api_post(
                opener,
                base_url,
                f"/api/sessions/{session_id}/messages",
                token,
                {"content": "Question après retrait", "stream": False},
            ) as response:
                assert response.code == 201
            later_prompt = call_model.call_args_list[1][0][0][-1]["content"]
            assert private_text not in later_prompt
            assert "max_tokens" not in call_model.call_args_list[1][1]

        with open_no_redirect(
            opener,
            urllib.request.Request(
                f"{base_url}/api/sessions/{session_id}/messages",
                headers={"Cookie": f"{SESSION_COOKIE_NAME}={token}"},
            ),
        ) as response:
            history = _json_response(response)
        assert history["document"] is None
        assert len(history["messages"]) == 4


def test_deleting_conversation_cascades_to_its_document():
    with api_test_context() as (_, _, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        user_id = create_test_user(db_path, "alice", "secret123")
        session_id = _new_session(user_id, db_path)
        document_id = citadelle_memory.add_conversation_document(
            user_id,
            session_id,
            "persisted text",
            {"file_name": "notes.md"},
            db_path=db_path,
        )

        citadelle_memory.delete_session(session_id, db_path=db_path)

        with closing(sqlite3.connect(db_path)) as conn:
            assert conn.execute(
                "SELECT COUNT(*) FROM conversation_documents WHERE id = ?",
                (document_id,),
            ).fetchone() == (0,)


def test_temporary_upload_files_are_removed_after_success_and_error(
    tmp_path,
    monkeypatch,
):
    with api_test_context() as (base_url, opener, db_path):
        citadelle_memory.migrate_to_v11(db_path)
        credential = "alice"
        user_id = create_test_user(db_path, "alice", credential)
        cookie = login_as(opener, base_url, "alice", credential)
        session_id = _new_session(user_id, db_path)
        real_temporary_directory = login_server.TemporaryDirectory
        created_directories = []

        def temporary_directory(*args, **kwargs):
            directory = real_temporary_directory(dir=tmp_path)
            created_directories.append(Path(directory.name))
            return directory

        monkeypatch.setattr(
            login_server,
            "TemporaryDirectory",
            temporary_directory,
        )

        with _upload(
            opener,
            base_url,
            cookie,
            session_id,
            "notes.md",
            b"valid text",
        ) as response:
            assert response.code == 201
        error_session_id = _new_session(user_id, db_path)
        with _upload(
            opener,
            base_url,
            cookie,
            error_session_id,
            "invalid.md",
            b"\xff",
        ) as response:
            assert response.code == 400
        text_error_session_id = _new_session(user_id, db_path)
        with _upload(
            opener,
            base_url,
            cookie,
            text_error_session_id,
            "invalid.txt",
            b"\xff",
        ) as response:
            assert response.code == 400

        assert created_directories
        assert all(not directory.exists() for directory in created_directories)


def test_chat_html_exposes_document_controls():
    web_dir = Path(login_server.WEB_DIR)
    html = (web_dir / "chat.html").read_text(encoding="utf-8")
    script = (web_dir / "chat.js").read_text(encoding="utf-8")

    assert 'id="attach-chat-document"' in html
    assert 'id="chat-document-file"' in html
    assert 'id="chat-document-name"' in html
    assert 'id="remove-chat-document"' in html
    assert "Joindre un .md" in html
    assert "/api/chat/upload" in script
    assert "/api/chat/document/" in script
