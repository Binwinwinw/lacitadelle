#!/usr/bin/env python3
"""Bootstrap : télécharge et vérifie les binaires llamafile.

Lit dev/tools/llamafile_config.json, télécharge les assets marqués
required=true, vérifie leur SHA-256, les stocke dans
dev/tools/vendor/llamafile/. Échoue proprement en cas d'erreur.

Voir dev/tools/BOOTSTRAP_CONTRACT.md pour le contrat complet.

Usage :
    python dev/tools/bootstrap.py

Aucune dépendance externe. Python 3.10+ requis.

Note Windows : si les accents dans les messages provoquent une
UnicodeEncodeError, lancer `set PYTHONIOENCODING=utf-8` avant
(ou `chcp 65001` pour passer le terminal en UTF-8).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# Chemins (relatifs au fichier, pas au cwd)
TOOLS_DIR = Path(__file__).resolve().parent
CONFIG_PATH = TOOLS_DIR / "llamafile_config.json"
VENDOR_DIR = TOOLS_DIR / "vendor" / "llamafile"

# Paramètres
CHUNK_SIZE = 64 * 1024
HTTP_TIMEOUT = 60
SHA256_LEN = 64

# Codes de sortie
EXIT_OK = 0
EXIT_ASSET_FAILED = 1
EXIT_CONFIG_ERROR = 2


class BootstrapError(Exception):
    """Erreur attendue du bootstrap (config, réseau, checksum).

    Les BootstrapError sont signalées à l'utilisateur sans traceback.
    Les autres exceptions indiquent un bug de programmation.
    """


def load_config() -> dict[str, Any]:
    """Charge et valide la configuration JSON.

    Voir BOOTSTRAP_CONTRACT.md, section « Contrat de la configuration ».

    Raises:
        BootstrapError: si le fichier est absent, invalide, ou viole le schéma.
    """
    if not CONFIG_PATH.is_file():
        raise BootstrapError(
            f"Configuration absente : {CONFIG_PATH}. "
            f"Le fichier dev/tools/llamafile_config.json est requis."
        )

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise BootstrapError(
            f"Configuration JSON invalide ({CONFIG_PATH}) : {e}"
        ) from e

    if not isinstance(config, dict):
        raise BootstrapError(
            f"Configuration invalide : la racine doit être un objet JSON, "
            f"trouvé {type(config).__name__}."
        )

    # Clé version obligatoire, non vide
    version = config.get("version")
    if not isinstance(version, str) or not version.strip():
        raise BootstrapError(
            "Configuration invalide : 'version' doit être une chaîne non vide."
        )

    # Clé assets obligatoire, dict non vide
    assets = config.get("assets")
    if not isinstance(assets, dict) or not assets:
        raise BootstrapError(
            "Configuration invalide : 'assets' doit être un objet JSON non vide."
        )

    # Validation de chaque asset
    for name, meta in assets.items():
        if not isinstance(name, str) or not name.strip():
            raise BootstrapError(
                f"Configuration invalide : nom d'asset vide ou non-chaîne."
            )
        if not isinstance(meta, dict):
            raise BootstrapError(
                f"Configuration invalide [asset '{name}'] : la valeur doit être un objet JSON."
            )

        url = meta.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise BootstrapError(
                f"Configuration invalide [asset '{name}'] : 'url' doit être une "
                f"chaîne commençant par 'https://' (trouvé : {url!r})."
            )

        sha256 = meta.get("sha256")
        if not isinstance(sha256, str) or len(sha256) != SHA256_LEN:
            raise BootstrapError(
                f"Configuration invalide [asset '{name}'] : 'sha256' doit faire "
                f"{SHA256_LEN} caractères (trouvé : {len(sha256) if isinstance(sha256, str) else 'non-chaîne'})."
            )
        if not all(c in "0123456789abcdefABCDEF" for c in sha256):
            raise BootstrapError(
                f"Configuration invalide [asset '{name}'] : 'sha256' doit être hexadécimal."
            )

        filename = meta.get("filename")
        if not isinstance(filename, str) or not filename.strip():
            raise BootstrapError(
                f"Configuration invalide [asset '{name}'] : 'filename' doit être une chaîne non vide."
            )
        if "/" in filename or "\\" in filename or ".." in filename:
            raise BootstrapError(
                f"Configuration invalide [asset '{name}'] : 'filename' ne doit pas "
                f"contenir '/', '\\' ou '..' (trouvé : {filename!r})."
            )

        required = meta.get("required")
        if not isinstance(required, bool):
            raise BootstrapError(
                f"Configuration invalide [asset '{name}'] : 'required' doit être un booléen strict."
            )

    return config


def compute_sha256(path: Path) -> str:
    """Calcule le SHA-256 d'un fichier en streaming.

    Retourne la représentation hexadécimale en minuscules.
    Compatible Python 3.10 (pas de hashlib.file_digest).

    Raises:
        BootstrapError: si le fichier est absent ou illisible.
    """
    if not path.is_file():
        raise BootstrapError(
            f"Fichier absent pour calcul SHA-256 : {path}"
        )
    sha = hashlib.sha256()
    try:
        with path.open("rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                sha.update(chunk)
    except OSError as e:
        raise BootstrapError(
            f"Erreur de lecture pour calcul SHA-256 ({path}) : {e}"
        ) from e
    return sha.hexdigest()


def verify_sha256(path: Path, expected: str) -> None:
    """Vérifie le SHA-256 d'un fichier.

    Comparaison insensible à la casse (le SHA-256 en config peut être
    en majuscules, on normalise en minuscules).

    Raises:
        BootstrapError: si le checksum ne correspond pas.
    """
    actual = compute_sha256(path)
    if actual.lower() != expected.lower():
        raise BootstrapError(
            f"Checksum invalide pour {path} : "
            f"attendu {expected}, calculé {actual}"
        )


def _cleanup_partial(path: Path) -> None:
    """Supprime un fichier partiel s'il existe. Ignore les erreurs."""
    try:
        if path.exists():
            path.unlink()
    except OSError:
        # On ignore : le nettoyage est best-effort.
        pass


