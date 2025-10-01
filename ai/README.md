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

- **TokenAI** – jedna wspólna klasa reagująca na najbliższych wrogów, patrolująca otoczenie i zużywająca przydzielony budżet PE na paliwo/CV.
- **CommanderAI** – zbiera listę własnych żetonów na podstawie właściciela (`"ID (Nacja)"`), dzieli dostępne PE po równo, uruchamia `TokenAI` i raportuje logi.
- **GeneralAI** – generuje PE w `EconomySystem`, tworzy proste profile dowódców (liczba żetonów, średnie zużycie), rezerwuje adaptacyjnie 10–20% środków i rozdaje resztę proporcjonalnie.

> **Uwaga:** W tej gałęzi brak specjalizacji żetonów, rankingów celów, modułu konfiguracji AI oraz pamięci strategicznej. `ai/tokens/specialized_ai.py` jest stubbem utrzymującym kompatybilność importów.

## Struktura katalogów
```
ai/
├── commander/        # Minimalny CommanderAI
├── general/          # Adaptacyjny GeneralAI
├── logs/             # Logger i narzędzia czyszczenia logów
├── tests/            # Testy jednostkowe AI
├── tokens/           # TokenAI + fabryka stub
└── README.md         # Ten dokument
```

## Zarządzanie punktami ekonomicznymi (PE)

**GeneralAI**
- Generuje PE i punkty specjalne przez `EconomySystem`.
- Utrzymuje bufor rezerwy (`base_reserve_ratio = 0.15`) korygowany w przedziale 10–20% na podstawie historii przydziałów.
- Buduje profil każdego dowódcy (liczba żetonów, minimalny koszt aktywacji, prosty „headroom”).
- Rozdaje środki proporcjonalnie do wymaganego minimum i zapotrzebowania, zapisując historię przydziałów.

**CommanderAI**
- Synchronizuje PE gracza z obiektem `EconomySystem`.
- Dzieli dostępny budżet po równo między wszystkie posiadane żetony (brak limitu 3 jednostek).
- Dla każdego żetonu tworzy `TokenAI`, przekazuje mu budżet i zapisuje ile PE zostało faktycznie wydane/zwroconego.
- Po turze przywraca niewykorzystane punkty do ekonomii dowódcy.

**TokenAI**
- Próbuje wykonać ruch (priorytet najbliższy wróg, inaczej patrol najtańszych heksów).
- Wykonuje pojedynczy atak, jeśli wróg znajduje się w zasięgu.
- Pozostały budżet przeznacza na uzupełnienie paliwa i wartości bojowej (`combat_value`).
- Loguje cały przebieg tury wraz z raportem z ruchu, ataku i resupply.

## Logowanie
- Każda warstwa loguje do dwóch formatów: tekst (`ai/logs/<component>/text/…`) i CSV (`ai/logs/<component>/csv/…`).
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
- Brak specjalizacji żetonów i konfiguracji profili AI – wszystkie jednostki zachowują się identycznie.
- Dowódca nie zarządza limitami aktywacji, priorytetami celów ani rotacją garnizonów.
- TokenAI nie posiada pamięci ani planowania wielotaktowego; reaguje wyłącznie na stan bieżący.
- System logowania nie agreguje metryk ML – katalogi `logs/dane_ml/` są obecnie nieużywane przez AI.

Mimo uproszczeń kod zapewnia punkt wyjścia do dalszego rozwoju – przestrzeganie powyższych zasad umożliwia stopniowe rozbudowywanie logiki bez łamania parytetu z graczem human.