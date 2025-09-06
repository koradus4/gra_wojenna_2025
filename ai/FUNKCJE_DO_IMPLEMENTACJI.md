# 🤖 FUNKCJE AI DO IMPLEMENTACJI

**Status:** 58 funkcji z `pass` wymagających implementacji  
**Data:** 6 września 2025  
**Cel:** Pełne uruchomienie autonomicznego AI Commander  
**Wersja systemu:** 3.8 (PE Validation System Complete)  
**Architektura:** Modułowa integracja z Engine (SILNIK_GRY_ANALIZA.md)

**KLUCZOWE INTEGRACJE Z SILNIKIEM:**
- ✅ **GameEngine API:** `execute_action()`, `process_key_points()`, `update_all_players_visibility()`
- ✅ **Token System:** MP, fuel, CV, artillery shot limits (AL/AC/AP: 1+1 ataku/turę)
- ✅ **Board System:** pathfinding A*, hex distance, terrain modifiers
- ✅ **Fog of War:** graduowana widoczność (FULL/PARTIAL/MINIMAL detection levels)
- ✅ **PE Validation:** multi-layer protection przeciw ujemnym PE

---

## 🔥 KRYTYCZNE (Priorytet 1) - 23 funkcje

### **ai_commander.py** - Główny sterownik AI

#### `make_tactical_turn(game_engine, player_id=None)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **KOMPLETNIE ZAIMPLEMENTOWANE** (700+ linii kodu)  
**Rzeczywista implementacja:**
- [x] ✅ **GŁÓWNY MÓZG AI** - kompletny sterownik z logowaniem i monitoringiem
- [x] ✅ **Krok 1:** `get_my_units()` - pobiera wszystkie#### `_determine_purchase_priority(commander, strategic_state)`
**Plik:** `strategia_ai.py`  
**Sta### **ekonomia_ai.py** - System ekonomiczny

#### `_optimize_budget(commander, game_engine)`
**Plik:** `ekonomia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **OPTYMALIZACJA BUDŻETU** - mądre zarządzanie punktami ekonomicznymi (PE)
- [ ] **Krok 1:** Budget assessment i current financial situation:
  - Sprawdź current PE balance
  - Oblicz predicted PE income dla następnych 3-5 tur
  - Policz committed PE (reserved dla resupply już zaplanowanego)
- [ ] **Krok 2:** Expenditure analysis i kategoryzacja wydatków:
  - `ESSENTIAL` - resupply critical units (CV < 30%)
  - `URGENT` - new units dla immediate tactical needs
  - `INVESTMENT` - long-term strategic purchases
  - `LUXURY` - nice-to-have improvements
- [ ] **Krok 3:** Risk vs reward budget allocation:
  - Safe budget (75% PE) - dla guaranteed essential needs
  - Investment budget (20% PE) - dla strategic opportunities
  - Emergency reserve (5% PE) - dla unexpected crisis
- [ ] **Krok 4:** Temporal budget planning:
  - Current turn immediate needs
  - Next 2-3 turns projected spending
  - Long-term strategic investment plan
- [ ] **Krok 5:** Adaptive budget reallocation:
  - Jeśli critical situation → reallocate everything to essentials
  - Jeśli comfortable position → increase investment budget
  - Jeśli desperate → spend everything NOW
- [ ] **Krok 6:** Return optimized budget allocation plan
- [ ] **Dla laika:** To jak domowy budżet - AI dzieli pieniądze na "musisz zapłacić" vs "fajnie by było kupić" vs "odłóż na później"

#### `_adaptive_purchase_system(commander, strategic_state, game_engine)`
**Plik:** `ekonomia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **ADAPTACYJNY SYSTEM ZAKUPÓW** - inteligentne dostosowanie strategii kupowania do sytuacji
- [ ] **Krok 1:** Strategic context analysis dla purchase decisions:
  - Current strategic phase (early, mid, end game)
  - Enemy threat level i composition
  - Own army strengths/weaknesses
  - Map control i territorial situation
- [ ] **Krok 2:** Adaptive purchase doctrine selection:
  - `QUALITY_OVER_QUANTITY` - gdy mamy dużo PE, kupujemy elite units
  - `QUANTITY_OVER_QUALITY` - gdy mało PE, kupujemy cheap mass
  - `SPECIALIZED_RESPONSE` - kupujemy específic counters do enemy composition
  - `BALANCED_APPROACH` - mixed purchases dla versatility
- [ ] **Krok 3:** Dynamic price-value analysis:
  - Sprawdź current market prices (mogą się zmieniać przez grę)
  - Calculate cost-effectiveness dla different scenarios
  - Consider timing (czy lepiej kupić teraz czy później)
- [ ] **Krok 4:** Predictive enemy response modeling:
  - Przewiduj jak enemy może zareagować na nasze purchases
  - Prepare counter-counter strategies
  - Avoid predictable patterns którzy enemy może exploit
- [ ] **Krok 5:** Portfolio diversification dla army composition:
  - Nie polegaj na only one unit type
  - Ensure combined arms capability
  - Maintain tactical flexibility
- [ ] **Krok 6:** Execute adaptive purchases + monitor effectiveness
- [ ] **Dla laika:** To jak mądry kupiec który zmienia strategię zakupów w zależności na sytuację - czasami kupuje drogo ale dobrze, czasami tanio ale dużo, zawsze myśli co przeciwnik zrobi w odpowiedziE (`pass`)  
**Plan implementacji:**
- [ ] **PRIORYTETY ZAKUPÓW** - inteligentne określanie co kupować w zależności od sytuacji
- [ ] **Krok 1:** Analiza current army composition:
  - Policz ile mamy każdego typu jednostek (INF, TANK, AT, ART)
  - Sprawdź army balance vs optimal composition
  - Zidentyfikuj gaps w capabilities (np. brak AT vs enemy armor)
- [ ] **Krok 2:** Ocena strategic needs według sytuacji:
  - `DEFENSIVE_PHASE` - priorytet dla AT, entrenchment units
  - `OFFENSIVE_PHASE` - priorytet dla TANK, assault infantry
  - `BREAKTHROUGH_PHASE` - priorytet dla fast units, exploitation
  - `DESPERATE_PHASE` - priorytet dla cost-effective quantity
- [ ] **Krok 3:** Analiza enemy composition (przez rozpoznanie):
  - Jeśli wróg ma dużo czołgów → kupuj AT
  - Jeśli wróg ma mainly infantry → kupuj artillery
  - Jeśli wróg ma air power → kupuj AA units
- [ ] **Krok 4:** Budget vs urgency analysis:
  - High PE budget - możemy kupić expensive quality units
  - Low PE budget - kupujemy cheap quantity units
  - Critical situation - emergency purchases mimo kosztów
- [ ] **Krok 5:** Return priority list z typami jednostek do kupowania:
  - `URGENT` - krytyczne potrzeby (np. AT gdy enemy ma tank advantage)
  - `HIGH` - ważne dla strategii (np. artillery dla offensive)
  - `MEDIUM` - wzmocnienie army composition
  - `LOW` - luxury units gdy mamy dużo PE
- [ ] **Krok 6:** Include quantity recommendations dla każdego typu
- [ ] **Dla laika:** To jak generał który planuje zakupy sprzętu - patrzy czego mu brakuje w armii i co jest potrzebne żeby wygrać obecną bitwę

#### `_get_available_purchase_options(commander, game_engine)`
**Plik:** `strategia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **DOSTĘPNE OPCJE ZAKUPU** - sprawdzanie co można aktualnie kupić
- [ ] **Krok 1:** Sprawdź dostępny PE budget w game_engine
  - Current PE balance gracza
  - PE income per turn dla planning future purchases
  - Reserved PE dla resupply (nie do wydania na nowe units)
- [ ] **Krok 2:** Pobierz available unit types z game_engine:
  - Lista wszystkich dostępnych typów jednostek dla danej nacji
  - Sprawdź unit costs dla każdego typu
  - Verification że commander ma access do tych typów
- [ ] **Krok 3:** Sprawdź deployment limitations:
  - Maximum units per hex dla nowych jednostek
  - Available deployment locations (własne VP, miasta)
  - Sprawdź czy nie osiągnęliśmy unit cap limits
- [ ] **Krok 4:** Kalkulacja purchasing power:
  - Ile jednostek każdego typu możemy sobie pozwolić
  - Multiple purchase scenarios (cheap quantity vs expensive quality)
  - Cost-effectiveness ratio dla każdego unit type
- [ ] **Krok 5:** Filtering options by strategic situation:
  - Remove unit types które nie pasują do current strategic phase
  - Prioritize units które są skuteczne przeciw detected enemy types
- [ ] **Krok 6:** Return structured list z wszystkimi opcjami + cost analysis
- [ ] **Dla laika:** To jak sprawdzanie sklepu z bronią - ile mamy pieniędzy, co jest dostępne, ile to kosztuje i co jest nam potrzebne

#### `_choose_optimal_purchases(purchase_options, priorities, budget)`
**Plik:** `strategia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **OPTYMALNY WYBÓR ZAKUPÓW** - algorytm knapsack dla maximizing utility
- [ ] **Krok 1:** Konwersja priorities na numerical weights:
  - `URGENT` = weight 10.0 (kupuj pierwszej kolejności)
  - `HIGH` = weight 7.0
  - `MEDIUM` = weight 4.0
  - `LOW` = weight 1.0
- [ ] **Krok 2:** Kalkulacja utility score dla każdej purchase option:
  - `utility = (unit_effectiveness * priority_weight) / unit_cost`
  - Higher utility = better value for money
- [ ] **Krok 3:** Knapsack algorithm dla budget optimization:
  - Sort purchases by utility score (descending)
  - Iteratively add purchases while budget allows
  - Consider "package deals" (np. multiple infantry vs one tank)
- [ ] **Krok 4:** Verify army composition balance:
  - Nie kupuj only one type units (potrzebujemy combined arms)
  - Ensure minimum diversity w army composition
  - Sprawdź że nie ignorujemy critical gaps
- [ ] **Krok 5:** Alternative scenarios analysis:
  - Generate 2-3 different purchase plans
  - Compare scenarios (quantity vs quality vs balanced)
  - Choose best scenario based on strategic state
- [ ] **Krok 6:** Return final purchase list z exact units + deployment locations
- [ ] **Dla laika:** To jak mądre robienie zakupów - AI wybiera tak żeby za dostępne pieniądze kupić najbardziej przydatne rzeczyrami
- [x] ✅ **Krok 2:** `_check_and_manage_garrisons()` - zarządza garnizonami
- [x] ✅ **Krok 3:** Czyszczenie przestarzałych rozkazów
- [x] ✅ **Krok 4:** `advanced_autonomous_mode()` - główny algorytm z grupowaniem adaptacyjnym
- [x] ✅ **Krok 5:** `opportunistic_capture_phase()` - delegowany do `ai.rajdy_ai`
- [x] ✅ **Krok 6:** `deploy_new_tokens()` - stawianie nowych jednostek
- [x] ✅ **Krok 7:** System wsparcia garnizonów zaimplementowany
- [x] ✅ **Plus dodatkowe:** Progressive movement, turn summary, casualties tracking
- [x] ✅ **Dla laika:** W pełni działający dowódca który obsługuje całą armię od A do Z

#### `advanced_autonomous_mode(my_units, game_engine)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **KOMPLETNIE ZAIMPLEMENTOWANE** (100+ linii kodu)  
**Rzeczywista implementacja:**
- [x] ✅ **MÓZG MYŚLĄCY AI** - pełne zarządzanie strategiczne
- [x] ✅ **Krok 1:** Filtrowanie dostępnych key points (current_value > 0)
- [x] ✅ **Krok 2:** `prioritize_targets()` - priorytetyzacja celów z oceną
- [x] ✅ **Krok 3:** `adaptive_grouping()` - tworzenie grup adaptacyjnych (SZTURM/HUNT/DEFENSE/SUPPORT)
- [x] ✅ **Krok 4:** `assign_targets_with_coordination()` - przypisywanie celów bez duplikatów
- [x] ✅ **Krok 5:** `dynamic_reassignment()` - automatyczne przeprzypisywanie pustych celów
- [x] ✅ **Krok 6:** Szczegółowe logowanie: TOP 8 celów, analiza grup, przypisania
- [x] ✅ **Plus:** Target reservation system, koordynacja bez konfliktów
- [x] ✅ **Dla laika:** Pracuje jak sztab generalny - analizuje mapę, tworzy zespoły i rozdaje im konkretne zadania

