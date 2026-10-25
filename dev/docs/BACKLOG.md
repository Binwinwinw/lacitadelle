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
(décision #33). Le CRUD admin (10B-3a à 10B-3e) est terminé (décisions
#35, #41, #42, #43, #44 et #45). Restent les logs (10B-4) et les
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

### 10B-3 — CRUD admin (découpé en 5 sous-lots)

**Statut** : terminé (décision #34; sous-lots 10B-3a à 10B-3e terminés).
**Décision actée** : 2026-10-24.
**Dépendances** : 10B-2 (admin read-only terminé).

#### 10B-3a — Créer un utilisateur

**Statut** : terminé (décision #35, 2026-10-24).
**Périmètre livré** : formulaire dans `admin.html`, route
`POST /api/admin/users` protégée par `require_admin`, validation du nom
d'utilisateur (3-30 caractères, alphanumérique ASCII et underscore,
unicité), mot de passe temporaire aléatoire de 16 caractères affiché une
seule fois, rôle `user` et `must_change_password=1` forcés. Le mot de passe
n'est pas inclus dans l'API de lecture des utilisateurs.

**Dépendances** : 10B-2.
**Tests** : création et hash, doublon, nom trop court/invalide,
authentification et autorisation admin, connexion temporaire et changement
forcé.

#### 10B-3b — Désactiver/réactiver

**Statut** : terminé (décision #41, 2026-10-24).
**Périmètre livré** : boutons « Désactiver » / « Réactiver » avec
confirmation simple; routes `POST /api/admin/users/{id}/deactivate` et
`POST /api/admin/users/{id}/activate` protégées par `require_admin`.
La désactivation est atomique avec la suppression des sessions
conversationnelles (les messages sont supprimés par cascade), puis révoque
les jetons d'authentification en mémoire. Le dernier admin actif et
l'auto-désactivation sont protégés. `is_active=0` bloque le login.

**Dépendances** : 10B-3a.
**Tests** : six tests couvrent les actions, les protections, l'invalidation
des jetons, le login bloqué et l'accès non-admin.

#### 10B-3c — Promouvoir/rétrograder

**Statut** : terminé (décision #43, 2026-10-24).
**Périmètre livré** : routes protégées pour promouvoir et rétrograder,
boutons et confirmations UI. La promotion d'un user actif transfère
atomiquement le rôle admin de l'appelant à la cible, maintenant exactement
un admin actif jusqu'à V3.2. La rétrogradation protège le dernier admin et
interdit l'auto-rétrogradation. Les sessions de connexion et conversations
du compte rétrogradé sont invalidées/supprimées; les conversations ne sont
pas restaurées à la réactivation.

**Dépendances** : 10B-3b.
**Tests** : six tests couvrent le transfert atomique, les cibles invalides,
la rétrogradation, les protections du dernier admin et de soi-même, et
l'accès non-admin.

#### 10B-3d — Supprimer un utilisateur

**Statut** : terminé (décision #44, 2026-10-24).
**Périmètre livré** : bouton « Supprimer » avec double confirmation
(confirmation puis saisie exacte du username); route
`POST /api/admin/users/{id}/delete` protégée par `require_admin`.

Protections serveur : impossible de supprimer le dernier admin actif ou de
se supprimer soi-même. Suppression physique de `users` dans une transaction;
la cascade FK supprime sessions, messages et préférences, puis les jetons
en mémoire sont révoqués. La table `metrics` n'existe pas dans le schéma
actuel; aucun backup applicatif n'est créé.

**Tests** : cinq tests couvrent suppression/cascade, dernier admin,
auto-suppression, non-admin et utilisateur absent.

**Dépendances** : 10B-3c.

#### 10B-3e — Reset du mot de passe par l'admin

**Statut** : terminé (décision #45, 2026-10-24).
**Périmètre livré** : route `POST /api/admin/users/{id}/reset-password`
protégée par `require_admin`, avec mot de passe aléatoire de 16 caractères,
hash scrypt et `must_change_password=1`. Les sessions d'authentification
existantes de la cible sont révoquées. L'interface affiche le mot de passe
temporaire une seule fois avec un bouton Copier; le reset est autorisé sur
son propre compte.

**Dépendances** : 10B-3d.
**Tests** : quatre tests couvrent reset/hash, self-reset, non-admin et
utilisateur absent, ainsi que le changement obligatoire à la connexion.

**Moment de traitement** : terminé; test manuel à effectuer par le décideur
après redémarrage de `lancer.bat`.

---

## Phase 10C — Auto-création d'un admin au démarrage

**Statut** : terminé (décision #40, 2026-10-24).
**Décision actée** : 2026-10-24.
**Dépendances** : aucune (indépendant de B-1).

**Périmètre livré** :

- `citadelle_memory.ensure_admin_exists()` vérifie l'existence d'un admin
  actif dans la base courante de façon transactionnelle. Si aucun n'existe,
  le helper crée `superadmin` actif avec `must_change_password=1`.
- `login_server.main()` appelle le helper après les migrations. Le mot de
  passe généré est affiché une fois dans la console; un admin actif existant
  produit seulement un message avec son username.
- En cas d'erreur de migration/création, le proxy affiche l'erreur et l'action
  manuelle sans retry et poursuit son démarrage.
- Aucun fichier de mot de passe ni option par variable d'environnement.
- Le cas d'un `superadmin` présent uniquement dans un backup reste non
  supporté.

**Tests** : quatre tests couvrent la création et son hash, l'admin actif
existant, l'admin inactif et les messages de démarrage/erreur.

**Moment de traitement** : terminé; test manuel par le décideur à effectuer
sur la base locale.

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
