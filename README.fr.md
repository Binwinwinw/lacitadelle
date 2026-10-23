# La Citadelle

[English](./README.md) | **Français**

La Citadelle est une application locale de clavardage avec une IA. Vos conversations sont traitées sur votre appareil par un modèle local et ne sont pas envoyées à un service cloud. Lors de la première installation, l’application télécharge le moteur et le modèle depuis leurs sources officielles.

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

## Sécurité

L’interface web et le serveur de modèle écoutent uniquement sur votre ordinateur. N’exposez pas La Citadelle à un réseau ni à Internet.

## Arrêter La Citadelle

Fermez les deux fenêtres de commande :

- **Lacitadelle Server** — serveur de modèle sur le port 8080.
- **Lacitadelle Proxy** — interface web et authentification sur le port 8081.

## Dépannage

- **L’antivirus bloque `dist\llamafile.exe` :** vérifiez la quarantaine de l’antivirus et autorisez le fichier si vous faites confiance à cette installation.
- **Python n’est pas reconnu :** installez Python 3.10 ou version ultérieure et vérifiez que `python` est disponible dans le PATH.
- **Un téléchargement échoue :** vérifiez votre connexion Internet et relancez `install.bat`.
- **Le navigateur ne s’ouvre pas :** ouvrez manuellement `http://localhost:8081` après l’installation.

## Contribuer

Consultez [CONTRIBUTING.fr.md](./CONTRIBUTING.fr.md) pour configurer l’environnement de développement et contribuer au projet.

## Licence

La Citadelle est distribuée sous licence Apache 2.0. Consultez [LICENSE](./LICENSE).