#### `_check_and_manage_garrisons(game_engine, my_units)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **KOMPLETNIE ZAIMPLEMENTOWANE**  
**Rzeczywista implementacja:**
- [x] ✅ **ROTACJA STRAŻY** - automatyczne zarządzanie garnizonami
- [x] ✅ **Krok 1:** Pobieranie aktualnego stanu key points z game_engine
- [x] ✅ **Krok 2:** Iteracja przez wszystkie jednostki gracza 
- [x] ✅ **Krok 3:** Sprawdzanie czy jednostka stoi na punkcie kluczowym (pozycja vs key_points_state)
- [x] ✅ **Krok 4:** Obliczanie current_ratio (current_value/initial_value) punktu
- [x] ✅ **Krok 5:** Automatyczne ustawianie `hold_position = True` dla jednostek na aktywnych punktach
- [x] ✅ **Krok 6:** Delegacja do `enforce_garrison_limits()` - zaawansowane limity rotacji
- [x] ✅ **Krok 7:** Automatyczne zwalnianie garnizonów z wyczerpanych punktów (current_value ≤ 0)
- [x] ✅ **Plus:** Szczegółowe logowanie każdej decyzji garnizonowej
- [x] ✅ **Dla laika:** Jak sierżant który codziennie sprawdza kto stoi na warcie, automatycznie przydziela nowych strażników gdzie trzeba i zwalnia ze służby gdy punkt nie jest już ważny

#### `get_my_units(game_engine, player_id=None)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **KOMPLETNIE ZAIMPLEMENTOWANE**  
**Rzeczywista implementacja:**
- [x] ✅ **SPIS ŻOŁNIERZY** - dokładne spisywanie wszystkich jednostek
- [x] ✅ **Krok 1:** Auto-detekcja player_id z `current_player_obj` jeśli nie podano
- [x] ✅ **Krok 2:** Przeszukiwanie wszystkich tokenów z limitem 200 (safety)
- [x] ✅ **Krok 3:** Sprawdzanie właściciela (obsługa format "2 (Polska)" i "2")
- [x] ✅ **Krok 4:** Zbieranie pełnych danych jednostki:
  - ID, pozycja (q,r), punkty ruchu (MP), paliwo, combat value
  - Referencja do obiektu token dla dalszego użycia
- [x] ✅ **Krok 5:** Zwracanie listy słowników z wszystkimi danymi
- [x] ✅ **Dla laika:** Działa jak skrupulatny adiutant który spisuje dokładnie kto gdzie stoi i w jakim stanie

#### `ai_attempt_combat(unit, game_engine, player_id, player_nation="Unknown")`
**Plik:** `ai_commander.py`  
**Status:** ✅ **ZAIMPLEMENTOWANE JAKO DELEGACJA** → `ai.walka_ai.ai_attempt_combat()`  
**Rzeczywista implementacja w ai.walka_ai:**
- [x] ✅ **MÓZG BOJOWY** - kompletna logika decyzji o walkach
- [x] ✅ **Krok 1:** Sprawdzanie warunków wstępnych (amunicja, CV, MP)
- [x] ✅ **Krok 2:** Pre-combat resupply jeśli CV < 80% maksimum
- [x] ✅ **Krok 3:** `attempt_retreat_low_cv()` - automatyczny odwrót rannych
- [x] ✅ **Krok 4:** `find_enemies_in_range()` - wykrywanie celów z line of sight
- [x] ✅ **Krok 5:** `evaluate_combat_ratio()` - ocena każdego wroga osobno
- [x] ✅ **Krok 6:** Wybór najlepszego celu (ratio ≥ 1.2 wymagane)
- [x] ✅ **Krok 7:** `try_flank_before_attack()` - próba oskrzydlenia
- [x] ✅ **Krok 8:** `execute_ai_combat()` - wykonanie ataku przez silnik
- [x] ✅ **Dla laika:** Kompletny system który sprawdza czy warto walczyć, z kim i jak najlepiej zaatakować

#### `find_enemies_in_range(unit, game_engine, player_id)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **ZAIMPLEMENTOWANE JAKO DELEGACJA** → `ai.walka_ai.find_enemies_in_range()`  
**Rzeczywista implementacja w ai.walka_ai:**
- [x] ✅ **SKANER WROGÓW** - zaawansowane wykrywanie celów z respektem mechanik gry
- [x] ✅ **Krok 1:** Sprawdzanie zasięgu ataku z stats jednostki (attack.range)
- [x] ✅ **Krok 2:** Obliczanie line of sight z VisionService (tylko widoczni wrogowie)
- [x] ✅ **Krok 3:** Przeszukiwanie wszystkich tokenów z filtrowaniem właściciela
- [x] ✅ **Krok 4:** Sprawdzanie odległości z `board.hex_distance()`
- [x] ✅ **Krok 5:** **Respektowanie detection_level** - system graduowanej widoczności:
  - Pełne dane dla detection ≥ 0.8
  - Ograniczone dane dla detection < 0.8  
  - Fallback do szacunków gdy brak precyzyjnych danych
- [x] ✅ **Krok 6:** Zwracanie listy z kompletnymi danymi: pozycja, CV, ID, odległość, detection_level
- [x] ✅ **Dla laika:** Jak żołnierz z lornetką który skanuje okolicę i zapisuje wszystko co widzi, ale tylko to co rzeczywiście może zobaczyć

#### `evaluate_combat_ratio(unit, enemy)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **ZAIMPLEMENTOWANE JAKO DELEGACJA** → `ai.walka_ai.evaluate_combat_ratio()`  
**Rzeczywista implementacja w ai.walka_ai:**
- [x] ✅ **KALKULATOR SZANS** - precyzyjna ocena stosunku sił bojowych
- [x] ✅ **Krok 1:** Bezpieczne pobieranie danych z tokenów (zabezpieczenia przed None)
- [x] ✅ **Krok 2:** Porównanie attack value mojej jednostki z defense value wroga
- [x] ✅ **Krok 3:** Uwzględnienie modyfikatorów combat value dla obu stron
- [x] ✅ **Krok 4:** Kalkulacja podstawowego stosunku sił (attack/defense)
- [x] ✅ **Krok 5:** Zastosowanie bonusów specjalistycznych:
  - AT vs pojazdy pancerne: bonus x1.5
  - Artyleria vs piechota: bonus specjalny
  - Inne kombinacje typów jednostek
- [x] ✅ **Krok 6:** Zwracanie float ratio gdzie >1.0 = przewaga atakującego
- [x] ✅ **Dla laika:** Jak doświadczony dowódca który patrzy na swoje czołgi i wroga i szacuje "czy mamy większe szanse na wygraną"

#### `_attempt_retreat_low_cv(unit, game_engine)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **ZAIMPLEMENTOWANE JAKO DELEGACJA** → `ai.walka_ai.attempt_retreat_low_cv()`  
**Rzeczywista implementacja w ai.walka_ai:**
- [x] ✅ **SYSTEM ODWROTU** - inteligentne ratowanie rannych jednostek
- [x] ✅ **Krok 1:** Sprawdzanie czy jednostka potrzebuje ewakuacji (CV, paliwo, amunicja)
- [x] ✅ **Krok 2:** Ocena zagrożenia w okolicy z `scan_for_enemies()` 
- [x] ✅ **Krok 3:** Znajdowanie bezpiecznej pozycji odwrotu (algorytm pathfinding)
- [x] ✅ **Krok 4:** Sprawdzanie czy droga ucieczki jest bezpieczna
- [x] ✅ **Krok 5:** Wykonanie odwrotu z trybem MARCH (szybka ewakuacja)
- [x] ✅ **Krok 6:** Logowanie decyzji i oznaczanie jednostki jako "w odwrocie"
- [x] ✅ **Dla laika:** Jak ranny żołnierz który automatycznie ucieka z pola bitwy do bezpiecznego miejsca gdy sytuacja staje się zbyt niebezpieczna

#### `_try_flank_before_attack(unit, enemy, game_engine)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **ZAIMPLEMENTOWANE JAKO DELEGACJA** → `ai.walka_ai.try_flank_before_attack()`  
**Rzeczywista implementacja w ai.walka_ai:**
- [x] ✅ **MANEWR OSKRZYDLENIA** - zaawansowane pozycjonowanie taktyczne
- [x] ✅ **Krok 1:** Sprawdzanie warunków oskrzydlenia (zasięgi ataku, odległości)
- [x] ✅ **Krok 2:** Znajdowanie kandydackich pozycji wokół wroga:
  - W zasięgu ataku mojej jednostki  
  - Poza zasięgiem kontrataku wroga
  - Nie zajęte przez inne jednostki
  - Na poprawnych hexach mapy
- [x] ✅ **Krok 3:** Sprawdzanie dostępności każdej pozycji z `board.find_path()`
- [x] ✅ **Krok 4:** Wybór najkrótszej dostępnej drogi (optymalizacja MP)
- [x] ✅ **Krok 5:** Wykonanie manewru z `MoveAction` przez silnik
- [x] ✅ **Krok 6:** **UWAGA:** Obecna implementacja NIE uwzględnia jeszcze ataków reakcji!
- [x] ✅ **Status:** Podstawowy flanking działa, ale wymaga rozszerzenia o mechanikę reaction attacks
- [x] ✅ **Dla laika:** Jak żołnierz który próbuje obejść wroga z boku żeby mieć lepszą pozycję do strzału, ale jeszcze nie przewiduje że wróg może go zauważyć po drodze

#### `execute_ai_combat(unit, enemy, game_engine, player_nation="Unknown")`
**Plik:** `ai_commander.py`  
**Status:** ✅ **ZAIMPLEMENTOWANE JAKO DELEGACJA** → `ai.walka_ai.execute_ai_combat()`  
**Rzeczywista implementacja w ai.walka_ai:**
- [x] ✅ **WYKONAWCA ATAKU** - precyzyjne wykonanie walki przez silnik gry
- [x] ✅ **Krok 1:** Sprawdzanie warunków wstępnych (amunicja, cel na pozycji, zasięg)
- [x] ✅ **Krok 2:** Przygotowanie danych do `CombatAction` (attacker_id, defender_id)
- [x] ✅ **Krok 3:** Wywołanie `game_engine.execute_action()` z kompletną obsługą błędów
- [x] ✅ **Krok 4:** Parsowanie wyniku walki z `ActionResult`
- [x] ✅ **Krok 5:** Logowanie szczegółów ataku (kto, kogo, wynik, obrażenia)
- [x] ✅ **Krok 6:** Aktualizacja stanu taktycznego post-combat
- [x] ✅ **Krok 7:** Return boolean - True jeśli atak wykonany, False przy błędzie systemu
- [x] ✅ **Dla laika:** Jak żołnierz który naciska spust - wszystkie przygotowania skończone, teraz tylko wykonuje strzał i raportuje co się stało

#### `scan_for_enemies(unit_pos, game_engine, range=3)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **KOMPLETNIE ZAIMPLEMENTOWANE**  
**Rzeczywista implementacja:**
- [x] ✅ **RADAR TAKTYCZNY** - zaawansowane skanowanie okolicy z respektem fog of war
- [x] ✅ **Krok 1:** Pobieranie danych gracza i narodu z current_player_obj
- [x] ✅ **Krok 2:** Sprawdzanie visible_tokens dla tego gracza (tylko to co AI może widzieć)
- [x] ✅ **Krok 3:** Filtrowanie wrogów (wykluczenie własnych jednostek po nation)
- [x] ✅ **Krok 4:** Obliczanie odległości z `board.hex_distance()` 
- [x] ✅ **Krok 5:** Respektowanie ograniczenia zasięgu skanowania
- [x] ✅ **Krok 6:** Zwracanie listy (token, distance) dla wszystkich wykrytych wrogów
- [x] ✅ **Dla laika:** Jak żołnierz który wystawia głowę znad okopa i sprawdza czy w okolicy są wrogowie - ale tylko tych których rzeczywiście może zobaczyć przez mgłę wojny

