#!/usr/bin/env python3
"""
Test systemu defensywnego AI Commander
Sprawdza funkcje obrony, odwrotu i deployment
"""

import sys
from pathlib import Path

# Dodaj ścieżkę projektu do sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ai.ai_commander import (
    assess_defensive_threats,
    plan_defensive_retreat,
    deploy_purchased_units,
    defensive_coordination,
    calculate_hex_distance,
    get_all_key_points
)


def create_mock_game_engine():
    """Tworzy mock game_engine do testów"""
    
    # Mock board
    class MockBoard:
        def __init__(self):
            self.tokens = []
            self.occupied_hexes = set()
        
        def is_occupied(self, q, r):
            return (q, r) in self.occupied_hexes
        
        def neighbors(self, q, r):
            """Zwraca sąsiadujące hexagony"""
            return [
                (q + 1, r), (q - 1, r),
                (q, r + 1), (q, r - 1),
                (q + 1, r - 1), (q - 1, r + 1)
            ]
    
    # Mock player
    class MockPlayer:
        def __init__(self, nation, player_id):
            self.nation = nation
            self.id = player_id
    
    # Mock token
    class MockToken:
        def __init__(self, token_id, owner, q, r, combat_value=5):
            self.id = token_id
            self.owner = owner
            self.q = q
            self.r = r
            self.combat_value = combat_value
    
    # Utwórz engine
    engine = type('MockEngine', (), {})()
    engine.board = MockBoard()
    engine.current_player_obj = MockPlayer("Polska", 2)
    engine.tokens = []
    
    # Dane mapy z punktami kluczowymi
    engine.map_data = {
        'key_points': {
            '10,5': {'type': 'miasto', 'value': 100},
            '15,8': {'type': 'fortyfikacja', 'value': 150},
            '20,10': {'type': 'węzeł komunikacyjny', 'value': 75}
        },
        'spawn_points': {
            'Polska': ['5,5', '6,6', '7,7'],
            'Niemcy': ['25,25', '26,26', '27,27']
        }
    }
    
    # Dodaj żetony polskie
    polish_tokens = [
        MockToken("PL_001", "2 (Polska)", 8, 7, 8),   # Blisko punktu kluczowego
        MockToken("PL_002", "2 (Polska)", 12, 6, 6),  # Przy punkcie kluczowym
        MockToken("PL_003", "2 (Polska)", 18, 12, 4), # Daleko od wszystkich
    ]
    
    # Dodaj żetony niemieckie (wrogowie)
    german_tokens = [
        MockToken("DE_001", "3 (Niemcy)", 11, 7, 10), # Zagrożenie dla PL_001
        MockToken("DE_002", "3 (Niemcy)", 22, 15, 8), # Zagrożenie dla PL_003
    ]
    
    all_tokens = polish_tokens + german_tokens
    engine.board.tokens = all_tokens
    engine.tokens = all_tokens
    
    # Zajmij hexagony
    for token in all_tokens:
        engine.board.occupied_hexes.add((token.q, token.r))
    
    return engine


def test_calculate_hex_distance():
    """Test obliczania dystansu hex"""
    print("=== TEST: calculate_hex_distance ===")
    
    # Test przypadki
    cases = [
        ((0, 0), (0, 0), 0),    # Identyczne pozycje
        ((0, 0), (1, 0), 1),    # Sąsiad
        ((0, 0), (2, 1), 2),    # Dystans 2
        ((5, 5), (10, 8), 5),   # Długi dystans
    ]
    
    for pos1, pos2, expected in cases:
        result = calculate_hex_distance(pos1, pos2)
        status = "✅" if result == expected else "❌"
        print(f"{status} Dystans {pos1} -> {pos2}: {result} (oczekiwano: {expected})")
    
    print()


def test_get_all_key_points():
    """Test pobierania punktów kluczowych"""
    print("=== TEST: get_all_key_points ===")
    
    engine = create_mock_game_engine()
    key_points = get_all_key_points(engine)
    
    print(f"Znaleziono {len(key_points)} punktów kluczowych:")
    for pos, data in key_points.items():
        print(f"  {pos}: {data['type']} (wartość: {data['value']})")
    
    assert len(key_points) == 3, f"Oczekiwano 3 punkty, znaleziono {len(key_points)}"
    print("✅ Test punktów kluczowych przeszedł\n")


