@echo off
:: ============================================================
:: BabySteps Digital School — Dev Startup Script
:: Starts: Django backend (8000) + React frontend (3000)
:: Optional: Ollama LLM (11434) if not already running
:: ============================================================
setlocal EnableDelayedExpansion

set "PROJECT_DIR=D:\Sridhar\Projects\BabyStepsDigitalSchool"
set "FRONTEND_DIR=%PROJECT_DIR%\frontend"
set "PYTHON=D:\Program Files\Python310\python.exe"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=3000"
set "OLLAMA_PORT=11434"

title BabySteps Digital School — Dev Launcher
color 0A

echo.
echo  =====================================================
echo   BabySteps Digital School  ^|  Dev Environment
echo  =====================================================
echo.

:: ── 1. Check Python ─────────────────────────────────────
if not exist "%PYTHON%" (
    echo  [ERROR] Python not found at: %PYTHON%
    echo  Please update PYTHON path in this script.
    goto :error_exit
)
echo  [OK] Python  ^|  %PYTHON%

:: ── 2. Check Node / npm ─────────────────────────────────
where npm >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] npm not found. Please install Node.js.
    goto :error_exit
)
echo  [OK] npm     ^|  found in PATH

:: ── 3. Check manage.py ──────────────────────────────────
if not exist "%PROJECT_DIR%\manage.py" (
    echo  [ERROR] manage.py not found in: %PROJECT_DIR%
    goto :error_exit
)
echo  [OK] Django  ^|  manage.py found

:: ── 4. Check frontend ───────────────────────────────────
if not exist "%FRONTEND_DIR%\package.json" (
    echo  [ERROR] package.json not found in: %FRONTEND_DIR%
    goto :error_exit
)
echo  [OK] React   ^|  package.json found
echo.

:: ── 5. Port conflict checks ──────────────────────────────
call :check_port %BACKEND_PORT% "Django backend"
if errorlevel 1 goto :error_exit

call :check_port %FRONTEND_PORT% "React frontend"
if errorlevel 1 goto :error_exit

:: ── 6. Ollama — start if not running ────────────────────
netstat -an | findstr ":%OLLAMA_PORT% " | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo  [INFO] Ollama not detected on port %OLLAMA_PORT%.
    where ollama >nul 2>&1
    if not errorlevel 1 (
        echo  [INFO] Starting Ollama LLM server...
        start "Ollama LLM" /min cmd /k "ollama serve"
        timeout /t 3 /nobreak >nul
        echo  [OK] Ollama  ^|  starting on port %OLLAMA_PORT%
    ) else (
        echo  [WARN] Ollama not installed — LLM features will be unavailable.
    )
) else (
    echo  [OK] Ollama  ^|  already running on port %OLLAMA_PORT%
)
echo.

:: ── 7. Run pending Django migrations ─────────────────────
echo  Checking Django migrations...
"%PYTHON%" "%PROJECT_DIR%\manage.py" migrate --run-syncdb 2>&1 | findstr /i "applying\|no migrations\|OK"
echo.

:: ── 8. Start Django backend ──────────────────────────────
echo  Starting Django backend on http://localhost:%BACKEND_PORT% ...
start "BabySteps Backend (Django :8000)" cmd /k ^
    "color 0B && title BabySteps Backend (Django :8000) && cd /d "%PROJECT_DIR%" && "%PYTHON%" manage.py runserver %BACKEND_PORT%"

:: Brief pause so Django socket binds before frontend starts
timeout /t 2 /nobreak >nul

:: ── 9. Start React frontend ───────────────────────────────
echo  Starting React frontend on http://localhost:%FRONTEND_PORT% ...
start "BabySteps Frontend (React :3000)" cmd /k ^
    "color 0D && title BabySteps Frontend (React :3000) && cd /d "%FRONTEND_DIR%" && npm start"

:: ── 10. Summary ───────────────────────────────────────────
echo.
echo  =====================================================
echo   Services launching in separate windows
echo  =====================================================
echo   Frontend  : http://localhost:%FRONTEND_PORT%
echo   Backend   : http://localhost:%BACKEND_PORT%
echo   Admin     : http://localhost:%BACKEND_PORT%/admin/
echo   API root  : http://localhost:%BACKEND_PORT%/api/
echo  =====================================================
echo.
echo  Close the individual windows to stop each service.
echo  Press any key to close this launcher...
echo.
pause >nul
goto :eof

:: ── Helper: check if port is already bound ───────────────
:check_port
    netstat -an | findstr ":%~1 " | findstr "LISTENING" >nul 2>&1
    if not errorlevel 1 (
        echo  [ERROR] Port %~1 is already in use (%~2^).
        echo         Stop the existing process and try again.
        exit /b 1
    )
    exit /b 0

:error_exit
    echo.
    echo  Startup aborted. Fix the errors above and re-run.
    echo.
    pause
    exit /b 1
