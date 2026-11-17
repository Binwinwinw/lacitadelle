# TODO — La Citadelle

**Politique** : ce fichier contient uniquement les actions à mener. Toute
tâche terminée est supprimée ici; sa trace reste dans
`dev/docs/JOURNALDESMODIFS.md` et `dev/docs/JOURNALDEBORD.md`.

**Dernière mise à jour** : 2026-11-17.

## Actif

### Priorité P2

- [ ] Valider manuellement les wrappers et l'installation sur Windows, Linux
  et macOS avant la diffusion de l'archive multi-OS. Le correctif macOS
  `exec` + `start_new_session` est préparé; revalider trois messages
  consécutifs sur Mac. — Propriétaire : Décideur.
- [ ] Valider `dist/release/LaCitadelle.exe` sur un poste Windows sans Python;
  vérifier premier téléchargement, affichage du mot de passe admin dans la
  console, chat, parcours SmartScreen et que llamafile reste actif après Ctrl+C
  dans le proxy. Utiliser un profil de test ou sauvegarder les données avant
  tout nettoyage. —
  Propriétaire : Décideur.
- [ ] Vérifier sur le serveur cible les ports TCP 80/443 et confirmer que
  8080, 8081 et 2019 ne sont pas exposés. — Propriétaire : Décideur.
- [ ] Test manuel post-streaming : vérifier affichage progressif, arrêt du
  stream et neutralisation XSS pendant le stream. — Propriétaire : Décideur.
- [ ] Tester login et chat dans un navigateur avec un compte réel de test. —
  Propriétaire : Décideur.
- [ ] Re-tester manuellement le persona Nexxus V1.1 après les ajustements
  (anti-flagornerie, conseils pros, llamafile). — Propriétaire : Décideur.
- [ ] Validation manuelle post-Qwen3-4B : persona V1.3/V1.4, réponses structurées,
  pas d'URL  inventée, pas d'article de loi inventé. — Propriétaire : Décideur.
- [ ] Exécuter le test manuel 10C sur une base jetable, jamais sur la base
  réelle. — Propriétaire : Décideur.

### Priorité P3

- [ ] Cadrer puis implémenter l'upload GGUF (stockage et taille maximale à
  définir). — Propriétaire : à planifier.
- [ ] Surveiller le port 9931 de llamafile et confirmer qu'il reste fermé
  depuis l'extérieur. — Propriétaire : Décideur.
- [ ] Aligner le REPL (client CLI séparé) sur le persona Nexxus; son prompt
  actuel est distinct du persona web. — Propriétaire : à planifier.
- [ ] Avant tout nettoyage de la base de production, vérifier une sauvegarde
  restaurable et confirmer les données à conserver; clarifier aussi
  l'ancienne alerte de sessions/POST avant toute suppression. —
  Propriétaire : Décideur.

## En attente de validation Décideur

- [ ] Valider le premier démarrage sur une VM vierge hors réseau, avec le
  runtime llamafile et le GGUF déjà présents; `install.bat` nécessite encore
  le réseau si ces assets manquent. — Propriétaire : Décideur.
- [ ] Lancer MEP-TER après validation de la VM et de la checklist de l'hôte. —
  Propriétaire : Décideur.
- [ ] Publier manuellement la release GitHub `v3.1.0` avec l'EXE Windows et
  l'archive source-only après validation du Décideur. — Propriétaire :
  Décideur.

## Prochains GO planifiés (post-v3.0.0)

- [ ] **14-CONCURRENCE** : définir la charge cible, mesurer la capacité et
  choisir une stratégie serveur. — Propriétaire : à planifier.
- [ ] **14-PLAYWRIGHT-E2E** : implémenter et certifier les scénarios E2E
  documentés après publication de v3.0.0. — Propriétaire : à planifier.
- [ ] **14-SECURITY-LOG** : cadrer et ajouter un journal de sécurité dédié
  après publication de v3.0.0. — Propriétaire : IDE.
- [ ] **14-INSTALL-DOC-BIS** : documenter les notes macOS après validation
  manuelle par le Décideur. — Propriétaire : Décideur.
- [ ] **14-PERSONA-NEXXUS-V2** : implémenter les outils de lecture de fichiers
  avec la politique `security_files.py` (V1 = classification uniquement). —
  Propriétaire : à planifier.
