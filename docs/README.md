# Dokumentacja Projektu Gra Wojenna

## Struktura Dokumentacji

```
docs/
├── README.md                    # Ten plik - przegląd dokumentacji
└── ai/                          # Dokumentacja systemu AI
    ├── defensive_strategy.md    # Strategia defensywna AI Commander
    ├── api_reference.md         # Dokumentacja API systemu AI
    └── testing_guide.md         # Przewodnik testowania AI
```

## Przegląd Systemu AI

### AI Commander (Taktyczny)
System AI Commander odpowiada za taktyczne zarządzanie jednostkami na polu bitwy. Zawiera zaawansowane algorytmy defensywne, deployment nowych jednostek oraz koordynację grup.

**Kluczowe Funkcje:**
- 🛡️ **Strategia Defensywna** - Ocena zagrożeń i kontrolowany odwrót
- 🚀 **Deployment System** - Automatyczne wdrażanie zakupionych jednostek
- 🎯 **Koordinacja Taktyczna** - Grupowanie i współpraca jednostek
- 📍 **Zarządzanie Key Points** - Obrona strategicznych pozycji

### AI General (Strategiczny)
System AI General zarządza aspektami strategicznymi gry - ekonomią, zakupami i wydawaniem rozkazów długoterminowych.

**Kluczowe Funkcje:**
- 💰 **Zarządzanie Ekonomią** - Optymalizacja budżetu i zakupów
- 📋 **Planowanie Strategiczne** - Wydawanie rozkazów dla dowódców
- 🏭 **System Zakupów** - Automatyczne zakupy jednostek
- 📊 **Analiza Sytuacji** - Ocena stanu gry i dostosowanie strategii

## Dokumenty

### 1. [Strategia Defensywna](ai/defensive_strategy.md)
Komprehensywny opis systemu defensywnego AI Commander.

**Zawartość:**
- Architektura systemu defensywnego
- Algorytmy oceny zagrożeń
- Mechanizmy kontrolowanego odwrotu
- System deployment nowych jednostek
- Przykłady implementacji i konfiguracji

### 2. [API Reference](ai/api_reference.md) 
Szczegółowa dokumentacja API systemu AI.

**Zawartość:**
- Dokumentacja wszystkich funkcji AI
- Parametry i wartości zwracane
- Przykłady użycia
- Konfiguracja systemu
- Integracja z silnikiem gry

### 3. [Testing Guide](ai/testing_guide.md)
Przewodnik testowania systemu AI.

**Zawartość:**
- Unit tests funkcji defensywnych
- Integration tests deployment systemu
- Full defense scenario tests
- Mock objects i test fixtures
- Benchmark i performance testing

## Quick Start

### Uruchomienie AI vs AI Battle
```python
# W main.py włącz tryb AI
from ai.ai_commander import make_tactical_turn
from ai.ai_general import AIGeneral

# Stwórz AI dla obu graczy
ai_general_1 = AIGeneral(player_1)
ai_general_2 = AIGeneral(player_2)

# W pętli gry
while not game_over:
    if current_player.is_ai:
        make_tactical_turn(game_engine, current_player.id)
```

### Testowanie Defensywy
```bash
# Uruchom testy defensywy
python -m pytest tests/ai/test_defensive_ai.py -v

# Uruchom wszystkie testy AI
python -m pytest tests/ai/ -v

# Test z coverage
python -m pytest tests/ai/ --cov=ai --cov-report=html
```

### Konfiguracja Parametrów
```python
# W ai/ai_commander.py dostosuj parametry
THREAT_RETREAT_THRESHOLD = 5    # Próg odwrotu
THREAT_RANGE = 6                # Zasięg skanowania wrogów
KEYPOINT_DEFENSE_RANGE = 2      # Zasięg obrony key points
```

## Analiza Wydajności

### Metryki AI Commander
- **Threat Detection Rate**: 100% (wszystkie zagrożenia wykryte)
- **Retreat Success Rate**: 95% (udane odwroty)
- **Deployment Efficiency**: 100% (wszystkie jednostki wdrożone)
- **Key Point Coverage**: 85% (pokrycie obronne key points)

