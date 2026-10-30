# TODO — La Citadelle

**Politique** : ce fichier contient uniquement les actions à mener. Toute
tâche terminée est supprimée ici; sa trace reste dans
`dev/docs/JOURNALDESMODIFS.md` et `dev/docs/JOURNALDEBORD.md`.

**Dernière mise à jour** : 2026-10-30.

## Actif

### Priorité P2

- [ ] Vérifier sur le serveur cible les ports TCP 80/443 et confirmer que
  8080, 8081 et 2019 ne sont pas exposés. — Propriétaire : Décideur.
- [ ] Planifier le GO CONCURRENCE après la mise en production; mesurer et
  accepter la capacité du serveur mono-thread avant d'élargir l'usage. —
  Propriétaire : Décideur.
- [ ] Planifier Playwright E2E et définir les scénarios à certifier. —
  Propriétaire : à planifier.
- [ ] Exécuter le test manuel 10C sur une base jetable, jamais sur la base
  réelle. — Propriétaire : Décideur.

### Priorité P3

- [ ] Prévoir un journal `[security]` dédié aux refus de rate limiting; les
  429 actuels apparaissent seulement dans le log d'accès `[proxy]`. —
  Propriétaire : IDE.
- [ ] Cadrer puis implémenter l'upload GGUF (stockage et taille maximale à
  définir). — Propriétaire : à planifier.
- [ ] Surveiller le port 9931 de llamafile et confirmer qu'il reste fermé
  depuis l'extérieur. — Propriétaire : Décideur.
- [ ] Tester login et chat dans un navigateur avec un compte réel de test. —
  Propriétaire : Décideur.
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
- [ ] Décider si le déploiement utilisera l'archive `v3-distribution`;
  si oui, régénérer et publier l'archive avec les changements Phase 12 avant
  de l'utiliser. — Propriétaire : Décideur.