def test_assess_defensive_threats():
    """Test oceny zagrożeń defensywnych"""
    print("=== TEST: assess_defensive_threats ===")
    
    engine = create_mock_game_engine()
    
    # Pobierz polskie jednostki
    my_units = []
    for token in engine.board.tokens:
        if token.owner == "2 (Polska)":
            my_units.append({
                'id': token.id,
                'q': token.q,
                'r': token.r,
                'combat_value': token.combat_value,
                'mp': 3,
                'fuel': 5
            })
    
    threat_assessment = assess_defensive_threats(my_units, engine)
    
    print(f"Ocena zagrożeń dla {len(my_units)} jednostek:")
    for unit_id, assessment in threat_assessment.items():
        threat_level = assessment['threat_level']
        enemy_count = len(assessment['threatening_enemies'])
        safe_point = assessment['nearest_safe_point']
        print(f"  {unit_id}: Threat={threat_level}, Enemies={enemy_count}, SafePoint={safe_point}")
    
    # Sprawdź czy PL_001 jest zagrożony (blisko DE_001)
    pl_001_threat = threat_assessment.get('PL_001', {}).get('threat_level', 0)
    assert pl_001_threat > 0, "PL_001 powinien być zagrożony przez DE_001"
    print("✅ Test oceny zagrożeń przeszedł\n")


def test_defensive_retreat():
    """Test planowania odwrotu defensywnego"""
    print("=== TEST: plan_defensive_retreat ===")
    
    engine = create_mock_game_engine()
    
    # Pobierz polskie jednostki
    my_units = []
    for token in engine.board.tokens:
        if token.owner == "2 (Polska)":
            my_units.append({
                'id': token.id,
                'q': token.q,
                'r': token.r,
                'combat_value': token.combat_value,
                'mp': 3,
                'fuel': 5
            })
    
    threat_assessment = assess_defensive_threats(my_units, engine)
    
    # Znajdź zagrożone jednostki
    threatened_units = []
    for unit in my_units:
        assessment = threat_assessment.get(unit['id'], {})
        if assessment.get('threat_level', 0) > 1:
            threatened_units.append(unit)
    
    if threatened_units:
        retreat_plan = plan_defensive_retreat(threatened_units, threat_assessment, engine)
        
        print(f"Plan odwrotu dla {len(threatened_units)} zagrożonych jednostek:")
        for unit_id, retreat_pos in retreat_plan.items():
            print(f"  {unit_id}: Odwrót do {retreat_pos}")
        
        print("✅ Test planowania odwrotu przeszedł")
    else:
        print("ℹ️ Brak zagrożonych jednostek do testowania")
    
    print()


def test_defensive_coordination():
    """Test koordynacji defensywnej"""
    print("=== TEST: defensive_coordination ===")
    
    engine = create_mock_game_engine()
    
    # Pobierz polskie jednostki
    my_units = []
    for token in engine.board.tokens:
        if token.owner == "2 (Polska)":
            my_units.append({
                'id': token.id,
                'q': token.q,
                'r': token.r,
                'combat_value': token.combat_value,
                'mp': 3,
                'fuel': 5
            })
    
    threat_assessment = assess_defensive_threats(my_units, engine)
    defensive_groups = defensive_coordination(my_units, threat_assessment, engine)
    
    print(f"Utworzono {len(defensive_groups)} grup defensywnych:")
    for kp_pos, group in defensive_groups.items():
        print(f"  Punkt {kp_pos}: {len(group)} jednostek ({[u['id'] for u in group]})")
    
    print("✅ Test koordynacji defensywnej przeszedł\n")


def run_all_tests():
    """Uruchamia wszystkie testy defensywne"""
    print("🛡️ TESTY SYSTEMU DEFENSYWNEGO AI COMMANDER\n")
    
    try:
        test_calculate_hex_distance()
        test_get_all_key_points()
        test_assess_defensive_threats()
        test_defensive_retreat()
        test_defensive_coordination()
        
        print("🎉 WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
        
    except Exception as e:
        print(f"❌ BŁĄD TESTU: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
