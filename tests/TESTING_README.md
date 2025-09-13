# 🎮 System Testowania AI w Grze Wojennej

## 🚀 Szybki Start

### 1. Podstawowe testy (5 minut):
```bash
python quick_test.py
```

### 2. Pełny test (20 minut):
```bash
python quick_test.py --full
```

### 3. Test wydajności (10 minut):
```bash
python quick_test.py --performance
```

### 4. Lista scenariuszy:
```bash
python quick_test.py --list-scenarios
```

### 5. Test konkretnego scenariusza:
```bash
python quick_test.py --scenario balanced_standard
```

## 📊 Co testujemy?

### ✅ Funkcjonalność AI:
- Strategiczne planowanie
- Taktyczne decyzje
- Zarządzanie ekonomią
- Rozpoznanie terenu
- Adaptacja do sytuacji

### 📈 Performance:
- Szybkość podejmowania decyzji
- Zużycie pamięci
- Stabilność systemu
- Obsługa błędów

### 🎯 Scenariusze testowe:

1. **balanced_standard** - Standardowa gra ze zbalansowanym AI
2. **aggressive_vs_defensive** - Agresywne vs defensywne AI
3. **economic_warfare** - Focus na ekonomię
4. **quick_decisive** - Szybka rozgrywka
5. **endurance_test** - Test wytrzymałości (długa gra)
6. **ai_adaptation_test** - Test adaptacji AI
7. **stress_test** - Test obciążeniowy
8. **human_vs_ai** - Symulacja gry z człowiekiem

## 📋 Interpretacja wyników

### 🏆 Test Result:
- **PASS** ✅ - AI działa poprawnie
- **FAIL** ❌ - Problemy z AI
- **ERROR** 🔥 - Błędy krytyczne
- **TIMEOUT** ⏰ - AI zbyt wolne

### 📊 Performance Score (0-100):
- **90-100**: Excellent - AI gotowe do wyzwań
- **70-89**: Good - AI działa dobrze
- **50-69**: Average - AI wymaga poprawek
- **30-49**: Poor - Poważne problemy
- **0-29**: Critical - AI nie nadaje się do gry

### ⚡ Metryki wydajności:
- **Czas tury AI** - powinien być < 3s
- **Zużycie pamięci** - powinno być < 300MB
- **Błędy AI** - powinny być = 0

## 📁 Pliki wynikowe

Po testach znajdziesz w `tests/results/`:
- `summary_YYYYMMDD_HHMMSS.json` - Podsumowanie JSON
- `detailed_YYYYMMDD_HHMMSS.csv` - Szczegółowe dane CSV
- `performance_YYYYMMDD_HHMMSS.log` - Logi wydajności

## 🔧 Rozwiązywanie problemów

### ❌ AI zbyt wolne:
- Sprawdź `ai/konfiguracja_ai.py`
- Zmniejsz `MAX_CALCULATION_TIME`
- Sprawdź `ENABLE_DETAILED_LOGGING = False`

### 💾 Za duże zużycie pamięci:
- Sprawdź czyszczenie w `czyszczenie/game_cleaner.py`
- Zmniejsz `MAX_UNITS_PER_PLAYER`

### 🐛 Błędy AI:
- Sprawdź logi w `ai/logs/`
- Sprawdź konfigurację w `ai/konfiguracja_ai.py`

## 💡 Wskazówki

1. **Pierwszy test**: Zawsze zacznij od `python quick_test.py`
2. **Debugging**: Użyj `--scenario` dla konkretnych problemów
3. **Performance**: Regularnie uruchamiaj `--performance`
4. **Przed wydaniem**: Zawsze `--full` test

## 🎯 Cel testów

System ma odpowiedzieć na pytanie: **"Czy AI może wygrać z doświadczonym graczem?"**

- **Tak**, jeśli średni Performance Score > 70
- **Prawdopodobnie**, jeśli Performance Score 50-70
- **Nie**, jeśli Performance Score < 50

---

*Stworzono przez GitHub Copilot dla projektu "Gra Wojenna 1939"*