# AI Testing Documentation

## Przegląd Testów

System testów AI składa się z trzech głównych kategorii:
- **Unit Tests** - Testowanie pojedynczych funkcji
- **Integration Tests** - Testowanie współpracy modułów
- **Full Defense Tests** - Kompleksowe scenariusze obronne

## Struktura Testów

```
tests/
├── ai/
│   ├── test_defensive_ai.py      # Testy jednostkowe AI defensywnego
│   ├── test_deployment.py        # Testy deployment jednostek
│   └── test_full_defense.py      # Testy integracyjne obrony
└── [inne testy...]
```

## Unit Tests (test_defensive_ai.py)

### Klasa TestDefensiveAI

#### `test_assess_defensive_threats()`
Testuje funkcję oceny zagrożeń defensywnych.

**Test Coverage:**
- ✅ Wykrywanie wrogów w zasięgu 6 hex
- ✅ Kalkulacja poziomów zagrożenia
- ✅ Identyfikacja najbliższych punktów bezpieczeństwa
- ✅ Obsługa pustej listy jednostek

**Przykładowy Test:**
```python
def test_assess_defensive_threats(self):
    # Symulacja jednostek i wrogów
    my_units = [{'id': 'unit1', 'q': 5, 'r': 5, 'combat_value': 3}]
    enemy_units = [{'id': 'enemy1', 'q': 3, 'r': 4, 'combat_value': 5}]
    
    # Mock engine
    mock_engine = Mock()
    mock_engine.board.tokens = {
        'enemy1': create_mock_token('enemy1', 3, 4, 2)  # player_id=2 = wróg
    }
    
    # Test
    threats = assess_defensive_threats(my_units, mock_engine)
    
    # Assertions
    assert 'unit1' in threats
    assert threats['unit1']['threat_level'] == 5
    assert len(threats['unit1']['threatening_enemies']) == 1
```

#### `test_plan_defensive_retreat()`
Testuje planowanie kontrolowanego odwrotu.

**Test Coverage:**
- ✅ Wybór optymalnych pozycji odwrotu
- ✅ Kierowanie do punktów kluczowych
- ✅ Unikanie wrogów podczas odwrotu
- ✅ Obsługa kolizji pozycji

#### `test_calculate_hex_distance()`
Testuje obliczenia dystansu hexagonalnego.

**Test Cases:**
```python
# Test dystansów
assert calculate_hex_distance((0, 0), (1, 0)) == 1
assert calculate_hex_distance((0, 0), (3, 3)) == 6
assert calculate_hex_distance((5, 5), (2, 3)) == 4
```

#### `test_defensive_coordination()`
Testuje koordynację defensywną wokół punktów kluczowych.

**Test Coverage:**
- ✅ Grupowanie jednostek wokół key points
- ✅ Przydziały ról w grupach
- ✅ Optymalizacja pokrycia defensywnego

## Deployment Tests (test_deployment.py)

### Klasa TestDeployment

#### `test_deploy_purchased_units()`
Testuje wdrażanie zakupionych jednostek.

**Setup:**
```python
def setUp(self):
    # Tworzy test_file z jednostkami
    self.test_file = f"nowe_dla_Polska_{int(time.time())}.json"
    test_units = [{
        "id": "new_unit_1",
        "label": "Test Pluton",
        "stats": {
            "unit_type": "P",
            "size": "Pluton",
            "combat_value": 3,
            "maintenance": 1,
            "movement": 4
        }
    }]
    
    with open(self.test_file, 'w', encoding='utf-8') as f:
        json.dump(test_units, f, ensure_ascii=False, indent=2)
```

**Test Coverage:**
- ✅ Odczyt plików JSON z jednostkami
- ✅ Znajdowanie spawn points
- ✅ Tworzenie tokenów w grze
- ✅ Usuwanie plików po deployment
- ✅ Obsługa błędów (brak spawn points, nieprawidłowy JSON)

