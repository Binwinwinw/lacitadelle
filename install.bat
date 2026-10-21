@echo off
cd /d "%~dp0"

echo Installation de La Citadelle...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python n'est pas installe.
    pause
    exit /b 1
)
python -B dev\tools\bootstrap.py
if errorlevel 1 (
    echo ERREUR lors du telechargement.
    pause
    exit /b 1
)
echo Installation terminee. Lancement...
timeout /t 3 /nobreak >nul
start "" lancer.bat
exit