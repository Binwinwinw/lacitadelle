# Runbook

## Réinitialiser un compte administrateur

À utiliser si un compte admin actif est inaccessible et que la réinitialisation
par l'interface n'est pas possible. Arrêter l'application avant la procédure.

1. Fermer les fenêtres de `lancer.bat`.
2. Créer `%TEMP%\reset_admin.py` à partir du script ci-dessous.
3. Depuis la racine du dépôt, exécuter `python "%TEMP%\reset_admin.py"`.
4. Noter le mot de passe temporaire affiché une seule fois dans la console.
5. Relancer `lancer.bat`, se connecter avec le compte admin et changer le mot
   de passe lorsque l'interface le demande.
6. Supprimer `%TEMP%\reset_admin.py`. Ne pas enregistrer le mot de passe dans
   un fichier, un log ou un ticket.

```python
import secrets
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "dev" / "tools"))
from citadelle_memory import DB_PATH, hash_password

username = input("Nom du compte admin : ").strip()
if not DB_PATH.is_file():
    raise SystemExit(f"Base de données introuvable : {DB_PATH}")

temporary_password = secrets.token_urlsafe(18)
with sqlite3.connect(DB_PATH) as connection:
    result = connection.execute(
        "UPDATE users SET password_hash = ?, must_change_password = 1 "
        "WHERE username = ? AND role = 'admin' AND is_active = 1",
        (hash_password(temporary_password), username),
    )
    if result.rowcount != 1:
        raise SystemExit("Compte admin actif introuvable; aucune modification.")

print(f"Mot de passe temporaire (à noter une seule fois) : {temporary_password}")
```

Le hash utilise `citadelle_memory.hash_password` et ses paramètres scrypt V3.
Le script ne change ni le rôle, ni l'état actif, ni les conversations; l'arrêt
du proxy invalide les sessions d'authentification gardées en mémoire.

## Test manuel 10C — Création initiale d'un admin

Ne pas exécuter ce test contre la base réelle. Il démarre le proxy sur le port
8081 et vérifie le changement obligatoire du mot de passe initial.

1. Arrêter La Citadelle et vérifier que le port 8081 est libre. Ne pas arrêter
   un processus inconnu pour libérer le port.
2. Depuis la racine du dépôt, ouvrir PowerShell et préparer une copie isolée
   contenant uniquement les fichiers nécessaires au proxy :

   ```powershell
   $testRoot = Join-Path $env:TEMP (
       "citadelle-10c-test-" + [guid]::NewGuid().ToString("N")
   )
   New-Item -ItemType Directory -Force "$testRoot\dev\tools\web" | Out-Null
   New-Item -ItemType Directory -Force "$testRoot\citadelle_data" | Out-Null
   Copy-Item dev\tools\login_server.py "$testRoot\dev\tools\"
   Copy-Item dev\tools\citadelle_memory.py "$testRoot\dev\tools\"
   Copy-Item dev\tools\model_health.py "$testRoot\dev\tools\"
   Copy-Item dev\tools\web\* "$testRoot\dev\tools\web\" -Recurse
   ```

3. Démarrer le proxy depuis cette copie; sa base vide sera créée sous
   `$testRoot\citadelle_data`, sans toucher à la base réelle :

   ```powershell
   Push-Location $testRoot
   python dev\tools\login_server.py
   ```

4. Noter le mot de passe initial `superadmin` affiché une seule fois dans la
   console. Ouvrir `http://localhost:8081`, se connecter et vérifier que
   l'interface impose le changement de mot de passe.
5. Choisir un mot de passe temporaire propre au test, le modifier, puis
   vérifier que la page de changement est quittée et que le compte peut se
   reconnecter avec le nouveau mot de passe.
6. Arrêter le proxy avec Ctrl+C, revenir au dépôt et supprimer uniquement la
   copie temporaire créée pour ce test :

   ```powershell
   Pop-Location
   Remove-Item -LiteralPath $testRoot -Recurse -Force
   ```

Ne pas copier de vraie base dans cette arborescence et ne pas consigner le mot
de passe dans un fichier, un log ou un ticket. Si la copie ou le port isolé ne
peut pas être préparé, reporter le test; ne pas basculer vers la base réelle.

## Limites de concurrence

Serveur mono-thread : une requête lente bloque les suivantes.

Limite connue : N utilisateurs simultanés non testé.

Dette : passage à `ThreadingHTTPServer` = GO CONCURRENCE dédié. Il devra
traiter SQLite WAL, l'état de session thread-safe et les tests de charge avant
toute promesse de capacité concurrente.
