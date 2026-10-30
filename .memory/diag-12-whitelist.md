# Diagnostic Phase 12 — cycle de vie whitelist et rollback

**Statut** : diagnostic en lecture seule; aucune décision #70 ouverte.
**Reproduction** : non effectuée; conclusions théoriques fondées sur le code et
les réglages SQLite lus en mode `ro`.

## Contexte

Le parcours normal télécharge un runtime et un GGUF, puis `lancer.bat` vérifie
le fichier et la whitelist avant de démarrer llamafile. La whitelist est
fail-closed, mais le bootstrap ne l'initialise pas. Sur une base neuve, la
vérification pré-runtime arrive aussi avant les migrations et le démarrage du
proxy, donc avant que l'admin puisse remplir la liste dans `/settings`.

## 2. Cartographie de la whitelist

### Source et représentation

- **Aucune table whitelist dédiée** : le stockage est la clé `allowed_models`
  dans la table SQLite générique `settings`.
- Schéma exact (`citadelle_memory.py:130-135`) :
  `settings(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)`.
- `settings.allowed_models` est un tableau JSON de chemins GGUF absolus.
  `get_setting` renvoie `None` si la clé manque (`citadelle_memory.py:286-305`);
  `_get_allowed_models` convertit cette absence en `[]`
  (`login_server.py:622-632`).
- `model_health.check_whitelist` refuse un chemin vide, une clé absente, une
  erreur SQL, un JSON invalide ou un chemin absent de la liste
  (`model_health.py:39-77`). Les chemins sont résolus et normalisés avec
  `Path.resolve`, `normpath` et `normcase`.
- L'admin peut lire et remplacer la liste via
  `GET/POST /api/settings/allowed_models`. Le POST n'enregistre que des
  fichiers `.gguf` existants, non vides et résolus en absolu
  (`login_server.py:634-712`; UI `settings.html:50-62,302-360`).
- `llamafile_config.json` est le **manifest de téléchargement**, pas la
  whitelist. `dist/.current_model` est un miroir du modèle choisi, pas un
  registre d'autorisation.

### Inventaire des occurrences

La recherche demandée a trouvé 137 occurrences dans 12 fichiers :

| Fichier | Occurrences | Rôle |
|---|---:|---|
| `.memory/decisions.md` | 22 | Décisions et historique |
| `dev/docs/BACKLOG.md` | 12 | Spécification et résultat des lots |
| `dev/docs/JOURNALDEBORD.md` | 7 | Chronologie |
| `dev/docs/JOURNALDESMODIFS.md` | 7 | Historique des changements |
| `dev/docs/ROADMAP.md` | 1 | Livrable de la Phase 11 |
| `dev/docs/RUNBOOK-PROD.md` | 1 | Procédure de restauration |
| `dev/tools/login_server.py` | 17 | API admin, contrôle et persistance |
| `dev/tools/model_health.py` | 11 | Vérification de whitelist et rollback |
| `dev/tools/web/settings.html` | 2 | Interface admin |
| `dev/tests/test_admin_model.py` | 34 | Validation API et chemins de rollback |
| `dev/tests/test_e2e_model_change.py` | 6 | Tests de bout en bout |
| `dev/tests/test_model_health.py` | 17 | Tests du contrôle fail-closed |

Aucune occurrence correspondante n'a été trouvée dans `AGENTS.md` ni dans
`dist/`. Il n'existe pas de constante Python qui énumère la whitelist. La
constante `DEFAULT_MODEL_PATH` est seulement un chemin de repli, pas une
autorisation.

### Schéma et état local observé

La base locale a été ouverte en mode SQLite `ro`; aucun utilisateur, mot de
passe ou autre table n'a été lu. Elle contient une table `settings` avec le
schéma ci-dessus. `SELECT * FROM settings` montre une liste de deux modèles
autorisés; `current_model_path` et `previous_model_path` sont présents et
pointent actuellement vers le même modèle (basename Qwen3 4B). Le marqueur
`dist/.current_model` correspond au modèle courant. Ce snapshot n'est donc
pas l'état d'une première installation.

## 3. Cycle de vie du modèle

### Installation

- `install.bat:11-15` appelle `python -B dev\tools\bootstrap.py`, puis
  démarre `lancer.bat` si le bootstrap réussit.