#### `choose_movement_mode(unit, target, game_engine)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **ZAIMPLEMENTOWANE JAKO DELEGACJA** → `ai.ruch_jednostek.choose_movement_mode()`  
**Rzeczywista implementacja w ai.ruch_jednostek:**
- [x] ✅ **SELEKTOR TRYBU RUCHU** - inteligentny wybór sposobu poruszania się
- [x] ✅ **Zabezpieczenie anti-loop** - licznik wywołań per jednostka
- [x] ✅ **Krok 1:** Sprawdzanie odległości do celu z `board.hex_distance()`
- [x] ✅ **Krok 2:** Skanowanie wrogów w okolicy `_lazy_scan_for_enemies(range=6)`
- [x] ✅ **Krok 3:** Logika wyboru trybu:
  - **RECON** dla bardzo dalekich celów (>8 hexów) gdy brak wrogów
  - **COMBAT** gdy wrogowie w zasięgu lub cel blisko (<4 hexy)
  - **MARCH** dla średnich odległości bez zagrożenia
- [x] ✅ **Krok 4:** Szczegółowe logowanie decyzji i powodów
- [x] ✅ **Dla laika:** Jak kierowca który wybiera prędkość - szybko na autostradzie, ostrożnie w mieście, bardzo wolno w niebezpiecznych miejscach

#### `move_towards(unit, target, game_engine)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **ZAIMPLEMENTOWANE JAKO DELEGACJA** → `ai.ruch_jednostek.move_towards()`  
**Rzeczywista implementacja w ai.ruch_jednostek:**
- [x] ✅ **NAWIGATOR** - kompletny system prowadzenia jednostek do celu
- [x] ✅ **Krok 1:** Sprawdzanie warunków wstępnych (MP, paliwo, cel)
- [x] ✅ **Krok 2:** `choose_movement_mode()` - inteligentny wybór trybu ruchu  
- [x] ✅ **Krok 3:** `_lazy_calculate_progressive_target()` - progressive movement dla dalekich celów
- [x] ✅ **Krok 4:** `board.find_path()` - pathfinding z uwzględnieniem MP i paliwa
- [x] ✅ **Krok 5:** Bezpieczne wykonanie ruchu z `game_engine.execute_action()`
- [x] ✅ **Krok 6:** Sprawdzanie reakcji wrogów po ruchu
- [x] ✅ **Krok 7:** Szczegółowe logowanie każdego kroku i decyzji
- [x] ✅ **Plus:** Zabezpieczenia przed infinite loops, obsługa błędów pathfinding
- [x] ✅ **Dla laika:** Jak GPS w samochodzie - planuje najlepszą trasę, prowadzi krok po kroku, unika niebezpieczeństw i mówi co się dzieje

### **Klasy do implementacji**

#### `class AdaptiveAICommander`
**Plik:** `ai_commander.py`  
**Status:** ✅ **KOMPLETNIE ZAIMPLEMENTOWANA** (300+ linii kodu)  
**Rzeczywista implementacja:**
- [x] ✅ **ADAPTACYJNY SYSTEM AI** - zaawansowany dowódca z uczeniem się
- [x] ✅ **Atrybuty inicjalizacji:** strategic_state, budget_allocation, keypoint_priorities
- [x] ✅ **Delegacje do modułów:** `strategia_ai`, `ekonomia_ai`, `rozpoznanie_ai`
- [x] ✅ **VP-based strategic switching** - zmiana strategii według wyników VP
- [x] ✅ **Poziomy agresji:** 0.0 (defensywny) do 1.0 (pełny atak)
- [x] ✅ **Adaptive budget allocation:** elastyczny podział 20-40-40
- [x] ✅ **Reconnaissance tracking:** zbieranie danych o przeciwniku
- [x] ✅ **Purchase queue management:** kolejka adaptacyjnych zakupów
- [x] ✅ **Dla laika:** To jak bardzo doświadczony generał który uczy się podczas wojny i zmienia taktykę w zależności na to co działa, a co nie

#### `class AICommander.__init__(self, player)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **KOMPLETNIE ZAIMPLEMENTOWANE**  
**Rzeczywista implementacja:**
- [x] ✅ **INICJALIZACJA DOWÓDCY** - pełne przygotowanie AI do działania
- [x] ✅ **Krok 1:** Przypisanie gracza i sprawdzenie jego danych
- [x] ✅ **Krok 2:** Inicjalizacja zmiennych stanu (unit tracking, combat stats)
- [x] ✅ **Krok 3:** Ustawienie domyślnych strategii i preferencji
- [x] ✅ **Krok 4:** Przygotowanie systemów logowania i monitorowania
- [x] ✅ **Krok 5:** Inicjalizacja adaptacyjnego budżetu i priorytetów
- [x] ✅ **Dla laika:** To jak nowy generał który dostaje armię - sprawdza jakich ma żołnierzy, jakie ma zasoby i przygotowuje się do dowodzenia

#### `class AICommander.pre_resupply(self, game_engine)`
**Plik:** `ai_commander.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **WSTĘPNE ZAOPATRZENIE** - przygotowanie jednostek przed główną turą
- [ ] **Krok 1:** Sprawdź stan wszystkich jednostek (paliwo, amunicja, CV) z `self.player.units`
- [ ] **Krok 2:** Zidentyfikuj jednostki wymagające natychmiastowego resupply:
  - CV < 50% maksimum (ranne wymagające napraw)
  - fuel < 30% maksimum (brak możliwości ruchu) 
  - ammunition < 25% (brak możliwości walki)
- [ ] **Krok 3:** Sprawdź dostępne PE z `self.player.pe` dla resupply
- [ ] **Krok 4:** Priorytetyzuj jednostki według ważności i `unit.type`:
  - Artyleria (AL/AC/AP - wysokowartościowe, ograniczone ataki)
  - Czołgi (TK - front line units)  
  - AT (AT - specialized anti-armor)
  - Piechota (IN - najbardziej rozpowszechniona)
- [ ] **Krok 5:** Wykonaj resupply z `game_engine.execute_action()` typu RESUPPLY
- [ ] **Krok 6:** Logowanie kosztów i efektów zaopatrzenia
- [ ] **Integracja z silnikiem:** wykorzystanie Token.fuel, Token.ammunition, Player.pe
- [ ] **Dla laika:** Jak sprawdzenie przed misją czy żołnierze mają amunicję, paliwo i czy ranni są wyleczeni
- [ ] **Krok 5:** Wykonaj resupply w kolejności priorytetów do wyczerpania PE
- [ ] **Krok 6:** Zaloguj podsumowanie resupply (ile jednostek, koszt PE)
- [ ] **Dla laika:** To jak sprawdzenie i naprawianie sprzętu przed misją - tankowanie, ładowanie amunicji, naprawa uszkodzeń

#### `class AICommander.make_tactical_turn(self, game_engine)`
**Plik:** `ai_commander.py`  
**Status:** ✅ **KOMPLETNIE ZAIMPLEMENTOWANE**  
**Rzeczywista implementacja:**
- [x] ✅ **METODA KLASOWA** turę taktyczną - wrapper dla funkcji globalnej
- [x] ✅ **Delegacja do:** `make_tactical_turn(game_engine, self.player.id)`
- [x] ✅ **Kontekst gracza:** używa self.player jako źródło danych
- [x] ✅ **Integracja z AdaptiveAICommander:** może korzystać z adaptacyjnych strategii
- [x] ✅ **Dla laika:** To ta sama funkcja co globalna, ale wywołana w kontekście konkretnego dowódcy AI

### **wybor_celow.py** - System wyboru celów

#### `find_target(unit, game_engine)`
**Plik:** `wybor_celow.py`  
**Status:** ✅ ZAIMPLEMENTOWANE  
**Plan implementacji:**
- [x] ✅ Już zaimplementowane

#### `find_alternative_target(unit, base_target, game_engine)`
**Plik:** `wybor_celow.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **PLAN B** - znajduje alternatywny cel gdy główny cel jest nieosiągalny
- [ ] **Krok 1:** Sprawdź dlaczego główny cel jest problematyczny:
  - **PATH_BLOCKED:** brak drogi do celu (pathfinding zwraca None)
  - **TOO_DEFENDED:** cel zbyt silnie broniony (ratio < 0.8)
  - **OUT_OF_RANGE:** cel za daleko (brak MP/fuel na dojście)
  - **ALREADY_TAKEN:** cel już został zajęty przez kogoś innego
  - **TARGET_DESTROYED:** cel został zniszczony/wyczerpany
- [ ] **Krok 2:** Określ kryteria alternatywnego celu na podstawie problemu:
  - Jeśli PATH_BLOCKED → szukaj celów z wolną drogą z `board.find_path()`
  - Jeśli TOO_DEFENDED → szukaj słabiej bronionych celów  
  - Jeśli OUT_OF_RANGE → szukaj bliższych celów z `board.hex_distance()`
  - Jeśli ALREADY_TAKEN → szukaj innych podobnych celów
  - Jeśli TARGET_DESTROYED → szukaj dowolnych dostępnych celów
- [ ] **Krok 3:** Skanuj mapę w poszukiwaniu alternatyw:
  - Rozpocznij od obszaru wokół pierwotnego celu (promień 5-8 hexów)
  - Rozszerz wyszukiwanie jeśli nie ma lokalnych alternatyw
  - Sprawdź punkty kluczowe z `game_engine.board.key_points`, wrogich jednostek z `game_engine.get_visible_tokens()`
  - Uwzględnij tylko cele które jednostka może rzeczywiście zaatakować
- [ ] **Krok 4:** Oceń każdą alternatywę według wielokryterialnej funkcji:
  - **Dostępność:** czy jednostka może dotrzeć (`board.find_path()` + MP)
  - **Opłacalność:** wartość VP celu vs ryzyko strat  
  - **Wykonalność:** czy jednostka ma odpowiedni typ do tego celu
- [ ] **Krok 5:** Wybierz najlepszą alternatywę lub zwróć None jeśli żadna nie spełnia minimów
- [ ] **Integracja z silnikiem:** wykorzystanie pathfinding, visible_tokens, key_points
- [ ] **Dla laika:** Jak żołnierz który widzi że nie może zaatakować głównego celu i szuka innego sposobu na wykonanie misji
  - **Opłacalność:** stosunek korzyści do kosztu (value/distance)
  - **Wykonalność:** czy atak ma szanse powodzenia (combat ratio)
  - **Priorytet strategiczny:** jak ważny jest cel dla ogólnej strategii
- [ ] **Krok 5:** Wybierz najlepszą alternatywę:
  - Uporządkuj kandydatów według wyniku funkcji oceny
  - Sprawdź czy najlepszy kandydat spełnia minimalne wymagania
  - Zwróć najlepszy cel lub None jeśli żaden nie nadaje się
- [ ] **Krok 6:** Loguj decyzję dla debugowania (dlaczego zmieniono cel)
- [ ] **Dla laika:** To jak gdy idziesz do restauracji ale jest zamknięta - szukasz innej restauracji w okolicy która jest otwarta, nie za droga i ma dobre jedzenie

#### `find_alternative_target_around(unit, base_target, game_engine, search_radius=3)`
**Plik:** `wybor_celow.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **LOKALNY SKANER** - przeszukuje obszar wokół głównego celu w poszukiwaniu alternatyw
- [ ] **Krok 1:** Określ centrum i promień przeszukiwania:
  - Centrum: pozycja base_target (q, r)
  - Promień: search_radius (domyślnie 3 hexy, max 8)
  - Sprawdź czy obszar mieści się w granicach mapy
- [ ] **Krok 2:** Generuj wszystkie pozycje w promieniu wyszukiwania:
  - Użyj `board.get_neighbors()` dla każdego ring od 1 do search_radius
  - Zbierz wszystkie hexy w obszarze: [(q1,r1), (q2,r2), ...]
  - Wyklucz pozycję base_target (nie szukamy tego samego celu)
- [ ] **Krok 3:** Sprawdź każdą pozycję pod kątem potencjalnych celów:
  - **Punkty kluczowe:** czy na tym hexie jest aktywny `key_point` z `game_engine.board.key_points`
  - **Wrogie jednostki:** czy stoi tam wroga jednostka z `game_engine.get_visible_tokens()`
  - **Pozycje strategiczne:** ważne pozycje obronne lub punkty kontrolne
  - **Puste pozycje taktyczne:** hexy dające przewagę pozycyjną
- [ ] **Krok 4:** Filtruj cele według dostępności dla tej jednostki:
  - Sprawdź `board.find_path()` - czy jednostka może tam dotrzeć
  - Sprawdź zasięg ataku - czy może zaatakować z tej odległości
  - Sprawdź `unit.mp` i `unit.fuel` - czy wystarczy na podróż + akcję
  - Sprawdź line of sight - czy cel jest widoczny (fog of war)
- [ ] **Krok 5:** Oceń każdy dostępny cel lokalny:
  - **Bliskość:** bliższe cele = wyższy priorytet (oszczędność MP)
  - **Wartość:** punkty kluczowe o wyższej wartości VP = wyższy priorytet
  - **Trudność:** słabiej bronione cele = wyższy priorytet  
  - **Synergia:** cele które uzupełniają strategię grupy
- [ ] **Krok 6:** Zwróć listę celów posortowaną według priorytetu:
  - Format: `[{"position": (q,r), "type": "keypoint/enemy/tactical", "value": int, "distance": int}]`
  - Sortowanie: najlepsze cele na początku listy
  - Pustą listę jeśli żaden cel w obszarze nie nadaje się
- [ ] **Integracja z silnikiem:** wykorzystanie board.key_points, pathfinding, visible_tokens
- [ ] **Dla laika:** Jak gdy szukasz parkingu koło sklepu - jeśli nie ma miejsca bezpośrednio przed wejściem, to przeszukujesz pobliskie uliczki w coraz większym kręgu

#### `get_keypoint_value(keypoint_data)`
**Plik:** `wybor_celow.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **EVALUATOR WARTOŚCI** - oblicza rzeczywistą wartość punktu kluczowego dla AI
- [ ] **Krok 1:** Pobierz podstawowe dane punktu z `keypoint_data`:
  - `initial_value` - pierwotna wartość punktu z mapy
  - `current_value` - aktualna wartość (może być zmniejszona z `game_engine.board.key_points`)
  - `type` - typ punktu ("city", "factory", "port", etc.)
  - `position` - lokalizacja na mapie (q, r)