#### `test_find_spawn_points()`
Testuje algorytm znajdowania punktów spawn.

**Kryteria Spawn Points:**
1. Pozycja kontrolowana przez gracza
2. Brak kolizji z istniejącymi jednostkami
3. Dostęp do sieci komunikacyjnej
4. Minimalna odległość od wrogów (3 hex)

#### `test_deployment_validation()`
Testuje walidację wdrożonych jednostek.

**Validation Checks:**
- ✅ Jednostka ma prawidłowe ID
- ✅ Stats są zgodne z JSON
- ✅ Pozycja jest w spawn points
- ✅ Token jest dodany do engine

## Integration Tests (test_full_defense.py)

### Klasa TestFullDefense

#### `test_complete_defensive_scenario()`
Kompleksowy test scenariusza defensywnego.

**Scenariusz:**
```
Runda 1: Atak polski na pozycje niemieckie
- AI ocenia zagrożenie
- Planuje odwrót kontrolowany
- Wdraża nowe jednostki
- Wykonuje koordynację defensywną

Walidacja:
- Zagrożone jednostki się wycofują
- Nowe jednostki są wdrożone
- Grupy defensywne są utworzone
- Key points są bronione
```

#### `test_full_ai_turn_defensive()`
Test pełnej tury AI z elementami defensywnymi.

**Fazy Turu:**
1. **COMBAT PHASE** - Ataki na priorytetowe cele
2. **DEFENSIVE PHASE** - Ocena i reakcja na zagrożenia
3. **DEPLOYMENT PHASE** - Wdrożenie zakupionych jednostek
4. **MOVEMENT PHASE** - Ruch pozostałych jednostek

**Metryki Sukcesu:**
- Threat detection rate: 100%
- Retreat success rate: ≥90%
- Deployment rate: 100%
- Key point coverage: ≥80%

#### `test_multi_turn_defensive_persistence()`
Test persistencji strategii defensywnej przez wiele tur.

**Test na 5 turach:**
- Tura 1: Początkowa pozycja defensywna
- Tura 2: Reakcja na presję wroga
- Tura 3: Kontratak lokalny
- Tura 4: Umocnienie pozycji
- Tura 5: Stabilizacja linii frontu

## Mock Objects

### MockEngine
```python
class MockEngine:
    def __init__(self):
        self.board = MockBoard()
        self.current_player_obj = MockPlayer()
        self.action_log = []
    
    def execute_action(self, action_type, params):
        self.action_log.append((action_type, params))
        return True
```

### MockBoard
```python
class MockBoard:
    def __init__(self):
        self.tokens = {}
        self.hexes = self._create_test_map()
    
    def get_neighbors(self, q, r):
        return [(q+1, r), (q-1, r), (q, r+1), (q, r-1), (q+1, r-1), (q-1, r+1)]
```

### MockToken
```python
def create_mock_token(token_id, q, r, player_id, combat_value=3):
    token = Mock()
    token.id = token_id
    token.q, token.r = q, r
    token.player_id = player_id
    token.stats = {'combat_value': combat_value, 'movement': 4, 'fuel': 10}
    return token
```

## Uruchamianie Testów

### Pojedyncze Testy
```bash
# Unit tests defensywy
python -m pytest tests/ai/test_defensive_ai.py -v

# Testy deployment
python -m pytest tests/ai/test_deployment.py -v

# Testy integracyjne
python -m pytest tests/ai/test_full_defense.py -v
```

### Wszystkie Testy AI
```bash
python -m pytest tests/ai/ -v
```

### Z Coverage
```bash
python -m pytest tests/ai/ --cov=ai --cov-report=html
```

## Przykładowe Wyniki