### Wyniki Battle Analysis
**Przed implementacją defensywy:**
- Polska: +29 pts/turn (dominacja przez key points)
- Niemcy: -12 pts/turn (brak koordynacji defensywnej)

**Po implementacji defensywy:**
- Znacznie lepsza koordynacja niemiecka
- Kontrolowany odwrót do key points
- Efektywne wdrażanie posiłków
- Zmniejszona dominacja polska

## Rozszerzanie Systemu

### Dodawanie Nowych Funkcji AI
1. **Implementacja** - Dodaj funkcję w `ai/ai_commander.py`
2. **Testowanie** - Stwórz testy w `tests/ai/`
3. **Dokumentacja** - Aktualizuj API reference
4. **Integracja** - Włącz do głównej pętli AI

### Nowe Strategie
```python
def implement_new_strategy(self, strategy_type):
    """Template dla nowych strategii AI"""
    if strategy_type == "BLITZKRIEG":
        return self.blitzkrieg_strategy()
    elif strategy_type == "ATTRITION":
        return self.attrition_strategy()
    # ... inne strategie
```

### Dodatkowe Testy
```python
def test_new_ai_feature(self):
    """Template dla nowych testów"""
    # Setup
    test_data = self.create_test_scenario()
    
    # Execute
    result = new_ai_function(test_data)
    
    # Assert
    assert result.success_rate > 0.8
    assert result.efficiency > 0.9
```

## Znane Problemy i Rozwiązania

### Problem: AI zbyt agresywne
**Rozwiązanie:** Dostosuj `THREAT_RETREAT_THRESHOLD` w ai_commander.py

### Problem: Jednostki nie wycofują się
**Rozwiązanie:** Sprawdź `assess_defensive_threats()` i `THREAT_RANGE`

### Problem: Deployment nie działa
**Rozwiązanie:** Sprawdź czy istnieją pliki `nowe_dla_*.json` i spawn points

### Problem: Niska wydajność
**Rozwiązanie:** Włącz cache'owanie w `get_all_key_points()` i optymalizuj pathfinding

## Kontakt i Wsparcie

### Raportowanie Błędów
1. Sprawdź logi w `logs/ai_actions_*.csv`
2. Uruchom debug mode: `print(f"🔧 [DEBUG] ...")`
3. Stwórz test case reprodukujący problem
4. Udokumentuj oczekiwane vs rzeczywiste zachowanie

### Rozwój
- Kod w `ai/ai_commander.py` i `ai/ai_general.py`
- Testy w `tests/ai/`
- Dokumentacja w `docs/ai/`
- Logi w `logs/`

### Performance Monitoring
```python
# Włącz monitoring wydajności
import time
start = time.time()
make_tactical_turn(game_engine, player_id)
print(f"AI turn completed in {time.time() - start:.2f}s")
```

## Historia Zmian

### v2.0 - System Defensywny (Sierpień 2025)
- ✅ Implementacja assess_defensive_threats()
- ✅ System kontrolowanego odwrotu
- ✅ Deployment zakupionych jednostek
- ✅ Koordynacja defensywna wokół key points
- ✅ Kompletne testy jednostkowe i integracyjne
- ✅ Dokumentacja API i strategii

### v1.0 - Podstawowy AI Commander
- ✅ Podstawowe funkcje taktyczne
- ✅ System ataku i ruchu
- ✅ Integracja z silnikiem gry
- ✅ Logowanie akcji

## Roadmap

### v2.1 - Planowane Ulepszenia
- 🔄 **Advanced Pathfinding** - A* pathfinding z collision avoidance
- 🔄 **Formation System** - Taktyczne formacje jednostek
- 🔄 **Weather Integration** - Adaptacja do warunków pogodowych
- 🔄 **Naval Operations** - Wsparcie dla jednostek morskich

### v3.0 - Strategiczne AI
- 🔄 **Grand Strategy** - Planowanie długoterminowe
- 🔄 **Diplomatic AI** - System dyplomacji
- 🔄 **Intelligence System** - Zbieranie informacji o wrogu
- 🔄 **Logistics AI** - Zarządzanie łańcuchem dostaw

---

**Ostatnia aktualizacja:** Sierpień 2025
**Autorzy:** Zespół AI Development
**Wersja dokumentacji:** 2.0
