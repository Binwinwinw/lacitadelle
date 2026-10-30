# Journal des modifications

Ce document résume les évolutions du produit et de sa distribution.

## Phases 1-5 — Distribution actuelle

- **Phase 1** : le bootstrap télécharge llamafile-thin 0.10.6 dans `dist/` et le GGUF séparément dans `dev/tools/vendor/llamafile/`; les deux assets sont vérifiés par checksum.
- **Phase 2** : création d'une archive ZIP autonome pour les utilisateurs, sans Git ni binaires pré-téléchargés.
- **Phase 3** : suppression des anciens artefacts de distribution et nettoyage documentaire; la release GitHub v0.1.0 contenant l'ancien runtime regroupé est obsolète et doit être dépréciée manuellement.
- **Phase 4** : nettoyage des quirks legacy, renommage du fichier en `README.md` et vérification des liens.
- **Phase 5** : alignement de `OBJECTIF.md`, annotation des décisions historiques, suppression de l'ancien outil développeur et des contrats morts; archive renommée `lacitadelle-distribution.zip` et régénérée après le ménage.

## V1 — Terminée (2026-10-18)

> **HISTORIQUE** — cet état précède les évolutions V2/V3 et les Phases 1-5 de distribution.

### Travaux accomplis

- **Socle documentaire** : instructions projet, périmètre, stratégie Git, base llamafile, stratégie de vendorisation et contrats bootstrap, external et mémoire.
- **Choix du runtime et du modèle** : llamafile 0.10.6 thin, `zipalign` et Qwen3-1.7B Q4_K_M en mode external.
- **Bootstrap V1** : `dev/tools/bootstrap.py` téléchargeait et vérifiait les assets du runtime et du GGUF.
- **Fabrication V1** : `dev/tools/setup_lacitadelle.py` assemblait l'exécutable external d'environ 44 Mo; cet outil a été supprimé en Phase 5.
- **Lancement actuel** : `install.bat` lance le bootstrap sans construire le runtime ; `lancer.bat` démarre le serveur et le proxy puis ouvre le navigateur.
- **Conversation et mémoire** : le serveur headless sert l'API locale et l'interface web ; `dev/tools/client.py` fournit un REPL relié à `dev/tools/citadelle_memory.py` et à la base SQLite à trois tables.
- **Reproductibilité V1** : le parcours de zéro a été confirmé; l'installation téléchargeait les assets puis fabriquait l'exécutable.
- **Nettoyage documentaire Temps 2** : les mentions opérationnelles obsolètes liées à `main/` ont été retirées ; les historiques de décisions ont été conservés selon Solution A.

### Décisions clés

- Modèle externe : le GGUF n'est pas embarqué dans l'exécutable llamafile.
- Modèle V1 : Qwen3-1.7B Q4_K_M, licence Apache 2.0.
- Serveur local headless sur le port 8080, contexte de 8192 tokens.
- Mémoire SQLite locale disponible via le client Python séparé ; un seul utilisateur par défaut en V1.
- Les cinq agents de nettoyage documentaire du Temps 2 ont été créés et utilisés.

### Limites connues

- L'interface web transmet l'historique et peut saturer le contexte sur les longues conversations ; le client REPL borne l'historique envoyé.
- Pas de login ni de multi-utilisateurs actifs.
- Pas de détection GPU ni de bascule automatique.
- Pas de prompt système personnalisable ni de reprise HTTP Range.

## V3.0 — Terminée

### Réalisations

- Inscription avec mot de passe, login scrypt, changement forcé de mot de passe et logout.
- Sessions d'authentification avec cookie `Max-Age=86400` et expiration côté serveur.
- Proxy local et webchat; sessions et messages filtrés par utilisateur.
- Distribution actuelle : archive ZIP autonome; llamafile-thin et le GGUF sont téléchargés séparément par le bootstrap.
- 73 tests permanents passent.

### V3.1 — Roadmap

- Routes d'administration : comptes, reset, activation/désactivation, rôles et suppression.
- HTTPS avec certificat auto-signé.
- Protection CSRF pour les requêtes POST/DELETE.
- Rate limiting du login.

### V3.2+

- Multi-admin configurable.
- Détection GPU, prompt système personnalisé et reprise HTTP Range restent des évolutions futures.

## [2026-10-22 → 2026-10-23] Refonte distribution (Phases 1-7)

**Commit** : `64f0ba4` (Phase 7; synthèse des 10 commits de la séquence)

**Raison** : livrer une distribution autonome sans Git, avec moteur et modèle
téléchargés séparément, puis documenter les parcours utilisateur et
contributeur en anglais et en français.

**Fichiers modifiés** : évolution de `bootstrap.py`, `llamafile_config.json`,
`lancer.bat`, documentation produit et contrats; ajout de `LICENSE`,
`README.fr.md`, `CONTRIBUTING.md` et `CONTRIBUTING.fr.md`; archivage dans
`lacitadelle-distribution.zip`.

**Impact** : distribution ZIP autonome, exécution headless avec `--server`,
documentation bilingue, licence Apache 2.0 et validation du chat par
navigateur.

Le brief Phase 7 annonçait neuf commits mais en énumérait dix; les dix
références listées ont été vérifiées et sont conservées ici :

1. `6bfba9d` — `feat: refonte distribution (llamafile-thin direct, sans .llamafile pré-construit)`
2. `ee766ce` — `feat: packaging Phase 2 (archive ZIP autonome sans Git)`
3. `6db45c9` — `docs: Phase 3 finale (legacy supprimé, doc nettoyée, archive régénérée)`
4. `ad8390b` — `docs: clôture distribution (quirks nettoyés, README.md, archive à jour)`
5. `9c9df0e` — `docs: vérité produit et décisions historiques (Phase 5A)`
6. `4aea85b` — `chore: nettoyage dépôt et contrats (Phase 5B)`
7. `92f36fd` — `docs: purge finale résidus Phase 5C (archive renommée partout, contrats historiques annotés)`
8. `f50691f` — `fix: correctif lancer.bat (llamafile --server headless, logs dans la fenêtre)`
9. `b5c7833` — `docs: clôture Phase 6C (test navigateur chat validé, distribution V3.1)`
10. `64f0ba4` — `docs: README bilingue, CONTRIBUTING séparé, licence Apache 2.0 (Phase 7)`

