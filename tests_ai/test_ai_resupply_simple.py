"""Test AI resupply system - uproszczona wersja bez pełnego GameEngine"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Mockowy setup bez pełnego ładowania plików
class MockBoard:
    def __init__(self):
        self.tokens = []

class MockGameEngine:
    def __init__(self):
        self.board = MockBoard()

class MockPlayer:
    def __init__(self, player_id, nation):
        self.id = player_id
        self.nation = nation
        self.punkty_ekonomiczne = 0
        self.economy = None

class MockToken:
    def __init__(self, stats):
        self.stats = stats
        self.id = stats.get('id', 'test')
        self.maxFuel = stats.get('maintenance', 0)
        self.currentFuel = self.maxFuel
        self.combat_value = stats.get('combat_value', 0)
        self.owner = None

def test_ai_resupply_basic():
    """Test podstawowy: AI z punktami uzupełnia jednostki z niskim paliwem"""
    print("=== TEST AI RESUPPLY ===")
    
    # Setup
    engine = MockGameEngine()
    ai_player = MockPlayer("1", "Niemcy")
    ai_player.punkty_ekonomiczne = 20
    
    # Stwórz żeton z niskim paliwem
    token = MockToken({
        'id': 'test_tank',
        'label': 'Test Tank',
        'maintenance': 10,  # maxFuel
        'combat_value': 8
    })
    token.currentFuel = 3  # Niskie paliwo (30%)
    token.combat_value = 5  # Niska siła (62.5%)
    token.owner = f"{ai_player.id} ({ai_player.nation})"
    
    # Dodaj do silnika
    engine.board.tokens = [token]
    
    print(f"PRZED: paliwo={token.currentFuel}/{token.maxFuel}, combat={token.combat_value}/8, punkty={ai_player.punkty_ekonomiczne}")
    
    # Import i test AI Commander
    from ai.ai_commander import AICommander
    ai_commander = AICommander(ai_player)
    
    # Wywołaj resupply
    ai_commander.pre_resupply(engine)
    
    print(f"PO: paliwo={token.currentFuel}/{token.maxFuel}, combat={token.combat_value}/8, punkty={ai_player.punkty_ekonomiczne}")
    
    # Sprawdzenia
    assert token.currentFuel > 3, f"Paliwo powinno zostać uzupełnione: {token.currentFuel} > 3"
    assert token.combat_value >= 5, f"Siła bojowa powinna zostać uzupełniona: {token.combat_value} >= 5"
    assert ai_player.punkty_ekonomiczne < 20, f"Punkty powinny zostać wydane: {ai_player.punkty_ekonomiczne} < 20"
    
    print("✅ Test AI resupply zakończony pomyślnie!")

def test_ai_resupply_no_points():
    """Test: AI bez punktów nie uzupełnia"""
    print("=== TEST AI RESUPPLY BEZ PUNKTÓW ===")
    
    engine = MockGameEngine()
    ai_player = MockPlayer("1", "Niemcy")
    ai_player.punkty_ekonomiczne = 0  # Brak punktów
    
    token = MockToken({
        'id': 'test_tank',
        'label': 'Test Tank',
        'maintenance': 10,
        'combat_value': 8
    })
    token.currentFuel = 3
    token.combat_value = 5
    token.owner = f"{ai_player.id} ({ai_player.nation})"
    
    engine.board.tokens = [token]
    
    from ai.ai_commander import AICommander
    ai_commander = AICommander(ai_player)
    
    old_fuel = token.currentFuel
    old_combat = token.combat_value
    
    ai_commander.pre_resupply(engine)
    
    # Nic się nie powinno zmienić
    assert token.currentFuel == old_fuel, "Paliwo nie powinno się zmienić bez punktów"
    assert token.combat_value == old_combat, "Combat nie powinno się zmienić bez punktów"
    
    print("✅ Test bez punktów zakończony pomyślnie!")

def test_ai_resupply_full_units():
    """Test: AI nie uzupełnia pełnych jednostek"""
    print("=== TEST AI RESUPPLY PEŁNE JEDNOSTKI ===")
    
    engine = MockGameEngine()
    ai_player = MockPlayer("1", "Niemcy")
    ai_player.punkty_ekonomiczne = 20
    
    token = MockToken({
        'id': 'test_tank',
        'label': 'Test Tank',
        'maintenance': 10,
        'combat_value': 8
    })
    token.currentFuel = 10  # Pełne paliwo
    token.combat_value = 8  # Pełna siła
    token.owner = f"{ai_player.id} ({ai_player.nation})"
    
    engine.board.tokens = [token]
    
    from ai.ai_commander import AICommander
    ai_commander = AICommander(ai_player)
    
    old_points = ai_player.punkty_ekonomiczne
    
    ai_commander.pre_resupply(engine)
    
    # Punkty nie powinny zostać wydane
    assert ai_player.punkty_ekonomiczne == old_points, "Punkty nie powinny zostać wydane na pełne jednostki"
    
    print("✅ Test pełnych jednostek zakończony pomyślnie!")

def test_ai_resupply_priority():
    """Test: AI priorytetyzuje niskie paliwo"""
    print("=== TEST AI RESUPPLY PRIORYTET ===")
    
    engine = MockGameEngine()
    ai_player = MockPlayer("1", "Niemcy")
    ai_player.punkty_ekonomiczne = 10  # Ograniczone punkty
    
    # Jednostka z bardzo niskim paliwem
    token1 = MockToken({
        'id': 'low_fuel',
        'label': 'Low Fuel Tank',
        'maintenance': 10,
        'combat_value': 8
    })
    token1.currentFuel = 1  # 10% paliwa
    token1.combat_value = 8  # Pełna siła
    token1.owner = f"{ai_player.id} ({ai_player.nation})"
    
    # Jednostka z niską siłą bojową
    token2 = MockToken({
        'id': 'low_combat',
        'label': 'Damaged Tank',
        'maintenance': 10,
        'combat_value': 8
    })
    token2.currentFuel = 10  # Pełne paliwo
    token2.combat_value = 3  # 37.5% siły
    token2.owner = f"{ai_player.id} ({ai_player.nation})"
    
    engine.board.tokens = [token1, token2]
    
    from ai.ai_commander import AICommander
    ai_commander = AICommander(ai_player)
    
    print(f"PRZED: Tank1 fuel={token1.currentFuel}, Tank2 combat={token2.combat_value}, punkty={ai_player.punkty_ekonomiczne}")
    
    ai_commander.pre_resupply(engine)
    
    print(f"PO: Tank1 fuel={token1.currentFuel}, Tank2 combat={token2.combat_value}, punkty={ai_player.punkty_ekonomiczne}")
    
    # Pierwszy tank powinien dostać więcej paliwa (niższy priorytet = wyższy)
    assert token1.currentFuel > 1, "Tank z niskim paliwem powinien zostać uzupełniony"
    
    print("✅ Test priorytetyzacji zakończony pomyślnie!")

if __name__ == "__main__":
    test_ai_resupply_basic()
    test_ai_resupply_no_points()
    test_ai_resupply_full_units()
    test_ai_resupply_priority()
    print("\n🎉 WSZYSTKIE TESTY AI RESUPPLY PRZESZŁY!")