- `dev/tools/llamafile_config.json:15-17` définit le GGUF
  `Qwen3-1.7B-Q4_K_M.gguf`, dans `dev/tools/vendor/llamafile/`, avec le
  SHA-256 `16da7ba1721b1620fa843e0978badd3d93756274fd209a01874b37e29750e207`.
- `bootstrap.py:35-48,335-365,416-450` place le GGUF dans `VENDOR_DIR`;
  llamafile-thin va dans `dist/` et est renommé `llamafile.exe` sous Windows.
  Les assets requis sont téléchargés si absents, vérifiés par SHA-256, puis
  publiés depuis un temporaire. Un fichier existant dont le hash est correct
  est conservé. Aucun seuil de taille attendu n'est déclaré dans la config.
- Ni `install.bat`, ni le bootstrap n'écrivent `dist/.current_model`, ne
  migrent SQLite et ne peuplent `settings.allowed_models`.

### Démarrage

- `lancer.bat:17-22` lit `dist/.current_model` s'il existe; sinon il choisit
  le défaut relatif `dev\tools\vendor\llamafile\Qwen3-1.7B-Q4_K_M.gguf`.
- Après vérification d'existence, il appelle
  `model_health.py --check-whitelist` avant de lancer llamafile
  (`lancer.bat:39-59`). Le runtime n'est lancé qu'à partir de la ligne 91.
- `login_server.py` n'est pas le chargeur du GGUF. Son `main()` applique les
  migrations V3-V6 et crée l'admin (`login_server.py:2327-2360`), mais le
  lanceur ne démarre le proxy qu'après la disponibilité de llamafile
  (`lancer.bat:110-118`). La migration qui crée `settings` arrive donc trop
  tard pour le premier contrôle de whitelist.

### Changement admin

`POST /api/admin/model` vérifie le fichier GGUF, puis refuse une liste vide
ou un chemin non autorisé (`login_server.py:1344-1435`). Si le changement
réussit, il déplace le `current_model_path` précédent vers
`previous_model_path` uniquement s'il existe et diffère de la cible, puis
enregistre le nouveau chemin SQLite et dans `dist/.current_model`
(`login_server.py:1440-1500`). Il n'y a pas de chargement à chaud du modèle
dans ce POST.

## 4. Cartographie du rollback

- **Échec avant démarrage** : un modèle absent mène à `--rollback`
  (`lancer.bat:24-39`); un modèle présent mais refusé par la whitelist mène
  également à `--rollback` (`lancer.bat:57-72`).
- **Échec de chargement** : après le démarrage de llamafile, un contrôle
  `/v1/models` raté mène aussi à `--rollback` (`lancer.bat:105-111,153-160`).
- `restore_previous_model` lit `previous_model_path`, puis fait
  `previous_path or DEFAULT_MODEL_PATH` sans vérifier qu'un état précédent
  existe ni que la cible existe (`model_health.py:119-136`). Il écrit ensuite
  le chemin dans le miroir et `current_model_path`; il journalise la cible
  (`model_health.py:138-155`).
- Si `settings` existe mais que `previous_model_path` manque, le rollback
  n'est donc pas un retour à un ancien modèle : il écrit le chemin par défaut
  et l'étiquette « modèle par défaut ». Le test
  `test_post_mirrors_path_and_first_manual_rollback_uses_default`
  confirme explicitement ce comportement (`test_admin_model.py:230-262`).
- Si la table `settings` elle-même n'existe pas, `check_whitelist` capture
  l'erreur SQL et retourne `False` (`model_health.py:42-53`). Le rollback
  échoue ensuite en lisant `previous_model_path`; `model_health.py` renvoie
  une erreur, puis `lancer.bat` passe au label de repli par défaut
  (`lancer.bat:62-83`). Ce repli repasse par la whitelist vide et s'arrête.
- **Point sans garde d'état antérieur** : les branches `MODEL_NOT_WHITELISTED`
  et `MODEL_LOAD_FAILED` appellent `--rollback` sans vérifier
  `previous_model_path`; le repli de `restore_previous_model` traite
  l'absence comme le chemin par défaut.

## 5. Première installation hors réseau

**REPRODUCTION NON EFFECTUÉE.** Aucun clone temporaire, bootstrap, serveur
ou changement réseau n'a été lancé; cela évite de créer/effacer des données
hors du seul fichier diagnostic autorisé.

Scénario théorique :

