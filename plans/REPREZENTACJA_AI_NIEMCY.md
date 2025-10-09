# Reprezentacja przeciwnika: Niemcy (AI)

## Cel dokumentu
Ten dokument opisuje komplet zasad i mechanik, które muszą być odwzorowane, aby wiernie symulować gracza sterowanego przez AI (Niemcy) w rozgrywce, w której gracz human (Polska) współdziała z silnikiem "Kampania 1939". Zawarte tu informacje łączą logikę silnika (`engine/`), warstwę rdzeniową (`core/`), system ekonomii oraz zachowanie warstw AI (`ai/`).

---

## 1. Struktura tury i kalendarz
- **Menedżer tur (`core/tura.py`)**:
  - 6 tur = 1 pełna doba. Mapowanie faz: 1 → rano, 2-3 → dzień, 4 → wieczór, 5-6 → noc.
  - `TurnManager.current_turn` zwiększa się przy każdym przejściu do kolejnego gracza.
  - `get_ui_weather_report()` zwraca skrót: `Data/Dzień | Pora dnia | Pogoda`.
  - `TurnManager.weather` korzysta z `core/pogoda.Pogoda`:
    - Temperatura w przedziale −5°C do 25°C, z ograniczeniem zmiany ±2°C między kolejnymi dniami.
    - Zachmurzenie: bezchmurnie / umiarkowane / duże.
    - Opady zależne od zachmurzenia; przy temperaturze < 0°C opady śnieżne.

- **Faza końca tury (`engine/GameEngine.next_turn`)**:
  - Reset punktów ruchu (`currentMovePoints`) według aktywnego trybu ruchu.
  - Reset paliwa nie następuje automatycznie – paliwo musi być uzupełniane akcjami AI/humana.
  - Reset limitów artylerii (jedna salwa zwykła i jedna reakcyjna na turę).
  - Czyszczenie tymczasowej widoczności i ponowne przeliczenie mgły wojny.

---

## 2. Jednostki i parametry podstawowe
- **Źródło prawdy**: `core/unit_factory.py` oraz system balansowania `balance/model.py` opisany w `docs/TOKEN_BALANCING_GUIDE.md`.
- **Typy jednostek** (`unitType`): `P` (piechota), `K` (kawaleria), `TL`, `TŚ`, `TC`, `TS`, `AL`, `AC`, `AP`, `Z` (zaopatrzenie), `D` (dowództwo), `G` (generał).
- **Parametry statystyczne**:
  - `move` – maksymalne MP w trybie bojowym.
  - `maintenance` – pula paliwa.
  - `combat_value` – aktualna siła bojowa (HP).
  - `attack.range` i `attack.value` – zasięg i siła ataku.
  - `defense_value` – bazowa obrona modyfikowana terenem.
  - `sight` – zasięg widzenia.
  - `price` – koszt w PE; używany także jako wartość VP przy eliminacji.
- **Tryby ruchu (`Token.apply_movement_mode`)**:
  - `combat`: 100% MP, 100% obrony.
  - `march`: 150% MP, 50% obrony.
  - `recon`: 50% MP, 125% obrony; użyteczne do zwiadu.
  - Zmiana trybu blokowana do końca tury, jeśli została już raz ustawiona.
- **System paliwa**:
  - Przed ruchem walidowana jest dostępność paliwa; jednostka bez paliwa nie ruszy się (`validate_movement_resources`).
  - Konsumpcja paliwa = koszt ruchu (1 + modyfikator terenu) za każde pole.
- **Limity artylerii** (`engine/token.py`):
  - Jednostki `AL`, `AC`, `AP` mogą oddać 1 strzał normalny i 1 strzał reakcyjny na turę.
  - Próba kolejnego ataku zostaje zablokowana z komunikatem.

---

## 3. Ruch i pathfinding
- **Walidacja początkowa** (`MovementValidator.validate_basic_movement`):
  - Pole musi istnieć, nie być nieprzejezdne (`move_mod == -1`) i nie może być zajęte przez sojusznika.
- **Walidacja zasobów** (`validate_movement_resources`):
  - Sprawdza dostępne MP i paliwo po uwzględnieniu trybu ruchu.
- **Pathfinding** (`PathfindingService.find_movement_path`):
  - Korzysta z `Board.find_path` (A* na heksach). Uwzględnia MP, paliwo i widoczne jednostki przeciwnika.
  - Jeśli brak pełnej ścieżki, stosuje fallback do najbliższego osiągalnego pola.
