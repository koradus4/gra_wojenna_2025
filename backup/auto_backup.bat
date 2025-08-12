@echo off
:: SZYBKI BACKUP NA GITHUB - Windows Batch
:: =====================================
:: 
:: Użycie: auto_backup.bat "nazwa commita"
:: Przykład: auto_backup.bat "Poprawki AI General"

setlocal enabledelayedexpansion

:: Sprawdź argumenty
if "%~1"=="" (
    echo ❌ Błąd: Brak nazwy commita!
    echo Użycie: auto_backup.bat "nazwa_commita"
    echo Przykład: auto_backup.bat "Poprawki AI General"
    pause
    exit /b 1
)

set "COMMIT_NAME=%~1"
set "TIMESTAMP=%date% %time:~0,8%"

echo 🚀 AUTOMATYCZNY BACKUP NA GITHUB
echo ==================================================
echo 📝 Nazwa commita: %COMMIT_NAME%
echo ⏰ Czas: %TIMESTAMP%
echo.

:: Przejdź do katalogu projektu
cd /d "c:\Users\klif\kampania1939_restored"

:: 1. Sprawdź status
echo 1️⃣ SPRAWDZANIE STATUSU
git status --porcelain
if errorlevel 1 (
    echo ❌ Błąd sprawdzania statusu git
    pause
    exit /b 1
)

:: 2. Dodaj pliki
echo.
echo 2️⃣ DODAWANIE PLIKÓW
git add -A
if errorlevel 1 (
    echo ❌ Błąd dodawania plików
    pause
    exit /b 1
)

:: 3. Podgląd zmian
echo.
echo 3️⃣ PODGLĄD ZMIAN
git status --short

:: 4. Potwierdź
echo.
echo 4️⃣ POTWIERDZENIE
set /p "confirm=Czy chcesz commitować zmiany jako '%COMMIT_NAME%'? (tak/nie): "
if /i not "%confirm%"=="tak" if /i not "%confirm%"=="t" (
    echo ❌ Anulowano backup
    pause
    exit /b 0
)

:: 5. Commit
echo.
echo 5️⃣ TWORZENIE COMMITA
git commit -m "%COMMIT_NAME% - %TIMESTAMP%"

:: 6. Sprawdź gałąź
echo.
echo 6️⃣ SPRAWDZANIE GAŁĘZI
for /f "tokens=*" %%i in ('git branch --show-current') do set "CURRENT_BRANCH=%%i"
if "!CURRENT_BRANCH!"=="" set "CURRENT_BRANCH=main"
echo 📍 Aktualna gałąź: !CURRENT_BRANCH!

:: 7. Push na GitHub
echo.
echo 7️⃣ WYSYŁANIE NA GITHUB
git push origin !CURRENT_BRANCH!
if errorlevel 1 (
    echo ❌ Błąd wysyłania na GitHub
    pause
    exit /b 1
)

:: 8. Podsumowanie
echo.
echo 🎉 BACKUP ZAKOŃCZONY POMYŚLNIE!
echo ==================================================
echo ✅ Commit: %COMMIT_NAME% - %TIMESTAMP%
echo ✅ Gałąź: !CURRENT_BRANCH!
echo ✅ Wysłano na: https://github.com/koradus4/turowka_z_ai
echo.
echo 🎯 Backup wykonany poprawnie!

pause
