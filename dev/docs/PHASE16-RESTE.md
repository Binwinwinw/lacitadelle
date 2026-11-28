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

- **État** : arbitrages fonctionnels A et techniques B terminés et consignés
  le 2026-11-25 dans les décisions #135 et #136; décisions #137–#139 du
  2026-11-27 : poursuite Windows-first, arbitrage C1–C4 et stratégie de
  contexte. C1 peut être demandé sous Windows par un GO distinct. C0a Windows
  est validé par C0A-3; C0b Linux/macOS est reporté, sans résultat présumé.
  L’implémentation C n’est pas commencée;
  l’upload chat reste `.md` seulement.
- **Description** : réaliser ultérieurement l’allowlist approuvée `.md`, `.txt`,
  `.csv`, `.json`, `.sql`; cela ne décrit pas la disponibilité actuelle.
- **Faits clés** : le chat accepte `.md`; le helper générique `.txt`/PDF et le
  workflow admin PDF/SQL sont des parcours distincts, pas une preuve de support
  d’upload multiformat dans le chat.
- **Contraintes décidées** : traitement local, fichier non fiable/non exécuté,
  permissions non issues du document et vérifications imposées côté serveur.
- **Dépendances et arbitrages** : profondeur approuvée : CSV/JSON structurés,
  Markdown/TXT/SQL textuels, aucun contenu exécuté. La version cible est à
  déterminer. C0a a produit les preuves Windows; C0b Linux/macOS est reporté
  (décision #137), sans prétendre valider ces plateformes. Selon #139, `.txt`
  et `.sql` peuvent être livrés sur Linux/macOS après leur vérification propre,
  sans attendre C0b; CSV/JSON restent bloqués sur chaque plateforme jusqu'à
  validation de son C0b. C1 peut être demandé sous Windows; C1/C2 n'attendent
  pas C0b et C3/C4 peuvent y être développés, preuves multiplateformes avant
  livraison. Les README n'annoncent aucun format non vérifié. Les décisions
  #138/#139 tranchent architecture, deadline totale, candidats CSV, validation
  serveur par plateforme, contrôles JSON décodés et option C de contexte. Les
  plafonds et budgets restent révisables après mesure du protocole réel. Le
  script
  autonome et sa notice sont dans la
  section C0 du BACKLOG. Voir le
  [plan détaillé](./BACKLOG.md#16-multiformat), la
  [décision #135](../../.memory/decisions.md#2026-11-25-arbitrage-fonctionnel-du-premier-palier-multiformat), la
  [décision #136](../../.memory/decisions.md#2026-11-25-arbitrage-des-conditions-techniques-multiformat) et les
  [invariants #134](../../.memory/decisions.md#2026-11-24-cadrage-documentaire-du-chantier-16-multiformat) et la
  [spécification du premier incrément](./SPEC-FICHIERS-CHAT.md).
- **Prochaine action** : demander un GO distinct pour C1 sous Windows.
  C0b reste le verrou pour activer CSV/JSON et clore le multiformat POSIX;
  il ne bloque pas la livraison de `.txt`/`.sql` après vérification propre
  (#139).
- **Proposition de découpage C1–C4** (à arbitrer; ne constitue pas une
  autorisation d’implémentation) :

| Lot | Objectif et fichiers visés | Tests à écrire en premier | Preuve, arrêt, dépendances et plateformes |
|---|---|---|---|
| **C1 — texte simple** | Ajouter un lecteur chat UTF-8 borné pour `.txt` et `.sql` texte; `.sql` demeure admin-only selon #136. Adapter le dispatch et la réponse d’upload dans [login_server.py](../tools/login_server.py) et ajouter un point d’entrée chat dédié dans [extract_text.py](../tools/nodes/extract_text.py). Réutiliser les contrôles d’ownership et de stockage existants; aucune migration prévue. | Étendre [test_chat_documents.py](../tests/test_chat_documents.py) avec UTF-8, BOM, vide/contrôles, limites, rôle `user`/`admin`, session non propriétaire, erreur et nettoyage. Étendre [test_nodes.py](../tests/test_nodes.py) si le lecteur partagé change. | API de test isolée avec DB/temporaire; `.md` inchangé et SQL refusé aux non-admins. Arrêt si le nettoyage, les droits ou les codes existants changent sans décision. Dépend de #135/#136, pas de C0b. Développement et preuve initiale sous Windows; selon #139, `.txt`/`.sql` POSIX peuvent être livrés après validation propre sans attendre C0b. |
| **C2 — parseurs structurés et contexte** | Implémenter les fonctions CSV/JSON pures et la fiche/segmentation Option C, sans activation avant C3. Nouveau module proposé : `dev/tools/nodes/extract_structured.py`; vérifier aussi [index_fts5.py](../tools/nodes/index_fts5.py). Le prototype [json_prescan_prototype.py](../tools/json_prescan_prototype.py) et ses [tests](../tests/test_json_prescan_prototype.py) restent une référence C0, pas une dépendance de production. | Nouveau `dev/tests/test_chat_structured_documents.py` : parsing, limites exact/+1, fiche complète, segments CSV avec en-tête répété, segments JSON avec Pointer, éléments volumineux divisés par enfants, contexte total et absence de troncature silencieuse. Étendre [test_nodes_fts5_improve.py](../tests/test_nodes_fts5_improve.py) pour vérifier l’adéquation de FTS5 aux segments/locators. | Option C #139 : fichier ≤≈6 000 tokens entier; sinon fiche toujours présente (≈1 000 tokens) + segments retrouvés selon la question. CSV : 3–10 lignes/segment (≈500–1 000 tokens), en-tête répété. JSON : élément de premier niveau avec Pointer, divisé par enfants s’il est trop gros. Budget de départ : 6–9 segments (≈8 000 tokens), fiche en plus, ≥12 000 tokens réservés à conversation/réponse; valeurs à réviser après mesures. Aucune troncature silencieuse. C2 n’attend pas C0b; arrêter si FTS5 ne préserve pas les locators/coverage. |
| **C3 — worker borné et packaging** | Intégrer le module dédié `dev/tools/nodes/structured_worker.py` via [login_server.py](../tools/login_server.py). Orientation #138 : lancement par subprocess; spawn depuis le serveur seulement si une mesure du protocole réel le justifie. Pour l’EXE, dispatch frozen avant les imports lourds dans [lancer.py](../tools/lancer.py), imports de [build.spec](../tools/packaging/build.spec) et, si nécessaire, [build.py](../tools/packaging/build.py). | Nouveau `dev/tests/test_structured_worker.py` : protocole, requête/réponse bornées, enfant bloqué ou qui ne lit pas, délai couvrant l’envoi, parsing et retour, arrêt/cleanup sans orphelin. Étendre [test_chat_documents.py](../tests/test_chat_documents.py) pour les erreurs API; étendre [test_packaging.py](../tests/test_packaging.py) pour le dispatch gelé si le contrat le permet. | Tests ciblés puis smoke PyInstaller one-file Windows, sans installation implicite. Arrêt si l’envoi peut dépasser le délai, si un worker reste actif ou si le smoke échoue; pas de fallback in-process sans mesure réelle favorable. C3 dépend de C2. Développement/validation sous Windows seulement; aucune preuve Linux/macOS. |
| **C4 — durcissement et disponibilité** | Rejeter les contrôles JSON décodés et substituts isolés selon #138, avec locators et erreurs finales dans `extract_structured.py` et [login_server.py](../tools/login_server.py). Capacités par plateforme déterminées/refusées côté serveur; [chat.html](../tools/web/chat.html) et [chat.js](../tools/web/chat.js) restent hors du lot C (D les reflète seulement). | Compléter `test_chat_structured_documents.py` avec échappements décodés dans valeurs et clés, NUL, C0 hors TAB/CR/LF, DEL, C1, substituts isolés, absence de persistance sur rejet, locators et frontières des limites. Compléter [test_chat_documents.py](../tests/test_chat_documents.py) pour l’échec API et le nettoyage. | Suite ciblée Windows et smoke empaqueté; toute capacité doit échouer fermée. Arrêt si une valeur interdite est acceptée ou si le client peut contourner la capacité serveur. Dépend de C2/C3. C3/C4 peuvent être développés sous Windows; CSV/JSON restent désactivés jusqu’à validation C0b de la plateforme. `.txt`/`.sql` POSIX ne l’attendent pas (#139). |

- **Hors C** : l’interface et la présentation des formats restent dans D.
  Jusqu’à sa validation, le sélecteur conserve `.md` seulement. Aucun README
  n’annonce de format avant la vérification effective. D affiche pour l’analyse
  partielle « analyse partielle : N segments sur M consultés »; aucun résultat
  n’est tronqué silencieusement.
- **Livraison minimale recommandée** : après C1 puis un GO D distinct, proposer
  `.md` + `.txt` sur Windows; `.txt`/`.sql` POSIX peuvent suivre après validation
  propre sans attendre C0b (#139). Garder `.sql` admin-only; ne pas annoncer
  CSV/JSON avant le worker C3, le durcissement C4 et le C0b de la plateforme.

##### Décisions #138–#139 consignées

1. **Architecture du worker (C3)** : l’orientation est le module
   dédié lancé par `subprocess`; `spawn` depuis le serveur n’est retenu que si
   une mesure sur le protocole réel la justifie. Le dispatch frozen quitte avant
   les imports lourds. Les mesures C0A-3 ci-dessous sont celles du harnais
   synthétique, pas du worker de production : spawn source
   `239.609/252.539 ms`, subprocess source `97.900/136.836 ms` (médiane/max,
   5 essais); spawn figé `1 136.476/1 257.691 ms`, subprocess figé
   `1 027.486/2 107.919 ms`.
2. **Envoi et délai** : le délai mural couvre toute la durée :
   envoi, analyse, réponse et terminaison. Le test d’un enfant qui ne lit pas
   est obligatoire.
   - Le C0A-3 a arrêté un worker bloqué après `5.022 s` et une boucle CPU après
     `5.024 s`; le harnais borne l’entrée à 256 KiB et sa réponse à 512 octets.
     Dans `_call_worker`, `send_bytes` précède `poll(timeout)` : ce résultat ne
     prouve donc pas que l’envoi lui-même respecte le délai; le test
     obligatoire doit couvrir ce chemin.
3. **Plafonds CSV (C2)** : candidats conservés par #138 : 5 000 lignes,
   100 colonnes, 20 000 cellules et un champ de 64 KiB sont conservés.
   Le comptage précède l’analyse; chaque frontière est testée à exact et +1.
   Les candidats peuvent être révisés si les mesures réelles l’exigent. C0A-3
   a mesuré sur
   Windows, sur données synthétiques, 20 000 cellules à `265/855 ms` worker
   médiane/max; 131 000 lignes d’un caractère à `1.158/1.780 s`; et une ligne
   de virgules de 256 KiB à `475/711 ms`. Le dernier cas atteint environ 8.04 MB
   de pic `tracemalloc`. Les mesures ne sont ni RSS ni garantie de portabilité.
4. **Activation par plateforme** : les capacités sont décidées et refusées
   côté serveur; le client les affiche seulement. #139 précise que C0b bloque
   CSV/JSON seulement; `.txt`/`.sql` peuvent être livrés POSIX après validation
   propre à ces formats. Les README n’annoncent aucun format avant vérification.
5. **Échappements JSON décodés (C4)** : rejeter NUL, contrôles C0
   hors TAB/CR/LF, DEL, C1 et substituts isolés; les tests adverses précèdent
   le code. C0A-3 n’a pas couvert les contrôles
   obtenus via `\u0000`/`\u007f` ni les substituts isolés comme `\ud800`.
6. **Contexte (C2, Option C)** : injecter entièrement un fichier d’environ
   6 000 tokens ou moins. Au-delà, toujours joindre une fiche d’environ 1 000
   tokens (nom, format, taille, lignes/colonnes, noms/types, exemples et
   statistiques calculées par le parseur), puis retrouver des segments selon
   la question. CSV : 3–10 lignes, 500–1 000 tokens, en-tête répété; JSON :
   élément de premier niveau avec JSON Pointer, divisé par enfants s’il est
   trop gros. Budget de départ : 6–9 segments (≈8 000 tokens), fiche en plus,
   au moins 12 000 tokens pour conversation/réponse; valeurs à mesurer et
   réviser, sans troncature silencieuse. D affiche « analyse partielle : N
   segments sur M consultés ». Le modèle n’écrit ni n’exécute de code sur les
   fichiers.

##### Vérifications de suivi en C2

Décision #139 résout les deux points ouverts de #138. C2 doit encore vérifier
que l’index FTS5 existant convient aux segments et locators, puis mesurer le
protocole réel pour ajuster les budgets de départ; ces validations ne changent
pas l’Option C sans nouveau GO.

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