- **Koszt ruchu** (`calculate_path_cost_and_position`):
  - Każdy krok: koszt = 1 + `tile.move_mod`; jednocześnie odejmowany od MP i paliwa.
  - Ruch zatrzymuje się, jeśli w zasięgu widzenia pojawi się wróg; kończy się na polu, na którym wroga wykryto.
- **Aktualizacja widzenia** (`VisionService.update_player_vision`):
  - Każdy odwiedzony hex na trasie dokłada do tymczasowej widoczności i rejestruje wykrytych przeciwników z poziomem detekcji.

---

## 4. Widoczność i detekcja
- **Zasięg widzenia**: `VisionService.calculate_visible_hexes` tworzy listę heksów w promieniu `sight`.
- **Poziom detekcji** (`calculate_detection_level`):
  - Krzywa nieliniowa odległości: 1.0 przy dystansie 0; spada wykładniczo.
  - Mnożnik pory dnia: wieczór ×0.9, noc ×0.7.
- **Filtr informacji** (`engine/detection_filter.py`):
  - `detection_level ≥ 0.8` – pełne dane (pozycja, CV, typ).
  - `0.5 ≤ detection_level < 0.8` – przybliżenia (zakres CV, szacowany typ).
  - `< 0.5` – tylko informacja o obecności.
- **Generał vs dowódcy**:
  - Dowódca widzi tylko własne jednostki + heksy ujawnione tymczasowo.
  - Generał agreguje widoczność dowódców swojej nacji i zawsze widzi wszystkie własne żetony.
- **Czyszczenie widoczności** (`clear_temp_visibility`):
  - Po zmianie tury tymczasowe dane są zerowane, a `update_all_players_visibility` ponownie ustala mgłę wojny.

---

## 5. Walka
- **Walidacja** (`CombatAction._validate_combat`):
  - Zasięg ataku ≤ `attack.range`.
  - Jednostka musi mieć dodatnie MP w chwili ataku.
  - Blokada przy ataku na własny żeton.
  - Sprawdzenie limitów artylerii (`Token.can_attack`).
- **Obliczenia** (`CombatCalculator.calculate_combat_result`):
  - Atakujący: `attack.value` × losowy mnożnik 0.8–1.2.
  - Obrońca: (`defense_value` + `tile.defense_mod`) × losowy mnożnik 0.8–1.2.
  - Kontratak możliwy, jeśli dystans ≤ `defender.attack.range`.
- **Rozstrzygnięcie** (`CombatResolver.resolve_combat`):
  - Obrażenia odejmowane od `combat_value` obu stron.
  - 50% szans na "przeżycie na 1 CV" i odskok obrońcy na wolny hex oddalający od atakującego.
  - Eliminacja przy CV ≤ 0 → token usuwany.
  - Przyznanie VP równych `price` za zniszczenie wroga, odejmowanie VP przegranemu (`_award_vp_for_elimination`).
  - AI może wyzwolić taktyczne uzupełnienie (`tactical_resupply`), gdy CV spada poniżej 60% i obrażenia ≥ 3.
- **Skutki po walce**:
  - Atakujący zużywa wszystkie MP.
  - `ActionResult` zwraca szczegółowe dane do logów (pozostałe CV, parametry starcia).

---

## 6. Ekonomia i key pointy
- **Ekonomia gracza** (`core/ekonomia.EconomySystem`):
  - `generate_economic_points()` dodaje 1–100 PE na turę (dla każdego ekonomicznego źródła).
  - `add_special_points()` dodaje 1 punkt specjalny.
  - `subtract_points()` blokuje zejście poniżej 0 PE.
- **Key pointy** (`GameEngine.process_key_points`):
  - Wartość początkowa i bieżąca przechowywana w `GameEngine.key_points_state`.
  - Tylko jednostka **Zaopatrzenie (Z)** stojąca na hexie zbiera PE dla generała.
  - Co pełną turę (koniec doby) przydziela 10% wartości początkowej (min 1), redukując `current_value`.
  - Po wyczerpaniu (value ≤ 0) punkt jest usuwany z mapy (`_save_key_points_to_map`).
  - Logi zapisują szczegóły: okupant, ilość PE, pozostała wartość KP.

---

## 7. Warunki zwycięstwa
- **Klasa `VictoryConditions` (`core/zwyciestwo.py`)**:
  - Tryb `turns`: gra kończy się po przekroczeniu `max_turns` (domyślnie 30). Zwycięzca ustalany na podstawie sumy VP per naród.
  - Tryb `elimination`: monitoruje żywe jednostki per naród (`Player.has_living_units`). Gra kończy się, gdy tylko jedna nacja ma aktywne jednostki.
  - `get_victory_info()` zwraca `winner_nation`, `victory_reason`, aktualny tryb.