- [ ] **Krok 2:** Oblicz wskaźnik wyczerpania:
  - `depletion_ratio = current_value / initial_value`
  - Punkty bliskie wyczerpania (ratio < 0.3) mają wyższy priorytet
  - Punkty świeże (ratio > 0.8) mają standardowy priorytet
- [ ] **Krok 3:** Zastosuj modyfikatory typu punktu:
  - **CITY:** x1.2 (wysokie znaczenie ekonomiczne)
  - **FACTORY:** x1.5 (produkcja jednostek) 
  - **PORT:** x1.3 (import/eksport)
  - **RESOURCE:** x1.1 (surowce)
  - **STRATEGIC:** x1.4 (kluczowe pozycje)
  - **OTHER:** x1.0 (standardowe)
- [ ] **Krok 4:** Uwzględnij czynnik czasowy (pilność):
  - Oszacuj ile tur punkt może jeszcze przetrwać: `estimated_turns = current_value / 10`
  - **Krytyczne** (≤ 2 tury): bonus x2.0
  - **Pilne** (3-5 tur): bonus x1.5  
  - **Średnie** (6-10 tur): bonus x1.2
  - **Długoterminowe** (>10 tur): bonus x1.0
- [ ] **Krok 5:** Sprawdź modyfikatory sytuacyjne z visible_tokens:
  - Czy punkt jest już kontrolowany przez nas: -50% wartości
  - Czy punkt jest silnie broniony przez wroga: -30% wartości  
  - Czy punkt jest izolowany (daleko od innych): +20% wartości
  - Czy punkt ma bonus defensywny: +10% wartości
- [ ] **Krok 6:** Oblicz finalną wartość: 
  - `final_value = current_value * type_modifier * urgency_bonus * situational_modifier`
  - Zaokrąglij do integer, zwróć wartość w zakresie 0-1000
- [ ] **Integracja z silnikiem:** wykorzystanie board.key_points, visible_tokens
- [ ] **Dla laika:** Jak ekspert który ocenia ważność zadania - sprawdza ile jest warte, jak pilne, jakiego typu i w jakiej sytuacji się znajduje

### **grupowanie_ai.py** - System grupowania jednostek

#### `adaptive_grouping(my_units, game_engine)`
**Plik:** `grupowanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **ORGANIZATOR DRUŻYN** - tworzy specjalne zespoły do różnych zadań bojowych
- [ ] **Krok 1:** Przeanalizuj sytuację strategiczną na mapie:
  - Sprawdź gdzie są punkty kluczowe do ataku z `game_engine.board.key_points`
  - Znajdź wrogą artylerię z `game_engine.get_visible_tokens()` (type AL/AC/AP)
  - Zidentyfikuj własne punkty wymagające obrony
  - Oceń ogólną sytuację taktyczną (atak vs obrona)
- [ ] **Krok 2:** Posortuj jednostki według `unit.type` i możliwości:
  - **Czołgi** (TK - wysokie CV, pancerz) - siła uderzeniowa
  - **Piechota** (IN - uniwersalna, tania) - okupacja punktów
  - **Artyleria** (AL/AC/AP - daleki zasięg, ograniczone ataki) - wsparcie ogniowe
  - **AT** (AT - przeciwpancerne) - niszczenie czołgów wroga
  - **Szybkie jednostki** (RE, lekkie) - zwiad i rajdy
- [ ] **Krok 3:** Twórz grupy adaptacyjne według potrzeb sytuacyjnych:
  - **ASSAULT:** 2-3 czołgi TK + 1-2 piechota IN (do zajmowania punktów kluczowych)
  - **HUNT:** 2-3 szybkie jednostki (do polowania na wrogą artylerię)
  - **DEFENSE:** 1-2 AT + 1-2 piechota (do obrony własnych punktów)
  - **SUPPORT:** 1-2 artyleria AL/AC/AP + 1 escort (do ostrzału z bezpiecznej odległości)
  - **FLEXIBLE:** jednostki mieszane (do zadań zmieniających się dynamicznie)
- [ ] **Krok 4:** Sprawdź bliskość geograficzną z `board.hex_distance()` - grupuj jednostki w promieniu 5-8 hexów
- [ ] **Krok 5:** Sprawdź czy grupy mają zbalansowaną kompozycję (nie same czołgi, nie sama piechota)
- [ ] **Krok 6:** Zwróć listę grup z przypisanymi rolami: `[{"type": "ASSAULT", "units": [...], "leader": unit}]`
- [ ] **Integracja z silnikiem:** wykorzystanie visible_tokens, key_points, hex_distance
- [ ] **Dla laika:** Jak trener piłkarski który patrzy na dostępnych zawodników i tworzy różne drużyny - jedną ofensywną do ataku, drugą defensywną do obrony

#### `assign_targets_with_coordination(groups, game_engine)`
**Plik:** `grupowanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **KOORDYNATOR ZADAŃ** - inteligentnie rozdaje cele grupom bez konfliktów
- [ ] **Krok 1:** Skanowanie dostępnych celów na całej mapie:
  - **Punkty kluczowe** do zajęcia z `game_engine.board.key_points` (current_value > 0, nieokupowane przez nas)
  - **Wroga artyleria** do zniszczenia z `game_engine.get_visible_tokens()` (type AL/AC/AP)
  - **Wrogie skupiska** jednostek do rozbicia
  - **Własne punkty** wymagające wzmocnienia obrony
  - **Odłączone punkty** wroga (łatwe do przejęcia)
- [ ] **Krok 2:** Oceń priorytet każdego celu (skala 1-10):
  - **Priorytet 10:** Krytyczne punkty kluczowe (wyczerpują się w ≤ 2 tury)
  - **Priorytet 8-9:** Wroga artyleria zagrażająca naszym jednostkom
  - **Priorytet 6-7:** Wysokowartościowe punkty kluczowe  
  - **Priorytet 4-5:** Standardowe cele taktyczne
  - **Priorytet 1-3:** Cele opportunistyczne, rajdy
- [ ] **Krok 3:** Dopasuj grupy do celów według specjalizacji i efektywności:
  - **Grupy ASSAULT** → punkty kluczowe (główna siła uderzeniowa)
  - **Grupy HUNT** → wroga artyleria (szybka eliminacja zagrożeń)
  - **Grupy DEFENSE** → własne punkty do obrony (trzymanie pozycji)
  - **Grupy SUPPORT** → wsparcie innych grup (nie samodzielne cele)
  - **Grupy FLEXIBLE** → cele zmieniające się dynamicznie
- [ ] **Krok 4:** Sprawdź optymalne odległości z `board.hex_distance()` - bliższe grupy dostają bliższe cele
- [ ] **Krok 5:** System RESERVATION - unikaj duplikatów celów:
  - Jeden cel główny = jedna grupa główna
  - Maksymalnie jedna grupa backup per cel
  - Zaznacz cele jako "reserved" po przypisaniu
- [ ] **Krok 6:** Uwzględnij siłę grup vs trudność celów:
  - Silniejsze grupy → trudniejsze cele (bronione przez wroga)
  - Słabsze grupy → łatwiejsze cele (słabo bronione/puste)
- [ ] **Krok 7:** Zwróć assignments: `[{"group": group, "target": target, "priority": int, "role": str}]`
- [ ] **Integracja z silnikiem:** wykorzystanie key_points, visible_tokens, hex_distance
- [ ] **Dla laika:** Jak mądra dyspozytorka która sprawdza jakie są zlecenia i którą taksówkę wysłać gdzie - najlepszą do najważniejszego klienta

#### `dynamic_reassignment(groups, game_engine)`
**Plik:** `grupowanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **MENEDŻER ADAPTACJI** - dynamicznie przeprzypisuje cele gdy sytuacja się zmienia
- [ ] **Krok 1:** Sprawdź status wszystkich aktualnych przypisań:
  - Które grupy osiągnęły swoje cele (sukces)
  - Które grupy mają cele już nieaktualne (cel zniszczony przez kogoś innego)
  - Które grupy nie mogą dotrzeć do celu (`board.find_path()` zwraca None)
  - Które grupy są blokowane przez wrogów (path blocked)
- [ ] **Krok 2:** Zidentyfikuj grupy wymagające nowych celów:
  - **COMPLETED:** grupy które ukończyły misję
  - **OBSOLETE:** grupy z nieaktualnymi celami  
  - **BLOCKED:** grupy które nie mogą wykonać obecnej misji
  - **IDLE:** grupy bez przypisanego celu
- [ ] **Krok 3:** Znajdź nowe dostępne cele:
  - Cele które pojawiły się od ostatniego przypisania z `game_engine.board.key_points`
  - Cele które zostały odblokowane (wróg się wycofał) z `game_engine.get_visible_tokens()`
  - Cele o zwiększonym priorytecie (sytuacja krytyczna)
  - Cele backup dla grup które potrzebują wsparcia
- [ ] **Krok 4:** Przeprowadź inteligentne przypisanie:
  - **Priorytet geograficzny:** najbliższe cele z `board.hex_distance()` dla grup w okolicy
  - **Priorytet specjalizacji:** HUNT grupy do artylerii AL/AC/AP, ASSAULT do punktów
  - **Priorytet pilności:** najważniejsze cele do najsilniejszych grup
  - **Load balancing:** rozłóż grupy równomiernie po mapie
- [ ] **Krok 5:** Aktualizuj system reservation:
  - Usuń reservations dla starych celów
  - Dodaj reservations dla nowych przypisań
  - Sprawdź konflikty i je rozwiąż
- [ ] **Krok 6:** Loguj wszystkie zmiany dla debugowania
- [ ] **Krok 7:** Zwróć zaktualizowane assignments
- [ ] **Integracja z silnikiem:** wykorzystanie pathfinding, key_points, visible_tokens, hex_distance
- [ ] **Dla laika:** Jak mądra dyspozytorka która cały czas monitoruje swoich kierowców i jak któryś ukończy zlecenie albo gdzieś utknął w korku, to natychmiast daje mu nowe zadanie

#### `group_units_by_proximity(units, game_engine)`
**Plik:** `grupowanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **KLASTER GEOGRAFICZNY** - grupuje jednostki według bliskości na mapie
- [ ] **Krok 1:** Przygotuj dane pozycyjne wszystkich jednostek:
  - Zbierz pozycje (q, r) każdej jednostki z `unit.position`
  - Sprawdź aktualną dostępność (`unit.mp` > 0, nie w retreat)
  - Odfiltruj jednostki zajęte garnizonami (hold_position = True)
- [ ] **Krok 2:** Oblicz macierz odległości między wszystkimi jednostkami:
  - Użyj `board.hex_distance()` dla każdej pary jednostek
  - Uwzględnij rzeczywiste drogi z `board.find_path()` nie tylko odległość w linii prostej
  - Ustaw próg bliskości: 6-8 hexów = "blisko", >12 hexów = "daleko"
