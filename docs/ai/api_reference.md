# AI Commander API Documentation

## Przegląd

AI Commander to zaawansowany system sztucznej inteligencji do automatycznego zarządzania jednostkami w grze wojennej. System zawiera dwa główne komponenty: AI General (strategiczny) i AI Commander (taktyczny).

## Struktura Modułów

```
ai/
├── __init__.py
├── ai_general.py          # Strategiczny AI - zarządzanie ekonomią i zakupami
├── ai_commander.py        # Taktyczny AI - zarządzanie jednostkami
└── ai_commander_backup.py # Kopia zapasowa poprzedniej wersji
```

## AI Commander (Taktyczny)

### Klasa AICommander

```python
class AICommander:
    def __init__(self, player: Any)
    def pre_resupply(self, game_engine: Any) -> None
    def make_tactical_turn(self, game_engine: Any) -> None
    def receive_orders(self, orders_file_path=None, current_turn=1)
```

### Główne Funkcje

#### `make_tactical_turn(game_engine, player_id=None)`
Główna funkcja wykonująca turę taktyczną AI.

**Parametry:**
- `game_engine`: Instancja silnika gry
- `player_id`: ID gracza (opcjonalne, auto-detect)

**Fazy tury:**
1. **COMBAT PHASE** - Wykonanie ataków
2. **FAZA DEFENSYWNA** - Ocena zagrożeń i odwrót
3. **FAZA DEPLOYMENT** - Wdrażanie zakupionych jednostek
4. **FAZA RUCHU** - Ruch pozostałych jednostek

#### `get_my_units(game_engine, player_id)`
Pobiera jednostki gracza z silnika gry.

**Zwraca:**
```python
[{
    'id': str,
    'q': int, 'r': int,  # Pozycja hex
    'combat_value': int,
    'mp': int,           # Movement points
    'fuel': int,
    'token': Token       # Referencja do obiektu
}]
```

### Funkcje Defensywne

#### `assess_defensive_threats(my_units, game_engine)`
Ocenia zagrożenia defensywne dla jednostek.

**Parametry:**
- `my_units`: Lista jednostek gracza
- `game_engine`: Silnik gry

**Zwraca:**
```python
{
    unit_id: {
        'threat_level': int,              # Poziom zagrożenia
        'threatening_enemies': list,      # Lista wrogów w pobliżu
        'nearest_safe_point': tuple,      # Najbliższy punkt bezpieczeństwa
        'safe_point_distance': int        # Dystans do punktu bezpieczeństwa
    }
}
```

#### `plan_defensive_retreat(threatened_units, threat_assessment, game_engine)`
Planuje kontrolowany odwrót zagrożonych jednostek.

**Parametry:**
- `threatened_units`: Lista zagrożonych jednostek
- `threat_assessment`: Wynik assess_defensive_threats
- `game_engine`: Silnik gry

**Zwraca:**
```python
{unit_id: retreat_position}  # Mapa jednostka -> pozycja odwrotu
```

#### `deploy_purchased_units(game_engine, player_id)`
Wdraża zakupione jednostki do gry.

**Parametry:**
- `game_engine`: Silnik gry
- `player_id`: ID gracza

**Zwraca:**
- `int`: Liczba wdrożonych jednostek

**Proces:**
1. Skanuje pliki `nowe_dla_{nation}_*.json`
2. Dla każdej jednostki znajduje optymalną pozycję
3. Tworzy token i dodaje do gry
4. Usuwa plik po deployment

#### `defensive_coordination(my_units, threat_assessment, game_engine)`
Koordynuje obronę wokół punktów kluczowych.

**Zwraca:**
```python
{
    key_point_position: [units]  # Grupy jednostek dla każdego punktu
}
```

### Funkcje Pomocnicze

#### `calculate_hex_distance(pos1, pos2)`
Oblicza dystans między pozycjami hex.

```python
def calculate_hex_distance(pos1, pos2):
    q1, r1 = pos1
    q2, r2 = pos2
    return max(abs(q1 - q2), abs(r1 - r2), abs((q1 + r1) - (q2 + r2)))
```

#### `get_all_key_points(game_engine)`
Pobiera wszystkie punkty kluczowe z mapy.

**Zwraca:**
```python
{
    (q, r): {
        'type': str,     # 'miasto', 'fortyfikacja', 'węzeł komunikacyjny'
        'value': int     # Wartość punktów
    }
}
```

#### `find_target(unit, game_engine)`
Znajduje cel dla jednostki (punkty kluczowe, wrogowie).

#### `can_move(unit)`
Sprawdza czy jednostka może się poruszać.

**Zwraca:**
- `bool`: True jeśli unit ma MP > 0 i fuel > 0

#### `move_towards(unit, target, game_engine)`
Wykonuje ruch jednostki w kierunku celu.

**Parametry:**
- `unit`: Słownik z danymi jednostki
- `target`: Pozycja docelowa (q, r) lub lista
- `game_engine`: Silnik gry

**Zwraca:**
- `bool`: True jeśli ruch się udał

### Zaawansowane Funkcje

#### `advanced_autonomous_mode(my_units, game_engine)`
Zaawansowany tryb autonomiczny z grupowaniem adaptacyjnym.

**Algorytm:**
1. Priorytetyzuje cele według wartości i dystansu
2. Grupuje jednostki adaptacyjnie (3-5 jednostek)
3. Przydziela cele grupom
4. Koordynuje ruch

#### `prioritize_targets(game_engine)`
Priorytetyzuje cele dla AI.

**Zwraca:**
```python
[{
    'position': tuple,
    'type': str,
    'value': int,
    'priority_score': float
}]
```

#### `adaptive_grouping(units, target_count)`
Adaptacyjne grupowanie jednostek.