def download(url: str, dest: Path) -> None:
    """Télécharge `url` vers `dest` en streaming.

    Écrit vers le chemin exact fourni (le caller est responsable du
    temporaire et de la publication atomique).

    Raises:
        BootstrapError: sur HTTPError, URLError, ou timeout.
    """
    # S'assurer que le dossier parent existe
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "LaCitadelle-bootstrap/1.0"},
        )
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
            with dest.open("wb") as f:
                while chunk := response.read(CHUNK_SIZE):
                    f.write(chunk)
    except urllib.error.HTTPError as e:
        # HTTPError hérite de URLError : traiter en premier pour préserver
        # le code HTTP dans le message.
        _cleanup_partial(dest)
        raise BootstrapError(
            f"Erreur HTTP lors du téléchargement de {url} : "
            f"{e.code} {e.reason}"
        ) from e
    except urllib.error.URLError as e:
        _cleanup_partial(dest)
        raise BootstrapError(
            f"Erreur réseau lors du téléchargement de {url} : {e.reason}"
        ) from e
    except (TimeoutError, OSError) as e:
        _cleanup_partial(dest)
        raise BootstrapError(
            f"Erreur d'E/S lors du téléchargement de {url} : {e}"
        ) from e


def process_asset(name: str, meta: dict[str, Any]) -> None:
    """Traite un asset : télécharge si absent, répare si corrompu, vérifie.

    Cycle (mode réparateur) :
      1. Fichier final présent + checksum OK → rien à faire.
      2. Fichier final présent + checksum KO → suppression + téléchargement
         vers temporaire + vérification + publication atomique.
      3. Fichier final absent → téléchargement vers temporaire + vérification
         + publication atomique.

    Une seule tentative de réparation. Pas de boucle de retry.

    Raises:
        BootstrapError: sur tout échec.
    """
    url = meta["url"]
    expected_sha = meta["sha256"]
    filename = meta["filename"]
    final_path = VENDOR_DIR / filename
    temp_path = VENDOR_DIR / f".tmp-{filename}-{os.getpid()}"

    # Cas 1 : fichier final présent
    if final_path.is_file():
        try:
            verify_sha256(final_path, expected_sha)
            print(f"[OK] {name} : déjà présent et valide ({filename})")
            return
        except BootstrapError:
            # Mode réparateur : suppression + retéléchargement
            print(
                f"[REPARATION] {name} : checksum invalide, "
                f"réparation en cours ({filename})",
                file=sys.stderr,
            )
            try:
                final_path.unlink()
            except OSError as e:
                raise BootstrapError(
                    f"Impossible de supprimer le fichier corrompu "
                    f"{final_path} : {e}"
                ) from e

    # Cas 2/3 : téléchargement vers temporaire
    print(f"[DOWNLOAD] {name} : téléchargement depuis {url}")
    try:
        download(url, temp_path)
        verify_sha256(temp_path, expected_sha)
    except BootstrapError as e:
        # Nettoyage du temporaire en cas d'échec
        _cleanup_partial(temp_path)
        raise BootstrapError(
            f"Réparation échouée pour {name} ({filename}) : {e}"
        ) from e

    # Publication atomique
    try:
        temp_path.rename(final_path)
    except OSError as e:
        _cleanup_partial(temp_path)
        raise BootstrapError(
            f"Impossible de publier {final_path} : {e}"
        ) from e

    print(f"[OK] {name} : téléchargé et vérifié ({filename})")


def main() -> int:
    """Point d'entrée. Retourne le code de sortie."""
    try:
        config = load_config()
    except BootstrapError as e:
        print(f"ERREUR [config] : {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    assets = config["assets"]
    required = [
        (name, meta) for name, meta in assets.items()
        if meta.get("required", False) is True
    ]

    if not required:
        print("Aucun asset requis dans la configuration.")
        return EXIT_OK

    print(f"Bootstrap : {len(required)} asset(s) requis à traiter.")
    print(f"Destination : {VENDOR_DIR}")
    print()

    failures = []
    for name, meta in required:
        try:
            process_asset(name, meta)
        except BootstrapError as e:
            failures.append((name, str(e)))
            print(f"ERREUR [{name}] : {e}", file=sys.stderr)

    print()
    if failures:
        print(
            f"Résumé : {len(required) - len(failures)} OK, "
            f"{len(failures)} échec(s)",
            file=sys.stderr,
        )
        return EXIT_ASSET_FAILED

    print(f"Résumé : {len(required)} asset(s) traité(s) avec succès.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())