## [2026-10-23] Assainissement du dépôt (Phase 7C)

**Commit** : Phase 7C (commit courant; identifiant consultable dans
l'historique Git).

**Fichiers modifiés** : `.gitignore`, `AGENTS.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.

**Raison** : retirer de l'index les deux commits locaux de backup non poussés,
ignorer les archives et backups régénérables, rattraper la synthèse de la
distribution Phase 1-7 et formaliser les règles de suivi des GO.

**Impact** : aucune modification du code ou de l'archive livrée; les backups
ZIP restent locaux et exclus de Git.

## [2026-10-23] Phase 7E-Lot1 — Corrections critiques documentation

**Commit** : `635ef2f`

**Fichiers modifiés** : `.github/copilot-instructions.md`,
`dev/docs/MEMORY_CONTRACT.md`, `dev/docs/GIT_STRATEGY.md`,
`dev/docs/OUTILS_INTRUSIFS.md`, `.memory/quirks.md`,
`dev/docs/OBJECTIF.md`, `AGENTS.md`, `dev/docs/JOURNALDEBORD.md`.

**Raison** : corriger cinq contradictions P1 identifiées par l'audit
Phase 7D.

**Impact** : documentation alignée sur le produit actuel (runtime et GGUF
séparés, schéma SQLite V3, chemins `dist/` et `vendor/` exacts, signalement
sans restauration automatique, vocabulaire V3.1/authentification clarifié).
La release v0.1.0 supprimée est signalée comme historique; `v3-distribution`
reste prévue après Phase 7E-Lot3.

## [2026-10-23] Synchronisation de la correction README français

**Commit** : `81ab659` (merge normal de `cf1c26e`)

**Fichiers modifiés** : `README.fr.md`.

**Raison** : intégrer la correction de clarté apportée au guide utilisateur
français sur la branche distante.

**Impact** : documentation française synchronisée; aucune modification du
code, des tests ou de l'archive de distribution.

## [2026-10-23] Phase 7E-Lot1c — Restauration consigne de sécurité

**Commit** : Phase 7E-Lot1c (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `README.fr.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : `cf1c26e` (merge `81ab659`) avait retiré l'avertissement de
sécurité sur l'exposition de La Citadelle à un réseau ou à Internet. Les
reformulations accidentelles « DISCUSSION/CHAT » et « Terminale » ont aussi
été corrigées.

**Impact** : avertissement de sécurité restauré et terminologie française
clarifiée; aucun impact sur le code ou les tests.

## [2026-10-23] Phase 7E-Lot2 — Décisions historiques + trailer Assisted-by

**Commit** : Phase 7E-Lot2 (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `.memory/decisions.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : l'audit 7D a identifié quatre décisions supplantées sans
annotation et cinq décisions implicites non actées.

**Impact** : traçabilité complète (23 décisions), trailer `Assisted-by` acté,
tests intermittents reportés en Phase 8, quatre règles `AGENTS.md`
formalisées, licence Apache 2.0 et documentation bilingue tracées.

## [2026-10-23] Phase 7E-Lot3 — TODO.md + corrections doc P2

**Commit** : Phase 7E-Lot3 (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `.gitignore`, `AGENTS.md`,
`dev/docs/ARCHITECTURE.md`, `README.md`, `dev/tools/login_server.py`
(docstring), `dev/docs/AUTH_CONTRACT.md`,
`.github/agents/rules/ponytail.instructions.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`;
`TODO.md` créé localement (gitignoré, non versionné).

**Raison** : finaliser les corrections P2 de l'audit 7D et instaurer
`TODO.md` local avec une stratégie anti-chronologique et un roulement.

**Impact** : documentation alignée sur l'état réel; `TODO.md` reste local,
gitignoré et absent de l'archive; la règle 5 est actée dans `AGENTS.md`.

## [2026-10-23] Phase 7F-A — Barre de progression stdlib

**Commit** : Phase 7F-A (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/bootstrap.py`,
`dev/tests/test_bootstrap_progress.py`, `.memory/decisions.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`;
`TODO.md` mis à jour localement (gitignoré).

**Raison** : rendre visibles les téléchargements de llamafile-thin et du
GGUF pour les utilisateurs.

**Impact** : progression ASCII en TTY et journalisée en non-TTY, deux tests
dédiés, décision #24; aucun ajout de dépendance.

## [2026-10-23] Phase 7F-C — Décision Spec Kit

**Commit** : Phase 7F-C (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `.memory/decisions.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`;
`TODO.md` mis à jour localement (gitignoré).

**Raison** : acter le résultat de l'expérience Spec Kit de la Phase 7F-B.

**Impact** : la méthode actuelle est conservée pour La Citadelle; Spec Kit
reste une piste pour de futurs projets plus gros; aucun changement de code,
de tests ou de dépendance.

## [2026-10-23] Phase 8b — Corps POST consommé avant contrôle d'auth

**Commit** : Phase 8b (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tests/test_change_password.py`, `.memory/decisions.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`;
`TODO.md` mis à jour localement (gitignoré).

**Raison** : corriger le WinError 10053 causé par des requêtes POST refusées
avant consommation de leur corps.

**Impact** : le corps POST est lu une seule fois avant les contrôles, sous
une limite de 1 Mio et en conservant les plafonds propres aux routes; test
de non-régression 401/403 ajouté; 76 tests validés 10/10, sans dépendance.

## [2026-10-23] Phase 9A — Roadmap historique et règle de suivi

**Commit** : Phase 9A (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/docs/ROADMAP.md`, `AGENTS.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.
`TODO.md` vérifié, sans entrée Roadmap à retirer; inchangé.

**Raison** : regrouper l'histoire V1–Phase 8b à partir des traces Git,
décisions, journaux et validations du décideur; formaliser la mise à jour de
la Roadmap à la clôture des phases majeures.

**Impact** : Roadmap macroscopique traçable, sept phases validées, règle 6
ajoutée à la section de suivi; aucune modification du code, des tests ou des
décisions mémoire.

## [2026-10-23] Phase 9B — Correction des compteurs AGENTS.md

**Commit** : Phase 9B (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `AGENTS.md`, `dev/docs/JOURNALDESMODIFS.md`,
`dev/docs/JOURNALDEBORD.md`. `TODO.md` vérifié, sans ligne de compteurs à
retirer; inchangé.

**Raison** : aligner les compteurs de tests et de décisions d'`AGENTS.md` sur
les traces actuelles; vérifier le statut de la release `v3-distribution`.

**Impact** : compteurs corrigés (76 tests, 26 décisions). Aucune mention de
release dans `AGENTS.md`; la release `v3-distribution` a été confirmée sur
GitHub, donc aucune correction de release n'était nécessaire. Aucun code ni
test modifié.

## [2026-10-23] Phase 9C — Backlog versionné Mode B

**Commit** : Phase 9C (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/docs/BACKLOG.md`, `dev/docs/ROADMAP.md`,
`AGENTS.md`, `dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`;
`TODO.md` mis à jour localement (gitignoré).

**Raison** : consigner les tâches Mode B validées, leur dépendance et les
questions restant à trancher en conception.

**Impact** : B-1 inclut l'ancien B-3; B-2 exige rollback automatique et
whitelist testée avec dérogation avertie. Règle 7 de suivi ajoutée; aucun
code, test ou décision mémoire modifié.

## [2026-10-23] Phase 9D — Parcours documentaire et CHANGELOG pointeur

**Commit** : Phase 9D (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `CHANGELOG.md`, `AGENTS.md`,
`.memory/decisions.md`, `dev/docs/JOURNALDESMODIFS.md`,
`dev/docs/JOURNALDEBORD.md`. `TODO.md` vérifié, sans tâche 9D à retirer;
inchangé.

**Raison** : définir l'ordre de lecture des documents, fournir un pointeur
CHANGELOG et maintenir les références projet et règles structurelles.

**Impact** : tableau de fichiers et parcours de lecture ajoutés, décisions
#27–29 actées, règle 8 ajoutée; aucun code ni test modifié.

## [2026-10-23] Phase 10A — Conception Mode B-1

**Commit** : Phase 10A (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.

**Raison** : acter la conception Mode B-1 après validation du décideur.

**Impact** : huit choix de conception consignés en décision #30 et B-1
passé à « à implémenter (spec validée) ». Aucun code, test ou template
modifié.

## [2026-10-24] Phase 10B-1 — Réglages et préférences utilisateur

**Commit** : Phase 10B-1 (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/citadelle_memory.py`,
`dev/tools/login_server.py`, `dev/tools/web/settings.html`,
`dev/tools/web/chat.html`, `dev/tools/web/chat.js`,
`dev/tools/web/style.css`, `dev/tests/test_settings.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.

**Raison** : implémenter la tranche utilisateur validée de B-1 : page de
réglages, préférence de thème et taille du texte en SQLite.

**Impact** : migration idempotente, routes protégées et validées, lien
sidebar, neuf tests dédiés; admin/CRUD, logs et indicateurs restent reportés.

## [2026-10-24] Phase 10B-1b — Changement volontaire du mot de passe

**Commit** : Phase 10B-1b (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/login_server.py` (suppression manuelle
du blocage volontaire par le décideur), `dev/tools/web/change-password.html`,
`dev/tests/test_change_password.py`, `.memory/decisions.md`,
`dev/docs/BACKLOG.md`, `dev/docs/JOURNALDESMODIFS.md`,
`dev/docs/JOURNALDEBORD.md`.

**Raison** : permettre le changement volontaire depuis `/settings` tout en
conservant l'ancien mot de passe comme vérification et le gate obligatoire.

**Impact** : template neutre, tests volontaires ajoutés, assertion obsolète
du mode non-obligatoire actualisée; `401` retenu pour ancien mot de passe
erroné/manquant; 89 tests validés. Aucun autre code serveur modifié.

## [2026-10-24] Phase 10B-2 — Administration read-only

**Commit** : Phase 10B-2 (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/admin.html`, `dev/tools/web/chat.html`,
`dev/tools/web/chat.js`, `dev/tools/web/settings.html`,
`dev/tools/web/style.css`, `dev/tests/test_admin.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.

**Raison** : livrer la première tranche admin du Mode B-1, en lecture seule,
avec contrôle de rôle côté serveur.

**Impact** : page `/admin`, API protégée sans `password_hash`, lien
conditionnel et neuf tests; CRUD, logs et indicateurs restent reportés.

## [2026-10-24] Phase 10B-3-PLAN — Découpage CRUD admin

**Commit** : Phase 10B-3-PLAN (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.

**Raison** : acter et détailler le découpage du CRUD admin en cinq sous-lots
séquentiels avant toute implémentation.

**Impact** : décision #34 et périmètres, dépendances et questions ouvertes
documentés; aucun code ni test modifié.

## [2026-10-24] Phase 10B-3a — Création d'utilisateur admin

**Commit** : Phase 10B-3a (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/admin.html`, `dev/tests/test_admin.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.

**Raison** : permettre à un admin de créer un compte user avec mot de passe
temporaire généré, affiché une seule fois et changé à la première connexion.

**Impact** : route protégée, formulaire admin, validation et sept tests;
aucune action 10B-3b/c/d/e, aucun log ni indicateur ajouté.

## [2026-10-24] Phase 10B-2b — Menu admin conditionnel et règle 9

**Commit** : Phase 10B-2b (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/web/style.css`, `AGENTS.md`,
`.memory/decisions.md`, `dev/docs/JOURNALDESMODIFS.md`,
`dev/docs/JOURNALDEBORD.md`.

**Raison** : corriger l'affichage du lien Administration pour les comptes
user, acter la traçabilité immédiate dans `TODO.md` et tracer le nettoyage
futur de la base sans l'exécuter.

**Impact** : la règle CSS respecte `hidden`; règle 9 et décision #36
documentées. Aucun changement d'autorisation serveur ni suppression de
données.

## [2026-10-24] Phase 10-cleanup — Base locale et superadmin

**Commit** : Phase 10-cleanup (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `.memory/decisions.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.
La base locale `citadelle_data/memory.db` et son backup restent gitignorés.

**Raison** : supprimer les comptes et données de test après sauvegarde
vérifiée, puis créer un compte administrateur propre.

**Impact** : trois comptes, trois sessions, 20 messages et une préférence
supprimés en cascade; un `superadmin` actif créé avec changement de mot de
passe requis. 105 tests passent. `create_admin.py` a levé une erreur
d'encodage après l'insertion, à l'impression de son avertissement; l'état
SQLite a été vérifié. Validation manuelle encore attendue; mot de passe
absent des documents et du commit.

## [2026-10-24] Phase 10-cleanup-ter — Encodage CLI et transfert manuel

**Commit** : Phase 10-cleanup-ter (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/create_admin.py`,
`.memory/decisions.md`, `dev/docs/JOURNALDESMODIFS.md`,
`dev/docs/JOURNALDEBORD.md`.

**Raison** : corriger l'erreur d'encodage Windows du CLI et respecter le
transfert manuel du mot de passe au décideur.

**Impact** : stdout/stderr basculés en UTF-8 sous Windows; 4 tests ciblés et
105 tests passent. Le décideur a confirmé la création manuelle de
`superadmin` puis `didier`; état vérifié en lecture seule. Aucune suppression
de base effectuée par l'IDE; mot de passe absent du commit.

## [2026-10-24] Phase 10C-PLAN — Auto-création admin au démarrage

**Commit** : Phase 10C-PLAN (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.
`TODO.md` a également été mis à jour localement et reste gitignoré.

**Raison** : acter la création automatique du premier admin et documenter
son périmètre avant l'implémentation.

**Impact** : décision #39, Phase 10C, dépendances, périmètre et questions
ouvertes documentés. Aucun code ni test modifié.

## [2026-10-24] Phase 10C — Auto-création admin au démarrage

**Commit** : Phase 10C (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/citadelle_memory.py`,
`dev/tools/login_server.py`, `dev/tests/test_auto_admin.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.
`TODO.md` a été mis à jour localement et reste gitignoré.

**Raison** : implémenter la création du premier compte admin au démarrage
du proxy, selon les décisions #39 et #40.

**Impact** : `superadmin` auto-créé sans admin actif; mot de passe affiché
une seule fois en console; message informatif si admin actif présent; erreur
opérationnelle signalée sans retry ni arrêt du proxy. Quatre tests ajoutés,
109 tests au total.

## [2026-10-24] Phase 10B-3b — Désactivation et réactivation user

**Commit** : Phase 10B-3b (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/admin.html`, `dev/tests/test_admin.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.
`TODO.md` a été mis à jour localement et reste gitignoré.

**Raison** : permettre à un admin de désactiver/réactiver un utilisateur en
respectant les protections du dernier admin et de l'auto-désactivation.

**Impact** : routes protégées, confirmation UI, suppression des sessions de
conversation et révocation des jetons d'authentification à la désactivation.
Six tests ajoutés; 115 tests passent. Aucun code des lots 10B-3c/d/e modifié.

## [2026-10-24] Phase 10B-3b-bis — Suppression explicite des messages

**Commit** : Phase 10B-3b-bis (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tests/test_admin.py`, `.memory/decisions.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.
`TODO.md` a été mis à jour localement et reste gitignoré.

**Raison** : garantir que la désactivation supprime les messages associés
aux sessions, sans dépendre uniquement de la cascade SQLite.

**Impact** : suppression explicite messages → sessions → désactivation dans
la transaction; test d'intégration avec FK désactivées, réactivation et
vérification d'une liste vide. Décision #42; 116 tests passent.


## [2026-10-24] Phase 10B-3c — Promotion/rétrogradation avec transfert admin

**Commit** : Phase 10B-3c (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/admin.html`, `dev/tests/test_admin.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.
`TODO.md` a été mis à jour localement et reste gitignoré.

**Raison** : implémenter promotion et rétrogradation en résolvant la
contradiction du workflow à admin unique par transfert atomique du rôle.

**Impact** : transfert sans état à zéro admin, protections serveur,
confirmations UI et invalidation des sessions/conversations du rétrogradé.
Six tests ajoutés; 122 tests passent. Aucun changement 10B-3d/e.

## [2026-10-24] Phase 10B-3d — Suppression physique d'un utilisateur

**Commit** : Phase 10B-3d (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/admin.html`, `dev/tests/test_admin.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.
`TODO.md` reste local et gitignoré.

**Raison** : permettre la suppression admin d'un utilisateur avec double
confirmation et protection des comptes privilégiés.

**Impact** : suppression physique et cascade FK, invalidation des jetons,
protections serveur du dernier admin et de l'auto-suppression. La table
`metrics` n'existe pas dans le schéma actuel. Cinq tests ajoutés;
127 tests passent. Aucun reset de mot de passe ajouté.

## [2026-10-24] Phase 10B-3e — Reset du mot de passe admin

**Commit** : Phase 10B-3e (identifiant consultable dans l'historique Git)

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/admin.html`, `dev/tests/test_admin.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`, `dev/docs/JOURNALDEBORD.md`.
`TODO.md` reste local et gitignoré.

**Raison** : fournir aux admins un reset à mot de passe temporaire, forcé
au changement au prochain login.

**Impact** : route protégée, mot de passe fort de 16 caractères affiché une
seule fois dans l'interface, sessions d'authentification invalidées, aucun
email ni log du secret. Quatre tests ajoutés; 131 tests passent.

## [2026-10-25] Phase 10B-3f — Validation E2E partielle du CRUD admin

**Commit** : identifiant consultable dans l'historique Git

**Fichiers modifiés** : `dev/docs/JOURNALDEBORD.md`,
`dev/docs/JOURNALDESMODIFS.md`. `TODO.md` reste local et gitignoré.

**Raison** : consigner le résultat de la validation manuelle du CRUD
administrateur dans le navigateur intégré de l'IDE.

**Impact** : 4/6 scénarios E2E réussis. 10B-3d non validé car le navigateur
ne supporte pas `prompt()`; la suppression par route a réussi avec une saisie
simulée uniquement pour nettoyer le compte de test. 10B-3e n'a pas été
exécuté après l'échec. Aucun code ni test automatisé modifié.

## [2026-10-25] Phase 10B-3g — Modal custom et validation E2E CRUD admin

**Commit** : identifiant consultable dans l'historique Git

**Fichiers modifiés** : `dev/tools/web/admin.html`,
`dev/tools/web/style.css`, `dev/tests/test_admin.py`,
`.memory/decisions.md`, `dev/docs/JOURNALDEBORD.md`,
`dev/docs/JOURNALDESMODIFS.md`. `TODO.md` reste local et gitignoré.

**Raison** : remplacer `prompt()` non supporté par le navigateur intégré et
terminer les validations E2E 10B-3d/10B-3e.

**Impact** : modal `<dialog>` accessible avec vérification exacte du username,
erreur inline et annulation clavier; helper réutilisé pour le reset. Une
assertion UI obsolète mise à jour; 131 tests passent. E2E 6/6 OK, dont la
suppression en cascade d'un utilisateur avec une session et deux messages.
Les comptes de test sont supprimés et la base retrouve son état attendu.

## [2026-10-25] Phase 10B-4a — Métriques d'inférence backend

**Commit** : identifiant consultable dans l'historique Git

**Fichiers modifiés** : `dev/tools/citadelle_memory.py`,
`dev/tools/login_server.py`, `dev/tests/test_inference_metrics.py`,
`dev/docs/MEMORY_CONTRACT.md`, `dev/docs/BACKLOG.md`,
`.memory/decisions.md`, `dev/docs/JOURNALDEBORD.md`,
`dev/docs/JOURNALDESMODIFS.md`. `TODO.md` reste local et gitignoré.

**Raison** : persister côté backend les métadonnées d'inférence nécessaires
aux logs sans enregistrer de contenu sensible.

**Impact** : migration SQLite V5 idempotente; capture du user/session,
timestamp, durée, statut et tokens disponibles dans `inference_metrics`.
Aucun prompt, réponse générée ou secret n'est enregistré. Quatre tests
dédiés; 135 tests passent. Aucun endpoint ni changement frontend.

## [2026-10-25] Phase 10B-4b — Route et onglet Logs

**Commit** : identifiant consultable dans l'historique Git

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/admin.html`, `dev/tools/web/settings.html`,
`dev/tools/web/style.css`, `dev/tests/test_logs.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`.
`TODO.md` reste local et gitignoré.

**Raison** : exposer les métadonnées d'inférence aux comptes autorisés dans
une route et une interface locales, sans exposer le contenu des échanges.

**Impact** : route authentifiée filtrée selon le rôle, limite de 500 lignes,
onglet admin et section logs utilisateur, polling visible uniquement.
Cinq tests dédiés; 140 tests passent. E2E navigateur admin et arrêt du
polling hors onglet vérifiés; base restaurée et migration V5 réappliquée.

## [2026-10-25] Phase 10B-5 — Indicateurs agrégés et clôture Mode B-1

**Commit** : identifiant consultable dans l'historique Git

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/admin.html`, `dev/tools/web/settings.html`,
`dev/tools/web/style.css`, `dev/tests/test_indicators.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`.
`TODO.md` reste local et gitignoré.

**Raison** : fournir des indicateurs d'inférence agrégés par fenêtre et
clôturer le Mode B-1 sans exposer le contenu des conversations.

**Impact** : route authentifiée avec filtrage rôle/user et fenêtres 24 h,
7 j et 30 j; 7 indicateurs, cartes KPI admin, tableau user et polling lorsque
la page est visible. Cinq tests dédiés; 145 tests passent. Aucun changement
de schéma ni endpoint/traitement de contenu de conversation.

## [2026-10-25] Phase 11-PLAN — Conception du Mode B-2

**Commit** : identifiant consultable dans l'historique Git

**Fichiers modifiés** : `.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`.
`TODO.md` reste local et gitignoré.

**Raison** : acter les cinq choix de conception du changement de modèle
administrateur avant toute implémentation.

**Impact** : décision #50 et sous-lots 11a–11f proposés; aucun code, test,
template ou configuration modifié.

## [2026-10-25] Phase 11-PLAN-BIS — Sous-lots Mode B-2 et audit TODO

**Commit** : identifiant consultable dans l'historique Git

**Fichiers modifiés** : `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`.
`TODO.md` reste local et gitignoré.

**Raison** : détailler les six sous-lots d'implémentation et rendre
explicitement visibles les travaux en attente, bloqués et dettes résiduelles.

**Impact** : périmètres, dépendances et questions ouvertes 11a–11f ajoutés.
Audit TODO : 12 divergences de libellés historiques, 8 travaux en attente,
2 bloqués et 2 incohérences documentaires clarifiées. Aucun code modifié.

## [2026-10-25] Phase 11a — Migration settings et helpers

**Commit** : `d2fdc3b`

**Fichiers modifiés** : `dev/tools/citadelle_memory.py`,
`dev/tools/login_server.py`, `dev/tests/test_settings_migration.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`.
`TODO.md` reste local et gitignoré.

**Raison** : fournir le stockage SQLite et les helpers nécessaires au futur
changement de modèle, avant toute route ou interface.

**Impact** : migration V6 idempotente appelée depuis `init_db()` et au
démarrage du proxy; helpers get/set avec upsert. Quatre tests dédiés,
149 tests au total. Aucun endpoint ou fichier UI modifié.

## [2026-10-25] Phase 11b — Route de configuration du modèle

**Commit** : `7c9786c`

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tests/test_admin_model.py`, `.memory/decisions.md`,
`dev/docs/BACKLOG.md`, `dev/docs/JOURNALDEBORD.md`,
`dev/docs/JOURNALDESMODIFS.md`. `TODO.md` reste local et gitignoré.

**Raison** : permettre à un admin actif d'enregistrer le chemin d'un GGUF
local validé avant les lots de test de chargement et d'interface.

**Impact** : route protégée, validation du fichier et écriture
`current_model_path`; cinq tests dédiés, 154 tests passent. Aucun test de
chargement, redémarrage llamafile ou changement UI.

## [2026-10-25] Phase 11b-bis — Fiabilisation du lancement

**Commit** : `b7903ca`

**Fichiers modifiés** : `lancer.bat`, `.memory/decisions.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`.
`TODO.md` reste local et gitignoré.

**Raison** : remplacer le délai fixe de lancement par des contrôles de
disponibilité et conserver les erreurs du proxy pour diagnostic.

**Impact** : sondage actif de llamafile (max 120 s) et du proxy (max 60 s);
stderr seul vers `dist/proxy.log`, stdout préservé pour le mot de passe
one-time. Trois lancements vérifiés, HTTP 200 sur les deux ports. Aucun code
Python, test ni interface modifié.

## [2026-10-26] Phase 11b-ter (documentaire) — Entrée BACKLOG 11b-bis

**Commit** : `b233778`

**Fichiers modifiés** : `dev/docs/BACKLOG.md`.

**Raison** : ajouter après coup l'entrée de suivi du correctif de lancement
Phase 11b-bis.

**Impact** : entrée documentaire 11b-bis ajoutée au BACKLOG; aucun sous-lot
technique 11b-ter ni changement runtime.

## [2026-10-27] Phase 11c-PRE-3 — Correctifs documentaires P2

**Commit** : référence consultable dans l'historique Git (hash de ce commit
non auto-référençable).

**Fichiers modifiés** : `AGENTS.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`.
`TODO.md` a été mis à jour localement et reste gitignoré.

**Raison** : corriger les huit écarts documentaires P2 relevés par l'audit
11c-PRE-2B avant la Phase 11c.

**Impact** : compteurs et progression documentaire actualisés; questions
résolues retirées du BACKLOG; origine des données de test reformulée; hashes
et nomenclature des commits 11a à 11b-ter précisés. Aucun code ni test modifié.

## [2026-10-27] Phase 11c — Section UI de changement de modèle

**Commit** : `a79d6f3`

**Fichiers modifiés** : `dev/tools/web/settings.html`,
`dev/tools/login_server.py`, `dev/tests/test_settings_ui.py`,
`.memory/decisions.md`, `AGENTS.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`.
`TODO.md` a été mis à jour localement et reste gitignoré.

**Raison** : permettre à un admin de configurer le chemin du modèle depuis
`/settings` et de consulter la valeur enregistrée, en réutilisant le POST 11b.

**Impact** : section UI masquée hors admin, GET admin-only pour le chemin
configuré, POST 11b inchangé; trois tests HTTP ajoutés. Le chargement runtime
reste différé au test et redémarrage 11d.

## [2026-10-27] Phase 11c — Page admin dédiée de changement de modèle

**Commit** : `cedd1e5`

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/admin.html`, `dev/tools/web/admin_model.html`,
`dev/tests/test_admin_model_page.py`, `.memory/decisions.md`,
`dev/docs/BACKLOG.md`, `dev/docs/JOURNALDEBORD.md`,
`dev/docs/JOURNALDESMODIFS.md`. `TODO.md` reste local et gitignoré.

**Raison** : ajouter une page d'administration dédiée en complément de la
section de réglages existante, tout en réutilisant la validation de 11b.

**Impact** : GET/POST `/admin/model` protégés, template statique avec feedback
par redirection; le contrat JSON `/api/admin/model` reste inchangé. Cinq tests
HTTP ajoutés; le chargement runtime et le rollback restent en 11d.

## [2026-10-27] Phase 11c — Référence du commit de la page dédiée

**Commit** : référence consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final de l'implémentation dédiée
dans les références Phase 11c.

**Impact** : le BACKLOG et l'entrée Phase 11c référencent `cedd1e5`; aucun
code ni test modifié.

## [2026-10-28] Phase 11c-consolidation-v3 — Retrait manuel de la page dédiée

**Commit** : `4347c2f`

**Fichiers modifiés** : `.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`,
`dev/tools/login_server.py`, `dev/tools/web/admin.html`.
Fichiers supprimés : `dev/tests/test_admin_model_page.py`,
`dev/tools/web/admin_model.html`. `TODO.md` reste local et gitignoré.

**Raison** : supprimer la duplication de l'interface `/admin/model` v1 tout en
conservant la section `/settings` v2 et son GET admin-only; les commits v1
concernés sont `cedd1e5` et `2864b3c`.

**Impact** : routes et template de page dédiée retirés; `GET /api/settings/model`
et `POST /api/admin/model` conservés. Les 157 tests v2 passent. Aucun
`git revert` ni changement des décisions #50–#55.

## [2026-10-28] Phase 11c-consolidation-v3 — Références des commits v1

**Commit** : identifiant consultable dans l'historique Git (correction
documentaire post-commit).

**Fichiers modifiés** : `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : préciser les hashes des commits v1 annulés dans la consolidation.

**Impact** : BACKLOG et journaux identifient `cedd1e5`, `2864b3c` et le commit
correctif `4347c2f`; aucun code ni test modifié.

## [2026-10-28] Phase 11d — Chargement réel et rollback manuel

**Commit** : `7a13c19`.

**Fichiers modifiés** : `dev/tools/model_health.py`,
`dev/tools/login_server.py`, `dev/tests/test_model_health.py`,
`dev/tests/test_admin_model.py`, `lancer.bat`,
`dev/tools/web/settings.html`, `.memory/decisions.md`,
`dev/docs/BACKLOG.md`, `dev/docs/JOURNALDEBORD.md`,
`dev/docs/JOURNALDESMODIFS.md`. `TODO.md` reste local et gitignoré.

**Raison** : charger le chemin configuré au redémarrage, vérifier le modèle
servi par `/v1/models` et restaurer le chemin précédent sans reload assisté.

**Impact** : miroir `dist/.current_model`, rollback manuel avec demande de
redémarrage, sept tests ajoutés; 164 tests au total.

## [2026-10-28] Phase 11c-consolidation-v3 — Référence du commit de correction

**Commit** : référence consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit de consolidation
manuelle dans les références 11c.

**Impact** : BACKLOG et journal pointent vers `4347c2f`; aucun code ni test
modifié.

## [2026-10-27] Phase 11c — Référence du hash d'implémentation

**Commit** : identifiant consultable dans l'historique Git (entrée de suivi
du hash du commit `a79d6f3`).

**Fichiers modifiés** : `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit d'implémentation
Phase 11c dans ses références documentaires.

**Impact** : BACKLOG et journal pointent vers `a79d6f3`; aucun code ni test
modifié.

## [2026-10-28] Phase 11d — Référence du hash d'implémentation

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit d'implémentation
Phase 11d dans ses références documentaires.

**Impact** : BACKLOG et journal pointent vers `7a13c19`; aucun code ni test
modifié.

## [2026-10-28] Phase 11d-ter — Validation du chemin modèle

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `lancer.bat`, `.memory/decisions.md`,
`dev/docs/BACKLOG.md`, `dev/docs/JOURNALDEBORD.md` et
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : valider l'existence du GGUF avant llamafile, restaurer le chemin
précédent si possible et arrêter clairement si le chemin par défaut manque.

**Impact** : un chemin invalide ne déclenche plus le démarrage de llamafile
avant le rollback; tests isolés du batch valides et invalides.

## [2026-10-28] Phase 11d-quater — Isolation des tests modèle

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/tests/test_admin_model.py`,
`dev/tests/test_model_health.py`, `.memory/decisions.md`,
`dev/docs/BACKLOG.md`, `dev/docs/JOURNALDEBORD.md` et
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : corriger l'isolation des constantes du miroir et restaurer le
fichier réel après chaque test.

**Impact** : ajout d'un test de non-régression; 165 tests passent sans laisser
`dist/.current_model` pollué.

## [2026-10-28] Phase 11d-ter/quater — Référence du commit

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit de correction,
qui ne peut pas s'auto-référencer.

**Impact** : les entrées 11d-ter et 11d-quater pointent vers `2067dbf`;
aucun code ni test modifié.

## [2026-10-28] Phase 11e — Whitelist configurable de modèles (V1)

**Commit** : `4762646`.

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/settings.html`, `dev/tests/test_admin_model.py`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md` et `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : permettre à l'admin de gérer les chemins GGUF autorisés et
refuser les chemins valides mais absents de la whitelist.

**Impact** : validation GGUF existante conservée avant le contrôle
d'autorisation; 6 tests ajoutés, 171 tests passent.

## [2026-10-28] Phase 11e — Référence du commit

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit d'implémentation
Phase 11e.

**Impact** : BACKLOG et journal pointent vers `4762646`; aucun code ni test
modifié.

## [2026-10-28] Phase 11e-bis — Ordre whitelist avant sélection

**Commit** : `80814a0`.

**Fichiers modifiés** : `dev/tools/web/settings.html`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md` et `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : afficher la configuration de la whitelist avant le choix du
modèle actif.

**Impact** : déplacement HTML uniquement; IDs, JavaScript et endpoints
inchangés; 171 tests passent.

## [2026-10-28] Phase 11e-bis — Référence du commit

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit 11e-bis.

**Impact** : BACKLOG et journal pointent vers `80814a0`; aucun code ni test
modifié.

## [2026-10-28] Phase 11f — Filet whitelist, E2E et logs sécurité

**Commit** : `fd3fd79`.

**Fichiers modifiés** : `dev/tools/model_health.py`, `lancer.bat`,
`dev/tools/login_server.py`, `dev/tests/test_model_health.py`,
`dev/tests/test_e2e_model_change.py`, `.memory/decisions.md`,
`dev/docs/BACKLOG.md`, `dev/docs/ROADMAP.md`,
`dev/docs/JOURNALDEBORD.md` et `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : empêcher le démarrage d'un modèle hors whitelist, tester le
workflow admin de bout en bout et tracer les changements et rollbacks.

**Impact** : contrôle fail-closed avant llamafile, tests E2E et logs
`[security]` dans `dist/proxy.log`; 176 tests passent.

## [2026-10-28] Phase 11f — Référence du commit

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md` et `dev/docs/ROADMAP.md`.

**Raison** : ajouter après création le hash final de clôture de la Phase 11.

**Impact** : BACKLOG, journal et Roadmap pointent vers `fd3fd79`; aucun code
ni test modifié.

## [2026-10-29] Phase 11-POLISH — Documentation, messages et CORS

**Commit** : `09524b5`.

**Fichiers modifiés** : `AGENTS.md`, `dev/docs/JOURNALDEBORD.md`,
`dev/tools/login_server.py`, `dev/tests/test_admin_model.py`,
`dev/tests/test_e2e_model_change.py`, `lancer.bat`,
`dev/docs/RUNBOOK.md`, `.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : clore les dettes documentaires de la Phase 11, distinguer les
erreurs de validation GGUF et restreindre CORS avec l'option du runtime.

**Impact** : procédure admin de reset temporaire documentée, CORS limité
aux origines locales et 176 tests conservés.

## [2026-10-29] Phase 11-POLISH — Référence du commit

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit 11-POLISH.

**Impact** : BACKLOG et journal pointent vers `09524b5`; aucun code ni test
modifié.

## [2026-10-29] Phase 11-POLISH-BIS-CORS — Retour au défaut llamafile

**Commit** : `56e8e54`.

**Fichiers modifiés** : `lancer.bat`, `.memory/decisions.md`,
`dev/docs/BACKLOG.md`, `dev/docs/JOURNALDEBORD.md` et
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : le runtime renvoyait la liste `--cors-origins` comme une seule
valeur `Access-Control-Allow-Origin`, refusée par les navigateurs.

**Impact** : suppression du flag; le défaut CORS local du runtime est
restauré. Le frontend reste proxyfié par `login_server.py`.

## [2026-10-29] Phase 11-POLISH-BIS-CORS — Référence du commit

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du correctif CORS.

**Impact** : BACKLOG et journal pointent vers `56e8e54`; aucun code ni test
modifié.

## [2026-10-29] Phase 11-POLISH-QUATER — Corrections documentaires

**Commit** : `0982b96`.

**Fichiers modifiés** : `AGENTS.md`, `dev/docs/BACKLOG.md`,
`dev/docs/ROADMAP.md`, `dev/docs/JOURNALDEBORD.md` et
`dev/docs/JOURNALDESMODIFS.md`. `TODO.md` reste local et gitignoré.

**Raison** : corriger les écarts documentaires #1, #2, #3, #5, #6, #7 et
#8 relevés lors de l'audit 11-POLISH-TER; documenter #55 comme retirée par #56.

**Impact** : compteurs, inventaire B-1, snapshots TODO et Roadmap alignés;
doublon historique retiré et sous-lot upload ajouté au Backlog; 176 tests
inchangés.

## [2026-10-29] Référence du commit 11-POLISH-QUATER

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final des corrections documentaires.

**Impact** : le commit principal 11-POLISH-QUATER est référencé par `0982b96`.

## [2026-10-29] Phase 11-FINAL-DETTES — CORS, guides et limites

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `AGENTS.md`, `.memory/decisions.md`, `README.md`,
`README.fr.md`, `lancer.bat`, `dev/tools/login_server.py`,
`dev/tests/test_llamafile_proxy.py`, `dev/tests/test_load.py`,
`dev/docs/RUNBOOK.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md` et `dev/docs/JOURNALDESMODIFS.md`.
`TODO.md` reste local et gitignoré.

**Raison** : réduire la dette CORS, compléter les consignes utilisateur,
mesurer le login séquentiel et consigner les limites concurrentes et 10C.

**Impact** : CORS limité à une origine locale et routes proxy authentifiées;
181 tests verts, dont 100 logins en 6,9 s. Playwright, test manuel 10C et
charge concurrente restent reportés.

## [2026-10-29] RELEASE-UPDATE — Asset utilisateur v3-distribution

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md` et `dev/docs/JOURNALDESMODIFS.md`; asset
`lacitadelle-distribution.zip` de la release `v3-distribution`.
`TODO.md` reste local et gitignoré.

**Raison** : remplacer l'asset antérieur à la Phase 11 par une archive issue
des fichiers suivis du dépôt à `e3a1082`.

**Impact** : 82 entrées (81 fichiers suivis et `LISEZMOI.txt`), 219 243
octets; SHA-256 vérifié identique après téléchargement depuis GitHub.


## [2026-10-30] Phase MEP — Préparation production

**Commit** : `a729e99`.

**Fichiers modifiés** : `Caddyfile`, `AGENTS.md`,
`dev/docs/ARCHITECTURE-PROD.md`, `dev/docs/RUNBOOK-PROD.md`,
`.memory/decisions.md`, `dev/docs/BACKLOG.md`,
`dev/docs/JOURNALDEBORD.md` et `dev/docs/JOURNALDESMODIFS.md`.
`TODO.md` reste local et gitignoré.

**Raison** : préparer le reverse proxy HTTPS, le DNS/pare-feu, les sauvegardes
SQLite et le monitoring sans déployer de service.

**Impact** : Caddyfile modèle et runbooks prêts pour revue; aucun code métier,
test, DNS, pare-feu, certificat ou service modifié/déployé. Le go-live reste
bloqué par les contrôles V3.1 non implémentés.

## [2026-10-30] Référence du commit Phase MEP

**Commit** : identifiant consultable dans l'historique Git (hash non
auto-référençable).

**Fichiers modifiés** : `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit de préparation MEP.

**Impact** : le commit principal Phase MEP est référencé par `a729e99`.

## [2026-10-30] Sécurité V3.1 — Cookie Secure, CSRF et rate limiting

**Commit** : référence à ajouter après création du commit.

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/chat.html`, `dev/tools/web/chat.js`,
`dev/tools/web/settings.html`, `dev/tools/web/admin.html`,
`dev/tools/web/change-password.html`, `dev/tests/test_security.py`,
`dev/tests/_helpers.py`, `dev/tests/test_change_password.py`,
`dev/docs/AUTH_CONTRACT.md`, `dev/docs/RUNBOOK-PROD.md`,
`dev/docs/ARCHITECTURE-PROD.md`, `dev/docs/BACKLOG.md`,
`.memory/decisions.md`, `dev/docs/JOURNALDEBORD.md` et
`dev/docs/JOURNALDESMODIFS.md`. `TODO.md` reste local et gitignoré.

**Raison** : ajouter les protections V3.1 bloquantes avant toute exposition
publique et conserver la compatibilité des tests HTTP authentifiés.

**Impact** : Secure conditionnel au HTTPS, jeton CSRF par session et
limitation mémoire par IP; cinq tests de sécurité ajoutés, suite complète
186 tests verts. Aucun déploiement effectué; MEP-BIS reste manuel.

## [2026-10-30] Phase MEP-BIS — Validation locale et compteurs

**Commit** : `9cd6ab9`.

**Fichiers modifiés** : `AGENTS.md`, `.memory/decisions.md`,
`dev/docs/BACKLOG.md`, `dev/docs/JOURNALDEBORD.md` et
`dev/docs/JOURNALDESMODIFS.md`. `TODO.md` reste local et gitignoré.

**Raison** : confirmer les contrôles V3.1 en runtime local, aligner les
compteurs du guide agents et auditer les prérequis documentés de production.

**Impact** : 186 tests permanents et 68 décisions référencés; HTTP local
vérifié (login, cookie, CSRF, 429). Les 429 sont journalisés comme accès
`[proxy]`, sans événement dédié `[security]`; aucun déploiement effectué.

## [2026-10-30] Référence du commit Phase MEP-BIS

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit de validation
MEP-BIS.

**Impact** : le commit principal Phase MEP-BIS est référencé par `9cd6ab9`.

## [2026-10-30] Phase 12-FIX-WHITELIST — Première installation

**Commit** : `9b5a0b4`.

**Fichiers modifiés** : `lancer.bat`, `dev/tools/citadelle_memory.py`,
`dev/tools/model_health.py`, `dev/tests/test_first_install_model.py`,
`.memory/diag-12-whitelist.md`, `.memory/decisions.md`,
`dev/docs/BACKLOG.md`, `dev/docs/JOURNALDEBORD.md` et
`dev/docs/JOURNALDESMODIFS.md`. `TODO.md` reste local et gitignoré.

**Raison** : initialiser la whitelist du GGUF intégré sur base neuve,
conditionner le contrôle de démarrage à un modèle courant valide et refuser
un rollback automatique sans précédent.

**Impact** : SHA-256 du GGUF vérifié avant autorisation initiale; huit tests
ajoutés, 194 tests verts, aucun test préexistant modifié. Aucun déploiement;
validation VM vierge à faire.

## [2026-10-30] Référence du commit Phase 12-FIX-WHITELIST

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit de correction
Phase 12-FIX-WHITELIST.

**Impact** : le commit principal Phase 12-FIX-WHITELIST est référencé par
`9b5a0b4`.
