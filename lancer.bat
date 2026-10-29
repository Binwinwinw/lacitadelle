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

set "MODEL_PATH="
if exist dist\.current_model (
    set /p MODEL_PATH=<dist\.current_model
)
if not defined MODEL_PATH (
    set "MODEL_PATH=dev\tools\vendor\llamafile\Qwen3-1.7B-Q4_K_M.gguf"
)

if exist "%MODEL_PATH%" goto MODEL_PATH_VALID

echo ERREUR : le modele "%MODEL_PATH%" est introuvable.
echo Tentative de rollback...
python dev\tools\model_health.py --rollback 2>> dist\proxy.log
if errorlevel 1 goto MODEL_PATH_DEFAULT

set "MODEL_PATH="
if exist dist\.current_model set /p MODEL_PATH=<dist\.current_model
if not defined MODEL_PATH goto MODEL_PATH_DEFAULT
if not exist "%MODEL_PATH%" (
    echo ERREUR : le modele restaure "%MODEL_PATH%" est introuvable.
    goto MODEL_PATH_DEFAULT
)
echo Modele restaure : "%MODEL_PATH%"
python dev\tools\model_health.py --check-whitelist "%MODEL_PATH%" 2>> dist\proxy.log
if errorlevel 1 goto MODEL_WHITELIST_DEFAULT
goto MODEL_PATH_READY

:MODEL_PATH_DEFAULT
echo Utilisation du modele par defaut.
set "MODEL_PATH=dev\tools\vendor\llamafile\Qwen3-1.7B-Q4_K_M.gguf"
if not exist "%MODEL_PATH%" (
    echo ERREUR : le modele par defaut "%MODEL_PATH%" est introuvable.
    exit /b 1
)
python dev\tools\model_health.py --check-whitelist "%MODEL_PATH%" 2>> dist\proxy.log
if errorlevel 1 (
    echo ERREUR : le modele par defaut n'est pas dans la whitelist.
    exit /b 1
)
goto MODEL_PATH_READY

:MODEL_PATH_VALID
python dev\tools\model_health.py --check-whitelist "%MODEL_PATH%" 2>> dist\proxy.log
if errorlevel 1 goto MODEL_NOT_WHITELISTED
goto MODEL_PATH_READY

:MODEL_NOT_WHITELISTED
echo ERREUR : le modele n'est pas dans la whitelist.
echo Tentative de rollback...
python dev\tools\model_health.py --rollback 2>> dist\proxy.log
if errorlevel 1 goto MODEL_WHITELIST_DEFAULT
set "MODEL_PATH="
if exist dist\.current_model set /p MODEL_PATH=<dist\.current_model
if not defined MODEL_PATH goto MODEL_WHITELIST_DEFAULT
if not exist "%MODEL_PATH%" goto MODEL_WHITELIST_DEFAULT
python dev\tools\model_health.py --check-whitelist "%MODEL_PATH%" 2>> dist\proxy.log
if errorlevel 1 goto MODEL_WHITELIST_DEFAULT
echo Modele restaure : "%MODEL_PATH%"
goto MODEL_PATH_READY

:MODEL_WHITELIST_DEFAULT
echo Utilisation du modele par defaut.
set "MODEL_PATH=dev\tools\vendor\llamafile\Qwen3-1.7B-Q4_K_M.gguf"
if not exist "%MODEL_PATH%" (
    echo ERREUR : le modele par defaut "%MODEL_PATH%" est introuvable.
    exit /b 1
)
python dev\tools\model_health.py --check-whitelist "%MODEL_PATH%" 2>> dist\proxy.log
if errorlevel 1 (
    echo ERREUR : le modele par defaut n'est pas dans la whitelist.
    exit /b 1
)

:MODEL_PATH_READY
echo Demarrage du serveur llamafile (port 8080)...
start "Lacitadelle Server" dist\llamafile.exe -m "%MODEL_PATH%" --server --host 127.0.0.1 --port 8080 --nologo --log-timestamps --cors-origins http://localhost:8081

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
goto MODEL_LOAD_FAILED

:LLAMA_READY
echo llamafile pret.
echo Verification du modele charge...
python dev\tools\model_health.py --check "%MODEL_PATH%"
if errorlevel 1 goto MODEL_LOAD_FAILED
if not exist dist mkdir dist

echo Demarrage du proxy de login (port 8081)...
>>dist\proxy.log echo [launcher] Demarrage du proxy %DATE% %TIME%
REM Keep stdout on the proxy console because first-admin setup can print a one-time password.
start "Lacitadelle Proxy" cmd /k "python dev\tools\login_server.py 2>> dist\proxy.log"

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

:MODEL_LOAD_FAILED
echo ERREUR : llamafile ne confirme pas le modele configure.
echo Restauration du chemin precedent...
python dev\tools\model_health.py --rollback 2>> dist\proxy.log
if errorlevel 1 (
    echo ERREUR : rollback impossible. Voir dist\.current_model et la base locale.
) else (
    echo Chemin precedent restaure dans dist\.current_model.
)
echo Fermez la fenetre "Lacitadelle Server", puis relancez lancer.bat.
exit /b 1
