# SKRYPTY BACKUP
# ==============

## 🚀 **Automatyczne skrypty backup na GitHub**

Utworzyłem 3 różne skrypty do automatycznego tworzenia kopii i wysyłania na GitHub:

### 📋 **Dostępne skrypty GitHub:**

#### 1. **Python** - `backup/auto_backup.py`
```bash
python backup/auto_backup.py "nazwa commita"
```

#### 2. **Windows Batch** - `backup/auto_backup.bat`  
```cmd
backup\auto_backup.bat "nazwa commita"
```

#### 3. **PowerShell** - `backup/auto_backup.ps1`
```powershell
.\backup\auto_backup.ps1 "nazwa commita"
```

### 🎯 **Przykłady użycia GitHub backup:**

```bash
# Python
python backup/auto_backup.py "Poprawki AI General - system zakupów"

# Batch
backup\auto_backup.bat "Dodano nowe funkcje AI"

# PowerShell  
.\backup\auto_backup.ps1 "Fixes bugs in combat system"
```

## 💾 **Skrypty backup lokalnego**

Dodatkowo utworzyłem 3 skrypty do tworzenia kopii zapasowych na dysku lokalnym:

### 📋 **Dostępne skrypty lokalnego backup:**

#### 1. **Python** - `backup/local_backup.py`
```bash
python backup/local_backup.py
```

#### 2. **Windows Batch** - `backup/local_backup.bat`  
```cmd
backup\local_backup.bat
```

#### 3. **PowerShell** - `backup/local_backup.ps1`
```powershell
.\backup\local_backup.ps1
```

### 🎯 **Przykłady użycia lokalnego backup:**

```bash
# Python - interaktywny wybór lokalizacji
python backup/local_backup.py

# Batch - jeden klik
backup\local_backup.bat

# PowerShell - z kolorowym outputem
.\backup\local_backup.ps1
```

### 📁 **Format folderów lokalnego backup:**
- **Nazwa:** `gra_wojenna_YYYYMMDD_HHMMSS`
- **Przykład:** `gra_wojenna_20250727_143022`
- **Lokalizacja:** `~/Desktop/backups_gra_wojenna/`

### ✨ **Co robią skrypty GitHub:**

1. ✅ **Sprawdzają status** git repo
2. ✅ **Dodają wszystkie pliki** (`git add -A`)
3. ✅ **Pokazują podgląd** zmian
4. ✅ **Proszą o potwierdzenie** przed commitem
5. ✅ **Tworzą commit** z nazwą + timestamp
6. ✅ **Wykrywają aktualną gałąź**
7. ✅ **Wysyłają na GitHub** (`git push`)
8. ✅ **Pokazują podsumowanie**

### �️ **Co robią skrypty lokalnego backup:**

1. ✅ **Kopiują cały projekt** na dysk lokalny
2. ✅ **Dodają timestamp** do nazwy folderu
3. ✅ **Wykluczają niepotrzebne pliki** (__pycache__, .git, *.log)
4. ✅ **Liczą statystyki** (pliki, rozmiar)
5. ✅ **Tworzą plik info** z metadanymi backup
6. ✅ **Interaktywny wybór** lokalizacji
7. ✅ **Pokazują progress** kopiowania
8. ✅ **Podsumowanie** z statystykami

### �🛡️ **Bezpieczeństwo:**

- **Potwierdzenie przed commitem** (GitHub)
- **Pokazuje dokładnie co zostanie wysłane** (GitHub)
- **Obsługuje błędy git** (GitHub)
- **Wyklucza niepotrzebne pliki** (lokalny)
- **Automatyczne czyszczenie w przypadku błędu** (lokalny)
- **Automatyczny timestamp** (oba typy)

### 📦 **Wybierz najwygodniejszy dla Ciebie!**

- **Python** - uniwersalny, działa wszędzie
- **Batch** - szybki, natywny Windows, jeden klik
- **PowerShell** - nowoczesny, kolorowy output

### 🎯 **Kiedy używać którego backup:**

#### 📤 **GitHub backup:**
- Do udostępniania zmian zespołowi
- Wersjonowanie kodu
- Backup w chmurze
- Ciągła integracja

#### 💾 **Lokalny backup:**
- Szybkie kopie robocze
- Backup przed dużymi zmianami
- Archiwizacja wersji
- Bezpieczeństwo bez internetu

Ten plik jest przestarzały. Używaj tylko:
- backup_local_min.py
- backup_push_github.py