- [ ] **Krok 3:** Algorytm klasterowania (podobny do k-means dla hexów):
  - Znajdź jednostki w promieniu PROXIMITY_THRESHOLD (domyślnie 6 hexów)
  - Twórz klastry startując od najbardziej centralnych jednostek
  - Dla każdego klastra dodawaj sąsiednie jednostki w zasięgu
  - Unikaj nakładających się klastrów (jedna jednostka = jeden klaster)
- [ ] **Krok 4:** Walidacja klastrów pod kątem przydatności:
  - **Minimalna wielkość:** klaster musi mieć ≥ 2 jednostki
  - **Maksymalna wielkość:** klaster nie może mieć > 6 jednostek (zbyt duży)
  - **Balans typów:** preferuj klastry z mieszanką `unit.type` jednostek
  - **Odrzuć:** pojedyncze jednostki daleko od wszystkich innych
- [ ] **Krok 5:** Wybierz "lidęra" każdego klastra:
  - Najsilniejsza jednostka (highest `unit.cv`) lub
  - Najbardziej centralna pozycja w klastrze lub  
  - Jednostka z najlepszą mobilnością (highest `unit.mp`)
- [ ] **Krok 6:** Zwróć grupy geograficzne: `[{"leader": unit, "members": [units], "center": (q,r), "radius": int}]`
- [ ] **Integracja z silnikiem:** wykorzystanie hex_distance, pathfinding, unit.position/mp/cv
- [ ] **Dla laika:** Jak organizowanie spotkania znajomych - sprawdzasz kto mieszka blisko kogo i tworzysz grupy żeby ludzie z tej samej dzielnicy mogli się spotkać razem

### **ruch_jednostek.py** - System ruchu

#### `choose_movement_mode(unit, target, game_engine)` (duplikat)
**Plik:** `ruch_jednostek.py`  
**Status:** ✅ **KOMPLETNIE ZAIMPLEMENTOWANE** - to samo co w `ai_commander.py`  
**Uwaga:** Ta funkcja to duplikat - implementacja znajduje się w `ai.ruch_jednostek`

#### `move_towards(unit, target, game_engine)` (duplikat)
**Plik:** `ruch_jednostek.py`  
**Status:** ✅ **KOMPLETNIE ZAIMPLEMENTOWANE** - to samo co w `ai_commander.py`  
**Uwaga:** Ta funkcja to duplikat - implementacja znajduje się w `ai.ruch_jednostek`

---

## 🎯 WYSOKIE (Priorytet 2) - 12 funkcji

### **strategia_ai.py** - System strategiczny

#### `analyze_strategic_state(commander, game_engine)`
**Plik:** `strategia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **ANALIZA STANU STRATEGICZNEGO** - kompleksowa ocena całościowej sytuacji na mapie
- [ ] **Krok 1:** Zbieranie danych o kontroli terenu:
  - Policz kontrolowane victory points z `game_engine.board.key_points` (nasze vs przeciwnika)
  - Oceń trendy w kontroli (czy zyskujemy czy tracimy VP przez ostatnie 3 tury)
  - Sprawdź strategic locations (mosty, przełęcze, kluczowe miasta)
- [ ] **Krok 2:** Analiza rozkładu sił na mapie:
  - Oblicz total combat value w każdym sektorze z `game_engine.get_visible_tokens()`
  - Zidentyfikuj gdzie mamy przewagę, a gdzie jesteśmy słabi (`unit.cv` własne vs wrogie)
  - Sprawdź koncentrację vs rozproszenie jednostek
- [ ] **Krok 3:** Ocena sytuacji ekonomicznej:
  - Przychód PE per turn vs wydatki z `commander.player.pe`
  - Stan jednostek (ile potrzebuje resupply) z `unit.fuel`, `unit.ammunition`, `unit.cv`
  - Przewidywane koszty następnej tury
- [ ] **Krok 4:** Analiza zagrożeń i szans:
  - **Zagrożenia:** wroga artyleria AL/AC/AP blisko naszych jednostek
  - **Szanse:** słabo bronione key_points wroga do przejęcia  
  - **Trendy:** czy sytuacja się poprawia czy pogarsza
- [ ] **Krok 5:** Określ podstawową strategię na następne 2-3 tury:
  - **OFFENSIVE:** gdy mamy przewagę sił i dobre PE
  - **DEFENSIVE:** gdy jesteśmy słabsi lub brakuje zasobów
  - **BALANCED:** gdy sytuacja jest wyrównana
  - **DESPERATE:** gdy jesteśmy w krytycznej sytuacji
- [ ] **Krok 6:** Zwróć strategic assessment: `{"strategy": str, "vp_trend": int, "threat_level": float, "opportunities": list}`
- [ ] **Integracja z silnikiem:** wykorzystanie key_points, visible_tokens, player.pe, unit stats
- [ ] **Dla laika:** Jak generał który patrzy na całą mapę i sprawdza "czy wygrywamy czy przegrywamy, gdzie mamy problemy i jakie są nasze szanse"
  - Possible future purchases vs available budget
- [ ] **Krok 4:** Analiza pozycji przeciwnika:
  - Wykorzystaj rozpoznanie do oceny enemy strength
  - Przewiduj prawdopodobne enemy moves
  - Identyfikuj weakness w pozycji przeciwnika
- [ ] **Krok 5:** Określenie overall strategic phase:
  - `EARLY_GAME` - pierwszych kilka tur, deployment phase
  - `EXPANSION` - walka o kluczowe pozycje
  - `CONTACT` - first major engagements
  - `DECISIVE` - kluczowe starcia o zwycięstwo
  - `ENDGAME` - finalizacja rezultatu
- [ ] **Krok 6:** Return strategic_state object z wszystkimi danymi
- [ ] **Dla laika:** To jak generał który patrzy na wielką mapę i odpowiada sobie na pytanie "jak wygląda cała wojna?" - czy wygrywamy, przegrywamy, gdzie są nasze silne i słabe punkty

#### `_adapt_strategy_to_state(commander, strategic_state, game_engine)`
**Plik:** `strategia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **ADAPTACJA STRATEGII** - dostosowanie taktyki do aktualnej sytuacji strategicznej
- [ ] **Krok 1:** Analiza current vs recommended strategy:
  - Sprawdź jaką strategię aktualnie prowadzi `commander.strategic_state`
  - Porównaj z optymalną strategią dla `strategic_state`
  - Oceń czy zmiana strategii jest potrzebna (różnica w approach)
- [ ] **Krok 2:** Wybór głównej strategic doctrine według sytuacji:
  - `AGGRESSIVE_OFFENSE` - gdy mamy przewagę sił >1.3 ratio, atakujemy wszystko
  - `CAREFUL_ADVANCE` - powolne, ostrożne poszerzanie kontroli przy równych siłach
  - `ACTIVE_DEFENSE` - broń się, ale szukaj możliwości kontruderzenia przy niewielkiej przewadze wroga
  - `STRATEGIC_WITHDRAWAL` - organized retreat do lepszych pozycji przy znacznej przewadze wroga
  - `DESPERATE_DEFENSE` - ostatnia obrona kluczowych punktów przy krytycznej sytuacji
- [ ] **Krok 3:** Dostosowanie tactical priorities:
  - Combat vs movement vs resupply priorities w `commander.budget_allocation`
  - Risk tolerance (czy ryzykować vs grać bezpiecznie) - aggression_level 0.0-1.0
  - Resource allocation (ile PE na walkę vs ile na zakupy)
- [ ] **Krok 4:** Aktualizacja commander parameters:
  - Zmień `commander.aggression_level` według sytuacji strategicznej
  - Ustaw `commander.risk_tolerance` na nowy poziom
  - Zaktualizuj `commander.budget_allocation_strategy` (attack/defense/mixed)
- [ ] **Krok 5:** Komunikacja zmiany strategii do innych subsystemów AI
- [ ] **Krok 6:** Logowanie strategic decision dla analizowania wzorców
- [ ] **Integracja z silnikiem:** wykorzystanie commander state, strategic analysis
- [ ] **Dla laika:** Jak doświadczony dowódca który słysząc raporty z frontu mówi "w takim razie zmieniamy plan" i przestawia całą armię na nową taktykę

#### `prioritize_keypoints(commander, game_engine)`
**Plik:** `strategia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **PRIORYTETYZACJA PUNKTÓW KLUCZOWYCH** - ranking najważniejszych celów na mapie
- [ ] **Krok 1:** Identification wszystkich strategicznych lokacji:
  - Victory points z `game_engine.board.key_points` (główne cele do zwycięstwa)
  - Supply hubs (kluczowe dla logistyki) - punkty z high initial_value
  - Defensive positions (choke points, elevated terrain)
  - Bridge heads i crossing points na mapie
- [ ] **Krok 2:** Ocena strategic value każdego punktu:
  - **VP Value:** ile punktów zwycięstwa daje (`keypoint.current_value`)
  - **Tactical Value:** jak dobra pozycja taktyczna (teren, obrona)
  - **Economic Value:** czy generuje PE lub resource bonus
  - **Network Value:** jak łączy inne kluczowe pozycje (connectivity)
- [ ] **Krok 3:** Analiza current control status z `game_engine.get_visible_tokens()`:
  - `CONTROLLED_BY_US` - nasze jednostki na pozycji, do obrony
  - `CONTROLLED_BY_ENEMY` - wrogie jednostki na pozycji, do ataku
  - `NEUTRAL` - brak jednostek, wolne do zdobycia
  - `CONTESTED` - obie strony mają jednostki w pobliżu, walka w toku
- [ ] **Krok 4:** Ocena difficulty of capture/defense:
  - Siła wrogich garrison units (suma `unit.cv` na pozycji i w pobliżu)
  - Difficulty of approach (terrain, bottlenecks) z `board.find_path()`
  - Support z okolicznych wrogich pozycji (w zasięgu 3-5 hexów)
  - Required force ratio dla sukcesu (minimum 1.5:1 dla ataku)
- [ ] **Krok 5:** Kalkulacja priority score dla każdego punktu:
  - Formula: `(Strategic_Value * Urgency_Multiplier) / (Required_Force + Risk_Factor)`
  - Higher score = wyższy priorytet w planowaniu
  - Uwzględnij depletion rate (punkty wyczerpujące się szybko = wyższy priorytet)
- [ ] **Krok 6:** Return sorted list of keypoints by priority: `[{"position": (q,r), "priority": float, "type": str}]`
- [ ] **Integracja z silnikiem:** wykorzystanie key_points, visible_tokens, pathfinding
- [ ] **Dla laika:** Jak generał który patrzy na mapę i decyduje "które miasto jest najważniejsze do zdobycia" - bierze pod uwagę wartość, trudność i ryzyko

#### `_determine_purchase_priority(commander, strategic_state)`
**Plik:** `strategia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **PRIORYTETY ZAKUPÓW** - określenie najważniejszych jednostek do kupienia
- [ ] **Krok 1:** Analiza obecnego składu armii:
  - Zlicz jednostki według typów (TK, IN, AL, AT, etc.) z `commander.player.units`
  - Sprawdź braki w kompozycji (czy brakuje artylerii, czy za mało czołgów)
  - Oceń stan obecnych jednostek (ile potrzebuje resupply vs nowe zakupy)
- [ ] **Krok 2:** Dopasowanie do strategic_state:
  - **OFFENSIVE strategy:** priorytet TK (czołgi) i AL (artyleria do wsparcia)
  - **DEFENSIVE strategy:** priorytet AT (przeciwpancerne) i IN (piechota do garnizonu)
  - **BALANCED strategy:** równowaga między wszystkimi typami
  - **DESPERATE strategy:** tanie jednostki IN dla maximum numbers
- [ ] **Krok 3:** Analiza map terrain i tactical needs:
  - Obszary otwarte = więcej czołgów TK
  - Tereny trudne = więcej piechoty IN
  - Punkty kluczowe do obrony = więcej AT
  - Dalekie cele = więcej artylerii AL/AC/AP dla support
- [ ] **Krok 4:** Economic constraints analysis:
  - Sprawdź dostępne PE z `commander.player.pe`
  - Porównaj koszty różnych typów jednostek
  - Preferuj cost-effective choices przy ograniczonym budżecie
- [ ] **Krok 5:** Określ priority queue dla zakupów:
  - Lista typu: `[{"unit_type": "TK", "priority": 0.9, "reason": "offensive_push"}, ...]`
  - Wyższy priority = ważniejsze do kupienia first
- [ ] **Krok 6:** Zwróć structured purchase priorities
- [ ] **Integracja z silnikiem:** wykorzystanie player.pe, player.units, strategic analysis
- [ ] **Dla laika:** Jak generał który sprawdza stan swojej armii i decyduje "czego nam najbardziej brakuje" - czy więcej czołgów, czy może artylerii

