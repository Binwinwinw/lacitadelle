# TODO — La Citadelle

**Politique** : ce fichier contient uniquement les actions à mener. Toute
tâche terminée est supprimée ici; sa trace reste dans
`dev/docs/JOURNALDESMODIFS.md` et `dev/docs/JOURNALDEBORD.md`.

**Dernière mise à jour** : 2026-11-08.

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
