@echo off
setlocal EnableExtensions

cd /d "%~dp0.."

set "VENV_DIR=%CD%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "REQUIREMENTS=%CD%\requirements.txt"
set "ENV_EXAMPLE=%CD%\.env.example"
set "ENV_FILE=%CD%\.env"

if not exist "%VENV_PYTHON%" (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        python -m venv "%VENV_DIR%"
    ) else (
        where py >nul 2>nul
        if %errorlevel% equ 0 (
            py -3 -m venv "%VENV_DIR%"
        ) else (
            echo Python is not available in PATH. Install Python 3.10+ first.
            pause
            exit /b 1
        )
    )
)

"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :fail

"%VENV_PYTHON%" -m pip install -r "%REQUIREMENTS%"
if errorlevel 1 goto :fail

if not exist "%ENV_FILE%" (
    if exist "%ENV_EXAMPLE%" (
        copy /y "%ENV_EXAMPLE%" "%ENV_FILE%" >nul
        echo .env created from .env.example
    )
)

"%VENV_PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
if errorlevel 1 goto :fail

goto :eof

:fail
echo.
echo Startup failed.
pause
exit /b 1