"""Test progresywnego celu ruchu na PRAWDZIWYCH danych mapy.

Używamy realnego pliku `data/map_data.json`, żeby zweryfikować:
1. Zwrócony heks jest osiągalny w ramach mp/fuel.
2. Nowa pozycja przybliża do final_target (mniejszy dystans heksowy) – jeśli ruch możliwy.
3. Brak MP/FUEL powoduje pozostanie w miejscu.
"""

from ai.ruch_postepowy_ai import calculate_progressive_target
from engine.board import Board

# --- Wspólny stub silnika z prawdziwą planszą ---
class StubEngine:
    def __init__(self):
        self.board = Board("data/map_data.json")

ENGINE = StubEngine()

def _distance(a, b):
    return ENGINE.board.hex_distance(a, b)

def test_progressive_target_real_map_advances():
    unit = {"id": "U1", "q": 2, "r": 2, "mp": 6, "fuel": 6}
    final_target = (20, 15)
    start_pos = (unit['q'], unit['r'])
    result = calculate_progressive_target(unit, final_target, ENGINE)
    assert isinstance(result, tuple) and len(result) == 2
    # Powinien istnieć path w limicie MP/FUEL (chyba że brak ruchu – wtedy równy start_pos)
    if result != start_pos:
        path = ENGINE.board.find_path(start_pos, result, max_mp=unit['mp'], max_fuel=unit['fuel'])
        assert path and len(path) - 1 <= unit['mp']
        assert _distance(result, final_target) < _distance(start_pos, final_target)

def test_progressive_target_no_resources_stays():
    unit = {"id": "U2", "q": 5, "r": 5, "mp": 0, "fuel": 0}
    final_target = (10, 12)
    result = calculate_progressive_target(unit, final_target, ENGINE)
    assert result == (unit['q'], unit['r'])

def test_progressive_target_limited_progress():
    unit = {"id": "U3", "q": 3, "r": 10, "mp": 2, "fuel": 2}
    final_target = (15, 25)
    start_pos = (unit['q'], unit['r'])
    result = calculate_progressive_target(unit, final_target, ENGINE)
    # Może się zdarzyć, że brak sensownego progresu (teren / rzeki) – wtedy zostanie na miejscu.
    if result != start_pos:
        assert _distance(result, final_target) < _distance(start_pos, final_target)
        path = ENGINE.board.find_path(start_pos, result, max_mp=unit['mp'], max_fuel=unit['fuel'])
        assert path and len(path) - 1 <= unit['mp']
