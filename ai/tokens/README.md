# Token AI – aktualny stan minimalny

System `ai/tokens` obsługuje **pojedynczą** klasę `TokenAI`. Specjalizacje i zaawansowane heurystyki, o których wspomina starsza dokumentacja, zostały uproszczone – wszystkie jednostki korzystają z identycznej logiki.

## Pliki
- `token_ai.py` – pełna implementacja zachowania żetonu.
- `specialized_ai.py` – stub fabryki (`create_token_ai`) zwracający zawsze `TokenAI`. Pozostawiony dla kompatybilności importów.
- `__init__.py` – eksport `TokenAI` i `create_token_ai`.

## Przebieg tury (`TokenAI.execute_turn`)
1. **Log startu** – zapisuje stan wejściowy (pozycja, zapas MP/fuel, budżet PE).
2. **Ruch** – jeśli żeton może się poruszać, próbuje kolejno kandydatów:
   - gdy widzi wrogów (na podstawie zasięgu `sight`), wybiera kierunek skracający dystans do najbliższego przeciwnika;
   - w przeciwnym razie patroluje najtańsze sąsiednie heksy (`move_mod` rosnąco).
   Ruch wykonywany jest przez `MoveAction`, a wynik interpretuje `engine.execute_action`.
3. **Atak** – sprawdza, czy w zasięgu (`attack.range`) znajduje się wróg. Jeśli tak, generuje `CombatAction` i analizuje zwrócone dane (`combat_result`, kontratak, zadane/otrzymane obrażenia).
4. **Resupply** – pozostały budżet PE wykorzystuje na uzupełnienie paliwa (`currentFuel → maxFuel`) i wartości bojowej (`combat_value → stats['combat_value']`).
5. **Log końcowy** – zapisuje wykorzystany budżet, powodzenie ruchu/ataku, zużycie paliwa oraz ewentualne zniszczenie żetonu.

## Pipeline autonomicznego żetonu (w pigułce)

1. **Odbierz kontekst** – Commander przekazuje `engine`, `player` i budżet PE; żeton odczytuje swoje aktualne MP, paliwo, CV oraz widocznych przeciwników.
2. **Sklasyfikuj status** – na podstawie paliwa, CV oraz zagrożeń wybiera tryb: `normal`, `low_fuel`, `threatened` lub `urgent_retreat`.
3. **Ułóż plan** – mapuje status na listę akcji (`refuel_minimum`, `restore_cv`, `maneuver`, `withdraw`, `attack`). Kolejność wyznacza priorytet.
4. **Wykonuj akcje** – każdą akcję realizuje po kolei, po każdej aktualizując kontekst (np. po ruchu aktualizuje pozycję i widoczne zagrożenia).
5. **Bilansuj zasoby** – niewykorzystane PE zamienia na paliwo/CV, a resztę odkłada jako `reserved_pe` do zwrotu dowódcy.
6. **Raportuj** – wysyła log końcowy z podsumowaniem ruchu, ataku, trybu ruchu i zużycia zasobów.

## Ważniejsze metody

| Metoda                         | Opis                                                                                   |
|--------------------------------|----------------------------------------------------------------------------------------|
| `_candidate_moves(engine)`     | Generuje listę heksów, do których warto spróbować się przemieścić (wróg → patrol).     |
| `_perform_movement(...)`       | Iteruje po kandydatach, woła `MoveAction` i loguje niepowodzenia.                      |
| `_select_attack_target(...)`   | Wyszukuje najbliższego wroga w zasięgu broni.                                          |
| `_perform_attack(...)`         | Odpala `CombatAction`, interpretuje wynik i przygotowuje raport do logów.              |
| `_perform_resupply(...)`       | Zużywa przydzielony budżet na paliwo i combat value (w tej kolejności).               |
| `_is_enemy(other)`             | Porównuje nacje na podstawie napisu właściciela (`"ID (Nacja)"`).                      |
| `_is_destroyed_after_attack`   | Weryfikuje, czy żeton przetrwał po walce (na podstawie logów i obecności na planszy). |

Cała logika operuje na istniejących strukturach silnika (`engine.board`, `engine.tokens`, `MoveAction`, `CombatAction`).

## Integracja z CommanderAI
`CommanderAI` przydziela każdemu żetonowi równy budżet PE i wywołuje `TokenAI.execute_turn(engine, player, share)`. Zwrócona wartość (`spent_pe`) służy do wyliczenia refundu i raportowania budżetu w logach dowódcy.

## Testy
- `ai/tests/test_token_ai.py` – jednostkowe sprawdzenie ruchu, wyboru celu i resupply na mockowanej planszy.
- `ai/tests/test_ai_basic.py` – smoke test uruchamiający pełną turę na uproszczonym silniku.

## Ograniczenia znane z kodu
- Brak pamięci taktycznej: żeton nie zapamiętuje poprzednich pozycji ani kontaktów.
- Brak specjalizacji – `specialized_ai.py` nie rozróżnia typów jednostek.
- Budżet PE wykorzystywany jest wyłącznie na paliwo i combat value; brak napraw, zakupów czy złożonych decyzji.
- Jeśli `MoveAction`/`CombatAction` zwróci błąd, AI tylko loguje zdarzenie – nie próbuje alternatywnych planów.

Dokumentację utrzymujemy minimalną i zgodną z aktualną implementacją, aby stanowiła solidny punkt startowy dla ewentualnych rozbudów (np. przywrócenia specjalizacji w `specialized_ai.py`).