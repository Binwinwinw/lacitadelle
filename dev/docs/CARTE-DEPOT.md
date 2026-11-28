# Carte du dépôt La Citadelle

> Carte d’orientation, pas une spécification. Mettre à jour les domaines,
> points d’entrée et tests concernés lorsqu’ils changent.

## Upload du chat

- [login_server.py](../tools/login_server.py) : `do_POST`, `handle_post_chat_upload`, `_parse_chat_upload`, `_extract_chat_upload`, `_safe_chat_upload_filename`; limites `MAX_CHAT_UPLOAD_BODY_SIZE`, `MAX_MARKDOWN_BYTES`.
- [citadelle_memory.py](../tools/citadelle_memory.py) : `add_conversation_document`, `get_conversation_document_for_user`, `delete_conversation_document_for_user`.
- Tests : [test_chat_documents.py](../tests/test_chat_documents.py) couvre upload, limites, droits, isolation et nettoyage.

## Extraction et FTS5

- [extract_text.py](../tools/nodes/extract_text.py) : `extract_markdown_document`, `extract_text`, `ExtractTextError`, `DocumentLimitError`, `MAX_MARKDOWN_BYTES`, `MAX_MARKDOWN_CHARS`.
- [index_fts5.py](../tools/nodes/index_fts5.py) : `chunk_by_paragraph`, `index_fts5`, `search_fts5`, `normalize_query`, `rerank`, `DEFAULT_CHUNK_SIZE`.
- [login_server.py](../tools/login_server.py) : `_build_document_context` recherche les passages utilisés dans le contexte.
- Tests : [test_nodes.py](../tests/test_nodes.py), [test_nodes_fts5_improve.py](../tests/test_nodes_fts5_improve.py), [test_chat_documents.py](../tests/test_chat_documents.py).

## Sécurité des fichiers

- [security_files.py](../tools/security_files.py) : `PUBLIC_EXTENSIONS`, `SENSITIVE_EXTENSIONS`, `CRITICAL_EXTENSIONS`, `classify_file`, `can_read`.
- Inconnus/sensibles : admins seulement; critiques : refusés à tous. [extract_text.py](../tools/nodes/extract_text.py) applique les contrôles.
- Tests : [test_persona_nexxus.py](../tests/test_persona_nexxus.py), [test_security.py](../tests/test_security.py).

## Lanceur figé et proxy

- [lancer.py](../tools/lancer.py) : `IS_FROZEN`, `main`, `select_model_path`, `start_llamafile`; le dispatch figé utilise `--citadelle-proxy`.
- Windows lance llamafile dans une nouvelle console; Linux/macOS utilisent `sh -c`, `exec` et une session isolée.
- [login_server.py](../tools/login_server.py) : `main`, `do_GET`, `do_POST` et handlers HTTP/API.
- Tests : [test_cross_platform.py](../tests/test_cross_platform.py), [test_packaging.py](../tests/test_packaging.py), [test_login_routes.py](../tests/test_login_routes.py).

## Rendu Markdown du chat

- [chat.html](../tools/web/chat.html) charge Marked et DOMPurify avant [chat.js](../tools/web/chat.js).
- `renderMarkdown` assainit le HTML; `createMessage` et `renderAssistantMarkdown` insèrent le résultat.
- Tests : [test_chat_markdown.py](../tests/test_chat_markdown.py), [test_chat_documents.py](../tests/test_chat_documents.py).

## Sonde C0 et prototype

- [c0_multiformat_probe.py](../tools/c0_multiformat_probe.py) : `prescan_json`, `load_json_bounded`, `_call_worker`, `_check_worker_proofs`, `_run_measurements`.
- [json_prescan_prototype.py](../tools/json_prescan_prototype.py) est hors production; test : [test_json_prescan_prototype.py](../tests/test_json_prescan_prototype.py).
- Ces prototypes ne signifient pas que le multiformat est livré.

## Packaging

- [build.py](../tools/packaging/build.py), [build.spec](../tools/packaging/build.spec) et [requirements.txt](../tools/packaging/requirements.txt) décrivent le build PyInstaller.
- Tests : [test_packaging.py](../tests/test_packaging.py), [test_cross_platform.py](../tests/test_cross_platform.py).

## Documents de pilotage

- [decisions.md](../../.memory/decisions.md) : décisions actées.
- [PHASE16-RESTE.md](./PHASE16-RESTE.md) : reprise et travaux de phase 16.
- [BACKLOG.md](./BACKLOG.md) et [ETAT-PROJET.md](./ETAT-PROJET.md) : tâches validées et état courant.
- [SPEC-FICHIERS-CHAT.md](./SPEC-FICHIERS-CHAT.md) : spécification fonctionnelle des fichiers du chat.
