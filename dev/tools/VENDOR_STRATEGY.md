# Stratégie de vendorisation du binaire llamafile

## Contexte
La v1 utilise un binaire llamafile pré-compilé (Option X, voir dev/docs/BASE_LLAMAFILE.md).
Ce binaire est une dépendance externe, comme `main/`. Il ne doit pas être versionné.
Seul le script qui le télécharge l'est.

## Questions à trancher

### Où stocker le binaire téléchargé ?
TODO — chemin dans le projet (ex. dev/tools/vendor/llamafile/), gitignoré.

### Comment vérifier l'intégrité ?
TODO — checksum SHA-256 officiel de la release, vérifié à chaque téléchargement.

### Comment gérer les mises à jour de version ?
TODO — fichier de config (ex. dev/tools/llamafile_version.txt) contenant
version + URL + checksum, versionné dans Git.

### Que se passe-t-il si le téléchargement échoue ?
TODO — comportement attendu du script (erreur claire, pas de binaire partiel, etc.).

### Que se passe-t-il si le checksum ne correspond pas ?
TODO — refus du binaire, message d'erreur, arrêt du pipeline.