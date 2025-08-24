# AI Commander – Plan Implementacji (Tactical Layer)

## 1. Cel
Zapewnić AI sterujące dowódcą (poziom taktyczny) działające w tych samych ramach co human:
- Legalny ruch (MP, paliwo, zajętość)
- Legalny atak (zasięg, wrogowie, brak cheat vision)
- Priorytety: przejęcie key points > atak opłacalny > koncentracja > defensywa
- Brak wieszania się przy braku opcji (fallback PASS)

## 2. Iteracje (roadmap)
| Iteracja | Zakres | Kryterium DONE |
|----------|--------|----------------|
| MVP-0 | Uzupełnienie braków silnika (movement, attack skeleton, vision, path) | Testy bazowe zielone |
| MVP-1 | Ruch do najbliższego key pointu / podejście do wroga | Jednostki faktycznie się przemieszczają |
| MVP-2 | Ataki z przewagą (ratio CV ≥ 1.3) | AI eliminuje słabe cele |
| MVP-3 | Priorytety złożone: capture vs attack vs reposition | Decyzje różnicują się sytuacyjnie |
| MVP-4 | Koncentracja / screen / odwrót < 25% HP | Jednostki cofają lub grupują się |
| MVP-5 | Log CSV + deterministyczne decyzje (seed) | Powtarzalność w scenariuszu testowym |
| MVP-6 | Rozszerzone heurystyki ryzyka (strefy wrogów) | Unika samobójczych wejść |
| MVP-7 | Synergia z Generałem (prośby o alokację / potrzeby) | Wymiana sygnałów ekonomicznych |

## 3. Kontrakt danych (wejście)
```
state = {
	'turn': int,
	'commander_id': int,
	'nation': str,
	'units': [ {id,q,r,cv,mp,fuel,max_mp,sight,range,role?,hp?} ],
	'enemies_visible': [ {id,q,r,cv,range} ],
	'key_points': [ {q,r,owner?,value,dist?} ],
	'map_meta': { 'cols': int, 'rows': int },
	'constraints': { 'fog': bool }
}
```
Źródło: engine.tokens + board + key_points_state (gdy wypełnione).

## 4. Pipeline tury
1. gather_state()
2. classify_units() – role: SPEARHEAD / INFANTRY / SUPPORT / SCREEN / RESERVE
3. detect_threats() – wrogowie w zasięgu ataku / potencjalnego kontrataku
4. determine_mode() – ASSAULT / ADVANCE / CONSOLIDATE / HOLD / RETREAT
5. generate_objectives() – lista TacticalObjective
6. score_objectives_per_unit()
7. build_action_plan() – sekwencja (move/attack)
8. execute_actions() – walidacja tuż przed wykonaniem; illegal → skip & log
9. finalize_turn() – log + cleanup tymczasowej widoczności

## 5. Typy TacticalObjective
| Typ | Opis | Generowanie |
|-----|------|-------------|
| capture | Wejście na neutralny / wrogi key point | key_points in range path ≤ N |
| attack | Atak na wroga z przewagą | enemy_visible + ratio ≥ threshold |
| approach | Zbliżenie do priorytetowego celu (KP / klaster) | brak bezpośr. dojścia |
| approach_partial | **NOWY** Częściowy ruch w kierunku celu poza zasięgiem MP | gdy pełny approach niemożliwy |
| reposition | Lepszy defense_mod / koncentracja | gdy brak innych |
| retreat | Wycofanie poniżej HP / paliwa | hp/fuel threshold |
| hold | Brak lepszych opcji | fallback |
| scout | Eksploracja nieznanych sektorów | brak KP/wrogów w early fazie |

Struktura:
```
TacticalObjective(
	type: str,
	target_hex: (q,r),
	priority: int,
	reason: str,
	aux: dict (np. target_enemy_id, expected_ratio)
)
```

## 6. Priorytety (bazowe)
1. capture (≤ 3 ruchy) – 90
2. attack (ratio ≥ 1.6 lub enemy on KP) – 80
3. capture (dalsze) – 70
4. attack (1.3 ≤ ratio < 1.6) – 60
5. approach (skraca dystans do KP ≤ 2) – 50
6. scout (early faza) – 45 (po odkryciu KP → 15)
7. reposition (koncentracja / osłona) – 40
8. **approach_partial** (ruch w kierunku celu poza zasięgiem) – **35**
9. retreat (hp<25%) – 95 (nadpisuje)
10. hold – 10

