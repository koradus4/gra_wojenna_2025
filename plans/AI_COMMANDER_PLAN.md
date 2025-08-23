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
8. retreat (hp<25%) – 95 (nadpisuje)
9. hold – 10

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
- Range / adjacency nadal spełnione
- Anti-loop: cache odwiedzonych heksów tej jednostki w turze

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
Wersja dokumentu: 1.2
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