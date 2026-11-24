# Bilan — clôture du périmètre AIWorkflow et fichiers du chat

**Date** : 2026-11-24

**Statut** : le sous-périmètre AIWorkflow et le premier incrément fichiers
du chat de la Phase 16 sont clôturés. Les autres tâches modèles/UX de la
Phase 16 restent ouvertes dans le [BACKLOG](./BACKLOG.md).

Ce bilan clôt le périmètre nommé dans le GO 16-PHASE-CLOSE; il ne déclare pas
terminées les tâches qui ne sont pas couvertes par ce périmètre.

## Livrables

### AIWorkflow

- Spécification d’architecture, moteur d’orchestration maison, nœuds locaux et
  trois workflows : `analyse_md`, `analyse_pdf` et `analyse_sql`.
- API et interface d’administration; intégration au chat et page de diagnostic
  GPU/runtime/logs.
- Retrieval SQLite FTS5 amélioré : chunks par paragraphe, reranking BM25 et
  normalisation ciblée des pluriels.
- Test UI headless Node/Python; aucune dépendance `jsdom` ajoutée.
- E2E `analyse_md` sur `ARCHITECTURE.md` : les huit titres attendus ont été
  retrouvés avec Ornith. Ce résultat porte sur ce document et ce test, pas sur
  tous les documents ou modèles.

### Fichiers du chat

- Premier incrément livré : un fichier `.md` par conversation, texte extrait
  et métadonnées conservés avec le propriétaire; l’original est temporaire.
- Migration SQLite v11, routes d’ajout et de retrait, reprise après rechargement,
  permissions `admin`/`user`, interface d’ajout/retrait et historique conservé.
- FTS5 ne recherche que le document de la conversation courante; les dépassements
  sont explicites et le rendu signale les extraits partiels.
- Quatorze tests dédiés couvrent migration, extraction, droits, limites,
  suivi, retrait, cascade et UI.

### Modèles V3.1

Décision V3.1 conservée : Ornith est recommandé comme défaut local, Qwen3.5
comme second modèle et Qwen3-4B comme fallback intégré. Granite a été retiré
de la whitelist par la décision modèle précédente. Cette clôture ne modifie
ni modèle ni whitelist.

| Modèle | Résultat composite communiqué | Latence communiquée |
|---|---:|---:|
| Ornith-1.5-9B | 4/7 | 9,79 s |
| Qwen3.5-9B | 5/7 | 12,83 s |
| Granite-4.1-8B | 3/7 | 48,17 s |
| Qwen3-4B | 3/7 | 7,57 s |

Les résultats sont historiques et n’ont pas été rejoués dans ce GO. Note de
provenance : le journal conserve une ligne de batterie indiquant Qwen3-4B à
4/7 en 7,57 s, puis une reclassification stricte à 3/7 sans latence associée.
Le tableau reprend la synthèse fournie pour ce GO; les sorties brutes ne
permettent pas de confirmer que la note et la latence Qwen3-4B proviennent du
même passage.

## Vérification de clôture

- Préflight : `.\.venv\Scripts\python.exe -m pytest -q` — `327 passed in
  81.38s`; 130 décisions datées après l’ajout de la décision de clôture.
- AIWorkflow et les chemins serveur autorisés n’ont pas été modifiés dans le
  GO de clôture.
- Aucun modèle live, navigateur réel, base utilisateur ou whitelist n’a été
  utilisé ou modifié dans ce GO.

## Tâches terminées et suites ouvertes

**Clôturés dans ce périmètre** : conception et implémentation AIWorkflow,
tests UI, amélioration RAG, E2E `analyse_md`, premier incrément fichiers du
chat et normalisation documentaire AIWorkflow. Les tâches terminées conservent
leur statut et leurs références dans le [BACKLOG](./BACKLOG.md).

**Suites planifiées, non implémentées** :

1. **16-FICHIERS-CHAT-LIVE-TEST** : test manuel navigateur + modèle du parcours
   ajout, suivi, rechargement et retrait.
2. **16-CLEANUP-DETTE** : revoir les avertissements Ruff préexistants,
   l’approximation du budget tokenizer et la gestion des logs.
3. **16-MULTIFORMAT** : cadrer les extracteurs futurs PDF, documents
   bureautiques et SQL comme texte; aucune exécution du contenu SQL.

Le RAG général du chat, l’accès web et les autres dettes modèles/UX restent
distincts et ouverts selon le [BACKLOG](./BACKLOG.md) et le [TODO](../../TODO.md).

## Commits clés

| Commit | Livrable |
|---|---|
| `6561b47`, `5df516e` | Moteur AIWorkflow, nœuds et workflow Markdown; retrieval local. |
| `fc0575e`, `a5273c2`, `d2e4ebf`, `916dc0a` | API, interface, workflows PDF/SQL et intégration au chat. |
| `9c419f4` | Tests UI headless du chat AIWorkflow. |
| `ebd5efe` | RAG FTS5 : chunks, BM25 et pluriels. |
| `2f4d34c` | Document complet par défaut pour `analyse_md`; E2E 8/8 sur Architecture. |
| `21d0f3f` | Page et API de diagnostic GPU/runtime/logs. |
| `7f22958` | Décision V3.1 sur le modèle local recommandé et les fallbacks. |
| `fd34e82` | Premier incrément de fichiers Markdown rattachés aux conversations. |

Décisions de référence : [decisions.md](../../.memory/decisions.md), en
particulier les décisions #127 à #130.
