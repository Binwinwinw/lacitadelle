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
