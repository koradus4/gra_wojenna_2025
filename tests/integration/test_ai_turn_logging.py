import os
import csv
from pathlib import Path

# Zakładamy że ai_commander.make_tactical_turn jest dostępny
from ai.ai_commander import make_tactical_turn

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
        self.tokens = []
        self.key_points_state = {}
        self.board = DummyBoard()
        self.current_player_obj = DummyPlayer()
        self.turn_number = 1
        self.players = [self.current_player_obj]
        self.map_data = {'key_points': {}}
    def save_state(self, path):
        pass


def test_turn_logging_creates_columns(tmp_path, monkeypatch):
    # Przekieruj katalog logów do temp
    logs_dir = tmp_path / 'logs' / 'ai_commander'
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Monkeypatch ścieżek w module logowania
    from ai import logowanie_ai
    logowanie_ai.LOG_DIR = logs_dir
    logowanie_ai.LOG_FILE = logs_dir / 'actions_test.csv'
    logowanie_ai.TURN_LOG_FILE = logs_dir / 'turns_test.csv'

    engine = DummyEngine()

    # Uruchom turę (powinna być bez crashu na pustych danych)
    make_tactical_turn(engine, player_id=engine.current_player_obj.id)

    # Sprawdź pliki i kolumny
    assert logowanie_ai.LOG_FILE.exists(), 'Brak pliku actions CSV'
    assert logowanie_ai.TURN_LOG_FILE.exists(), 'Brak pliku turns CSV'

    with open(logowanie_ai.LOG_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert 'skip_reason' in header, 'Brak kolumny skip_reason w actions'

    with open(logowanie_ai.TURN_LOG_FILE, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for col in ['casualties_turn','new_units_turn']:
            assert col in header, f'Brak kolumny {col} w turns'
