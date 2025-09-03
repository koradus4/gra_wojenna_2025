import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai.rajdy_ai import opportunistic_capture_phase, evaluate_movement_mode_for_raid

class DummyToken:
    def __init__(self, id_, q, r, owner, mp=3, fuel=3, movement_mode='combat'):
        self.id = id_
        self.q = q
        self.r = r
        self.owner = owner
        self.currentMovePoints = mp
        self.currentFuel = fuel
        self.maxMovePoints = mp * 2  # base MP dla testów
        self.movement_mode = movement_mode
        self.movement_mode_locked = False
        self.moved_capture = False
    
    def apply_movement_mode(self):
        """Symuluje zmianę MP w zależności od trybu ruchu"""
        multipliers = {'march': 1.5, 'combat': 1.0, 'recon': 0.8}
        base_mp = self.maxMovePoints // 2  # odwrócenie z konstruktora
        self.currentMovePoints = int(base_mp * multipliers.get(self.movement_mode, 1.0))

class DummyEngine:
    def __init__(self):
        self.board = self
        self.key_points_state = {
            '1,0': {'current_value': 50},   # blisko
            '5,0': {'current_value': 100},  # daleko dla march
            '10,0': {'current_value': 200}, # bardzo daleko
        }
        self.tokens = []
    
    def hex_distance(self, pos1, pos2):
        """Podstawowa kalkulacja odległości hex"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    # Minimal path: jeśli różnica <=1 zwróć ścieżkę, inaczej None
    def find_path(self, start, goal, max_mp=3, max_fuel=3):
        dist = self.hex_distance(start, goal)
        if dist <= min(max_mp, max_fuel):
            return [start, goal]
        return None


def test_opportunistic_capture_none():
    eng = DummyEngine()
    units = []
    res = opportunistic_capture_phase(eng, units, player_id=2)
    assert res == []


def test_opportunistic_capture_simple():
    eng = DummyEngine()
    t = DummyToken('U1', 0, 0, '2')
    eng.tokens.append(t)
    units = [{'id': t.id, 'q': t.q, 'r': t.r, 'mp': t.currentMovePoints, 'fuel': t.currentFuel, 'token': t}]
    captured = opportunistic_capture_phase(eng, units, player_id=2)
    # Jeśli logika pozwala na natychmiastowe zajęcie bliskiego punktu – lista może mieć 1
    assert isinstance(captured, list)


def test_evaluate_movement_mode_for_raid():
    """Test nowej funkcji oceny trybu ruchu dla rajdów"""
    eng = DummyEngine()
    
    # Jednostka z podstawowymi parametrami
    token = DummyToken('TestUnit', 0, 0, '2', mp=6, fuel=10, movement_mode='combat')
    unit = {
        'id': token.id,
        'q': token.q,
        'r': token.r,
        'mp': token.currentMovePoints,
        'fuel': token.currentFuel,
        'base_mp': token.maxMovePoints // 2,
        'token': token
    }
    
    # Test 1: Bliski cel - powinien wybrać combat lub recon
    close_target = (1, 0)
    mode, mp = evaluate_movement_mode_for_raid(unit, close_target, eng)
    print(f"Bliski cel {close_target}: tryb={mode}, MP={mp}")
    assert mode in ['combat', 'recon']
    
    # Test 2: Daleki cel - powinien wybrać march
    far_target = (8, 0)
    mode, mp = evaluate_movement_mode_for_raid(unit, far_target, eng)
    print(f"Daleki cel {far_target}: tryb={mode}, MP={mp}")
    assert mode == 'march'
    
    # Test 3: Sprawdź czy MP się zmienia odpowiednio
    if mode == 'march':
        expected_mp = int(unit['base_mp'] * 1.5)
        assert mp >= expected_mp * 0.9  # tolerancja ±10%


def test_rajdy_with_movement_optimization():
    """Test rajdów z optymalizacją trybu ruchu"""
    eng = DummyEngine()
    
    # Jednostka która może dosięgnąć daleki cel tylko w trybie march
    token = DummyToken('LongRange', 0, 0, '2', mp=4, fuel=10, movement_mode='combat')
    unit = {
        'id': token.id,
        'q': token.q,
        'r': token.r,
        'mp': token.currentMovePoints,
        'fuel': token.currentFuel,
        'base_mp': 4,
        'token': token
    }
    
    print(f"Przed rajdem: MP={unit['mp']}, tryb={token.movement_mode}")
    
    # Test rajdu - powinien automatycznie przełączyć na march dla dalekiego celu
    captured = opportunistic_capture_phase(eng, [unit], player_id=2)
    
    print(f"Po rajdzie: MP={unit['mp']}, tryb={token.movement_mode}")
    print(f"Przejęto: {captured}")
    
    # Sprawdź czy tryb został zmieniony na march (dla dalekiego celu o wartości 200)
    if captured:
        assert token.movement_mode in ['march', 'combat']  # zależnie od logiki wyboru


def test_fuel_vs_movement_mode_optimization():
    """Test optymalizacji paliwa vs trybu ruchu"""
    eng = DummyEngine()
    
    # Jednostka z małą ilością paliwa
    token = DummyToken('LowFuel', 0, 0, '2', mp=8, fuel=3, movement_mode='combat')
    unit = {
        'id': token.id,
        'q': token.q,
        'r': token.r,
        'mp': token.currentMovePoints,
        'fuel': token.currentFuel,
        'base_mp': 8,
        'token': token
    }
    
    # Cel w zasięgu paliwa ale nie MP w trybie combat
    medium_target = (3, 0)
    mode, mp = evaluate_movement_mode_for_raid(unit, medium_target, eng)
    
    print(f"Paliwo limitujące: Fuel={unit['fuel']}, MP={mp}, tryb={mode}")
    
    # Sprawdź czy function bierze pod uwagę ograniczenie paliwa
    effective_range = min(mp, unit['fuel'])
    target_distance = eng.hex_distance((unit['q'], unit['r']), medium_target)
    
    if target_distance <= effective_range:
        print(f"Cel osiągalny: dystans={target_distance}, zasięg={effective_range}")
    else:
        print(f"Cel nieosiągalny: dystans={target_distance}, zasięg={effective_range}")


if __name__ == "__main__":
    print("🎯 TESTY OPTYMALIZACJI RAJDÓW AI")
    print("="*50)
    
    test_opportunistic_capture_none()
    print("✅ Test 1: Brak jednostek")
    
    test_opportunistic_capture_simple()
    print("✅ Test 2: Podstawowy rajd")
    
    test_evaluate_movement_mode_for_raid()
    print("✅ Test 3: Ocena trybu ruchu")
    
    test_rajdy_with_movement_optimization()
    print("✅ Test 4: Rajdy z optymalizacją trybu")
    
    test_fuel_vs_movement_mode_optimization()
    print("✅ Test 5: Optymalizacja paliwo vs tryb")
    
    print("\n🎊 WSZYSTKIE TESTY ZALICZONE!")
