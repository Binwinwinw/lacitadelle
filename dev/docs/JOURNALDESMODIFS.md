# Journal des modifications

Ce document résume les évolutions du produit et de sa distribution.

## [2026-11-13] Fix Ruff B011 (assert False dans tests)

**Commit** : en cours de rédaction.
**Fichiers modifiés** : `dev/tests/test_auth_hash.py`,
`dev/tests/test_migration_v3.py`, `.memory/decisions.md`, `AGENTS.md`,
journaux.
**Raison** : Ruff B011 dans 3 tests.
**Impact** : tests robustes sous python -O. 93 décisions.

## [2026-11-13] Création ETAT-PROJET.md

**Commit** : en cours de rédaction.
**Fichiers modifiés** : `dev/docs/ETAT-PROJET.md` (nouveau),
`AGENTS.md`, `.memory/decisions.md`, journaux.
**Raison** : fournir un point d'entrée "état actuel".
**Impact** : documentation pérenne. Règle 13 ajoutée. 92 décisions.

## [2026-11-13] Clôture post-audit — La Citadelle stable

**Commit** : en cours de rédaction.
**Fichiers modifiés** : `.memory/decisions.md`, `TODO.md`, journaux.
**Raison** : test manuel complet validé par le Décideur.
**Impact** : La Citadelle est officiellement stable. 6 Must Fix résolus.
91 décisions, 244 tests. Prêt pour release.

## [2026-11-12] Bilan audit ponytail-audit (6 fix résolus)

**Commit** : en cours de rédaction.

**Fichiers modifiés** : `.memory/decisions.md`, `TODO.md`,
`dev/docs/LLM-LIMITES.md`, `AGENTS.md`, journaux.

**Raison** : consigner l'audit et ses 6 fix.

**Impact** : documentation pérenne. Règle 12 "audit avant release"
ajoutée. 90 décisions.

## [2026-11-12] Fix payload model (audit Should Fix 3)

**Commit** : en cours de rédaction.

**Fichiers modifiés** : `dev/tools/login_server.py`,
`.memory/decisions.md`, `AGENTS.md`, `dev/docs/JOURNALDEBORD.md`,
`dev/docs/JOURNALDESMODIFS.md`.

**Raison** : payload envoyait l'identifiant Qwen3-1.7B en dur.

**Impact** : le payload reflète désormais le modèle actif.

## [2026-11-12] Fix REPL contexte + doc modèle (audit Must Fix 4+5)

**Commit** : en cours de rédaction.

**Fichiers modifiés** : `dev/tools/client.py`,
`dev/docs/ARCHITECTURE.md`, `dev/docs/OBJECTIF.md`,
`dev/docs/RUNBOOK-PROD.md`, `dev/docs/BACKLOG.md`,
`.memory/decisions.md`, `AGENTS.md`, journaux.

**Raison** : audit révèle incohérence REPL + docs obsolètes.

**Impact** : cohérence webchat/REPL, docs alignées. 244 tests,
88 décisions.

## [2026-11-12] Fix proxy démarre après échec migration (audit Must Fix 3)

**Commit** : en cours de rédaction.

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tests/test_auto_admin.py`, `.memory/decisions.md`,
`AGENTS.md`, journaux.

**Raison** : audit révèle que le proxy démarre malgré échec migration.

**Impact** : sys.exit(1) si migration échoue. Test adapté. 244 tests,
87 décisions.

## [2026-11-12] Fix migration destructive (audit Must Fix 2)

**Commit** : en cours de rédaction.

**Fichiers modifiés** : `dev/tools/citadelle_memory.py`,
`dev/tests/test_migration_backup.py`, `.memory/decisions.md`,
`AGENTS.md`, journaux.

**Raison** : audit révèle que migrate_to_v3 peut DROP TABLE sans backup.

**Impact** : backup automatique avant migration destructive.
Collision timestamp gérée. 2 tests (242 + 2 = 244).

## [2026-11-12] Fix distribution Qwen3-4B

**Commit** : en cours de rédaction.

**Fichiers modifiés** : `dev/tools/llamafile_config.json`,
`dev/tools/model_health.py`, `dev/tools/citadelle_memory.py`,
`.memory/decisions.md`, `AGENTS.md`, `dev/docs/LLM-LIMITES.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : audit révèle que le passage à Qwen3-4B n'était pas
distribué (config, model_health, citadelle_memory attendaient 1.7B).

