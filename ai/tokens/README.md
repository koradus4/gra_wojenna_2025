# Token AI – logika autonomicznych żetonów

System `ai/tokens` odpowiada za zachowanie pojedynczego żetonu kontrolowanego przez AI. Wszystkie decyzje podejmowane są **wyłącznie w oparciu o istniejące mechaniki gry**, identyczne z tymi, z których korzysta gracz human.

## Struktura modułu
- `token_ai.py` – klasa bazowa `TokenAI` implementująca wspólną logikę percepcji, ruchu i ataku.
- `specialized_ai.py` – klasy dziedziczące (`SupplyTokenAI`, `CavalryTokenAI`, `ArtilleryTokenAI`, `InfantryTokenAI`) oraz fabryka `create_token_ai` zwracająca odpowiednią implementację na podstawie `stats['unitType']`.
- `__init__.py` – eksportuje klasy/funkcje dla reszty projektu.

## Klasa bazowa `TokenAI`
`TokenAI` przyjmuje instancję żetonu z silnika (posiadającą m.in. `id`, `owner`, `q`, `r`, `stats`, `currentMovePoints`, `currentFuel`). Kluczowe metody:

| Metoda | Cel | Zależności |
| --- | --- | --- |
| `get_owner_nation()` | Ekstrahuje nację z ciągu `"{player_id} ({nation})"`. | Pole `token.owner` (string generowany przez silnik). |
| `is_enemy(other)` | Sprawdza, czy inny żeton należy do innej nacji. | `get_owner_nation()`, `other.owner`. |
| `can_move()` | Weryfikuje dostępność ruchu według reguł human. | `currentMovePoints`, `currentFuel`. |
| `can_attack_target(target, engine)` | Upewnia się, że cel jest w zasięgu, nie jest sojusznikiem i że żeton może wykonać atak. | `engine.board.hex_distance`, `token.stats['attack']['range']`, `token.can_attack('normal')`. |
| `find_enemies_in_sight(engine)` | Przeszukuje `engine.tokens`, filtrując wrogów w zasięgu `stats['sight']`. | `engine.tokens`, `engine.board.hex_distance`. |
| `find_closest_enemy(engine)` | Szuka najbliższego wroga spośród widocznych. | `find_enemies_in_sight`. |
| `decide_move_target(engine)` | Domyślna heurystyka: idź w stronę najbliższego wroga, jeśli można się ruszyć. | `can_move`, `find_closest_enemy`. |
| `decide_attack_target(engine)` | Zwraca `id` pierwszego wroga, którego można legalnie zaatakować. | `find_enemies_in_sight`, `can_attack_target`. |
| `execute_turn(engine, player)` | Wykonuje pełną turę: (1) ruch przez `MoveAction`, (2) atak przez `CombatAction`. | `engine.execute_action`, klasy akcji z `engine.action_refactored_clean`. |

> **Ważne:** `TokenAI` nie implementuje żadnych nowych reguł. Wyłącznie odczytuje stan z żetonu i silnika, a następnie woła te same akcje (`MoveAction`, `CombatAction`) co gracz human.

### Przebieg tury (`execute_turn`)
1. Log startu tury (printy pomocnicze do debugowania).
2. Próba wyznaczenia celu ruchu (`decide_move_target`). Jeśli zwrócono współrzędne, tworzony jest `MoveAction`, który trafia do `engine.execute_action(action, player=...)`. Rezultat akcji interpretowany jest jak w kodzie human (`tuple` lub obiekt z polem `success`).
3. Po ewentualnym ruchu żeton wybiera cel ataku (`decide_attack_target`). Jeśli znaleziono wroga, wykonywany jest `CombatAction` przez silnik.
4. Log końca tury.

### Dane wykorzystywane z żetonu i silnika
- `token.stats`:
	- `attack.range` – maksymalny dystans ataku.
	- `sight` – zasięg widzenia wykorzystywany w detekcji wrogów.
	- `unitType` – identyfikator typu (Piechota, Kawaleria, Artyleria, Zaopatrzenie itd.).
- `token.currentMovePoints`, `token.currentFuel` – ograniczenia mobilności.
- `token.can_attack('normal')` – limit strzałów (np. dla artylerii).
- `engine.board.hex_distance((q1, r1), (q2, r2))` – liczy dystans heksowy.
- `engine.tokens` – wszystkie jednostki na mapie (AI+human) do oceny widoczności.
- `engine.key_points` – używane przez `SupplyTokenAI` do szukania punktów ekonomicznych.

## Specjalizacje w `specialized_ai.py`

### `SupplyTokenAI` (`unitType == "Z"`)
- Nadpisuje `decide_move_target`, aby znaleźć najbliższy key point (`engine.key_points`).
- Jeśli nie ma key pointów, wraca do logiki bazowej (podąża za wrogiem).
- `execute_turn` jedynie rozszerza log komunikatem o poszukiwaniu PE.

### `CavalryTokenAI` (`unitType == "K"`)
- Preferuje agresywny ruch w stronę najbliższego wroga.
- Jeśli wróg nie jest widoczny, przeszukuje otoczenie w zasięgu ruchu, wybierając najdalszy nieeksplorowany heks (heurystyka zwiadowcza).
- `_get_explored_positions` zbiera heksy zajęte przez wszystkie jednostki `engine.tokens` – prosty sposób na „mapę odwiedzonych pól”.