---

## 8. Zachowanie AI: Niemcy
- **Hierarchia (`ai/README.md`)**:
  - `GeneralAI`:
    - Zarządza ekonomią przez `EconomySystem` (rezerwa adaptacyjna 10–20%).
    - Buduje profil dowódców (liczba żetonów, minimalne koszty aktywacji).
    - Rozdziela pozostałe PE proporcjonalnie do zapotrzebowania.
  - `CommanderAI`:
    - Synchronizuje `player.economy` z systemem ekonomii.
    - Dzieli budżet po równo między posiadane żetony.
    - Uruchamia `TokenAI` dla każdego żetonu i zbiera raporty.
    - Zwraca niewykorzystane PE po turze.
  - `TokenAI`:
    - Klasyfikuje stan żetonu (`normal`, `low_fuel`, `threatened`, `urgent_retreat`).
    - Priorytetyzuje ruch w stronę zagrożeń lub celów specjalistów; może uzupełniać paliwo w trakcie marszu.
    - Wykonuje pojedynczy atak, gdy przeciwnik w zasięgu i heurystyki na to pozwalają.
    - Zużywa pozostały budżet na paliwo / `combat_value` i raportuje niewykorzystane PE.
  - System logów AI (`ai/logs/`) rejestruje wszystkie decyzje (warstwa general, commander, token).
- **Doktryna Niemiec** (`TOKEN_BALANCING_GUIDE.md`):
  - `quality_bias` +0.02, `attack_bonus` +3%, `combat_bonus` +2%. Zapewnia przewagę ogniową w porównaniu z Polską.
- **Specjalne procedury**:
  - `GameEngine.ai_enemy_memory` przechowuje widziane jednostki przeciwnika (sightings) i wygasza je w `_decay_enemy_memory()`.
  - `CombatResolver._check_post_damage_resupply` może wyzwolić `CommanderAI.tactical_resupply` po poważnych stratach.

---

## 9. Dane mapy i startowe ustawienia
- **Mapa (`data/map_data.json`)**:
  - `meta`: heksy (pointy-top), 56 kolumn, 40 wierszy, `hex_size` 30.
  - `terrain`: każdy hex ma `move_mod` i `defense_mod` wpływające na ruch i obronę.
  - `spawn_points`: zestawy startowych hexów per nacja (Polska, Niemcy) – używane przy konfiguracji startowej.
  - `key_points`: definicje punktów strategicznych (typ, wartość startowa). Aktualny stan synchronizowany z `key_points_state`.
- **Żetony startowe**:
  - Wczytywane z `tokens_index.json` oraz `start_tokens.json` (przez `engine.token.load_tokens`).
  - Każdy żeton zawiera `unitType`, `unitSize`, `price`, ścieżkę grafiki i dodatkowe metadane (`unit_full_name`).

---

## 10. Co musi zawierać model przeciwnika (AI Niemcy)
Aby wiernie opisać drugiego gracza, reprezentacja powinna przechowywać i aktualizować następujące elementy:

1. **Stan globalny**
   - Numer tury (`GameEngine.turn`) i bieżącą fazę dnia (`TurnManager.get_current_day_phase`).
   - Aktualną pogodę (`TurnManager.current_weather`).
   - Wykaz aktywnych key pointów z bieżącą wartością.

2. **Ekonomia**
   - `EconomySystem.economic_points`, `special_points`, `assigned_points` dla generała niemieckiego.
   - Zapisy przydziałów PE z key pointów (wartość, hex, okupant).

3. **Jednostki AI**
   - Pełen stan każdego żetonu: pozycja `(q, r)`, `currentMovePoints`, `currentFuel`, `combat_value`, `movement_mode`, flagi artylerii (`shots_fired_this_turn`, `reaction_shot_used`).
   - Historia ruchu oraz ostatnio wykryte cele (przez `VisionService` i `ai_enemy_memory`).
   - Przynależność do dowódcy (właściciel `"ID (Niemcy)"`).

4. **Widoczność**
   - `visible_hexes`, `visible_tokens`, `temp_visible_token_data` (z `detection_level`).
   - Rozróżnienie widoczności generała (suma dowódców) i poszczególnych dowódców.

5. **Statystyki potyczek**
   - Rezultaty ostatnich walk (obrażenia, ewentualne odskoki, przyznane VP) – dostępne w `CombatResolver` i logach.
   - Zdarzenia wymagające resupply.

6. **Warunki zwycięstwa**
   - Monitorowanie VP (`Player.victory_points`, `vp_history`).
   - Liczbę żywych jednostek na potrzeby trybu eliminacji.