## 7. Scoring ruchu
```
MOVE_SCORE = 
	base_priority(objective)
	- path_len * 1.0
	+ defense_mod * 0.3
	+ ally_adjacent_count * 0.5
	- enemy_threat_count * threat_weight
	+ (on_key_point ? +5 : 0)
```

## 8. Scoring ataku
```
ATTACK_SCORE =
	(our_cv / enemy_cv) * 10
	+ (enemy_on_key_point ? 8 : 0)
	+ (enemy_is_support ? 4 : 0)
	- (expected_retaliation_cv * 0.4)
```
Odrzucenie jeżeli (our_cv / enemy_cv) < 1.15 (chyba że enemy_hp krytyczne).

## 9. Filtry legalności
- Token istnieje i MP > 0
- Fuel > 0
- Ścieżka wolna / aktualna
- **KRYTYCZNE: Rzeczywiste sprawdzenie pathfindingu z limitami MP/Fuel**
- **NOWE: Jeśli cel poza zasięgiem MP, generuj approach_partial**
- **NOWE: Cache sprawdzonych ścieżek na turę (optymalizacja)**
- Range / adjacency nadal spełnione
- Anti-loop: cache odwiedzonych heksów tej jednostki w turze

### 9.1 **POPRAWKA PATHFINDING BUG**
**Problem:** AI Commander używa `board.find_path(start, target)` bez limitów MP, ale MoveAction używa `find_path(start, target, max_mp=X)` z limitami.

**Rozwiązanie:**
```python
# ZAWSZE używaj limitowanego pathfindingu w AI Commander:
path = board.find_path(
    unit_pos, target,
    max_mp=unit.get('currentMovePoints', 0),
    max_fuel=unit.get('currentFuel', 99)
)

# Jeśli path == None, sprawdź czy możliwy partial move:
if not path:
    unlimited_path = board.find_path(unit_pos, target)
    if unlimited_path and len(unlimited_path) > 1:
        max_steps = min(unit.get('currentMovePoints', 0), len(unlimited_path) - 1)
        if max_steps > 0:
            # Generuj approach_partial objective
            partial_target = unlimited_path[max_steps]
            return create_partial_objective(partial_target)
```

## 9.2 **PRIORYTETOWE POPRAWKI (CRITICAL)**

### **A. Natychmiastowe (Blokery ruchu jednostek)**
1. **Fix _score_move_objective()** - używaj rzeczywistego pathfindingu z MP limits
2. **Fix _generate_capture_objectives()** - filtruj cele nieosiągalne w jednej turze  
3. **Dodaj partial movement logic** - gdy cel za daleko, idź ile możesz

### **B. Ważne (Stabilność AI)**
4. **Fix objective filtering** - eliminuj cele poza zasięgiem WSZYSTKICH jednostek
5. **Dodaj approach_partial generation** - automatycznie dla celów 4+ hexów dalej
6. **Cache pathfinding results** - unikaj wielokrotnych wywołań tej samej ścieżki

### **C. Długoterminowe (Jakość decyzji)**
7. **Multi-turn planning** - preferuj cele osiągalne w 2-3 turach
8. **Dynamic replanning** - gdy partial move ukończony, przegeneruj objectives
9. **Formation awareness** - grupuj jednostki w marszach

