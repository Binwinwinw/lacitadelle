@echo off
cd /d "%~dp0"

echo Installation de La Citadelle...
python --version >nul 2>&1
if errorlevel 1 goto python_missing
python --version

echo.
echo [1/2] Telechargement et verification des dependances...
python dev\tools\bootstrap.py
if errorlevel 1 goto bootstrap_failed

echo.
echo [2/2] Construction du fichier Lacitadelle...
python -B dev\tools\setup_lacitadelle.py
if errorlevel 1 goto setup_failed

echo.
echo Installation terminee.
choice /C ON /M "Lancer lancer.bat maintenant?"
if errorlevel 2 exit /b 0
start "" "%~dp0lancer.bat"
exit /b 0

:python_missing
echo ERREUR : Python 3.10+ est requis et doit etre disponible dans PATH.
goto failed

:bootstrap_failed
echo ERREUR : le telechargement ou la verification des dependances a echoue.
goto failed

:setup_failed
echo ERREUR : la construction du fichier Lacitadelle a echoue.

:failed
pause
exit /b 1