# La Citadelle

[English](./README.md) | **Français**

La Citadelle est une application locale de chat avec une IA. Vos conversations sont traitées sur votre appareil par un modèle local et ne sont pas envoyées à un service cloud. Lors de la première installation, l’application télécharge le moteur et le modèle depuis leurs sources officielles.

## Installation

### Prérequis

- Windows 10 ou version ultérieure.
- Python 3.10 ou version ultérieure.
- Environ 3 Go d’espace disque libre.
- Une connexion Internet pour le premier lancement.
- Git n’est pas requis.

### Étapes

1. Téléchargez la dernière archive depuis les [releases GitHub](https://github.com/Binwinwinw/lacitadelle/releases/latest) : le fichier s’appelle `lacitadelle-distribution.zip`.
2. Décompressez-la dans un dossier où vous avez le droit d’écrire.
3. Double-cliquez sur `install.bat`. Le script vérifie que Python est disponible, télécharge le moteur llamafile (environ 42 Mo) et le modèle Qwen3 (environ 1,28 Go), vérifie leurs sommes de contrôle, puis lance `lancer.bat`.
4. Votre navigateur s’ouvre sur `http://localhost:8081`. Choisissez **Créer un compte**, puis connectez-vous.
5. Commencez à discuter.

Le premier lancement peut prendre plusieurs minutes pendant le téléchargement du moteur et du modèle et le chargement du modèle. Les lancements suivants sont beaucoup plus rapides.

## Utilisation

Créez un compte, connectez-vous, puis choisissez **+ Nouvelle session** pour démarrer une conversation. Vos conversations sont enregistrées localement et restent accessibles lors de vos prochaines connexions.

### Comptes et gestion des modèles

- Le compte initial s’appelle `superadmin`, mais son rôle applicatif est
  `admin` : il n’existe pas de rôle superadmin distinct.
- Les admins peuvent gérer les chemins GGUF autorisés et choisir le modèle
  actif depuis **Paramètres**. Le modèle sélectionné sera chargé au prochain
  démarrage de `lancer.bat`.
- Les utilisateurs peuvent discuter et accéder uniquement à leurs propres
  conversations.

## Limites connues

- Le serveur Python est mono-thread : une requête lente bloque les suivantes.
- Limite connue : le nombre d’utilisateurs simultanés n’a pas été testé.
  Les tests de charge concurrents et le passage à `ThreadingHTTPServer`
  nécessitent un GO CONCURRENCE dédié.
- Le test de charge automatisé vérifie 100 connexions séquentielles
  (6,9 secondes sur la machine testée; limite de 10 secondes). Il ne mesure
  pas les chats ou requêtes modèle simultanés; le temps varie selon la machine.

## Sécurité

Le proxy web écoute sur `127.0.0.1:8081` et le serveur de modèle sur
`127.0.0.1:8080`. Le serveur de modèle n’accepte les requêtes CORS du navigateur
que depuis `http://localhost:8081`; l’interface utilise le proxy Python.
CORS ne remplace pas un pare-feu : les programmes locaux peuvent toujours
accéder à l’adresse loopback. N’exposez pas La Citadelle à un réseau ni à
Internet. La version locale utilise HTTP; un accès réseau en production exige
HTTPS et les protections supplémentaires prévues par le projet.

## Arrêter La Citadelle

Fermez les deux fenêtres de votre terminal :

- **Lacitadelle Server** — serveur de modèle sur le port 8080.
- **Lacitadelle Proxy** — interface web et authentification sur le port 8081.

## Dépannage

- **Si votre antivirus bloque `dist\llamafile.exe` :** vérifiez la quarantaine de l’antivirus et autorisez le fichier si vous faites confiance à cette installation.
- **Python n’est pas reconnu :** installez Python 3.10 ou version ultérieure et vérifiez que `python` est disponible dans le PATH.
- **Un téléchargement échoue :** vérifiez votre connexion Internet et relancez `install.bat`.
- **Le navigateur ne s’ouvre pas :** ouvrez manuellement `http://localhost:8081` après l’installation.
- **Un port est déjà utilisé :** fermez les fenêtres d’une instance précédente,
  puis réessayez. N’exposez pas les services sur une autre interface réseau.
- **Le modèle est introuvable :** relancez `install.bat` pour vérifier ou
  télécharger le moteur et le modèle par défaut. Un admin ne peut sélectionner
  qu’un modèle existant dans la liste autorisée.
- **Le compte admin est inaccessible :** arrêtez l’application et suivez la
  procédure de réinitialisation isolée dans
  [`dev/docs/RUNBOOK.md`](./dev/docs/RUNBOOK.md).

## Contribuer

Consultez [CONTRIBUTING.fr.md](./CONTRIBUTING.fr.md) pour configurer l’environnement de développement et contribuer au projet.

## Licence

La Citadelle est distribuée sous licence Apache 2.0. Consultez [LICENSE](./LICENSE).