- [ ] **16-CHAT-CONTEXT-STRATEGY** — MAX_CONTEXT_TOKENS + troncature par
  paire user/assistant. — Propriétaire : à planifier.

### Chat et modèles

- [ ] **16-FEATURE-MODEL-USE-V2** : redémarrage automatique du proxy
  et de llamafile après sélection d'un modèle; progression, détection
  d'échec et rollback. — Propriétaire : à planifier (après V1).
- [ ] **16-FEATURE-MODEL-DRIFT-DETECTION** : bandeau dans `/settings`
  si `current_model_path` (SQLite) diffère du modèle chargé dans
  llamafile (`/v1/models`). — Propriétaire : à planifier (après V1).
- [ ] **16-FEATURE-AUTO-MODEL-SELECTION** : détection du matériel au
  premier lancement et sélection Qwen3.5-9B si ≥ 8 Go VRAM, Qwen3-4B
  sinon. — Propriétaire : à planifier (V3, après UX).
- [ ] **16-FEATURE-RESPONSE-TIME** : validation manuelle de l'affichage
  discret de la durée sous chaque réponse du chat. — Propriétaire :
  Décideur.
- [ ] **16-FEATURE-ORCHESTRATION-LOG** : validation manuelle de la colonne
  et du filtre de modèle dans les logs admin. — Propriétaire : Décideur.
- [ ] **16-CHAT-RAG-LOCAL** : base de connaissances locale (upload
  documents, recherche BM25, injection dans le prompt). Objectif :
  fiabiliser les faits couverts indépendamment du knowledge cutoff.
  **Effort** : 2-3 jours. **Priorité** : basse.
  **Dépendances** : cadrer l'import et le stockage des documents.
  — Propriétaire : à planifier.
- [ ] **16-CHAT-WEB-ACCESS** (optionnel) : accès web contrôlé via API
  (DuckDuckGo, Légifrance, Wikipedia). Casse la promesse offline et
  doit être désactivé par défaut dans `/settings`.
  **Effort** : 1-2 jours. **Priorité** : basse.
  **Dépendances** : choisir le fournisseur/API; validation explicite du
  compromis avec la promesse offline.
  — Propriétaire : à planifier.

### Qualité et dette

- [ ] **16-FIX-SETTINGS-SCROLL** : validation manuelle du scroll vertical
  sur la liste des modèles autorisés et de la mise en page responsive
  sur écran large/mobile. — Propriétaire : Décideur.
- [ ] **16-FIX-WHITELIST-UX** : message précis pour les entrées
  invalides de la whitelist, au lieu de "Chaque modèle doit être un
  fichier GGUF existant". — Propriétaire : à planifier.
- [ ] **UX-Whitelist-Date** — Ajouter colonne « Date d'ajout »
  (informative) au tableau whitelist de l'application. Implémentation
  dans un GO séparé. Priorité : basse. Fichier cible probable :
  `dev/tools/web/admin.html` (tableau whitelist) + CSS. Pas de logique
  métier associée. — Propriétaire : à planifier.
- [ ] **16-FIX-FLAKY-TESTS** : identifier et corriger les tests
  intermittents (`test_migration_v3`, `test_api_messages`).
  — Propriétaire : à planifier.
- [ ] **16-REFACTOR-LOGIN-SERVER** : découper `login_server.py`
  (~2600 lignes) en modules auth, chat, admin, settings et static.
  — Propriétaire : à planifier (maintenabilité).
- [ ] **16-AGENTS-RULES-18** : formaliser dans AGENTS.md la règle
  selon laquelle tout GO qui modifie un fichier testé met à jour son
  test associé. **Effort** : 30 min. **Priorité** : moyenne.
  **Dépendances** : aucune.
  — Propriétaire : à planifier.

### Distribution et environnement

- [ ] **16-FIX-OTHER-PROJECTS-VENV** : recréer les `.venv` des autres
  projets (Nexxus Studio, etc.) avec Python 3.15, selon la procédure
  La Citadelle. — Propriétaire : Décideur.
- [ ] **16-DOC-RELEASE-NOTES** : documenter dans RELEASE-NOTES.md les
  changements majeurs (modèles testés, choix du défaut, migration
  Python, etc.). — Propriétaire : à planifier.
