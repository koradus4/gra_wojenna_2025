"""
Testy minimalnego TokenAI.
"""
from __future__ import annotations

from dataclasses import dataclass
import random

from ai.tokens import TokenAI, create_token_ai
from engine.action_refactored_clean import CombatResolver


@dataclass
class DummyTile:
    move_mod: int = 0
    defense_mod: int = 0


class DummyBoard:
    def __init__(self):
        self.key_points = {}

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


def make_supply_token(token_id="Z_test", q=0, r=0) -> DummyToken:
    token = DummyToken(token_id, q=q, r=r)
    token.stats["unitType"] = "Z"
    token.maxMovePoints = 6
    token.currentMovePoints = 6
    token.maxFuel = 6
    token.currentFuel = 6
    return token


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
    assert token.currentFuel == 5  # uzupełnione paliwo do 70% + reszta budżetu
    assert token.combat_value == 5  # pozostałe punkty na CV


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

    def fake_detection(engine, player, base_map=None):
        return {enemy.id: {"detection_level": 1.0, "distance": 1}}

    ai._collect_detection_map = fake_detection  # type: ignore[attr-defined]
    ai.execute_turn(engine, player=None, pe_budget=0)

    assert "enemy" in engine.attacks


def test_supply_specialist_moves_towards_assigned_key_point():
    token = make_supply_token()

    engine = DummyEngine([token])
    engine.board.key_points = {"0,3": {"value": 100}}
    target_hex = (0, 3)

    ai = create_token_ai(token)

    board = engine.board
    start_distance = board.hex_distance((token.q, token.r), target_hex)

    ai.execute_turn(engine, player=None, pe_budget=0)

    new_distance = board.hex_distance((token.q, token.r), target_hex)

    assert new_distance < start_distance, (
        f"Konwój powinien zbliżyć się do KP, dystans {new_distance} vs {start_distance}"
    )


def test_supply_specialist_does_not_add_withdraw_when_safe():
    token = make_supply_token("Z_safe")
    ai = create_token_ai(token)
    board = DummyBoard()
    context = {
        "position": (token.q, token.r),
        "current_fuel": token.currentFuel,
        "max_fuel": token.maxFuel,
        "danger_zones": {(token.q, token.r): 0},
        "visible_enemies": [],
        "supply_target_kp": (token.q, token.r + 1),
        "board": board,
    }
    planned_actions = ["refuel_minimum", "restore_cv", "attack", "maneuver"]

    adjusted = ai.specialist.adjust_actions(planned_actions, "normal", context, pe_budget=5)

    assert "attack" not in adjusted
    assert "withdraw" not in adjusted
    assert "maneuver" in adjusted


def test_supply_token_turn_after_forced_retreat(monkeypatch):
    class RetreatTile(DummyTile):
        pass

    class RetreatBoard(DummyBoard):
        def __init__(self, engine):
            super().__init__()
            self._engine = engine

        def get_tile(self, q, r):  # pragma: no cover - simple override
            return RetreatTile()

        def is_occupied(self, q, r):
            for tok in self._engine.tokens:
                if (tok.q, tok.r) == (q, r):
                    return True
            return False

    class SupplyToken:
        def __init__(self, token_id, owner, q=0, r=0):
            self.id = token_id
            self.owner = owner
            self.q = q
            self.r = r
            self.maxMovePoints = 6
            self.currentMovePoints = 6
            self.maxFuel = 6
            self.currentFuel = 6
            self.combat_value = 4
            self.stats = {
                "unitType": "Z",
                "move": 6,
                "sight": 3,
                "maintenance": 6,
                "combat_value": 4,
                "attack": {"range": 1, "value": 2},
            }

        def can_attack(self, _mode: str = "normal") -> bool:
            return True

        def set_position(self, q, r):
            self.q = q
            self.r = r

    class EnemyToken(SupplyToken):
        def __init__(self, token_id, owner, q=0, r=0):
            super().__init__(token_id, owner, q, r)
            self.stats.update({
                "unitType": "INF",
                "combat_value": 5,
                "attack": {"range": 1, "value": 4},
                "defense_value": 3,
            })

    class RetreatEngine(DummyEngine):
        def __init__(self, tokens):
            super().__init__(tokens)
            self.board = RetreatBoard(self)
            self.board.key_points = {"1,0": {"value": 120}}
            self.players = []
            self.ai_commanders = {}

    attacker = EnemyToken("ATT", "2 (Niemcy)", q=0, r=0)
    supply = SupplyToken("Z_retreat", "1 (Polska)", q=1, r=0)

    engine = RetreatEngine([attacker, supply])

    monkeypatch.setattr(random, "random", lambda: 0.0)
    monkeypatch.setattr(CombatResolver, "_find_retreat_position", lambda *args, **kwargs: (2, 0))

    combat_result = {
        "attack_result": 5,
        "defense_result": 0,
        "attack_mult": 1.0,
        "defense_mult": 1.0,
        "defense_mod": 0,
        "can_counterattack": False,
        "distance": 1,
        "attack_range": 1,
        "defense_range": 1,
    }

    CombatResolver.resolve_combat(engine, attacker, supply, combat_result)

    assert supply.combat_value == 1
    assert (supply.q, supply.r) == (2, 0)

    supply.currentMovePoints = supply.maxMovePoints
    supply.currentFuel = 0

    ai_instance = create_token_ai(supply)

    def fake_detection(_engine, _player, base_map=None):
        return {
            attacker.id: {
                "detection_level": 1.0,
                "distance": engine.board.hex_distance((supply.q, supply.r), (attacker.q, attacker.r)),
            }
        }

    def fake_visible(_engine, _detection_map=None):
        return [attacker]

    monkeypatch.setattr(ai_instance, "_collect_detection_map", fake_detection)
    monkeypatch.setattr(ai_instance, "_visible_enemies", fake_visible)

    supply.currentFuel = 0
    supply.currentMovePoints = supply.maxMovePoints

    spent_pe = ai_instance.execute_turn(engine, player=None, pe_budget=6)

    assert spent_pe == 6
    assert supply.combat_value >= 3
    assert supply.currentFuel >= 3
    assert engine.moves == [], "Konwój po odwrocie powinien utrzymać pozycję"
    assert (supply.q, supply.r) == (2, 0)
    assert ai_instance.memory.get("action_profile") == "retreat"
    final_distance = engine.board.hex_distance((attacker.q, attacker.r), (supply.q, supply.r))
    assert final_distance == 2