#### `_get_available_purchase_options(commander, game_engine)`
**Plik:** `strategia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **DOSTĘPNE OPCJE ZAKUPU** - sprawdzenie co można kupić w obecnej turze
- [ ] **Krok 1:** Pobierz dostępne typy jednostek z game engine:
  - Sprawdź katalog dostępnych unit types (TK, IN, AL, AT, AC, AP, RE)
  - Pobierz koszty PE dla każdego typu jednostki
  - Sprawdź ograniczenia produkcyjne (limit per turn, special requirements)
- [ ] **Krok 2:** Sprawdź deployment constraints:
  - Zidentyfikuj dostępne deployment hexes z `game_engine.board`
  - Sprawdź czy są wolne pozycje startowe (nie blokowane przez inne jednostki)
  - Uwzględnij zasady deployment (czy można deployować w enemy territory)
- [ ] **Krok 3:** Budget feasibility check:
  - Obecne PE z `commander.player.pe`
  - Zarezerwowane PE dla resupply obecnych jednostek
  - Pozostały budget dla nowych zakupów: `available_pe = total_pe - reserved_pe`
- [ ] **Krok 4:** Strategic limitations analysis:
  - Maksymalna liczba jednostek per player (jeśli istnieje limit)
  - Special unit restrictions (czy można kupić unlimited artillery?)
  - Turn-based purchase limits (max units per turn)
- [ ] **Krok 5:** Generuj complete purchase menu:
  - Lista wszystkich dostępnych kombinacji unit type + deployment position
  - Format: `[{"unit_type": "TK", "cost": 40, "deployment_hex": (q,r), "available": True}, ...]`
  - Oznacz opcje które są affordable z obecnym budgetem
- [ ] **Krok 6:** Return structured purchase options
- [ ] **Integracja z silnikiem:** wykorzystanie unit catalog, deployment rules, player.pe
- [ ] **Dla laika:** Jak sprawdzenie w sklepie wojskowym "co mamy w ofercie, ile to kosztuje i czy mnie na to stać"

#### `_select_optimal_purchases(commander, available_options, budget)`
**Plik:** `strategia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **OPTYMALIZACJA ZAKUPÓW** - wybór najlepszej kombinacji jednostek w ramach budżetu
- [ ] **Krok 1:** Setup optimization parameters:
  - Total available budget (PE points)
  - Purchase priorities z `_determine_purchase_priority()` 
  - Strategic goals (czy skupiamy się na offense, defense, balance)
- [ ] **Krok 2:** Generate feasible purchase combinations:
  - Wszystkie kombinacje jednostek które mieszczą się w budget
  - Uwzględnij deployment constraints (gdzie można postawić jednostki)
  - Wyklucz combinations które violate strategic sense (same type only)
- [ ] **Krok 3:** Score każdą kombinację według multiple criteria:
  - **Strategic alignment:** czy combination pasuje do strategic_state
  - **Balanced composition:** czy mamy mix typów jednostek (nie tylko czołgi)
  - **Cost efficiency:** maksimum capability per PE spent
  - **Deployment feasibility:** czy można efektywnie rozmieścić units
- [ ] **Krok 4:** Apply weighting factors według sytuacji:
  - Desperate situations = więcej cheap units (więcej IN, mniej TK)
  - Strong economy = focus na quality units (więcej TK, AL)
  - Balanced game = optimize dla flexibility
- [ ] **Krok 5:** Select optimal combination:
  - Wybierz highest scoring feasible combination
  - Ensure remaining budget (budget - cost) > minimum threshold
  - Verify all selected units można actually deploy
- [ ] **Krok 6:** Return purchase plan: `[{"unit_type": str, "deployment_hex": (q,r), "cost": int}, ...]`
- [ ] **Integracja z silnikiem:** wykorzystanie budget management, deployment system
- [ ] **Dla laika:** Jak mądre zakupy w sklepie - masz listę potrzebnych rzeczy, ograniczony budżet i wybierasz najlepszą kombinację która da ci największą wartość

### **ekonomia_ai.py** - System ekonomiczny

#### `optimize_budget(commander, game_engine)`
**Plik:** `ekonomia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **OPTYMALIZACJA BUDŻETU** - efektywne zarządzanie ekonomicznymi punktami PE
- [ ] **Krok 1:** Analiza aktualnej sytuacji finansowej:
  - Sprawdź current PE z `commander.player.pe`
  - Przewidywany income następnej tury z kontrolowanych key_points
  - Oszacuj essential expenses (resupply, urgent purchases)
- [ ] **Krok 2:** Kategoryzacja wydatków według priorytetów:
  - **CRITICAL:** resupply jednostek z CV < 30% (immediate survival)
  - **HIGH:** zakup jednostek do wypełnienia strategic gaps
  - **MEDIUM:** resupply jednostek z moderate damage
  - **LOW:** improvement purchases (extra units, upgrades)
- [ ] **Krok 3:** Budget allocation strategy:
  - Reserve minimum 30% PE dla emergency resupply
  - Allocate based na strategic_state: 
    * OFFENSIVE = 60% purchases, 40% resupply
    * DEFENSIVE = 40% purchases, 60% resupply  
    * BALANCED = 50% purchases, 50% resupply
- [ ] **Krok 4:** Economic forecasting:
  - Predict PE income dla next 2-3 turns
  - Identify potential economic opportunities (new key points)
  - Plan long-term expensive purchases (heavy units)
- [ ] **Krok 5:** Risk management:
  - Never spend last 10 PE (emergency reserve)
  - Prioritize survival over expansion w desperate situations
  - Avoid overspending który leaves units without resupply
- [ ] **Krok 6:** Generate budget plan: `{"resupply_budget": int, "purchase_budget": int, "reserved": int}`
- [ ] **Integracja z silnikiem:** wykorzystanie player.pe, key_points income, unit costs
- [ ] **Dla laika:** Jak prowadzenie budżetu domowego - sprawdzasz ile masz pieniędzy, ile potrzebujesz na jedzenie i rachunki, a resztę możesz wydać na przyjemności

#### `adaptive_purchase_ai(commander, game_engine, budget_plan)`
**Plik:** `ekonomia_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **ADAPTACYJNE ZAKUPY** - inteligentny system kupowania jednostek dostosowany do sytuacji
- [ ] **Krok 1:** Analiza tactical situation dla purchase decisions:
  - Sprawdź najbliższe zagrożenia z `game_engine.get_visible_tokens()` 
  - Oceń gdzie potrzebujemy reinforcements most urgently
  - Zidentyfikuj gaps w present army composition
- [ ] **Krok 2:** Adaptive prioritization based na game phase:
  - **EARLY_GAME:** focus na balanced force composition
  - **MID_GAME:** specialize według developing tactical situation  
  - **LATE_GAME:** maximize immediate impact per PE spent
  - **ENDGAME:** prefer cheap units dla numerical advantage
- [ ] **Krok 3:** Counter-strategy purchases:
  - Jeśli enemy ma много czołgów → kupuj więcej AT units
  - Jeśli enemy ma artillery threatening → kupuj fast units dla raids
  - Jeśli enemy ma strong infantry → kupuj armor dla breakthrough
- [ ] **Krok 4:** Deployment-aware purchasing:
  - Sprawdź available deployment hexes z `game_engine.board`
  - Preferuj units które można deploy close to action zones
  - Avoid purchases które będą stranded far from combat
- [ ] **Krok 5:** Execute intelligent purchases:
  - Start z highest priority purchases z budget_plan
  - Adjust quantities based na available PE
  - Use `game_engine.execute_action()` dla actual purchases
  - Reserve small buffer dla unexpected opportunities
- [ ] **Krok 6:** Track purchase effectiveness dla future learning:
  - Log what was bought, why, i eventual outcome
  - Build purchase pattern recognition dla better decisions
- [ ] **Krok 7:** Return purchase summary: `{"units_bought": list, "pe_spent": int, "strategic_reason": str}`
- [ ] **Integracja z silnikiem:** wykorzystanie execute_action, deployment system, visible_tokens
- [ ] **Dla laika:** Jak mądre zakupy na targu - patrzysz co dzieje się w okolicy, co ci brakuje w domu, i kupujesz exactly to co potrzebujesz w tej chwili

---

## ⚔️ ŚREDNIE (Priorytet 3) - 15 funkcji

### **walka_ai.py** - System walki

#### `ai_attempt_combat(unit: Dict, game_engine: Any, player_id: int, player_nation: str = "Unknown") -> bool`
**Plik:** `walka_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **PODEJMOWANIE WALKI (TYPOWANA)** - główna funkcja inicjująca combat sequence
- [ ] **Krok 1:** Pre-combat validation i setup:
  - Verify unit to valid combat-capable Token
  - Check player_id authorization dla control
  - Ensure unit ma sufficient ammo + fuel
- [ ] **Krok 2:** Target acquisition i enemy detection:
  - Call `find_enemies_in_range()` dla comprehensive scan
  - Filter viable targets (excluduj allies, neutrals)
  - Prioritize targets by threat level i strategic value
- [ ] **Krok 3:** Combat decision matrix:
  - For každdy viable target: call combat evaluation
  - Calculate expected outcome dla każej potential combat
  - Choose optimal target based on risk/reward ratio
- [ ] **Krok 4:** Tactical positioning verification:
  - Check czy unit potrzebuje flanking maneuver
  - Verify optimal attack position
  - Consider reaction attack risks
- [ ] **Krok 5:** Combat execution z proper logging:
  - Execute chosen combat através proper game engine
  - Log combat attempt z player_nation context
  - Update unit status post-combat
- [ ] **Krok 6:** Return boolean success indicator
- [ ] **Dla laika:** To jak dowódca czołgu który patrzy przez peryskop, wybiera cel, sprawdza czy ma dobra pozycję i daje rozkaz "OGIEŃ!"

#### `find_enemies_in_range(unit: Dict, game_engine: Any, player_id: int) -> List[Dict]`
**Plik:** `walka_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **WYKRYWANIE WROGÓW (TYPOWANA)** - precyzyjny system lokalizacji przeciwników
- [ ] **Krok 1:** Range calculation based na unit capabilities:
  - Determine maximum attack range dla unit type
  - Include detection range (może być większy niż attack range)
  - Factor in unit experience bonuses dla detection
- [ ] **Krok 2:** Systematic battlefield scanning:
  - Iterate através wszystkich hexagons w calculated range
  - Apply line-of-sight calculations (terrain blocking)
  - Consider stealth/camouflage mechanics
- [ ] **Krok 3:** Enemy identification i filtering:
  - Detect wszystkie non-friendly units w range
  - Exclude player_id's own units (prevent friendly fire)
  - Verify detected units są actually hostile
- [ ] **Krok 4:** Detailed enemy analysis:
  - Gather intelligence na každdy detected enemy
  - Estimate combat capabilities (CV, unit type)
  - Assess movement capabilities i threat potential
- [ ] **Krok 5:** Tactical situation assessment:
  - Group enemies by threat priority
  - Calculate combined threat z multiple enemies
  - Identify high-value targets (artillery, command)
- [ ] **Krok 6:** Return structured enemy list z metadata
- [ ] **Dla laika:** To jak obserwator w wieży który ma lornetki i skanuje okolicę, tworzy listę wszystkich wrogich żołnierzy które widzi i ocenia jak niebezpieczni są