### `ArmoredTokenAI` (`unitType ∈ {"TC", "TŚ", "TL", "TS"}`)
- Definiuje mapę priorytetów celów (najpierw zaopatrzenie, potem artyleria, następnie dowództwo i reszta).
- `_select_focus_enemy` wybiera najcenniejszy cel, uwzględniając zarówno typ, jak i dystans (`engine.board.hex_distance`).
- Zarówno ruch, jak i atak próbują zbliżyć się do wybranego celu; jeśli cel jest w zasięgu, pancerna jednostka prowadzi ogień w pierwszej kolejności właśnie do niego.

### `ArtilleryTokenAI` (`unitType in ["AL", "AP"]`)
- Dąży do ustawienia się w optymalnej odległości:
	- jeśli cel jest za daleko – zbliża się;
	- jeśli za blisko (poniżej 2 pól) – stara się odsunąć, zachowując dystans do ostrzału.
- Korzysta z tego samego `attack.range` co silnik, nie modyfikuje limitów strzałów (`can_attack('normal')`).

### `InfantryTokenAI` (domyślne zachowanie)
- Nie nadpisuje logiki ruchu/ataku, wykorzystuje bazową implementację `TokenAI`.
- Używana również jako fallback dla nieznanych `unitType` – zapewnia, że każdy żeton ma działające AI.

### `CommandTokenAI` (`unitType ∈ {"D", "G"}`)
- Jednostki dowodzenia pełnią funkcję strategiczną poza mapą – AI utrzymuje pozycję i nie generuje akcji ruchu/ataku.
- Przygotowane jako bezpieczny handler dla żetonów dowódczych, gdyby pojawiły się na planszy (zapobiega niekontrolowanym ruchom).

## Fabryka `create_token_ai`
```python
def create_token_ai(token) -> TokenAI:
	unit_type = _get_unit_type(token)  # helper odczytujący stats['unitType'] lub atrybut tokenu
	if unit_type == 'Z':
		return SupplyTokenAI(token)
	if unit_type == 'K':
		return CavalryTokenAI(token)
	if unit_type in ['AL', 'AP', 'AC']:
		return ArtilleryTokenAI(token)
	if unit_type in ['TC', 'TŚ', 'TL', 'TS']:
		return ArmoredTokenAI(token)
	if unit_type in ['D', 'G']:
		return CommandTokenAI(token)
	return InfantryTokenAI(token)
```
- Dzięki temu `CommanderAI` może w prosty sposób otrzymać odpowiednie zachowanie dla każdego żetonu.
- Domyślna piechota (`InfantryTokenAI`) zabezpiecza system przed brakiem specjalizacji.

## Integracja z resztą AI
- `CommanderAI` (w folderze `ai/commander/`) wywołuje `create_token_ai(token)` dla każdego obsługiwanego żetonu, przydziela mu budżet (`ai_reserved_pe`) i uruchamia `execute_turn`.
- `TokenAI` może odczytać lub modyfikować przydział przez interfejs dowódcy (`CommanderAI.get_allowance` / `spend_allowance`) – domyślna implementacja wykorzystuje 1 PE w momencie aktywacji.
- `GeneralAI` wpływa pośrednio na zachowanie żetonów poprzez dostarczanie PE dowódcom; brak środków oznacza brak aktywacji żetonów.
- Logowanie decyzji odbywa się przez `ai.logs.log_token`, które zapisuje te same komunikaty równolegle w CSV i w logu tekstowym (`tokens/csv/…`, `tokens/text/…`).

## Testowanie logiki żetonów
- `ai/tests/test_token_ai.py` zawiera mocki `Engine` i `Board`, które:
	- udostępniają `execute_action`, `tokens`, `board.hex_distance` oraz `key_points`.
	- symulują scenariusze: tworzenie AI, wykrywanie wrogów, zachowanie zaopatrzenia oraz pełną turę.
- Testy pokazują, że wszystkie decyzje są podejmowane przy użyciu istniejących atrybutów żetonów i metod silnika.

- `log_token(..., level="DEBUG", **context)` pozwala wzbogacić wpis o dane kontekstowe, które trafią do kolumny `context` (JSON) w CSV i do logu tekstowego w formie `klucz=wartość`.

## Najważniejsze założenia
- **Żadnych nowych zasad:** AI korzysta dokładnie z tych samych ograniczeń (MP, paliwo, zasięg, limity ataku) co gracz ludzki.
- **Brak bezpośredniej manipulacji mapą:** wszystkie działania przechodzą przez `engine.execute_action`.
- **Budżet żetonu kontroluje dowódca:** jeśli `CommanderAI` nie przydzielił środków, żeton nie zostanie aktywowany.
- **Ostrożność przy mockowaniu:** aby testy działały, mock `engine` musi udostępniać te same pola/metody, których używa `TokenAI` (np. `board`, `tokens`, `key_points`).

Tak udokumentowana logika pozwala łatwo rozbudowywać specjalizacje żetonów, zachowując zgodność z istniejącą mechaniką gry.