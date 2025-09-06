# 📁 ANALIZA FOLDERU CORE - KAMPANIA 1939

## 📌 WPROWADZENIE

Folder `core/` zawiera podstawowe moduły logiki biznesowej gry **Kampania 1939**. Ten dokument analizuje każdy plik pod kątem funkcjonalności, duplikatów i potrzeby reorganizacji.

**Data analizy:** 6 września 2025  
**Wersja systemu:** 3.8 (z PE Validation System)  
**Status:** ANALIZA KOMPLETNA ✅

---

## 🗂️ STRUKTURA FOLDERU CORE

```
core/
├── dyplomacja.py          # ❌ PUSTY - do implementacji
├── ekonomia.py            # ✅ AKTYWNY - system ekonomiczny PE
├── pogoda.py              # ✅ AKTYWNY - generator pogody
├── rozkazy.py             # ❌ PUSTY - do implementacji  
├── tura.py                # ✅ AKTYWNY - menedżer tur
├── unit_factory.py        # ✅ AKTYWNY - fabryka jednostek
├── zwyciestwo.py          # ⚠️ CZĘŚCIOWY - warunki zwycięstwa
└── __pycache__/           # Cache Pythona
```

---

## 📋 SZCZEGÓŁOWA ANALIZA PLIKÓW

### ✅ **ekonomia.py** - KLASA EconomySystem

**Status:** AKTYWNY I POTRZEBNY ✅  
**Funkcjonalność:**
- Zarządzanie punktami ekonomicznymi (PE) i specjalnymi
- System PE Validation (v3.8) - ochrona przed ujemnymi wartościami
- Operacje: dodawanie, odejmowanie, sprawdzanie bilansów
- Obsługa przydzielonych punktów dowódcom

**Kluczowe metody:**
- `generate_economic_points()` - generuje losowe PE (1-100)
- `subtract_points(points)` - bezpieczne odejmowanie z walidacją
- `add_economic_points(points)` - dodawanie PE z key points
- `get_points()` - zwraca aktualne PE i punkty specjalne

**Integracja:**
- Używany przez `engine/engine.py` w `process_key_points()`
- Używany przez `gui/panel_generala.py` dla ekonomii graczy
- Używany przez `ai/zaopatrzenie_ai.py` dla AI wydatków

**Czy duplikat?** ❌ NIE - to jest JEDYNE źródło logiki ekonomicznej

---

### ✅ **pogoda.py** - KLASA Pogoda

**Status:** AKTYWNY I POTRZEBNY ✅  
**Funkcjonalność:**
- Generator pogody z realistycznymi ograniczeniami
- Temperatura: -5°C do 25°C (max zmiana ±2°C dziennie)
- Zachmurzenie: Bezchmurnie/umiarkowane/duże
- Opady: Bezdeszczowo/lekkie/intensywne + śnieg poniżej 0°C

**Kluczowe metody:**
- `generuj_pogode()` - generuje pogodę z ograniczeniami temperatury
- `generuj_raport_pogodowy()` - formatuje raport tekstowy
- `wypisz_pogode()` - deprecated (pusta metoda)

**Integracja:**
- Używany przez `core/tura.py` w `TurnManager`
- Panel pogody w GUI generała i dowódcy
- Generowanie co 6 tur (mechanika czasowa)

**Czy duplikat?** ❌ NIE - jedyna implementacja systemu pogody

---

### ✅ **tura.py** - KLASA TurnManager

**Status:** AKTYWNY I POTRZEBNY ✅  
**Funkcjonalność:**
- Zarządzanie kolejnością graczy i turami
- Reset zasobów jednostek (MP, fuel, akcje artylerii)
- Integracja z systemem pogody
- Kontrola limitów tur (domyślnie 10)

**Kluczowe metody:**
- `next_turn()` - przechodzi do następnego gracza
- `rozpocznij_nowa_ture()` - inicjuje nową turę z pogodą
- `get_current_player()` - zwraca aktywnego gracza
- `is_game_over(max_turns)` - kontrola końca gry

**Integracja:**
- Używany przez główne pliki gry (`main.py`, `main_ai.py`)
- Reset akcji artylerii (`token.reset_turn_actions()`)
- Generowanie pogody co 6 tur

**Czy duplikat?** ❌ NIE - unikalny menedżer sekwencji gry

---

### ✅ **unit_factory.py** - FABRYKA JEDNOSTEK

**Status:** AKTYWNY I BARDZO POTRZEBNY ✅  
**Funkcjonalność:**
- Centralna definicja statystyk wszystkich typów jednostek
- Identyczne dane jak w `token_shop.update_stats` (single source of truth)
- Wsparcia, upgrady, ceny, statystyki combat/defense
- Dozwolone kombinacje typów jednostek i wsparć

**Kluczowe komponenty:**
- `RANGE_DEFAULTS`, `MOVE_DEFAULTS`, `ATTACK_DEFAULTS` - podstawowe statystyki
- `COMBAT_DEFAULTS`, `DEFENSE_DEFAULTS` - wartości bojowe
- `PRICE_DEFAULTS`, `MAINTENANCE_DEFAULTS` - ekonomia jednostek
- `SUPPORT_UPGRADES` - bonusy od wsparcia
- `ALLOWED_SUPPORT` - matrix kompatybilności