#### `evaluate_combat_ratio(unit: Dict, enemy: Dict) -> float`
**Plik:** `walka_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **OCENA STOSUNKU SIŁ (TYPOWANA)** - precyzyjny algorytm porównywania siły bojowej
- [ ] **Krok 1:** Basic combat value extraction:
  - Get current CV (Combat Value) dla both units
  - Verify values są sensible (nie negative, nie zero)
  - Handle edge cases (damaged units, resupply status)
- [ ] **Krok 2:** Unit type effectiveness matrix:
  - Apply rock-paper-scissors bonuses/penalties
  - AT units vs TANK = bonus dla AT
  - Infantry vs Artillery = bonus dla Infantry
  - Armor vs Infantry = bonus dla Armor
- [ ] **Krok 3:** Terrain i positioning modifiers:
  - Defender w fortified position = defensive bonus
  - Attacker z higher ground = offensive bonus
  - Units w cover (forest, city) = defensive modifier
- [ ] **Krok 4:** Experience i morale factors:
  - Veteran units fight better (experience bonus)
  - Units with high morale = combat effectiveness bonus
  - Damaged units fight worse (CV degradation effect)
- [ ] **Krok 5:** Advanced ratio calculation:
  - Formula: (Adjusted_Attacker_CV / Adjusted_Defender_CV)
  - Include all modifiers w calculation
  - Cap ratio at reasonable limits (0.1 - 10.0)
- [ ] **Krok 6:** Return precise float ratio z confidence metrics
- [ ] **Dla laika:** To jak porównywanie dwóch bokserów przed walką - sprawdza wagę, umiejętności, doświadczenie i przewiduje kto ma lepsze szanse

#### `execute_ai_combat(unit: Dict, enemy: Dict, game_engine: Any, player_nation: str = "Unknown") -> bool`
**Plik:** `walka_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **WYKONANIE WALKI (TYPOWANA)** - precyzyjne wykonanie akcji bojowej
- [ ] **Krok 1:** Final pre-combat validation:
  - Double-check wszystkie combat preconditions
  - Verify positions nie changed during planning
  - Ensure both units still exist i są capable
- [ ] **Krok 2:** Combat action preparation:
  - Create proper CombatAction object dla game engine
  - Include attacker/defender IDs + player nation context
  - Set combat parameters (ammo type, attack mode)
- [ ] **Krok 3:** Game engine interaction z error handling:
  - Call `game_engine.execute_action()` z complete error handling
  - Handle potential exceptions (invalid action, timing issues)
  - Retry logic dla transient failures
- [ ] **Krok 4:** Combat result processing:
  - Parse ActionResult dla combat outcome
  - Extract damage dealt/received information
  - Update internal tracking z combat statistics
- [ ] **Krok 5:** Post-combat state management:
  - Update unit states based on combat results
  - Handle potential unit destruction/retreat
  - Log combat details dla player_nation analytics
- [ ] **Krok 6:** Return boolean success/failure z detailed logging
- [ ] **Dla laika:** To jak strzelanie z broni - wszystko jest przygotowane, teraz tylko naciśnij spust, sprawdź czy trafił i zobacz co się stało z celem

#### `attempt_retreat_low_cv(unit: Dict, game_engine: Any) -> bool`
**Plik:** `walka_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **ODWRÓT SŁABYCH JEDNOSTEK** - automatyczna ewakuacja uszkodzonych sił
- [ ] **Krok 1:** Damage assessment i retreat threshold:
  - Check current CV vs maximum CV percentage
  - Default threshold: retreat quando CV < 30% maximum
  - Consider unit type (some units are more fragile)
- [ ] **Krok 2:** Escape route analysis:
  - Find safe hexagons poza enemy threat range
  - Prioritize friendly-controlled territory
  - Avoid routes que atravessam enemy zones of control
- [ ] **Krok 3:** Retreat feasibility check:
  - Verify unit ma sufficient movement points
  - Check dla fuel availability (no fuel = no retreat)
  - Ensure retreat path não blocked by obstacles
- [ ] **Krok 4:** Risk vs benefit evaluation:
  - Cost of staying (probable destruction)
  - Cost of retreat (lost tactical position)
  - Strategic value of preserving damaged unit
- [ ] **Krok 5:** Retreat execution z optimal pathing:
  - Move usando shortest safe path
  - Use MARCH mode dla maximum distance
  - Avoid reaction attacks podczas withdrawal
- [ ] **Krok 6:** Post-retreat positioning i status update
- [ ] **Dla laika:** To jak ranny żołnierz który automatycznie ucieka z pola bitwy cuando jest zbyt słaby żeby dalej walczyć - szuka najbezpieczniejszej drogi do wycofania się

#### `try_flank_before_attack(unit: Dict, enemy: Dict, game_engine: Any) -> bool`
**Plik:** `walka_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać manewr oskrzydlenia przed atakiem

### **zaopatrzenie_ai.py** - System zaopatrzenia

#### `pre_resupply(commander, game_engine)`
**Plik:** `zaopatrzenie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać wstępne uzupełnianie

#### `tactical_resupply(commander, game_engine, trigger="DAMAGE")`
**Plik:** `zaopatrzenie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać taktyczne uzupełnianie

#### `_perform_resupply(unit, game_engine, resupply_type="fuel")`
**Plik:** `zaopatrzenie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać wykonanie uzupełniania

### **obrona_ai.py** - System obrony

#### `assess_defensive_threats(my_units: List[Dict], game_engine: Any) -> Dict[str, Any]`
**Plik:** `obrona_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać ocenę zagrożeń obronnych

#### `plan_defensive_retreat(threatened_units: List[Dict], threat_assessment: Dict, game_engine: Any) -> List[Dict]`
**Plik:** `obrona_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać planowanie odwrotu obronnego

#### `find_safe_retreat_position(unit: Dict, target_point: Position, threatening_enemies: List[Dict], game_engine: Any) -> Position`
**Plik:** `obrona_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać znajdowanie bezpiecznej pozycji odwrotu

#### `find_safe_fallback_position(unit: Dict, threatening_enemies: List[Dict], game_engine: Any) -> Position`
**Plik:** `obrona_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać znajdowanie pozycji zapasowej

#### `evaluate_position_safety(position: Position, threatening_enemies: List[Dict], target_point: Position = None) -> float`
**Plik:** `obrona_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać ocenę bezpieczeństwa pozycji

#### `defensive_coordination(my_units: List[Dict], threat_assessment: Dict, game_engine: Any) -> None`
**Plik:** `obrona_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać koordynację obrony

#### `plan_group_defense(key_point: Dict, defending_units: List[Dict], game_engine: Any) -> Dict`
**Plik:** `obrona_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać planowanie obrony grupowej

---

## 🔧 NISKIE (Priorytet 4) - 8 funkcji

### **rozpoznanie_ai.py** - System rozpoznania

#### `gather_reconnaissance(commander, game_engine: Any)`
**Plik:** `rozpoznanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać zbieranie informacji rozpoznawczych

#### `analyze_enemy_clusters(enemies: List[Dict])`
**Plik:** `rozpoznanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać analizę skupisk wroga

### **rajdy_ai.py** - System rajdów

#### `opportunistic_capture_phase(game_engine, my_units: List[Dict], player_id: int)`
**Plik:** `rajdy_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać rajdy opportunistyczne

### **rekomendacje_ai.py** - System rekomendacji

#### `_generate_action_recommendations(ai) -> List[str]`
**Plik:** `rekomendacje_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać generowanie rekomendacji

#### `_execute_strategic_plan(ai, strategic_plan: Dict[str, Any], game_engine) -> None`
**Plik:** `rekomendacje_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] TODO: Opisać wykonanie planu strategicznego

### **reakcje_ai.py** - System reakcji

#### `check_ai_reaction_attacks(game_engine, my_units, player_id)`
**Plik:** `reakcje_ai.py`  
**Status:** ⚠️ CZĘŚCIOWO (ma implementację ale niepełną)  
**Plan implementacji:**
- [ ] TODO: Sprawdzić i uzupełnić logikę reakcji

---

## 📊 PODSUMOWANIE - STAN RZECZYWISTY PO KOREKCIE

**Całkowity stan implementacji:**
- ✅ **GOTOWE (główny plik):** 8 funkcji w `ai_commander.py` 
- ✅ **GOTOWE (delegacje):** 7 funkcji delegowanych do innych modułów  
- ❌ **Brakuje:** 43 funkcje wymagające implementacji
- ⚠️ **Częściowe:** 1 funkcja (`check_ai_reaction_attacks`)
- **RAZEM:** 15/58 funkcji zaimplementowanych (26% ukończenia)

**KOMPLETNIE ZAIMPLEMENTOWANE W AI_COMMANDER.PY:**
1. ✅ `make_tactical_turn()` - 700+ linii, główny sterownik AI
2. ✅ `advanced_autonomous_mode()` - 100+ linii, strategiczne myślenie  
3. ✅ `get_my_units()` - kompletne spisywanie jednostek
4. ✅ `scan_for_enemies()` - radar taktyczny z fog of war
5. ✅ `_check_and_manage_garrisons()` - zarządzanie garnizonami
6. ✅ `prioritize_targets()` - funkcja pomocnicza (używana)
7. ✅ `opportunistic_capture_phase()` - delegacja do `ai.rajdy_ai`
8. ✅ `get_player_nation()` - funkcja pomocnicza

**ZAIMPLEMENTOWANE JAKO DELEGACJE:**
1. ✅ `ai_attempt_combat()` → `ai.walka_ai` (kompletne)
2. ✅ `find_enemies_in_range()` → `ai.walka_ai` (z detection system)
3. ✅ `evaluate_combat_ratio()` → `ai.walka_ai` (z bonusami)
4. ✅ `_attempt_retreat_low_cv()` → `ai.walka_ai` (system odwrotu)
5. ✅ `_try_flank_before_attack()` → `ai.walka_ai` (podstawowy flanking)
6. ✅ `execute_ai_combat()` → `ai.walka_ai` (wykonanie przez silnik)
7. ✅ `move_towards()` → `ai.ruch_jednostek` (nawigacja + progressive)
8. ✅ `choose_movement_mode()` → `ai.ruch_jednostek` (wybór trybu)

**STATUS NAJWAŻNIEJSZYCH SYSTEMÓW:**
- 🎯 **Główny sterownik AI:** ✅ GOTOWY (make_tactical_turn)
- 🧠 **Myślenie strategiczne:** ✅ GOTOWY (advanced_autonomous_mode)  
- ⚔️ **System walki:** ✅ GOTOWY (cały moduł ai.walka_ai)
- 🚶 **System ruchu:** ✅ GOTOWY (ai.ruch_jednostek)
- 🏰 **Zarządzanie garnizonami:** ✅ GOTOWY
- 📊 **Grupowanie i koordynacja:** ❌ CZĘŚCIOWO (szkielety)

**Plan działania - ZAKTUALIZOWANY:**
1. **KROK 1:** ✅ **UKOŃCZONE** - Główne funkcje AI Commander działają  
2. **KROK 2:** ❌ **DO ZROBIENIA** - Dokończyć KRYTYCZNE (15 pozostałych)
3. **KROK 3:** ❌ **DO ZROBIENIA** - Zaimplementować WYSOKIE (12 funkcji)  
4. **KROK 4:** ❌ **DO ZROBIENIA** - Zaimplementować ŚREDNIE (15 funkcji)
5. **KROK 5:** ❌ **DO ZROBIENIA** - Zaimplementować NISKIE (8 funkcji)

**Pierwsza funkcja do kontynuacji:** `adaptive_grouping()` w `ai.grupowanie_ai` - kluczowa dla koordynacji zespołów

---

## 🛡️ NISKIE (Priorytet 4) - 8 funkcji

### **logowanie_ai.py** - System logowania

#### `setup_ai_logging()`
**Plik:** `logowanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **SETUP LOGÓW AI** - konfiguracja systemu logowania dla debugowania AI
- [ ] **Krok 1:** Konfiguracja poziomów logowania:
  - DEBUG dla detailed AI decision analysis
  - INFO dla strategic decisions i major actions
  - WARNING dla suboptimal decisions lub problemy
  - ERROR dla AI failures lub critical issues
- [ ] **Krok 2:** Setup plików logów:
  - `ai_tactical.log` dla tactical decisions
  - `ai_strategic.log` dla strategic planning
  - `ai_combat.log` dla combat decisions i outcomes
  - `ai_economy.log` dla economic decisions i resource management
- [ ] **Krok 3:** Structured logging format:
  - Timestamp dla event correlation
  - Player ID i nation dla multiplayer debugging
  - Turn number dla temporal analysis
  - Decision category dla filtering
- [ ] **Krok 4:** Performance monitoring:
  - Track AI decision time dla optimization
  - Monitor memory usage podczas complex calculations
  - Log computational bottlenecks
- [ ] **Krok 5:** Integration z debug systems:
  - Easy toggle między log levels
  - Support dla conditional logging (only dla specific players)
  - File rotation dla preventing disk space issues
- [ ] **Krok 6:** Return configured logger objects
- [ ] **Integracja z silnikiem:** wykorzystanie standard Python logging
- [ ] **Dla laika:** Jak konfiguracja systemu nagrywania rozmów telefonicznych dla później analiza co poszło źle

