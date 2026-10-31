# Runbook de préparation production

## Première installation (poste neuf)

La Citadelle s'exécute localement sous Windows, Linux et macOS. L'archive est
source-only : elle ne contient ni llamafile ni modèle GGUF. Une connexion
Internet est nécessaire à la première installation si ces assets ne sont pas
déjà présents.

### Pré-requis et durée

- Windows 10/11, une distribution Linux avec Bash, ou macOS avec Bash.
- Python 3.10+ dans le `PATH` (`python` sous Windows, `python3` sous Linux/macOS);
  Python 3.13.17 a été testé sous Windows.
- Sous macOS, Homebrew est recommandé pour installer Python.
- Connexion Internet et droits d'écriture sur le dossier d'installation.
- Environ 2 Go d'espace disque libre.
- Prévoir 5–15 minutes pour télécharger environ 1,33 Go, selon la connexion,
  puis 1–2 minutes pour le démarrage; durée totale indicative : 10–20 minutes.

### Étapes

1. Télécharger l'archive `lacitadelle-distribution.zip` depuis la source
   officielle et l'extraire dans un dossier accessible en écriture, par
   exemple `C:\citadelle\`.
2. Facultatif : calculer le SHA-256 avec
   `Get-FileHash .\lacitadelle-distribution.zip -Algorithm SHA256` et le
   comparer à l'empreinte publiée séparément avec l'archive.
3. Lancez l'installateur natif :
    - Windows : double-cliquer sur `install.bat`.
    - Linux : exécuter `./install.sh`. Si nécessaire, commencer par
      `chmod +x install.sh lancer.sh`.
    - macOS : ouvrir `install.command`. Si Gatekeeper bloque le premier
      lancement, faire un clic droit sur le fichier puis choisir **Ouvrir**.
4. L'installateur télécharge l'unique runtime llamafile-thin universel et le
    GGUF, vérifie leurs SHA-256 depuis `dev/tools/llamafile_config.json`, puis
    lance `lancer.py`. Le runtime est placé dans `dist/` sous le nom
    `llamafile.exe` (Windows), `llamafile-linux` (Linux) ou
    `llamafile-macos` (macOS).
5. Une console du runtime est ouverte sous Windows; la console du lanceur
    affiche la sortie du proxy.
6. **Copier immédiatement le mot de passe admin affiché dans la console du
   lanceur.** Il n'est affiché qu'une fois. Le lanceur relaie la sortie standard
   du proxy; ses erreurs standard sont redirigées vers
   `dist/proxy.log`. Le mot de passe n'est donc pas récupérable depuis ce log.
7. Ouvrir `http://127.0.0.1:8081/`, se connecter comme `superadmin` avec le
   mot de passe copié, puis le changer lorsqu'il est demandé.
8. Utiliser le chat. Le lanceur ouvre aussi automatiquement l'interface;
    le relancer (`lancer.bat`, `lancer.sh` ou `lancer.command`) est utile après
    un arrêt.

### Vérifications après installation

- Le runtime adapté à l'OS et
  `dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf` existent.
- `citadelle_data/memory.db` existe et la liste
  `settings.allowed_models` contient le GGUF intégré autorisé.
- Au premier lancement, `dist/.current_model` peut être absent : c'est
  normal. Sans modèle courant configuré, le lanceur utilise le GGUF intégré
  vérifié; le miroir est créé lors d'un changement de modèle.
- Vérifier `dist/proxy.log` pour les erreurs d'initialisation ou
  `[security] rollback refusé`; ce dernier message n'est pas attendu sur une
  première installation saine.

## Dépannage — Première installation

### Runtime llamafile introuvable ou non exécutable

L'installation n'a pas terminé le bootstrap ou le runtime manque. Relancer
`install.bat`, `install.sh` ou `install.command` avec Internet disponible.
Les chemins attendus sont `dist/llamafile.exe` sous Windows,
`dist/llamafile-linux` sous Linux et `dist/llamafile-macos` sous macOS.
Sous Linux/macOS, appliquer `chmod +x` au wrapper puis relancer l'installation
si le runtime n'a pas le droit d'exécution. Pour une installation manuelle,
comparer son SHA-256 à `dev/tools/llamafile_config.json`.

