# 📁 ANALIZA FOLDERU `core/` – Kampania 1939

## 📌 Stan na 1 października 2025 (wersja 3.8)
- `core/` dostarcza wspólne systemy ekonomii, tur, pogody i warunków zwycięstwa współdzielone przez launchery human oraz AI (`main.py`, `ai_launcher.py`).
- Kluczowe klasy (`EconomySystem`, `TurnManager`, `VictoryConditions`) są włączone do bieżącej rozgrywki i wykorzystywane zarówno w interfejsach GUI, jak i w testach regresyjnych.
- `unit_factory.py` pozostaje jedynym źródłem prawdy dla statystyk jednostek; wyniki muszą być zgodne z `gui/token_shop.py`.
- W katalogu pozostał jeden placeholder (`dyplomacja.py`) przewidziany na przyszłe rozszerzenia.
- Warstwa logowania sesji została przeniesiona pod `ai/logs/` i korzysta z `utils/session_manager.py` oraz `utils/session_archiver.py` do rotacji i archiwizacji.

## 🗂️ Zawartość katalogu

| Plik | Status | Główna odpowiedzialność | Kluczowe integracje |
|------|--------|-------------------------|----------------------|
| `ekonomia.py` | ✅ aktywny | System punktów ekonomicznych i specjalnych (PE) | `engine.process_key_points`, `ai/general`, `ai/commander`, GUI generała |
| `pogoda.py` | ✅ aktywny | Generator pogody z ograniczeniami historycznymi | `core.tura.TurnManager`, panele pogodowe GUI |
| `tura.py` | ✅ aktywny | Zarządzanie turami, resetami jednostek, porami dnia | Launchery (`main.py`, `ai_launcher.py`), `engine.update_all_players_visibility` |
| `unit_factory.py` | ✅ aktywny | Fabryka statystyk żetonów (koszty, zasięgi, wsparcia) | `gui.token_shop`, testy balansowe (`tests/test_unit_factory_parity.py`) |
| `zwyciestwo.py` | ✅ aktywny | Warunki zwycięstwa: limit tur lub eliminacja | Launchery (ekrany końcowe), `VictoryConditions` w testach integracyjnych |
| `dyplomacja.py` | ⚪ placeholder | Rezerwacja pod przyszły system sojuszy | Brak – nieużywany |

> W katalogu nie ma już pliku `rozkazy.py`; poprzednie odniesienia można traktować jako archiwalne.

## 🔍 Szczegółowe moduły

### `ekonomia.py` – `EconomySystem`
- Generuje losowe PE (1–100) i 1 punkt specjalny na turę dowódcy/generała.
- `subtract_points` chroni przed zejściem poniżej zera i raportuje blokady w konsoli.
- `EconomySystem` jest tworzony dla każdego gracza (`engine/engine.py`) i synchronizowany w AI (`GeneralAI.execute_turn`, `CommanderAI._sync_player_points`).
- Testy regresyjne: `tests/test_polish_logging.py`, `tests/test_key_points.py`, `tests/ai/test_ai_basic.py` (przepływ PE).

### `pogoda.py` – `Pogoda`
- Losuje temperaturę (-5 °C do 25 °C), zachmurzenie i opady z ograniczeniem ±2 °C per doba.
- `TurnManager` odświeża pogodę co 6 tur (1 doba) i generuje raport tekstowy wykorzystywany w panelach GUI.
- Jeśli zajdzie potrzeba rozszerzeń (wiatr, mgła), moduł posiada gotowe pola na dodatkowe parametry.

### `tura.py` – `TurnManager`
- Przechowuje kolejność graczy, aktualną turę i udostępnia helpery czasu (`get_day_number`, `get_day_phase`, `get_current_date`).
- Resetuje `currentMovePoints`, `maxMovePoints` i liczniki artylerii (`token.reset_turn_actions`) na początku pełnej tury.
- Integruje `Pogoda` i generuje raport `Data/Dzień | Pora dnia | Pogoda` dla `PanelGenerala` i `PanelDowodcy`.
- Zewnętrzne moduły (np. `engine.VisionService`) korzystają z `get_day_phase` do modyfikacji progów detekcji.