def test_supply_specialist_removes_withdraw_while_garrisoning():
    token = make_supply_token("Z_garrison")
    ai = create_token_ai(token)
    position = (token.q, token.r)
    board = DummyBoard()
    context = {
        "position": position,
        "current_fuel": token.currentFuel,
        "max_fuel": token.maxFuel,
        "danger_zones": {position: 0},
        "visible_enemies": [],
        "supply_target_kp": position,
        "board": board,
    }
    planned_actions = ["maneuver", "withdraw"]

    adjusted = ai.specialist.adjust_actions(planned_actions, "normal", context, pe_budget=0)

    assert "maneuver" not in adjusted
    assert "withdraw" not in adjusted


def test_supply_specialist_adds_withdraw_when_enemy_close():
    token = make_supply_token("Z_threat")
    enemy = DummyToken("enemy", owner="2 (Niemcy)", q=token.q + 1, r=token.r)
    ai = create_token_ai(token)
    board = DummyBoard()
    context = {
        "position": (token.q, token.r),
        "current_fuel": token.currentFuel,
        "max_fuel": token.maxFuel,
        "danger_zones": {(token.q, token.r): 0},
        "visible_enemies": [enemy],
        "supply_target_kp": (token.q, token.r + 1),
        "board": board,
    }
    planned_actions = ["attack", "maneuver"]

    adjusted = ai.specialist.adjust_actions(planned_actions, "normal", context, pe_budget=2)

    assert "withdraw" in adjusted


def test_supply_specialist_changes_target_after_lock_expires():
    token = make_supply_token("Z_lock")
    ai = create_token_ai(token)
    board = DummyBoard()
    board.key_points = {
        "0,1": {"value": 60},
        "2,0": {"value": 65},
        "3,2": {"value": 70},
    }
    base_context = {
        "board": board,
        "position": (token.q, token.r),
        "danger_zones": {},
        "current_fuel": token.currentFuel,
        "max_fuel": token.maxFuel,
    }

    context = ai.specialist.extend_context(dict(base_context))
    first_target = context.get("supply_target_kp")
    assert first_target is not None

    first_key = f"{first_target[0]},{first_target[1]}"
    alternative_key = None
    for key in board.key_points.keys():
        if key != first_key:
            alternative_key = key
            break
    assert alternative_key is not None

    board.key_points[alternative_key]["value"] = board.key_points[first_key]["value"] + 200

    # W trakcie blokady cel pozostaje ten sam
    locked_context = ai.specialist.extend_context(dict(base_context))
    assert locked_context.get("supply_target_kp") == first_target

    for _ in range(3):
        ai.specialist.on_turn_start({})

    updated_context = ai.specialist.extend_context(dict(base_context))
    expected_new_target = tuple(map(int, alternative_key.split(",")))
    assert updated_context.get("supply_target_kp") == expected_new_target


def test_supply_token_garrison_recovers_after_attack(monkeypatch):
    token = make_supply_token("Z_under_attack")
    token.q = 1
    token.r = 1
    token.combat_value = 2  # silny spadek CV po ataku

    enemy = DummyToken("enemy", owner="2 (Niemcy)", q=token.q + 1, r=token.r)
    enemy.stats["unitType"] = "P"

    engine = DummyEngine([token, enemy])
    engine.board.key_points = {f"{token.q},{token.r}": {"value": 120}}

    ai = create_token_ai(token)

    def fake_collect_detection(engine_arg, player, base_map=None):
        return {enemy.id: {"detection_level": 1.0, "distance": 1}}

    def fake_visible_enemies(engine_arg, detection_map=None):
        return [enemy]

    monkeypatch.setattr(ai, "_collect_detection_map", fake_collect_detection)
    monkeypatch.setattr(ai, "_visible_enemies", fake_visible_enemies)

    spent_pe = ai.execute_turn(engine, player=None, pe_budget=3)

    assert spent_pe == 3, "Budżet powinien zostać użyty na odbudowę CV"
    assert token.combat_value == 5, "CV powinno zostać odbudowane do progu 80%"
    assert engine.moves == [], "Konwój w garnizonie nie powinien opuszczać KP"
    assert (token.q, token.r) == (1, 1), "Żeton powinien pozostać na swoim KP"

    flags = ai.context.get("specialist_flags")
    assert flags and "garnizon_na_kp" in flags, "Powinna zostać oznaczona obecność garnizonu"


def test_score_tile_prefers_objective_even_with_danger():
    token = make_supply_token("Z_scoring")
    engine = DummyEngine([token])
    ai = TokenAI(token)
    board = engine.board
    context = {
        "board": board,
        "position": (0, 0),
        "danger_zones": {(1, 0): 1, (0, 1): 0},
        "friendly_tokens": [],
        "visible_enemies": [],
        "specialist_objective": (1, 0),
    }

    score_objective = ai._score_tile(engine, context, (1, 0))
    score_alternative = ai._score_tile(engine, context, (0, 1))

    assert score_objective > score_alternative