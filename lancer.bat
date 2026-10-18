@echo off
REM Lance Lacitadelle depuis le dossier du .bat
cd /d "%~dp0"
dist\lacitadelle.llamafile.exe %*
pause