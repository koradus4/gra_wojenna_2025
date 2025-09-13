"""
ANALIZA BEZPIECZEŃSTWA: Stare pliki czyszczące NISZCZĄ DANE ML!
===============================================================

## ❌ NIEBEZPIECZNE FUNKCJE - NIE UŻYWAJ!

### 1. czyszczenie/czyszczenie_csv.py
**NISZCZY WSZYSTKO** - usuwa:
- ✅ Stare logi (OK)
- ❌ analysis/ml_ready/*.csv - BEZCENNE DANE ML!
- ❌ analysis/ml_ready/*_meta.json - METADANE ML!
- ❌ analysis/raporty/sesja_*.json - RAPORTY SESJI!

### 2. czyszczenie/game_cleaner.py - clean_csv_logs()
**NISZCZY WSZYSTKO** - kod:
```python
# Usuń WSZYSTKIE pliki CSV rekurencyjnie z logs/
for csv_file in logs_dir.rglob("*.csv"):
    csv_file.unlink()  # ❌ NISZCZY TAKŻE ML!
```

### 3. czyszczenie/game_cleaner.py - clean_ai_logs()  
**CZĘŚCIOWO NISZCZY** - szuka plików `ai_*.csv`:
- ❌ analysis/ml_ready/ai_decyzje_*.csv - USUWA! (test potwierdził)
- ✅ ekonomia_ai_*.csv - przypadkowo ocalał (nie pasuje do wzorca ai_*.csv)

## ✅ BEZPIECZNE FUNKCJE - MOŻNA UŻYWAĆ

### 1. czyszczenie/game_cleaner.py - quick_clean()
```python
✅ BEZPIECZNE:
- clean_strategic_orders()      # OK
- clean_purchased_tokens()      # OK  
- clean_purchased_tokens_from_index()  # OK
- clean_purchased_tokens_from_start()  # OK

❌ NIE WYWOŁUJE niebezpiecznych funkcji ML
```

### 2. czyszczenie/game_cleaner.py - tokens_soft() / tokens_hard()
```python
✅ BEZPIECZNE - działają tylko na:
- assets/start_tokens.json
- assets/tokens/*
- data/map_data.json (pola token)

❌ NIE RUSZAJĄ logs/
```

## 🔧 NAPRAWY POTRZEBNE:

### Funkcja clean_ai_logs() - dodać wykluczenia:
```python
# PRZED:
for f in logs_dir.rglob("ai_*.csv"):
    f.unlink()

# PO:
for f in logs_dir.rglob("ai_*.csv"):
    # CHROŃ dane ML!
    if 'analysis/ml_ready' in str(f):
        continue  # Pomiń!
    f.unlink()
```

### Funkcja clean_csv_logs() - dodać wykluczenia:
```python
# PRZED:
for csv_file in logs_dir.rglob("*.csv"):
    csv_file.unlink()

# PO:
for csv_file in logs_dir.rglob("*.csv"):
    # CHROŃ dane ML!
    if 'analysis/ml_ready' in str(csv_file):
        continue  # Pomiń!
    if 'analysis/raporty' in str(csv_file):
        continue  # Pomiń raporty!
    csv_file.unlink()
```

## 🎯 REKOMENDACJE:

### ✅ BEZPIECZNIE UŻYJ:
```bash
# Te komendy SĄ BEZPIECZNE:
python czyszczenie/game_cleaner.py --mode quick
python czyszczenie/game_cleaner.py --mode tokens_soft
python czyszczenie/game_cleaner.py --mode tokens_hard --confirm

# Te funkcje SĄ BEZPIECZNE w Pythonie:
from czyszczenie.game_cleaner import quick_clean, tokens_soft
quick_clean()
tokens_soft()
```

### ❌ NIE UŻYWAJ (niszczą ML):
```bash
# NIEBEZPIECZNE:
python czyszczenie/czyszczenie_csv.py
python czyszczenie/game_cleaner.py --mode csv
python czyszczenie/game_cleaner.py --mode new_game  # używa clean_ai_logs!

# NIEBEZPIECZNE w Pythonie:
from czyszczenie.game_cleaner import clean_csv_logs, clean_ai_logs
clean_csv_logs()  # ❌ NISZCZY ML!
clean_ai_logs()   # ❌ NISZCZY ML!
```

### 🆕 UŻYWAJ NOWEGO SYSTEMU:
```bash
# BEZPIECZNE NOWE:
python utils/smart_log_cleaner.py --mode session  # ✅
python utils/smart_log_cleaner.py --mode full     # ✅
python utils/smart_log_cleaner.py --mode archive  # ✅

# W launcherze:
🧹 Sesja (Ctrl+Shift+S)  # ✅
🗑️ Pełne                  # ✅  
📚 Archiwum               # ✅
📊 Status ML              # ✅
```

## 🚨 NATYCHMIASTOWE DZIAŁANIA:

1. **PRZESTAŃ używać** czyszczenie_csv.py
2. **PRZESTAŃ używać** --mode csv i --mode new_game  
3. **UŻYWAJ TYLKO** nowego systemu z utils/smart_log_cleaner.py
4. **LUB** używaj --mode quick (tylko żetony i rozkazy)

## 💡 NAPRAWY DO ZAIMPLEMENTOWANIA:

1. Napraw clean_ai_logs() - dodaj wykluczenie analysis/ml_ready
2. Napraw clean_csv_logs() - dodaj wykluczenie analysis/
3. Dodaj ostrzeżenia w czyszczenie_csv.py o niszczeniu ML
4. Zaktualizuj clean_all_for_new_game() aby używał nowych funkcji
"""