**Impact** : installation propre alignée sur Qwen3-4B et son SHA-256.
Signal PAIT-GGUF-100 accepté et documenté; le renderer n'est pas décrit
comme une garantie générale de sandbox.

## [2026-11-09] Context strategy — MAX_CONTEXT_TOKENS

**Commit** : en cours de rédaction.

**Fichiers modifiés** : `dev/tools/citadelle_memory.py`,
`dev/tools/login_server.py`, `dev/tests/test_chat_context.py`,
`.memory/decisions.md`, `AGENTS.md`, journaux.

**Raison** : MAX_CONTEXT_MESSAGES=15 (impair) pouvait couper une paire.

**Impact** : conversations longues supportées, troncature propre.
Tests : 241 passed (237 + 4).

## [2026-11-09] Persona V1.6 — Avertissement factuel

**Commit** : en cours de rédaction.

**Fichiers modifiés** : `dev/tools/prompts/system.txt`, `.memory/decisions.md`,
`dev/docs/JOURNALDEBORD.md`, `dev/docs/JOURNALDESMODIFS.md`, `chat.js`,
`style.css`, `TODO.md`, `AGENTS.md`.

**Raison** : Qwen3-4B hallucine sur les faits post-2024. V1.6 ajoute
avertissement + interdit détails précis. Avertissement UI ajouté.

**Impact** : Nexxus honnête mais limité sur les faits récents. 241 tests
(avec tests context) attendus. RAG local = dette identifiée.

## [2026-11-08] Persona V1.5 — Anti-affirmation juridique

**Commit** : en cours de rédaction (hash final à acter après validation).

**Fichiers modifiés** : `dev/tools/prompts/system.txt`,
`.memory/decisions.md`, `JOURNALDEBORD.md`, `JOURNALDESMODIFS.md`.

**Raison** : Qwen3-4B affirmait que les articles cités étaient corrects.

**Impact** : règle "ne jamais affirmer" ajoutée. Limite citation articles
acceptée. Phase persona clôturée à V1.5.

## [2026-11-08] Phase 16-MODEL-DEFAULT-SWITCH — Qwen3-4B par défaut

**Commit** : d40721b (feat: Qwen3-4B par défaut, 16-MODEL-DEFAULT-SWITCH).

**Fichiers modifiés** : `dev/tools/lancer.py`,
`dev/tests/test_first_install_model.py`, `.memory/decisions.md`,
`AGENTS.md`, `TODO.md`, JOURNALDESMODIFS.md, JOURNALDEBORD.md.

**Raison** : Qwen3-4B suit mieux les règles persona V1.3/V1.4 et produit
des réponses plus structurées sur les tests révélateurs. Le test utilise un
import dynamique pour lire le défaut sans hardcode.

**Impact** : défaut changé, test auto-adaptatif. Note : le commit `a6fef62`
(persona V1.4 system.txt) est journalisé ici (correctif post-commit).
Suite : validation manuelle par le Décideur.

## [2026-11-07] Persona V1.3 — limites confirmées de Qwen3-1.7B

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/tools/prompts/system.txt`,
`.memory/decisions.md`, `TODO.md`, AGENTS.md, JOURNALDESMODIFS.md et
JOURNALDEBORD.md.

**Raison** : consigner les observations manuelles post-V1.3 et prioriser
l'évaluation de modèles conversationnels plus grands.

**Impact** : le prompt V1.3 est conservé; les limites juridiques/factuelles
de Qwen3-1.7B et les trois règles prompt ajoutées sont documentées. Aucun
code métier ni test n'est modifié; la validation d'alternatives reste à faire.

## [2026-11-07] Phase 16-CHAT-STREAMING-V1 — Réponses SSE thinking-aware

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/tools/login_server.py`,
`dev/tools/web/chat.js`, `dev/tools/web/style.css`,
`dev/tests/test_chat_streaming.py`, `.memory/decisions.md`, `TODO.md` et
AGENTS.md; journaux de session et de commit.

**Raison** : afficher progressivement les réponses Nexxus, filtrer le flux
de raisonnement et assainir chaque rendu Markdown.