7. **Parametry balansowe**
   - Dostęp do `compute_token()` (dla oceny nowych zakupów) z uwzględnieniem doktryny niemieckiej.
   - Znajomość kosztów ulepszeń i możliwych upgrade'ów (np. `obserwator`, `drużyna granatników`).

---

## 11. Zalecany przepływ aktualizacji reprezentacji
1. **Początek tury AI**
   - Wywołać `TurnManager.get_turn_info()` → zaktualizować fazę dnia i pogodę.
   - Zresetować dynamiczne wskaźniki (MP, limity artylerii) zgodnie z `GameEngine.next_turn`.
   - Przeliczyć mgłę wojny (`update_all_players_visibility`).

2. **Faza generała**
   - Uaktualnić `EconomySystem` (dodanie PE, punktów specjalnych).
   - Zarejestrować przydziały PE do dowódców na podstawie logów `GeneralAI`.

3. **Faza dowódców / TokenAI**
   - Dla każdego żetonu aktualizować trasę ruchu, zużycie paliwa i wykrycia (`VisionService`).
   - Po akcji bojowej zaktualizować `combat_value`, ewentualne eliminacje oraz VP.
   - Przechwycić wywołania `tactical_resupply`, które mogą zmienić paliwo / CV.

4. **Koniec pełnej doby**
   - Uruchomić `GameEngine.process_key_points` – raporty przyznanych PE i aktualizacja `key_points_state`.
   - Sprawdzić warunki zwycięstwa (`VictoryConditions.check_game_over`).

---

## 12. Kluczowe pliki referencyjne
| Obszar | Plik | Rola |
| --- | --- | --- |
| Silnik tury i ruch | `engine/action_refactored_clean.py` | Walidacja ruchu, kalkulacja kosztów, walka, limit artylerii |
| Jednostki | `engine/token.py` | Punkty ruchu, paliwo, tryby, limity artylerii |
| Plansza | `engine/board.py` | Dane terenu, pathfinding, dystanse |
| Widoczność | `engine/detection_filter.py` | Stopnie detekcji i zakres informacji |
| Ekonomia | `core/ekonomia.py` | Generacja, odejmowanie, specjalne PE |
| Pory dnia | `core/tura.py` & `core/pogoda.py` | Struktura tury, raport pogodowy |
| Key pointy | `engine/engine.py` (`process_key_points`) | Zbieranie PE przez Z, wygaszanie punktów |
| Warunki zwycięstwa | `core/zwyciestwo.py` | Tryby `turns` i `elimination` |
| Balans jednostek | `docs/TOKEN_BALANCING_GUIDE.md`, `balance/model.py` | Statystyki + doktryny narodów |
| Zachowanie AI | `ai/README.md`, `ai/general/*`, `ai/commander/*`, `ai/tokens/*` | Alokacja PE, heurystyki, resupply |

---

## 13. Notatki implementacyjne
- Reprezentacja AI powinna przewidywać **częściową wiedzę** o jednostkach polskich: przechowuj zarówno potwierdzone dane (`info_quality = FULL`), jak i oszacowania (`estimate_range`, `estimate_unit_type`).
- Monitoruj **stan paliwa i MP** – brak paliwa uniemożliwia ruch, nawet jeśli AI przydzieliła MP.
- W systemie artylerii przechowuj flagi `shots_fired_this_turn` i `reaction_shot_used` per żeton, aby kontrolować dostępność ognia.
- Przy aktualizacji VP uwzględniaj 
  - zdobyte punkty z eliminacji,
  - przyznane VP za scenariusz (jeśli w przyszłości dodane),
  - historię w `Player.vp_history` dla raportów końcowych.
- Specjaliści AI (np. `SupplySpecialist`) mogą modyfikować zachowanie standardowego `TokenAI`; jeśli reprezentacja ma odzwierciedlać planowanie AI, zapisz przypisane role specjalistów.

---

## 14. Podsumowanie
Wdrożenie reprezentacji przeciwnika AI (Niemcy) wymaga synchronizacji danych z wielu warstw gry: od ekonomii i pór dnia, przez szczegóły ruchu, aż po heurystyki AI oraz filtrowanie informacji o przeciwniku. Niniejszy dokument stanowi kompletną bazę wiedzy, potrzebną do stworzenia wiernego modelu drugiego gracza, który reaguje na sytuację na polu bitwy, zarządza zasobami, stosuje ograniczenia artylerii i pogodowo-czasowe oraz podejmuje decyzje bojowe zgodnie z zaimplementowanymi zasadami silnika "Kampania 1939".
