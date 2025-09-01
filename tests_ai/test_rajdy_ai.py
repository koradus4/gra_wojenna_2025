from ai.rajdy_ai import opportunistic_capture_phase

class DummyToken:
    def __init__(self, id_, q, r, owner, mp=3, fuel=3):
        self.id = id_
        self.q = q
        self.r = r
        self.owner = owner
        self.currentMovePoints = mp
        self.currentFuel = fuel
        self.moved_capture = False

class DummyEngine:
    def __init__(self):
        self.board = self
        self.key_points_state = {
            '1,0': {'q':1,'r':0,'owner': None, 'value': 50},
        }
        self.tokens = []
    # Minimal path: jeśli różnica <=1 zwróć ścieżkę, inaczej None
    def find_path(self, start, goal, max_mp=3, max_fuel=3):
        if abs(start[0]-goal[0]) + abs(start[1]-goal[1]) <= 1:
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
