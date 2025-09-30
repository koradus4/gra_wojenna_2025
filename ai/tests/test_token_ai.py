"""
Testy minimalnego TokenAI.
"""
from __future__ import annotations

from dataclasses import dataclass

from ai.tokens import TokenAI, create_token_ai


@dataclass
class DummyTile:
    move_mod: int = 0


class DummyBoard:
    def get_tile(self, q, r):
        return DummyTile()

    def neighbors(self, q, r):
        return [
            (q + 1, r),
            (q + 1, r - 1),
            (q, r - 1),
            (q - 1, r),
            (q - 1, r + 1),
            (q, r + 1),
        ]

    def hex_distance(self, a, b):
        aq, ar = a
        bq, br = b
        return int((abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) / 2)


class DummyEngine:
    def __init__(self, tokens):
        self.tokens = tokens
        self.board = DummyBoard()
        self.moves = []
        self.attacks = []

    def execute_action(self, action, player=None):
        token = next(t for t in self.tokens if t.id == getattr(action, "token_id", None))
        action_name = action.__class__.__name__
        if action_name == "MoveAction":
            dest = (action.dest_q, action.dest_r)
            token.q, token.r = dest
            token.currentMovePoints = max(0, token.currentMovePoints - 1)
            token.currentFuel = max(0, token.currentFuel - 1)
            self.moves.append(dest)
            return (True, "OK")
        if action_name == "CombatAction":
            self.attacks.append(action.defender_id)
            return (True, "OK")
        return (False, "Unknown action")


class DummyToken:
    def __init__(self, token_id, owner="1 (Polska)", q=0, r=0):
        self.id = token_id
        self.owner = owner
        self.q = q
        self.r = r
        self.maxMovePoints = 4
        self.currentMovePoints = 4
        self.maxFuel = 6
        self.currentFuel = 6
        self.stats = {
            "sight": 3,
            "attack": {"range": 1},
            "combat_value": 6,
            "nation": "Polska",
        }
        self.combat_value = 6

    def can_attack(self, attack_type):
        return True


def test_create_token_ai_returns_base_class():
    token = DummyToken("t1")
    ai = create_token_ai(token)
    assert isinstance(ai, TokenAI)


def test_execute_turn_spends_budget_on_resupply():
    token = DummyToken("t2")
    token.currentFuel = 3  # braki paliwa
    token.combat_value = 2  # braki CV
    token.currentMovePoints = 0  # brak ruchu, całość budżetu na uzupełnienia
    enemy = DummyToken("enemy", owner="2 (Niemcy)", q=3, r=0)
    engine = DummyEngine([token, enemy])

    ai = TokenAI(token)
    spent = ai.execute_turn(engine, player=None, pe_budget=5)

    assert spent == 5
    assert token.currentFuel == 6  # uzupełnione do max (3 braków)
    assert token.combat_value == 4  # pozostałe 2 punkty


def test_execute_turn_moves_when_possible():
    token = DummyToken("t3")
    enemy = DummyToken("enemy", owner="2 (Niemcy)", q=2, r=0)
    engine = DummyEngine([token, enemy])

    ai = TokenAI(token)
    ai.execute_turn(engine, player=None, pe_budget=0)

    assert engine.moves, "ruch powinien zostać wykonany"
    assert (token.q, token.r) != (0, 0)


def test_execute_turn_attacks_enemy_in_range():
    token = DummyToken("t4")
    enemy = DummyToken("enemy", owner="2 (Niemcy)", q=1, r=0)
    engine = DummyEngine([token, enemy])

    ai = TokenAI(token)
    ai.execute_turn(engine, player=None, pe_budget=0)

    assert "enemy" in engine.attacks