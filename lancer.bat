@echo off
setlocal
REM Lance La Citadelle V2 (llamafile + proxy + navigateur)
cd /d "%~dp0"

echo ======================================
echo   La Citadelle V2 - Demarrage
echo ======================================
echo.

if not exist dist\llamafile.exe (
    echo ERREUR : dist\llamafile.exe introuvable.
    exit /b 1
)

echo Demarrage du serveur llamafile (port 8080)...
start "Lacitadelle Server" dist\llamafile.exe -m dev\tools\vendor\llamafile\Qwen3-1.7B-Q4_K_M.gguf --server --host 127.0.0.1 --port 8080 --nologo --log-timestamps

echo Attente active du serveur llamafile (maximum 120 secondes)...
set /a LLAMA_TRIES=0
:WAIT_LLAMA
curl.exe --silent --fail --connect-timeout 1 --max-time 2 --output NUL http://127.0.0.1:8080/v1/models
if not errorlevel 1 goto LLAMA_READY
set /a LLAMA_TRIES+=1
if %LLAMA_TRIES% GEQ 30 goto LLAMA_TIMEOUT
timeout /t 2 /nobreak >nul
goto WAIT_LLAMA

:LLAMA_TIMEOUT
echo ERREUR : llamafile ne repond pas apres 120 secondes.
exit /b 1

:LLAMA_READY
echo llamafile pret.
if not exist dist mkdir dist

echo Demarrage du proxy de login (port 8081)...
>>dist\proxy.log echo [launcher] Demarrage du proxy %DATE% %TIME%
REM Keep stdout on the proxy console because first-admin setup can print a one-time password.
start "Lacitadelle Proxy" cmd /c "python dev\tools\login_server.py 2>> dist\proxy.log"

echo Attente active du proxy (maximum 60 secondes)...
set /a PROXY_TRIES=0
:WAIT_PROXY
curl.exe --silent --fail --connect-timeout 1 --max-time 2 --output NUL http://127.0.0.1:8081/login
if not errorlevel 1 goto PROXY_READY
set /a PROXY_TRIES+=1
if %PROXY_TRIES% GEQ 15 goto PROXY_TIMEOUT
timeout /t 2 /nobreak >nul
goto WAIT_PROXY

:PROXY_TIMEOUT
echo ERREUR : le proxy ne repond pas apres 60 secondes.
echo Voir dist\proxy.log pour les erreurs du proxy.
exit /b 1

:PROXY_READY
echo Proxy pret.
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
exit /b 0
