# PowerShell script dla lokalnego backup
# Kodowanie: UTF-8

param(
    [string]$BackupPath = "",
    [switch]$Help
)

# Funkcja wyświetlania pomocy
function Show-Help {
    Write-Host "🚀 LOKALNY BACKUP PROJEKTU GRA WOJENNA" -ForegroundColor Cyan
    Write-Host "======================================"
    Write-Host ""
    Write-Host "Użycie:"
    Write-Host "  .\local_backup.ps1                    # Interaktywny backup"
    Write-Host "  .\local_backup.ps1 -BackupPath C:\..  # Z określoną ścieżką"
    Write-Host "  .\local_backup.ps1 -Help              # Pomoc"
    Write-Host ""
    Write-Host "Skrypt tworzy kopię całego projektu z datą i godziną."
    Write-Host "Domyślna lokalizacja: ~/Desktop/backups_gra_wojenna/"
    exit 0
}

if ($Help) {
    Show-Help
}

Write-Host "🚀 LOKALNY BACKUP PROJEKTU GRA WOJENNA" -ForegroundColor Cyan
Write-Host "======================================"
Write-Host ""

# Sprawdź dostępność Python
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python nie znaleziony"
    }
    Write-Host "✅ Python dostępny: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python nie jest zainstalowany lub niedostępny w PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Aby uruchomić backup, zainstaluj Python z https://python.org"
    Read-Host "Naciśnij Enter aby zakończyć"
    exit 1
}

# Uruchom skrypt Python
Write-Host "🔄 Uruchamianie skryptu backup..." -ForegroundColor Yellow
Write-Host ""

$scriptPath = Join-Path $PSScriptRoot "local_backup.py"

if ($BackupPath) {
    # Jeśli podano ścieżkę, przekaż jako argument (można rozszerzyć w przyszłości)
    python $scriptPath
} else {
    python $scriptPath
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Wystąpił błąd podczas wykonywania backup" -ForegroundColor Red
    Read-Host "Naciśnij Enter aby zakończyć"
    exit 1
}

Write-Host ""
Write-Host "✅ Backup zakończony!" -ForegroundColor Green
Read-Host "Naciśnij Enter aby zakończyć"
