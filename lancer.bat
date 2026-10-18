@echo off
REM Lance Lacitadelle depuis le dossier du .bat
cd /d "%~dp0"

echo Démarrage du serveur Lacitadelle...
echo Une fois le serveur prêt, le navigateur s'ouvrira automatiquement.

REM Lance le serveur en arrière-plan (start sans /wait)
start "Lacitadelle Server" dist\lacitadelle.llamafile.exe

REM Attend 3 secondes que le serveur démarre
timeout /t 3 /nobreak >nul

REM Ouvre le navigateur
start http://localhost:8080

echo.
echo Le serveur tourne dans une fenêtre séparée.
echo Fermez la fenêtre "Lacitadelle Server" pour arrêter le serveur.
echo.
pause
