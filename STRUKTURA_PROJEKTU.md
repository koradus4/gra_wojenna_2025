# STRUKTURA PROJEKTU KAMPANIA 1939

## 📌 STAN BIEŻĄCY (31 sierpnia 2025) – WERSJA 3.5 – SYSTEM BALANSOWANIA ARTYLERII

Aktualizacja koncentruje się na: **implementacji systemu ograniczenia strzałów artylerii**, aktualizacji dokumentacji projektowej i usprawnieniu równowagi gry.

## 🎯 NOWY SYSTEM OGRANICZENIA STRZAŁÓW ARTYLERII (POZIOM 1 - ZAIMPLEMENTOWANY 31.08.2025):

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

### Tabela postępu faz AI (stan na 31.08.2025)

| Faza | Status | Pokrycie | Notatki |
|------|--------|----------|---------|
| 0 Dokumentacja kontraktu | ZAKOŃCZONA | 100% | API zidentyfikowane w wersji 3.0 |
| 1 Szkielet modułu | ZAKOŃCZONA | 100% | AI Commander + AI General implementowane |
| 2 Adapter stanu | CZĘŚCIOWO | ~60% | Podstawowa analiza stanu, brak pełnego JSON API |
| 3 Ruch taktyczny | CZĘŚCIOWO | ~55% | Ruch, progresywny movement, garrison limit, opportunistic capture |
| 4 Walka selektywna | CZĘŚCIOWO | ~25% | **NOWE:** System ograniczenia artylerii zaimplementowany, podstawowa integracja CombatAction |
| 5 Strategia key points | CZĘŚCIOWO | ~45% | Capture opportunistyczne + bonusy, brak trwałego hold/rotation |
| 6 Ekonomia / zakupy | CZĘŚCIOWO | ~75% | Zakupy + alokacja, brak Emergency bundle/resupply |
| 7 Poziomy trudności | CZĘŚCIOWO | ~20% | Heurystyki statyczne; brak MCTS/adaptacji |
| 8 Logowanie decyzji | CZĘŚCIOWO | ~75% | Rozszerzone CSV (economy + commander), brak skip_reason/casualties |
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

**AI COMMANDER (ROZSZERZONY PODSTAWOWY):**
* ✅ Ruch (full + progresywny) z adaptacją MP
* ✅ Oportunistyczne capture + priorytety dla odłączonych KP
* ✅ Garrison limit + podstawowy stub rotacji
* ✅ Rozszerzone logi: path_len, path_used, progressive_used, decision_reason
* ❌ Brak pełnych zasad walki (risk gating)
* ❌ Brak resupply (pre_resupply placeholder)
* ❌ Brak retreat/reposition heurystyk
* ❌ Brak skip_reason w logu (diagnoza stagnacji utrudniona)
* ❌ Brak pełnej rotacji garnizonów

### Znane ograniczenia (3.5)

**AI GENERAL:**
* Brak Monte Carlo Tree Search dla trudniejszych poziomów
* Brak machine learning adaptacji między grami  
* Brak opponent modeling
* Sztywne strategie bez dynamicznego dostrajania wag

**AI COMMANDER (KRYTYCZNE LUKI):**
* pre_resupply() placeholder – brak wydawania punktów
* Brak mechanizmu emergency (gwałtowny spadek own_units)
* Brak risk-based combat (cv_ratio / przewidywane straty) - **CZĘŚCIOWO:** System artylerii ogranicza spam
* Brak skip_reason w logach
* Brak purge martwych alokacji (budżet mrożony w sektorach 0 units)

**SYSTEM BALANSOWANIA:**
* ✅ **Artyleria zbalansowana** - eliminacja dominacji przez ograniczenie strzałów
* ✅ **Dokumentacja kompletna** - przewodniki TOKEN i HEX balancing
* ❌ **Potrzebne dalsze testy** - wpływ na AI vs AI i długie kampanie
* ❌ **Brak reakcji AI** na nowy system (może wymagać dostrojenia heurystyk)

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

## 🧭 NASTĘPNE KROKI (PRIORYTETY TECHNICZNE – AKTUALNE 31.08.2025)

### **IMMEDIATE PRIORITIES – AI COMMANDER (NOWE PO SYSTEMIE ARTYLERII)**
1. **Testowanie wpływu systemu artylerii** na AI vs AI i długie kampanie
2. **Dostrojenie heurystyk AI** do nowego balansowania artylerii
3. Emergency Mode (own_units ≤ 8) – wymusza zakup pakietu: 2x P + 1x Z (+1x AL jeśli budżet pozwala)
4. Purge martwych alokacji – reset wag sektora po 2 turach z total_units==0
5. Resupply podstawowy – paliwo <30% → combat <50% (priorytet mobilne + supply chain)
6. Skip reason w logu (NO_PATH / ZERO_MP / GARRISON_HOLD / LOW_FUEL / BLOCKED)
7. **Analiza skuteczności** - czy AI kupuje różnorodnie po zbalansowaniu artylerii