### **D. Kod do natychmiastowego wdrożenia:**
```python
# ai/ai_commander.py - line ~346
def _score_move_objective(self, board, unit, objective):
    """FIX: Oceń cel z rzeczywistymi limitami MP/Fuel"""
    target = objective['target_hex']
    unit_pos = (unit['q'], unit['r'])
    
    # KRYTYCZNA POPRAWKA: Sprawdź rzeczywistą dostępność
    path = board.find_path(
        unit_pos, target,
        max_mp=unit.get('currentMovePoints', 0),
        max_fuel=unit.get('currentFuel', 99)
    )
    
    if not path:
        # Sprawdź czy możliwy partial move
        unlimited = board.find_path(unit_pos, target)
        if unlimited and len(unlimited) > 1:
            max_steps = min(unit.get('currentMovePoints', 0), len(unlimited) - 1)
            if max_steps > 0:
                # Partial move możliwy - niższy score ale wykonalny
                return objective['priority'] - max_steps * 2 + 10
        return -1000  # Całkowicie niemożliwe
    
    # Pełna ścieżka możliwa
    distance = len(path) - 1
    return objective['priority'] - distance * 1.5

# DODAJ NOWĄ METODĘ:
def _generate_approach_partial_objectives(self, state, board):
    """Generuj partial movement objectives dla celów poza zasięgiem"""
    objectives = []
    
    for kp in state['key_points']:
        if kp.get('owner') != self.player.nation:
            # Sprawdź czy KP jest poza zasięgiem ale partial ruch możliwy
            for unit in state['units']:
                unit_pos = (unit['q'], unit['r'])
                target_pos = (kp['q'], kp['r'])
                
                # Sprawdź czy pełna ścieżka niemożliwa
                full_path = board.find_path(
                    unit_pos, target_pos,
                    max_mp=unit.get('currentMovePoints', 0)
                )
                
                if not full_path:
                    # Sprawdź czy partial możlivy
                    unlimited = board.find_path(unit_pos, target_pos)
                    if unlimited and len(unlimited) > unit.get('currentMovePoints', 0):
                        # Cel za daleko ale można iść częściowo
                        max_steps = unit.get('currentMovePoints', 0)
                        if max_steps > 0:
                            partial_target = unlimited[max_steps]
                            objectives.append({
                                'type': 'approach_partial',
                                'target_hex': partial_target,
                                'priority': 35,
                                'reason': f"Partial approach to KP {kp['q']},{kp['r']}"
                            })
                            break  # Jeden objective per KP
    
    return objectives
```

## 10. Struktury i klasy
```
class AICommander:
		make_tactical_turn()
		_gather_state()
		_classify_units()
		_determine_mode()
		_generate_objectives()
		_score_objectives()
		_assign_objectives()
		_plan_actions()
		_execute_actions()
		_log_turn()
```
Dodatki: UnitContext, ThreatEntry, ActionSpec.

## 11. Logowanie
CSV / tekst:
- turn, commander_id, unit_id, action_type, from_hex, to_hex, enemy_id?, score, reason
- summary: objectives_generated, actions_executed, captures, attacks_successful
Tryby: OFF / NORMAL / DEBUG.

## 12. Testy (po fundamentach)
| Test | Cel |
|------|-----|
| test_state_adapter_min | Struktura state kompletna |
| test_objective_capture | Capture > attack przy wolnym KP |
| test_attack_filter_ratio | Odrzucony atak przy ratio < 1.15 |
| test_move_path_selection | Krótsza ścieżka wybrana |
| test_retreat_trigger | hp < 25% → retreat |
| test_no_stall_when_no_actions | Brak crashu gdy brak akcji |
| test_determinism_seed | Stabilny wynik przy seed |
| test_scout_generates_when_no_objectives | Scout pojawia się gdy brak innych |
| test_scout_suppressed_when_capture_available | Scout znika przy pojawieniu capture |
| test_scout_deterministic_seed | Powtarzalność sektorów |
| **test_partial_movement_generation** | **approach_partial generuje się dla celów poza zasięgiem** |
| **test_partial_movement_execution** | **Jednostka porusza się częściowo w kierunku celu** |
| **test_pathfinding_mp_limits** | **AI używa pathfindingu z limitami MP/Fuel** |
| **test_objective_filtering_reachable** | **Cele nieosiągalne są odfiltrowane** |
| **test_partial_vs_full_priority** | **Pełny approach > approach_partial** |

## 13. Ryzyka / zależności
- Braki implementacyjne w board / engine / action (blokery)
- Uszkodzone wpisy w start_tokens.json
- Brak key_points → brak testu capture
- Brak realnych strat w walce (na początek abstrakcja)

## 14. Minimalne poprawki silnika przed MVP-1
1. Token: get_movement_points(), apply_movement_mode(reset), aktualizacja MP
2. Board: neighbors(), is_occupied(), find_path(A*)
3. Engine: execute_action(Move/Combat), update_player_visibility()
4. CombatAction: prosta eliminacja (los / ratio) + removal defender
5. TurnManager: reset MP wszystkich żetonów
6. Dodanie kilku key_points + capture assignment

## 15. Sygnalizacja do Generała (future)
NEED_SUPPLY, NEED_ARMOR, PRESSURE_FRONT → modulacja alokacji.

