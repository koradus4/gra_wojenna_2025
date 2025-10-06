# Token AI – aktualny stan minimalny

System `ai/tokens` obsługuje **pojedynczą** klasę `TokenAI`, ale umożliwia lekkie specjalizacje dostarczane przez moduł `specialized_ai.py`. Bazowa logika odpowiada za wspólne zachowania, a wybrane typy jednostek (np. konwoje zaopatrzeniowe) mogą delikatnie korygować decyzje bez łamania symetrii względem graczy human.

## Pliki
- `token_ai.py` – pełna implementacja zachowania żetonu (statusy, profil akcji, ruch/atak/resupply, logowanie).
- `specialized_ai.py` – fabryka (`create_token_ai`) dobierająca specjalistę; zawiera m.in. `SupplySpecialist`, współdzieloną pamięć kontaktów (`SharedIntelMemory`) i placeholdere pod kolejne typy.
- `__init__.py` – eksport `TokenAI` i `create_token_ai`.

## Przebieg tury (`TokenAI.execute_turn`)
1. **Log startu** – zapisuje stan wejściowy (pozycja, zapas MP/fuel, budżet PE, status, profil akcji, notatki specjalisty) do `ai/logs/tokens/`.
2. **Klasyfikacja** – bazowa heurystyka ocenia paliwo, CV i zagrożenie (`danger_zones`), nadaje status (`normal`, `low_fuel`, `threatened`, `urgent_retreat`) i dobiera profil akcji (`retreat`, `recovery`, `combat`, `patrol`). Specjalista może ten wybór skorygować.
3. **Ruch** – jeśli żeton może się poruszać, iteruje kandydatów:
   - gdy widzi wrogów lub posiada wskazany cel specjalisty (np. Key Point dla konwoju), dobiera kierunek skracający dystans;
   - w pozostałych przypadkach patroluje najtańsze sąsiednie heksy (`move_mod` rosnąco).
   Każdy krok wykonywany jest przez `MoveAction`; w razie braku MP żeton próbuje uzupełnić paliwo z bieżącego budżetu PE.
4. **Atak** – wyszukuje cel w zasięgu (`attack.range`) i odpala `CombatAction`, o ile heurystyki (bazowe lub specjalisty) go nie blokują.
5. **Resupply** – pozostały budżet PE przeznacza na paliwo (`currentFuel → maxFuel`) i combat value (`combat_value → stats['combat_value']`), raportując rezerwę do zwrotu dowódcy.
6. **Log końcowy** – zapisuje wykorzystany budżet, powodzenie ruchu/ataku, zużycie paliwa oraz flagi specjalisty (np. garnizon na KP, niski poziom paliwa).

## Pipeline autonomicznego żetonu (w pigułce)

1. **Odbierz kontekst** – Commander przekazuje `engine`, `player` i budżet PE; `TokenAI` buduje słownik kontekstu (pozycja, paliwo, CV, widoczni wrogowie, wspólna pamięć wywiadowcza, flagi specjalisty).
2. **Sklasyfikuj status** – bazowa heurystyka wybiera status (`normal`, `low_fuel`, `threatened`, `urgent_retreat`), po czym specjalista może go skorygować (np. wymusić retreat).
3. **Ułóż plan** – status mapowany jest na profil akcji (`retreat`, `recovery`, `combat`, `patrol`), a następnie na listę kroków (`refuel_minimum`, `restore_cv`, `maneuver`, `withdraw`, `attack`). Specjalista może dodać/usunąć kroki (np. konwój usuwa `attack`).
4. **Wykonuj akcje** – każda akcja (ruch, atak, resupply) aktualizuje kontekst i loguje wynik. Ruch korzysta z `MoveAction`, atak z `CombatAction`, a resupply konsumuje budżet PE.
5. **Bilansuj zasoby** – niewykorzystane PE trafiają do raportu refundu, paliwo/CV są uzupełniane w zależności od priorytetów.
6. **Raportuj** – log końcowy zawiera podsumowanie ruchu, ataku, resupply, wykorzystanie PE oraz flagi pomocne przy analizie (np. „garnizon_na_kp”).

## Ważniejsze metody

| Metoda                         | Opis                                                                                   |
|--------------------------------|----------------------------------------------------------------------------------------|
| `_candidate_moves(engine)`     | Generuje listę heksów, do których warto spróbować się przemieścić (wróg → patrol → cel specjalisty). |
| `_perform_movement(...)`       | Iteruje po kandydatach, woła `MoveAction` i loguje niepowodzenia.                      |
| `_select_attack_target(...)`   | Wyszukuje najbliższego wroga w zasięgu broni.                                          |
| `_perform_attack(...)`         | Odpala `CombatAction`, interpretuje wynik i przygotowuje raport do logów (wraz z kontratakiem). |
| `_perform_resupply(...)`       | Zużywa przydzielony budżet na paliwo i combat value (w tej kolejności).               |
| `_is_enemy(other)`             | Porównuje nacje na podstawie napisu właściciela (`"ID (Nacja)"`).                      |
| `_is_destroyed_after_attack`   | Weryfikuje, czy żeton przetrwał po walce (na podstawie logów i obecności na planszy). |

Cała logika operuje na istniejących strukturach silnika (`engine.board`, `engine.tokens`, `MoveAction`, `CombatAction`).

## Integracja z CommanderAI
`CommanderAI` przydziela każdemu żetonowi równy budżet PE i wywołuje `TokenAI.execute_turn(engine, player, share)`. Zwrócona wartość (`spent_pe`) służy do wyliczenia refundu i raportowania budżetu w logach dowódcy; dodatkowo dowódca agreguje flagi specjalistów i human-notes w zbiorczym raporcie.

## Testy
- `ai/tests/test_token_ai.py` – jednostkowe sprawdzenie ruchu, wyboru celu i resupply na mockowanej planszy.
- `ai/tests/test_ai_basic.py` – smoke test uruchamiający pełną turę na uproszczonym silniku.

## Ograniczenia znane z kodu
- Brak pamięci taktycznej: żeton nie zapamiętuje poprzednich pozycji ani kontaktów.
- Tylko `SupplySpecialist` posiada dedykowane heurystyki; pozostałe typy korzystają z `GenericSpecialist`.
- Budżet PE wykorzystywany jest wyłącznie na paliwo i combat value; brak napraw, zakupów czy złożonych decyzji specjalistów.
- Jeśli `MoveAction`/`CombatAction` zwróci błąd, AI loguje zdarzenie i próbuje kolejnych kandydatów, ale nie planuje nowej strategii w tej turze.
- Współdzielona pamięć (`SharedIntelMemory`) przechowuje jedynie ostatnie wykrycia – brak analiz historycznych ani globalnych rozkazów.

Dokumentację utrzymujemy minimalną i zgodną z aktualną implementacją, aby stanowiła solidny punkt startowy dla ewentualnych rozbudów (np. przywrócenia specjalizacji w `specialized_ai.py`).