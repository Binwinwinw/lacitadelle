# État du projet La Citadelle

**Dernière mise à jour** : 2026-11-13

## Résumé exécutif

La Citadelle est une application locale de chat IA (Nexxus) basée sur
llamafile et Qwen3-4B. L'archive source prend en charge Windows, Linux et
macOS; un exécutable autonome est disponible pour Windows. Après validation
manuelle par le Décideur, le statut est **stable pour release**.

## Métriques actuelles

- **Tests** : 244 passed (`python -m pytest -q`)
- **Décisions documentées** : 92 (voir `.memory/decisions.md`)
- **Modèle par défaut** : `Qwen3-4B-Q4_K_M.gguf`
- **Qualité Python** : Ruff configuré dans `pyproject.toml`; 39 issues
  restent à examiner, sans corrections manuelles appliquées.

## Ce qui fonctionne

1. **Chat Markdown** : rendu local avec Marked et DOMPurify vendorisés.
2. **Streaming SSE** : événements `thinking`, `delta` et `done`.
3. **Persona V1.6** : avertissements factuels et consignes juridiques.
4. **Sécurité XSS** : DOMPurify assainit le HTML; Nexxus refuse les scripts.
5. **Distribution Qwen3-4B** : manifeste, `model_health` et tests alignés.
6. **Backup migration** : `VACUUM INTO` avant les `DROP TABLE` destructifs.
7. **Démarrage du proxy** : `sys.exit(1)` si l'initialisation échoue.
8. **REPL** : contexte par budget de 8000 tokens, comme le webchat.
9. **Payload modèle** : `extract_model_name()` au lieu d'un identifiant codé en dur.
10. **Qualité Python** : configuration pytest et Ruff dans `pyproject.toml`.

## Limites connues

1. **Knowledge cutoff ~2024** : Nexxus ne connaît pas les actualités
   post-2024. Voir [LLM-LIMITES.md](./LLM-LIMITES.md).
2. **Hallucinations juridiques** : le 4B peut citer des articles inexacts;
   le prompt demande des avertissements systématiques.
3. **Pas de RAG local** : pas de base de connaissances personnalisée.
4. **Pas d'accès web** : Nexxus reste hors ligne après installation.
5. **Ruff** : 39 issues restent à examiner; aucun changement manuel n'a été
   appliqué aux issues non auto-fixées.
6. **`login_server.py` (~2600 lignes)** : maintenabilité perfectible.

## Dettes futures

Les tâches actives sont suivies dans [`TODO.md`](../../TODO.md), notamment :

- `16-CHAT-RAG-LOCAL` : base de connaissances locale.
- `16-CHAT-WEB-ACCESS` : accès web contrôlé optionnel.
- `16-AGENTS-RULES-18` : règle de mise à jour des tests associés.
- Upload de GGUF via l'interface et autres validations manuelles de release.

## Où lire quoi

| Question | Fichier |
|---|---|
| Quelles décisions ont été prises ? | [`.memory/decisions.md`](../../.memory/decisions.md) |
| Que s'est-il passé récemment ? | [`JOURNALDEBORD.md`](./JOURNALDEBORD.md) |
| Que contient chaque commit ? | [`JOURNALDESMODIFS.md`](./JOURNALDESMODIFS.md) |
| Que reste-t-il à faire ? | [`TODO.md`](../../TODO.md) |
| Quelles sont les limites du LLM ? | [`LLM-LIMITES.md`](./LLM-LIMITES.md) |
| Quelles règles suivre ? | [`AGENTS.md`](../../AGENTS.md) |
| Comment lancer et exploiter ? | [`RUNBOOK-PROD.md`](./RUNBOOK-PROD.md) |

## Leçons clés

1. Un audit révèle des problèmes que les tests ne couvrent pas.
2. Les tests de cohérence entre sources détectent les modèles mal alignés.
3. Une validation manuelle finale reste nécessaire avant publication.
4. La documentation pérenne sert de point d'entrée et de mémoire du projet.
