@echo off
REM Lance La Citadelle V2 (llamafile + proxy + navigateur)
cd /d "%~dp0"

echo ======================================
echo   La Citadelle V2 - Demarrage
echo ======================================
echo.

echo Demarrage du serveur llamafile (port 8080)...
start "Lacitadelle Server" dist\llamafile.exe -m dev\tools\vendor\llamafile\Qwen3-1.7B-Q4_K_M.gguf --server --host 127.0.0.1 --port 8080 --nologo --log-timestamps

echo Attente du serveur (20 secondes)...
timeout /t 20 /nobreak >nul

echo Demarrage du proxy de login (port 8081)...
start "Lacitadelle Proxy" python dev\tools\login_server.py

echo Attente du proxy (3 secondes)...
timeout /t 3 /nobreak >nul

echo Ouverture de http://localhost:8081...
start http://localhost:8081

echo.
echo ======================================
echo   La Citadelle V2 est prete.
echo ======================================
echo.
echo Deux fenetres sont ouvertes :
echo   - "Lacitadelle Server" (llamafile, port 8080)
echo   - "Lacitadelle Proxy" (login, port 8081)
echo.
echo Pour arreter, fermez les deux fenetres.
echo.
timeout /t 5 /nobreak >nul
exit
