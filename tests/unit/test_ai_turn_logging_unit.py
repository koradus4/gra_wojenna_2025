from pathlib import Path
import csv
from ai.ai_commander import make_tactical_turn

class DummyToken:
    def __init__(self, id_='T1', owner='2 (TestNation)'):
        self.id = id_
        self.owner = owner
        self.q = 0
        self.r = 0
        self.currentMovePoints = 0
        self.currentFuel = 5
        self.combat_value = 5
        self.stats = {'combat_value':5}
        def is_artillery():
            return False
        self.is_artillery = is_artillery
        def apply_movement_mode(reset_mp=True):
            pass
        self.apply_movement_mode = apply_movement_mode

class DummyPlayer:
    def __init__(self, pid=2, nation="TestNation"):
        self.id = pid
        self.nation = nation
        self.economy = type('econ', (), {'get_points': lambda self: {'last_turn_income': 10}})()
        self.visible_tokens = set()
        self.is_ai_commander = True

class DummyBoard:
    def hex_distance(self, a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])
    def get_tile(self, q, r):
        return type('tile', (), {})()
    def is_occupied(self, q, r):
        return False
    def neighbors(self, q, r):
        return []
    def set_tokens(self, tokens):
        pass

class DummyEngine:
    def __init__(self):
        self.tokens = [DummyToken()]
        self.key_points_state = {}
        self.board = DummyBoard()
        self.current_player_obj = DummyPlayer()
        self.turn_number = 1
        self.players = [self.current_player_obj]
        self.map_data = {'key_points': {}}
    def save_state(self, path):
        pass


def test_turn_logging_unit(tmp_path, monkeypatch):
    # Patch log paths
    from ai import logowanie_ai
    logowanie_ai.LOG_DIR = tmp_path / 'logs' / 'ai_commander'
    logowanie_ai.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logowanie_ai.LOG_FILE = logowanie_ai.LOG_DIR / 'actions_test.csv'
    logowanie_ai.TURN_LOG_FILE = logowanie_ai.LOG_DIR / 'turns_test.csv'

    engine = DummyEngine()
    make_tactical_turn(engine, player_id=engine.current_player_obj.id)

    assert logowanie_ai.LOG_FILE.exists()
    # jeśli brak units_total>0 może nie być turn summary; zapewniamy jednostkę więc powinno być
    assert logowanie_ai.TURN_LOG_FILE.exists()

    with open(logowanie_ai.LOG_FILE, 'r', encoding='utf-8') as f:
        header = next(csv.reader(f))
        assert 'skip_reason' in header

    with open(logowanie_ai.TURN_LOG_FILE, 'r', encoding='utf-8') as f:
        header = next(csv.reader(f))
        assert 'casualties_turn' in header
        assert 'new_units_turn' in header
