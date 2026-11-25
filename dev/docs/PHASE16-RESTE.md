# Phase 16 — tâches restantes

**Date de l’inventaire** : 2026-11-24

**Sources** : [TODO.md](../../TODO.md) et [BACKLOG.md](./BACKLOG.md).

## Périmètre et comptage

L’inventaire compte **17 tâches ouvertes** liées aux modèles, à l’UX, à la
qualité, à la distribution et aux évolutions de Phase 16 : les 14 entrées
`16-*` restantes dans `TODO.md`, plus `MODELE-NETTOYAGE`, `UX-Whitelist-Date`
et la validation du persona après Qwen3-4B, qui n’ont pas de préfixe `16-`.

`16-FIX-FLAKY-TESTS` est clôturé sans correctif à partir des résultats du GO
précédent : suite complète 338/338 et 20 invocations ciblées (120 exécutions
de cas) sans échec. Aucun test n’a été relancé pour cette clôture; la campagne
ne constitue pas une garantie générale d’absence d’intermittence.
L’ancien WinError 10053 a été corrigé en Phase 8b; aucun symptôme intermittent
précis n’a été retrouvé pour `test_migration_v3`. La preuve détaillée figure
dans les journaux.

La validation de `16-FIX-SETTINGS-SCROLL` est clôturée le 2026-11-24 et n’est
plus comptée. Le défilement général a été vérifié en session authentifiée sur
écran large et étroit; trois modèles et leurs actions étaient accessibles.
L’essai statique précédent avec 60 entrées factices était concluant, mais le
cas authentifié avec une liste longue n’a pas été testé. Aucun défaut n’a été
reproduit; les détails et cette limite figurent dans les journaux.

Les livrables AIWorkflow, Fichiers Chat et Audit SQL sont exclus. Sont aussi
exclues les tâches `16-CLEANUP-DETTE` et `16-AUDIT-ACTOR`, terminées dans le GO
précédent. Les priorités hautes/moyennes/basses du BACKLOG sont conservées;
quand aucune priorité n’y est définie, celle de cet inventaire est une
proposition, pas une décision de périmètre.

Les contrôles généraux de TODO sans rattachement explicite à Phase 16 restent
dans TODO et ne sont pas reclassés ici. Chaque entrée ci-dessous devra être
traitée dans un GO séparé. Cet inventaire n’autorise aucune exécution ni aucun
élargissement de périmètre; toute proposition nouvelle doit suivre les
décisions et objectifs du projet.

## Inventaire priorisé

### Priorité moyenne

#### 1. `16-CHAT-CONTEXT-STRATEGY`

- **Description** : préciser `MAX_CONTEXT_TOKENS` et la troncature par paire
  user/assistant.
- **Dépendances** : aucune n’est précisée dans TODO; définir les règles de
  conservation de l’historique avant implémentation.
- **Priorité** : moyenne, proposée en raison de l’impact sur le contexte des
  conversations.

#### 2. `16-FEATURE-MODEL-USE-V2`

- **Description** : redémarrer automatiquement le proxy et llamafile après
  sélection d’un modèle, avec progression, détection d’échec et rollback.
- **Dépendances** : V1 de la sélection de modèle; TODO indique « après V1 ».
- **Priorité** : moyenne, déjà indiquée dans le BACKLOG; estimation existante
  de 4–6 h.

#### 3. `16-FIX-WHITELIST-UX`

- **Description** : remplacer le message générique pour une entrée invalide
  de whitelist par une erreur précise.
- **Dépendances** : aucune précisée; couvrir les entrées invalides par test.
- **Priorité** : moyenne, déjà indiquée dans le BACKLOG.

#### 4. `16-AGENTS-RULES-18`

- **Description** : formaliser dans `AGENTS.md` la règle de mise à jour des
  tests lorsqu’un fichier testé est modifié.
- **Dépendances** : aucune; effort estimé de 30 min.
- **Priorité** : moyenne, déjà indiquée dans le BACKLOG.

#### 5. `16-FEATURE-ORCHESTRATION-LOG`

- **Description** : vérifier manuellement la colonne et le filtre de modèle
  dans les logs admin.
- **Dépendances** : UI admin et données de test; critères d’acceptation à
  confirmer pendant le GO.