## 16. Backlog po MVP-3
- Strefy zagrożeń (heatmap)
- Alternatywne ścieżki (A/B)
- Chain move+attack
- Rezerwacja heksów w planowaniu
- Morale / cohesion (mnożniki)

## 17. Tryby trudności
| Parametr | Easy | Medium | Hard |
|----------|------|--------|------|
| Min attack ratio | 1.4 | 1.3 | 1.2 |
| Retreat hp% | 20 | 25 | 30 |
| Risk weight | 1.0 | 0.8 | 0.6 |
| Cluster importance | 0.5 | 0.8 | 1.1 |

## 18. Determinizm
- Lokalny RNG: seed_base + turn + commander_id
- Zero niekontrolowanych losowań
- Seed zapisany w logu

## 19. Fallbacki
- Brak path → najbliższy osiągalny (fallback_to_closest)
- Brak enemy/KP → HOLD + log NO_OBJECTIVES
- Illegal w momencie wykonania → skip + re-score reszty

## 20. Pseudokod rdzenia
```
def make_tactical_turn():
		S = gather_state()
		objectives = generate_objectives(S)
		scored = score_objectives(S, objectives)
		plan = build_plan(S, scored)
		for act in plan:
				if validate(act):
						exec(act)
		log_summary()
```

## 21. Eksploracja (wczesna faza)
Cel: sensowne ruchy zanim odkryte zostaną key points lub wrogowie (imitacja ludzkiego rozpoznania).

Warunek aktywacji:
- Brak widocznych wrogów AND brak niekontrolowanych key_points przez pierwsze X tur (domyślnie X=3) LUB do momentu wykrycia pierwszego KP.

