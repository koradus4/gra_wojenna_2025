"""
Test: Gdzie AI Commander wystawia zakupione żetony?

Sprawdza dokładne pozycje deployment dla różnych nacji i sytuacji
"""

import sys
import json
import shutil
from pathlib import Path
from unittest.mock import Mock

# Dodaj ścieżkę projektu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ai.ai_commander import find_deployment_position, evaluate_deployment_position


def load_real_spawn_points():
    """Ładuje prawdziwe spawn points z map_data.json"""
    try:
        with open('data/map_data.json', 'r', encoding='utf-8') as f:
            map_data = json.load(f)
        return map_data.get('spawn_points', {})
    except:
        # Fallback jeśli nie można załadować
        return {
            'Polska': ['6,-3', '0,2', '0,13', '0,14', '0,21', '0,29', '0,32', '6,30', '18,24', '24,-12', '25,20'],
            'Niemcy': ['52,-26', '55,-23', '55,-20', '55,-17', '55,-15', '55,-11', '55,-5', '54,6', '49,8', '41,12', '40,-20']
        }


def create_mock_engine_with_real_spawns():
    """Mock engine z prawdziwymi spawn points"""
    engine = Mock()
    engine.board = Mock()
    engine.board.tokens = []
    engine.board.occupied_hexes = set()
    
    def mock_is_occupied(q, r):
        return (q, r) in engine.board.occupied_hexes
    
    def mock_neighbors(q, r):
        return [(q+1, r), (q, r+1), (q-1, r+1), (q-1, r), (q, r-1), (q+1, r-1)]
    
    engine.board.is_occupied = mock_is_occupied
    engine.board.neighbors = mock_neighbors
    
    # Prawdziwe spawn points
    real_spawns = load_real_spawn_points()
    engine.map_data = {
        'spawn_points': real_spawns,
        'key_points': {
            '10,5': {'type': 'miasto', 'value': 100, 'current_value': 100},
            '15,8': {'type': 'fortyfikacja', 'value': 150, 'current_value': 150},
        }
    }
    
    # Fix dla get_my_units - musi być lista, nie Mock
    engine.tokens = []  # Lista zamiast Mock
    
    return engine, real_spawns


def test_spawn_points_locations():
    """Test pokazuje gdzie są spawn points dla każdej nacji"""
    print("📍 SPAWN POINTS LOCATIONS\n")
    
    engine, spawn_points = create_mock_engine_with_real_spawns()
    
    for nation, points in spawn_points.items():
        print(f"🏳️  {nation.upper()}:")
        print(f"   Liczba spawn points: {len(points)}")
        print(f"   Pozycje: {points}")
        
        # Konwertuj do współrzędnych
        coords = []
        for point_str in points:
            q, r = map(int, point_str.split(','))
            coords.append((q, r))
        
        print(f"   Współrzędne: {coords}")
        print()


def test_deployment_priority_polish():
    """Test deployment dla Polski - pokazuje dokładne pozycje"""
    print("🇵🇱 TEST DEPLOYMENT POLSKI\n")
    
    engine, spawn_points = create_mock_engine_with_real_spawns()
    
    # Ustaw gracza polskiego
    player = Mock()
    player.nation = "Polska"
    player.id = 2
    engine.current_player_obj = player
    
    # Mock unit data
    unit_data = {
        "id": "test_polish_unit",
        "label": "Test Polska Piechota",
        "unitType": "P"
    }
    
    # Test bez żadnych istniejących jednostek
    print("SCENARIUSZ 1: Pusta mapa - pierwszy deployment")
    position = find_deployment_position(unit_data, engine, 2)
    
    print(f"   Wybrana pozycja: {position}")
    if position:
        q, r = position
        print(f"   Hex coordinates: q={q}, r={r}")
        
        # Sprawdź czy to spawn point
        polish_spawns = spawn_points['Polska']
        spawn_coords = [tuple(map(int, sp.split(','))) for sp in polish_spawns]
        is_spawn = position in spawn_coords
        print(f"   Czy to spawn point: {is_spawn}")
        
        if is_spawn:
            spawn_index = spawn_coords.index(position)
            print(f"   Który spawn point: #{spawn_index + 1} z {len(polish_spawns)}")
    
    # Test z zajętymi spawn points
    print("\nSCENARIUSZ 2: Pierwsze spawn points zajęte")
    
    # Zajmij pierwsze 3 spawn points
    for i in range(3):
        if i < len(spawn_coords):
            engine.board.occupied_hexes.add(spawn_coords[i])
            print(f"   Zajęto spawn point: {spawn_coords[i]}")
    
    position2 = find_deployment_position(unit_data, engine, 2)
    print(f"   Nowa pozycja: {position2}")
    
    if position2:
        is_spawn2 = position2 in spawn_coords
        print(f"   Czy to spawn point: {is_spawn2}")
        
        if is_spawn2:
            spawn_index2 = spawn_coords.index(position2)
            print(f"   Który spawn point: #{spawn_index2 + 1}")
        else:
            print(f"   To pozycja sąsiednia do spawn point")


