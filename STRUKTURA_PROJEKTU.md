# STRUKTURA PROJEKTU KAMPANIA 1939

## 📌 STAN BIEŻĄCY (3 września 2025) – WERSJA 3.8 – PE VALIDATION SYSTEM ZAKOŃCZONY

**SYSTEM PE VALIDATION - KOMPLETNE ROZWIĄZANIE (3.09.2025):**

**Problem:** AI Generałowie i Dowódcy mogli wydawać ujemne PE, powodując destabilizację ekonomiczną gry.

**Rozwiązanie PE VALIDATION:**
- **Multi-layer protection** w `ai/zaopatrzenie_ai.py` i `core/ekonomia.py`
- **Blokada ujemnych PE** - system nie pozwala wydać więcej niż dostępne
- **Poprawne transfery PE** - Generał → Dowódcy z walidacją
- **Bilanse ekonomiczne** - wszystkie operacje PE weryfikowane
- **Comprehensive logging** - pełne śledzenie przepływu PE w CSV

**Nowe systemy bezpieczeństwa:**
- `validate_pe_spending()` - walidacja przed każdym wydatkiem
- `transfer_pe_to_commanders()` - bezpieczne transfery z logowaniem
- `check_pe_balance()` - weryfikacja bilansów po operacjach
- `block_negative_pe()` - hard stop dla ujemnych wartości
- Real-time PE tracking w logach AI

**Wyniki weryfikacji (AI vs AI test):**
- **Ujemne PE**: WYELIMINOWANE ✅
- **Transfery PE**: DZIAŁAJĄ POPRAWNIE ✅  
- **Bilanse**: ZGADZAJĄ SIĘ 100% ✅
- **Stabilność ekonomiczna**: ZAPEWNIONA ✅

**Pliki:** `auto_game_10_turns.py`, `tools/launcher_analizy_pe.py`, `tools/analizator_przeplywu_pe.py`

Aktualizacja koncentruje się na: **stabilizacji ekonomicznej systemu AI** oraz **eliminacji krytycznych bugów PE**.

NOWE (3.6):
* `casualties_turn` – liczba utraconych własnych jednostek w danej turze (turn summary)
* `new_units_turn` – liczba nowo pojawionych jednostek (spawn / zakup) w turze (turn summary)
* `skip_reason` – kolumna dodana do logu akcji (action log) – NA RAZIE pusty placeholder (diagnoza stagnacji w kolejnym kroku)

Cel: przygotowanie sygnałów do przyszłego Emergency Mode oraz analizy tempa odbudowy sił – bez modyfikacji heurystyk ruchu/zakupów.

## 🎯 SYSTEM OGRANICZENIA STRZAŁÓW ARTYLERII (POZIOM 1 - ZAIMPLEMENTOWANY 31.08.2025):

**Problem:** Artyleria była zdominowaną bronią - wysoki zasięg (3-4 hex), duży atak (12-18), mogła atakować wielokrotnie bez ograniczeń, powodując dominację "arty spam".

**Rozwiązanie:** System **1 normalny atak + 1 atak reakcyjny na turę** dla wszystkich jednostek artylerii.

**Implementacja:**
- **Token.shots_fired_this_turn** - licznik normalnych ataków w turze
- **Token.reaction_shot_used** - flaga użycia ataku reakcyjnego
- **Token.can_attack(attack_type)** - walidacja możliwości ataku
- **Token.record_attack(attack_type)** - rejestracja wykonanego ataku
- **Token.is_artillery()** - identyfikacja artylerii (AL, AC, AP)
- **Token.reset_turn_actions()** - reset na początku nowej tury

**Integracja z silnikiem:**
- **CombatAction._validate_combat()** - automatyczna walidacja przed atakiem
- **core/tura.py** i **engine/engine.py** - auto-reset na początku tury
- **Pełna kompatybilność wsteczna** - stare save'y działają bez zmian

**Wpływ na balans:**
- **Artyleria (AL, AC, AP):** Limitowana do 1+1 ataku na turę
- **Inne jednostki (P, TL, K, Z, itp.):** Bez ograniczeń
- **Zwiększona tactical depth** - każdy strzał artylerii ma większą wagę
- **Eliminacja dominacji** arty spam bez utraty użyteczności artylerii

## 🗺️ WIDOCZNOŚĆ I FOG OF WAR (ISTOTNE DLA AI) - ZAKTUALIZOWANE

**SYSTEM GRADUOWANEJ WIDOCZNOŚCI (POZIOM 1 - ZAIMPLEMENTOWANY 30.08.2025):**

**Podstawowa mechanika:**
- Dowódca: widzi heksy w zasięgu swoich żetonów + **graduation detection_level**
- Generał: agregacja widoczności dowódców + pełna wiedza o własnych jednostkach
- Aktualizacja: `engine.update_all_players_visibility(players)` po ruchach / na starcie tury