### Test Output
```
tests/ai/test_defensive_ai.py::TestDefensiveAI::test_assess_defensive_threats PASSED
tests/ai/test_defensive_ai.py::TestDefensiveAI::test_plan_defensive_retreat PASSED
tests/ai/test_defensive_ai.py::TestDefensiveAI::test_calculate_hex_distance PASSED
tests/ai/test_defensive_ai.py::TestDefensiveAI::test_defensive_coordination PASSED

tests/ai/test_deployment.py::TestDeployment::test_deploy_purchased_units PASSED
tests/ai/test_deployment.py::TestDeployment::test_find_spawn_points PASSED
tests/ai/test_deployment.py::TestDeployment::test_deployment_validation PASSED

tests/ai/test_full_defense.py::TestFullDefense::test_complete_defensive_scenario PASSED
tests/ai/test_full_defense.py::TestFullDefense::test_full_ai_turn_defensive PASSED
tests/ai/test_full_defense.py::TestFullDefense::test_multi_turn_defensive_persistence PASSED

=========================== 10 passed, 0 failed ===========================
```

### Coverage Report
```
Name                        Stmts   Miss  Cover
-----------------------------------------------
ai/ai_commander.py            245     12    95%
ai/ai_general.py               89      8    91%
-----------------------------------------------
TOTAL                         334     20    94%
```

## Debugging Testów

### Verbose Output
```python
# W testach używaj print dla debug
def test_assess_defensive_threats(self):
    print(f"\n🔧 Testing threat assessment...")
    threats = assess_defensive_threats(my_units, mock_engine)
    print(f"🔧 Found {len(threats)} threats")
    
    assert 'unit1' in threats
    print(f"✅ Threat assessment passed")
```

### Test Data Inspection
```python
# Zapisuj test data do analizy
def test_deployment_with_data_dump(self):
    result = deploy_purchased_units(mock_engine, player_id=1)
    
    # Zapisz wyniki do pliku
    with open('test_deployment_result.json', 'w') as f:
        json.dump({
            'deployed_count': result,
            'engine_tokens': len(mock_engine.board.tokens),
            'action_log': mock_engine.action_log
        }, f, indent=2)
```

## Integracja z CI/CD

### GitHub Actions
```yaml
name: AI Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt pytest pytest-cov
      - name: Run AI tests
        run: pytest tests/ai/ --cov=ai --cov-fail-under=90
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "Running AI tests..."
python -m pytest tests/ai/ -x
if [ $? -ne 0 ]; then
    echo "❌ AI tests failed. Commit aborted."
    exit 1
fi
echo "✅ AI tests passed."
```

## Benchmarking

### Performance Tests
```python
import time
import statistics

def benchmark_defensive_ai():
    """Benchmark dla funkcji defensywnych AI"""
    times = []
    
    for _ in range(100):
        start = time.time()
        assess_defensive_threats(sample_units, mock_engine)
        end = time.time()
        times.append(end - start)
    
    print(f"Średni czas: {statistics.mean(times):.4f}s")
    print(f"Mediana: {statistics.median(times):.4f}s")
    print(f"Max: {max(times):.4f}s")
```

### Memory Profiling
```python
import tracemalloc

def profile_ai_memory():
    tracemalloc.start()
    
    # Wykonaj AI funkcje
    make_tactical_turn(mock_engine, player_id=1)
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory: {current / 1024 / 1024:.1f} MB")
    print(f"Peak memory: {peak / 1024 / 1024:.1f} MB")
    tracemalloc.stop()
```

## Aktualizacje Testów

### Dodawanie Nowych Testów
1. Stwórz nową metodę `test_*` w odpowiedniej klasie
2. Dodaj mock objects jeśli potrzebne
3. Napisz assertions sprawdzające funkcjonalność
4. Uruchom test i sprawdź czy przechodzi
5. Dodaj test do dokumentacji

### Utrzymanie Testów
- Aktualizuj testy przy zmianach w AI
- Dodawaj nowe edge cases
- Monitoruj coverage i dąż do >90%
- Regularnie uruchamiaj performance benchmarks
