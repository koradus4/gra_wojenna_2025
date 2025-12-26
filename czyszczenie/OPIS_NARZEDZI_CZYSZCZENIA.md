# 🧹 Narzędzia Czyszczenia Projektu

## Przegląd

Ten folder zawiera narzędzia służące do czyszczenia danych z poprzednich sesji gry, zarządzania logami AI oraz przygotowywania systemu do nowej rozgrywki. Wszystkie narzędzia są zaprojektowane z myślą o bezpieczeństwie danych uczenia maszynowego.

## 📁 Pliki w Folderze

### `game_cleaner.py` - Główne Narzędzie Czyszczenia
**Uniwersalne narzędzie do różnych typów czyszczenia projektu.**

#### Tryby Działania:
- **`--mode quick`** - Szybkie czyszczenie podstawowych plików
- **`--mode new_game`** - Pełne przygotowanie do nowej gry
- **`--mode csv`** - Czyszczenie tylko plików CSV z logów
- **`--mode tokens_soft`** - Bezpieczne usunięcie żetonów (z backup)
- **`--mode tokens_hard`** - Radykalne usunięcie żetonów (wymaga `--confirm`)

#### Przykłady Użycia:
```bash
# Szybkie czyszczenie przed nową sesją
python game_cleaner.py --mode quick

# Pełne przygotowanie do nowej gry
python game_cleaner.py --mode new_game

# Usunięcie żetonów z backupem
python game_cleaner.py --mode tokens_soft

# Radykalne czyszczenie żetonów (UWAGA!)
python game_cleaner.py --mode tokens_hard --confirm
```

### `czyszczenie_csv.py` - Specjalistyczne Czyszczenie Logów
**Zaawansowane narzędzie do zarządzania plikami CSV i logami AI.**

#### Tryby Działania:
1. **BEZPIECZNE** - Czyści tylko sesyjne pliki, chroni dane ML
2. **AGRESYWNE** - Usuwa wszystko (wymaga kodu `ZNISZCZ_ML`)
3. **Wyjście** - Anulowanie operacji

#### Funkcje:
- 🛡️ Automatyczna ochrona danych uczenia maszynowego
- 📊 Szczegółowe statystyki operacji czyszczenia
- 🎯 Inteligentne rozpoznawanie ważnych danych
- 💾 Bezpieczne zarządzanie plikami sesyjnymi

## 🛡️ System Bezpieczeństwa

### Chronione Obszary:
- **`logs/analysis/`** - Dane uczenia maszynowego
- **`logs/dane_ml/`** - Zbiory danych do ML
- **`logs/archiwum_sesji/`** - Zarchiwizowane sesje
- **`logs/*/archives/`** - Wszystkie archiwa

### Czyszczone Bezpiecznie:
- **`logs/sesja_aktualna/`** - Bieżąca sesja (polskie nazwy)
- **`logs/current_session/`** - Sesja (kompatybilność wsteczna)
- **`strategic_orders.json`** - Rozkazy strategiczne
- **`purchased_tokens/`** - Zakupione żetony

## 🚨 Ważne Ostrzeżenia

### ⚡ Tryby Ryzykowne:
1. **`tokens_hard`** - Może usunąć wszystkie żetony z mapy
2. **Tryb AGRESYWNY** - Może usunąć dane uczenia maszynowego
3. **Bez backup** - Flaga `--no-backup` wyłącza zabezpieczenia

### 🔐 Mechanizmy Zabezpieczeń:
- **Potwierdzenia** - Interaktywne "tak/nie" przed usunięciem
- **Kody dostępu** - `ZNISZCZ_ML` dla trybu agresywnego
- **Flagi wymagane** - `--confirm` dla operacji ryzykownych
- **Automatyczne backupy** - Timestampowane kopie w `backup/`

## 💡 Rekomendacje Użycia

### Przed Każdą Sesją:
```bash
python game_cleaner.py --mode quick
```

### Po Zakończeniu Projektu:
```bash
python czyszczenie_csv.py  # wybierz tryb 1 (BEZPIECZNY)
```

### Reset Kompletny (UWAGA!):
```bash
python game_cleaner.py --mode new_game
python czyszczenie_csv.py  # tryb 2 z kodem ZNISZCZ_ML
```

## 🔧 Rozwiązywanie Problemów

### Problem: Emoji nie wyświetlają się
**Przyczyna:** Kodowanie Windows CP1250  
**Rozwiązanie:** Narzędzia działają poprawnie, to tylko kosmetyczny problem wyświetlania

### Problem: Brak uprawnień
**Przyczyna:** Pliki używane przez inne procesy  
**Rozwiązanie:** Zamknij main.py i inne skrypty przed czyszczeniem

### Problem: Przypadkowe usunięcie danych ML
**Rozwiązanie:** Sprawdź folder `backup/` - wszystkie ważne operacje tworzą kopie

### Problem: Nieakturalny folder current_session
**Przyczyna:** Stary system nazewnictwa  
**Rozwiązanie:** Narzędzia obsługują oba systemy (`sesja_aktualna/` i `current_session/`)

## 📝 Historia Wersji

- **v4.1** - Fix liczenia plików w tokens_hard, zaktualizowana struktura folderów
- **v4.0** - Wsparcie dla `logs/sesja_aktualna/` (polskie nazwy) + kompatybilność
- **v3.0** - System ochrony danych ML
- **v2.0** - Automatyczne backupy
- **v1.0** - Podstawowe czyszczenie

## ⚙️ Integracja z Systemem

Te narzędzia są w pełni zintegrowane z:
- **SessionManager** - Zarządzanie sesjami
- **AI Modules** - Logi AI i analizy
- **Main Game Loop** - Przygotowanie do nowej gry
- **ML Pipeline** - Ochrona danych uczenia

---

🎮 **Miłego grania i bezpiecznego czyszczenia!**