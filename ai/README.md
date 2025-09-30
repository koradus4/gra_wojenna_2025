# AI System - Jednolite zasady dla AI i człowieka

## Zasady projektowe
1. AI używa TYLKO istniejących reguł gry - żadnych specjalnych mechanik
2. AI wykonuje te same akcje co człowiek: MoveAction, CombatAction przez engine.execute_action()
3. AI respektuje te same ograniczenia: MP, paliwo, zasięgi, właścicieli
4. Żetony nie atakują sojuszników (owner validation)
5. Wszystkie nowe reguły muszą być zatwierdzone i zunifikowane dla AI+human

## Architektura AI
System hierarchiczny:
- **Żetony (TokenAI)**: Autonomiczne jednostki z percepcją i specjalizacją
- **Dowódcy (CommanderAI)**: Zarządzanie małymi grupami (max 3 żetony/turę)
- **Generałowie (GeneralAI)**: Dystrybucja PE, strategia wysokopoziomowa

### Owner format
`"{player_id} ({nation})"` np. `"2 (Polska)"`, `"5 (Niemcy)"`
- Polacy (owner zawiera "(Polska)") nie walczą z Polakami
- Niemcy (owner zawiera "(Niemcy)") nie walczą z Niemcami

## Struktura katalogów
```
ai/
├── tokens/           - Logika autonomicznych żetonów
├── commander/        - AI dowódcy, zarządzanie grupami
├── general/         - AI generała, dystrybucja PE
├── tests/           - Testy systemu AI
└── logs/            - Centralne logowanie AI
```

## Specjalizacja żetonów
- **Zaopatrzenie (Z)**: Zbieranie PE z punktów kluczowych
- **Kawaleria (K)**: Zwiad, szybkie przemieszczenie
- **Artyleria (AC/AL/AP)**: Pozycjonowanie, wsparcie ogniowe
- **Piechota (P/TL/TS)**: Obrona, utrzymanie pozycji
- **Drenaż (D)**: Specjalne operacje
- **Garnizony (G)**: Obrona miast i punktów strategicznych

## System PE (Punkty Ekonomiczne)
GeneralAI:
- Rezerwuje 10% PE dla nieprzewidzianych potrzeb
- Dystrybuuje 90% równomiernie między aktywnych dowódców
- Loguje pełen przebieg przekazania środków (CSV + log tekstowy)

CommanderAI:
- Przejmuje całą pulę PE przekazaną przez generała i magazynuje ją w rezerwie dowódcy
- Na starcie tury odzyskuje niewykorzystane przydziały żetonów i dokłada je do rezerwy
- Dzieli rezerwę **po równo** na wszystkie własne żetony (reszta zostaje w puli dowódcy)
- Utrzymuje przydział w atrybutach żetonu (`ai_reserved_pe`, `ai_commander_id`) – logika żetonu może korzystać z tej informacji
- Aktywacja żetonu kosztuje 1 PE z jego przydziału; brak środków zatrzymuje turę jednostki
- Zarządza maksymalnie 3 żetonami na turę (limit operacyjny)

## Logowanie
Wszystkie operacje AI zapisywane są równolegle w dwóch formatach:

- **Tekst** (`ai/logs/<component>/text/YYYY-MM-DD.log`) – log czytelny dla człowieka, z kontekstem w formie `klucz=wartość`.
- **CSV** (`ai/logs/<component>/csv/YYYY-MM-DD.csv`) – strukturalne dane gotowe do analizy (kolumny: `timestamp`, `component`, `level`, `message`, `context`).

Obsługiwane komponenty: `general`, `commander`, `tokens`, `debug`.

Dodatkowo dostępny jest skrypt `ai/logs/czyszczenie_logow.py`, który pozwala interaktywnie lub parametrycznie usuwać stare logi (obsługuje `--days`, `--all`, `--dry-run`).

## Launcher AI
`ai_launcher.py` - GUI do konfiguracji gier mieszanych AI/Human:
- Wybór AI/Human dla każdego gracza
- Podgląd konfiguracji w czasie rzeczywistym
- Integracja z główną pętlą gry

## Testy
Uruchom wszystkie testy AI:
```
python ai/tests/run_all_tests.py
```

## Status implementacji
✅ System żetonów z specjalizacją
✅ AI Generała z dystrybucją PE  
✅ AI Dowódcy z zarządzaniem grupami
✅ Launcher gier mieszanych
✅ System logowania
✅ Pełny zestaw testów
✅ Organizacja kodu (tests/, logs/)

System AI jest gotowy do użycia!

