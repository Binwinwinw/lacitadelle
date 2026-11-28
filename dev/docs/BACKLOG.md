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
- À l'époque de cette décision, conserver l'ancien modèle Qwen3-1.7B Q4_K_M
  comme modèle par défaut uniquement s'il existe
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
**Playwright E2E** : plan documenté dans RUNBOOK-PROD.md; implémentation
reportée au GO dédié 14-PLAYWRIGHT-E2E après validation macOS et publication
de v3.0.0.
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
**Documentation** : limitation, risques et absence de seuil validé décrits
dans RUNBOOK-PROD.md et SECURITY.md.
**Moment de traitement** : GO 14-CONCURRENCE après définition de la charge
cible; ne pas annoncer de seuil avant mesure.

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


## Phase MEP — Préparation mise en production

**Statut** : préparation et validation locale MEP-BIS terminées
(décisions #67 à #69); aucun déploiement effectué.
**Décision actée** : 2026-10-30.
**Dépendances** : FQDN public, DNS, règles pare-feu, compte de service,
emplacement de sauvegarde et vérification opérationnelle du Caddyfile.
**Périmètre livré** : architecture cible, configuration Caddy, cookie
`Secure`, CSRF, rate limiting, sauvegardes SQLite, restauration et monitoring.
**Sécurité V3.1** : implémentée et validée par 186 tests (décision #68);
aucun cas ni assertion préexistant n'a été modifié.
**Validation runtime** : login local, cookie HTTP, CSRF absent/valide et
rate limit login vérifiés; 429 est consigné par le log d'accès `[proxy]`.
Le préfixe dédié `[security] rate limit` n'est pas émis par le serveur.
**Questions ouvertes** : domaine réel, gestionnaire de service Windows,
destination de sauvegarde, fournisseur d'uptime et acceptation de la charge
mono-thread initiale.
**Prochaine étape** : déploiement manuel par le décideur après validation
de l'hôte cible, du pare-feu et des contrôles derrière Caddy; dette P2
concurrence à arbitrer séparément.

## Phase 12-FIX-WHITELIST-CYCLE — Première installation

**Statut** : implémentation terminée le 2026-10-30 (décision #70);
194 tests verts, aucun déploiement.
**Dépendances** : assets llamafile-thin et GGUF intégrés déjà présents;
leur téléchargement par `install.bat` requiert toujours le réseau.
**Périmètre livré** : migration idempotente de whitelist avec SHA-256 du GGUF
intégré, démarrage initial sans chemin courant, refus explicite du rollback
automatique sans modèle précédent.
**Tests** : huit nouveaux tests; les 186 tests existants restent inchangés.
**Questions ouvertes** : validation de bout en bout sur VM vierge hors réseau.
**Prochaine étape** : GO MEP-TER après validation manuelle par le Décideur.

## Phase 13-CROSS-PLATFORM — Windows, Linux et macOS

**Statut** : implémentation et correctifs Linux terminés le 2026-10-31
(décision #71 amendée); 205 tests verts. Le test réel Linux est validé;
Windows reste à valider avant diffusion. Le test réel macOS a révélé que
llamafile s'arrêtait après le premier échange; voir le correctif Phase
14-FIX-MACOS-LAUNCH ci-dessous.
**Dépendances** : décision #66 (archive source-only) préservée; runtime
llamafile thin universel 0.10.6.
**Périmètre livré** : lanceur et installateur Python multiplateformes,
wrappers `.bat`/`.sh`/`.command`, destinations runtime par OS, archive source-only
et documentation mise à jour.
**Tests** : huit tests multiplateformes initiaux et trois tests correctifs;
les 194 tests préexistants passent.
**Correctifs BIS** : normalisation LF des wrappers dans l'archive, exécution
APE Unix via `sh -c` avec `shlex.join`, arguments `-m` avant `--server`.
**Questions ouvertes** : compatibilité réelle à valider sur Windows et macOS
par le Décideur.
**Prochaine étape** : exécuter les tests manuels Windows/macOS, puis
diffuser l'archive sur décision du Décideur.

### Phase 14-FIX-MACOS-LAUNCH — Processus llamafile persistant

**Statut** : correctif implémenté le 2026-11-05 (décision #73); 221 tests
verts. La validation manuelle sur Mac reste à effectuer.
**Cause** : fin du shell `sh -c` après le fork APE, suivie de l'arrêt par le
superviseur; le runtime n'était pas isolé des signaux du terminal.
**Correctif** : `exec` dans la commande shell Unix et
`start_new_session=True`; lancement direct Windows inchangé.
**Tests** : T11 vérifie `exec`, T12 la session isolée sur Darwin et T13 le
lancement Windows direct.
**Prochaine étape** : Décideur, tester trois messages consécutifs sur macOS
avec l'archive courante; ne pas publier avant validation.

### 13-CROSS-PLATFORM-TER — Documentation des leçons post-test Linux

**Statut** : terminée le 2026-10-31.
**Périmètre livré** : documenter les corrections CRLF, APE et ordre des
arguments dans les notes de release, le runbook et AGENTS.md; préserver les
dix règles structurelles.
**Tests** : aucun exécuté ni modifié; référence conservée à 205.
**Prochaine étape** : le Décideur met à jour la description GitHub de
`v3.0.0-rc1`; l'asset ZIP reste inchangé.

## Phase 14 — Documentation des dettes P2/P3

**Statut** : procédure documentée le 2026-10-31; aucun code ni test modifié.
**Playwright E2E** : plan dans RUNBOOK-PROD.md; implémentation à planifier
dans le GO 14-PLAYWRIGHT-E2E après publication de v3.0.0.
**Concurrence mono-thread (P2)** : limitation et absence de capacité mesurée
documentées; GO 14-CONCURRENCE à planifier après définition de la charge cible.
**Ports 80/443 (P2)** : vérification multi-OS documentée; le Décideur doit
l'exécuter sur l'hôte cible avant déploiement public.
**Log `[security]` dédié (P3)** : état actuel et données à protéger documentés;
GO 14-SECURITY-LOG à planifier après publication de v3.0.0.

## Phase 14-PERSONA-NEXXUS-V1 — Persona et politique fichiers

**Statut** : V1.1 implémentée le 2026-10-31 (décision #72 amendée); 218 tests
verts.
**Périmètre livré** : prompt système versionné, injection dynamique du modèle,
de la date, de l'utilisateur et de la session; classification de sécurité
préparatoire en trois niveaux.
**Tests** : dix tests dédiés pour V1; trois tests ajoutés pour les corrections
V1.1; un test d'intégration existant actualisé pour le prompt dynamique.
**Amendement V1.1** : ton sans flagornerie, recommandations professionnelles
cadrées et environnement API llamafile documenté.
**Non livré** : aucun outil ni endpoint de lecture de fichiers. L'ouverture
future devra ajouter confinement de chemins, protection des liens symboliques
et gestion des courses de validation/lecture.
**Prochaine étape** : validation manuelle du persona par le Décideur; V2
nécessite un GO séparé avant tout outil de lecture.

## Phase 15-PACKAGING-PYINSTALLER-V1 — Exécutable Windows autonome

**Statut** : build local produit le 2026-11-06 (décisions #74–#77);
230 tests verts. L'EXE reste un artefact local ignoré par Git; aucune release
n'est publiée.
**Périmètre livré** : PyInstaller one-file, premier lancement avec bootstrap
runtime/GGUF, données persistantes dans `%APPDATA%\LaCitadelle\`, ressources
embarquées et script de build non destructif.
**Tests** : cinq tests unitaires de chemins, deux tests BIS, un test TER et un
test TER-V3; les 229 tests antérieurs sont conservés.
**Correctif TER** : `CREATE_NEW_CONSOLE` est utilisé sans redirection stdout
ou stderr; llamafile affiche ses logs dans sa console dédiée et reste actif
après l'arrêt du proxy.
**Correctif TER-V3** : en mode EXE, stdout du proxy hérite de la console afin
d'y afficher le mot de passe admin initial; en mode développement, le pipe et
le thread de forwarding restent actifs.
**Questions ouvertes** : validation sur un Windows sans Python, comportement
SmartScreen, affichage réel des logs, arrêt manuel du runtime et éventuelle
signature numérique.
**Prochaine étape** : test manuel du binaire par le Décideur; ne pas diffuser
avant vérification du SHA-256 et arbitrage sur la signature.

## Phase 16-CHAT-MARKDOWN-V1 — Rendu Markdown des réponses

**Statut** : Marked et DOMPurify chargés depuis jsDelivr avec versions et SRI
épinglées; deux tests statiques ajoutés; tests visuels manuels à effectuer.
**Sécurité** : le HTML généré est assaini avec une allowlist avant insertion;
si les dépendances ne chargent pas, le chat affiche le texte brut.
**Limite** : le rendu Markdown requiert une connexion au CDN.

## Phase 16-CHAT-MARKDOWN-V2 — Vendorisation offline (backlog)

**Objectif** : supprimer la dépendance CDN en copiant Marked et DOMPurify dans
`dev/tools/web/vendor/`, avec intégrité locale.
**Moment de traitement** : quand la dépendance CDN devient un problème,
notamment pour une distribution EXE hors ligne.

## Phase 16 — Récapitulatif session 2026-11-09

**Statut** : Phase 16 (Chat + Persona) clôturée à V1.6.
**Commits livrés** : 3248427, 8e4d706, d45c9cb, 7e0a9fb, 8864537, e38bac7, 98203b4.

### Ce qui a été livré

1. Persona V1.5 (anti-affirmation juridique) + V1.6 (avertissement factuel + limites LLM).
2. Avertissement UI permanent : bandeau "Nexxus connaît les données jusqu'à ~2024" dans chat.html.
3. Vendorisation offline Marked + DOMPurify dans dev/tools/web/vendor/ (fix proxy vendor/).
4. Context strategy : MAX_CONTEXT_TOKENS=8000 remplace MAX_CONTEXT_MESSAGES=15.
5. Migration Qwen3-1.7B → Qwen3-4B (par défaut dans lancer.py).
6. Règles 12-17 documentées dans AGENTS.md.
7. Vérification port 9931 (non écouté, documenté dans RUNBOOK-PROD.md).

### Limites identifiées (importantes)

1. **Tous les LLM locaux ont un knowledge cutoff** (~2024 pour Qwen3-4B).
   Pas de "patch" possible : les connaissances sont distribuées dans les poids.
2. **Qwen3-4B hallucine sur les faits post-2024** (lois, chiffres, institutions)
   malgré V1.4/V1.5/V1.6. Limite intrinsèque du 4B.
3. **L'avertissement V1.6 fonctionne** (présent en fin de réponse), mais
   n'empêche pas les hallucinations factuelles.
4. **Solutions possibles** (hors périmètre Phase 16) :
   - RAG local (base de connaissances, upload documents)
   - Accès web contrôlé (casse la promesse offline)

### Dettes planifiées (voir TODO.md)

- 16-CHAT-RAG-LOCAL
- 16-CHAT-WEB-ACCESS (optionnel)
- 16-AGENTS-RULES-18

## Phase 16 — Clôture finale des livrables centraux; reports actifs

**Statut** : clôture finale le 2026-11-24 des livrables AIWorkflow, premier
incrément Fichiers Chat et audit SQL, avec la sélection V3.1 conservée
(décisions #127, #130–#132). Les tâches historiques modèles/UX non terminées
restent des reports actifs; elles ne sont pas déclarées closes ici. La suite
complète compte 331 tests.

**GO planifiés** (détails, dépendances et propriétaires : voir TODO.md) :

### Priorité haute (UX)

1. **16-FEATURE-MODEL-USE** — terminé; validation manuelle du Décideur le 2026-11-15.
2. **16-FIX-SETTINGS-SCROLL** — clôturé le 2026-11-24 : défilement général
   vérifié en session authentifiée à 1440×667 et 390×844; trois modèles et
   leurs actions sont accessibles. Aucun débordement horizontal ni contenu
   inaccessible observé; aucun défaut reproduit, aucun correctif nécessaire.
   Essai statique précédent concluant avec 60 entrées factices; le cas
   authentifié avec liste longue n’a pas été testé. Limite consignée dans les
   journaux.

### Priorité moyenne (qualité)

3. **16-FIX-WHITELIST-UX** — 1 h.
4. **16-FIX-FLAKY-TESTS** — clôturé le 2026-11-24 sans correctif. Résultats de
   la campagne du GO 16-FIX-FLAKY-TESTS précédent (aucune réexécution dans ce
   GO) : suite complète 338/338 en 85,71 s; campagne ciblée : 20 invocations
   (5 migration seule, 5 API seule, 5 migration→API, 5 API→migration), 120
   exécutions de cas, aucun échec. Aucun intermittent actuel reproduit; cela
   ne garantit pas
   l’absence générale d’intermittence. L’ancien WinError 10053 a été signalé
   sur `test_change_password_ok` et `test_post_message_no_auth`; l’analyse a
   établi le corps POST lu après les contrôles d’auth et le défaut a été corrigé
   en Phase 8b. Aucun symptôme intermittent précis n’a été retrouvé pour
   `test_migration_v3`; son historique Ruff B011 est distinct.
5. **16-FEATURE-MODEL-USE-V2** — 4-6 h.
6. **16-AGENTS-RULES-18** — 30 min.
- **BACKLOG-ARCH-008 — E2E analyse_md** — terminé le 2026-11-22 (GO
  16-ARCH-WORKFLOW-ANALYSE-MD-FULL-CTX). **Dépendances** : amélioration RAG
  livrée. **Périmètre** : vérifier les huit sections Architecture avec Ornith.
  **Résultat** : document complet (14 359 caractères), 8/8 titres avec le
  nouveau mode `analyse_md`. **Moment** : terminé.

### Priorité haute (architecture et retrieval)

7. **16-GRAPHIFY-POC** — KO, clôturé le 2026-11-18. Le backend LLM requis
   est absent et le réseau est interdit; Graphify n'est pas intégré.
8. **16-ARCH-WORKFLOW-DESIGN** — **SPEC FAITE** le 2026-11-18; voir
   [`ARCHITECTURE.md`](./ARCHITECTURE.md). Le moteur maison et SQLite FTS5
   remplacent Graphify. Dépendance au POC levée.
9. **16-ARCH-WORKFLOW-IMPL** — **LIVRÉ** : moteur, nœuds, workflows
   `analyse_md`/`analyse_pdf`/`analyse_sql`, API, UI admin et intégration chat.
   Commits : `6561b47`, `5df516e`, `fc0575e`, `a5273c2`, `d2e4ebf`,
   `916dc0a`.

**Suivis AIWorkflow validés** :

- **16-ARCH-WORKFLOW-UI-TESTS** — terminé le 2026-11-19 (commit `9c419f4`).
  **Dépendances** : intégration chat livrée (`916dc0a`). **Périmètre** : test
  Node natif de la détection `.md`/`.pdf`/`.sql` et test Python de présence
  des éléments HTML. **Résultat** : script Node et test pytest livrés sans
  dépendance `jsdom`.
- **16-ARCH-WORKFLOW-RAG-IMPROVE** — terminé le 2026-11-19 (commit `ebd5efe`).
  **Dépendances** : index FTS5 et workflow Markdown livrés (`6561b47`,
  `5df516e`). **Périmètre** : chunks par paragraphe, reranking BM25 avec
  bonus de pertinence, normalisation de pluriels irréguliers. **Résultat** :
  7 tests ajoutés (294 passés); E2E complet `analyse_md` est ensuite validé
  avec 8/8 titres dans BACKLOG-ARCH-008 (`2f4d34c`).
- **16-DOCS-CLEANUP-BIS** — terminé le 2026-11-24.
  **Dépendances** : résultats des GO UI-TESTS et RAG-IMPROVE.
  **Périmètre** : actualiser le décompte de tests du README après chaque GO
  et clore la normalisation documentaire AIWorkflow. **Résultat** : les
  documents AIWorkflow ont été normalisés; README ne publie pas de compteur de
  tests, et le nombre actuel est suivi dans AGENTS/ETAT-PROJET.

### Priorité basse (évolutions)

9. **16-FEATURE-MODEL-DRIFT-DETECTION** — 1-2 h.
10. **16-FEATURE-AUTO-MODEL-SELECTION** — 1-2 jours.
11. **16-CHAT-RAG-LOCAL** — 2-3 jours.
12. **16-CHAT-WEB-ACCESS** — 1-2 jours, optionnel.
13. **16-REFACTOR-LOGIN-SERVER** — 4-6 h.
14. **16-FIX-OTHER-PROJECTS-VENV** — 5-10 min par projet.
15. **16-DOC-RELEASE-NOTES** — 30 min.
16. **16-FEATURE-RESPONSE-TIME** — implémenté; validation manuelle restante.
17. **MODELE-NETTOYAGE** — validé le 2026-11-17; migration v10 à planifier.
    **Périmètre** : retirer qwen2.5-3b, Mistral-Nemo-12B et Gemma-2-9B de
    `allowed_models`; garder Ornith, Llama-3.1-8B, Qwen3.5-9B et les Qwen3
    non testés. **Dépendances** : migration v9 publiée.
    **Questions ouvertes** : aucune. **Moment** : GO séparé après validation.
    **Effort** : à estimer.

**Effort total estimé** : ~10-15 jours de travail pour les tâches historiques
listées, hors MODELE-NETTOYAGE, POC Graphify clos et AIWorkflow livré. Les
suivis AIWorkflow restent sans estimation.

### 16-FICHIERS-CHAT — premier incrément

**Statut** : terminé le 2026-11-24 (GO 25; commit `fd34e82`).
**Décisions actées** : 2026-11-24 (décisions #128 et #129).
**Dépendances** : [spécification fonctionnelle](./SPEC-FICHIERS-CHAT.md) et
validation des propositions techniques, terminées avant l’implémentation.
**Priorité** : haute.
**Périmètre** : un document Markdown `.md` par conversation, contenu textuel
conservé avec son propriétaire et la conversation; retrait documentaire et
suppression de conversation selon la spécification. AIWorkflow et les profils
métier restent distincts. Quatorze tests dédiés; `327 passed`.
**Questions ouvertes** : aucune dans ce premier incrément; les autres formats
restent des évolutions distinctes.
**Moment de traitement** : terminé dans le GO 25.

### Suites validées après clôture du périmètre

#### 16-FICHIERS-CHAT-LIVE-TEST

**Statut** : terminé le 2026-11-24 (GO 16-FICHIERS-CHAT-LIVE-TEST-BIS).
**Dépendances** : premier incrément `.md` livré (GO 25).
**Priorité** : haute; clôturée.
**Périmètre** : test manuel navigateur + modèle du téléversement, question,
suivi, rechargement et retrait.
**Résultat** : upload, résumé, reprise après rechargement, suivi, retrait,
isolation inter-comptes et limites vérifiés; test modèle réussi après
redémarrage du runtime.
**Questions ouvertes** : aucune pour le parcours testé.
**Moment de traitement** : terminé.

#### 16-AUDIT-SQL

**Statut** : terminé le 2026-11-24 (GO 16-AUDIT-SQL; commit `6e8ef08`).
**Dépendances** : diagnostic #60 et décision d’occultation de `content`.
**Priorité** : haute; clôturée.
**Périmètre** : migration v12, audit des suppressions document/session et
tests sur les sessions #62/#63.
**Résultat** : les deux suppressions sont journalisées avec les bons
`session_id` et `user_id` propriétaire. Aucun bug de ciblage n’a été reproduit;
l’origine historique de l’écart #60 reste indéterminée.
**Moment de traitement** : terminé; la DB a été restaurée au backup de départ.

#### 16-CLEANUP-DETTE

**Statut** : terminé le 2026-11-24 (GO 16-CLEANUP-DETTE).
**Dépendances** : aucune.
**Priorité** : moyenne.
**Résultat** : deux diagnostics Ruff observés dans `login_server.py` (SIM102,
SIM105) sont corrigés; le GO en anticipait quatre, mais deux autres diagnostics
n’ont pas été reproduits avec Ruff 0.17.5. `count_tokens` utilise tiktoken si
le modèle est reconnu, sinon conserve le fallback `len(text) // 4` documenté.
Les suppressions journalisent les identifiants sans contenu documentaire.
**Limites** : le fallback reste approximatif pour les modèles GGUF inconnus;
aucune règle de rétention des logs n’a été définie dans ce GO.
**Moment de traitement** : livré selon le périmètre du GO; limites consignées.

#### 16-MULTIFORMAT

**Statut** : arbitrages A/B (#135/#136), Windows-first (#137), découpage
C1–C4 (#138) et texte/contexte (#139) consignés. C1 peut être demandé sous
Windows par un GO distinct; C2–C4 restent à exécuter. C0b Linux/macOS est
reporté, sans résultat présumé; CSV/JSON attendent C0b et la clôture
multiformat POSIX reste bloquée. `.txt`/`.sql` peuvent être livrés POSIX après
validation propre sans attendre C0b (#139). L’upload du chat accepte toujours
`.md` seulement.
**Priorité** : à déterminer.
**Objectif** : faire évoluer le contrôle actuel « Joindre un .md » vers
« Joindre un fichier » uniquement lorsque les formats effectivement pris en
charge sont définis et vérifiés. Le bouton ne promettra pas une compatibilité
universelle.
**Références de reprise** : [spécification du premier incrément](./SPEC-FICHIERS-CHAT.md),
[décision #135](../../.memory/decisions.md#2026-11-25-arbitrage-fonctionnel-du-premier-palier-multiformat),
[décision #136](../../.memory/decisions.md#2026-11-25-arbitrage-des-conditions-techniques-multiformat),
[invariants #134](../../.memory/decisions.md#2026-11-24-cadrage-documentaire-du-chantier-16-multiformat) et
[OBJECTIF.md](./OBJECTIF.md#L64) comme contexte de la proposition V4 examinée,
non comme version cible acquise.
La spécification décrit le contrat actuel `.md`; l’allowlist approuvée dans
la décision #135 et les conditions techniques de #136 restent un périmètre
futur, pas une capacité déjà disponible.

**Faits observés au HEAD audité `ee990535e039135cc0065136a71e3e4028ae9310`** :

| Étape | Composant existant et comportement | Conséquence pour le chantier |
|---|---|---|
| Interface | [`chat.html`](../tools/web/chat.html#L40) présente un input `accept=".md,text/markdown"` et « Joindre un .md ». [`chat.js`](../tools/web/chat.js#L278) envoie un multipart à `/api/chat/upload`; le nom et l’indication d’extraits sont affichés en texte. | Aligner le libellé et l’acceptation UI sur la future allowlist réelle; le filtre du navigateur ne remplace pas la validation serveur. |
| Réception et accès | [`login_server.py`](../tools/login_server.py#L2249) parse un seul identifiant de session et un fichier et réduit le nom à un basename. [`handle_post_chat_upload`](../tools/login_server.py#L2334) authentifie, vérifie le rôle, exige `.md`, contrôle la propriété de la session et refuse un second document. `do_POST` limite le corps général à 1 MiB et l’upload à `MAX_MARKDOWN_BYTES + 16 384`; le fichier est ensuite plafonné à 256 KiB. CSRF et rate limit sont appliqués. | Étendre l’allowlist fermée et faire appliquer côté serveur les règles propres à chaque format, en conservant authentification, CSRF et isolation utilisateur/conversation. |
| Extraction et classification | [`extract_markdown_document`](../tools/nodes/extract_text.py#L21) seul est appelé par le téléversement : `.md`, UTF-8 strict, 256 KiB et 200 000 caractères. [`extract_text`](../tools/nodes/extract_text.py#L58) prend aussi `.txt` et `.pdf`, mais ce helper n’est pas branché à l’upload chat; PDF importe `pypdf` à la demande. [`security_files.py`](../tools/security_files.py#L15) classe aussi des extensions PDF, bureautiques et images. | Une classification d’extension ne constitue ni une allowlist d’upload ni un extracteur. Le constat `pypdf` concerne seulement le candidat PDF hors palier; ce helper TXT/PDF, pypdf et OCR ne sont pas des prérequis de l’étape B approuvée. |
| Workflows distincts | [`workflow_runner.py`](../tools/workflow_runner.py#L23) et `analyse_pdf`/`analyse_sql` reçoivent des chemins serveur autorisés; ce parcours admin n’est pas le téléversement du chat. | Ne pas compter les capacités AIWorkflow comme formats déjà supportés par « Joindre un fichier ». Le contenu SQL, scripts et macros ne sera pas exécuté. |
| Stockage et suppression | La migration v11 de [`citadelle_memory.py`](../tools/citadelle_memory.py#L455) conserve texte extrait et métadonnées par propriétaire/session; l’index unique limite à un document par conversation. L’original passe par un répertoire temporaire nettoyé; le retrait supprime le contenu extrait, pas les messages. | Cardinalité maintenue à un document actif par conversation (décision #136); préciser la politique applicable aux originaux, aux contenus extraits et aux données dérivées. |
| Contexte modèle et historique | [`handle_get_messages`](../tools/login_server.py#L2546) retourne les métadonnées du document, pas son contenu ni l’original. [`_build_document_context`](../tools/login_server.py#L2617) transmet jusqu’à 6 000 caractères, ou jusqu’à 12 passages FTS5 dans cette limite; le prompt marque le document comme donnée non fiable et interdit les appels d’outils sur sa demande. Le budget actuel est estimé à 8 000 tokens, avec jusqu’à 1 024 pour la réponse; ces estimations ne sont pas des limites multiformat validées. | Définir les sorties normalisées, les résultats partiels et leurs indications UI par format; conserver la séparation instructions/données et ne donner aucun pouvoir au document. |

**Décisions validées dans le GO 16-MULTIFORMAT-DOC** :

- Les documents servent à lire, résumer et analyser; leur contenu n’est jamais
  exécuté, ne modifie pas les instructions système et ne peut autoriser une
  action ou un outil.
- Le traitement reste local et confidentiel; aucun service externe ni
  récupération automatique de ressources réseau n’est autorisé.
- Les formats formeront une liste explicite et fermée, contrôlée côté serveur.
  Les limites, refus et traitements partiels seront visibles.
- Le libellé cible « Joindre un fichier » accompagne une prise en charge réelle
  et testée. Le GO documentaire du 2026-11-24 n’autorisait aucun nouveau format
  à l’implémentation; le périmètre futur a depuis été approuvé par la décision
  #135, sans rendre ces formats disponibles actuellement.

**Proposition fonctionnelle examinée avant arbitrage (GO 16-MULTIFORMAT-ARBITRAGE), non approuvée à cette date** :

| Candidat | Utilité et contenu accessible / lecture envisagée | Réutilisation établie, dépendances possibles et limites | Risques / recommandation |
|---|---|---|---|
| `.md` | Commenter, résumer, reformuler et questionner le texte Markdown; le modèle reçoit le texte ou des passages partiels selon le contrat courant. | Seul format du téléversement chat actuellement pris en charge; extraction UTF-8 stricte existante. | À préserver dans chaque option; aucune extension du comportement actuel n’est proposée ici. |
| `.txt` | Lire, résumer et questionner le texte brut. | Un helper générique sait lire `.txt` dans un autre parcours, sans être branché à l’upload chat. Encodage et extraction restent à définir; aucune nouvelle dépendance n’est présumée. | Premier palier recommandé; décider le traitement des encodages et erreurs au cadrage technique. |
| `.csv` | Interroger des données tabulaires; proposer une lecture structurée des en-têtes, lignes et cellules. | Aucun extracteur chat établi. La bibliothèque standard Python pourrait lire la syntaxe CSV, sans que ce soit un choix d’implémentation. | Premier palier recommandé sous réserve d’arbitrer la lecture structurée; délimiteurs, guillemets, encodage et volume sont des limites à cadrer. Les cellules restent des données, jamais des formules exécutées. |
| `.json` | Expliquer des objets, listes, clés et valeurs d’un document structuré. | Aucun extracteur chat établi. La bibliothèque standard Python sait analyser JSON, sans choix technique arrêté. | Premier palier recommandé sous réserve d’une lecture structurée; JSON invalide, imbrication profonde et volumes excessifs devront être traités explicitement. Aucun code n’est évalué. |
| `.sql` | Faire expliquer ou résumer un script de requêtes comme source textuelle. | Le workflow admin `analyse_sql` est un parcours distinct et n’est pas une capacité réutilisable d’upload chat. | Premier palier recommandé en texte seulement; aucune requête n’est analysée contre une DB ni exécutée. |
| Code et configuration : `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.html`, `.css`, `.sh`, `.bash`, `.bat`, `.ps1`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.xml` | Demander une explication du texte source ou de configuration; aucun résultat d’exécution. | Aucun parcours d’upload chat établi pour ces extensions; pas de parseur de format retenu. | Palier ultérieur séparé, pas une famille générique autorisée. Risques de secrets dans les configurations, contenu d’instructions non fiable et diversité syntaxique. `.env`, clés, certificats et binaires ne sont pas inclus dans cette liste candidate. |
| Nom `Dockerfile` | Expliquer le texte des instructions de construction. | Aucun extracteur chat établi; règle candidate : accepter uniquement un fichier dont le basename est exactement `Dockerfile`, sans extension. | Palier ultérieur séparé; jamais lancer `docker build` ni exécuter une instruction. Confirmer la règle de nom et sa portabilité avant de l’envisager. |
| PDF textuel | Résumer et questionner le texte réellement présent dans la couche texte du PDF. | Un helper distinct utilise `pypdf`, mais il n’est pas branché à l’upload chat; sa disponibilité comme dépendance du produit n’est pas établie. | Palier ultérieur conditionnel à la validation du parseur et de son isolation. PDF numérisé, OCR et extraction d’images sont exclus; fichiers chiffrés, malformés ou lourds exigent un traitement défini. |
| `.docx` | Lire et expliquer le texte des paragraphes et tableaux. | Aucun extracteur chat établi; une dépendance de parsing OOXML pourrait être nécessaire, à choisir à l’étape B. | Palier bureautique ultérieur; archives structurées, contenu embarqué et complexité du parseur augmentent les risques. Pas de macros, d’exécution ni de récupération externe. |
| `.xlsx` | Lire les feuilles, cellules, valeurs et formules comme contenu; les formules peuvent être expliquées comme texte. | Aucun extracteur chat établi; parsing de classeur potentiellement dépendant d’une bibliothèque, non choisie. | Palier bureautique ultérieur; ne pas recalculer les formules ni charger de liens externes. `.xlsm`, macros et objets actifs ne sont pas proposés. |
| `.odt` | Lire et expliquer le texte des paragraphes et tableaux. | Aucun extracteur chat établi; parsing ODF pourrait demander une dépendance, non choisie. | Palier bureautique ultérieur; archive structurée et contenu embarqué à traiter de façon isolée. Aucun objet, macro ou ressource externe n’est exécuté/récupéré. |

Cette matrice décrit des candidats et des profondeurs de lecture proposées,
pas des formats disponibles. Pour tout format, le contenu serait une donnée
locale non fiable; seules les données effectivement extraites et transmises
seraient accessibles au modèle. Une extraction ou un contexte partiel devrait
être signalé; aucune lecture exhaustive n’est promise. OCR, formats non
énumérés et exécution de code, macros, requêtes ou formules ne sont pas inclus.

**Options de premier palier examinées avant l’arbitrage du 2026-11-25** :

| Option | Allowlist exacte et usages proposés | Exclusions | Interface, dépendances et inconnues | Compromis |
|---|---|---|---|---|
| **A — recommandée, palier textuel structuré** | `.md`, `.txt`, `.csv`, `.json`, `.sql`. Texte pour Markdown/TXT/SQL; lecture tabulaire CSV et lecture de l’arbre JSON, sans évaluation. | PDF, OCR, bureautique, code/configuration, `Dockerfile`, images et toute extension non listée. | Le sélecteur futur et le serveur devraient annoncer la même liste fermée; erreurs de format et résultats partiels visibles. Le cadrage technique doit confirmer parsing, encodages, limites et isolation. Le helper TXT n’est pas une preuve de support chat. | Couvre documents et données textuelles courantes sans introduire les parseurs d’archives PDF/OOXML/ODF. Recommandée seulement si le Décideur accepte la distinction entre texte brut et lecture structurée CSV/JSON. |
| **B — alternative restreinte** | `.md`, `.txt`; les deux lus comme texte, selon les limites qui seront décidées. | CSV/JSON/SQL, PDF, bureautique, code/configuration, `Dockerfile`, images et OCR. | Interface simple et allowlist courte; il reste à arbitrer encodages TXT, extraction et limites. | Risque et surface fonctionnelle réduits; reporte l’analyse de données structurées et les documents bureautiques. |
| **C — alternative plus large, conditionnelle** | `.md`, `.txt`, `.csv`, `.json`, `.sql`, `.pdf`, `.docx`, `.xlsx`, `.odt`. PDF limité à sa couche texte; bureautique limitée au texte/tableaux/cellules définis ci-dessus. | OCR, images, code/configuration, `Dockerfile`, macros (`.docm`, `.xlsm`), contenus exécutables et formats non listés. | Chaque famille doit avoir un extracteur validé, des limites, une isolation et des tests propres; dépendances et gestion des archives à établir à l’étape B. L’interface ne pourrait annoncer ces formats qu’après vérification de leur parcours réel. | Permettrait davantage d’usages documentaires, mais réunit plusieurs familles et risques de parsing. Ne pas retenir si les dépendances, protections ou résultats partiels ne sont pas démontrables. |

**Recommandation formulée avant arbitrage** : l’option A était proposée comme
base de discussion, sans approbation à cette date. L’arbitrage du 2026-11-25
(décision #135) a retenu son allowlist et sa profondeur de lecture comme
périmètre fonctionnel futur.

Les options portent sur les formats, pas sur le nombre de pièces jointes. Le
comportement actuel est d’un document par conversation; la décision #136
maintient un document actif par conversation pour la première implémentation.

**Contexte de version examiné avant arbitrage** : [OBJECTIF.md](./OBJECTIF.md#L64)
présente V4 comme cible proposée pour les fichiers du chat; cette proposition
a été examinée, mais n’a pas été retenue comme rattachement acquis.
**Version cible actuelle** : à déterminer, conformément à la décision #135.

**Arbitrage du Décideur du 2026-11-25 — décision #135** :

1. **Option A retenue pour le premier palier futur** : `.md`, `.txt`, `.csv`,
   `.json`, `.sql`.
2. **Profondeur approuvée** : CSV/JSON lus structurellement; Markdown/TXT/SQL
   lus comme texte. Aucun contenu n’est exécuté; SQL est explicitement admis
   comme source textuelle seulement.
3. **Options B et C** : non retenues pour ce premier palier, sans interdiction
   définitive de les réexaminer.
4. **Version** : à déterminer; aucun rattachement V4 acquis.
5. **Exclusions de ce palier** : PDF, bureautique, fichiers de code/configuration
   autres que l’exception `.sql` (y compris `.py`), `Dockerfile`, images et OCR.

Ces formats sont approuvés pour une réalisation future, pas disponibles
actuellement dans l’upload chat. Le seul format actuellement pris en charge
reste `.md`.

**Arbitrage technique B du Décideur — décision #136** :

Les cinq recommandations du cadrage B ont reçu une réponse affirmative. `.sql`
reste réservé aux administrateurs; CSV utilise la première ligne logique non
vide comme en-tête et refuse les séparateurs ambigus; le mode sans en-tête est
hors du premier palier. JSON reste dans l’allowlist, sous condition de preuve
adverse du pré-scan avant `json.loads`. Le worker CSV/JSON est à valider en
premier sur les trois systèmes. Un document actif par conversation et le
nettoyage temporaire sont retenus, sans garantie de purge des sauvegardes,
messages déjà écrits ou pages SQLite libres. Les détails et conditions sont
consignés dans la [décision #136](../../.memory/decisions.md#2026-11-25-arbitrage-des-conditions-techniques-multiformat).

**Proposition technique B — arbitrée, non implémentée** :

Les constats ci-dessous proviennent d’une lecture ciblée des composants cités
au HEAD initial `b3da82ea5e32734953efc11c998a53ad91070f85`. La cartographie
antérieure au HEAD `ee990535e039135cc0065136a71e3e4028ae9310` reste historique;
aucun audit général ni test n’a été exécuté.

| Point et constat directement vérifié | Évolution proposée | Compatibilité à préserver | Preuve future |
|---|---|---|---|
| Réception : [`do_POST`](../tools/login_server.py#L3272) borne le corps chat à 272 KiB avant lecture, puis vérifie authentification, gate de changement de mot de passe, CSRF et rate limit; [`handle_post_chat_upload`](../tools/login_server.py#L2334) répète l’authentification, vérifie le rôle, la session propriétaire et le document déjà attaché. | Garder route, séquence de confiance et champs `session_id`/`file`; refuser tout élément multipart non prévu et dispatcher uniquement les cinq suffixes approuvés. Garder serveur comme autorité; l’UI et le MIME client ne décident pas du type. | `.md` conserve les codes/résultats existants; non-authentifié 401, CSRF 403, session non possédée 404, second document 409. | API isolée : chacun des droits, codes et limites; champ/fichier supplémentaire refusé. |
| Corps et nom : [`_parse_chat_upload`](../tools/login_server.py#L2249) parse le corps MIME complet; `_safe_chat_upload_filename` (même fichier, L2235) enlève les chemins et refuse nom vide, `.`/`..`, plus de 255 caractères, `:` et contrôles. Le parseur collecte une session et un fichier mais ignore les autres parts inconnues. | Exiger exactement deux parts `form-data`; suffixe final insensible à la casse sélectionne le parseur, nom complet conservé pour affichage. Les suffixes précédents ne changent pas le mode; `.py.txt` reste du texte `.txt`, jamais du code exécuté. MIME déclaré ignoré comme preuve de sécurité. | Maintenir l’assainissement du basename et la taille maximale du nom; ne jamais utiliser le nom comme chemin persistant. | Noms multi-suffixes, séparateurs Windows/Unix, absence/majuscules d’extension, contrôles et part MIME incohérente. |
| Extraction : `_extract_chat_upload` (même fichier, L2295) écrit dans `TemporaryDirectory` et nettoie succès/erreur; [`extract_markdown_document`](../tools/nodes/extract_text.py#L21) contrôle `.md`, classe, UTF-8 strict, 256 KiB, NUL/vide et 200 000 caractères. [`extract_text`](../tools/nodes/extract_text.py#L58) lit aussi TXT/PDF ailleurs, sans intégration chat ni ces mêmes limites. | Conserver le chemin `.md`; ajouter un dispatch chat spécifique aux formats du palier, sans reprendre le helper PDF/TXT comme preuve de support. Refuser entièrement un document invalide ou trop complexe; ne pas stocker de résultat d’extraction tronqué. | Pas de dépendance nouvelle recommandée : `csv` et `json` sont dans la bibliothèque standard. L’original demeure temporaire. | Tests unitaires d’extraction temporaires et tests API des erreurs/cleanups. |
| Classification : [`PUBLIC_EXTENSIONS`](../tools/security_files.py#L15) contient TXT/CSV/JSON/MD mais pas SQL; [`classify_file`](../tools/security_files.py#L60) classe par défaut un suffixe inconnu `SENSITIVE`, que [`can_read`](../tools/security_files.py#L96) réserve à `admin`. Les signatures ZIP/GZIP/BZIP sont aussi sensibles. | Décision #136 : `.sql` reste réservé aux administrateurs pour la première implémentation; toute ouverture aux comptes `user` exige une décision explicite. Rejeter les signatures binaires/archives dans l’extracteur. | Les droits restent par propriétaire/conversation; `admin` ne voit pas les documents d’autrui. Une classification ne prouve ni le type ni l’innocuité. | Matrice `user`/`admin` propriétaire/non-propriétaire, SQL et fichiers déguisés; archive refusée même si suffixe autorisé. |
| Stockage : [`migrate_to_v11`](../tools/citadelle_memory.py#L457) crée `conversation_documents(content TEXT, metadata JSON, user_id, session_id)` avec un index unique sur la session. `add/get/delete_conversation_document_for_user` (L941, L980, L1000) vérifient le propriétaire; suppression de conversation en cascade. | Décision #136 : garder un document actif par conversation. Le stockage de texte normalisé et de métadonnées dans les colonnes existantes reste une proposition; pas de migration de schéma décidée. | Garder le texte `.md` historique lisible et son comportement après rechargement; maintenir erreurs/ownership existants. | Régression de lecture des anciens documents; isolation et suppression active avec DB temporaire. |
| Suppression et sauvegardes : le trigger d’audit de [`citadelle_memory.py`](../tools/citadelle_memory.py#L494) conserve identifiants/métadonnées et `content_redacted=true`, pas le contenu. La sauvegarde `VACUUM INTO` lue dans `migrate_to_v3` précède la table v11; aucune politique générale de rétention des copies n’est établie dans les sources ciblées. | Décision #136 : conserver l’original en temporaire et le nettoyer après succès ou erreur; aucune purge n’est garantie pour sauvegardes, messages déjà écrits ou pages SQLite libres. | Les messages déjà écrits peuvent conserver des informations dérivées; ne pas promettre l’effacement absolu de backups. | Vérifier audit redacted, cascade et nettoyage temporaire; aucun test ne prétend prouver l’effacement de sauvegardes. |
| Contexte : [`_build_document_context`](../tools/login_server.py#L2617) transmet jusqu’à 6 000 caractères en entier; sinon FTS5 jusqu’à 12 passages et la limite totale. [`index_fts5`](../tools/nodes/index_fts5.py#L57) coupe par paragraphes en chunks de 500; `search_fts5` retourne contenu, chemin et metadata de chunk, mais le builder actuel conserve surtout le contenu. | Sérialiser CSV/JSON en segments auto-descriptifs (n° de ligne/colonne ou JSON Pointer) et ne retenir que des segments complets dans le budget; répéter le locator si un segment est divisé. Ne pas changer le comportement Markdown par défaut. | Maintenir budget actuel estimatif, recherche limitée au document courant, prompt « donnée non fiable » et absence d’outil. Le prompt seul ne constitue pas un contrôle d’autorisation. | Petit document complet; retrieval partiel avec locators; absence de mélange inter-documents; coverage générée par le serveur. |
| Interface : [`chat.html`](../tools/web/chat.html#L41) annonce `.md` seulement et « Joindre un .md ». [`chat.js`](../tools/web/chat.js#L76) affiche le nom avec `textContent`, marque les documents longs comme extraits, envoie multipart avec CSRF; [`renderMarkdown`](../tools/web/chat.js#L43) assainit les réponses via DOMPurify. | Après validation de chaque parcours, aligner `accept` sur les cinq suffixes et afficher le format, le séparateur détecté, l’en-tête retenu, les erreurs et la couverture partielle en texte sûr. Garder le libellé actuel jusqu’à ce que les cinq formats soient réellement vérifiés. | Aucun HTML extrait directement injecté; pas de route de téléchargement de l’original; l’UX Markdown reste fonctionnelle. | Tests DOM/UI et vérification navigateur après implémentation, pas dans ce GO. |
| Tests : [`test_chat_documents.py`](../tests/test_chat_documents.py) couvre déjà migration, Markdown, limites, CSRF, droits, retrait, nettoyage et HTML. [`api_test_context`](../tests/_helpers.py#L140) utilise une DB temporaire et un serveur loopback sur port éphémère. | Étendre les tests existants; toutes les DB/fichiers restent temporaires. Pas de fixture utilisant l’installation réelle. | Préserver la suite Markdown et ses fixtures; aucun test n’est lancé pendant le cadrage. | Plan de tests détaillé ci-dessous; validation manuelle multiplateforme requise avant release. |

#### Lecteurs et représentation proposés

| Format approuvé | Traitement proposé | Représentation normalisée | Erreurs/dépendances |
|---|---|---|---|
| `.md` | Garder `extract_markdown_document` et son contrat actuel; éviter de changer le BOM ou le texte stocké existant. | Texte Markdown courant. | UTF-8 strict, vide/NUL et limites actuelles; aucune dépendance nouvelle. |
| `.txt` | Lecteur chat dédié, pas le helper générique; décodage UTF-8 strict. | Texte brut, fins de ligne normalisées en LF. | Encodage invalide, vide/espaces seuls, NUL/contrôles refusés. |
| `.csv` | `csv.reader(..., strict=True)` de la bibliothèque standard, flux logique ligne par ligne. | Première ligne logique non vide comme en-tête selon #136; valeurs brutes indexées par colonne et enregistrement. Aucune conversion numérique/formule. | Virgule, point-virgule et tabulation candidats; séparation ambiguë refusée. Mode sans en-tête hors premier palier. Limite globale de champ `csv.field_size_limit` est process-wide, donc worker à valider en premier ou verrou/restauration à étudier. |
| `.json` | `json.loads` standard après pré-scan lexical borné; `object_pairs_hook` rejette clés dupliquées; `parse_constant` et parseur de nombres rejettent NaN/Infinity et valeurs non finies. | Ordre des listes et objets conservé; fragments annotés par JSON Pointer RFC 6901 (racine `""`, échappement `~0`/`~1`). Lexèmes numériques conservés en texte typé pour éviter de promettre des calculs/précision flottante. | JSON reste approuvé fonctionnellement, mais son implémentation dépend de tests adverses concluant que profondeur/nœuds sont bornés avant `json.loads`, avec chaînes et échappements. Aucun `eval`, schéma exécuté ou déréférencement externe. |
| `.sql` | Lecture UTF-8 textuelle sans analyse SQL. | Texte source inchangé, hormis normalisation de fins de ligne commune aux nouveaux formats. | Ne jamais ouvrir de base, exécuter une requête, traiter les imports/includes ou utiliser le workflow admin `analyse_sql`. Réservé aux administrateurs pour la première implémentation selon #136. |

Aucune ligne de `.csv` ou valeur JSON n’est convertie en calcul. Dans un CSV,
les cellules commençant par `=`, `+`, `-` ou `@` restent des chaînes de données;
elles ne sont ni ouvertes dans un tableur ni interprétées. Un fichier `.sql`
reste du texte même s’il contient des instructions valides.

#### Encodage, noms et validation commune proposés

- Conserver pour `.md` le décodage `utf-8` actuel. Pour les quatre nouveaux
  suffixes, UTF-8 strict seulement; autoriser un BOM UTF-8 initial et le retirer
  avant parsing. Aucun fallback Latin-1/Windows-1252/UTF-16 : l’encodage de
  remplacement peut modifier des valeurs silencieusement.
- Normaliser CRLF/CR en LF pour texte brut; passer les CSV à `csv.reader` avec
  gestion explicite des fins de ligne pour préserver les cellules multilignes.
- Rejeter NUL, caractères C0 autres que TAB/CR/LF, DEL et contrôles C1, y
  compris s’ils sont décodés depuis un JSON échappé. Refuser un texte brut vide
  ou seulement blanc. JSON `null`, `false`, `0` et chaîne vide restent des
  valeurs JSON syntaxiquement valides.
- Suffixe final autorisé, insensible à la casse; suffixe absent/hors allowlist
  refusé. Les points précédents d’un nom ne changent pas le parser : `code.py.txt`
  est un `.txt` affiché sous son nom complet et n’est jamais exécuté. Cette
  politique est par extension, pas une détection de langage dans du texte.
- Conserver `_safe_chat_upload_filename`: basename seulement, pas de chemin,
  limite actuelle 255 caractères, rejet `:`, contrôles et noms vides. Afficher
  le nom avec `textContent`. Le type MIME client est non fiable et ne sélectionne
  jamais le parser; suffixe + validation de format font foi.
- Refuser les signatures binaires et archives reconnues (ZIP/PK, GZIP, BZIP,
  PE/ELF/Mach-O) indépendamment du rôle. Pour le texte ordinaire, aucune signature
  ne prouve qu’un fichier est sûr; l’allowlist/UTF-8/contrôles ne remplace pas
  la validation serveur ni l’isolation.
- Rejeter les parts multipart supplémentaires. Le `Content-Length` maximal
  borne déjà le corps avant lecture, mais le parseur MIME courant matérialise
  le corps avant le comptage des parts : ce comptage seul n’est pas une borne
  mémoire préalable.

#### Contrat CSV proposé

- Délimiteurs candidats : virgule, point-virgule et tabulation. Détecter sur
  un échantillon borné (8 KiB proposés), valider les 20 premiers
  enregistrements logiques; retenir un seul séparateur cohérent, sinon refuser
  avec une erreur expliquant l’ambiguïté. `csv.Sniffer` est une heuristique,
  donc sa réponse n’est jamais acceptée sans validation de cohérence.
- Décision #136 : la première ligne logique non vide est l’en-tête. Le mode
  sans en-tête est hors du premier palier; ne pas l’inférer ni l’exposer comme
  option de ce palier.
- En-têtes dupliqués/vide : garder le texte source et l’ordinal (`colonne 1`,
  `colonne 2`); nommer une colonne sans texte `column_N` sans écraser sa valeur
  d’origine. Cellules multilignes prises en charge par le parseur strict.
- Lignes entièrement vides ignorées avec compteur; fichier sans en-tête ou
  données selon la règle retenue donne un état explicite. Pour longueur variable,
  distinguer cellule vide de cellule absente et conserver les cellules
  supplémentaires sous leur ordinal; ne rien tronquer ni décaler.
- La sortie délimite explicitement `header_row`, `row_number`, `column_index`,
  libellé original et valeur textuelle. Une ligne/cellule trop longue ou une
  syntaxe cassée fait échouer tout l’attachement, sans table partielle persistée.

#### Contrat JSON proposé

- Racine objet, tableau, chaîne, nombre, booléen ou `null`; le parser standard
  valide la syntaxe. Le pré-scan n’est qu’une garde de profondeur/nœuds et doit
  gérer chaînes et échappements; il ne remplace jamais `json.loads`.
- Refuser les clés dupliquées plutôt que laisser le comportement standard
  « dernière clé gagnante » perdre une valeur; refuser constantes non-JSON et
  nombres non finis. Préserver l’ordre des tableaux et des membres d’objet.
- Chaque fragment normalisé porte son JSON Pointer source; un objet/tableau
  est découpé par enfants complets, jamais par suppression silencieuse de clés.
  Les fragments longs sont segmentés en répétant le Pointer et l’index de
  segment. Si l’ensemble dépasse les limites, refuser le document, pas le
  réduire silencieusement.

#### Limites proposées et mécanismes applicables

| Limite | Valeur candidate / unité | Justification | Enforcement proposé | Dépassement et test |
|---|---|---|---|---|
| Corps HTTP upload | 272 KiB (256 KiB fichier + 16 KiB multipart), actuel | Réutilise la borne actuelle et laisse un budget fixe aux en-têtes MIME. | `do_POST` avant lecture du corps. | 413; tester exact et +1 octet. |
| Fichier brut | 256 KiB par fichier, actuel | Ne pas élargir le coût d’entrée qui borne déjà `.md`. | Avant écriture temporaire; le MIME doit rester borné à 272 KiB. | 413; tester exact et +1. |
| Parts/champs | exactement 2 parts utiles (`session_id`, un `file`), proposition | Une seule pièce par conversation est le contrat actuel; les champs cachés ne doivent pas être ignorés. | Comptage après parsing MIME; le plafond brut protège la taille avant parse. Un streaming MIME serait requis pour une limite pré-parse. | 400 pour champs/fichiers supplémentaires; fixtures multipart adverses. |
| Texte/normalisation | 200 000 caractères au plus, actuel `.md`, proposé pour chaque sortie | Conserve la limite existante et borne le texte persisté. | Contrôle du décodage et cap pendant sérialisation des formats structurés. | 413, attachement non créé; tester frontière et expansion CSV/JSON. |
| CSV | 5 000 lignes de données, 100 colonnes, 20 000 cellules total, champ 64 KiB, candidates | Cap de lignes séparé pour CSV à une colonne; cellules plafonnent les petits champs nombreux; fichier/input et sortie restent en plus bornés. | `field_size_limit` dans worker isolé; compter lignes/cellules pendant lecture. `csv.reader` construit chaque ligne avant son contrôle de largeur; l’input cap borne la pire ligne mais pas une RSS stricte. | 413; tester chacun des seuils et une ligne maximale. Valeurs à calibrer, non approuvées. |
| JSON | profondeur 64 et 20 000 nœuds, candidates; sortie ≤200 000 caractères | Évite récursion/objet excessif tout en laissant les structures courantes; calé sur les plafonds existants d’entrée/sortie, non mesuré. | Pré-scan lexical avant `json.loads`, puis hooks doublons/constants et cap de sérialisation. Un cap appliqué seulement après `json.loads` ne protège pas l’allocation préalable. | 413 pour complexité/taille, 400 pour syntaxe; tester 64/65 et 20 000/20 001. |
| Pages | Non applicable au premier palier | PDF est hors allowlist; aucun compteur de pages/parsing PDF requis. | Pas de lecteur PDF ni de pypdf dans l’étape B. | Vérifier le refus d’un fichier `.pdf`; aucun test d’extraction PDF. |
| Contexte modèle | 6 000 caractères, 12 passages, ~1 500 tokens; réponse ≤1 024, actuels | Compatibilité avec le chemin `.md`; tokenisation GGUF reste approximative. | Budget serveur actuel (8 000 tokens estimés total). Segments complets privilégiés; pas de coupe sans locator. | Refuser si question+document dépassent le budget; partial explicit si retrieval. Tests petit/grand. |
| Durée du parseur structuré | 5 s murales/worker, candidate non mesurée | Le fichier ≤256 KiB et le JSON ≤20k nœuds donnent un travail borné; 5 s est un objectif à vérifier sur l’OS matériel minimum, pas une mesure acquise. | Seulement un worker terminable permet un timeout dur; dans le `HTTPServer` courant, le parseur in-process n’est pas interruptible. | Arrêter worker et retourner une erreur visible (503 proposé); test avec worker volontairement bloquant. |
| Mémoire | Pas de seuil RSS portable proposé | Input/structures plafonnés ne donnent pas une borne mémoire exacte; Python amplifie objets/strings. | Aucune limite RSS cross-platform dans l’architecture/std-lib étudiée; mesurer le worker et décider éventuelle limite OS-spécifique. | Bloquant si une limite mémoire dure est exigée; ne pas annoncer un quota absent. |
| Simultanéité | 1 requête servie à la fois actuellement; rate-limit chat 30 POST/min/IP partagé | `HTTPServer` sérialise les handlers et un parsing long bloque les autres requêtes. | Préserver le rate-limit; si serveurs threadés/worker pool futurs, ajouter un sémaphore/queue bornée (pas existant). | Pas de test de charge dans ce GO; futur test de concurrence et absence d’état partagé. |
| Volume cumulé | Aucun quota par compte proposé | Le premier incrément ne borne que fichier/conversation; aucun plafond cumulé par utilisateur n’est documenté. | Toute limite de stockage globale demande un arbitrage; ne pas la déduire du plafond de fichier. | Décision nécessaire avant promesse de quota; test seulement après qu’un seuil soit choisi. |

#### Isolation, stockage et conservation proposés

`login_server.py` utilise actuellement un `HTTPServer` séquentiel : un parser
in-process long bloque le proxy; il n’existe pas de timeout parsing ni de
plafond RSS. Deux options ont été comparées; selon #136, valider d’abord le
worker CSV/JSON et son packaging. En cas d’échec, toute alternative sans délai
ni limite mémoire durs exige une décision explicite.

| Option | Avantage | Limite/portabilité |
|---|---|---|
| In-process, stdlib + petites bornes | Diff et packaging minimaux; pas de dépendance, fonctionne dans le serveur Python actuel. | Pas de timeout interruptible ni isolation mémoire; exceptions sont capturables, mais une boucle/pression mémoire bloque le service. |
| Worker process pour CSV/JSON | Parent peut imposer le délai mural proposé et terminer un worker bloqué; seuls bytes en entrée et texte/métadonnées bornés en sortie; aucune DB/route/network n’est nécessaire au worker. | Pas un sandbox ni un plafond RSS portable. Le mode `spawn` et le lancement PyInstaller one-file doivent être vérifiés Windows/Linux/macOS; `login_server.py` ne peut pas être passé comme script à l’EXE gelé. Un worker dédié n’existe pas encore. |

**Recommandation proposée, précisée par #136** : valider d’abord le worker
CSV/JSON et son packaging Windows/Linux/macOS. En cas d’échec, toute alternative
sans délai ni limite mémoire durs exige une décision explicite. Le texte
`.md`/`.txt`/`.sql` reste un décodage borné. Le worker n’est pas un sandbox et
ne garantit pas l’isolation réseau/fichiers; son code doit n’opérer que sur les
octets fournis.

| Élément | Proposition | Compatibilité/limite |
|---|---|---|
| Cardinalité | Garder un document actif par conversation (index unique actuel). | Décidée par #136; aucune migration ni remplacement implicite; réexaminer seulement si un besoin est validé. |
| Original | Toujours fichier temporaire, nettoyé succès/erreur. | Ne pas persister ni servir de route download. Nettoyage échoué est erreur explicite. |
| Dérivé | Garder texte normalisé complet dans `conversation_documents.content`; format/version/comptages dans `metadata` JSON. | Schéma v11 suffit pour ces champs; pas de migration prévue. Markdown sans nouveau parseur reste compatible. |
| Retrait/suppression | Supprimer la ligne active; préserver messages historiques. La suppression de session cascade comme aujourd’hui. | Audit v12+ stocke identifiants/métadonnées et `content_redacted`, pas le texte. Le snapshot `VACUUM INTO` observé concerne la migration V3 avant table v11; la politique des copies/sauvegardes manuelles et la purge des pages SQLite ne sont pas établies. Ne pas promettre l’effacement absolu de backups. |

#### Contrat serveur, interface et modèle proposé

- Garder `POST /api/chat/upload`, multipart et la réponse 201
  `{document_id,status,metadata}`; conserver `GET /api/sessions/{id}/messages`
  (métadonnées sans contenu) et `DELETE /api/chat/document/{id}`.
- Codes actuellement observés pour l’upload `.md` : 401 non-authentifié,
  403 CSRF/droit, 404 session absente ou non possédée, 409 document déjà
  présent, 413 corps/fichier/texte au-delà des limites, 415 type de contenu non
  multipart ou suffixe autre que `.md`, 400 multipart invalide ou contenu
  Markdown/UTF-8 invalide, 500 erreur de stockage/vérification interne.
- Codes proposés pour les nouveaux traitements : 400 syntaxe CSV/JSON invalide
  et 413 dépassement des limites propres à ces formats. Garder 415 pour un
  suffixe hors de la future allowlist est proposé, même si le handler actuel
  renvoie déjà 415 pour tout suffixe autre que `.md`. Un timeout de worker
  renverrait 503 si cette option est retenue; ce code n’est pas actuellement
  utilisé par l’upload.
- Métadonnées additionnelles proposées dans le JSON existant : `format`,
  `extraction_version`, `characters`, état extraction complet et seulement les
  compteurs non sensibles (CSV: délimiteur/rows/columns; JSON: root type/nodes).
  Pas de contenu dans l’API de messages.
- Extraction à l’upload tout-ou-rien; un fichier dépassant un cap n’est pas
  tronqué ni attaché. La partialité actuelle concerne le contexte d’une question,
  distincte de l’extraction.
- Contexte court = complet; retrieval long = passages structurés avec numéro de
  ligne/colonne ou JSON Pointer. [`_build_document_user_content`](../tools/login_server.py#L2658)
  garde le marqueur de donnée non fiable; ajouter un état serveur
  `document_context` (`complete|partial`, locators sélectionnés) à l’événement
  SSE, à la réponse non-stream et à l’historique.
- [`add_message`](../tools/citadelle_memory.py#L830) accepte déjà des metadata
  JSON; le chemin streaming de [`call_llamafile`](../tools/login_server.py#L2679)
  devra recevoir le contexte de la réponse au lieu de ne sauvegarder que le
  texte modèle. [`handle_get_messages`](../tools/login_server.py#L2546) expose
  les messages; proposer un champ additif document_context sans changer
  `role`/`content` ni rendre le contenu extrait accessible.
- L’UI de [`chat.js`](../tools/web/chat.js#L447) traite les événements SSE;
  afficher la couverture et les locators avec `textContent`, et préserver cette
  provenance après rechargement. Pas de migration de messages proposée puisque
  `messages.metadata` existe déjà; tester la sérialisation/désérialisation et
  les lignes historiques dont metadata est vide.
- Le client affiche le coverage/locators en `textContent`; ne pas dépendre de la
  réponse du modèle pour signaler la partialité. Conserver DOMPurify pour le
  Markdown assistant; ne jamais rendre directement le contenu extrait.
- CSV/JSON/SQL restent une donnée non fiable. Le préfixe de prompt existant est
  conservé, mais les droits sont vérifiés dans l’application; le document ne
  donne aucune permission, aucun outil n’est activé et aucune URL/include n’est
  chargée. OCR/PDF/bureautique n’entrent pas dans le worker ni le build.
- Le sélecteur futur annonce exactement les cinq extensions après que tous les
  parcours sont passés; label « Joindre un .md » conservé jusqu’à validation de
  la liste complète. Aucun changement UI dans ce GO.

#### Plan de changements et tests futurs

| Lot futur | Composants identifiés | Changements/test principaux | Ordre et garde |
|---|---|---|---|
| Fondations/validation | `login_server.py`, `extract_text.py`, `security_files.py`, `test_chat_documents.py` | suffixe/parts/noms, UTF-8/BOM/contrôles, caps, SQL role, refus archives; tests unitaires `tmp_path` et API loopback. | Avant tout parseur; bloquer si SQL permissions ne sont pas tranchées. |
| Texte | `extract_text.py`, `login_server.py`, tests existants | `.txt` et `.sql` via chemin chat, aucune exécution; conserver `.md`; limites/encodage/permissions. | Dépend de fondations; n’utilise pas le helper PDF générique. |
| CSV/JSON | extracteurs chat et tests existants; worker si approuvé | parsing strict, separators/header rule, duplicate keys, pre-scan JSON, normalized outputs, source locators et caps. | Bloquer le JSON si le pré-scan/limites pré-parse ne sont pas jugés fiables; calibrer worker sur Windows/Linux/macOS. |
| Stockage/contexte | `citadelle_memory.py`, `login_server.py`, `index_fts5.py`, `chat.js` | garder cardinalité; stocker métadonnées; segments/locators complets; metadata par message pour coverage partielle; compat ancien `.md`. | Schéma v11 semble suffire; migration seulement si validation prouve le besoin. |
| Interface/validation finale | `chat.html`, `chat.js`, docs utilisateurs et tests | affichage sûr, erreurs/partial explicites, allowlist UI=serveur; bouton renommé après validation réelle des cinq formats. | Couvre tests d’isolation, données malveillantes, absence exécution/réseau, rendu, suppression et tests manuels multiplateformes avant release. |

Les futurs tests s’exécutent uniquement avec `tmp_path`, DB temporaire et
loopback éphémère comme `api_test_context`; jamais sur la DB réelle. Ajouter
notamment: cinq succès formatés; refus `.py`/hors liste; `.SQL` case, extensions
multiples et sans suffixe; encodages/BOM/CRLF/NUL; SQL contenant `DROP` jamais
exécuté; CSV quoting/multilignes/headers dupliqués ou absents/lignes irrégulières/
formule-like; JSON tous types racine/doublons/NaN/profondeur/nœuds/escapes;
bornes exactes/+1, parser timeout, cleanup, auth/roles/CSRF/propriété, double
upload, retrait/cascade, anciennes lignes Markdown, retrieval avec locators,
partial visible, prompt injection et contenu non rendu en HTML.

#### Arbitrages B obtenus et conditions restant à satisfaire en C

Les cinq recommandations ont reçu une réponse affirmative et sont consignées
dans la [décision #136](../../.memory/decisions.md#2026-11-25-arbitrage-des-conditions-techniques-multiformat).
`.sql` reste admin-only; le contrat d’en-tête et les séparateurs CSV sont
tranchés; JSON reste dans l’allowlist; le worker CSV/JSON doit être validé en
premier; cardinalité et nettoyage temporaire sont fixés. La liste de formats
n’est pas réduite.

Avant de déclarer les traitements disponibles en C :
- démontrer par des tests adverses que le pré-scan JSON borne profondeur et
  nœuds avant `json.loads`, y compris chaînes et échappements; en cas d’échec,
  revenir à l’arbitrage sans retirer JSON silencieusement;
- valider le worker et son packaging Windows/Linux/macOS; si cela échoue,
  aucune approche sans délai/mémoire durs n’est acceptée sans nouvelle décision
  explicite du Décideur;
- mesurer le délai candidat de 5 s et les seuils CSV/JSON, qui restent des
  candidats non approuvés. Aucune limite mémoire portable n’est promise.

#### C0 — résultats

**Statut** : C0a Windows corrigé et validé par C0A-3. C0b Linux/macOS est
reporté (décision #137) jusqu'à disponibilité du projet sur ces plateformes;
aucun résultat POSIX n'est présumé. C0b reste un verrou pour CSV/JSON et la
clôture multiformat POSIX, mais ne bloque pas la livraison de `.txt`/`.sql`
après leur validation propre (#139). C1/C2 n'attendent pas C0b; C3/C4 peuvent
être développés sous Windows, mais leurs preuves multiplateformes restent
requises avant l’activation CSV/JSON. Les README n'annoncent pas de format non
vérifié.

**Fichiers créés** :

- [prototype `json_prescan_prototype.py`](../tools/json_prescan_prototype.py),
  isolé et non importé par le code de production;
- [tests `test_json_prescan_prototype.py`](../tests/test_json_prescan_prototype.py),
  58 cas ciblés, incluant le différentiel à graine fixe sur des octets
  structurels et l’identité de la copie embarquée;
- [sonde autonome `c0_multiformat_probe.py`](../tools/c0_multiformat_probe.py),
  bibliothèque standard seulement, sans dépôt requis.

Le script autonome embarque une copie du scanner pour pouvoir être transféré
seul; le test d’identité compare les définitions du scanner et de son chargeur
dans les deux fichiers. Les tests et la sonde utilisent des données
synthétiques/mémoire ou temporaires seulement : aucune DB, document utilisateur,
serveur ou réseau n’a été utilisé. Le worker n’est pas un sandbox.

**Référence C0A initiale** (Python du projet
`.\.venv\Scripts\python.exe -m pytest -q`) :

- avant modification : `338 passed in 92.40s (0:01:32)`, code de sortie 0;
- après ajout des tests : `375 passed in 96.36s (0:01:36)`, code de sortie 0;
- variation : +37 cas attendus dans `test_json_prescan_prototype.py`.

**Sonde Windows C0A initiale (historique, remplacée pour transfert)** :
commande
`.\.venv\Scripts\python.exe dev\tools\c0_multiformat_probe.py`.
Résultat initial `RÉUSSI`, code de sortie 0, durée 49.669 s. Machine rapportée :
Windows 11, Python 3.15.2, Intel64 Family 6 Model 158 Stepping 10, 12 cœurs
logiques, mémoire physique 63.94 GiB. SHA-256 source :
`7ff6277dec71132cc04c0ac865e7d8e37e7cab7b876c2a04a9874da08031900b`.

Tableau historique de la première sonde C0A; les résultats Windows actuels
sont consignés dans le complément C0A-2 ci-dessous.

| Vérification | Windows — résultat | Linux — résultat | macOS — résultat |
|---|---|---|---|
| Pré-scan JSON adverse | RÉUSSI; limites exactes/+1, chaînes/échappements, UTF-8, BOM, données après racine et propriété à graine fixe | En attente; à saisir dans le bloc de retour | En attente; à saisir dans le bloc de retour |
| Délai du worker bloqué | RÉUSSI; terminé à 5.024 s | En attente; observer spawn et arrêt | En attente; observer spawn et arrêt |
| Absence d’orphelins | RÉUSSI; aucun enfant restant | En attente; rapporter PID éventuel | En attente; rapporter PID éventuel |
| Échanges bornés | RÉUSSI; réponse normale bornée, réponse excessive refusée par le parent | En attente | En attente |
| Isolation des imports | RÉUSSI historiquement, non probant (voir C0A-2) | En attente | En attente |
| `csv.field_size_limit` | RÉUSSI; changement enfant sans effet sur le parent | En attente | En attente |
| Coût de démarrage | RÉUSSI; ping spawn médiane/max 0.206/0.244 s, sonde légère et non serveur | En attente | En attente |
| Mesures synthétiques | RÉUSSI; 9 scénarios × 20 exécutions, détails ci-dessous | En attente | En attente |
| Packaging figé | RÉUSSI; PyInstaller 6.22.3 one-file et smoke worker, code 0; aucun outil installé | Facultatif si PyInstaller est déjà présent | Facultatif si PyInstaller est déjà présent |

Mesures Windows. Les temps worker incluent création du processus et échange IPC;
les pics `tracemalloc` ne sont pas la mémoire résidente (RSS).

| Scénario | In-process médiane/max (ms) | Pic tracemalloc (B) | Worker médiane/max (ms) | Pic tracemalloc enfant (B) |
|---|---:|---:|---:|---:|
| CSV — 5 000 lignes, 1 colonne | 28.141 / 31.845 | 136 869 | 206.914 / 219.622 | 136 869 |
| CSV — 100 colonnes | 0.098 / 0.140 | 25 808 | 186.249 / 233.545 | 25 784 |
| CSV — 20 000 cellules | 4.445 / 6.436 | 219 439 | 184.506 / 200.326 | 219 439 |
| CSV — champ 64 KiB | 0.935 / 1.259 | 721 574 | 183.516 / 257.204 | 721 574 |
| CSV — fichier ~256 KiB | 2.878 / 3.272 | 1 662 806 | 183.699 / 193.574 | 1 662 806 |
| JSON — profondeur 64 | 0.117 / 0.276 | 5 029 | 180.988 / 213.249 | 4 997 |
| JSON — 20 000 nœuds | 41.596 / 53.755 | 1 351 167 | 220.816 / 255.767 | 1 351 298 |
| JSON — chaîne longue | 28.928 / 43.324 | 402 726 | 210.921 / 245.513 | 402 870 |
| JSON — fichier ~256 KiB | 40.625 / 58.923 | 526 906 | 218.568 / 242.832 | 527 147 |

Les limites 64, 20 000, 64 KiB et 256 KiB restent des valeurs candidates,
non des seuils approuvés. Ces mesures décrivent cette machine et ne promettent
aucune limite RSS portable.

**Sortie de retour C0A initiale (historique; ne pas transférer)** :

```text
C0A|status=RÉUSSI|mode=complet|system=Windows 11|python=3.15.2|python_path=<répertoire masqué>/python.exe|cpu=Intel64 Family 6 Model 158 Stepping 10, GenuineIntel|logical_cpus=12|ram_GiB=63.94|sha256=7ff6277dec71132cc04c0ac865e7d8e37e7cab7b876c2a04a9874da08031900b|checks=Pré-scan JSON adverse=OK,Worker spawn et protections=OK,Mesures synthétiques=OK|measures=csv_5000_lignes_1_colonne:in_ms=28.141/31.845,in_peak_B=136869,worker_ms=206.914/219.622,worker_peak_B=136869,csv_100_colonnes:in_ms=0.098/0.140,in_peak_B=25808,worker_ms=186.249/233.545,worker_peak_B=25784,csv_20000_cellules:in_ms=4.445/6.436,in_peak_B=219439,worker_ms=184.506/200.326,worker_peak_B=219439,csv_champ_64KiB:in_ms=0.935/1.259,in_peak_B=721574,worker_ms=183.516/257.204,worker_peak_B=721574,csv_proche_256KiB:in_ms=2.878/3.272,in_peak_B=1662806,worker_ms=183.699/193.574,worker_peak_B=1662806,json_profondeur_64:in_ms=0.117/0.276,in_peak_B=5029,worker_ms=180.988/213.249,worker_peak_B=4997,json_20000_noeuds:in_ms=41.596/53.755,in_peak_B=1351167,worker_ms=220.816/255.767,worker_peak_B=1351298,json_chaine_longue:in_ms=28.928/43.324,in_peak_B=402726,worker_ms=210.921/245.513,worker_peak_B=402870,json_proche_256KiB:in_ms=40.625/58.923,in_peak_B=526906,worker_ms=218.568/242.832,worker_peak_B=527147|orphans=none|duration_s=49.669
```

#### C0A-2 — corrections et preuve comparative d’isolation (Windows, 2026-11-26)

**Résultat** : la première sonde C0A-2 a signalé que son auto-vérification
classait encore le BOM simple comme invalide; ce cas de test de la sonde a été
corrigé. La sonde complète finale réussit, code 0, sans orphelin. Aucun
comportement du produit ne change.

- Référence avant modification : `375 passed in 96.67s`, code 0.
- Suite finale : `396 passed in 97.03s`, code 0, soit +21 tests.
- Tests ciblés : `58 passed`; le différentiel décrit ci-dessous couvre les
  octets structurels et scalaires, vérifie l’acceptation dans les deux sens et
  compare exactement les comptes.
- Ruff 0.17.5 : aucun problème sur les trois fichiers Python.
- Sonde : Windows 11, Python 3.15.2, Intel64 Family 6 Model 158 Stepping 10,
  12 cœurs logiques, 63.94 GiB; `RÉUSSI`, 187.684 s.
- SHA-256 du script exécuté par C0A-2 (historique) :
  `b748eb05e082ec4188ec3ea00013a92ba96e2fccc66711118b0cecd6babf0b7a`.

Le candidat de longueur maximale d’un littéral numérique est 1 000 caractères;
il n’est pas approuvé. Le pré-scan refuse la limite +1 et un entier de 5 000
chiffres avant tout appel à `json.loads`. Un BOM UTF-8 initial est retiré; le
double BOM est rejeté. `load_json_bounded` détecte aussi les clés dupliquées
après décodage, y compris les clés rendues identiques par un échappement.
Restent volontairement hors couverture, à traiter en C4 : validation des
caractères de contrôle obtenus par `\u0000` et `\u007f`, et rejet des
substituts isolés comme `\ud800`. Aucun de ces cas n’est implémenté ici.

**Comparaison d’isolation C0A-2 (historique)** — la sonde a créé dans son répertoire temporaire
un faux module principal important `sqlite3` et `http.server` au niveau
supérieur. Les modules cités sont ceux présents dans l’enfant parmi les
imports sondés; les temps sont une seule exécution par architecture et ne
constituent pas les mesures comparatives à cinq essais de C0A-3.

| Architecture | Modules sondés présents dans l’enfant | Démarrage mesuré | Observation |
|---|---|---:|---|
| `spawn`, source | `__main__`, `__mp_main__`, `light_worker`, `sqlite3`, `http.server` | 209.684 ms | Le démarrage réimporte le module principal et ses imports lourds. |
| `subprocess`, source | `__main__` seulement; 62 modules au total | 118.094 ms | Le module worker dédié n’importe ni `sqlite3` ni `http.server`. |
| `spawn`, PyInstaller one-file | `__main__`, `__mp_main__`, `light_worker`, `sqlite3`, `http.server` | 947.590 ms | Les imports du faux principal sont présents dans l’enfant figé. |
| `subprocess`, PyInstaller one-file | `__main__` seulement | 1 802.097 ms | Le worker figé dédié n’importe pas les deux modules du principal. |

PyInstaller 6.22.3 était déjà installé. Les deux exécutables one-file ont été
construits dans le répertoire temporaire de la sonde, puis exécutés; aucun
outil n’a été installé. Ces observations comparent les deux architectures,
sans en choisir une.

Mesures sur 16 scénarios; la première exécution de chaque cas a été écartée,
puis 20 exécutions ont été mesurées. Le temps worker inclut démarrage du
processus et échange IPC; `tracemalloc` mesure les allocations Python et ne
représente pas la mémoire résidente (RSS).

| Scénario | In-process médiane/max (ms) | Pic (B) | Worker médiane/max (ms) | Pic enfant (B) | Résultat |
|---|---:|---:|---:|---:|---|
| CSV — 5 000 lignes, 1 colonne | 32.065 / 40.731 | 136 869 | 231.219 / 265.025 | 136 869 | Accepté |
| CSV — 100 colonnes | 0.093 / 0.188 | 25 784 | 205.473 / 238.099 | 25 784 | Accepté |
| CSV — 20 000 cellules | 5.068 / 8.250 | 219 439 | 195.612 / 231.978 | 219 439 | Accepté |
| CSV — champ 64 KiB | 0.639 / 1.015 | 721 574 | 198.833 / 299.041 | 721 574 | Accepté |
| CSV — fichier ~256 KiB | 2.748 / 3.064 | 1 662 806 | 198.947 / 219.555 | 1 662 806 | Accepté |
| CSV — 256 KiB de virgules, une ligne | 26.600 / 35.690 | 8 037 660 | 224.125 / 259.228 | 8 037 660 | Accepté |
| CSV — 131 000 lignes d’un caractère | 690.332 / 905.170 | 1 327 348 | 848.662 / 977.061 | 1 327 348 | Accepté |
| CSV — champ cité multiligne 256 KiB | 58.060 / 75.572 | 1 835 947 | 274.967 / 352.440 | 1 835 947 | Rejet `csv.Error` |
| CSV — 100 colonnes × 300 lignes | 9.589 / 11.534 | 319 444 | 226.348 / 260.849 | 319 444 | Accepté |
| JSON — profondeur 64 | 0.119 / 0.157 | 5 002 | 203.743 / 283.111 | 6 677 | Accepté |
| JSON — 20 000 nœuds | 47.313 / 58.227 | 1 351 490 | 273.320 / 465.876 | 1 353 874 | Accepté |
| JSON — chaîne longue | 36.280 / 51.431 | 402 914 | 239.530 / 290.545 | 403 206 | Accepté |
| JSON — fichier ~256 KiB | 40.148 / 52.889 | 527 238 | 235.361 / 301.655 | 527 483 | Accepté |
| JSON — 20 000 flottants | 189.364 / 246.251 | 84 342 | 416.873 / 485.144 | 84 454 | Rejet `JsonPreScanError` |
| JSON — 20 000 objets à clés longues | 129.638 / 151.291 | 264 344 | 345.273 / 379.556 | 264 456 | Rejet `JsonPreScanError` |
| JSON — 128 000 scalaires, rejet au nœud 20 001 | 185.423 / 222.645 | 260 342 | 364.188 / 427.265 | 260 454 | Rejet `JsonPreScanError` |

Ces mesures décrivent cette machine uniquement. Les seuils de profondeur 64,
20 000 nœuds, champ 64 KiB, fichier 256 KiB, littéral numérique 1 000 et délai
5 s restent des candidats non approuvés; aucune limite mémoire portable n’est
établie. Le worker n’est pas un sandbox.

**Sortie finale à copier — sonde C0A-2 (Windows)** :

```text
C0A|status=RÉUSSI|mode=complet|system=Windows 11|python=3.15.2|python_path=<répertoire masqué>/python.exe|python_supported=true|cpu=Intel64 Family 6 Model 158 Stepping 10, GenuineIntel|logical_cpus=12|ram_GiB=63.94|sha256=b748eb05e082ec4188ec3ea00013a92ba96e2fccc66711118b0cecd6babf0b7a|checks=Pré-scan JSON adverse=OK,Worker spawn et protections=OK,Isolation spawn source=OK,Isolation subprocess source=OK,Isolation PyInstaller=OK,Mesures synthétiques=OK|measures=csv_5000_lignes_1_colonne:outcome=accepted,in_ms=32.065/40.731,in_peak_B=136869,worker_ms=231.219/265.025,worker_peak_B=136869,csv_100_colonnes:outcome=accepted,in_ms=0.093/0.188,in_peak_B=25784,worker_ms=205.473/238.099,worker_peak_B=25784,csv_20000_cellules:outcome=accepted,in_ms=5.068/8.250,in_peak_B=219439,worker_ms=195.612/231.978,worker_peak_B=219439,csv_champ_64KiB:outcome=accepted,in_ms=0.639/1.015,in_peak_B=721574,worker_ms=198.833/299.041,worker_peak_B=721574,csv_proche_256KiB:outcome=accepted,in_ms=2.748/3.064,in_peak_B=1662806,worker_ms=198.947/219.555,worker_peak_B=1662806,csv_virgules_256KiB_une_ligne:outcome=accepted,in_ms=26.600/35.690,in_peak_B=8037660,worker_ms=224.125/259.228,worker_peak_B=8037660,csv_131000_lignes_un_caractere:outcome=accepted,in_ms=690.332/905.170,in_peak_B=1327348,worker_ms=848.662/977.061,worker_peak_B=1327348,csv_champ_multiligne_256KiB_rejete:outcome=rejected_Error,in_ms=58.060/75.572,in_peak_B=1835947,worker_ms=274.967/352.440,worker_peak_B=1835947,csv_100_colonnes_300_lignes:outcome=accepted,in_ms=9.589/11.534,in_peak_B=319444,worker_ms=226.348/260.849,worker_peak_B=319444,json_profondeur_64:outcome=accepted,in_ms=0.119/0.157,in_peak_B=5002,worker_ms=203.743/283.111,worker_peak_B=6677,json_20000_noeuds:outcome=accepted,in_ms=47.313/58.227,in_peak_B=1351490,worker_ms=273.320/465.876,worker_peak_B=1353874,json_chaine_longue:outcome=accepted,in_ms=36.280/51.431,in_peak_B=402914,worker_ms=239.530/290.545,worker_peak_B=403206,json_proche_256KiB:outcome=accepted,in_ms=40.148/52.889,in_peak_B=527238,worker_ms=235.361/301.655,worker_peak_B=527483,json_20000_flottants_rejete:outcome=rejected_JsonPreScanError,in_ms=189.364/246.251,in_peak_B=84342,worker_ms=416.873/485.144,worker_peak_B=84454,json_20000_objets_cles_longues_rejete:outcome=rejected_JsonPreScanError,in_ms=129.638/151.291,in_peak_B=264344,worker_ms=345.273/379.556,worker_peak_B=264456,json_128000_scalaires_rejete_20001:outcome=rejected_JsonPreScanError,in_ms=185.423/222.645,in_peak_B=260342,worker_ms=364.188/427.265,worker_peak_B=260454|orphans=none|duration_s=187.684
```

#### C0A-3 — corrections ciblées et validation Windows (2026-11-27)

Le différentiel déterministe couvre les octets JSON structurels et scalaires;
les valeurs non finies et les clés dupliquées sont rejetées côté référence.
L’acceptation est vérifiée dans les deux sens et les comptes de nœuds/profondeur
sont comparés exactement. Le nombre de tests reste inchangé : 58 ciblés et
396 dans la suite complète.

- Suite complète : `396 passed in 114.25s`, code 0.
- Tests ciblés : `58 passed`, code 0; Ruff ne signale aucun problème sur les
  trois fichiers Python.
- Sonde Windows complète : `RÉUSSI`, code 0, `291.472 s`, aucun orphelin.
- SHA-256 actuel de la sonde à transférer :
  `9251e6a6742a161031a7956652c56c3715a194c93a02b55c2e0ac8d0b1d8e169`.
- Le ping spawn mesure une sonde légère, pas le serveur : médiane/max
  `0.237/0.365 s`.

| Comparaison | Démarrage médiane/max (ms, 5 mesures) | Résultat attendu |
|---|---:|---|
| Spawn source | 239.609 / 252.539 | Non isolé |
| Subprocess source | 97.900 / 136.836 | Isolé |
| Spawn PyInstaller figé | 1 136.476 / 1 257.691 | Non isolé |
| Subprocess PyInstaller figé | 1 027.486 / 2 107.919 | Isolé |

Sous Linux/macOS, le contrôle PyInstaller est `SKIP` par défaut et ne change
pas le succès global. `--frozen` l’active explicitement; sous Windows, le
comportement existant est conservé.

#### Notice autonome pour le Décideur — C0b Linux/macOS (sonde C0A-3)

Le fichier [c0_multiformat_probe.py](../tools/c0_multiformat_probe.py) est
autonome, utilise la bibliothèque standard, n’importe pas le dépôt et ne fait
aucun accès réseau/DB/service. Il requiert Python 3.10 ou plus récent et
signale dans son résumé si l’interpréteur est inférieur à 3.10. La sonde crée
et supprime son propre répertoire temporaire; elle ne lit aucun document
utilisateur. La sonde Windows C0A-3 est validée. C0b Linux/macOS est reporté
par la décision #137 jusqu'à disponibilité des plateformes; aucun résultat
n'est présumé. Reprendre cette notice lorsque le projet sera disponible sur
Linux ou macOS.

1. Transférer uniquement le script par copie directe ou support amovible. Après
   publication, il pourra aussi être récupéré depuis le dépôt.
2. Vérifier son empreinte dans le dossier contenant le script.
   Linux : `sha256sum c0_multiformat_probe.py`.
   macOS : `shasum -a 256 c0_multiformat_probe.py`.
   Comparer le résultat à `9251e6a6742a161031a7956652c56c3715a194c93a02b55c2e0ac8d0b1d8e169`.
3. Noter la version et le chemin de l’interpréteur :
   `python3 --version` puis `python3 -c 'import sys; print(sys.executable)'`.
   Si la version diffère de 3.15.2, la consigner; Python 3.10+ est requis.
4. Lancer la sonde complète, sans `chmod` nécessaire :
   Linux et macOS : `python3 c0_multiformat_probe.py`.
   Sous Windows, la durée observée était de 291.472 s; elle varie selon la
   machine. Le délai global est de 900 s. En cas d’expiration, la sonde émet
   un rapport partiel et termine avec le code 124; traiter cela comme un échec.
   Le contrôle PyInstaller est `SKIP` par défaut hors Windows. S’il est déjà
   installé et que cette comparaison est souhaitée, lancer
   `python3 c0_multiformat_probe.py --frozen`; ne rien installer.
   Résultat attendu : `RÉUSSI`, puis un bloc `C0A|...` unique.
5. En cas d’échec, copier la sortie humaine et le bloc `C0A|...`; ne pas
   modifier l’application ni relancer en boucle. Si Python est absent ou
   inférieur à 3.10, noter « non testable » et utiliser uniquement un
   interpréteur déjà disponible ou demander une décision distincte avant toute
   installation.
6. Sous POSIX, `multiprocessing` peut créer un processus auxiliaire
   `resource_tracker`. Il peut apparaître pendant que Python exécute la sonde;
   ne pas le confondre avec un worker orphelin et ne pas l’arrêter pendant
   l’exécution. Vérifier les PID après la fin de la sonde : un tracker qui
   subsisterait après la sortie de son parent doit être signalé.
7. Le script liste les PID enfants encore actifs et la commande pour les arrêter.
   Linux/macOS : vérifier un PID indiqué avec `ps -p <PID> -o pid=,ppid=,comm=`;
   arrêter uniquement ce PID avec `kill -TERM <PID>`, puis `kill -KILL <PID>`
   seulement s’il reste actif. macOS : noter spécifiquement le démarrage `spawn`,
   la fin de chaque enfant et tout PID qui survivrait à son parent.

Tableau à compléter avec les retours du Décideur (ne préremplir que Windows;
aucun résultat Linux/macOS n’est présumé) :

| Plateforme | Vérification | Résultat | Version de Python | Remarques |
|---|---|---|---|---|
| Windows | Pré-scan adverse | RÉUSSI | 3.15.2 | 58 tests ciblés; différentiel à graine fixe sur octets structurels, comptes exacts |
| Windows | Délai worker | RÉUSSI, 5.022 s | 3.15.2 | `spawn` bloqué sur tube; CPU 5.024 s |
| Windows | Orphelins | RÉUSSI, aucun | 3.15.2 | Timeout, boucle CPU et erreurs de réception |
| Windows | Échange borné | RÉUSSI | 3.15.2 | Réponse normale bornée; dépassement refusé |
| Windows | Isolation spawn source | RÉUSSI | 3.15.2 | Non isolé attendu; médiane/max 239.609/252.539 ms, 5 mesures |
| Windows | Isolation subprocess source | RÉUSSI | 3.15.2 | Isolé attendu; médiane/max 97.900/136.836 ms, 5 mesures |
| Windows | Coût de démarrage | RÉUSSI, ping 0.237/0.365 s médiane/max | 3.15.2 | 20 mesures; sonde légère, pas le serveur |
| Windows | Mesures | RÉUSSI, 16 × 20 | 3.15.2 | Rejets chronométrés; `tracemalloc`, pas RSS |
| Windows | Isolation figée | RÉUSSI | 3.15.2 | PyInstaller 6.22.3; spawn 1 136.476/1 257.691 ms, subprocess 1 027.486/2 107.919 ms, médiane/max sur 5 mesures |
| Windows | Packaging figé | RÉUSSI | 3.15.2 | Build et exécution worker temporaires, code 0 |
| Linux | Pré-scan adverse | En attente | À renseigner | Exécuter le même script |
| Linux | Délai worker | En attente | À renseigner | Vérifier `spawn` et arrêt |
| Linux | Orphelins | En attente | À renseigner | Rapporter PID éventuel |
| Linux | Échange borné | En attente | À renseigner | Vérifier refus de surcharge |
| Linux | Isolation des imports | En attente | À renseigner | Aucun résultat présumé |
| Linux | Coût de démarrage | En attente | À renseigner | 20 exécutions |
| Linux | Mesures | En attente | À renseigner | `tracemalloc`, pas RSS |
| Linux | Packaging figé | SKIP par défaut | À renseigner | Opt-in avec `--frozen` si PyInstaller est déjà présent |
| macOS | Pré-scan adverse | En attente | À renseigner | Exécuter le même script |
| macOS | Délai worker | En attente | À renseigner | Observer le comportement `spawn` |
| macOS | Orphelins | En attente | À renseigner | Vérifier l’enfant après timeout |
| macOS | Échange borné | En attente | À renseigner | Vérifier refus de surcharge |
| macOS | Isolation des imports | En attente | À renseigner | Aucun résultat présumé |
| macOS | Coût de démarrage | En attente | À renseigner | 20 exécutions |
| macOS | Mesures | En attente | À renseigner | `tracemalloc`, pas RSS |
| macOS | Packaging figé | SKIP par défaut | À renseigner | Opt-in avec `--frozen` si PyInstaller est déjà présent |

Essai PyInstaller Windows exécuté sans installation, avec `$python` pointant
sur `.venv\Scripts\python.exe` et `$script` sur le chemin absolu de la sonde :

```powershell
rtk $python -m PyInstaller --noconfirm --onefile --name c0a-multiformat-probe --distpath $dist --workpath $work --specpath $spec $script
rtk $exe --smoke
```

Sorties : `Build complete!`, `pyinstaller_build_exit=0`,
`packaged_smoke_exit=0`, smoke `RÉUSSI`, orphelins `aucun`. Les dossiers
temporaires dist/work/spec hors dépôt ont été supprimés après la vérification.

**Point de reprise C0** : C0a Windows validé par C0A-3; C0b Linux/macOS est
reporté (décision #137) jusqu'à disponibilité des plateformes, sans résultat
présumé. C0b reste un verrou pour CSV/JSON et la clôture multiformat POSIX,
mais ne bloque pas la livraison de `.txt`/`.sql` après validation propre (#139).
C1/C2 n'attendent pas C0b; C3/C4 peuvent être développés sous Windows, avec
preuves multiplateformes requises avant activation CSV/JSON. Aucune capacité
nouvelle n’est livrée.

**Matrice besoin → changement → preuve future** :

| Besoin | Composants à faire évoluer après arbitrage | Vérification attendue |
|---|---|---|
| Libellé et sélection | [`chat.html`](../tools/web/chat.html), [`chat.js`](../tools/web/chat.js); acceptation cohérente avec l’allowlist serveur. | Pour chaque format autorisé, sélection et affichage cohérents; refus UI/API concordants pour le reste. |
| Validation et droits | [`login_server.py`](../tools/login_server.py), [`security_files.py`](../tools/security_files.py); type réel, nom, taille, authentification, CSRF, propriétaire et conversation. | Fichiers valides/invalides, noms et chemins malveillants, droits user/admin et isolation inter-comptes. |
| Extraction | [`extract_text.py`](../tools/nodes/extract_text.py) ou extracteurs existants approuvés; aucun nouveau module ni paquet choisi par ce GO. | Fichiers corrompus, chiffrés, vides, sans texte, dépassant les limites ou provoquant une extraction bloquée. |
| Limites et isolation | [`login_server.py`](../tools/login_server.py), parseur(s) et stockage après choix. | Dépassement de taille/durée/mémoire, archives excessives, nettoyage après succès/erreur; aucun réseau ni exécution. |
| Stockage et suppression | [`citadelle_memory.py`](../tools/citadelle_memory.py), [`login_server.py`](../tools/login_server.py); cardinalité et limites de purge selon la décision #136. | Accès propriétaire/conversation, retrait, suppression, reprise après rechargement et absence de fuite. |
| Modèle et résultats | [`login_server.py`](../tools/login_server.py), [`chat.js`](../tools/web/chat.js); contenu traité comme donnée non fiable et état partiel visible. | Tentatives d’injection d’instructions, absence d’appel d’outil, rendu sûr et indication correcte des analyses partielles. |
| Guides utilisateurs | [`README.md`](../../README.md) et [`README.fr.md`](../../README.fr.md), après validation réelle des formats. | Aucun format annoncé avant que son parcours soit pris en charge et vérifié. |

**Validation future** : non-régression `.md`; succès/refus de chaque format
autorisé/interdit; fichiers corrompus, chiffrés, compressés ou excessifs;
limites et nettoyage; isolation utilisateur/conversation; absence d’exécution,
macros et accès réseau; affichage sûr, injection d’instructions et signalement
des traitements partiels. Ces tests portent sur la future intégration au chat;
C0a ne la modifie pas. La suite actuelle `.md` et les tests isolés du prototype
ont été exécutés, sans rendre de format supplémentaire disponible.

**Tests existants** : quatorze cas dans
[test_chat_documents.py](../tests/test_chat_documents.py) couvrent notamment
migration, UTF-8/classification, limites `.md`, authentification et CSRF,
isolation, refus d’un second document, suivi après rechargement, retrait,
nettoyage temporaire et contrôles HTML. Ces tests décrivent le premier incrément;
ils ne valident pas encore de formats multiformat.

**Prochaine action** : demander un GO distinct pour C1 sous Windows.
C0b Linux/macOS reste reporté (#137), sans résultat présumé; CSV/JSON et la
clôture multiformat POSIX restent bloqués par C0b. `.txt`/`.sql` peuvent être
livrés POSIX après leur validation propre sans attendre C0b (#139). C1/C2
n'attendent pas C0b; C3/C4 peuvent être développés sous Windows, avec preuves
multiplateformes requises avant activation CSV/JSON.
**Moment de traitement** : C0a Windows validé; C0b Linux/macOS reporté
(décision #137). C0 reste ouvert pour CSV/JSON jusqu'à validation C0b; la
livraison textuelle `.txt`/`.sql` n'en dépend pas (#139).

**Point de reprise**

- **Étapes A et B** : terminées et arbitrées le 2026-11-25 par les décisions
  #135 et #136; Windows-first et arbitrages C1–C4 consignés par #137/#138;
  texte POSIX et contexte arbitrés par #139 le 2026-11-27.
- **Étape C** : non commencée; GO distinct requis. D et E ne sont pas
  commencées.
- **Capacité actuelle** : l’upload chat accepte `.md` seulement.
- **Périmètre futur approuvé** : `.md`, `.txt`, `.csv`, `.json`, `.sql`;
  CSV/JSON structurés, Markdown/TXT/SQL textuels, aucun contenu exécuté.
- **Version cible** : à déterminer.
- **Prochaine action** : demander un GO distinct pour C1 sous Windows.
- **Contexte (Option C, décision #139)** : jusqu’à ≈6 000 tokens, fichier entier;
  au-delà, fiche ≈1 000 tokens et segments selon la question. CSV : 3–10 lignes
  par segment avec en-tête; JSON : élément de premier niveau avec JSON Pointer,
  subdivisé par enfants au besoin. Budget de départ : 6–9 segments (≈8 000
  tokens) et ≥12 000 tokens pour conversation/réponse; valeurs à réviser après
  mesure réelle. D affiche le compte N/M des segments consultés, sans
  troncature silencieuse. C2 vérifie l’adéquation de FTS5 aux segments/locators.
- **C1/C2** : peuvent avancer sans attendre C0b.
- **C3/C4** : peuvent être développés sous Windows; preuves multiplateformes
  requises avant livraison.
- **Conditions C** : tests adverses du pré-scan JSON avant `json.loads`;
  subprocess dédié, délai total envoi→terminaison, plafonds CSV candidats
  comptés avant analyse et packaging worker; preuves C0b avant activation
  CSV/JSON et clôture POSIX. Plafonds/budgets révisables après mesure réelle.
- **Points de suivi** : livraison `.txt`/`.sql` POSIX après validation propre,
  sans attendre C0b; aucun format annoncé avant vérification.
- **Autorisation** : C1 peut être demandé par un GO distinct sous Windows;
  aucune implémentation C n’est autorisée sans ce GO.
- **Références à lire dans l’ordre** : [présente section](#16-multiformat);
  [décision #135](../../.memory/decisions.md#2026-11-25-arbitrage-fonctionnel-du-premier-palier-multiformat);
  [décision #136](../../.memory/decisions.md#2026-11-25-arbitrage-des-conditions-techniques-multiformat);
  [invariants #134](../../.memory/decisions.md#2026-11-24-cadrage-documentaire-du-chantier-16-multiformat);
  [SPEC-FICHIERS-CHAT](./SPEC-FICHIERS-CHAT.md) pour le contrat actuel;
  [PHASE16-RESTE](./PHASE16-RESTE.md) et [ETAT-PROJET](./ETAT-PROJET.md);
  dernière entrée de [JOURNALDEBORD](./JOURNALDEBORD.md) et
  [JOURNALDESMODIFS](./JOURNALDESMODIFS.md) pour l’arrêt.
- **Référence C0a** : préflight au HEAD
  `da70406d63c622fd7df0a01621f1f267fe09f787`; les faits de code du cadrage B
  restent rattachés au HEAD `b3da82ea5e32734953efc11c998a53ad91070f85` et à la
  cartographie antérieure `ee990535e039135cc0065136a71e3e4028ae9310`.
- **Vérifications C0a** : suite historique `338 passed in 92.40s`, puis
  `375 passed in 96.36s`; C0A-2 : `396 passed in 97.03s`; C0A-3 :
  `396 passed in 114.25s`, 58 tests ciblés. Pré-scan, worker, comparaisons
  d’isolation (cinq mesures), mesures et packaging Windows réussis. Détails et
  limites dans « C0 — résultats » ci-dessus. Aucun code de production, DB
  utilisateur ou format d’upload n’a changé.

Chaque futur GO 16-MULTIFORMAT met à jour ce point de reprise, le statut
concerné et les journaux dans le même lot.

**Étapes proposées** (découpage de travail; A est consignée comme terminée;
ce tableau n’autorise pas l’implémentation) :

| Étape | Précondition | Résultat attendu | Preuve de validation | Condition d’arrêt |
|---|---|---|---|---|
| A. Arbitrage fonctionnel — terminé le 2026-11-25 | Proposition examinée et arbitrage explicite du Décideur. | Allowlist et profondeur approuvées; version cible à déterminer. | Décision #135 consignée. | Aucun travail technique n’est autorisé par cette étape seule. |
| B. Cadrage technique — terminé et arbitré le 2026-11-25 | Décision #136 répondant aux cinq recommandations du cadrage. | Proposition B arbitrée; aucune implémentation n’en découle. | Décisions #135/#136 consignées, conditions C explicites. | Les conditions de preuve restent obligatoires avant support effectif. |
| C. Implémentation séparément autorisée | GO distinct après B arbitrée. | Contrôles serveur, extraction et tests correspondants selon le périmètre approuvé. | Tests adverses JSON, validation packaging worker et mesures seuils; tests ciblés des formats. | Revenir à l’arbitrage si le pré-scan échoue; aucune alternative sans limites dures sans décision explicite. |
| D. Intégration utilisateur | Étape C vérifiée et GO distinct. | Sélection, messages, résultats partiels; renommer le bouton seulement pour les capacités vérifiées. | Vérifications UI/API concordantes avec l’allowlist. | Arrêter si les formats annoncés diffèrent du support réel ou si les résultats partiels sont opaques. |
| E. Validation et clôture | Étapes C et D vérifiées. | Preuves fonctionnelles/sécurité, documentation utilisateur et suivi réconcilié; livraison autorisée séparément. | Résultats de validation et journaux cohérents. | Ne pas clôturer ni livrer tant qu’une preuve manque ou qu’un échec reste ouvert. |

#### 16-AUDIT-ACTOR

**Statut** : terminé le 2026-11-24 (GO 16-CLEANUP-DETTE, migration v13).
**Dépendances** : audit SQL v12 livré.
**Priorité** : moyenne.
**Résultat** : `audit_log.actor_id` reçoit l’identité authentifiée fournie par
les handlers API/admin; `user_id` reste le propriétaire de la ligne. Les
suppressions SQL directes sans contexte d’acteur restent enregistrées avec
`actor_id=NULL`.
**Moment de traitement** : livré par la migration v13 et ses tests.

**Note** : TODO.md est la source de vérité pour la liste actionnable;
BACKLOG.md conserve le statut, les priorités et l'effort estimé sans
répéter les détails des GO.
