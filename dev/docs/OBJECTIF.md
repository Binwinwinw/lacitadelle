## 1. Produit livré à l'utilisateur

Le produit livré comprend :

- un runtime `.llamafile` préconstruit (environ 44 Mo) ;
- un modèle GGUF externe Qwen3-1.7B Q4_K_M (environ 1,28 Go) ;
- un proxy Python local (`login_server.py`) et un webchat.

L'utilisateur clone le dépôt, lance `install.bat`, puis `lancer.bat`.
Le navigateur ouvre le webchat sur `http://localhost:8081`.

## 2. Public cible

Utilisateur non-technique souhaitant une IA locale. L'interface livrée est un
webchat local servi par le proxy Python.

## 3. Contrainte d'exécution

Python 3.10+ requis chez l'utilisateur : OUI (bootstrap et proxy).
Réseau requis au premier lancement : OUI (runtime et GGUF téléchargés).
Réseau requis après installation : NON ; les services communiquent en local.
Parcours d'installation automatisé : Windows 10+ (`install.bat`).
Le runtime llamafile prend en charge macOS, Windows, Linux et BSD ; aucun
script d'installation Unix n'est fourni actuellement.

## 4. Rapport à llamafile upstream (mozilla-ai/llamafile)

llamafile est le RUNTIME et le FORMAT de distribution.
La Citadelle produit des llamafiles personnalisés via un pipeline Python de fabrication, à partir d'assets upstream précompilés et d'un GGUF.

## 5. Famille de produit visée

Famille 2 (application Python packagée + runtime external) avec une
distribution préconstruite : le `.llamafile` est fourni via GitHub Releases.

## 6. Périmètre et non-objectifs

- V3.0 : pas de routes d'administration web ; reportées en V3.1.
- V3.1 : HTTPS, CSRF, rate limiting et routes d'administration.
- V3.2 : multi-admin.
- V2+ : détection GPU.
- Pas de tool calling, d'agent PC ni de modification du code C++ de
  llamafile dans le périmètre actuel.

## 7. Décisions dérivées

- v1 = distribution external : runtime préconstruit, GGUF téléchargé séparément,
  proxy Python local et webchat.
- Python est requis pour l'installation et le proxy ; le modèle est téléchargé
  au premier lancement puis utilisé hors ligne.
- L'administration web est reportée en V3.1 ; le multi-admin en V3.2.
