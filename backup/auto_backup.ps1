# AUTOMATYCZNY BACKUP NA GITHUB - PowerShell
# ==========================================
# 
# Użycie: .\auto_backup.ps1 "nazwa commita"
# Przykład: .\auto_backup.ps1 "Poprawki AI General"

param(
    [Parameter(Mandatory=$true, HelpMessage="Podaj nazwę commita")]
    [string]$CommitName
)

function Write-Step {
    param([string]$Message, [string]$Icon = "🔄")
    Write-Host "$Icon $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Run-GitCommand {
    param([string]$Command, [string]$Description)
    
    Write-Step $Description
    Write-Host "   Komenda: $Command" -ForegroundColor Gray
    
    try {
        $result = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            if ($result) {
                Write-Host "   $result" -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Error "Błąd wykonania: $result"
            return $false
        }
    } catch {
        Write-Error "Wyjątek: $($_.Exception.Message)"
        return $false
    }
}

# Główna funkcja
function Main {
    $timestamp = Get-Date -Format "dd.MM.yyyy HH:mm:ss"
    
    Write-Host "🚀 AUTOMATYCZNY BACKUP NA GITHUB" -ForegroundColor Yellow
    Write-Host "=" * 50 -ForegroundColor Yellow
    Write-Host "📝 Nazwa commita: $CommitName" -ForegroundColor White
    Write-Host "⏰ Czas: $timestamp" -ForegroundColor White
    Write-Host ""
    
    # Przejdź do katalogu projektu
    Set-Location "c:\Users\klif\kampania1939_restored"
    
    # Sprawdź czy to repo git
    if (!(Test-Path ".git")) {
        Write-Error "Nie jesteś w repozytorium git!"
        return $false
    }
    
    # 1. Status
    Write-Step "SPRAWDZANIE STATUSU" "1️⃣"
    if (!(Run-GitCommand "git status --porcelain" "Sprawdzam zmiany")) {
        return $false
    }
    
    # 2. Add
    Write-Host ""
    Write-Step "DODAWANIE PLIKÓW" "2️⃣"
    if (!(Run-GitCommand "git add -A" "Dodaję wszystkie pliki")) {
        return $false
    }
    
    # 3. Podgląd
    Write-Host ""
    Write-Step "PODGLĄD ZMIAN" "3️⃣"
    Run-GitCommand "git status --short" "Sprawdzam pliki do commita"
    
    # 4. Potwierdzenie
    Write-Host ""
    Write-Step "POTWIERDZENIE" "4️⃣"
    $confirm = Read-Host "Czy chcesz commitować zmiany jako '$CommitName'? (tak/nie)"
    
    if ($confirm -notin @('tak', 't', 'yes', 'y')) {
        Write-Error "Anulowano backup"
        return $false
    }
    
    # 5. Commit
    Write-Host ""
    Write-Step "TWORZENIE COMMITA" "5️⃣"
    $fullCommitMessage = "$CommitName - $timestamp"
    if (!(Run-GitCommand "git commit -m `"$fullCommitMessage`"" "Tworzę commit")) {
        Write-Host "⚠️ Możliwe że nie ma zmian do commitowania" -ForegroundColor Yellow
    }
    
    # 6. Sprawdź gałąź
    Write-Host ""
    Write-Step "SPRAWDZANIE GAŁĘZI" "6️⃣"
    try {
        $currentBranch = git branch --show-current
        if (!$currentBranch) { $currentBranch = "main" }
        Write-Host "   📍 Aktualna gałąź: $currentBranch" -ForegroundColor Gray
    } catch {
        $currentBranch = "main"
        Write-Host "   📍 Domyślna gałąź: $currentBranch" -ForegroundColor Gray
    }
    
    # 7. Push
    Write-Host ""
    Write-Step "WYSYŁANIE NA GITHUB" "7️⃣"
    if (!(Run-GitCommand "git push origin $currentBranch" "Wysyłam na GitHub")) {
        return $false
    }
    
    # 8. Podsumowanie
    Write-Host ""
    Write-Host "🎉 BACKUP ZAKOŃCZONY POMYŚLNIE!" -ForegroundColor Green
    Write-Host "=" * 50 -ForegroundColor Green
    Write-Success "Commit: $fullCommitMessage"
    Write-Success "Gałąź: $currentBranch"
    Write-Success "Wysłano na: https://github.com/koradus4/turowka_z_ai"
    Write-Host ""
    
    return $true
}

# Uruchom
try {
    $success = Main
    
    if ($success) {
        Write-Host "🎯 Backup wykonany poprawnie!" -ForegroundColor Green
    } else {
        Write-Host "💥 Wystąpił błąd podczas backupu!" -ForegroundColor Red
    }
} catch {
    Write-Error "Nieoczekiwany błąd: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "Deprecated. Use backup_local_min.py"
