import pytest

from ai.tokens.token_ai import TokenAI
from engine.action_refactored_clean import MoveAction, CombatAction


class TileStub:
    def __init__(self, move_mod=0, defense_mod=0):
        self.move_mod = move_mod
        self.defense_mod = defense_mod


class BoardStub:
    def __init__(self, tiles=None):
        self.tiles = tiles or {}

    def neighbors(self, q, r):
        # axial directions
        directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        return [(q + dq, r + dr) for dq, dr in directions]

    def get_tile(self, q, r):
        return self.tiles.get((q, r), TileStub())

    @staticmethod
    def hex_distance(start, end):
        sq, sr = start
        eq, er = end
        return int((abs(sq - eq) + abs(sr - er) + abs((sq - sr) - (eq - er))) / 2)


class TokenStub:
    def __init__(self, token_id, nation, q=0, r=0, move=4, fuel=8, cv=8):
        self.id = token_id
        self.owner = f"{token_id} ({nation})"
        self.stats = {
            "move": move,
            "maintenance": fuel,
            "combat_value": cv,
            "attack": {"range": 1, "value": 5},
            "nation": nation,
        }
        self.q = q
        self.r = r
        self.maxMovePoints = move
        self.currentMovePoints = move
        self.maxFuel = fuel
        self.currentFuel = fuel
        self.combat_value = cv
        self.movement_mode_locked = True

    def set_position(self, q, r):
        self.q = q
        self.r = r

    def can_attack(self, _attack_type="normal"):
        return True

    def record_attack(self, _attack_type="normal"):
        return None

    def is_artillery(self):
        return False


class EngineStub:
    def __init__(self, board, tokens):
        self.board = board
        self.tokens = tokens
        self.move_calls = []
        self.attack_calls = 0

    def execute_action(self, action, player=None):
        if isinstance(action, MoveAction):
            token = next(tok for tok in self.tokens if tok.id == action.token_id)
            token.set_position(action.dest_q, action.dest_r)
            token.currentMovePoints = max(0, token.currentMovePoints - 1)
            token.currentFuel = max(0, token.currentFuel - 1)
            self.move_calls.append((token.id, (action.dest_q, action.dest_r)))
            return type(
                "Result",
                (),
                {
                    "success": True,
                    "message": "OK",
                    "data": {
                        "final_position": (action.dest_q, action.dest_r),
                        "remaining_mp": token.currentMovePoints,
                        "remaining_fuel": token.currentFuel,
                    },
                },
            )()
        if isinstance(action, CombatAction):
            self.attack_calls += 1
            return type(
                "CombatResult",
                (),
                {
                    "success": True,
                    "message": "OK",
                    "data": {
                        "combat_result": {
                            "attack_result": 1,
                            "defense_result": 0,
                            "can_counterattack": False,
                        },
                        "attacker_remaining": 5,
                        "defender_remaining": 4,
                    },
                },
            )()
        return type("Result", (), {"success": False, "message": "Unsupported"})()


class PlayerStub:
    def __init__(self, nation="NationA"):
        self.id = "Commander"
        self.nation = nation
        self.economy = type("Economy", (), {"economic_points": 0, "get_points": lambda self: {"economic_points": 0}})()


@pytest.fixture
def base_board():
    tiles = {
        (0, -1): TileStub(defense_mod=1),
        (1, 0): TileStub(),
        (1, -1): TileStub(move_mod=1),
    }
    return BoardStub(tiles)


def test_resupply_reaches_thresholds(base_board):
    token = TokenStub("T1", "NationA", q=0, r=0, move=3, fuel=10, cv=10)
    token.currentFuel = 2
    token.combat_value = 4
    enemy = TokenStub("E1", "NationB", q=5, r=5, move=3, fuel=8, cv=10)
    engine = EngineStub(base_board, [token, enemy])
    player = PlayerStub()

    ai = TokenAI(token)
    spent = ai.execute_turn(engine, player, pe_budget=8)

    assert spent >= 6
    assert token.currentFuel >= 6  # 60% paliwa
    assert token.combat_value >= 7  # 70% CV
    assert engine.attack_calls == 0


def test_attack_skipped_when_ratio_low(base_board):
    token = TokenStub("T2", "NationA", q=0, r=0, move=2, fuel=8, cv=8)
    token.currentMovePoints = 0
    enemy = TokenStub("E2", "NationB", q=1, r=0, move=2, fuel=8, cv=20)
    enemy.stats["combat_value"] = 20
    enemy.combat_value = 20
    engine = EngineStub(base_board, [token, enemy])
    player = PlayerStub()

    ai = TokenAI(token)
    spent = ai.execute_turn(engine, player, pe_budget=0)

    assert spent == 0
    assert engine.attack_calls == 0


def test_withdraw_moves_to_safer_hex(base_board):
    token = TokenStub("T3", "NationA", q=0, r=0, move=3, fuel=8, cv=10)
    token.combat_value = 2  # poniżej 30%
    enemy = TokenStub("E3", "NationB", q=1, r=0, move=3, fuel=8, cv=10)
    engine = EngineStub(base_board, [token, enemy])
    player = PlayerStub()

    ai = TokenAI(token)
    ai.execute_turn(engine, player, pe_budget=2)

    assert (token.q, token.r) != (0, 0)
    assert base_board.hex_distance((token.q, token.r), (enemy.q, enemy.r)) >= 1
