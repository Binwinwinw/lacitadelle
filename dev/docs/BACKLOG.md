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

**Statut** : partiellement implémenté (spec validée).
**Décision actée** : 2026-10-23.  
**Dépendances** : aucune.
**Spec validée** : voir la décision #30 dans
[`.memory/decisions.md`](../../.memory/decisions.md).

**Avancement** : la tranche 10B-1 (préférences utilisateur) est terminée
(décision #31). La tranche 10B-2 (admin read-only) est terminée
(décision #33). Restent le CRUD admin (10B-3), les logs (10B-4) et les
indicateurs (10B-5).

La tranche 10B-1b (changement volontaire du mot de passe) est terminée
(décision #32). Les logs et les indicateurs restent hors de cette tranche.

**Périmètre** :

- La page `GET /settings` est accessible aux utilisateurs authentifiés, avec
  une entrée dans la sidebar après « Nouvelle session » et des sections
  conditionnelles selon le rôle.
- Le user peut changer son mot de passe via `/change-password` et régler le
  thème (sombre/clair) et la taille du texte (petite/normale/grande). Les
  préférences sont enregistrées par compte en SQLite. La langue reste le
  français; les options de pagination des sessions sont hors B-1.
- La section admin donne accès à la gestion complète des comptes selon
  `AUTH_CONTRACT.md` (V3.1), aux logs/indicateurs et à B-2. Les opérations
  admin restent protégées par les règles du contrat; B-1 n'implémente pas le
  changement de modèle.
- Les autorisations sont vérifiées côté serveur à chaque requête : 401 pour
  une session absente et 403 pour un user non-admin. Le rôle est revalidé en
  base. Le proxy reste sur loopback jusqu'aux protections V3.1 avant toute
  écoute réseau.
- Les logs sont rafraîchis par polling toutes les cinq secondes lorsque
  l'onglet est visible. Le proxy enregistre des événements d'inférence
  structurés (date, user/session, résultat, durée et compteurs disponibles),
  sans prompt, réponse générée, mot de passe ou cookie.
- La latence est mesurée autour de l'appel au modèle. Les tokens/s utilisent
  uniquement les compteurs d'usage effectivement renvoyés par l'API; sinon
  l'indicateur est indisponible, sans estimation. Les sessions actives sont
  les tokens d'authentification non expirés conservés en mémoire du proxy.
- Les événements et indicateurs sont persistés dans une table SQLite dédiée,
  filtrable par user/session. Ils suivent le cycle de vie de la base locale;
  aucun contenu de conversation n'est stocké.

**Questions tranchées** : les huit choix de conception sont consignés dans la
décision #30 de `.memory/decisions.md`.

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