## Zależności modułów
- `ai/__init__.py` eksportuje kluczowe klasy (`GeneralAI`, `CommanderAI`, `TokenAI`) oraz funkcje logujące, dzięki czemu pozostałe części projektu mogą je importować z jednego miejsca.
- `ai/general/general_ai.py` korzysta z `engine.player.Player`, `core.ekonomia.EconomySystem` oraz funkcji logujących z `ai.logs`. Nie wykonuje akcji bezpośrednio na mapie – tylko rozdziela PE pomiędzy graczy o roli „Dowódca”.
- `ai/commander/commander_ai.py` współpracuje z `GeneralAI` poprzez ekonomię gracza (odbiera przekazane PE), tworzy żetonowe AI przez `ai.tokens.create_token_ai`, korzysta z logów (`ai.logs`) i oczekuje od `game_engine` listy `tokens` oraz metody `execute_action` (tej samej, której używa human).
- `ai/tokens/token_ai.py` opiera się wyłącznie na istniejącej logice gry: importuje `MoveAction` i `CombatAction` z `engine.action_refactored_clean`, odczytuje statystyki żetonu (`stats`, `currentMovePoints`, `currentFuel`) oraz wykorzystuje `engine.board.hex_distance` do oceny dystansu.
- `ai/tokens/specialized_ai.py` rozszerza `TokenAI` i używa dodatkowych danych silnika: `engine.key_points` (Z – zaopatrzenie), `engine.tokens` (detekcja wrogów) oraz mapy (`board`).
- `ai/logs/ai_logger.py` tworzy centralną instancję loggera opartą na standardowej bibliotece (`os`, `datetime`). Funkcje skrótowe (`log_general`, `log_commander`, itd.) są wykorzystywane w każdym poziomie AI.
- `ai/tests/…` odzwierciedla zależności runtime – importuje `core.ekonomia.EconomySystem`, `engine.player.Player`, korzysta z fabryki żetonów oraz tworzy proste mocki `engine`/`board`.

## Przepływ sterowania w turze AI
1. **Generał (`GeneralAI.execute_turn`)**: generuje PE, rezerwuje 10%, resztę dzieli (równie) pomiędzy dowódców tej samej nacji. Każde przekazanie odbywa się przez metody ekonomii (`subtract_points` / `add_economic_points`), co gwarantuje, że AI korzysta z tych samych mechanizmów co human.
2. **Dowódca (`CommanderAI.execute_turn`)**: odczytuje przekazane PE z własnej ekonomii, filtruje żetony `game_engine.tokens` po właścicielu (`"id (Nacja)"`), ogranicza się do maksymalnie 3 jednostek i dla każdej tworzy odpowiednie AI przez `create_token_ai`.
3. **Żetony (`TokenAI.execute_turn`)**: wybierają cel ruchu i ewentualnego ataku, następnie przekazują decyzje do silnika poprzez `engine.execute_action(MoveAction/CombatAction, player=…)`. Weryfikacja wrogów oraz zasięgów odbywa się wyłącznie przez istniejące atrybuty i metody silnika (`stats`, `board.hex_distance`, `can_attack`).
4. **Logowanie (`ai.logs`)**: każdy poziom AI raportuje swoje działania; powstają dzienne pliki `ai_general_YYYY-MM-DD.log`, `ai_commander_YYYY-MM-DD.log`, `ai_tokens_YYYY-MM-DD.log` i `ai_debug_YYYY-MM-DD.log`.

### Powiązania z innymi modułami gry
- **Silnik (`engine`)**: AI nie ma własnych akcji – wywołuje `engine.execute_action`, korzysta z `engine.board` oraz struktur tokenów dostarczanych przez silnik gry.
- **Ekonomia (`core.ekonomia`)**: wszystkie operacje na PE przechodzą przez ten sam system co w trybie human.
- **Gracze (`engine.player.Player`)**: AI wymaga, aby obiekty graczy miały poprawnie skonfigurowaną ekonomię oraz role (`Generał`, `Dowódca`).
- **Launcher (`ai_launcher.py`, poza folderem ai)**: buduje konfigurację (AI/Human) i instancjonuje odpowiednie klasy bazując na eksporcie `ai/__init__.py`.

## Testy i mocki
- `ai/tests/run_all_tests.py` uruchamia oba zestawy testów i demonstruje scenariusz końca-to-końca.
- Testy należy odpalać z katalogu `ai/tests/` (lub zadbać o poprawny `PYTHONPATH`), aby unikać błędów `attempted relative import with no known parent package`.
- `test_ai_basic.py` mockuje minimalny `GameEngine` bez planszy – pokazuje, że logika dowódcy nie wymaga dostępu do `board` (błędy w toku testów wynikają z braku pełnego mocka i są celowo logowane jako ostrzeżenia).
- `test_token_ai.py` tworzy mock planszy z metodą `hex_distance`, key pointy i strikte pokazuje, jak `TokenAI` korzysta z istniejących mechanizmów ruchu/ataku.

## Dodatkowe uwagi implementacyjne
- W kodzie zachowano zasadę: **brak nowych reguł** – AI używa dokładnie tych samych metod, zasobów i ograniczeń co gracze human.
- `create_token_ai` zwraca `InfantryTokenAI` jako domyślne zachowanie, jeśli `unitType` nie jest rozpoznany, co zabezpiecza system przed brakiem specjalizacji.
- Logger tworzy pliki na podstawie bieżącej daty – przy długich sesjach warto rotować logi lub czyścić folder `ai/logs/`.