Generowanie sektorów:
- Koncentryczne pierścienie wokół środka masy startowych jednostek: promienie 2,4,6...
- Każdy sektor = zbiór heksów; fog_density = (#nieodkryte / #w sektorze).

TacticalObjective 'scout':
- priority 45 (po odkryciu pierwszego KP spada do 15)
- reason: SCOUT_R<radius>_S<index>
- aux: { 'sector_id': int, 'fog_density': float }

Tie-break: deterministyczny RNG (seed = base_seed + turn + commander_id + sector_id).

Zakończenie:
- sector_completion ≥ 0.8 OR pojawił się wyższy priorytet OR brak nieodkrytych heksów.

Cache:
- cache_explored_hexes: set[(q,r)] po każdym ruchu
- sector_progress[sector_id] = visited / total

---
## 22. Uzupełnianie paliwa i combat value (resupply)
Cel: AI używa identycznych zasad co gracz (brak cheatów) – każde +1 fuel lub +1 combat kosztuje 1 punkt ekonomiczny, nie przekracza maksów, odejmuje z puli `punkty_ekonomiczne`.

Moment wykonania:
1. Faza pre‑tactical (przed generowaniem objectives) – aby stan zasobów wpływał na plan ruchu / ataku.
2. (Opcjonalnie future) Mikro‑resupply po dużych stratach jeśli pozostaje budżet rezerwowy.

Dane wejściowe:
- Lista własnych żetonów z: currentFuel, maxFuel, combat_value (current), max_combat(stats.combat_value), rola (SPEARHEAD/ARTYLERIA/INFANTRY/SCREEN), planowana odległość ruchu (estymowana), czy broni key pointu.
- Budżet ekonomiczny: `punkty_ekonomiczne`.

Heurystyka priorytetyzacji (kolejność):
1. Krytyczne paliwo: fuel_pct < 0.3 AND rola in {SPEARHEAD, ARTYLERIA}.
2. Krytyczny combat: combat_pct < 0.5 AND rola ≠ SCREEN.
3. Obrona key point: unit_on_key_point AND combat_pct < 0.7.
4. Planowany atak w tej turze (wytypowany potencjalny objective attack) i fuel_pct < 0.5.
5. Jednostki z fuel_pct < 0.5 ogólnie.
6. Pozostałe (skip jeśli budżet niski).

Budżetowanie:
- Całkowity budżet = P.
- Rezerwa strategiczna R = ceil(P * 0.2) (nie naruszamy w zwykłym resupply; wyjątek: krytyczne punkty obrony fuel_pct/combat_pct < 0.2 – wtedy można wejść w rezerwę).
- Budżet operacyjny O = P - R.
- Minimalny jednostkowy próg opłacalności: jeżeli fuel_pct > 0.85 i combat_pct > 0.9 → pomijaj.

Algorytm (pseudokod):
```
def ai_resupply(player):
	P = player.punkty_ekonomiczne
	if P <= 0: return
	R = ceil(P * 0.2)
	O = P - R
	candidates = rank_units(units)
	for u in candidates:
		if player.punkty_ekonomiczne <= 0: break
		max_missing_fuel = u.maxFuel - u.currentFuel
		max_missing_combat = u.max_combat - u.combat_value
		if max_missing_fuel <=0 and max_missing_combat <=0: continue
		# Dynamiczna preferencja: w krytyce najpierw fuel jeśli fuel_pct<0.3 else combat jeśli combat_pct<0.5
		allot_fuel, allot_combat = plan_split(u, player.punkty_ekonomiczne, O, R)
		spent = allot_fuel + allot_combat
		if spent == 0: continue
		u.currentFuel += allot_fuel; u.combat_value += allot_combat
		clamp()
		player.punkty_ekonomiczne -= spent
		log_resupply(u, allot_fuel, allot_combat)
```

plan_split(u,...):
- Jeśli fuel_pct < 0.3 → priorytet fuel: przyznaj min(max_missing_fuel, budżet_dostępny_do_wydania_na_tę_jednostkę).
- Następnie combat do progu 0.6 jeśli wystarczy budżetu.
- W normalnym trybie: dążyć do wyrównania (fuel_pct i combat_pct do min(0.7, max z obu)).

Ochrona budżetu:
- Jeżeli (player.punkty_ekonomiczne - spent) < R i jednostka nie spełnia kryterium "krytyczne" → przerwij pętlę.

Anty‑overfill:
- clamp po każdej aktualizacji.

Deterministyczny tie‑break:
- sortowanie: (priorytet_kategorii DESC, min(fuel_pct, combat_pct) ASC, id ASC)

Logowanie (rozszerzenie CSV):
- action_type: resupply_ai
- fields: unit_id, fuel_added, combat_added, fuel_after, combat_after, reason_category, remaining_points

Testy:
- test_resupply_limits_respected
- test_resupply_skips_full_units
- test_resupply_reserve_protected
- test_resupply_prioritization_order

Rozszerzenia future:
- Dynamiczna zmiana R gdy brak kontaktu bojowego (można zmniejszyć rezerwę do 10%).
- Integracja z sygnałami Generała (np. PRIORITY_FRONT_X zwiększa wagę jednostek z tego frontu).

Założenia kosztowe (jeśli później pojawi się różnicowanie): dodamy mapę kosztów per typ zasobu; obecnie 1:1.

## Aktualizacja priorytetów globalnych (inkluzja resupply)
Resupply nie jest TacticalObjective – dzieje się przed ich generacją; jednak jeśli paliwo < próg krytyczny a brak środków → oznacz jednostkę tagiem LIMITED_OPS wpływającym na scoring movement/attack (-15 do oceny).

---
Wersja dokumentu: 1.6 (zaktualizowane; wcześniejsze wpisy wersji w sekcjach 23–26 pozostawione jako changelog)
Data: 2025-08-23
Autor: System planowania AI
\n+## 23. Replan przy kontakcie (kontakt z wrogiem w trakcie ruchu)
Fakt w kodzie: `PathfindingService.calculate_path_cost_and_position` przerywa ruch gdy `_enemy_in_sight` zwraca True (zatrzymanie na heksie kontaktu). To zapewnia naturalny "stop na kontakt" jak u człowieka.

Zasady ujęte w planie (bez cheatów):
- Jeśli podczas wykonywania ruchu pojawi się nowy przeciwnik w zasięgu wzroku: kończymy ruch na bieżącym polu (już działa w kodzie).
- Po zakończeniu ruchu (w tej samej turze) AI oznacza jednostkę statusem CONTACT i w następnej fazie decyzji (kolejna jednostka lub kolejna pętla) ponownie ocenia: atak / reposition / hold / retreat.
- Brak przewidzenia niewidocznych wcześniej wrogów (FOW respektowany – widzenie liczone via `VisionService.calculate_visible_hexes`).
- Dodatkowe triggery replanu (planowane): zablokowana ścieżka (brak środków), nagły spadek paliwa, utrata celu (cel został zajęty).

Testy do dodania:
- test_contact_stops_movement (symulacja ścieżki gdzie w połowie pojawia się wróg)
- test_contact_sets_replan_flag (CONTACT → nowe objective w kolejnej ocenie)

Implementacja flag:
- token.temp_flags.add('CONTACT') przy zatrzymaniu; czyszczone na koniec tury.

---
Wersja dokumentu: 1.3 (patrz sekcja 24 dla 1.4)
Data: 2025-08-23
Autor: System planowania AI

## 24. Integracja z `main_ai.py` (AI Dowódca) – Wersja 1.4
Cel: Uruchomienie logiki AI Dowódcy w normalnej pętli gry obok AI Generała bez modyfikowania zasad gry.

Zakres minimalny (MVP-1 kompatybilny):
1. Definicja klasy `AICommander` (zgodnie ze strukturą sekcji 10) w module `ai/ai_commander.py` (jeśli nie istnieje) – na start stub z metodą `make_tactical_turn()` wypisującą log „NO_OP”.
2. Dodanie w `main_ai.py` słownika `ai_commanders = {player.id: AICommander(player) ...}` dla graczy z rolą "Dowódca" oznaczonych jako AI.
3. UI: analogicznie do checkboxów generałów – (future) można dodać checkboxy dla dowódców; w pierwszym kroku można konfigurować przez stałą / flagę.
4. Pętla tury (fragment w `main_game_loop`):
   - Jeśli `current_player.role == "Dowódca"` i `current_player.is_ai_commander`:
	 a. (Opcjonalnie) `ai_commander.pre_resupply(game_engine)` – implementuje algorytm z sekcji 22 (jeśli budżet > 0).
	 b. `ai_commander.make_tactical_turn(game_engine)` – generuje i wykonuje plan.
	 c. `turn_manager.next_turn()`.
5. Czyszczenie flag tymczasowych (CONTACT, LIMITED_OPS) – na końcu pełnej tury tak jak czyszczona jest tymczasowa widoczność.
6. Logowanie: dopisać typ akcji `commander_ai_action` do CSV wspólnego (można użyć istniejącego mechanizmu logów akcji) – minimalnie: turn, commander_id, unit_id, action_type, from, to, reason.

Flagi / atrybuty w obiekcie Player:
- `player.is_ai_commander = True` (analogicznie jak `is_ai` dla generała, aby nie mieszać ról).
- Referencja do instancji: przechowywana w `turn_manager.ai_commanders[player.id]` lub bezpośrednio w słowniku lokalnym pętli.

Kolejność faz dla AI Dowódcy (po integracji):
1. Reset MP/fuel (mechanika tury silnika).
2. Pre‑resupply (sekcja 22) – aktualizacja `punkty_ekonomiczne` po stronie dowódcy (jeżeli system ekonomii przydziela mu punkty).
3. Tactical pipeline (sekcje 4–11, 21–23).
4. Log + cleanup jednostkowy.

Minimalny stub `AICommander` (pseudokod):
```
class AICommander:
	def __init__(self, player):
		self.player = player

	def pre_resupply(self, game_engine):
		pass  # implementacja wg sekcji 22 (później)

	def make_tactical_turn(self, game_engine):
		# Tymczasowo brak realizacji – placeholder
		print(f"[AICommander] NO_OP turn for commander {self.player.id}")
```

Testy integracyjne (nowe):
- `test_ai_commander_stub_runs_no_errors` – wywołanie pętli tury z jednym AI Dowódcą nie rzuca wyjątków.
- `test_ai_commander_resupply_applies_points` – po zaimplementowaniu resupply paliwo rośnie, punkty maleją.

Aktualizacja wersji: 1.4 (dodano sekcję integracji, bez zmian w poprzednich sekcjach).

Wersja dokumentu: 1.4
Data: 2025-08-23
Autor: System planowania AI

## 25. Zależność ekonomiczna (obsada key points) – Wersja 1.5
Fakt systemowy: tylko Generał otrzymuje punkty ekonomiczne z key points (sekcja `GameEngine.process_key_points`). Dowódca NIE dostaje bezpośrednio tych punktów, ale musi utrzymywać żetony na heksach, aby strumień punktów dla Generała (i pośrednio budżety przyszłe) płynął.

Implikacje dla AI Dowódcy:
1. TacticalObjective `capture` i późniejsze `hold` na KP mają wartość ekonomiczną mimo braku natychmiastowego VP.
2. Garrison heuristic: jeśli KP nadal ma `current_value` > 0 i brak nadciągającego zagrożenia, utrzymaj 1 jednostkę (najtańszą stabilną) – inne mogą manewrować.
3. Jeśli brak jednostek rezerwowych → priorytet pozostawienia tej, która już stoi (koszt ruchu = 0) zamiast rotacji.
4. Rezygnacja z obsady tylko gdy: (a) KP wyczerpane (`current_value <= 0`), (b) krytyczna potrzeba taktyczna (RETREAT / zagrożenie eliminacją), (c) wymiana na jednostkę o wyższym defense_mod.
5. Scoring modyfikacja: heks na aktywnym KP +5 (już uwzględnione w sekcji 7) → utrzymujemy; jeśli KP prawie wyczerpane (`current_value / initial_value < 0.1`) bonus redukuj do +1.

Rozszerzenie danych (opcjonalne): dodać do stanu w `_gather_state()` pole `key_points[i]['remaining_ratio'] = current/initial` jeśli dostępne.

Testy (future):
- test_hold_preserves_garrison_when_value_remaining
- test_release_garrison_when_value_depleted

Aktualizacja wersji: 1.5 (dodano sekcję zależności ekonomicznej – brak zmian logiki wcześniejszych sekcji).

Wersja dokumentu: 1.5
Data: 2025-08-23
Autor: System planowania AI

## 26. Zadania integracyjne przed implementacją logiki (Wersja 1.6)
Cel: Minimalny kod umożliwiający uruchomienie pętli AI Dowódcy zanim powstanie pełna logika objectives.

Do wykonania (małe, niskie ryzyko):
1. `main_ai.py`: utworzyć słownik `ai_commanders = {}` analogicznie do `ai_generals` i przy tworzeniu graczy oznaczonych jako AI Dowódca dodawać `AICommander(player)`.
2. Pętla tury: jeśli `current_player.role == "Dowódca"` i `current_player.is_ai_commander`: wywołać `ai_commander.pre_resupply(game_engine)` -> `ai_commander.make_tactical_turn(game_engine)` -> `turn_manager.next_turn()`.
3. `Player`: jeśli brak, dodać atrybut runtime `is_ai_commander = False` (bez modyfikacji konstruk tora – można ustawić dynamicznie po stworzeniu instancji).
4. Log: na razie wystarczy print (CSV dopiero przy MVP-5).
5. Pathfinding: używamy istniejącej implementacji (brak zmian). Jeżeli w przyszłości brak funkcji dostępu – dodać adapter `engine.board.find_path` (A*), ale NIE blokuje startu NO_OP.
6. Test szybki (manualny): uruchomić grę z jednym AI Dowódcą – oczekiwany output w konsoli: `[AICommander] NO_OP for commander X` i normalny postęp tur.

Kryterium akceptacji planu do wdrożenia:
- Sekcje 23–26 odzwierciedlają potrzebną integrację i brak otwartych pytań o podstawy.

Po akceptacji: wykonujemy sekcję 26, potem przechodzimy do MVP-1 (ruch do KP).

---

## 27. **AKTUALIZACJA PLANU - ANALIZA OBECNYCH PROBLEMÓW (v1.7)**

### **27.1 Zidentyfikowane problemy w implementacji**

**A. GŁÓWNY PROBLEM: Pathfinding Discrepancy**
- AI Commander używa `board.find_path(start, target)` bez limitów MP
- MoveAction używa `find_path(start, target, max_mp=X)` z limitami  
- **Skutek:** AI wybiera cele 10+ hexów dalej gdy jednostki mają 6 MP
- **Status:** BLOKUJE wszystkie ruchy jednostek

**B. Brak filtrowania celów po rzeczywistym zasięgu**
- Plan przewiduje "key_points in range path ≤ N" ale nie implementuje sprawdzania MP
- Wszystkie cele są akceptowane niezależnie od możliwości dotarcia
- **Status:** Powoduje frustrujące zachowanie AI

**C. Brak partial movement logic**
- Gdy cel za daleko, AI rezygnuje kompletnie
- Brak mechanizmu "idź ile możesz w kierunku celu"
- **Status:** Ogranicza użyteczność AI na dużych mapach

### **27.2 Priorytetowe poprawki**

**KRYTYCZNE (natychmiastowe):**
1. **Fix _score_move_objective()** - zawsze używaj pathfindingu z limitami MP/Fuel
2. **Fix _generate_capture_objectives()** - filtruj tylko osiągalne cele
3. **Dodaj approach_partial** - dla celów częściowo osiągalnych

**WAŻNE (stabilność):**
4. **Cache pathfinding** - unikaj wielokrotnych wywołań
5. **Better objective filtering** - eliminate impossible targets early
6. **Fallback improvements** - lepsze zachowanie gdy brak osiągalnych celów

### **27.3 STAN RZECZYWISTY - ANALIZA KODU (24.08.2025)**

**✅ CO JEST ZAIMPLEMENTOWANE:**
- ✅ Podstawowy ruch jednostek (find_target, move_towards)
- ✅ Strategiczne rozkazy z JSON (receive_orders, load_strategic_orders)
- ✅ Pathfinding z ograniczeniami MP/Fuel
- ✅ Logowanie akcji do CSV w logs/ai_commander/
- ✅ Autonomiczny fallback gdy brak rozkazów strategicznych

**❌ KRYTYCZNE LUKI W IMPLEMENTACJI:**
- ❌ **RESUPPLY/REGENERACJA** - brak implementacji sekcji 22
  - `pre_resupply()` to tylko placeholder: `pass`
  - AI Commander nie uzupełnia fuel ani combat_value
  - Dowódcy nie mają dostępu do punktów ekonomicznych na resupply
- ❌ **WALKA/COMBAT** - brak CombatAction
  - Brak analizy wrogów w zasięgu
  - Brak attack objectives  
  - Brak oceny stosunku sił (combat ratio)
- ❌ **ZAAWANSOWANE CELE** - tylko podstawowy ruch
  - Brak capture key points
  - Brak retreat objectives
  - Brak reposition/formation tactics

**PRZYSZŁY PLAN ROZWOJU:**

**FAZA A: RESUPPLY SYSTEM (KRYTYCZNY)**
1. Implementacja pre_resupply() zgodnie z sekcją 22
2. Budżetowanie: rezerwa 20% + operacyjny 80%
3. Priorytetyzacja: paliwo < 30% → combat < 50% → key points
4. Integracja z player.punkty_ekonomiczne

**FAZA B: COMBAT SYSTEM**  
5. CombatAction implementation
6. Analiza wrogów w zasięgu ataku
7. Combat ratio evaluation (min 1.3 dla ataku)

**FAZA C: TACTICAL OBJECTIVES**
8. Key Points capture/hold objectives
9. Retreat dla jednostek < 25% HP
10. Formation awareness

### **27.4 Zaktualizowane wymagania dla MVP-1**

**PODSTAWOWE (OBECNY STAN):**
- ✅ Jednostki faktycznie się przemieszczają
- ✅ Wszystkie ruchy są legalne (w ramach MP/Fuel)  
- ✅ Brak prób niemożliwych ruchów
- ✅ Partial movement działa gdy cel za daleko

**ROZSZERZONE MVP-1 (DO IMPLEMENTACJI):**
- ❌ **AI Commander ma resupply** - uzupełnia fuel/combat za punkty ekonomiczne
- ❌ **AI Commander atakuje** - podstawowe CombatAction gdy ratio korzystny
- ❌ **AI Commander przejmuje key points** - capture objectives

**Dodatkowe testy krytyczne:**
- `test_pathfinding_mp_consistency` - AI i MoveAction używają tego samego pathfindingu
- `test_no_impossible_moves` - AI nie generuje ruchów poza zasięgiem MP
- `test_partial_progress` - jednostki robią postęp w kierunku dalekich celów
- `test_mp_exhaustion_handling` - zachowanie gdy MP = 0

---

**Wersja dokumentu: 1.7**  
**Data aktualizacji: 2025-08-24**  
**Zmiany:** Dodano analizę problemów implementacji, zaktualizowano wymagania MVP-1, rozszerzono testy o partial movement

```

Aktualizacja wersji: 1.6 (dodano sekcję 26, brak zmian wcześniejszych sekcji).

Wersja dokumentu: 1.6
Data: 2025-08-23
Autor: System planowania AI