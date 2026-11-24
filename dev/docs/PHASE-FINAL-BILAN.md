# Bilan final — Phase 16

**Date** : 2026-11-24

**Statut** : clôture finale des livrables AIWorkflow, premier incrément
Fichiers Chat, audit SQL et sélection V3.1. Les autres travaux historiques
modèles/UX restent des reports actifs dans le TODO/BACKLOG; ils ne sont pas
déclarés terminés par ce bilan.

## Livrables clôturés

### AIWorkflow

- Moteur d’orchestration local et trois workflows : `analyse_md`,
  `analyse_pdf` et `analyse_sql`.
- Spécification, nœuds, API, interface d’administration, intégration chat,
  diagnostic GPU/runtime/logs et retrieval SQLite FTS5.
- E2E `analyse_md` : 8/8 titres retrouvés sur `ARCHITECTURE.md` avec Ornith.
  Ce résultat porte sur ce document et ce test, pas sur tous les documents ou
  modèles.

### Fichiers Chat

- Premier incrément livré : un document Markdown `.md` par conversation,
  texte extrait conservé avec propriétaire/conversation, original temporaire.
- Migration v11, routes upload/retrait, suivi après rechargement, isolation
  `user`/`admin`, interface et conservation de l’historique.
- Quatorze tests dédiés couvrent migration, extraction, permissions, limites,
  suivi, retrait, cascade et UI.
- Test live : premier appel refusé pendant l’indisponibilité du runtime, puis
  résumé en 11,4 s; après rechargement, question de suivi répondue en 3,6 s;
  retrait avec historique conservé. Isolation vérifiée : compte
  secondaire sans session admin visible et accès direct renvoyant 404. Limites
  vérifiées : second `.md` refusé (409), `.txt` refusé (415), fichier
  supérieur à 256 KiB refusé (413).

### Audit SQL

- Migration v12 : `audit_log` et triggers `AFTER DELETE` sur
  `conversation_documents` et `sessions`.
- Quatre tests vérifient suppression de document, suppression de session,
  cascade, occultation du contenu et idempotence.
- `old_data` conserve les métadonnées et marque `content_redacted`; le texte
  documentaire n’y est pas copié. `user_id` représente le propriétaire de la
  ligne, pas nécessairement l’acteur authentifié lors d’une suppression
  directe ou indirecte.
- Session #62 : retrait via l’UI audité avec `user_id=1`, `session_id=62`.
  Session #63 : DELETE direct audité avec `user_id=1`, `session_id=63`.
- Écart historique #60 : aucun défaut de ciblage n’a été reproduit. La cause
  de l’absence antérieure de document reste inconnue; retrait manuel et état
  UI périmé sont des hypothèses, non des faits établis.
- La DB de test a été restaurée depuis le backup : les événements #62/#63 et
  la table `audit_log` ne sont pas conservés dans la DB restaurée. Le proxy
  réappliquera v12 au prochain démarrage.

### Modèles V3.1

Sélection conservée : Ornith recommandé comme défaut local, Qwen3.5 comme
second choix et Qwen3-4B comme fallback intégré. Le rollback modèle reste le
comportement de repli sécurisé prévu; il n’a pas été rejoué dans ce GO doc-only.

| Modèle sélectionné | Résultat composite communiqué | Latence communiquée |
|---|---:|---:|
| Ornith-1.5-9B | 4/7 | 9,79 s |
| Qwen3.5-9B | 5/7 | 12,83 s |
| Qwen3-4B | 3/7 | 7,57 s |

Granite-4.1-8B (3/7, 48,17 s) est retiré de la whitelist. Ces scores sont
historiques et n’ont pas été rejoués dans ce GO. Le journal conserve aussi une
mesure préliminaire différente de Qwen3-4B; les sorties brutes ne permettent
pas de réconcilier les deux classements.

## Vérification et suites

- Préflight : `331 passed`; aucun code, modèle ou whitelist modifié dans ce GO
  doc-only.
- Rollback et sélection V3.1 conservés; aucun benchmark ou lancement de modèle
  n’a été effectué pour cette clôture documentaire.
- Clôturés : AIWorkflow, premier incrément Fichiers Chat, audit SQL et parcours
  live demandé. Les autres actions déjà présentes dans TODO/BACKLOG restent
  reportées, pas implicitement terminées.
- Suites décidées : `16-CLEANUP-DETTE`, `16-MULTIFORMAT` et
  `16-AUDIT-ACTOR` (attribuer l’acteur authentifié, au-delà du propriétaire).

## Commits clés

| Commit | Livrable |
|---|---|
| `6561b47`, `5df516e` | Moteur AIWorkflow, nœuds et workflow Markdown; retrieval local. |
| `fc0575e`, `a5273c2`, `d2e4ebf`, `916dc0a` | API, UI, workflows PDF/SQL et intégration chat. |
| `9c419f4`, `ebd5efe`, `2f4d34c` | Tests UI, amélioration RAG et E2E `analyse_md` 8/8. |
| `21d0f3f`, `7f22958` | Diagnostic GPU/runtime/logs et décision modèles V3.1. |
| `fd34e82` | Premier incrément fichiers Markdown du chat (migration v11). |
| `28bb8b7` | Clôture du sous-périmètre AIWorkflow + Fichiers Chat. |
| `6e8ef08` | Audit SQL v12 (migration, triggers et tests). |

Références : [décisions](../../.memory/decisions.md),
[BACKLOG](./BACKLOG.md), [TODO](../../TODO.md) et
[JOURNALDEBORD](./JOURNALDEBORD.md).