### `unit_factory.py`
- Przechowuje słowniki statystyk (zasięgi, ruch, atak, ceny, wsparcia) odwzorowane 1:1 względem `gui/token_shop.update_stats`.
- Funkcje pomocnicze (`get_unit_defaults`, `build_unit_stats`, `describe_unit`) umożliwiają spójną prezentację danych w GUI i testach.
- Testy spójności: `tests/test_unit_factory_parity.py`, `tests/test_token_workflow.py`, `tests/test_balance_parity_token_shop.py`.
- Pozostaje w `core/`, ponieważ jest wykorzystywany równocześnie przez GUI, testy balansowe i narzędzia analityczne.

### `zwyciestwo.py` – `VictoryConditions`
- Obsługuje dwa tryby: *turns* (porównanie Victory Points po ukończeniu limitu tur) i *elimination* (do ostatniego żyjącego narodu).
- `main.py` oraz `ai_launcher.py` tworzą obiekt `VictoryConditions` przy starcie gry i sprawdzają stan w pętli wydarzeń.
- `_check_elimination_victory` zakłada istnienie metody `player.has_living_units(game_engine)`; w przypadku braku danych fallback kończy grę dopiero po wyzerowaniu wszystkich graczy.
- `_determine_victory_points_winner` agreguje VP per naród i wykrywa remisy.
- Do uzupełnienia w kolejnych iteracjach: dokładna detekcja żywych jednostek bez odwołań do `sys.modules`, formatowanie komunikatu zwycięstwa dla GUIs.

### `dyplomacja.py`
- Plik utrzymany jako placeholder – brak implementacji oraz referencji w kodzie.
- Zalecane: albo usunięcie do katalogu `plans/`, albo pozostawienie z krótkim opisem planowanej funkcjonalności przy pierwszej implementacji.

## 🔗 Integracje z innymi katalogami
- `engine/engine.py` wykorzystuje `EconomySystem` oraz `VictoryConditions`; reset widoczności i generowanie PE odbywa się w ramach jednej logiki.
- GUI (`gui/panel_generala.py`, `gui/panel_dowodcy.py`) korzysta z `TurnManager`, `EconomySystem` i raportów pogodowych.
- AI (`ai/general`, `ai/commander`, `ai/tokens`) używa wyłącznie publicznych metod `EconomySystem` i danych o turze.
- Testy automatyczne w `tests/` zakładają obecność wszystkich funkcji opisanych powyżej – zmiany w API wymagają aktualizacji fixtures.

## 🧪 Pokrycie testami
- `tests/core/` – testy jednostkowe `TurnManager`, generatora pogody i ekonomii.
- `tests/ai/` – weryfikacja przepływu PE i integracji z `EconomySystem`.
- `tests/integration/test_system_ready.py` – smoke test całego przepływu tury z wykorzystaniem `VictoryConditions`.
- `tests/test_polish_logging.py` – potwierdza współpracę `TurnManager` z systemem logowania (sesje dzienne).

## ✅ Rekomendacje dalszych prac
1. **VictoryConditions** – oczyścić mechanizm wyszukiwania `GameEngine` (zastąpić logiką wstrzykiwaną z launchera) i dostarczyć pełne komunikaty dla GUI.
2. **EconomySystem** – rozważyć parametr startowej wartości PE oraz deterministyczny generator na potrzeby testów.
3. **Dyplomacja** – zdecydować o implementacji (system sojuszy) lub przenieść opis do dokumentacji planów (`plans/`).
4. **Unit Factory** – utrzymać synchronizację z `gui/token_shop.py`; każdy refaktoring powinien być potwierdzony testami `test_unit_factory_parity.py`.

---
**Dokument zaktualizowany:** 1 października 2025  
**Autor aktualizacji:** GitHub Copilot  
**Lokalizacja:** `core/ANALIZA_FOLDERU_CORE.md`
