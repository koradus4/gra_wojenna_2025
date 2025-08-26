"""Test AI resupply system - sprawdź czy AI potrafi uzupełniać jednostki"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from engine.engine import GameEngine
from engine.player import Player
from engine.token import Token

def test_ai_resupply_basic():
    """Test podstawowy: AI z punktami uzupełnia jednostki z niskim paliwem"""
    print("=== TEST AI RESUPPLY ===")
    
    # Setup z wymaganymi parametrami
    engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens",
        tokens_start_path="assets/start_tokens.json"
    )
    ai_player = Player("1", "Niemcy")
    ai_player.punkty_ekonomiczne = 20
    
    # Stwórz żeton z niskim paliwem
    token = Token({
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
    assert token.currentFuel > 3, "Paliwo powinno zostać uzupełnione"
    assert token.combat_value >= 5, "Siła bojowa powinna zostać uzupełniona"
    assert ai_player.punkty_ekonomiczne < 20, "Punkty powinny zostać wydane"
    
    print("✅ Test AI resupply zakończony pomyślnie!")

def test_ai_resupply_no_points():
    """Test: AI bez punktów nie uzupełnia"""
    print("=== TEST AI RESUPPLY BEZ PUNKTÓW ===")
    
    engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens",
        tokens_start_path="assets/start_tokens.json"
    )
    ai_player = Player("1", "Niemcy")
    ai_player.punkty_ekonomiczne = 0  # Brak punktów
    
    token = Token({
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
    
    engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens",
        tokens_start_path="assets/start_tokens.json"
    )
    ai_player = Player("1", "Niemcy")
    ai_player.punkty_ekonomiczne = 20
    
    token = Token({
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

if __name__ == "__main__":
    test_ai_resupply_basic()
    test_ai_resupply_no_points()
    test_ai_resupply_full_units()
    print("\n🎉 WSZYSTKIE TESTY AI RESUPPLY PRZESZŁY!")
