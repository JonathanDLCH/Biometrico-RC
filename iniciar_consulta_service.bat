@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=%~dp0venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=%~dp0env\Scripts\python.exe"
set "LOGIN_URL=http://127.0.0.1:8000/accounts/login/"

if not exist "%PYTHON%" (
    echo No se encontro Python en .venv, venv o env.
    echo Crea el entorno virtual e instala requirements.txt antes de continuar.
    pause
    exit /b 1
)

set "DJANGO_DEBUG=true"
set "DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1"

"%PYTHON%" manage.py check
if errorlevel 1 (
    echo Django encontro errores de configuracion.
    pause
    exit /b 1
)

start "Consulta Service - Django" /D "%~dp0" "%PYTHON%" manage.py runserver 127.0.0.1:8000

for /L %%i in (1,1,30) do (
    powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -Uri '%LOGIN_URL%' -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
    if not errorlevel 1 goto open_browser
    timeout /t 1 /nobreak >nul
)

echo El servidor no respondio. Revisa la ventana de Django para ver el error.
pause
exit /b 1

:open_browser
start "" "%LOGIN_URL%"
exit /b 0