**Impact** : rétrocompatibilité JSON conservée; texte complet persisté à la
fin du flux sans changement de schéma. Cinq tests ajoutés (237 au total).
Validation visuelle XSS/streaming par le Décideur en attente.

## [2026-11-06] Clôture diagnostic Nexxus et persona V1.2

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/tools/prompts/system.txt`,
`.memory/decisions.md`, `TODO.md`, `JOURNALDESMODIFS.md`,
`JOURNALDEBORD.md`.

**Raison** : clore le cycle de diagnostic R4/R5 et corriger trois défauts
de persona observés (émojis, clôture, hallucinations factuelles).

**Impact** : trois puces ajoutées au prompt système. Aucun code modifié.
Tests R4/R5 (deux sessions de cinq tours) sans radotage entre tours;
erreurs factuelles sur Markdown documentées comme limite acceptée du modèle
par défaut.

## [2026-11-06] Phase 16-CHAT-MARKDOWN-V1-FIX — Vérification SRI et backlog V2

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/docs/BACKLOG.md`, JOURNALDEBORD.md et
JOURNALDESMODIFS.md.

**Raison** : confirmer les empreintes des scripts CDN Markdown et tracer
l'option future de vendorisation offline, à traiter si la dépendance CDN
devient un problème.

**Impact** : les SRI configurés sont exacts pour les deux bundles vérifiés;
aucun changement de code ni release n'est requis.

## [2026-11-06] Phase 16-CHAT-MARKDOWN-V1 — Rendu Markdown assaini

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/tools/web/chat.html`, `chat.js`, `style.css`,
`dev/tests/test_chat_markdown.py`, RUNBOOK-PROD.md, AGENTS.md, BACKLOG, TODO
et journaux.

**Raison** : afficher les réponses de l'assistant avec une mise en forme
Markdown tout en empêchant l'injection de HTML non fiable.

**Impact** : Marked et DOMPurify sont chargés avec versions et empreintes SRI
épinglées; deux tests statiques ajoutés; sans CDN, rendu en texte brut.
Validation visuelle par le Décideur en attente.

## [2026-11-06] Phase 15-RELEASE-WINDOWS-V1 — Préparation v3.1.0

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `RELEASE-NOTES.md`, `TODO.md`, JOURNALDEBORD.md et
JOURNALDESMODIFS.md; archive source-only régénérée localement.

**Raison** : documenter l'EXE Windows one-click avec son SHA-256 et préparer
la distribution source-only pour la publication manuelle de v3.1.0.

**Impact** : le ZIP ne contient ni `.git`, ni `node_modules`, ni binaires;
l'EXE reste un fichier séparé. Aucune release GitHub n'est publiée.

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

## [2026-10-30] RELEASE-ZIP — Archive source-only v3 et notes

**Commit** : `14c7445`.

**Fichiers modifiés** : `dev/tools/creer_archive.py`, `RELEASE-NOTES.md`,
`SECURITY.md`, `dev/docs/JOURNALDEBORD.md` et
`dev/docs/JOURNALDESMODIFS.md`. L'archive ZIP reste ignorée par Git.

**Raison** : aligner le générateur sur le contenu source-only existant,
embarquer les documents de sécurité/release et exclure données locales,
caches, secrets et binaires.

**Impact** : archive régénérée localement depuis le source V3/Phase 12; les
SHA-256 runtime/GGUF sont conservés dans le bootstrap. Le SHA-256 de l'archive
est communiqué séparément pour éviter une empreinte auto-référente; aucun
binaire ni déploiement n'est ajouté.

## [2026-10-30] Référence du commit RELEASE-ZIP

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit de packaging
source-only.

**Impact** : le commit principal RELEASE-ZIP est référencé par `14c7445`.

## [2026-10-30] Phase 12-POLISH-INSTALL-DOC — Parcours poste neuf

**Commit** : `9bc6c55`.

**Fichiers modifiés** : `dev/docs/RUNBOOK-PROD.md`,
`dev/docs/JOURNALDEBORD.md` et `dev/docs/JOURNALDESMODIFS.md`.
`TODO.md` ne contenait aucune dette `INSTALL-DOC` et reste inchangé.

**Raison** : documenter le premier démarrage Windows, la sortie console du
mot de passe one-time, la redirection stderr vers `dist/proxy.log` et le
dépannage correspondant.

**Impact** : documentation seulement; aucun code, test, base ou service
modifié. Les tests de référence restent à 194; l'archive release n'est pas
régénérée dans ce GO.

## [2026-10-30] Référence du commit INSTALL-DOC

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/docs/JOURNALDESMODIFS.md`.