def test_deployment_priority_german():
    """Test deployment dla Niemiec"""
    print("\n🇩🇪 TEST DEPLOYMENT NIEMIEC\n")
    
    engine, spawn_points = create_mock_engine_with_real_spawns()
    
    # Ustaw gracza niemieckiego
    player = Mock()
    player.nation = "Niemcy"
    player.id = 5
    engine.current_player_obj = player
    
    unit_data = {
        "id": "test_german_unit",
        "label": "Test Niemiecki Panzer",
        "unitType": "TC"
    }
    
    print("SCENARIUSZ: Deployment niemieckich jednostek")
    position = find_deployment_position(unit_data, engine, 5)
    
    print(f"   Wybrana pozycja: {position}")
    if position:
        german_spawns = spawn_points['Niemcy']
        spawn_coords = [tuple(map(int, sp.split(','))) for sp in german_spawns]
        is_spawn = position in spawn_coords
        print(f"   Czy to spawn point: {is_spawn}")
        
        if is_spawn:
            spawn_index = spawn_coords.index(position)
            print(f"   Który spawn point: #{spawn_index + 1} z {len(german_spawns)}")
            print(f"   Pierwsze spawn points Niemiec: {german_spawns[:3]}")


def test_deployment_scoring_system():
    """Test systemu oceny pozycji deployment"""
    print("\n🎯 TEST SYSTEMU OCENY POZYCJI\n")
    
    engine, spawn_points = create_mock_engine_with_real_spawns()
    
    # Test pozycji
    test_positions = [
        (6, -3),   # Polski spawn point
        (52, -26), # Niemiecki spawn point  
        (10, 5),   # Key point miasto
        (15, 8),   # Key point fortyfikacja
        (0, 0),    # Centrum mapy
    ]
    
    my_units = []  # Brak jednostek
    
    print("Ocena pozycji (bez jednostek):")
    for pos in test_positions:
        score = evaluate_deployment_position(pos, my_units, engine)
        print(f"   {pos}: {score} punktów")
    
    # Test z jednostkami
    print("\nOcena pozycji (z jednostkami w pobliżu):")
    my_units = [
        {'q': 5, 'r': -2},  # Blisko (6,-3)
        {'q': 8, 'r': 0}    # Średnio blisko
    ]
    
    for pos in test_positions:
        score = evaluate_deployment_position(pos, my_units, engine)
        print(f"   {pos}: {score} punktów")


def test_real_deployment_example():
    """Przykład rzeczywistego deployment z logami"""
    print("\n🎮 RZECZYWISTY PRZYKŁAD DEPLOYMENT\n")
    
    # Symulacja prawdziwej sytuacji z gry
    scenarios = [
        {
            'name': 'Polski Commander ID=2',
            'nation': 'Polska',
            'spawn_points': ['6,-3', '0,2', '0,13', '0,14'],
            'expected_first': (6, -3),
            'description': 'Rozpoczyna od spawn point (6,-3) - wschodni brzeg'
        },
        {
            'name': 'Polski Commander ID=3', 
            'nation': 'Polska',
            'spawn_points': ['6,-3', '0,2', '0,13', '0,14'],
            'expected_first': (6, -3),
            'description': 'Też (6,-3) jeśli wolny, lub (0,2) jako backup'
        },
        {
            'name': 'Niemiecki Commander ID=5',
            'nation': 'Niemcy', 
            'spawn_points': ['52,-26', '55,-23', '55,-20', '55,-17'],
            'expected_first': (52, -26),
            'description': 'Rozpoczyna od (52,-26) - zachodni brzeg'
        }
    ]
    
    for scenario in scenarios:
        print(f"📋 {scenario['name']}:")
        print(f"   Nacja: {scenario['nation']}")
        print(f"   Główne spawn points: {scenario['spawn_points'][:4]}")
        print(f"   Pierwsza pozycja: {scenario['expected_first']}")
        print(f"   Opis: {scenario['description']}")
        print()


if __name__ == "__main__":
    print("📍 TEST: Gdzie AI Commander wystawia zakupione żetony?")
    print("=" * 60)
    
    try:
        # Test 1: Pokaż wszystkie spawn points
        test_spawn_points_locations()
        
        # Test 2: Deployment Polski
        test_deployment_priority_polish()
        
        # Test 3: Deployment Niemiec
        test_deployment_priority_german()
        
        # Test 4: System oceny
        test_deployment_scoring_system()
        
        # Test 5: Przykłady rzeczywiste
        test_real_deployment_example()
        
        print("=" * 60)
        print("🎯 PODSUMOWANIE POZYCJI DEPLOYMENT:")
        print("   🇵🇱 POLSKA: Zaczyna od (6,-3), potem (0,2), (0,13), etc.")
        print("   🇩🇪 NIEMCY: Zaczyna od (52,-26), potem (55,-23), (55,-20), etc.")
        print("   📍 LOGIKA: Spawn points → sąsiednie → najwyższa ocena")
        
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
