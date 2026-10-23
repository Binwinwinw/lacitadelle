## 1. Produit livré à l'utilisateur

Le produit livré comprend :

- le runtime llamafile-thin 0.10.6, téléchargé dans `dist/` et renommé
  `llamafile.exe` sous Windows ;
- le modèle GGUF externe Qwen3-1.7B Q4_K_M, téléchargé dans
  `dev/tools/vendor/llamafile/` ;
- un proxy Python local (`login_server.py`) et un webchat.

La distribution est une archive ZIP autonome, sans Git ni binaire intégré.
L'utilisateur l'extrait, lance `install.bat`, puis `lancer.bat`. Le navigateur
ouvre le webchat sur `http://localhost:8081`.

La release GitHub `v0.1.0` a été supprimée. La nouvelle release
`v3-distribution` est prévue après la Phase 7E-Lot3.

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

llamafile est le runtime d'inférence. Le bootstrap télécharge le runtime
llamafile-thin 0.10.6 depuis la release upstream mozilla-ai/llamafile et le
GGUF séparément depuis Hugging Face. Aucun assemblage par `zipalign` n'est
effectué sur le parcours utilisateur.

## 5. Famille de produit visée

Famille 2 : application Python avec runtime external, distribuée dans une
archive ZIP autonome sans Git ni binaires pré-téléchargés.

Dans ce document, **distribution V3** désigne l'archive ZIP et son parcours
utilisateur. Les numéros **V3.0**, **V3.1** et **V3.2** désignent les versions
du périmètre d'authentification et d'administration, pas les versions de
l'archive.

## 6. Périmètre et non-objectifs

- Authentification V3.0 : login local et webchat, sans routes d'administration.
- Authentification V3.1 : routes d'administration, HTTPS, CSRF et rate limiting.
- Authentification V3.2 : multi-admin.
- V2+ : détection GPU.
- Pas de tool calling, d'agent PC ni de modification du code C++ de
  llamafile dans le périmètre actuel.

## 7. Décisions dérivées

- v1 = distribution external : runtime préconstruit, GGUF téléchargé séparément,
  proxy Python local et webchat.
- Le runtime llamafile-thin et le modèle GGUF sont téléchargés et vérifiés par
  checksum lors de l'installation ; ils sont ensuite utilisés hors ligne.
- Le parcours utilisateur est : extraction de l'archive, `install.bat`, puis
  `lancer.bat`.
- Python est requis pour l'installation et le proxy.
- L'administration web est reportée en V3.1 ; le multi-admin en V3.2.