- **Priorité** : moyenne, proposée; la validation est explicitement en attente
  dans TODO.

#### 6. `16-MULTIFORMAT`

- **État** : cadrage documentaire fait le 2026-11-24; implémentation non
  commencée. Le chat reste `.md` seulement.
- **Description** : faire évoluer le contrôle vers « Joindre un fichier »
  seulement avec une allowlist réelle, explicite et vérifiée; aucune liste de
  formats additionnels n’est approuvée.
- **Faits clés** : le chat accepte `.md`; le helper générique `.txt`/PDF et le
  workflow admin PDF/SQL sont des parcours distincts, pas une preuve de support
  d’upload multiformat dans le chat.
- **Contraintes décidées** : traitement local, fichier non fiable/non exécuté,
  permissions non issues du document et vérifications imposées côté serveur.
- **Dépendances et arbitrages** : premier incrément `.md` et test live terminés;
  restent l’allowlist, le palier, la version cible, les extracteurs/dépendances,
  les limites et la conservation. Voir le
  [plan détaillé](./BACKLOG.md#16-multiformat), la
  [décision #134](../../.memory/decisions.md#2026-11-24-cadrage-documentaire-du-chantier-16-multiformat) et la
  [spécification du premier incrément](./SPEC-FICHIERS-CHAT.md).
- **Prochaine action** : obtenir l’arbitrage du Décideur sur l’allowlist
  initiale, le premier palier et la version cible avant tout GO technique.
- **Priorité** : moyenne, proposée; le BACKLOG la laisse à déterminer.

#### 7. Validation persona post-Qwen3-4B (TODO sans identifiant)

- **Description** : vérifier les réponses structurées et l’absence d’URL ou
  d’articles de loi inventés.
- **Dépendances** : compte de test et critères de validation à confirmer.
  TODO cite V1.3/V1.4 alors que le projet a depuis évolué; recadrer le test sur
  la version courante du persona avant de l’exécuter.
- **Priorité** : moyenne, proposée pour une validation utilisateur visible.

### Priorité basse

#### 8. `16-FEATURE-MODEL-DRIFT-DETECTION`

- **Description** : afficher un bandeau dans `/settings` si le modèle déclaré
  en SQLite diffère de celui renvoyé par llamafile (`/v1/models`).
- **Dépendances** : modèle chargé observable via `/v1/models` et état
  `current_model_path`.
- **Priorité** : basse, déjà indiquée dans le BACKLOG.

#### 9. `16-FEATURE-AUTO-MODEL-SELECTION`

- **Description** : détecter le matériel au premier lancement et choisir un
  modèle selon ses capacités. TODO propose Qwen3.5-9B à partir de 8 Go de VRAM,
  sinon Qwen3-4B.
- **Dépendances** : TODO la place après l’UX. Revalider les seuils et modèles
  proposés contre la décision V3.1 courante avant tout GO d’implémentation.
- **Priorité** : basse, déjà indiquée dans le BACKLOG.

#### 10. `16-FEATURE-RESPONSE-TIME`

- **Description** : valider manuellement l’affichage discret de la durée sous
  chaque réponse.
- **Dépendances** : le code est indiqué comme implémenté dans le BACKLOG;
  disposer d’une réponse générée pour la vérification.
- **Priorité** : basse, déjà indiquée dans le BACKLOG.

#### 11. `16-CHAT-RAG-LOCAL`

- **Description** : ajouter une base de connaissances locale avec upload,
  recherche BM25 et injection dans le prompt.
- **Dépendances** : cadrer l’import et le stockage des documents; avant
  l’implémentation, confirmer le périmètre et la version cible dans les
  objectifs du projet.
- **Priorité** : basse, déjà indiquée dans le BACKLOG; effort estimé de 2–3
  jours.

#### 12. `16-CHAT-WEB-ACCESS` (optionnel)

- **Description** : accès web contrôlé par API (DuckDuckGo, Légifrance ou
  Wikipedia), désactivé par défaut.
- **Dépendances** : choisir un fournisseur/API et obtenir une validation
  explicite du compromis avec la promesse hors ligne. Tout élargissement de
  périmètre nécessite un GO, une décision approuvée et la mise à jour des
  objectifs.
- **Priorité** : basse, déjà indiquée dans le BACKLOG; effort estimé de 1–2
  jours.

#### 13. `16-REFACTOR-LOGIN-SERVER`

- **Description** : découper `login_server.py` en modules auth, chat, admin,
  settings et static.
- **Dépendances** : stabiliser d’abord les tests intermittents; estimation
  existante de 4–6 h.
- **Priorité** : basse, déjà indiquée dans le BACKLOG.

#### 14. `16-FIX-OTHER-PROJECTS-VENV`

- **Description** : recréer les environnements `.venv` des autres projets,
  notamment Nexxus Studio, avec Python 3.15.
- **Dépendances** : identifier les projets et vérifier leur compatibilité;
  propriétaire indiqué dans TODO : Décideur.
- **Priorité** : basse, déjà indiquée dans le BACKLOG.

#### 15. `16-DOC-RELEASE-NOTES`

- **Description** : documenter les changements majeurs, les modèles évalués,
  le choix du défaut et la migration Python.
- **Dépendances** : utiliser les résultats et choix effectivement validés;
  ne pas présenter d’hypothèses comme des faits.
- **Priorité** : basse, déjà indiquée dans le BACKLOG.

#### 16. `MODELE-NETTOYAGE` (TODO sans identifiant)

- **Description** : l’ancienne tâche propose de retirer Qwen2.5-3B,
  Mistral-Nemo-12B et Gemma-2-9B, et de conserver Ornith, Llama-3.1-8B,
  Qwen3.5-9B et des Qwen3 non testés dans `allowed_models`.
- **Dépendances** : migration v9 publiée selon le BACKLOG; réconcilier d’abord
  la liste historique de TODO avec la décision V3.1 et l’état courant. Aucune
  modification de whitelist n’est autorisée par cet inventaire.
- **Priorité** : basse, déjà rangée dans les évolutions du BACKLOG.

#### 17. `UX-Whitelist-Date` (TODO sans identifiant)

- **Description** : ajouter une colonne informative « Date d’ajout » au
  tableau whitelist.
- **Dépendances** : tableau existant dans `admin.html`; confirmer l’intérêt et
  la source de la date avant le GO.
- **Priorité** : basse, déjà indiquée dans TODO.

## Ordre de traitement proposé

Chaque ligne représente un GO autonome; cet ordre ne donne pas l’autorisation
d’exécuter les GO suivants.

1. `16-FIX-WHITELIST-UX`.
2. `16-CHAT-CONTEXT-STRATEGY`.
3. `16-FEATURE-MODEL-USE-V2`.
4. `16-FEATURE-RESPONSE-TIME` — validation manuelle seule.
5. `16-FEATURE-ORCHESTRATION-LOG` — validation manuelle seule.
6. `16-AGENTS-RULES-18` — GO documentaire indépendant.
7. Validation persona post-Qwen3-4B — recadrer d’abord la version et les
   critères.
8. `MODELE-NETTOYAGE` — réconcilier la liste historique avant tout changement.
9. `16-FEATURE-MODEL-DRIFT-DETECTION`.
10. `16-FEATURE-AUTO-MODEL-SELECTION` — après revalidation des seuils/modèles.
11. `16-MULTIFORMAT` — arbitrer l’allowlist et le premier palier avant tout GO
    technique.
12. `16-CHAT-RAG-LOCAL` — après définition de l’import et du stockage.
13. `16-CHAT-WEB-ACCESS` — uniquement après décision explicite sur le mode hors
    ligne et mise à jour du périmètre.
14. `16-REFACTOR-LOGIN-SERVER` — après stabilisation des tests.
15. `UX-Whitelist-Date`.
16. `16-FIX-OTHER-PROJECTS-VENV`.
17. `16-DOC-RELEASE-NOTES` — après validation des informations à publier.

## Recommandation

Traiter d’abord `16-FIX-WHITELIST-UX`, puis `16-CHAT-CONTEXT-STRATEGY`.
`16-FIX-FLAKY-TESTS` est clôturé sans correctif après une campagne bornée sans
échec; cela ne garantit pas l’absence générale d’intermittence. La validation
de `16-FIX-SETTINGS-SCROLL` est aussi clôturée sans correctif; le cas
authentifié avec une liste longue reste non testé. Garder `16-CHAT-WEB-ACCESS`
optionnel, car
il contredit la promesse hors ligne sans décision de périmètre.
