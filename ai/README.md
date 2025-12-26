ai/
# AI System – stan minimalny zgodny z zasadami gry

Ostatnia aktualizacja: **1 października 2025**

## Zasady projektowe
1. AI korzysta **wyłącznie** z istniejących mechanik silnika (`MoveAction`, `CombatAction`).
2. Wszystkie limity (MP, paliwo, zasięgi, właściciel) są sprawdzane w tych samych miejscach co dla gracza human.
3. Brak „skryptów specjalnych” – decyzje AI kończą się zawsze wywołaniem `engine.execute_action`.
4. Walidacja właściciela (`"{player_id} ({nation})"`) chroni przed atakami na sojuszników.
5. Wszelkie rozszerzenia muszą nadal zachowywać symetrię zasad human ⇄ AI.

## Architektura i obecny poziom zaawansowania
Hierarchia pozostaje trzywarstwowa, ale wszystkie warstwy działają w **uproszczonym** trybie bazowym:

- **TokenAI** – uniwersalna klasa żetonu wspierana przez lekkie specjalizacje (`ai/tokens/specialized_ai.py`), reagująca na najbliższych wrogów, patrolująca otoczenie i zarządzająca budżetem PE (paliwo/CV).
- **CommanderAI** – zbiera listę własnych żetonów na podstawie właściciela (`"ID (Nacja)"`), dzieli dostępne PE po równo, uruchamia `TokenAI` i konsoliduje raporty/zwroty w logach `ai/logs/commander/`.
- **GeneralAI** – generuje PE w `EconomySystem`, tworzy profile dowódców (liczba żetonów, średnia konsumpcja), rezerwuje adaptacyjnie 10–20% środków i rozdaje resztę proporcjonalnie, raportując do `ai/logs/general/`.

> **Uwaga:** System specjalistów pozostaje minimalistyczny – aktywnie działa tylko wariant dla konwojów zaopatrzeniowych (`SupplySpecialist`), a brak jest globalnych rankingów celów, modułu konfiguracji AI oraz pamięci strategicznej. Pozostałe typy korzystają z domyślnego `GenericSpecialist`.

## Struktura katalogów
```
ai/
├── commander/        # Minimalny CommanderAI
├── general/          # Adaptacyjny GeneralAI
├── logs/             # Logger AI + sesje/archiwa (`ai/logs/...`)
├── tests/            # Testy jednostkowe AI
├── tokens/           # TokenAI + system specjalistów i pamięć współdzielona
└── README.md         # Ten dokument
```

## Zarządzanie punktami ekonomicznymi (PE)

**GeneralAI**
- Generuje PE i punkty specjalne przez `EconomySystem`.
- Utrzymuje bufor rezerwy (`base_reserve_ratio = 0.15`) korygowany w przedziale 10–20% na podstawie historii przydziałów.
- Buduje profil każdego dowódcy (liczba żetonów, minimalny koszt aktywacji, prosty „headroom”).
- Rozdaje środki proporcjonalnie do wymaganego minimum i zapotrzebowania, zapisując historię przydziałów.

**CommanderAI**
- Synchronizuje PE gracza z obiektem `EconomySystem` i aktualizuje `player.punkty_ekonomiczne`.
- Dzieli dostępny budżet po równo między wszystkie posiadane żetony (brak limitu 3 jednostek, brak priorytetów typów).
- Dla każdego żetonu tworzy `TokenAI`, przekazuje budżet, rejestruje faktyczne wydatki oraz refundy i loguje zbiorcze podsumowanie.
- Po turze przywraca niewykorzystane punkty do ekonomii dowódcy.

**TokenAI**
- Klasyfikuje status (`normal`, `low_fuel`, `threatened`, `urgent_retreat`) i dobiera profil akcji (`retreat`, `recovery`, `combat`, `patrol`).
- Próbuje wykonać ruch (z priorytetem na zagrożenia lub cele specjalisty), a przy braku MP może doładować paliwo w trakcie marszu.
- Wykonuje pojedynczy atak, jeśli wróg znajduje się w zasięgu i heurystyki (bazowe lub specjalisty) go nie blokują.
- Pozostały budżet przeznacza na uzupełnienie paliwa i wartości bojowej (`combat_value`), raportując niewykorzystane PE.
- Loguje cały przebieg tury do `ai/logs/tokens/` wraz z flagami specjalistów, wynikiem ruchu/ataku i zmianami zasobów.

## Logowanie
- Każda warstwa loguje do dwóch formatów: tekst (`ai/logs/<component>/text/...`) i CSV (`ai/logs/<component>/csv/...`).
- Bieżąca sesja trafia do `ai/logs/sessions/<timestamp>/`, archiwizacją zajmuje się `utils/session_archiver.py`, a utrzymaniem sesji `utils/session_manager.py`.
- Dostępny jest skrypt `ai/logs/czyszczenie_logow.py` z opcjami `--days`, `--all`, `--dry-run`; używany m.in. z launcherów GUI.

## Uruchamianie AI
- **Launcher mieszany:** `ai_launcher.py` (konfiguracja Human/AI na gracza, czyszczenie logów, start gry).
- **Skrypty narzędziowe:** `scripts/auto_ai_session.py` (symulacje AI vs AI) korzystają z tych samych klas `GeneralAI` / `CommanderAI`.

## Testy
```
python ai/tests/run_all_tests.py
```
Pakiet zawiera:
- `test_ai_basic.py` – smoke test Generała i Dowódcy na mocku silnika.
- `test_token_ai.py` – weryfikacja heurystyk ruchu/ataku z uproszczoną planszą hex.

## Powiązania z innymi modułami
- `ai/__init__.py` eksportuje `GeneralAI`, `CommanderAI`, `TokenAI` oraz funkcje logujące.
- `core.ekonomia.EconomySystem` dostarcza jedyny kanał operacji na PE.
- `engine.action_refactored_clean` dostarcza `MoveAction` i `CombatAction` używane przez `TokenAI`.
- `ai/logs/ai_logger.py` odpowiada za mapowanie logów do CSV/tekst.

## Znane ograniczenia
- Tylko konwoje zaopatrzeniowe mają dedykowanego specjalistę; reszta żetonów używa `GenericSpecialist`.
- Brak limitów aktywacji, priorytetów celów czy rotacji garnizonów na poziomie CommanderAI.
- TokenAI nie prowadzi planowania wielotaktowego – pamięć służy jedynie do rejestrowania nieudanych hexów.
- System logowania nie agreguje metryk ML – katalogi `ai/logs/dane_ml/` pozostają nieużywane.
- Współdzielona pamięć wywiadowcza (SharedIntelMemory) przechowuje tylko ostatnie wykrycia; brak centralnego systemu dowodzenia.

Mimo uproszczeń kod zapewnia punkt wyjścia do dalszego rozwoju – przestrzeganie powyższych zasad umożliwia stopniowe rozbudowywanie logiki bez łamania parytetu z graczem human.