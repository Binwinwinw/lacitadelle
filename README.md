# La Citadelle

Application locale destinée à un public non-technique. La distribution
autonome fournit un webchat Python et télécharge séparément le runtime
llamafile-thin et le modèle GGUF depuis leurs sources officielles.

Voir `dev/docs/OBJECTIF.md` pour le périmètre v1, et `AGENTS.md` pour
les instructions de développement.

## Téléchargement des fichiers requis

Le bootstrap télécharge et vérifie llamafile-thin dans `dist/` (renommé
`llamafile.exe` sous Windows) et le modèle GGUF dans
`dev/tools/vendor/llamafile/` :

    python dev/tools/bootstrap.py

Le modèle fait environ 1,28 Go et le runtime environ 42 Mo. Les
relancements vérifient les checksums et ne retéléchargent pas les fichiers
valides.

Si un fichier est corrompu, le script le supprime et le retélécharge
(mode réparateur). Voir `dev/tools/BOOTSTRAP_CONTRACT.md` pour les
détails et les limites connues.

## Installation et première utilisation

### Prérequis

- Python 3.10+ installé.
- Environ 3 Go d'espace disque libre.
- Connexion internet pour le premier téléchargement.
- Aucun Git requis.

`install.bat` vérifie la présence de Python, mais pas sa version.
Vérifiez manuellement `python --version` : Python 3.10 ou supérieur est requis.

### Parcours rapide (Windows, sans Git)

1. Décompressez `lacitadelle-v2.zip` dans un dossier accessible en écriture.
2. Double-cliquez sur `install.bat`.
3. Une fois l'installation terminée, `lancer.bat` démarre automatiquement.

`install.bat` vérifie Python, télécharge llamafile-thin depuis les releases
Mozilla AI et le modèle GGUF depuis HuggingFace, puis lance `lancer.bat`.
Le navigateur s'ouvre sur `http://localhost:8081`.

**Aucune compilation ni exécution de zipalign sur l'ordinateur utilisateur.**
Un antivirus peut bloquer `dist/llamafile.exe`; autorisez ce fichier si
nécessaire.

**Release GitHub v0.1.0 OBSOLÈTE** : ne pas utiliser son ancien artefact.
Le décideur doit déprécier cette release manuellement.

### Création du premier administrateur

Choisissez une seule des deux méthodes :

1. Inscrivez le premier compte via `/register` : il reçoit le rôle admin.
2. Si aucun administrateur n'existe, créez-en un en lançant :

       python dev/tools/create_admin.py

Ne faites pas les deux : `create_admin.py` échoue si un admin existe déjà.
Après une inscription, connectez-vous avec le mot de passe choisi.
Un compte créé par `create_admin.py` reçoit un mot de passe temporaire à changer
à la première connexion.

### En cas de problème

- **L'antivirus bloque le runtime** : autorisez `dist/llamafile.exe`.
- **Python n'est pas reconnu** : vérifiez que Python 3.10+ est dans le PATH.
- **Le téléchargement échoue** : vérifiez la connexion et relancez
  `python dev/tools/bootstrap.py`.

`dev/tools/setup_lacitadelle.py` reste un outil de build développeur
historique; il ne fait pas partie de la distribution ni de l'installation
utilisateur.

Sur Unix, aucun script d'installation automatique n'est fourni dans cette
version. Le bootstrap peut être lancé avec `python dev/tools/bootstrap.py`.

## Version 3.0 (authentification complète)

V3.0 ajoute le login avec mot de passe (hashé avec scrypt), l'inscription et la
séparation des conversations par utilisateur. Le premier compte inscrit devient
admin, mais aucune route d'administration web n'est disponible en V3.0.

### Lancement

Double-cliquez sur `lancer.bat` à la racine du projet.

Deux fenêtres s'ouvrent :

- **Lacitadelle Server** : serveur llamafile (port 8080).
- **Lacitadelle Proxy** : proxy Python pour le login (port 8081).

Le navigateur s'ouvre sur `http://localhost:8081`.

### Utilisation

1. Créez un compte via `/register` avec un nom d'utilisateur et un mot de passe.
2. Connectez-vous via `/login`.
3. Créez une session avec le bouton « Nouvelle session » et envoyez des messages.
4. Les conversations sont liées à votre compte : après déconnexion puis
  reconnexion, vous retrouvez vos sessions.
5. Déconnectez-vous avec le bouton « Déconnexion » de la barre latérale.

Un compte marqué `must_change_password` est redirigé vers le formulaire de
changement de mot de passe. Les cookies et les sessions côté serveur expirent
après 24 heures.

### Limites V3.0

- **Pas de HTTPS** : le proxy écoute uniquement sur localhost (loopback).
  Ne l'exposez pas sur un réseau.
- **Une seule session de login par utilisateur** : un nouveau login révoque
  le précédent.
- **Pas de routes admin web** : reportées en V3.1, avec HTTPS, CSRF et
  limitation de débit du login.

### Arrêt

Fermez les deux fenêtres « Lacitadelle Server » et « Lacitadelle Proxy ».

## État du projet

- V3.0 : authentification avec mot de passe, proxy local et conversations
  séparées par utilisateur
- Distribution : archive autonome sans Git; llamafile-thin et GGUF séparés

## Structure du dépôt

- `dev/` — code et documentation de La Citadelle
- `lacitadelle-v2.zip` — archive générée par `python -B dev/tools/creer_archive.py`
- `.memory/` — mémoire projet (décisions, instructions)
- `AGENTS.md` — source de vérité des instructions agents