**Raison** : ajouter après création le hash final du commit de documentation
INSTALL-DOC.

**Impact** : le commit principal INSTALL-DOC est référencé par `9bc6c55`.

## [2026-10-31] Phase 13-CROSS-PLATFORM — Windows, Linux et macOS

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : bootstrap, installateur et lanceur Python; wrappers
natifs; configuration et générateur ZIP; tests; documentation produit,
contrats, runbook, sécurité et release; décision #71, TODO, BACKLOG et journaux.

**Raison** : ajouter le support Windows/Linux/macOS en réutilisant l'asset
llamafile thin universel vérifié, sans modifier la politique source-only de la
décision #66.

**Impact** : huit tests multiplateformes ajoutés, suite complète à 202 tests;
archive source-only régénérée. Validation manuelle Linux/macOS et diffusion
restent en attente du Décideur.

## [2026-10-31] Phase 13-CROSS-PLATFORM-BIS — Correctifs Linux APE et wrappers

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `.gitattributes`, générateur d'archive, lanceur,
tests multiplateformes, amendement de la décision #71, journaux et BACKLOG.

**Raison** : corriger les fins CRLF des wrappers ZIP, l'exécution du runtime APE
sur Linux et l'ordre des arguments llamafile révélés par le test réel.

**Impact** : trois tests T8/T9/T10 ajoutés; la suite compte 205 tests. Archive
source-only régénérée; Linux validé, tests manuels Windows/macOS en attente.

## [2026-10-31] Phase 13-CROSS-PLATFORM-TER — Leçons post-test Linux

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `RELEASE-NOTES.md`, `dev/docs/RUNBOOK-PROD.md`,
`AGENTS.md`, `dev/docs/BACKLOG.md`, `dev/docs/JOURNALDESMODIFS.md` et
`dev/docs/JOURNALDEBORD.md`.

**Raison** : diffuser les correctifs CRLF, APE et ordre des arguments aux
utilisateurs, mainteneurs et futures sessions IDE après le test Linux réel.

**Impact** : documentation uniquement; aucune modification de code ni de test.
La suite reste à 205 tests; l'asset GitHub n'est pas modifié.

