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

**Statut** : terminé (décision de clôture #49).
**Décision actée** : 2026-10-23.  
**Dépendances** : aucune.
**Spec validée** : voir la décision #30 dans
[`.memory/decisions.md`](../../.memory/decisions.md).

**Avancement** : 10B-1 (préférences), 10B-1b (changement de mot de passe),
10B-2 (admin read-only), 10B-3a à 10B-3e (CRUD admin), 10B-4a/4b
(métriques et logs) et 10B-5 (indicateurs agrégés) sont terminés.
Décompte historique non revérifié en 11-POLISH-TER : 11 sous-lots 10B sont
nommés ci-dessous; les 8 autres du total historique de 19 ne sont pas
identifiables dans l'inventaire conservé.

La conception globale et la clôture du Mode B-1 sont consignées dans les
décisions #30 et #49.

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

**Moment de traitement** : terminé (voir décisions #1–#49).

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

### 10B-4 — Logs (découpé en deux sous-lots)

**Statut** : terminé (10B-4a et 10B-4b; décisions #47 et #48).
**Dépendances** : spécification Mode B-1 (décision #30); 10B-4b dépend de
10B-4a.

#### 10B-4a — Métadonnées d'inférence (backend)

**Statut** : terminé (décision #47, 2026-10-25).
**Périmètre livré** : table `inference_metrics`, migration idempotente V5 et
capture par le proxy de l'utilisateur/session, horodatage, durée, statut et
compteurs de tokens disponibles. Aucun prompt, réponse générée ou secret
n'est stocké. Aucun endpoint ni interface n'est ajouté dans ce sous-lot.

**Tests** : capture, association/filtrage par user, cascade utilisateur,
`session_id` mis à NULL et schéma sans colonnes de contenu; 135 tests passent.

#### 10B-4b — Route et onglet Logs

**Statut** : terminé (décision #48, 2026-10-25).
**Périmètre livré** : `GET /api/logs/tail?lines=50` relit le rôle du compte
actif, retourne les logs globaux aux admins et filtre les users par
`user_id`. Limite de 1 à 500 lignes, tri horodatage/id décroissant, réponse
sans prompt/réponse/secret. Onglet Logs admin et section « Mes logs » user,
tableau métadonnées et polling à cinq secondes seulement quand la page est
visible (et l'onglet admin sélectionné).
**Dépendances** : 10B-4a.
**Tests** : cinq tests couvrent auth, accès global admin, filtrage user,
limites de lignes, absence de contenu sensible et présence des tableaux.
140 tests passent; parcours navigateur intégré admin/polling vérifié.

### 10B-5 — Indicateurs agrégés

**Statut** : terminé (décision #49, 2026-10-25).
**Décision actée** : 2026-10-23 (conception Mode B-1, décision #30).
**Dépendances** : 10B-4b.
**Périmètre livré** : `GET /api/indicators` avec fenêtre 24 h, 7 jours ou
30 jours, filtrage admin/user, sept indicateurs agrégés et compte des sessions
d'authentification en mémoire non expirées. Débit tokens calculé uniquement
depuis les compteurs réellement reçus et durées positives; sinon indisponible.
Cartes KPI admin, tableau user, sélecteur de fenêtre et polling lorsque le
document est visible.
**Tests** : cinq tests couvrent authentification, agrégation, filtrage,
fenêtres, sessions actives, données vides et absence de champs sensibles.
145 tests passent.

**Conséquence** : Mode B-1 est terminé; Mode B-2 (changement de modèle) reste
une tranche indépendante.

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

**Test manuel** : non exécuté; en attente d'une base jetable. La procédure
isolée est documentée dans [`RUNBOOK.md`](./RUNBOOK.md). Ne pas utiliser la
base locale réelle pour ce test.

---

## Mode B-2 — Changement de modèle (admin)

**Statut** : Phase 11 complète (11a–11f, 11-POLISH et 11-POLISH-BIS-CORS;
décisions #50–#64). L'upload GGUF reste un GO séparé.
**Décision actée** : 2026-10-25.
**Dépendances** : Mode B-1 terminé (décision #49).

**Périmètre décidé** :

- Rendre le bouton « Changer de modèle » accessible uniquement aux admins,
  depuis la section admin de `/settings`. L'action utilise
  `POST /api/admin/model`, protégée selon le contrat V3.1.
- Stocker la configuration runtime dans SQLite, table `settings`; la clé
  `current_model_path` désigne le GGUF actif. Le launcher ne doit plus
  dépendre d'un chemin de modèle codé en dur.
- Conserver Qwen3-1.7B Q4_K_M comme modèle par défaut uniquement s'il existe
  et figure dans `settings.allowed_models`. `llamafile_config.json` reste le
  manifeste des assets d'installation, distinct de l'état runtime.
- La whitelist V1 est un tableau JSON de chemins GGUF absolus géré depuis
  `/settings`. Tout modèle hors liste est refusé; aucune dérogation ou essai
  non autorisé n'est proposé.
- Le catalogue de modèles testés, les empreintes et les avertissements de
  compatibilité de template/contexte restent hors de cette V1 et nécessitent
  un GO distinct.
- Tester le chargement avant application et faire un rollback immédiat si le
  test échoue. Ajouter un filet de sécurité au prochain démarrage si le
  modèle nouvellement sélectionné ne démarre pas.
- Conserver l'ancien modèle pour rollback; aucune suppression automatique
  après changement.
- Toute action est limitée à un admin actif, avec erreur claire et
  diagnostic de rollback ne contenant pas de secret.

**Sous-lots Phase 11** :

#### 11a — Migration settings + helpers

**Statut** : terminé (décision #51, 2026-10-25).
**Périmètre** :

- Table `settings(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT
  NOT NULL)` et migration `migrate_to_v6()` idempotente.
- Helpers `get_setting(key, default=None, db_path=None)` et
  `set_setting(key, value, db_path=None)` dans `citadelle_memory.py`;
  upsert de la valeur et de `updated_at`.
- `migrate_to_v6()` appelée depuis `init_db()` et au démarrage du proxy après
  V5.
- Quatre tests couvrent migration/init_db, idempotence, get/set, valeur par
  défaut et upsert; 149 tests passent.

**Dépendances** : aucune.

#### 11b — Route `POST /api/admin/model`

**Statut** : terminé (décision #52, 2026-10-25).
**Périmètre livré** :

- Route POST avec `require_admin` et body JSON `model_path`.
- Résoudre le chemin absolu et valider fichier existant, extension `.gguf`,
  type fichier régulier et taille supérieure à zéro.
- Enregistrer `current_model_path` via `set_setting`; retourner le chemin
  et sa taille, avec un message indiquant que le chargement est différé.
- Aucun hash/whitelist (lot 11e), test de chargement ou redémarrage (11d),
  ni interface (11c) dans ce lot.

**Tests** : cinq tests couvrent authentification/autorisation, chemin valide,
chemin absent, extension invalide et fichier vide; 154 tests passent.

**Dépendances** : 11a.

#### 11b-bis — Correctif `lancer.bat` (attente active + log stderr proxy)

**Statut** : terminé (décision #53, commit `b7903ca`).
**Périmètre** : attente active des ports 8080 (maximum 120 s) et 8081
(maximum 60 s) par sondes `curl`. Le stderr du proxy est redirigé vers
`dist/proxy.log`; stdout reste dans la console pour protéger l'affichage du
mot de passe auto-admin.
**Tests réels** : trois lancements réussis; `/v1/models` et `/login` ont
répondu HTTP 200.
**Diagnostic** : la cause initiale n'a pas été reproduite (llamafile prêt en
3,192 s, proxy manuel en 0,539 s). Le correctif est un garde-fou de
disponibilité et de diagnostic, pas la correction d'une cause prouvée.
**Dépendances** : 11b.

#### 11c — UI de changement (admin)

**Périmètre** :

- Ajouter à `/settings` une section admin-only via `/api/me`, avec consultation
  du chemin configuré via `GET /api/settings/model`.
- Enregistrer un chemin GGUF depuis un formulaire qui réutilise le POST JSON
  `/api/admin/model`; conserver la validation côté serveur.
- Afficher le résultat et préciser que le runtime ne prend pas le nouveau
  chemin en compte avant le test de chargement et le redémarrage de 11d.

**Tests** : trois tests HTTP couvrent la présence du formulaire, l'accès admin
au chemin configuré et les contrôles d'accès du POST existant.

**Consolidation 2026-10-28** : page `/admin/model` dédiée (11c v1; commits
`cedd1e5` et `2864b3c`) retirée manuellement par `4347c2f` (décision #56);
11c v2 dans `/settings` conservée. La décision #55 (page dédiée) est
explicitement retirée par la consolidation #56.
**Statut** : terminé (décision #54, commit `a79d6f3`; consolidation #56).
**Dépendances** : 11b.

#### 11d — Test de chargement + rollback immédiat

**Périmètre** :

- Lire `dist/.current_model` au démarrage, avec fallback sur le GGUF Qwen3
  par défaut quand le miroir est absent ou vide.
- Vérifier après la sonde de démarrage que `data[0].id` de `/v1/models`
  correspond au chemin attendu (normalisé ou basename).
- Conserver `previous_model_path` et le miroir fichier; en cas d'échec,
  restaurer la configuration précédente et demander un redémarrage manuel.
- Afficher dans `/settings` l'instruction de relancer `lancer.bat`; aucun
  reload assisté ni rollback automatique.

**Tests** : sept nouveaux tests couvrent les quatre cas du health check et
les trois cas de persistance/rollback manuel; 165 tests au total après la
consolidation 11d-ter/quater.

**Consolidation 11d-ter/quater** : validation d'existence du GGUF avant
llamafile (décision #58); isolation et test de non-régression de
`dist/.current_model` (décision #59).

**Statut** : terminé (décisions #57–#59; commit initial `7a13c19`).
**Dépendances** : 11b et 11c.

#### 11e — Whitelist configurable (V1)

**Périmètre** :

- Stocker `allowed_models` en JSON dans `settings`; l'absence de valeur
  équivaut à une liste vide.
- Restreindre `POST /api/admin/model` aux chemins GGUF autorisés, après la
  validation GGUF existante.
- Exposer la liste par GET et permettre aux admins de la gérer par POST et
  depuis `/settings`.
- Valider les fichiers ajoutés (existants, `.gguf`, non vides) et refuser
  toute sélection hors whitelist.

**Hors périmètre de cette V1** : catalogue `MODELES_COMPATIBLES.md` et
validation par nom de fichier ou empreinte; ils nécessitent un GO distinct.

**Tests** : six tests ajoutés; 171 tests au total.

**Statut** : terminé (décision #60, commit `4762646`).
**Dépendances** : 11d.

#### 11e-bis — Ordre des sections de /settings

**Périmètre** : placer « Modèles autorisés » avant « Changer de modèle » sans
modifier leur contenu ni leur comportement.

**Tests** : 171 tests existants passent; ordre HTML, IDs et JavaScript vérifiés.

**Statut** : terminé (décision #61, commit `80814a0`).
**Dépendances** : 11e.

#### 11f — E2E + filet au démarrage

**Périmètre** :

- `model_health.check_whitelist()` valide le modèle courant contre
  `settings.allowed_models` et refuse une liste absente ou vide.
- `lancer.bat` vérifie la whitelist avant llamafile; après rollback, il
  revérifie le chemin restauré et ne démarre le modèle par défaut que s'il
  existe et est autorisé.
- Le test E2E couvre le POST admin, la mise à jour SQLite et
  `dist/.current_model`, ainsi que le refus d'un modèle valide non autorisé.
- Les changements et rollbacks sont journalisés avec `[security]` dans
  `dist/proxy.log`.

**Tests** : cinq tests ajoutés (trois whitelist, deux E2E); 176 tests au total.

**Statut** : terminé (décision #62, commit `fd3fd79`).
**Dépendances** : 11d et 11e.

#### 11-POLISH — Dette documentaire et CORS

**Périmètre** : aligner les compteurs agents, supprimer le doublon 11c,
clarifier les erreurs GGUF/whitelist, documenter le reset admin temporaire
et vérifier la restriction CORS de llamafile. Le flag multi-origines a ensuite
été retiré en 11-POLISH-BIS-CORS car son en-tête de réponse était rejeté par
les navigateurs; le défaut `*` reste en place pour l'usage local via le proxy.

**Validation** : 176 tests; `--cors-origins` était reconnu par le runtime,
mais son résultat multi-origines n'était pas valide pour les navigateurs.

**Statut** : terminé (décision #63, commit `09524b5`).
**Dépendances** : Phase 11f.

#### 11-POLISH-BIS-CORS — Retour au CORS par défaut

**Périmètre** : supprimer la liste multi-origines invalide de
`lancer.bat`; le frontend utilise le proxy Python. La restriction locale a
ensuite été appliquée par #65 avec l'origine unique
`http://localhost:8081`.

**Validation** : 176 tests; démarrage réel vérifié après retrait du flag.

**Statut** : terminé (décisions #64 et #65; #64 commit `56e8e54`).
**Dépendances** : 11-POLISH.

#### 11-POLISH-BIS — Upload GGUF (bouton Parcourir)

**Statut** : à planifier (GO séparé, annoncé par la décision #63).
**Périmètre provisoire** : permettre à l'admin de sélectionner un GGUF local
avec un bouton « Parcourir ». Le stockage, la taille maximale et la validation
complémentaire restent à cadrer.
**Playwright E2E** : reporté à 11-POLISH-BIS; dépendance non installée.
**Dépendances** : whitelist configurable 11e.

---

## Tâches bloquées / à trancher

- **Nettoyage base locale** (`admin`/`user`, `phase6c-admin` sans mot de passe,
  `phase6c-chat`) : au moment de la mise en production.

### Concurrence serveur (P2)

**Statut** : reportée; le serveur actuel est mono-thread. Une requête lente
bloque les suivantes et le nombre d'utilisateurs simultanés n'est pas testé.
**Décision actée** : 2026-10-29 (décision #65).
**Dépendances** : mise en production et GO CONCURRENCE dédié.
**Périmètre** : `ThreadingHTTPServer`, SQLite WAL, sessions thread-safe et
tests de charge concurrents.
**Questions ouvertes** : capacité simultanée cible et limites à certifier.
**Moment de traitement** : après production, selon les retours utilisateurs.

## Phase RELEASE-UPDATE — Asset utilisateur v3-distribution

**Statut** : terminé le 2026-10-29 (décision #66).
**Dépendances** : dépôt à `e3a1082` et release GitHub `v3-distribution`.
**Périmètre livré** : asset `lacitadelle-distribution.zip` remplacé; archive
vérifiée à 219 243 octets, 82 entrées et SHA-256 concordant avec l'asset
publié.
**Questions ouvertes** : aucune pour cette mise à jour; une nouvelle release
versionnée reste à décider avant mise en production.
**Moment de traitement** : terminé; nouvelle version à publier sur décision du
décideur.
