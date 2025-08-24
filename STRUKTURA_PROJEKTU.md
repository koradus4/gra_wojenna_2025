# STRUKTURA PROJEKTU KAMPANIA 1939

## 📌 STAN BIEŻĄCY (Sierpień 2025) – WERSJA 3.1 – POSTĘP WDROŻENIA AI

Aktualizacja dostosowana do implementacji modułu AI (gracza komputerowego). W przeciwieństwie do wersji 3.0 katalog `ai/` **już istnieje** i zawiera wstępny szkielet (`__init__.py`, `ai_general.py`). Zaimplementowano podstawowego Generała AI skupionego na analizie ekonomii i ważonym przydziale punktów do dowódców (alokacja 60% budżetu z systemem wag i karą za niewydane środki). Brak jeszcze: faktycznych zakupów jednostek, ruchu taktycznego oraz heurystyk mapowych. Kod silnika nadal dostarcza stabilne punkty zaczepienia: ruch, walka, pathfinding, widoczność, ekonomia (key points) i zapis stanu.

**Nowe w 3.1 (skrót):** katalog `ai/`, klasa `AIGeneral` (alokacja ekonomii + logowanie po polsku), fundament pod przyszłe fazy.

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
├── tools/                       # Narzędzia diagnostyczne
├── tools/                       # Narzędzia diagnostyczne
├── utils/                       # Pomocnicze moduły
└── ai/                          # Wstępny moduł sztucznej inteligencji (Faza 1 częściowa)
```

### Katalog `ai/` (stan bieżący + planowane rozszerzenia)
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

### Tabela postępu faz AI (stan na 24.08.2025)

| Faza | Status | Pokrycie | Notatki |
|------|--------|----------|---------|
| 0 Dokumentacja kontraktu | ZAKOŃCZONA | 100% | API zidentyfikowane w wersji 3.0 |
| 1 Szkielet modułu | ZAKOŃCZONA | 100% | AI Commander + AI General implementowane |
| 2 Adapter stanu | CZĘŚCIOWO | ~60% | Podstawowa analiza stanu, brak pełnego JSON API |
| 3 Ruch taktyczny | CZĘŚCIOWO | ~40% | AI Commander: ruch bez walki, brak resupply |
| 4 Walka selektywna | NIE ROZPOCZĘTO | 0% | Brak CombatAction w AI Commander |
| 5 Strategia key points | CZĘŚCIOWO | ~30% | AI General: analiza KP, AI Commander: brak capture |
| 6 Ekonomia / zakupy | CZĘŚCIOWO | ~70% | AI General: pełna implementacja, AI Commander: brak resupply |
| 7 Poziomy trudności | CZĘŚCIOWO | ~20% | AI General: strategie, brak MCTS |
| 8 Logowanie decyzji | CZĘŚCIOWO | ~60% | AI General: pełne logi, AI Commander: tylko ruchy |
| 9 Adaptacja | NIE ROZPOCZĘTO | 0% | Brak pamięci / uczenia maszynowego |

### Obecna funkcjonalność AI (3.2 - ZAKTUALIZOWANA)

**AI GENERAL (KOMPLETNY POZIOM STRATEGICZNY):**
* ✅ Pełny parytet z human generałem - VP, Key Points, faza gry
* ✅ 5 strategii adaptacyjnych (ROZWÓJ/KRYZYS_PALIWA/DESPERACJA/OCHRONA/EKSPANSJA)
* ✅ System budżetu 20-40-40 z elastycznym podziałem
* ✅ Analiza per dowódca (paliwo, combat value, typy jednostek)
* ✅ EconAction.COMBO - kombinacja alokacji + zakupów
* ✅ Kompletne logowanie ekonomii, Key Points, strategii
* ❌ **BRAK: MCTS algorithm, machine learning, poziomy trudności**

**AI COMMANDER (PODSTAWOWY POZIOM TAKTYCZNY):**
* ✅ Podstawowy ruch jednostek z pathfinding MP/Fuel
* ✅ Strategiczne rozkazy z JSON + autonomiczny fallback  
* ✅ Logowanie akcji do CSV
* ❌ **BRAK: Resupply (fuel/combat regeneration)**
* ❌ **BRAK: Combat system (CombatAction)**
* ❌ **BRAK: Key points capture/hold**
* ❌ **BRAK: Retreat/reposition tactics**

### Znane ograniczenia (3.2)

**AI GENERAL:**
* Brak Monte Carlo Tree Search dla trudniejszych poziomów
* Brak machine learning adaptacji między grami  
* Brak opponent modeling
* Sztywne strategie bez dynamicznego dostrajania wag

**AI COMMANDER (KRYTYCZNE LUKI):**
* **pre_resupply()** to placeholder - brak uzupełniania fuel/combat za punkty ekonomiczne
* Brak implementacji walki - tylko ruch, żadnych ataków
* Brak taktycznych objectives (capture, retreat, reposition)
* Brak integracji z player.punkty_ekonomiczne dla resupply
* Niezaimplementowane formation awareness i multi-unit coordination

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
- `find_path(start, goal, max_mp, max_fuel, visible_tokens=None, fallback_to_closest=False)`
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

## 🧭 NASTĘPNE KROKI (PRIORYTETY TECHNICZNE – ZAKTUALIZOWANE 24.08.2025)

### **IMMEDIATE PRIORITIES - AI COMMANDER:**
1. **(KRYTYCZNY) Implementacja resupply system** - sekcja 22 z AI_COMMANDER_PLAN.md
   - pre_resupply() z budżetem 20% rezerwa + 80% operacyjny
   - Uzupełnianie fuel/combat za player.punkty_ekonomiczne
   - Priorytetyzacja: paliwo < 30% → combat < 50% → key points

2. **(WAŻNY) Combat system implementation**
   - CombatAction dla AI Commander
   - Analiza wrogów w zasięgu ataku
   - Combat ratio evaluation (min 1.3 dla bezpiecznego ataku)

3. **(WAŻNY) Key points capture/hold**
   - Capture objectives dla neutralnych/wrogich KP
   - Hold objectives dla własnych KP z economic value

### **MEDIUM TERM - AI GENERAL:**
4. **(Faza 7) Monte Carlo Tree Search**
   - Implementacja MCTS dla poziomów Medium/Hard/Expert
   - Tree search dla decyzji budżetowych
   - Simulation engine z lookahead 3-5 tur

5. **(Faza 7) Poziomy trudności**
   - 4 poziomy: Easy (heurystyki) → Expert (MCTS + ML)
   - Różne time budgets i exploration parameters
   - Adaptive difficulty na podstawie win rate

### **LONG TERM - ADVANCED AI:**
6. **(Faza 9) Machine Learning adaptacja**
   - Memory system dla skutecznych strategii
   - Pattern recognition dla typów przeciwników  
   - Meta-learning między grami

7. **(Integration) AI Coordination**
   - AI General → strategic orders → AI Commander
   - Feedback loop przez VP, economic efficiency
   - Commander specialization (różne style per dowódca)

## 🗒️ CHANGELOG
**3.2 (24.08.2025)**
* **MAJOR UPDATE** - Pełna analiza rzeczywistego stanu AI implementation
* AI General: KOMPLETNY poziom strategiczny z 5 strategiami adaptacyjnymi
* AI Commander: PODSTAWOWY poziom taktyczny, BRAK resupply/combat/capture
* Zaktualizowano tabele postępu - rzeczywiste % completion
* Dodano krytyczne luki: resupply, combat system, key points capture
* Plan rozwoju: MCTS dla AI General, resupply/combat dla AI Commander
* Zmieniono priorytety na immediate (resupply) vs long term (MCTS)

**3.0 (15.08.2025)**
* Konsolidacja dokumentacji kontraktu dla AI (bez implementacji katalogu `ai/`)
* Określenie faz wdrożenia i heurystyk startowych

---

## 📚 META
Dokument przygotowuje grunt pod implementację gracza komputerowego bez refaktoryzacji istniejących modułów. Zmiany w silniku ograniczyć do dodania (jeśli brak) jednolitego API zakupów.

Wersja: 3.1 (20 sierpnia 2025)
Status: Częściowa implementacja (Generał ekonomiczny)
Autor aktualizacji: analiza wewnętrzna / automatyczna aktualizacja AI

---

*Koniec dokumentu.*