## [2026-10-31] Phase 14-DETTES-DOC — Procédures P2/P3

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/docs/RUNBOOK-PROD.md`, `SECURITY.md`,
`dev/docs/BACKLOG.md`, `TODO.md`, `dev/docs/JOURNALDESMODIFS.md` et
`dev/docs/JOURNALDEBORD.md`.

**Raison** : clarifier les plans Playwright, concurrence mono-thread,
vérification des ports 80/443 et journalisation de sécurité; convertir les
dettes correspondantes en prochaines étapes explicites.

**Impact** : documentation uniquement; 205 tests inchangés, aucun déploiement
ni mise à jour de release.

## [2026-10-31] Phase 14-PERSONA-NEXXUS-V1 — Persona et politique fichiers

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : prompt système et CHANGELOG des prompts, politique de
classification des fichiers, proxy, tests, documentation, décision #72,
BACKLOG, TODO et journaux.

**Raison** : définir l'identité de Nexxus et injecter son contexte par requête,
tout en préparant une politique d'accès aux fichiers sans activer leur lecture.

**Impact** : dix tests dédiés; la suite compte 215 tests. Un test d'intégration
du chat vérifie le nouveau prompt; aucun outil ou endpoint de lecture ajouté.

## [2026-10-31] Phase 14-PERSONA-NEXXUS-BIS — Ajustements après tests manuels

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : prompt et changelog système, tests du persona, décision
#72 amendée, BACKLOG et journaux.

**Raison** : interdire plus explicitement la flagornerie, préciser quand
recommander un professionnel et décrire l'API llamafile locale.

**Impact** : trois assertions ajoutées; la suite passe à 218 tests. Aucun code
métier ni outil de lecture de fichiers ajouté.

## [2026-10-31] Phase 14-POLISH-COMPTEURS — Synchronisation documentaire

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `AGENTS.md`, `CONTRIBUTING.md`,
`CONTRIBUTING.fr.md`, `RELEASE-NOTES.md`, `dev/docs/RUNBOOK-PROD.md`,
`dev/docs/ROADMAP.md` et les journaux.

**Raison** : aligner les compteurs actuels sur 218 tests, 72 décisions et dix
règles, sans modifier les chiffres des entrées historiques.

**Impact** : documentation seulement; les 218 tests ne sont pas modifiés.

## [2026-11-05] Phase 15-PACKAGING-PYINSTALLER-V1 — Exécutable Windows autonome

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : outils de chemins et packaging PyInstaller, lanceur,
bootstrap, chemins mémoire/modèle/proxy, tests de packaging, documentation,
décision #74, BACKLOG, TODO et journaux.

**Raison** : permettre le lancement de La Citadelle sous Windows sans Python
installé, avec téléchargement vérifié des assets au premier lancement et
stockage persistant dans le profil utilisateur.

**Impact** : build local `dist/release/LaCitadelle.exe` (10,3 Mo), cinq tests
nouveaux, suite complète à 226 tests. L'EXE reste ignoré par Git; aucune
release n'est créée et validation sur poste vierge reste en attente.

## [2026-11-05] Phase 15-PACKAGING-PYINSTALLER-BIS — Runtime Windows persistant

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/tools/lancer.py`,
`dev/tests/test_cross_platform.py`, README bilingue, RUNBOOK-PROD.md,
AGENTS.md, RELEASE-NOTES.md, décision #75, BACKLOG, TODO et journaux.

**Raison** : maintenir llamafile actif après l'arrêt du proxy PyInstaller et
conserver ses sorties dans un journal dédié.

**Impact** : deux tests ajoutés (228 tests au total); le proxy s'arrête sans
terminer le runtime. Build PyInstaller régénéré localement, EXE ignoré par Git
et non publié; validation manuelle Windows en attente.

## [2026-11-05] Phase 15-PACKAGING-TER — Console llamafile visible sous Windows

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/tools/lancer.py`,
`dev/tests/test_cross_platform.py`, RUNBOOK-PROD.md, AGENTS.md,
ARCHITECTURE.md, README et notes de release, décision #76, BACKLOG, TODO et
journaux.

**Raison** : supprimer le conflit entre `CREATE_NEW_CONSOLE` et la redirection
stdout/stderr qui rendait le terminal vide et faisait échouer llamafile.

**Impact** : trois tests Windows adaptés et T16 ajouté; 229 tests passent.
EXE PyInstaller régénéré localement, ignoré par Git et non publié; validation
manuelle sur Windows en attente.

## [2026-11-06] Phase 15-PACKAGING-TER-V3 — Sortie proxy visible dans l'EXE

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/tools/lancer.py`,
`dev/tests/test_cross_platform.py`, RUNBOOK-PROD.md, AGENTS.md, décision #77,
BACKLOG, TODO et journaux.

**Raison** : afficher dans la console PyInstaller le mot de passe admin émis
sur stdout par le proxy, sans modifier le forwarding du mode développement.

**Impact** : T17 ajouté sans modifier les 229 tests existants; 230 tests
passent. EXE régénéré localement, ignoré par Git et non publié; validation
manuelle par le Décideur en attente.

## [2026-11-05] Phase 14-FIX-MACOS-LAUNCH — Runtime llamafile persistant

**Commit** : identifiant consultable dans l'historique Git.

**Fichiers modifiés** : `dev/tools/lancer.py`,
`dev/tests/test_cross_platform.py`, RUNBOOK-PROD.md, AGENTS.md, décision #73,
BACKLOG, TODO et journaux.

**Raison** : corriger l'arrêt de llamafile après le premier message sur macOS
en remplaçant le shell avec `exec` et en isolant le runtime du terminal.

**Impact** : trois tests couvrent le lancement Unix et Windows; la suite
complète compte 221 tests. Archive régénérée, source-only et non publiée;
validation manuelle macOS en attente.