1. Une vraie installation hors réseau, sans assets préinstallés, s'arrête
   dans `bootstrap.py` : les deux assets requis ont des URL HTTPS
   (`llamafile_config.json:6-17`). Elle n'atteint pas le lanceur.
2. Après téléchargement réussi, un premier lancement sans
   `citadelle_data/` ni `dist/.current_model` choisit le GGUF Qwen3 par
   défaut. Le contrôle pré-runtime cherche `settings.allowed_models` avant
   que `login_server.py` n'ait créé la table.
3. La whitelist est donc refusée. Le lanceur appelle le rollback même s'il
   n'existe aucun modèle précédent. Si la table est absente, la commande de
   rollback échoue puis le contrôle du défaut échoue encore; si la table est
   déjà créée mais sans `previous_model_path`, le rollback écrit le défaut
   comme « courant », puis la whitelist vide le refuse également.

## 6. Synthèse

| Hypothèse | Résultat | Preuve |
|---|---|---|
| H1 — whitelist statique obsolète | **INFIRMÉE** | La whitelist est une valeur SQLite dynamique; le JSON ne décrit que les assets. |
| H2 — whitelist vide sans auto-enregistrement | **CONFIRMÉE** | Absence de `allowed_models` → `[]`/refus; ni install ni bootstrap ne l'inscrivent (`login_server.py:622-632`, `model_health.py:39-77`). |
| H3 — rollback sans état antérieur | **CONFIRMÉE** | Le lanceur l'appelle sur tout refus; l'absence de `previous_model_path` tombe sur le défaut (`lancer.bat:62-83`, `model_health.py:119-136`). |
| H4 — dépendance HTTPS/proto | **INFIRMÉE** | Le contrôle whitelist compare des chemins et SQLite; aucun protocole réseau n'y participe. |
| H5 — casse/chemin Windows | **INFIRMÉE comme cause racine** | Le contrôle et le POST normalisent/résolvent les chemins; aucune incohérence de casse n'explique l'absence de clé. |

**Cause racine** : le premier lancement vérifie une whitelist SQLite qui n'est
jamais initialisée par l'installation, avant que le proxy ne migre la base ou
permette à l'admin d'ajouter le GGUF; tout refus déclenche ensuite un rollback
inconditionnel qui confond « aucun précédent » avec « modèle par défaut ».

### Recommandation fonctionnelle pour un futur GO

1. Avant le contrôle pré-runtime, initialiser `settings` et autoriser
   uniquement le GGUF par défaut dont le hash du manifest a été vérifié;
   ne pas autoriser automatiquement d'autres GGUF téléchargés ou trouvés.
2. Séparer « initialiser le premier modèle » du rollback : n'appeler le
   rollback que si un chemin précédent est enregistré, existe et est encore
   autorisé. Sans précédent, démarrer le défaut vérifié ou s'arrêter avec une
   instruction claire, sans écrire un faux état de rollback.
3. Garder la whitelist fail-closed pour les changements admin et préserver
   les 186 tests actuels; ajouter des tests d'installation à base vide, de
   première autorisation, de rollback sans précédent et de rollback valide.

**Périmètre estimé** : `lancer.bat`, `dev/tools/model_health.py`,
`dev/tools/citadelle_memory.py` et probablement `dev/tools/bootstrap.py` ou
`dev/tools/login_server.py`, selon le point choisi pour l'initialisation;
`dev/tests/test_model_health.py`, `test_admin_model.py` et un test E2E.
Environ 6-8 tests nouveaux, 4-6 heures avec validation Windows et suite
complète. Risque principal : trop élargir l'autorisation initiale; la limiter
au GGUF intégré au manifest et vérifié par SHA-256.

## Références principales

- `install.bat:11-15`
- `dev/tools/llamafile_config.json:6-18`
- `dev/tools/bootstrap.py:35-48,155-190,335-365,416-450`
- `lancer.bat:17-22,24-39,43-50,57-83,89-118,153-160`
- `dev/tools/model_health.py:17-25,39-77,119-155`
- `dev/tools/citadelle_memory.py:30-32,130-135,280-305`
- `dev/tools/login_server.py:622-712,1344-1500,2327-2360`
- `dev/tools/web/settings.html:50-62,302-360`
- `dev/tests/test_model_health.py:131-145`
- `dev/tests/test_admin_model.py:230-262,274-324`
- `.memory/decisions.md:1316-1386`