### « Permission denied » sous Linux/macOS

L'archiveur peut avoir retiré le bit exécutable lors de l'extraction. Depuis
le dossier extrait, exécuter `chmod +x install.sh lancer.sh
install.command lancer.command`, puis relancer l'installateur.

### Gatekeeper bloque `install.command` ou `lancer.command` sous macOS

Vérifier que l'archive vient de la source officielle et que les sommes de
contrôle sont valides. Faire un clic droit (ou Control-clic) sur le fichier
`.command`, choisir **Ouvrir**, puis confirmer l'ouverture. Ne pas désactiver
Gatekeeper globalement.

### « Python introuvable »

Installer Python 3.10+ depuis [python.org](https://www.python.org/) sous
Windows (cocher **Add Python to PATH**). Sous Linux/macOS, installer Python 3.10+
depuis le gestionnaire de paquets de la distribution ou Homebrew. Vérifier
`python --version` sous Windows ou `python3 --version` sous Linux/macOS.

### Téléchargement échoué ou expiré

Vérifier la connexion, puis relancer l'installateur natif; le bootstrap reprend les
assets manquants et vérifie leur checksum. Sur un réseau d'entreprise,
configurer `HTTP_PROXY`/`HTTPS_PROXY` selon les consignes de l'organisation.
Ne pas remplacer un fichier partiel par un asset de source non vérifiée.

### Page vide ou fichiers web introuvables

Vérifier que l'archive contient `dev/tools/web/` avec notamment `login.html`,
`chat.html`, `settings.html` et `admin.html`. En cas de fichiers absents,
retélécharger et ré-extraire l'archive officielle sans déplacer ce dossier.

### Initialisation whitelist refusée ou SHA-256 invalide

Vérifier la présence de
`dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf` et comparer son SHA-256
au manifeste. Relancer l'installateur natif avec Internet pour laisser le bootstrap
réparer un asset corrompu. Le lanceur ne doit pas inscrire un fichier absent
ou dont le hash est invalide.

### « rollback refusé : aucun modèle antérieur valide »

Ce message signifie qu'aucun chemin précédent n'est enregistré; il ne prouve
pas à lui seul que le GGUF est corrompu. Sur une première installation saine,
le chemin courant est absent et le lanceur démarre directement le modèle
intégré après vérification de son hash. Si le message apparaît, consulter
`dist/proxy.log` et distinguer ce refus d'un échec explicite de vérification
SHA-256.

### Mot de passe admin perdu

Si la console du lanceur est encore ouverte, récupérer le mot de passe one-time
dans la sortie standard relayée du proxy; il n'est pas dans `dist/proxy.log`. Si une
session admin authentifiée reste ouverte, l'utiliser pour réinitialiser le
compte.

Sans session admin utilisable, le dernier recours consiste à arrêter les deux
serveurs et à sauvegarder `citadelle_data\memory.db`, ses éventuels fichiers
`memory.db-wal`/`memory.db-shm` et `dist\.current_model`. Déplacer ensuite ces
fichiers hors de leurs chemins actifs (ensemble pour la base et ses sidecars),
puis relancer le lanceur natif. Une base neuve recrée `superadmin` et affiche un
nouveau mot de passe dans la console. Cette réinitialisation fait perdre de la
base active tous les comptes, sessions, conversations, préférences, métriques
et réglages; conserver la sauvegarde. Restaurer l'ancienne base rétablit aussi
l'ancien hash et ne révèle pas le mot de passe oublié.

### Port 8080 ou 8081 déjà utilisé

Identifier le processus avant d'agir; ne pas terminer un PID inconnu :

```powershell
Get-NetTCPConnection -State Listen -LocalPort 8080,8081
```

Sous Linux, utiliser `ss -ltnp '( sport = :8080 or sport = :8081 )'`;
sur macOS, utiliser `lsof -nP -iTCP:8080 -sTCP:LISTEN` puis la même commande
avec `8081`.

Arrêter proprement l'instance La Citadelle concernée, puis relancer
le wrapper natif `lancer.bat`, `lancer.sh` ou `lancer.command`.

## Statut et prérequis bloquants

Le parcours de première installation décrit ci-dessus couvre Windows, Linux
et macOS. Les procédures d'exploitation Caddy ci-dessous restent orientées
Windows; aucun DNS, pare-feu, certificat, service Caddy ni serveur public
n'est configuré par ce GO.

Les contrôles V3.1 (cookie `Secure` si HTTPS, CSRF sur les POST authentifiés
et rate limiting) sont implémentés par la décision #68. Cette préparation ne
déploie rien : avant l'ouverture publique, valider ces contrôles derrière le
Caddy réellement installé, le DNS, le certificat, les sauvegardes et les
alertes sur l'hôte cible.

La concurrence reste aussi non certifiée : `login_server.py` est mono-thread
et une inférence lente bloque les requêtes suivantes. Les seuils de monitoring
ci-dessous ne sont pas un test de capacité. Avant l'exposition, le décideur
doit accepter explicitement la charge initiale attendue ou lancer le GO
CONCURRENCE; ne pas annoncer une capacité non mesurée.

Les limites mémoire actuelles sont : après 5 échecs de `/login` par IP en
5 minutes, la tentative suivante est bloquée 15 minutes; les POST d'inférence
chat 30 par minute; `/api/admin/*` et les API de configuration admin modèle
10 par minute. Les compteurs sont réinitialisés au redémarrage du proxy et ne
limitent pas l'inscription; ils ne constituent pas une protection DDoS.

## Checklist du décideur avant déploiement

- [ ] Décider du FQDN public et vérifier les DNS `A` / `AAAA`.
- [ ] Valider derrière Caddy le cookie `Secure`, le rejet/acceptation CSRF et
      les réponses 429 avant l'ouverture à Internet.
- [ ] Décider si la capacité mono-thread est acceptable ou lancer le GO
      CONCURRENCE avant la mise en service.
- [ ] Installer Caddy depuis le site officiel sur l'hôte Windows; choisir un
      compte de service stable et persistant.
- [ ] Remplacer `citadelle.example.com` dans le Caddyfile; créer son dossier
      de logs et accorder au compte Caddy les droits minimaux nécessaires.
- [ ] Ouvrir seulement TCP 80/443 vers Caddy; vérifier que 8080, 8081 et 2019
      ne sont pas accessibles depuis Internet.
- [ ] Choisir un volume de sauvegarde protégé et configurer la tâche
      quotidienne.
- [ ] Configurer la surveillance externe sur `https://<domaine>/login` et
      tester la restauration sur une copie de staging.

## Préparation et validation Caddy

1. Télécharger `caddy.exe` depuis
   [caddyserver.com/download](https://caddyserver.com/download), le placer
   dans un répertoire contrôlé et ajouter ce répertoire au `PATH` du compte
   d'exploitation. Ne pas télécharger un binaire depuis un miroir inconnu.
2. Depuis la racine de l'application, remplacer le domaine d'exemple dans
   `Caddyfile`, puis créer `C:\ProgramData\LaCitadelle\Caddy\`. Vérifier les
   ACL du dossier de logs et du répertoire de données Caddy.
3. Après la configuration DNS et avant tout démarrage, valider la syntaxe :

   ```powershell
   caddy validate --config .\Caddyfile --adapter caddyfile
   ```

4. Caddy obtient et renouvelle automatiquement un certificat public lorsque
   le FQDN, le DNS, les ports et son stockage persistent sont correctement
   configurés. Il redirige également HTTP vers HTTPS. `caddy trust` installe
   la CA locale Caddy; ce n'est pas requis pour Let's Encrypt.
5. Pour une première validation en console :

   ```powershell
   caddy run --config .\Caddyfile --adapter caddyfile
   ```

   `caddy run` reste attaché à la console; Ctrl+C l'arrête. La commande
   `caddy start --config .\Caddyfile --adapter caddyfile` démarre en arrière-
   plan et `caddy stop` l'arrête. La documentation Caddy déconseille `caddy
   start` comme service Windows : son processus enfant reste attaché au
   terminal. Le démarrage automatique après redémarrage nécessite un compte
   de service et un gestionnaire de services Windows, à choisir et configurer
   hors de ce GO.

## Démarrage et arrêt — après autorisation de mise en service

### Démarrer

1. Vérifier que les ports et le DNS ciblent le bon hôte.
2. Lancer `lancer.bat`; attendre les messages de disponibilité de llamafile
   et du proxy.
3. Vérifier localement `http://127.0.0.1:8081/login` et
   `http://127.0.0.1:8080/v1/models`.
4. Démarrer Caddy avec le mode d'exploitation approuvé.
5. Depuis un client externe, vérifier `https://<domaine>/login`, le
   certificat et la redirection HTTP vers HTTPS. Ne pas publier les ports
   internes pour faciliter le diagnostic.

### Arrêter

1. Arrêter Caddy (`caddy stop` en mode arrière-plan, ou Ctrl+C en mode
   console) afin de fermer l'entrée publique.
2. Fermer les fenêtres `Lacitadelle Server` et `Lacitadelle Proxy` de
   `lancer.bat`.
3. Confirmer que les ports 8080 et 8081 ne sont plus à l'écoute. Ne pas tuer
   un processus inconnu pour libérer un port.

## Sauvegarde SQLite quotidienne

La commande `VACUUM INTO` crée une copie cohérente de la base ouverte. La
destination doit être nouvelle ou vide. Le marqueur `.current_model` est
copié dans le même jeu; éviter un changement de modèle pendant cette
opération afin que le marqueur et le réglage SQLite correspondent.

Enregistrer le script ci-dessous, lors du déploiement, sous
`C:\ProgramData\LaCitadelle\backup.ps1`, puis remplacer `$appRoot` et
`$backupRoot` par les chemins réels. Le volume de sauvegarde doit être
protégé par ACL, chiffré et distinct du volume de l'application.

```powershell
$ErrorActionPreference = 'Stop'
$appRoot = 'C:\LaCitadelle'
$backupRoot = 'D:\LaCitadelleBackups'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupSet = Join-Path $backupRoot $stamp

if (Test-Path -LiteralPath $backupSet) {
    throw "Le jeu de sauvegarde existe déjà : $backupSet"
}
New-Item -ItemType Directory -Path $backupSet -Force | Out-Null

$dbSource = Join-Path $appRoot 'citadelle_data\memory.db'
$dbTarget = Join-Path $backupSet 'memory.db'
$modelSource = Join-Path $appRoot 'dist\.current_model'
if (-not (Test-Path -LiteralPath $dbSource -PathType Leaf)) {
    throw "Base SQLite introuvable : $dbSource"
}
if (-not (Test-Path -LiteralPath $modelSource -PathType Leaf)) {
    throw "Marqueur de modèle introuvable : $modelSource"
}

$env:CITADELLE_DB_SOURCE = $dbSource
$env:CITADELLE_DB_TARGET = $dbTarget
try {
    python -c 'import os, sqlite3; src=sqlite3.connect(os.environ["CITADELLE_DB_SOURCE"], timeout=10); src.execute("VACUUM INTO ?", (os.environ["CITADELLE_DB_TARGET"],)); src.close(); check=sqlite3.connect(os.environ["CITADELLE_DB_TARGET"]); result=check.execute("PRAGMA integrity_check").fetchone()[0]; check.close(); print("integrity_check:", result); assert result == "ok"'
    if ($LASTEXITCODE -ne 0) { throw 'Échec de VACUUM INTO ou du contrôle SQLite.' }
}
finally {
    Remove-Item Env:CITADELLE_DB_SOURCE, Env:CITADELLE_DB_TARGET `
        -ErrorAction SilentlyContinue
}

Copy-Item -LiteralPath $modelSource `
    -Destination (Join-Path $backupSet '.current_model')
Set-Content -LiteralPath (Join-Path $backupSet 'SUCCESS.txt') `
    -Value "Vérifié le $(Get-Date -Format o)" -Encoding UTF8

$cutoff = (Get-Date).AddDays(-7)
$expiredSets = Get-ChildItem -LiteralPath $backupRoot -Directory |
    Where-Object {
        $_.Name -match '^\d{8}-\d{6}$' -and
        $_.LastWriteTime -lt $cutoff -and
        (Test-Path -LiteralPath (Join-Path $_.FullName 'SUCCESS.txt'))
    }
$expiredSets | Remove-Item -Recurse -Force
```

Dans le Planificateur de tâches Windows, exécuter ce fichier chaque jour à
heure creuse avec un compte dédié disposant uniquement des droits de lecture
sur l'application et d'écriture sur le volume de sauvegarde. L'action du
Planificateur peut lancer `powershell.exe -NoProfile -File
"C:\ProgramData\LaCitadelle\backup.ps1"` chaque jour à 02:00. Vérifier que
Python est dans le `PATH` de ce compte; sinon, remplacer `python` dans le
script par le chemin complet de `python.exe`.

Le script ne supprime que les jeux réussis, horodatés et âgés de plus de sept
jours sous le répertoire dédié; les jeux incomplets restent pour inspection.
Vérifier cette sélection sur l'hôte cible avant d'activer la tâche. Stocker
une copie chiffrée hors de l'hôte pour couvrir une panne du disque.

### Test mensuel de restauration

1. Choisir un jeu contenant `SUCCESS.txt`; vérifier également
   `PRAGMA integrity_check` sur sa base.
2. Restaurer dans une copie de staging isolée, jamais sur la base de
   production pendant le test.
3. Vérifier le login, les données attendues, le chargement du modèle et un
   échange de chat. Noter la durée et les erreurs sans copier de contenu de
   conversation dans un ticket.
4. Supprimer la copie de staging selon la procédure de l'organisation;
   conserver le jeu de sauvegarde valide.

### Copie à froid et restauration d'incident

Si `VACUUM INTO` est indisponible : fermer Caddy, arrêter proprement les deux
fenêtres de `lancer.bat`, puis copier `citadelle_data\memory.db` et
`dist\.current_model`. Ne pas copier la base pendant que le proxy tourne.

Pour restaurer un jeu validé, fermer d'abord l'entrée Caddy et arrêter les
deux fenêtres de `lancer.bat`. Adapter ensuite et exécuter ces commandes
depuis PowerShell. La base sauvegardée est vérifiée avant tout remplacement;
le répertoire `before-restore-*` conserve l'état courant :

```powershell
$ErrorActionPreference = 'Stop'
$appRoot = 'C:\LaCitadelle'
$backupSet = 'D:\LaCitadelleBackups\20261030-020000'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$before = Join-Path $appRoot "before-restore-$stamp"
$database = Join-Path $appRoot 'citadelle_data\memory.db'
$modelMarker = Join-Path $appRoot 'dist\.current_model'
$walFile = Join-Path $appRoot 'citadelle_data\memory.db-wal'
$shmFile = Join-Path $appRoot 'citadelle_data\memory.db-shm'
$backupDatabase = Join-Path $backupSet 'memory.db'
$backupMarker = Join-Path $backupSet '.current_model'

if (-not (Test-Path -LiteralPath (Join-Path $backupSet 'SUCCESS.txt'))) {
    throw "Jeu de sauvegarde non validé : $backupSet"
}
if (-not (Test-Path -LiteralPath $backupDatabase -PathType Leaf) -or
    -not (Test-Path -LiteralPath $backupMarker -PathType Leaf)) {
    throw "Base ou marqueur absent du jeu : $backupSet"
}

$env:CITADELLE_DB_TO_VERIFY = $backupDatabase
try {
    python -c 'import os, sqlite3; db=sqlite3.connect(os.environ["CITADELLE_DB_TO_VERIFY"]); result=db.execute("PRAGMA integrity_check").fetchone()[0]; db.close(); print("integrity_check:", result); assert result == "ok"'
    if ($LASTEXITCODE -ne 0) { throw 'La base de sauvegarde est invalide.' }
}
finally {
    Remove-Item Env:CITADELLE_DB_TO_VERIFY -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Path $before -Force | Out-Null
Copy-Item -LiteralPath $database -Destination (Join-Path $before 'memory.db')
Copy-Item -LiteralPath $modelMarker -Destination (Join-Path $before '.current_model')
if (Test-Path -LiteralPath $walFile) {
    Copy-Item -LiteralPath $walFile -Destination (Join-Path $before 'memory.db-wal')
    Remove-Item -LiteralPath $walFile -Force
}
if (Test-Path -LiteralPath $shmFile) {
    Copy-Item -LiteralPath $shmFile -Destination (Join-Path $before 'memory.db-shm')
    Remove-Item -LiteralPath $shmFile -Force
}
Copy-Item -LiteralPath $backupDatabase -Destination $database
Copy-Item -LiteralPath $backupMarker -Destination $modelMarker
```

Après la copie, vérifier que le chemin du GGUF indiqué par `.current_model`
existe et reste autorisé par la whitelist. Démarrer `lancer.bat`, vérifier le
login et le chat en local, puis redémarrer Caddy et tester HTTPS. En cas
d'échec, arrêter les services et revenir aux copies `before-restore`; préserver
le jeu de sauvegarde source pour diagnostic.

## Monitoring et seuils d'alerte

- **Proxy** : surveiller `dist\proxy.log`; contrôler les erreurs de démarrage,
  les 5xx et les erreurs de connexion à llamafile.
- **Caddy** : surveiller les journaux JSON et leurs rotations sous
  `C:\ProgramData\LaCitadelle\Caddy\lacitadelle.log`.
- **Disponibilité externe** : configurer UptimeRobot ou Pingdom sur
  `https://<domaine>/login`, sans identifiants. Alerter après trois délais
  d'attente consécutifs.
- **HTTP** : alerte si les réponses 5xx dépassent 1 % sur une fenêtre de cinq
  minutes, avec un volume minimal de requêtes pour éviter les faux positifs.
- **Disque** : alerte si l'espace libre descend sous 10 %; vérifier en
  priorité les journaux et les jeux de sauvegarde, sans supprimer une
  sauvegarde valide automatiquement.
- **Métriques** : consulter le tableau admin et les métriques SQLite
  `inference_metrics`; ne pas exposer l'interface d'administration sans
  authentification.

Les logs et sauvegardes peuvent révéler des métadonnées d'accès ou contenir
des données personnelles; limiter leur accès et leur rétention.

## Incidents

### Port occupé ou erreur 502

Vérifier le propriétaire des ports 80, 443, 8080, 8081 et 2019 avec
`Get-NetTCPConnection`. Ne pas terminer un PID inconnu. Tester les deux
services loopback; Caddy doit cibler uniquement `127.0.0.1:8081`.

### Certificat manquant ou expiré

Vérifier l'heure système, les enregistrements DNS, les règles entrantes 80/443,
la connectivité sortante ACME, les droits sur le répertoire de données Caddy
et ses logs. Les certificats publics sont gérés automatiquement; ne pas
installer la CA locale avec `caddy trust` pour corriger un certificat public.

### Base SQLite corrompue

Arrêter Caddy et l'application, conserver la base endommagée et ses éventuels
fichiers `-wal`/`-shm`, puis restaurer le dernier jeu vérifié. Ne pas lancer
une restauration sur la base active et ne pas supprimer l'original avant le
contrôle du login et des données.

## Retour arrière

La distribution utilisateur ne contient pas Git : un retour arrière se fait
vers la précédente archive ZIP ou release connue comme bonne, pas par
`git checkout` sur le serveur. Conserver le Caddyfile précédent et une
sauvegarde SQLite vérifiée; ne restaurer les données que si nécessaire.

## Références

- [HTTPS automatique Caddy](https://caddyserver.com/docs/automatic-https)
- [Commandes `run`, `start` et `stop`](https://caddyserver.com/docs/command-line)
- [Sauvegarde SQLite `VACUUM INTO`](https://www.sqlite.org/lang_vacuum.html#vacuuminto)
