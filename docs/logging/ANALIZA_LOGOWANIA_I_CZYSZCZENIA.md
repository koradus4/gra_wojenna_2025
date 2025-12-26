"""
ANALIZA SYSTEMU LOGOWANIA I CZYSZCZENIA
=======================================

System logowania DZIAŁA i generuje pliki po uruchomieniu gry!

## 📊 AKTUALNY STAN LOGÓW (po testach):

### ✅ System generuje pliki:
- **112 plików** w strukturze logs/ (dane z ostatniego testu demo_logging_system.py)
- **Dane ML**: ai_decyzje (110 rekordów), ekonomia_ai (16 rekordów) w logs/analysis/ml_ready/
- **Sesje gry**: logs/analysis/raporty/sesja_*.json z metadanymi
- **Logi AI**: logs/ai/ z podziałem na kategorie (general, dowodca, strategia, walka, etc.)
- **Logi human**: logs/human/ dla akcji gracza ludzkiego
- **Logi game**: logs/game/ dla mechaniki gry

### 🔍 Struktura katalogów:
```
logs/
├── ai/           # AI logs (dowodca, general, strategia, walka, ruch, ekonomia, etc.)
├── human/        # Human player logs (akcje, decyzje, interfejs)
├── game/         # Game mechanics logs (mechanika, stan, bledy)
└── analysis/     # Analizy i dane ML
    ├── ml_ready/     # Gotowe datasety ML (.csv + _meta.json)
    ├── raporty/      # Sesje gry i raporty
    └── statystyki/   # Statystyki gry
```

## 🧹 OPCJE CZYSZCZENIA - ANALIZA:

### 1. **SZYBKIE CZYSZCZENIE** (quick_clean) - Przycisk "🧹"
- ✅ Usuwa: strategic_orders, purchased tokens, nowe_dla_* foldery
- ✅ Zachowuje: WSZYSTKIE LOGI (AI, human, game, ML)
- 🎯 Użycie: Między grami z tym samym zestawem graczy

### 2. **PEŁNE CZYSZCZENIE** (full_clean) - Przycisk "🗑️"  
- ✅ Usuwa: jak szybkie + AI logs + game logs (stare pliki *.csv)
- ❌ Problem: NIE CZYŚCI nowego systemu logowania!
- 🎯 Użycie: Kompletnie nowa gra

### 3. **CZYŚĆ LOGI CSV** (clean_logs_only) - Przycisk "🧾"
- ✅ Usuwa: WSZYSTKIE *.csv z logs/ rekursywnie
- ❌ Problem: Usuwa TAKŻE WARTOŚCIOWE dane ML!
- 🎯 Użycie: Czyszczenie problemowe

### 4. **Skrót Ctrl+Shift+L** 
- ✅ Usuwa: WSZYSTKIE *.csv z logs/
- ❌ Problem: NISZCZY dane ML bez ostrzeżenia!

## 🎯 REKOMENDACJE CZYSZCZENIA:

### Co czyścić PO KAŻDEJ SESJI GRY:
```python
SESYJNE (zawsze czyścić):
✅ data/strategic_orders.json           # Rozkazy strategiczne
✅ assets/tokens/nowe_dla_*             # Foldery zakupionych żetonów  
✅ assets/tokens/aktualne/nowy_*.json   # Pliki zakupionych żetonów
✅ assets/start_tokens.json             # Resetuj do []
✅ logs/ai/*/dane_*.csv (bieżąca sesja) # Bieżące logi AI
✅ logs/game/*/dane_*.csv               # Bieżące logi game
✅ logs/human/*/dane_*.csv              # Bieżące logi human
```

### Co ARCHIWIZOWAĆ (zachować):
```python
ARCHIWALNE (zachować na przyszłość):
💾 logs/analysis/ml_ready/*.csv        # Datasety ML - BEZCENNE!
💾 logs/analysis/ml_ready/*_meta.json  # Metadane ML
💾 logs/analysis/raporty/sesja_*.json  # Raporty sesji
💾 logs/analysis/statystyki/           # Statystyki długoterminowe
💾 assets/tokens/index.json (czyść nowy_*) # Index bez zakupionych
💾 data/map_data.json (usuń 'token')   # Mapa bez rozmieszczonych żetonów
```

## 🔧 PROBLEMY DO NAPRAWY:

### 1. Pełne czyszczenie nie obsługuje nowego systemu
- `clean_all_for_new_game()` używa starych funkcji `clean_ai_logs()`, `clean_game_logs()`
- Te funkcje szukają `ai_*.csv`, `actions_*.csv` ale nowy system używa `dane_*.csv`
- **Rozwiązanie**: Zaktualizować funkcje czyszczenia

### 2. Brak rozróżnienia na sesyjne vs archiwalne
- Wszystkie funkcje czyszczą "na ślepo"
- **Rozwiązanie**: Nowe funkcje `clean_session_logs()`, `preserve_ml_data()`

### 3. Ctrl+Shift+L niszczy dane ML
- **Rozwiązanie**: Zmienić na `clean_session_logs()` zamiast `clean_csv_logs()`

## 💡 PROPOZYCJA ULEPSZENIA:

### Nowe funkcje czyszczenia:
1. **clean_session_only()** - tylko bieżąca sesja (dane_*.csv z dzisiaj)
2. **clean_preserve_ml()** - wszystko oprócz logs/analysis/ml_ready/
3. **archive_session()** - przenieś bieżące dane do archive/YYYY-MM-DD/
4. **clean_old_archives()** - usuń archiwa starsze niż N dni

### Zmienione przyciski:
- 🧹 "Sesja" → clean_session_only() 
- 🗑️ "Pełne" → clean_preserve_ml()
- 📚 "Archiwum" → archive_session() + clean_session_only()
- 💾 "Stare archiwa" → clean_old_archives(30) # starsze niż 30 dni

## ⚠️ OSTRZEŻENIE BEZPIECZEŃSTWA:
**NIE używaj Ctrl+Shift+L ani "Czyść logi CSV" - niszczą bezcenne dane ML!**
"""