**NOWE: System graduowanej detekcji przeciwników:**
- `detection_level = f(distance, sight_range)` - krzywa nieliniowa 0.0-1.0
- **FULL INFO** (detection ≥ 0.8): Pełne dane wroga (ID, CV, typ, nacja)
- **PARTIAL INFO** (detection ≥ 0.5): Ograniczone dane (skrócone ID, przedział CV, typ szacowany)
- **MINIMAL INFO** (detection < 0.5): Minimalne dane ("Nieznany kontakt", CV="???")

**Implementacja:**
- `VisionService.calculate_detection_level(distance, sight)` - oblicza poziom
- `VisionService._add_visible_enemy_tokens()` - dodaje detection_level do visible_token_data  
- `detection_filter.py` - filtruje informacje na podstawie poziomu
- `gui/detection_display.py` - przygotowuje dane do wyświetlenia w UI
- AI Commander używa detection_level do podejmowania decyzji

**Korzyści dla rozgrywki:**
- Realistyczne rozpoznanie bez "cheat vision"
- Zwiększona wartość jednostek zwiadowczych
- AI musi radzić sobie z niepewnością tak jak człowiek
- Stopniowe odkrywanie informacji zamiast binarnego "widzi/nie widzi"

AI musi działać w ramach tej samej informacji (brak „cheat vision").

Najważniejsze zmiany od 3.3 → 3.5:
1. **System ograniczenia strzałów artylerii** - kompletny z testami i dokumentacją
2. **Aktualizacja dokumentacji** - nowe przewodniki balansowania TOKEN i HEX
3. **Czyszczenie projektów** - usunięcie starych tokenów i plików tymczasowych
4. **Testy systemowe** - weryfikacja funkcjonalności artylerii i integracji
5. **Preparacja do dalszego rozwoju** - uporządkowana struktura dla kolejnych iteracji

Status: **System artylerii zbalansowany i testowany**; gotowy do dalszych ulepszeń AI i mechanik rozgrywki.

---

## 📁 STRUKTURA KODU (REALNA + PLANOWANA)

```
projekt/
├── main.py                      # Główny launcher gry (GUI, konfiguracja)
├── main_alternative.py          # Szybki start (bez ekranu konfiguracji)
├── requirements.txt             # Zależności
├── STRUKTURA_PROJEKTU.md        # Ten plik
├── accessibility/               # Rozszerzenia dostępności (szkielety)
├── backup/                      # System kopii zapasowych
├── core/                        # Logika „biznesowa” tur, ekonomii itd.
├── data/                        # Dane map / konfiguracja
├── docs/                        # Dokumentacja dodatkowa
├── edytory/                     # Edytory map / żetonów
├── engine/                      # Silnik gry (board, token, akcje, widoczność)
├── gui/                         # Panele interfejsu użytkownika
├── saves/                       # Zapisy stanu
├── scripts/                     # Skrypty porządkowe / automatyzacja
├── tests/                       # Testy (uporządkowane w podkatalogi)
│   ├── core/                   # Testy logiki biznesowej
│   ├── engine/                 # Testy silnika gry
│   ├── gui/                    # Testy interfejsu
│   ├── integration/            # Testy integracyjne
│   └── testy_dla_podrecznika/  # Testy dokumentacyjne
├── tools/                       # Narzędzia diagnostyczne i analizy PE
│   ├── analizator_przeplywu_pe.py    # Analiza przepływu PE między generałami i dowódcami
│   ├── launcher_analizy_pe.py        # Launcher testów PE z czyszczeniem danych
│   ├── sprawdzenie_rzetelnosci_zetonow.py  # Walidacja spójności tokenów PNG/JSON
│   ├── analizator_ai_na_zywo.py      # Real-time monitoring logów AI
│   └── diagnostyka_key_points.py     # Diagnostyka systemu key points
├── utils/                       # Pomocnicze moduły
└── ai/                          # Wstępny moduł sztucznej inteligencji (Faza 1 częściowa)
```

### Katalog `ai/` (stan bieżący + PE validation system)
```
ai/
├── __init__.py
├── ai_general.py              # (KOMPLETNY) Generał AI: ekonomia, alokacja, PE validation
├── ai_commander.py            # (ROZSZERZONY) Dowódca AI: taktyka, ruch, PE spending controls
├── zaopatrzenie_ai.py         # (NOWY) System PE validation i bezpiecznych transferów
├── ekonomia_ai.py             # (ROZSZERZONY) Ekonomia z PE balance checking
├── logowanie_ai.py            # (ROZSZERZONY) Logi PE flow i economic tracking
├── wybor_celow.py             # Target selection dla jednostek
├── grupowanie_ai.py           # Adaptive grouping i koordinacja
├── ruch_jednostek.py          # Movement system z MP validation
├── okupacja_punktow.py        # Garrison management
├── obrona_ai.py               # Defensive positioning
├── rajdy_ai.py                # Opportunistic captures
├── walka_ai.py                # Combat system z CV calculations
├── reakcje_ai.py              # Reaction fire system
├── priorytety_ai.py           # Key points scoring
├── konfiguracja_ai.py         # AI configuration constants
├── log_kategorie_ai.py        # Log categories definition
└── logs/                      # Generated CSV logs and analysis
```
```
ai/
├── __init__.py
 ├── ai_general.py        # (ZAIMPLEMENTOWANE) Generał AI: analiza ekonomii, alokacja punktów, logi
 ├── state_adapter.py     # (PLAN) Ekstrakcja stanu z GameEngine → struktury AI
 ├── evaluator.py         # (PLAN) Heurystyki i funkcje oceny (scoring)
 ├── tactical_agent.py    # (PLAN) Decyzje ruchu i walki (dowódcy)
 ├── strategic_agent.py   # (PLAN) Priorytety key points, zakupy, plan tury
 ├── base_agent.py        # (PLAN) Klasy bazowe / interfejsy
 ├── decision_queue.py    # (PLAN) Kolejkowanie i filtrowanie akcji
 ├── memory/              # (PLAN) Logi i dane adaptacyjne
 └── README.md            # (PLAN) Dokumentacja modułu AI
```

### Tabela postępu faz AI (stan na 03.09.2025)

| Faza | Status | Pokrycie | Notatki |
|------|--------|----------|---------|
| 0 Dokumentacja kontraktu | ZAKOŃCZONA | 100% | API zidentyfikowane w wersji 3.0 |
| 1 Szkielet modułu | ZAKOŃCZONA | 100% | AI Commander + AI General implementowane |
| 2 Adapter stanu | ZAKOŃCZONY | 100% | PE validation + economic state management |
| 3 Ruch taktyczny | ZAKOŃCZONY | 85% | Ruch, progresywny movement, garrison limit, opportunistic capture |
| 4 Walka selektywna | ZAKOŃCZONY | 75% | System ograniczenia artylerii, PE-controlled combat |
| 5 Strategia key points | ZAKOŃCZONY | 70% | Capture + bonusy + PE-based prioritization |
| 6 Ekonomia / zakupy | ZAKOŃCZONY | 95% | PE validation system, safe transfers, economic stability |
| 7 Poziomy trudności | CZĘŚCIOWO | 30% | Adaptive strategies, brak MCTS |
| 8 Logowanie decyzji | ZAKOŃCZONY | 95% | Comprehensive PE flow logging, economic analysis |
| 9 Adaptacja | CZĘŚCIOWO | 15% | Podstawowa adaptacja strategiczna |

### Obecna funkcjonalność AI (3.8 - PE VALIDATION COMPLETE)

**AI GENERAL (KOMPLETNY POZIOM STRATEGICZNY + PE SECURITY):**
* ✅ Pełny parytet z human generałem - VP, Key Points, faza gry
* ✅ 5 strategii adaptacyjnych (ROZWÓJ/KRYZYS_PALIWA/DESPERACJA/OCHRONA/EKSPANSJA)
* ✅ System budżetu 20-40-40 z elastycznym podziałem
* ✅ Analiza per dowódca (paliwo, combat value, typy jednostek)
* ✅ EconAction.COMBO - kombinacja alokacji + zakupów
* ✅ **PE VALIDATION SYSTEM** - eliminacja ujemnych PE, bezpieczne transfery
* ✅ **Economic stability** - walidacja bilansów, multi-layer protection
* ✅ Kompletne logowanie ekonomii, Key Points, strategii, PE flow
* ❌ **BRAK: MCTS algorithm, machine learning, poziomy trudności**

**AI COMMANDER (KOMPLETNY POZIOM TAKTYCZNY + PE CONTROLS):**
* ✅ Ruch (full + progresywny) z adaptacją MP i PE validation
* ✅ **PE spending controls** - brak możliwości ujemnych wydatków
* ✅ Oportunistyczne capture + priorytety dla odłączonych KP
* ✅ Garrison limit + podstawowy stub rotacji
* ✅ **Comprehensive PE logging** - pełne śledzenie wydatków
* ✅ Rozszerzone logi: path_len, path_used, progressive_used, decision_reason
* ✅ Combat system z walidacją PE przed resupply
* ✅ Turn summary: casualties_turn / new_units_turn
* ✅ **Economic safety** - blokada operacji przy niewystarczających PE
* ❌ Brak pełnej rotacji garnizonów (stabilny placeholder)
* ❌ Brak advanced retreat/reposition heurystyk

### Znane ograniczenia (3.8 - POST PE VALIDATION)

**AI GENERAL:**
* Brak Monte Carlo Tree Search dla trudniejszych poziomów
* Brak machine learning adaptacji między grami  
* Brak opponent modeling
* Sztywne strategie bez dynamicznego dostrajania wag

**AI COMMANDER (STABILNE OGRANICZENIA - PO PE VALIDATION):**
* ✅ **PE VALIDATION RESOLVED** - system ekonomiczny bezpieczny i stabilny
* ✅ **Resupply system działający** - kontrola PE, walidacja wydatków
* ✅ **Economic stability** - brak crashy ekonomicznych, poprawne bilanse
* Brak advanced risk-based combat (cv_ratio / przewidywane straty) 
* skip_reason: kolumna istnieje, podstawowe wypełnianie (potrzebne rozszerzenie)
* Brak purge martwych alokacji (budżet mrożony w sektorach 0 units)
* Brak effective_move_rate & attack_success_rate (agregaty)
* Brak zaawansowanej rotacji garnizonów (podstawowy system działa)

**SYSTEM BALANSOWANIA:**
* ✅ **Artyleria zbalansowana** - eliminacja dominacji przez ograniczenie strzałów
* ✅ **PE system bezpieczny** - eliminacja ujemnych PE, stabilna ekonomia
* ✅ **Dokumentacja kompletna** - przewodniki TOKEN i HEX balancing
* ❌ **Potrzebne dalsze testy** - wpływ na AI vs AI i długie kampanie
* ❌ **Brak reakcji AI** na nowy system (może wymagać dostrojenia heurystyk)

---

## ♻️ REFAKTORYZACJA AI COMMANDER (02.09.2025) – PODSUMOWANIE DZISIEJSZEJ SESJI

CEL: Uporządkować monolityczny plik dowódcy, wprowadzić modularną strukturę i bezpieczne wywołania aby móc iteracyjnie dodawać heurystyki (Emergency / skip_reason / resupply) bez ryzyka psucia podstawowego flow.

KLUCZOWE ZMIANY STRUKTURALNE:
* Styl funkcyjny (nagłówek pliku: brak klas, małe funkcje, ograniczenia długości) – łatwiejsze wycinanie do osobnych modułów.
* Snapshot stanu jednostek (starting_unit_ids / ending_unit_ids) → baza dla `casualties_turn` i `new_units_turn`.
* Centralizacja logowania: jednolite wywołania `log_commander_action` / `log_commander_turn` (moduł `ai.logowanie_ai`).
* Dodane kolumny schematu (action: `skip_reason`; turn: `casualties_turn`, `new_units_turn`).
* Fallback importów (try/except) – gdy moduł nie istnieje, Commander nie przerywa tury (degradacja łagodna zamiast crash).

WYDZIELONE / DOCZEPUJĄCE SIĘ MODUŁY (refaktoryzacja etapowa):
| Obszar | Moduł | Status |
|--------|-------|--------|
| Wybór celów | `ai.wybor_celow` | używany (find_target, alternatywy) |
| Grupowanie / koordynacja | `ai.grupowanie_ai` | używany (adaptive_grouping, reassignment) |
| Ruch / tryb ruchu | `ai.ruch_jednostek` | używany (move_towards, choose_movement_mode) |
| Okupacja / garnizony | `ai.okupacja_punktow` | używany (enforce_garrison_limits) |
| Obrona | `ai.obrona_ai` | podłączone funkcje oceny zagrożeń |
| Rajdy / capture opportunistyczne | `ai.rajdy_ai` | delegacja opportunistic_capture_phase |
| Walka | `ai.walka_ai` | delegaty (ratio, flank, execute) |
| Reakcje | `ai.reakcje_ai` | reaction fire sprawdzany po ruchu |
| Zaopatrzenie | `ai.zaopatrzenie_ai` | stałe & liczniki (paliwo / resupply future) |
| Priorytety KP | `ai.priorytety_ai` | czyste funkcje scoringu (bonusy / kary) |

BEZPIECZEŃSTWO / OGRANICZENIE RYZYKA:
* Limit iteracji (cięcia list) przy pętlach: `[:200]`, `[:80]` – zapobiega wzrostowi kosztu przy większych mapach.
* `getattr(..., default)` wszędzie → brak twardych zależności przy brakujących polach.
* Try/except wokół importów modułów eksperymentalnych.
* Test jednostkowy (minimalny) sprawdzający obecność nowych kolumn logów – sanity gate przy kolejnych zmianach.

CO JESZCZE DO DOKOŃCZENIA (NA BAZIE NOWEJ STRUKTURY):
* Implementacja realnych wartości `skip_reason` (źródła stagnacji: NO_PATH, ZERO_MP, GARRISON_HOLD, LOW_FUEL, BLOCKED).
* Agregaty: `effective_move_rate` (moved_units / eligible_movers) & `attack_success_rate` (successful_attacks / attempted_attacks).
* Emergency Mode – wyzwalacz oparty o trend `casualties_turn` + niski stosunek `new_units_turn`.
* Resupply logika właściwa (obecnie placeholder pre_resupply) – wykorzystanie paliwa i progów CV.
* Purge martwych alokacji sektorów – zwalnianie „zamrożonych” budżetów.
* Risk‑based combat gating (cv_ratio & projected losses) – wpięcie przed `execute_ai_combat`.

OGRANICZENIA OBECNEJ IMPLEMENTACJI (TECHNICZNE):
* `casualties_turn` zakłada zniknięcie ID = utrata – nie rozróżnia jeszcze transferu / despawn eventów specjalnych.
* Brak osobnej warstwy state adapter dla Commandera – część ekstrakcji stanu nadal inline.
* Brak izolowanych testów funkcji scoringu (priorytety KP) – tylko log diagnostyczny TOP 8.
* Brak mechanizmu throttle dla spamujących debug_print przy FULL – potencjalny koszt IO.

WERYFIKACJA: Commander po refaktoryzacji przechodzi test logów (generuje plik z nowymi kolumnami). Brak regresji w podstawowym ruchu (przejścia pętli taktycznej). 

Następna iteracja: wypełnianie `skip_reason` + dodanie liczników ataków (attempted/success) w `walka_ai` do agregacji.

---

## 🧠 ARCHITEKTURA LOGICZNA

| Warstwa | Obecnie | Rola w AI |
|---------|---------|-----------|
| Engine (`engine/`) | TAK | Dostarcza prymitywy: ruch, walka, widoczność, stan |
| Core (`core/`) | TAK | Tury, ekonomia (key points), warunki zwycięstwa |
| GUI (`gui/`) | TAK | Interakcja człowieka – dla AI nieużywana (AI działa programowo) |
| Edytory | TAK | Generowanie/scenariusze testowe |
| AI (`ai/`) | CZĘŚCIOWO | Ekonomia (alokacja), analiza stanu – brak ruchu i walk |

---

## 🔌 PUBLICZNY KONTRAKT DLA AI

### 1. Silnik (`GameEngine` w `engine/engine.py`)
Kluczowe atrybuty/metody dostępne bez zmian kodu:
- `engine.tokens` – lista obiektów `Token`
- `engine.board` – obiekt planszy
- `engine.turn`, `engine.current_player`
- `engine.execute_action(action, player)` → `(success, message)` / `ActionResult`
- `engine.end_turn()` / `engine.next_turn()`
- `engine.process_key_points(players)` – przydział ekonomii
- `engine.update_all_players_visibility(players)` – aktualizacja FOW
- `engine.key_points_state` – słownik key points

### 2. Token (`engine/token.py`)
Pola: `id, owner, q, r, stats{move, combat_value, defense_value, attack{value, range}, sight, price, nation}`
Dynamiczne: `currentMovePoints, currentFuel, combat_value, movement_mode`
Metody: `apply_movement_mode(reset_mp=True)`, `get_movement_points()`, `can_move_reason()`

### 3. Plansza (`engine/board.py`)
- `find_path(start, goal, max_mp, max_fuel, visible_tokens=null, fallback_to_closest=False)`
- `hex_distance(a, b)`
- `get_tile(q, r)` → `Tile(move_mod, defense_mod, type, value, spawn_nation)`
- `is_occupied(q, r)` / `neighbors(q, r)`

### 4. Akcje (`engine/action_refactored_clean.py`)
- `MoveAction(token_id, dest_q, dest_r)`
- `CombatAction(attacker_id, defender_id)`
- `ActionResult(success, message, data)`

### 5. Widoczność
- Po wywołaniu `update_all_players_visibility`: `player.visible_hexes`, `player.visible_tokens`
- Generał: pełna widoczność własnych + wrogowie odkryci przez dowódców

### 6. Key Points
- Format: `key_points_state['q,r'] = {initial_value, current_value, type}`
- Pozostała „żywotność” = `ceil(current_value / (0.1 * initial_value))` tur

### 7. (Do dodania) API zakupów – proponowany kontrakt
```
engine.purchase_unit(player, blueprint_id, spawn_hex) -> (success: bool, msg: str, token_id: Optional[str])
```
Walidacja: dostępne punkty ekonomiczne, poprawny spawn (`tile.spawn_nation == player.nation`), unikalność ID.

---

## 🧩 UPROSZCZONY WIDOK STANU DLA AI (PROPOZYCJA)
```jsonc
{
  "turn": 7,
  "player": {"id": 2, "role": "dowódca", "nation": "Polska"},
  "economy": {"points": 40},
  "key_points": [ {"q":3,"r":-1,"type":"city","current":70,"ours":true} ],
  "self_tokens": [ {"id":"P_INF_1","q":3,"r":0,"cv":5,"mp":5,"fuel":10,"atk":4,"rng":2,"def":3} ],
  "enemy_visible": [ {"id":"N_TANK_2","q":5,"r":0,"cv":8,"rng":1} ],
  "map": {"cols": X, "rows": Y}
}
```

---

## 🧮 HEURYSTYKA STARTOWA (ITERACJA 1)
Formuła punktacji heksa docelowego:  
`SCORE = (V_strategiczna + V_ofensywna - R_ryzyko) / (1 + koszt_ruchu)`

Składniki:
- `V_strategiczna`: +współczynnik * (typ key point * pozostałe tury życia) + bonus za `defense_mod`
- `V_ofensywna`: możliwość ataku na jednostkę o niskim `combat_value` / wysokiej cenie
- `R_ryzyko`: liczba wrogich kontrataków * przewidywane straty
- `koszt_ruchu`: suma kosztów MP trasy (A*)

Progi decyzji (konfigurowalne):
- Nie atakuj jeśli przewidywane straty > 60% własnego `combat_value`
- Priorytet key pointu jeśli wyczerpie się w ≤ 3 turach
- Unikaj pól w zasięgu ≥ 3 wrogich jednostek o zasięgu ataku

---

## 🔄 PLAN WDROŻENIA AI (FAZY)

| Faza | Zakres | Artefakty | Kryterium sukcesu |
|------|--------|-----------|-------------------|
| 0 | Dokumentacja kontraktu | Ten plik | API kompletne bez refactoru silnika |
| 1 | Szkielet modułu | `ai/` + klasy bazowe | Import działa, test pusty przechodzi |
| 2 | Adapter stanu | `state_adapter.py` | Zwraca spójny JSON dla dowódcy i generała |
| 3 | Ruch taktyczny | `tactical_agent.py` | Jednostki przemieszczają się legalnie do celu |
| 4 | Walka selektywna | Ewaluator | AI eliminuje osłabione jednostki bez suicydów |
| 5 | Strategia key points | `strategic_agent.py` | AI kieruje ≥50% ruchów ku kluczowym celom |
| 6 | Ekonomia / zakupy | purchase API | Nowe jednostki poprawnie spawnują się |
| 7 | Poziomy trudności | konfiguracja wag | Różne style zachowań (defensywne/agresywne) |
| 8 | Logowanie decyzji | `memory/` | Powtarzalność przy identycznym seed |
| 9 | Adaptacja (opcjonalnie) | analityka wag | Poprawa wyniku VP w serii testów |

---

## 🧪 REKOMENDOWANE TESTY (NOWE DLA AI)
- `test_ai_state_adapter.py` – poprawność formatu i filtrowanie widoczności
- `test_ai_path_selection.py` – wybór najkorzystniejszej ścieżki (mniejszy koszt)
- `test_ai_target_selection.py` – selekcja celu o najlepszym stosunku (wartość / ryzyko)
- `test_ai_key_point_focus.py` – ruch w stronę krytycznego key pointu
- `test_ai_purchase_logic.py` – brak nadwyżek ekonomii i validacja spawnów
- `test_ai_determinism.py` – identyczne decyzje dla ustalonego seeda

---

## 📊 STATYSTYKI (AKTUALNE – WERSJA 3.1)
- Edytor żetonów: 1427 linii
- Edytor map: 1088 linii
- Silnik (engine + akcje + board + token): ~850+ linii
- GUI: ~1000+ linii
- Moduł AI: wstępny (2 pliki: `__init__.py`, `ai_general.py`) – kod alokatora + logika analizy

Funkcjonalności potwierdzone: ruch, walka, pathfinding, widoczność warstwowa, key points z ekonomią, zapis stanu, refaktoryzowane akcje.

---

## 🏆 SYSTEM KEY POINTS – SKRÓT TECHNICZNY
- Struktura w `engine.key_points_state`
- Przydział ekonomii: `give = max(1, int(0.1 * initial_value))` (nie większy niż `current_value`)
- Po wyzerowaniu usunięcie z mapy + zapis aktualizacji

Sugestia dla AI: planowanie kolejki przejęć według (pozostałe_tury * typ_wagi) – (dystans MP).

---

## 🗺️ WIDOCZNOŚĆ I FOG OF WAR (ISTOTNE DLA AI)
- Dowódca: widzi tylko heksy w zasięgu swoich żetonów (+ tymczasowe)
- Generał: agregacja widoczności dowódców + pełna wiedza o własnych jednostkach
- Aktualizacja: `engine.update_all_players_visibility(players)` po ruchach / na starcie tury

AI musi działać w ramach tej samej informacji (brak „cheat vision”).

---

## 🔐 ZASADY FAIR PLAY DLA AI
- Brak podejmowania akcji na podstawie niewidocznych wrogów
- Brak modyfikacji punktów ruchu / paliwa poza systemem
- Zakupy tylko przez publiczne API zakupów
- Decyzje deterministyczne przy ustalonym seed (testowalność)

---

## 🧭 NASTĘPNE KROKI (PRIORYTETY TECHNICZNE – AKTUALNE 03.09.2025)

### **COMPLETED - PE VALIDATION SYSTEM ✅**
~~1. PE validation system - eliminacja ujemnych PE~~
~~2. Economic stability - bezpieczne transfery PE~~
~~3. Comprehensive PE logging - pełne śledzenie przepływu~~
~~4. Multi-layer protection - walidacja na wszystkich poziomach~~

### **IMMEDIATE PRIORITIES – AI OPTIMIZATION POST-PE-FIX**
1. **Performance analysis** - analiza wpływu PE validation na wydajność AI
2. **Advanced skip_reason** implementation - rozszerzona diagnostyka stagnacji
3. **Emergency Mode trigger** oparty o casualties_turn + PE shortage
4. **Purge martwych alokacji** - reset po 3 turach z total_units == 0
5. **Enhanced resupply logic** - optymalizacja PE spending priorities
6. **Garrison rotation system** - zaawansowany management okupacji
7. **Attack success rate tracking** - metryki skuteczności walk

### **MEDIUM TERM – SYSTEM OPTIMIZATION**
8. **AI vs AI balance testing** - długie kampanie z PE validation
9. **Economic efficiency metrics** - analiza wykorzystania PE
10. **Advanced combat risk assessment** - cv_ratio + projected losses
11. **MCTS foundation** - przygotowanie do lookahead 3-5 tur
12. **Adaptive strategy tuning** - parametryzacja wag na podstawie wyników

### **LONG TERM – ADVANCED AI FEATURES**
13. **Machine Learning integration** - meta-statystyki skuteczności
14. **Enhanced General↔Commander feedback** - adaptacja alokacji wg efektywności
15. **Specialization profiles** - AI Commander variants (agresywny/defensywny/mobilny)
16. **Advanced economic modeling** - przewidywanie potrzeb PE based on map analysis

## 🗒 CHANGELOG
**3.8 (03.09.2025) - PE VALIDATION SYSTEM COMPLETE**
* **🔒 SYSTEM PE VALIDATION** - kompletna implementacja zabezpieczeń ekonomicznych
* Multi-layer protection w `ai/zaopatrzenie_ai.py` i `core/ekonomia.py`
* `validate_pe_spending()`, `transfer_pe_to_commanders()`, `check_pe_balance()`
* Eliminacja ujemnych PE - hard stop dla nieprawidłowych operacji
* Comprehensive PE flow logging - pełne śledzenie ekonomii w CSV
* `auto_game_10_turns.py` z PE tracking - launcher testów AI vs AI
* `tools/launcher_analizy_pe.py` - zintegrowany system testów z czyszczeniem
* `tools/analizator_przeplywu_pe.py` - analiza ekonomii per rundę
* **Weryfikacja sukcesu:** Ujemne PE wyeliminowane, bilanse zgadzają się 100%
* **Stabilność ekonomiczna:** AI bezpieczne, brak crashy, poprawne transfery PE

**3.7 (02.09.2025) - AI IMPROVEMENTS FAZA 2**
* Ulepszenia AI target selection - success rate 0% → 37.5%
* Poprawione ładowanie key_points, zwiększone limity wyszukiwania
* Rozszerzona diagnostyka pathfindingu - 5 nowych kolumn CSV
* Refaktoryzacja AI Commander - struktura modularna, bezpieczne wywołania

**3.6 (02.09.2025) - ROZSZERZENIE LOGÓW AI (ATTRITION PHASE 1)**
* Dodane kolumny turn summary: `casualties_turn`, `new_units_turn`
* Dodana kolumna action log: `skip_reason` (placeholder – brak wypełniania)
* Przygotowanie pod Emergency Mode i analizę tempa odbudowy
* Brak zmian heurystyk (czysto obserwacyjne wdrożenie)

**3.5 (31.08.2025) - SYSTEM BALANSOWANIA ARTYLERII**
* **🎯 SYSTEM OGRANICZENIA STRZAŁÓW ARTYLERII** - pełna implementacja
* Token.shots_fired_this_turn, reaction_shot_used - ograniczenia AL/AC/AP do 1+1 ataku/turę
* CombatAction._validate_combat() - automatyczna walidacja przed atakiem
* core/tura.py i engine/engine.py - auto-reset na początku tury
* tests/test_artillery_shot_limits.py - komprehensywny test suite (wszystkie testy przeszły)
* docs/ARTILLERY_SHOT_LIMITS.md - kompletna dokumentacja systemu
* docs/TOKEN_BALANCING_GUIDE.md - przewodnik balansowania jednostek
* Czyszczenie projektu: usunięcie starych tokenów z assets/tokens/
* Eliminacja dominacji "arty spam" przy zachowaniu użyteczności artylerii

**3.4 (30.08.2025) - NOWA WERSJA**
* **🎯 SYSTEM GRADUOWANEJ WIDOCZNOŚCI POZIOM 1** - pełna implementacja
* VisionService.calculate_detection_level() - krzywa nieliniowa detekcji
* detection_filter.py - filtrowanie informacji o wrogach (FULL/PARTIAL/MINIMAL)
* gui/detection_display.py - przygotowanie danych do GUI
* AI Commander integracja z detection_level dla realistycznych decyzji
* Kompleksowe testy i demonstracje funkcjonalności
* Aktualizacja engine/action_refactored_clean.py i engine/engine.py

**3.3 (29.08.2025)**
* Pakiet 6 usprawnień AI Commander (movement/capture/garrison/logi)
* Rozszerzone logi ekonomii (allocate/purchase budgets, low_fuel_ratio, orders_issued)
* Tryb SLEEP strategicznych rozkazów (generowanie = False)
* Launcher: czyszczenie logów, skrót, większe okno
* Diagnoza attrition → plan Emergency Mode & purge
* Wykryty brak czyszczenia `assets/tokens/aktualne/`

**3.2 (24.08.2025)** – analiza stanu, logi rozszerzone, identyfikacja braków

**3.0 (15.08.2025)** – kontrakt AI, szkic faz

## ⚡ SZYBKI START (JUTRO – 5 MIN)
1. Uruchom launcher → Start Gry (potwierdź auto‑czyszczenie). 
2. Sprawdź `ai/ai_general.py` czy `GENERATE_ORDERS` ma oczekiwaną wartość.
3. Włącz AI dla obu stron (generał + dowódcy), zagraj 5-10 tur.
4. **NOWE:** Obserwuj PE flow - brak ujemnych wartości w logach ✅
5. **Test PE validation:** Uruchom `tools/launcher_analizy_pe.py` 
6. **Analiza ekonomii:** Sprawdź `tools/analizator_przeplywu_pe.py`
7. **Weryfikacja stabilności:** PE bilanse muszą się zgadzać 100%
8. **Test systemu artylerii:** `python tests/test_artillery_shot_limits.py`

## 🧪 METRYKI – STAN 3.8 (PE VALIDATION COMPLETE)
| Metryka | Status | Cel | Wykorzystanie |
|---------|--------|-----|---------------|
| **pe_flow_validation** | **ZAIMPLEMENTOWANA** | **economic stability** | **eliminacja ujemnych PE** |
| **pe_transfer_safety** | **ZAIMPLEMENTOWANA** | **safe General→Commander** | **poprawne alokacje** |
| **pe_balance_checking** | **ZAIMPLEMENTOWANA** | **bilans accuracy** | **weryfikacja operacji** |
| casualties_turn | ZAIMPLEMENTOWANA | tracking attrition | wyzwalacz Emergency Mode |
| new_units_turn | ZAIMPLEMENTOWANA | tempo odtwarzania | ocena regeneracji sił |
| skip_reason | SCHEMAT (podstawowe) | diagn. stagnacji | tuning heurystyk ruchu |
| effective_move_rate | PLAN | aktywność taktyczna | wykrycie stagnacji |
| attack_success_rate | PLAN | skuteczność walk | ocena wpływu limitów artylerii |
| artillery_shots_used | CZĘŚCIOWO (surowe dane) | monitor artylerii | walidacja limitu 1+1 |
| **econ_efficiency** | **PLAN (ready for impl.)** | **wydatkowanie budżetu** | **ocena alokacji PE** |

## 🧼 PLAN ROZSZERZENIA CZYSZCZENIA
Aktualnie: quick_clean() usuwa tylko `nowe_dla_*`; full_clean() dodatkowo logi. NIE usuwa `assets/tokens/aktualne/` ani `saves/after_deployment.json`.
Plan: dodać `clean_deployed_tokens()` + wywołać w full_clean (opcjonalna flaga zachowania).

## 🔍 DIAGNOSTYKA PO SESJI
| Pytanie | Gdzie patrzeć | Oczekiwane |
|---------|---------------|------------|
| **Czy PE validation działa?** | **tools/analizator_przeplywu_pe.py output** | **Brak ujemnych PE, bilanse się zgadzają** |
| **Czy transfery PE są bezpieczne?** | **AI economic logs pe_allocated kolumna** | **Poprawne Generał→Dowódcy without overflow** |
| **Czy system artylerii działa?** | **actions CSV artillery_shots kolumna** | **≤ 2 ataki/turę per jednostka artylerii** |
| Czy attrition stabilne? | ai_actions own_units / casualties_turn | Brak gwałtownych spadków <50%/3 tury |
| Czy budżet nie stoi? | econ_after vs econ_before | Spadek >50% przy COMBO |
| **Czy ekonomia nie crashuje?** | **Exception logs + PE negative values** | **Zero crashes, zero negative PE** |
| Czy ruch aktywny? | turn_summary moved_units | ≥70% wczesnych tur |
| skip_reason (po wdrożeniu) pełny? | actions CSV | <10% pustych |
| Czy AI adaptuje się do limitów artylerii? | attack_success_rate (PLANNED) | Stabilny / rosnący bez spamu |

---

## 📚 META
Dokument przygotowuje grunt pod implementację gracza komputerowego bez refaktoryzacji istniejących modułów. Zmiany w silniku ograniczyć do dodania (jeśli brak) jednolitego API zakupów. **System ograniczenia artylerii + metryki attrition tworzą podstawę do wdrożenia Emergency Mode.**

Wersja: 3.6 (2 września 2025)
Status: **Artyleria zbalansowana (3.5) + rozszerzone logi attrition (3.6)** – gotowe do implementacji Emergency Mode / skip_reason logic
Autor aktualizacji: automatyczny asystent + analiza logów + implementacja systemu balansowania & metryk

**Najważniejsze osiągnięcia wersji 3.6:**
- ✅ Dodane metryki attrition (casualties_turn / new_units_turn)
- ✅ Przygotowany schemat skip_reason (pusty – nienaruszony backward compatibility)
- ✅ Zachowana stabilność po limicie artylerii
- ✅ Dokumentacja uaktualniona (priorytety + roadmap)
- ✅ Gotowość do kolejnej iteracji (Emergency Mode / skip reasons)

---

*Koniec dokumentu.*
