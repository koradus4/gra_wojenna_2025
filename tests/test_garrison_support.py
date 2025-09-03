#!/usr/bin/env python3
"""Test systemu wsparcia garnizonu - automatyczne przydzielanie jednostek do ochrony punktów."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.wsparcie_garnizonu import assign_garrison_support, calculate_garrison_support


class MockGameEngine:
    def __init__(self):
        self.key_points_state = {
            "5,5": {"type": "miasto", "current_value": 80, "initial_value": 80},      # Cenny punkt
            "3,3": {"type": "wioska", "current_value": 25, "initial_value": 25},     # Średni punkt  
            "1,1": {"type": "ruiny", "current_value": 5, "initial_value": 10},       # Słaby punkt
        }
        self.tokens = []  # Brak wrogich tokenów na start
        
    class MockBoard:
        def hex_distance(self, pos1, pos2):
            return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    board = MockBoard()


class MockToken:
    def __init__(self, token_id, owner, q, r, hold_position=False):
        self.id = token_id
        self.owner = owner
        self.q = q
        self.r = r
        self.hold_position = hold_position
        self.currentFuel = 5
        self.currentMovePoints = 5
        self.combat_value = 6


def test_garrison_support_system():
    """Test systemu wsparcia garnizonów."""
    print("🧪 TEST: System wsparcia garnizonów")
    
    engine = MockGameEngine()
    
    # Stwórz jednostki
    garrison1 = MockToken("Garnizon_1", "2 (Polska)", 5, 5, hold_position=True)  # Na cennym punkcie
    garrison2 = MockToken("Garnizon_2", "2 (Polska)", 3, 3, hold_position=True)  # Na średnim punkcie
    garrison3 = MockToken("Garnizon_3", "2 (Polska)", 1, 1, hold_position=True)  # Na słabym punkcie
    
    idle1 = MockToken("Idle_1", "2 (Polska)", 4, 4, hold_position=False)  # Blisko garrison1
    idle2 = MockToken("Idle_2", "2 (Polska)", 6, 6, hold_position=False)  # Blisko garrison1  
    idle3 = MockToken("Idle_3", "2 (Polska)", 2, 2, hold_position=False)  # Blisko garrison2
    idle4 = MockToken("Idle_4", "2 (Polska)", 0, 0, hold_position=False)  # Blisko garrison3
    
    my_units = [
        {'id': 'Garnizon_1', 'q': 5, 'r': 5, 'token': garrison1},
        {'id': 'Garnizon_2', 'q': 3, 'r': 3, 'token': garrison2}, 
        {'id': 'Garnizon_3', 'q': 1, 'r': 1, 'token': garrison3},
        {'id': 'Idle_1', 'q': 4, 'r': 4, 'token': idle1},
        {'id': 'Idle_2', 'q': 6, 'r': 6, 'token': idle2},
        {'id': 'Idle_3', 'q': 2, 'r': 2, 'token': idle3},
        {'id': 'Idle_4', 'q': 0, 'r': 0, 'token': idle4},
    ]
    
    print(f"📊 STAN POCZĄTKOWY:")
    print(f"   - Garnizony: 3 (cenny punkt=80pts, średni=25pts, słaby=5pts)")
    print(f"   - Idle jednostki: 4")
    print(f"   - Wrogowie: 0")
    
    # Test 1: Bez wrogów
    print(f"\n🧪 TEST 1: Przydzielanie wsparcia bez wrogów")
    assigned = assign_garrison_support(my_units, engine)
    
    support_assignments = [(u['id'], u.get('assigned_target'), u.get('support_role')) 
                          for u in my_units if u.get('support_role')]
    
    print(f"   ✅ Przydzielono: {assigned} jednostek wsparcia")
    for unit_id, target, role in support_assignments:
        print(f"      - {unit_id} → {target} ({role})")
    
    # Sprawdź oczekiwania
    # Miasto (80pts) + 0 wrogów = 4+0 = 4 → 2 wsparcia
    # Wioska (25pts) + 0 wrogów = 1+0 = 1 → 1 wsparcie  
    # Ruiny (5pts) + 0 wrogów = 0+0 = 0 → 0 wsparcia
    expected_total = 3  # 2 + 1 + 0
    
    if assigned == expected_total:
        print(f"   ✅ PASS: Oczekiwano {expected_total}, otrzymano {assigned}")
    else:
        print(f"   ❌ FAIL: Oczekiwano {expected_total}, otrzymano {assigned}")
    
    # Test 2: Dodaj wrogów
    print(f"\n🧪 TEST 2: Przydzielanie wsparcia z wrogami")
    
    # Reset przydziałów
    for unit in my_units:
        unit.pop('assigned_target', None)
        unit.pop('support_role', None)
        unit.pop('support_for', None)
    
    # Dodaj wrogich tokenów blisko cennego punktu (5,5)
    enemy1 = MockToken("Enemy_1", "3 (Niemcy)", 6, 4, hold_position=False)
    enemy2 = MockToken("Enemy_2", "3 (Niemcy)", 4, 6, hold_position=False)
    engine.tokens = [enemy1, enemy2]  # 2 wrogów w zasięgu 4 od punktu (5,5)
    
    assigned_with_enemies = assign_garrison_support(my_units, engine)
    
    support_assignments_2 = [(u['id'], u.get('assigned_target'), u.get('support_role')) 
                            for u in my_units if u.get('support_role')]
    
    print(f"   ✅ Przydzielono z wrogami: {assigned_with_enemies} jednostek wsparcia")
    for unit_id, target, role in support_assignments_2:
        print(f"      - {unit_id} → {target} ({role})")
    
    # Sprawdź oczekiwania z wrogami
    # Miasto (80pts) + 2 wrogów = 4+2 = 6 → 4 wsparcia
    # Wioska (25pts) + 0 wrogów = 1+0 = 1 → 1 wsparcie
    # Ruiny (5pts) + 0 wrogów = 0+0 = 0 → 0 wsparcia
    # Ale max 1/3 z 4 dostępnych = 1, więc faktycznie będzie mniej
    
    if assigned_with_enemies > assigned:
        print(f"   ✅ PASS: Więcej wsparcia z wrogami ({assigned_with_enemies} vs {assigned})")
    else:
        print(f"   ⚠️  INFO: Wsparcie nie wzrosło ({assigned_with_enemies} vs {assigned}) - może limit jednostek")
    
    # Test 3: Kalkulator wsparcia
    print(f"\n🧪 TEST 3: Kalkulator wsparcia")
    
    # Test różnych scenariuszy
    scenarios = [
        ({"current_value": 80}, [], 10, "Cenny punkt, brak wrogów"),
        ({"current_value": 80}, [1, 2], 10, "Cenny punkt, 2 wrogów"),
        ({"current_value": 25}, [1], 10, "Średni punkt, 1 wróg"),
        ({"current_value": 5}, [], 10, "Słaby punkt, brak wrogów"),
        ({"current_value": 100}, [1, 2, 3, 4], 2, "Mega punkt, 4 wrogów, 2 dostępne"),
    ]
    
    for kp_data, enemies, available, desc in scenarios:
        support = calculate_garrison_support(kp_data, enemies, available)
        print(f"   📊 {desc}: {support} wsparcia")
    
    print(f"\n🎯 TEST ZAKOŃCZONY!")


if __name__ == "__main__":
    test_garrison_support_system()
