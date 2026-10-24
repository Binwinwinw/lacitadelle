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
(décision #33). Le CRUD admin (10B-3) est découpé ci-dessous en cinq
sous-lots (décision #34). Restent également les logs (10B-4) et les
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

**Statut** : en cours (10B-3a terminé; 10B-3b à implémenter).
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

**Statut** : à implémenter.
**Périmètre** : bouton dans `admin.html`, routes
`POST /api/admin/users/{id}/deactivate` et
`POST /api/admin/users/{id}/activate` (avec `require_admin`). Tests (action
OK, cible soi-même → 403, cible dernier admin → 403).

**Dépendances** : 10B-3a.
**Questions ouvertes** :

- Peut-on désactiver le dernier admin actif ? (probablement non, cohérent
  avec 3d).
- Un user désactivé voit-il ses sessions invalidées ?

#### 10B-3c — Promouvoir/rétrograder

**Périmètre** : bouton dans `admin.html`, routes
`POST /api/admin/users/{id}/promote` et
`POST /api/admin/users/{id}/demote` (avec `require_admin`). Contrainte : un
seul admin actif (jusqu'à V3.2). Tests (promotion OK, rétrogradation OK si
un autre admin existe, tentative de créer un 2e admin → 400).

**Dépendances** : 10B-3b.
**Questions ouvertes** :

- Si on rétrograde le dernier admin, faut-il refuser ou promouvoir
  automatiquement un autre ?
- La contrainte « un seul admin actif » est-elle temporaire (V3.2) ou
  définitive ?

#### 10B-3d — Supprimer un utilisateur

**Périmètre** : bouton dans `admin.html`, route
`POST /api/admin/users/{id}/delete` (avec `require_admin`). Protections :

- Impossible de supprimer le dernier admin.
- Impossible de se supprimer soi-même.
- Message de confirmation côté UI.
- Suppression en cascade (sessions, messages, préférences, metrics) via
  `ON DELETE CASCADE`.

Tests (suppression OK, dernier admin → 403, autosuppression → 403, cascade
vérifiée).

**Dépendances** : 10B-3c.
**Questions ouvertes** :

- Suppression logique (`is_active=0`) ou physique (`DELETE`) ?
  - Soft : garde l'historique, mais complexifie les requêtes.
  - Physique : supprime tout, plus propre.
- Les messages d'un utilisateur supprimé sont-ils conservés ?

#### 10B-3e — Reset du mot de passe par l'admin

**Périmètre** : bouton dans `admin.html`, route
`POST /api/admin/users/{id}/reset-password` (avec `require_admin`). L'admin
génère un mot de passe temporaire (ou en choisit un) et force
`must_change_password=1`. Tests (reset OK, `must_change_password` forcé,
non-admin → 403).

**Dépendances** : 10B-3d.
**Questions ouvertes** :

- Le mot de passe est-il généré (aléatoire) ou choisi par l'admin ?
- L'affichage est-il unique (une seule fois) ou réaffichable ?
- Comment l'utilisateur est-il notifié (email, log) ?
  - Pas de mail dans le projet actuel → log ?

**Moment de traitement** : un sous-lot par GO, dans l'ordre 10B-3a à
10B-3e. Le sous-lot suivant ne commence qu'après validation du précédent.

---

## Phase 10C — Auto-création d'un admin au démarrage

**Statut** : à implémenter (décision #39).
**Décision actée** : 2026-10-24.
**Dépendances** : aucune (indépendant de B-1).

**Périmètre** :

- Dans `login_server.py` (`main()`), détecter si la base active contient au
  moins un admin actif.
- Si aucun admin actif n'existe, créer `superadmin` avec rôle admin, compte
  actif, changement de mot de passe obligatoire et mot de passe généré
  aléatoirement; afficher ce mot de passe une seule fois dans la console
  proxy avec une consigne explicite de le noter.
- Si un admin actif existe, afficher un message informatif indiquant son
  username seulement, sans mot de passe.
- Ne pas prendre en charge le cas d'une base active vide avec un
  `superadmin` présent uniquement dans un backup; la détection porte sur la
  base active.
- Tests à prévoir : auto-création, absence de doublon si admin actif déjà
  présent et contenu des messages affichés.

**Questions ouvertes** (à trancher pendant la Review d'implémentation) :

- Le mot de passe doit-il être enregistré dans un fichier en plus de son
  affichage en console ?
- Que faire si la création échoue (base corrompue, permissions) ?
- L'auto-création doit-elle être désactivable par variable d'environnement ?

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
