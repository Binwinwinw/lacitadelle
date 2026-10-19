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
echo ======================================
echo   Installation terminee avec succes !
echo ======================================
echo.
echo Lancement de La Citadelle dans 3 secondes...
echo (le navigateur va s'ouvrir automatiquement)
echo.
timeout /t 3 /nobreak >nul

start "" lancer.bat
exit

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