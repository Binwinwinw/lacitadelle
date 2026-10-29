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