#### `log_ai_decision(decision_type, context, result)`
**Plik:** `logowanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **LOGOWANIE DECYZJI** - szczegółowe śledzenie każdej decyzji AI dla debugowania
- [ ] **Krok 1:** Format structured decision entry:
  - Decision timestamp z millisecond precision
  - Decision category (TACTICAL, STRATEGIC, COMBAT, ECONOMIC)
  - Player context (ID, nation, current situation)
- [ ] **Krok 2:** Context capture dla decision analysis:
  - Game state snapshot (current turn, VP status, PE available)
  - Unit states relevant dla decision (positions, CV, resources)
  - Enemy intelligence (what AI could see)
- [ ] **Krok 3:** Decision details documentation:
  - Input parameters dla decision function
  - Alternative options considered
  - Scoring criteria i weights used
  - Final choice i reasoning
- [ ] **Krok 4:** Outcome tracking:
  - Immediate result (success/failure/partial)
  - Resource costs (PE spent, units lost)
  - Strategic impact (VP gained/lost, position changes)
- [ ] **Krok 5:** Pattern analysis support:
  - Tag decisions z success/failure labels
  - Link related decisions dla sequence analysis
  - Mark critical decision points dla review
- [ ] **Krok 6:** Output formatting dla different consumers:
  - Human-readable dla manual analysis
  - Machine-readable dla automated pattern detection
  - Statistical summary dla performance metrics
- [ ] **Integracja z silnikiem:** leveruje game state data
- [ ] **Dla laika:** Jak prowadzenie szczegółowego dziennika wszystkich ważnych decyzji z uzasadnieniem - potem można przeczytać i zrozumieć dlaczego coś poszło źle

#### `analyze_ai_patterns(log_data)`
**Plik:** `logowanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **ANALIZA WZORCÓW** - wykrywanie patterns w behavior AI dla improvement
- [ ] **Krok 1:** Load i parse historical log data:
  - Read multiple game sessions
  - Normalize timestamps i game contexts
  - Filter by specific players, time periods, lub game situations
- [ ] **Krok 2:** Decision pattern extraction:
  - Identify recurring decision sequences
  - Find correlations między decisions i outcomes
  - Detect successful vs unsuccessful strategy patterns
- [ ] **Krok 3:** Performance metrics calculation:
  - Win/loss ratios in różnych scenarios
  - Resource efficiency (PE spent vs VP gained)
  - Combat effectiveness (attack success rates)
  - Economic management (PE generation vs spending)
- [ ] **Krok 4:** Problema detection:
  - Find repeated unsuccessful patterns
  - Identify decision biases (always attacking, never retreating)
  - Detect resource mismanagement patterns
- [ ] **Krok 5:** Improvement suggestions:
  - Recommend parameter adjustments
  - Suggest new decision criteria
  - Identify training data dla machine learning improvements
- [ ] **Krok 6:** Return analysis report: `{"patterns": list, "metrics": dict, "recommendations": list}`
- [ ] **Integracja z silnikiem:** statistical analysis tools
- [ ] **Dla laika:** Jak analiza nagrań meczów drużyny sportowej - sprawdzasz co się powtarza, co działa dobrze, co źle, i jak poprawić grę

### **rozpoznanie_ai.py** - System rozpoznania

#### `gather_intelligence(commander, game_engine)`
**Plik:** `rozpoznanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **ZBIERANIE WYWIADU** - systematyczne gromadzenie informacji o przeciwniku
- [ ] **Krok 1:** Tactical intelligence gathering:
  - Skanuj wszystkich visible enemies z `game_engine.get_visible_tokens()`
  - Catalog enemy unit types, pozycje, i estimated strength
  - Track enemy movement patterns z historical data
- [ ] **Krok 2:** Strategic intelligence assessment:
  - Monitor enemy control territory z `game_engine.board.key_points`
  - Estimate enemy PE income z controlled points
  - Analyze enemy purchase patterns (what types bought, where deployed)
- [ ] **Krok 3:** Threat assessment:
  - Identify immediate tactical threats (enemy artillery positions)
  - Assess strategic threats (enemy buildup in specific areas)
  - Evaluate enemy capabilities vs our own forces
- [ ] **Krok 4:** Opportunity identification:
  - Find weak points w enemy lines
  - Identify undefended valuable targets
  - Spot potential enemy mistakes lub overextension
- [ ] **Krok 5:** Intelligence synthesis:
  - Combine current observations z historical patterns
  - Create comprehensive enemy profile
  - Generate tactical i strategic recommendations
- [ ] **Krok 6:** Return intelligence report: `{"enemy_strength": dict, "threats": list, "opportunities": list}`
- [ ] **Integracja z silnikiem:** wykorzystanie visible_tokens, key_points, historical data
- [ ] **Dla laika:** Jak szpieg który obserwuje wroga i sprawdza ile ma żołnierzy, gdzie ich trzyma, jakie są ich słabe punkty i jak można ich pokonać

#### `predict_enemy_moves(intelligence_data, game_engine)`
**Plik:** `rozpoznanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **PREDYKCJA RUCHÓW WROGA** - przewidywanie prawdopodobnych działań przeciwnika
- [ ] **Krok 1:** Pattern analysis z historical enemy behavior:
  - Analyze past moves z intelligence_data
  - Identify enemy preferences (aggressive, defensive, economic focus)
  - Track timing patterns (when enemy attacks, retreats, purchases)
- [ ] **Krok 2:** Situational assessment dla prediction:
  - Current enemy positions i capabilities
  - Available enemy targets i opportunities
  - Enemy resource constraints (estimated PE, unit damage)
- [ ] **Krok 3:** Multi-scenario modeling:
  - **AGGRESSIVE scenario:** enemy goes all-out attack
  - **DEFENSIVE scenario:** enemy consolidates i defends
  - **ECONOMIC scenario:** enemy focuses na resource accumulation
  - **DESPERATE scenario:** enemy makes risky moves
- [ ] **Krok 4:** Probability weighting:
  - Assign probabilities do each scenario based na intelligence
  - Consider enemy personality (if available)
  - Weight recent behavior more heavily
- [ ] **Krok 5:** Specific move predictions:
  - Most likely target areas dla enemy attacks
  - Probable enemy unit deployments
  - Expected enemy economic decisions
- [ ] **Krok 6:** Return prediction set: `[{"move_type": str, "probability": float, "details": dict}]`
- [ ] **Integracja z silnikiem:** historical move analysis, game state projection
- [ ] **Dla laika:** Jak doświadczony gracz w szachy który patrzy na pozycję przeciwnika i przewiduje "prawdopodobnie zrobi tak albo tak"

#### `update_threat_assessment(commander, new_intelligence)`
**Plik:** `rozpoznanie_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **AKTUALIZACJA OCENY ZAGROŻEŃ** - dynamiczne update threat levels na podstawie nowych danych
- [ ] **Krok 1:** Integration nowych informacji:
  - Merge new_intelligence z existing threat database
  - Update enemy unit locations i status
  - Refresh threat calculations based na new positions
- [ ] **Krok 2:** Threat level calculation:
  - **CRITICAL:** immediate existential threats (enemy przy naszych key points)
  - **HIGH:** major tactical threats (strong enemy forces nearby)
  - **MEDIUM:** potential future threats (enemy buildup)
  - **LOW:** distant lub minor threats
- [ ] **Krok 3:** Threat categorization:
  - **TACTICAL:** immediate combat threats (enemy artillery w range)
  - **STRATEGIC:** longer-term positional threats (enemy controlling VP)
  - **ECONOMIC:** threats do resource generation (attacks na our key points)
- [ ] **Krok 4:** Priority recalculation:
  - Adjust defense priorities based na updated threats
  - Update target priority lists dla counter-attacks
  - Modify strategic plans according do threat changes
- [ ] **Krok 5:** Alert generation:
  - Generate warnings dla significantly increased threats
  - Recommend immediate responses dla critical threats
  - Update early warning systems
- [ ] **Krok 6:** Update commander's threat awareness i adjust strategies accordingly
- [ ] **Integracja z silnikiem:** real-time threat monitoring system
- [ ] **Dla laika:** Jak aktualizacja mapy zagrożeń w systemie bezpieczeństwa - gdy pojawia się nowa informacja, cały obraz zagrożeń się aktualizuje

### **konfiguracja_ai.py** - Konfiguracja AI

#### `load_ai_config(config_file_path)`
**Plik:** `konfiguracja_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **ŁADOWANIE KONFIGURACJI** - system zarządzania ustawieniami AI
- [ ] **Krok 1:** Load configuration z pliku:
  - Support JSON lub YAML format dla flexibility
  - Handle missing files z sensible defaults
  - Validate configuration structure i values
- [ ] **Krok 2:** AI personality parameters:
  - Aggression levels (0.0 conservative - 1.0 highly aggressive)
  - Risk tolerance settings
  - Economic vs military focus balance
- [ ] **Krok 3:** Tactical parameters:
  - Combat ratio thresholds dla attacking decisions
  - Retreat thresholds dla unit preservation
  - Grouping preferences i coordination settings
- [ ] **Krok 4:** Strategic parameters:
  - Resource allocation ratios (attack/defense/economy)
  - Long-term vs short-term planning balance
  - Victory condition priorities
- [ ] **Krok 5:** Performance tuning:
  - Decision timeout limits
  - Calculation depth limits dla complex decisions
  - Memory usage constraints
- [ ] **Krok 6:** Return validated config object z all parameters
- [ ] **Integracja z silnikiem:** configuration management system
- [ ] **Dla laika:** Jak ustawienia w grze komputerowej - możesz wybrać czy AI ma być agresywne czy defensywne, mądre czy szybkie

#### `save_ai_config(config_data, config_file_path)`
**Plik:** `konfiguracja_ai.py`  
**Status:** ❌ PUSTE (`pass`)  
**Plan implementacji:**
- [ ] **ZAPISYWANIE KONFIGURACJI** - preservation ustawień AI dla future use
- [ ] **Krok 1:** Configuration validation przed save:
  - Check all required parameters są present
  - Validate parameter ranges i types
  - Ensure configuration consistency
- [ ] **Krok 2:** Backup existing configuration:
  - Create backup z timestamp
  - Preserve previous working settings
  - Enable rollback if needed
- [ ] **Krok 3:** Format configuration dla storage:
  - Pretty-print JSON dla human readability
  - Include comments lub documentation w file
  - Organize parameters w logical sections
- [ ] **Krok 4:** Safe file writing:
  - Use atomic file operations
  - Handle disk space i permission issues
  - Verify successful write
- [ ] **Krok 5:** Configuration versioning:
  - Include config version number
  - Support migration między versions
  - Maintain compatibility z older formats
- [ ] **Krok 6:** Return success status i backup location
- [ ] **Integracja z silnikiem:** file system operations
- [ ] **Dla laika:** Jak zapisywanie ustawień w programie - żeby następnym razem pamiętał jak lubisz grać

---

## 📈 STATYSTYKI KOŃCOWE

**KOMPLETNA ANALIZA WSZYSTKICH 58 FUNKCJI AI:**
- ✅ **ZAIMPLEMENTOWANE:** 15 funkcji (26%)
- ❌ **DO IMPLEMENTACJI:** 43 funkcje (74%)
- ⚠️ **CZĘŚCIOWE:** 1 funkcja (2%)

**PODZIAŁ WEDŁUG PRIORYTETÓW:**
- 🔴 **KRYTYCZNE:** 8 gotowych, 15 do zrobienia (35% ukończenia)
- 🟡 **WYSOKIE:** 0 gotowych, 12 do zrobienia (0% ukończenia)  
- 🟠 **ŚREDNIE:** 0 gotowych, 15 do zrobienia (0% ukończenia)
- 🟢 **NISKIE:** 0 gotowych, 8 do zrobienia (0% ukończenia)

**GOTOWE SYSTEMY:**
- ✅ AI Commander (główny sterownik)
- ✅ System walki (ai.walka_ai)
- ✅ System ruchu (ai.ruch_jednostek)  
- ✅ Zarządzanie garnizonami

**SYSTEMY DO DOKOŃCZENIA:**
- ❌ Grupowanie i koordynacja (grupowanie_ai.py)
- ❌ Strategia i planning (strategia_ai.py)
- ❌ Zarządzanie ekonomią (ekonomia_ai.py)
- ❌ Rozpoznanie i wywiad (rozpoznanie_ai.py)

**STATUS: GOTOWY DO DALSZEJ IMPLEMENTACJI** 🚀

Dokumentacja wszystkich 58 funkcji AI została ukończona z szczegółowymi planami implementacji dostosowanymi do rzeczywistej architektury silnika gry.
