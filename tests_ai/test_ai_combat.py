"""Test AI Combat System - sprawdź czy AI potrafi atakować wrogów"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Mockowy setup
class MockBoard:
    def __init__(self):
        self.tokens = []
    
    def hex_distance(self, pos1, pos2):
        """Uproszczona funkcja odległości hex"""
        q1, r1 = pos1
        q2, r2 = pos2
        return abs(q1 - q2) + abs(r1 - r2)
    
    def get_tile(self, q, r):
        """Mockowy tile z defense_mod"""
        class MockTile:
            def __init__(self):
                self.defense_mod = 1  # Podstawowy modyfikator terenu
        return MockTile()

class MockGameEngine:
    def __init__(self):
        self.board = MockBoard()
        self.tokens = []
        self.current_player_obj = None
    
    def execute_action(self, action):
        """Mock execute_action - symuluj sukces"""
        class MockResult:
            def __init__(self):
                self.success = True
                self.message = "Mock combat successful"
        return MockResult()

class MockPlayer:
    def __init__(self, player_id, nation):
        self.id = player_id
        self.nation = nation

class MockToken:
    def __init__(self, token_id, owner, q, r, attack_val=10, defense_val=5, combat_val=8):
        self.id = token_id
        self.owner = owner
        self.q = q
        self.r = r
        self.combat_value = combat_val
        self.stats = {
            'attack': {'value': attack_val, 'range': 2},
            'defense_value': defense_val
        }

def test_ai_find_enemies():
    """Test: AI znajduje wrogów w zasięgu"""
    print("=== TEST ZNAJDOWANIE WROGÓW ===")
    
    # Setup
    engine = MockGameEngine()
    player = MockPlayer("1", "Niemcy")
    engine.current_player_obj = player
    
    # Niemiecka jednostka
    german_token = MockToken("german_tank", "1 (Niemcy)", 5, 5, attack_val=12)
    german_unit = {
        'id': 'german_tank',
        'q': 5, 'r': 5,
        'mp': 3, 'fuel': 8,
        'token': german_token
    }
    
    # Polscy wrogowie
    polish_token1 = MockToken("polish_infantry", "2 (Polska)", 6, 5)  # W zasięgu (1 hex)
    polish_token2 = MockToken("polish_tank", "2 (Polska)", 8, 8)     # Poza zasięgiem (4 hexy)
    
    engine.tokens = [german_token, polish_token1, polish_token2]
    
    # Import funkcji
    from ai.ai_commander import find_enemies_in_range
    
    # Test
    enemies = find_enemies_in_range(german_unit, engine, "1")
    
    print(f"Znaleziono {len(enemies)} wrogów w zasięgu")
    assert len(enemies) == 1, f"Powinien znaleźć 1 wroga, znalazł {len(enemies)}"
    assert enemies[0]['id'] == 'polish_infantry', "Powinien znaleźć polish_infantry"
    
    print("✅ Test znajdowania wrogów zakończony pomyślnie!")

def test_ai_combat_ratio():
    """Test: AI oblicza stosunek sił"""
    print("=== TEST STOSUNEK SIŁ ===")
    
    # Silna niemiecka jednostka
    german_token = MockToken("german_tank", "1 (Niemcy)", 5, 5, attack_val=15, defense_val=8)
    german_unit = {
        'token': german_token
    }
    
    # Słaba polska jednostka
    polish_token = MockToken("polish_infantry", "2 (Polska)", 6, 5, attack_val=6, defense_val=3)
    polish_enemy = {
        'token': polish_token,
        'q': 6, 'r': 5
    }
    
    from ai.ai_commander import evaluate_combat_ratio
    
    ratio = evaluate_combat_ratio(german_unit, polish_enemy)
    
    print(f"Combat ratio: {ratio:.2f}")
    # Ratio = atak(15) / (obrona(3) + terrain(1)) = 15/4 = 3.75
    assert ratio > 3.0, f"Ratio powinno być > 3.0, jest {ratio:.2f}"
    assert ratio >= 1.3, "Ratio powinno przekraczać próg ataku (1.3)"
    
    print("✅ Test stosunku sił zakończony pomyślnie!")

def test_ai_combat_execution():
    """Test: AI wykonuje atak przez CombatAction"""
    print("=== TEST WYKONANIE ATAKU ===")
    
    # Setup
    engine = MockGameEngine()
    player = MockPlayer("1", "Niemcy")
    engine.current_player_obj = player
    
    # Jednostki
    german_token = MockToken("german_tank", "1 (Niemcy)", 5, 5, attack_val=15)
    german_unit = {
        'id': 'german_tank',
        'q': 5, 'r': 5,
        'token': german_token
    }
    
    polish_token = MockToken("polish_infantry", "2 (Polska)", 6, 5, defense_val=3)
    polish_enemy = {
        'id': 'polish_infantry',
        'q': 6, 'r': 5,
        'token': polish_token
    }
    
    from ai.ai_commander import execute_ai_combat
    
    # Test wykonania ataku
    success = execute_ai_combat(german_unit, polish_enemy, engine, "Niemcy")
    
    print(f"Atak wykonany: {success}")
    assert success, "Atak powinien się udać"
    
    print("✅ Test wykonania ataku zakończony pomyślnie!")

def test_ai_combat_integration():
    """Test: Pełna integracja - AI znajduje, ocenia i atakuje"""
    print("=== TEST INTEGRACJA COMBAT ===")
    
    # Setup kompletnej sceny bojowej
    engine = MockGameEngine()
    player = MockPlayer("1", "Niemcy")
    engine.current_player_obj = player
    
    # Niemiecka jednostka z dobrym atakiem
    german_token = MockToken("german_panzer", "1 (Niemcy)", 5, 5, attack_val=18, combat_val=10)
    german_unit = {
        'id': 'german_panzer',
        'q': 5, 'r': 5,
        'mp': 3, 'fuel': 8,
        'token': german_token
    }
    
    # Słaby polski wróg w zasięgu
    polish_token = MockToken("polish_infantry", "2 (Polska)", 6, 5, defense_val=4, combat_val=6)
    
    engine.tokens = [german_token, polish_token]
    
    from ai.ai_commander import ai_attempt_combat
    
    # Test pełnej procedury
    combat_happened = ai_attempt_combat(german_unit, engine, "1", "Niemcy")
    
    print(f"Próba ataku: {combat_happened}")
    assert combat_happened, "AI powinno zaatakować słabego wroga"
    
    print("✅ Test integracji combat zakończony pomyślnie!")

def test_ai_combat_no_good_targets():
    """Test: AI nie atakuje gdy brak dobrych celów"""
    print("=== TEST BRAK DOBRYCH CELÓW ===")
    
    engine = MockGameEngine()
    player = MockPlayer("1", "Niemcy")
    engine.current_player_obj = player
    
    # Słaba niemiecka jednostka
    german_token = MockToken("german_scout", "1 (Niemcy)", 5, 5, attack_val=4, combat_val=3)
    german_unit = {
        'id': 'german_scout',
        'q': 5, 'r': 5,
        'mp': 2, 'fuel': 5,
        'token': german_token
    }
    
    # Silny polski wróg (za mocny do ataku)
    polish_token = MockToken("polish_fortress", "2 (Polska)", 6, 5, defense_val=15, combat_val=20)
    
    engine.tokens = [german_token, polish_token]
    
    from ai.ai_commander import ai_attempt_combat
    
    # AI nie powinno atakować
    combat_happened = ai_attempt_combat(german_unit, engine, "1", "Niemcy")
    
    print(f"Próba ataku silnego wroga: {combat_happened}")
    assert not combat_happened, "AI nie powinno atakować za silnych wrogów"
    
    print("✅ Test braku dobrych celów zakończony pomyślnie!")

if __name__ == "__main__":
    test_ai_find_enemies()
    test_ai_combat_ratio()
    test_ai_combat_execution()
    test_ai_combat_integration()
    test_ai_combat_no_good_targets()
    print("\n🎉 WSZYSTKIE TESTY AI COMBAT PRZESZŁY!")
    print("⚔️ AI może teraz atakować wrogów w zasięgu")
    print("🧠 AI ocenia stosunek sił przed atakiem")
    print("🎯 AI wybiera najlepsze cele do eliminacji")
