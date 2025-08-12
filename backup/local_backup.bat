@echo off
chcp 65001 >nul
title Lokalny Backup - Gra Wojenna

echo.
echo 🚀 LOKALNY BACKUP PROJEKTU GRA WOJENNA
echo ==========================================
echo.

REM Sprawdź czy Python jest dostępny
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nie jest zainstalowany lub niedostępny w PATH
    echo.
    echo Aby uruchomić backup, zainstaluj Python z https://python.org
    pause
    exit /b 1
)

REM Uruchom skrypt Python
echo 🔄 Uruchamianie skryptu backup...
echo.

python "%~dp0local_backup.py" %*

if errorlevel 1 (
    echo.
    echo ❌ Wystąpił błąd podczas wykonywania backup
    pause
    exit /b 1
)

echo.
echo ✅ Backup zakończony!
pause
