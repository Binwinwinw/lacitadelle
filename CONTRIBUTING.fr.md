# Contribuer à La Citadelle

[English](./CONTRIBUTING.md) | **Français**

## Prérequis

- Python 3.10 ou version ultérieure.
- Git.
- Environ 3 Go d’espace disque libre pour le moteur et le modèle.

## Cloner et configurer

```powershell
git clone https://github.com/Binwinwinw/lacitadelle.git
cd lacitadelle
python dev/tools/bootstrap.py
```

Le bootstrap télécharge et vérifie séparément le runtime llamafile-thin et le
GGUF Qwen3-4B Q4_K_M requis. Le modèle n’est pas incorporé au binaire runtime.
Ornith et Qwen3.5 sont des modèles locaux facultatifs que le manifeste actuel
ne télécharge pas automatiquement. Le bootstrap installe le runtime dans
`dist/llamafile.exe` sous Windows,
`dist/llamafile-linux` sous Linux ou `dist/llamafile-macos` sous macOS.
Consultez [BOOTSTRAP_CONTRACT.md](./dev/tools/BOOTSTRAP_CONTRACT.md) pour la
configuration, la validation, le téléchargement et la réparation.

## Exécuter les tests

```powershell
python -m pytest
```

Dernière exécution documentée : **313 tests passés le 2026-11-23 (GO 18)**.
Il s’agit d’un résultat historique, pas d’une exécution des tests dans le
GO 19. Consultez [ETAT-PROJET.md](./dev/docs/ETAT-PROJET.md) pour l’état daté
du projet. Les tests ciblés des helpers HTTP peuvent aussi être lancés avec :

```powershell
python dev/tests/test_http_helpers.py
```

Sous Linux et macOS, utiliser `python3` à la place de `python`.

## Exécuter en développement

Lancez `lancer.bat` sous Windows, `./lancer.sh` sous Linux ou
`lancer.command` sous macOS pour démarrer le serveur de modèle et le proxy web.
Le serveur de modèle écoute sur le port 8080; le proxy web authentifié écoute
sur le port 8081.

Pour démarrer le proxy manuellement, démarrez d’abord le serveur de modèle llamafile sur `127.0.0.1:8080`, puis exécutez :

```powershell
python dev/tools/login_server.py
```

## Générer l’archive de distribution

```powershell
python -B dev/tools/creer_archive.py
```

Cette commande crée `lacitadelle-distribution.zip` à la racine du dépôt. L’archive est publiée comme asset d’une release GitHub.

## Structure du dépôt

- `dev/tools/` — application Python et outils de distribution.
- `dev/tests/` — suite pytest.
- `dev/docs/` — architecture, contrats, périmètre produit et journaux du projet.
- `.memory/` — décisions du projet et instructions des agents.
- `AGENTS.md` — règles de travail des agents et du dépôt.
- `README.md` / `README.fr.md` — guides utilisateur.
- `CONTRIBUTING.md` / `CONTRIBUTING.fr.md` — guides de contribution.

## Documentation de référence

- [AGENTS.md](./AGENTS.md)
- [.memory/decisions.md](./.memory/decisions.md)
- [ARCHITECTURE.md](./dev/docs/ARCHITECTURE.md)
- [OBJECTIF.md](./dev/docs/OBJECTIF.md)
- [ETAT-PROJET.md](./dev/docs/ETAT-PROJET.md)
- [MODELES-TESTES.md](./dev/docs/MODELES-TESTES.md) — évaluations historiques;
  les dates et méthodologies diffèrent.

## Signaler un bogue

Ouvrez une [issue GitHub](https://github.com/Binwinwinw/lacitadelle/issues) et indiquez la version de l’application, le système d’exploitation, les étapes de reproduction, le résultat attendu et le résultat observé. N’incluez pas de mot de passe, de cookie de session ni d’autre secret.