**Integracja:**
- Używany przez `edytory/prototyp_kreator_armii.py` do obliczania statystyk
- Pozwala AI obliczać parametry jednostek z jednego źródła
- Synchronizacja z token shop systemem

**Czy duplikat?** ❌ NIE - to jest WYMAGANE centrum danych jednostek

---

### ⚠️ **zwyciestwo.py** - KLASA VictoryConditions

**Status:** CZĘŚCIOWY - WYMAGA DOKOŃCZENIA ⚠️  
**Funkcjonalność:**
- Warunki zwycięstwa: turns (standardowy) vs elimination
- Limity tur: 10, 20, 30 (domyślnie 30)
- Sprawdzanie końca gry i wyznaczanie zwycięzcy

**Kluczowe metody:**
- `check_game_over(current_turn, players)` - główna logika
- `_check_elimination_victory(players)` - eliminacja wrogów
- `_determine_victory_points_winner(players)` - zwycięstwo punktowe

**Problemy:**
- Niekompletna implementacja `_check_elimination_victory()`
- Błędy importu modułów (`sys.modules`)
- Nieskończone fragmenty kodu

**Integracja:**
- Nie jest jeszcze używany w głównej grze
- Przygotowany do integracji z `engine/engine.py`

**Czy duplikat?** ❌ NIE - jedyna logika warunków zwycięstwa

---

### ❌ **dyplomacja.py** - PUSTY PLIK

**Status:** DO IMPLEMENTACJI W PRZYSZŁOŚCI ❌  
**Zawartość:** Tylko komentarz "Plik do dalszej implementacji"

**Planowana funkcjonalność:**
- System sojuszy między nacjami
- Mechaniki dyplomatyczne
- Negocjacje między graczami

**Czy potrzebny teraz?** ❌ NIE - to feature na przyszłość

---

### ❌ **rozkazy.py** - PUSTY PLIK  

**Status:** PUSTY - NIEZNANE PRZEZNACZENIE ❌  
**Zawartość:** Kompletnie pusty plik

**Czy potrzebny?** ❌ NIE - brak implementacji i planu

---

## 🔍 ANALIZA DUPLIKATÓW I REDUNDANCJI

### ✅ **BRAK DUPLIKATÓW W FOLDERZE CORE**

Po szczegółowej analizie **WSZYSTKIE AKTYWNE PLIKI W CORE/ SĄ UNIKATOWE**:

1. **ekonomia.py** ≠ engine ekonomia - core zajmuje się logiką PE, engine zarządza keypoints
2. **pogoda.py** ≠ engine pogoda - core generuje, engine/GUI wykorzystuje
3. **tura.py** ≠ engine turns - core zarządza sekwencją, engine wykonuje akcje
4. **unit_factory.py** ≠ engine units - core definiuje statystyki, engine obsługuje tokens

### ⚠️ **POTENCJALNE USPRAWNIENIA**

1. **Przenieść `unit_factory.py`** → `engine/unit_factory.py`
   - Lepsze grupowanie z resztą logiki jednostek
   - Bliżej `token.py` i `action_refactored_clean.py`

2. **Dokończyć `zwyciestwo.py`**
   - Naprawić błędy implementacji
   - Dodać do głównego flow gry

3. **Usunąć puste pliki**
   - `dyplomacja.py` - dodać gdy potrzebny
   - `rozkazy.py` - usunąć lub określić cel

---

## 📊 PODSUMOWANIE I REKOMENDACJE

### ✅ **PLIKI DO ZACHOWANIA (5/7)**

| Plik | Status | Priorytet | Akcja |
|------|--------|-----------|-------|
| `ekonomia.py` | ✅ AKTYWNY | WYSOKI | Zachować - kluczowy dla PE |
| `pogoda.py` | ✅ AKTYWNY | ŚREDNI | Zachować - system pogody |
| `tura.py` | ✅ AKTYWNY | WYSOKI | Zachować - zarządza grą |
| `unit_factory.py` | ✅ AKTYWNY | WYSOKI | Rozważyć przeniesienie → engine/ |
| `zwyciestwo.py` | ⚠️ CZĘŚCIOWY | ŚREDNI | Dokończyć implementację |

### ❌ **PLIKI DO USUNIĘCIA (2/7)**

| Plik | Powód | Akcja |
|------|-------|--------|
| `dyplomacja.py` | Pusty placeholder | Usunąć lub przenieść do plans/ |
| `rozkazy.py` | Pusty bez celu | Usunąć |

### 🎯 **WNIOSKI**

1. **FOLDER CORE JEST POTRZEBNY** - zawiera unikatową logikę biznesową
2. **BRAK DUPLIKATÓW** - wszystkie aktywne pliki mają różne odpowiedzialności  
3. **ORGANIZACJA DOBRA** - logiczne grupowanie funkcjonalności
4. **POTRZEBA CLEANUP** - usunąć 2 puste pliki
5. **OPCJONALNE REFACTOR** - przenieść `unit_factory.py` do `engine/`

**REKOMENDACJA KOŃCOWA:** Zachować folder `core/` z 5 aktywnymi plikami, usunąć 2 puste, opcjonalnie zrefaktorować lokalizację `unit_factory.py`.

---

**📝 Dokument utworzony:** 6 września 2025  
**👤 Autor:** GitHub Copilot  
**📂 Lokalizacja:** `/core/ANALIZA_FOLDERU_CORE.md`
