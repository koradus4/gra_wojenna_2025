# Gra Wojenna - Wersja 3.8

Strategiczna gra wojenna z elementami sztucznej inteligencji napisana w Pythonie. Wykorzystuje hexagonalną planszę i system punktów zasobów do zarządzania jednostkami.

**AKTUALIZACJA 3.8:** Zaimplementowany PE Validation System - kompleksowe zabezpieczenie ekonomiczne przeciwko ujemnym PE.

## Kluczowe funkcje

- System hexagonalnej planszy z punktami kluczowymi i zasobami
- Zaawansowana sztuczna inteligencja z modułowym systemem komponentów
- **NOWE:** PE Validation System - zabezpieczenie przed ujemnymi PE
- Ekonomiczny system zarządzania zasobami z walidacją bezpieczeństwa
- System logowania i analizy rozgrywek z PE flow tracking
- Interfejs graficzny z obsługą myszki i klawiatury
- Tryb AI vs AI do testowania strategii z economic monitoring
- **NOWE:** Kompleksowe narzędzia diagnostyczne w języku polskim

## Struktura projektu

Projekt składa się z następujących głównych komponentów:

### Moduły core
- `engine/` - Silnik gry, hexagonalna plansza, tokeny
- `core/` - Podstawowe systemy: ekonomia, dyplomacja, rozkazy
- `gui/` - Interfejs graficzny i panele użytkownika

### Systemy AI (20+ modułów z PE Validation)
- `ai/` - Sztuczna inteligencja z PE security: strategia, taktyka, ekonomia, walka
- `ai/zaopatrzenie_ai.py` - **PE validation system** z funkcjami bezpieczeństwa
- `ai/ekonomia_ai.py` - **PE validation** w systemie zakupów i wydatków
- `ai/ai_general.py` - **Bezpieczne transfery PE** z walidacją
- `balance/` - System balansowania AI

### Narzędzia i utylity (Polish localization)
- `tools/` - **Polskojęzyczne** narzędzia analizy i diagnostyki PE
- `tools/analizator_przeplywu_pe.py` - Analiza przepływu PE między AI
- `tools/launcher_analizy_pe.py` - Launcher z czyszczeniem i analizą
- `tools/sprawdzenie_rzetelnosci_zetonow.py` - Walidacja tokenów
- `tools/analizator_ai_na_zywo.py` - Monitor AI w czasie rzeczywistym  
- `tools/diagnostyka_key_points.py` - Diagnostyka punktów kluczowych
- `edytory/` - Edytory map, tokenów i armii
- `czyszczenie/` - Utylity czyszczenia danych
- `tests/` - Testy jednostkowe
- `logs/` - Logi rozgrywek do analizy z PE flow data

## Uruchamianie gry

### Podstawowe uruchomienie
```bash
python main.py           # Tryb standardowy
python main_ai.py        # Tryb AI vs AI
python main_alternative.py  # Alternatywny launcher
```

### Testowanie PE Validation System
```bash
python tools/launcher_analizy_pe.py  # Kompleksowa analiza PE z czyszczeniem
python tools/analizator_przeplywu_pe.py  # Analiza przepływu PE
```

### Diagnostyka i monitoring
```bash
python tools/analizator_ai_na_zywo.py   # Monitor AI w czasie rzeczywistym
python tools/sprawdzenie_rzetelnosci_zetonow.py  # Walidacja tokenów
python tools/diagnostyka_key_points.py  # Diagnostyka punktów kluczowych
```

## Wymagania systemowe

- Python 3.8+
- Pygame 2.0+
- Numpy
- Pozostałe zależności w `requirements.txt`

## PE Validation System - NOWE

### Problem rozwiązany
AI mogło wydawać ujemne PE (punkty ekonomiczne), powodując destabilizację ekonomiczną i nieprzewidywalne zachowania.

### Rozwiązanie
Zaimplementowany multi-layer protection system:

#### Kluczowe komponenty
- `validate_pe_spending()` - sprawdza czy operacja nie spowoduje ujemnych PE
- `transfer_pe_to_commanders()` - bezpieczne transfery Generał→Dowódca
- `check_pe_balance()` - weryfikacja po każdej operacji ekonomicznej
- `block_negative_pe()` - hard stop dla nieprawidłowych operacji
- Comprehensive PE flow logging - pełne śledzenie w CSV

#### Efekt
- ✅ Ekonomia AI jest stabilna i bezpieczna
- ✅ Eliminacja ujemnych PE
- ✅ Pełne śledzenie przepływu ekonomii
- ✅ Diagnostyka w języku polskim
- ✅ Automated testing framework

## Szczegółowa dokumentacja

- `STRUKTURA_PROJEKTU.md` - Kompleksowa dokumentacja projektu
- `ai/OPIS_MODULOW_AI.md` - Opis modułów AI z PE validation
- `docs/` - Dokumentacja techniczna i przewodniki

## Rozwój i testowanie

### Czyszczenie środowiska
```bash
python czyszczenie/game_cleaner.py  # Kompleksowe czyszczenie
```

### Analiza i monitoring
- Wszystkie narzędzia w folderze `tools/` w języku polskim
- Automated PE flow analysis po każdej grze AI vs AI
- Real-time AI behavior monitoring
- Token consistency validation

### Status rozwoju
- **Wersja 3.8:** PE Validation System ✅ COMPLETED
- Ekonomia AI: Zabezpieczona i stabilna
- Diagnostic tools: Polskojęzyczne i funkcjonalne
- Testing framework: Automated i comprehensive

## Licencja

Projekt prywatny - wszystkie prawa zastrzeżone.

---
**Uwaga:** Jeśli napotkasz problemy z PE validation system, użyj narzędzi diagnostycznych z folderu `tools/` - wszystkie w języku polskim z jasnym opisem problemów i rozwiązań.
