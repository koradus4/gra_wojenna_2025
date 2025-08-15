# 📁 FOLDER BACKUP
# =================

## 🚀 **Skrypty backup projektu**

### 📋 **Zawartość folderu:**

#### 🔧 **Backup na GitHub (automatyczny):**
- `backup_push_github.py` (commit + push na origin main)

#### 💾 **Backup lokalny (kopia na dysku):**
- `backup_local_min.py` (lokalna kopia do `C:/Users/klif/gra+wojenna15082025`)

####  **Dokumentacja:**
- `BACKUP_SCRIPTS.md` - szczegółowa instrukcja użycia
- `README.md` - ten plik

---

## 🎯 **Szybki start:**

### 📤 **Backup na GitHub:**
```bash
# Z głównego katalogu projektu:
python backup/backup_push_github.py "Moja zmiana"

# lub
backup\backup_push_github.bat "Moja zmiana"

# lub
.\backup\backup_push_github.ps1 "Moja zmiana"
```

### 💾 **Backup lokalny:**
```bash
# Z głównego katalogu projektu:
python backup/backup_local_min.py

# lub
backup\backup_local_min.bat

# lub
.\backup\backup_local_min.ps1
```

**Backup lokalny tworzy folder:** `gra_wojenna_YYYYMMDD_HHMMSS`  
**Domyślna lokalizacja:** `~/Desktop/backups_gra_wojenna/`

---

## 📚 **Więcej informacji:**
Przeczytaj `BACKUP_SCRIPTS.md` w tym folderze dla pełnej dokumentacji!
