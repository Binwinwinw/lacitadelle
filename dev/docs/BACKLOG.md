# Backlog — Tâches versionnées à venir

Plan de route daté des tâches validées pour La Citadelle. Pour le détail des
décisions : [`.memory/decisions.md`](../../.memory/decisions.md). Pour
l'historique par phase : [`ROADMAP.md`](./ROADMAP.md). Pour le pense-bête
immédiat, local et gitignoré : [`TODO.md`](../../TODO.md).

Chaque tâche comporte un statut, une date de décision, ses dépendances, son
périmètre, ses questions ouvertes et son moment de traitement. Ce backlog
public ne contient que les tâches validées; il ne remplace ni les décisions ni
le journal des phases.

---

## Mode B-1 — Page de réglages (user + admin)

**Statut** : à concevoir.  
**Décision actée** : 2026-10-23.  
**Dépendances** : aucune.

**Périmètre** :

- Ajouter un bouton « Réglages » dans le chat.
- Présenter des sections conditionnelles selon le rôle (`user` ou `admin`).
- Pour un user : changement de mot de passe et préférences d'affichage.
- Pour un admin : gestion des comptes, accès au changement de modèle B-2 et
  aux logs d'inférence avec indicateurs. Cette partie fusionne l'ancien B-3.
- Vérifier les autorisations côté serveur, pas uniquement dans l'interface.
- Afficher les logs et indicateurs selon le rôle :
  - admin : logs d'inférence globaux;
  - user : logs limités à ses propres sessions;
  - indicateurs : tokens/s, latence et sessions actives.

**Questions ouvertes** (à trancher en conception) :

- Quelles préférences user inclure exactement : thème, langue, taille de
  police et options liées aux sessions ?
- Utiliser SSE ou polling pour les logs ?
- Les vues admin (globales) et user (filtrées par session) partagent-elles le
  même affichage ?
- Persister les logs dans un fichier rotatif ou dans une table en base ?

**Moment de traitement** : à décider par le décideur.

---

## Mode B-2 — Changement de modèle (admin)

**Statut** : à concevoir.  
**Décision actée** : 2026-10-23.  
**Dépendances** : B-1 (page de réglages).

**Périmètre** :

- Rendre le bouton « Changer de modèle » accessible uniquement aux admins,
  depuis la page B-1.
- Rendre dynamique le chemin du modèle via une configuration éditable, avec
  un fallback vers Qwen3. Le chemin pourra être relatif (par exemple
  `models/mon-modele.gguf`) ou absolu.
- Conserver le comportement actuel : Qwen3-1.7B Q4_K_M reste le modèle par
  défaut et est téléchargé par `install.bat`.
- Établir une whitelist curée de 5 à 10 modèles testés dans
  `dev/docs/MODELES_COMPATIBLES.md`, à créer pendant B-2, et la référencer
  depuis la page de réglages.
- Autoriser l'essai d'un modèle hors whitelist avec un avertissement clair :
  « non testé, peut casser l'application ». Prévoir une dérogation avec cet
  avertissement.
- Avertir que l'incompatibilité peut concerner le template de chat, la taille
  du contexte ou la mémoire disponible.
- Permettre de tester le modèle avant de l'appliquer.
- **Rollback automatique obligatoire** : si le nouveau modèle ne charge pas,
  revenir au modèle précédent, le conserver (fichier local ou référence dans
  la configuration), notifier l'admin avec une erreur claire et conserver le
  log de l'échec.

**Questions ouvertes** (à trancher en conception) :

- Quel emplacement retenir pour la configuration éditable ?
- Comment valider un GGUF avant application, par exemple par chargement et
  test de génération ?
- Le rollback conserve-t-il l'ancien modèle en mémoire ou relance-t-il le
  serveur, et quel en est le coût ?
- Comment calculer et vérifier l'empreinte des modèles fournis par l'admin ?
- Comment détecter un template de chat incompatible par un test de génération
  réelle ?

**Moment de traitement** : à décider par le décideur, après B-1.

---

## Tâches bloquées / à trancher

- **Nettoyage base locale** (`admin`/`user`, `phase6c-admin` sans mot de passe,
  `phase6c-chat`) : au moment de la mise en production.