**Parametry:**
- `units`: Lista jednostek
- `target_count`: Liczba celów

**Zwraca:**
```python
[{
    'group': [units],
    'leader': unit,
    'target': position,
    'distance': int
}]
```

### Logowanie

#### `log_commander_action(unit_id, action_type, from_pos, to_pos, reason, player_nation)`
Loguje akcje AI Commander do pliku CSV.

**Parametry:**
- `unit_id`: ID jednostki
- `action_type`: Typ akcji ('move', 'combat', 'retreat', etc.)
- `from_pos`: Pozycja początkowa
- `to_pos`: Pozycja końcowa  
- `reason`: Powód akcji
- `player_nation`: Nacja gracza

## AI General (Strategiczny)

### Funkcje Główne

#### Zarządzanie Ekonomią
- Monitorowanie punktów ekonomicznych
- Optymalizacja zakupów jednostek
- Planowanie strategiczne

#### Wydawanie Rozkazów
- Tworzenie plików z rozkazami strategicznymi
- Koordynacja między dowódcami
- Planowanie długoterminowe

## Konfiguracja

### Pliki Konfiguracyjne

#### `data/strategic_orders.json`
```json
{
    "orders": {
        "commander_id": {
            "mission_type": "ATTACK|DEFEND|SUPPORT",
            "target_hex": [q, r],
            "expires_turn": int,
            "status": "ACTIVE|COMPLETED|CANCELLED"
        }
    }
}
```

#### `nowe_dla_{nation}_{timestamp}.json`
```json
[{
    "id": "unit_id",
    "label": "Unit Label", 
    "stats": {
        "unit_type": "P|K|TC|...",
        "size": "Pluton|Kompania|...",
        "combat_value": int,
        "maintenance": int,
        "movement": int
    }
}]
```

### Parametry Systemowe

```python
# Progi zagrożenia
THREAT_RETREAT_THRESHOLD = 5    # Poziom zagrożenia wymagający odwrotu
THREAT_RANGE = 6                # Zasięg skanowania wrogów (hex)
KEYPOINT_DEFENSE_RANGE = 2      # Zasięg obrony punktu kluczowego

# Grupowanie
MIN_GROUP_SIZE = 3              # Minimalny rozmiar grupy
MAX_GROUP_SIZE = 5              # Maksymalny rozmiar grupy
MAX_GROUP_DISTANCE = 8          # Maksymalny dystans w grupie

# Ruch
MAX_RETREAT_RANGE = 4           # Maksymalny zasięg odwrotu
PROGRESSIVE_MOVE_ENABLED = True # Włącz ruch progresywny
```

## Przykłady Użycia

### Podstawowe Użycie
```python
from ai.ai_commander import make_tactical_turn

# Wykonaj turę AI dla gracza
make_tactical_turn(game_engine, player_id=2)
```

### Użycie z Klasą
```python
from ai.ai_commander import AICommander

commander = AICommander(player)
commander.pre_resupply(game_engine)     # Uzupełnij jednostki
commander.make_tactical_turn(game_engine)  # Wykonaj turę
```

### Testowanie Defensywy
```python
from ai.ai_commander import assess_defensive_threats, plan_defensive_retreat

units = get_my_units(game_engine, player_id)
threats = assess_defensive_threats(units, game_engine)
threatened = [u for u in units if threats.get(u['id'], {}).get('threat_level', 0) > 5]

if threatened:
    retreat_plan = plan_defensive_retreat(threatened, threats, game_engine)
```

## Obsługa Błędów

### Typowe Problemy

#### Brak Jednostek
```python
if not my_units:
    print(f"[AI] Brak jednostek dla gracza {player_id}")
    return
```

#### Błędy Pathfinding
```python
try:
    success = move_towards(unit, target, game_engine)
    if not success:
        print(f"[AI] Ruch nieudany dla {unit['id']}")
except Exception as e:
    print(f"[AI] Błąd ruchu: {e}")
```

#### Brak Danych Mapy
```python
key_points = get_all_key_points(game_engine)
if not key_points:
    print("[AI] Brak punktów kluczowych - używam fallback strategy")
```

## Integracja

### Z Silnikiem Gry
AI Commander integruje się z głównym silnikiem przez:
- `game_engine.current_player_obj` - aktualny gracz
- `game_engine.board.tokens` - żetony na planszy
- `game_engine.execute_action()` - wykonywanie akcji

### Z GUI
- Automatyczne uruchamianie w trybie AI
- Logowanie do plików CSV
- Wyświetlanie postępu w konsoli

### Z Systemem Ekonomicznym
- Odczyt punktów ekonomicznych z `player.economy`
- Automatyczne uzupełnianie jednostek w `pre_resupply()`
- Deployment zakupionych jednostek

## Wydajność

### Optymalizacje
- Grupowanie jednostek redukuje złożoność obliczeniową
- Cache'owanie punktów kluczowych
- Progresywny ruch dla długich dystansów
- Collision avoidance w czasie rzeczywistym

### Metryki
- Średni czas tury: <1s dla 20 jednostek
- Skuteczność combat: ~70% trafień
- Efficiency deployment: 100% wykorzystanie spawn points

## Debugging

### Flagi Debug
```python
print(f"[AI] Debug info")           # Podstawowe info
print(f"🔧 [DEBUG] Detailed info")  # Szczegółowe debug
print(f"✅ [SUCCESS] Action completed")  # Sukces
print(f"❌ [ERROR] Action failed")   # Błąd
```

### Pliki Log
- `logs/ai_actions_{date}.csv` - Akcje AI Commander
- `logs/ai_purchases_{date}.csv` - Zakupy AI General
- `logs/actions_{datetime}.csv` - Wszystkie akcje gry