### **MEDIUM TERM – SYSTEM BALANSOWANIA**
8. **Dodatkowe testy balansingu** - jednostki vs jednostki po ograniczeniu artylerii
9. **Rozszerzenie systemu** na inne OP jednostki jeśli zostaną zidentyfikowane
10. **Fine-tuning kosztów** w balance.model jeśli artyleria stanie się za słaba
11. MCTS po stabilizacji taktyki – lookahead 3–5 tur
12. Poziomy trudności – parametryzacja wag (agresja, supply bias, cv_threshold)

### **LONG TERM – ADVANCED AI / KOORDYNACJA**
13. Machine Learning (pamięć serii) – meta‑statystyki skuteczności
14. Feedback loop General↔Commander – adaptacja alokacji wg efektywności ruchów
15. Commander specialization – profile agresywny / defensywny / mobilny
16. **Rozszerzenie systemu ograniczeń** na inne aspekty rozgrywki jeśli potrzebne

## � CHANGELOG
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
* VisionService.calculate_detection_level() - krzya nieliniowa detekcji
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
3. Włącz AI dla Niemiec (generał + dowódcy), zagraj 5 tur.
4. **NOWE:** Obserwuj czy artyleria AI respektuje ograniczenia (max 1+1 atak/turę).
5. Zapisz turę spadku own_units ≤ 10 (log `ai_actions_*.csv`).
6. Notuj gdzie brak ruchu – przyda się do skip_reason.
7. **Test systemu artylerii:** `python tests/test_artillery_shot_limits.py`

## 🧪 METRYKI DO DODANIA
| Metryka | Cel | Wykorzystanie |
|---------|-----|---------------|
| casualties_turn | tracking attrition | wyzwalacz Emergency Mode |
| new_units_turn | tempo odtwarzania | ocena skuteczności pakietów |
| effective_move_rate | aktywność taktyczna | wykrycie stagnacji |
| skip_reason | diagn. stagnacji | tuning heurystyk ruchu |
| econ_efficiency | wydatkowanie budżetu | ocena alokacji Generała |
| **artillery_shots_used** | **monitorowanie artylerii** | **weryfikacja systemu ograniczeń** |
| **attack_success_rate** | **skuteczność ataków** | **ocena wpływu ograniczeń artylerii** |

## 🧼 PLAN ROZSZERZENIA CZYSZCZENIA
Aktualnie: quick_clean() usuwa tylko `nowe_dla_*`; full_clean() dodatkowo logi. NIE usuwa `assets/tokens/aktualne/` ani `saves/after_deployment.json`.
Plan: dodać `clean_deployed_tokens()` + wywołać w full_clean (opcjonalna flaga zachowania).

## 🔍 DIAGNOSTYKA PO SESJI
| Pytanie | Gdzie patrzeć | Oczekiwane |
|---------|---------------|------------|
| **Czy system artylerii działa?** | **actions CSV artillery_shots kolumna** | **≤ 2 ataki/turę per jednostka artylerii** |
| Czy attrition stabilne? | ai_actions own_units | Brak gwałtownych spadków <50%/3 tury |
| Czy budżet nie stoi? | econ_after vs econ_before | Spadek >50% przy COMBO |
| Czy ruch aktywny? | turn_summary moved_units | ≥70% wczesnych tur |
| (po wdrożeniu) skip_reason pełny? | actions CSV | <10% pustych |
| **Czy AI adaptuje się do systemu?** | **ai_actions attack patterns** | **Różnorodność celów, mniej arty spam** |

---

## 📚 META
Dokument przygotowuje grunt pod implementację gracza komputerowego bez refaktoryzacji istniejących modułów. Zmiany w silniku ograniczyć do dodania (jeśli brak) jednolitego API zakupów. **Nowy system ograniczenia artylerii pokazuje skuteczne podejście do balansowania bez breaking changes.**

Wersja: 3.5 (31 sierpnia 2025)
Status: **System artylerii zaimplementowany i przetestowany** (Generał ekonomia + taktyczne usprawnienia + balans artylerii)
Autor aktualizacji: automatyczny asystent + analiza logów + implementacja systemu balansowania

**Najważniejsze osiągnięcia wersji 3.5:**
- ✅ Pełny system ograniczenia strzałów artylerii 
- ✅ Elimianacja dominacji "arty spam"
- ✅ Zachowanie użyteczności artylerii przy zwiększeniu tactical depth
- ✅ Dokumentacja i testy komprehensywne
- ✅ Wsteczna kompatybilność z istniejącymi save'ami

---

*Koniec dokumentu.*
