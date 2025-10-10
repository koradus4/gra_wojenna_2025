import pytest
from types import SimpleNamespace

from core.ekonomia import EconomySystem
from engine.player import Player
from ai.commander.commander_ai import CommanderAI


class DummyBoard:
    def __init__(self, spawn_points):
        self.spawn_points = spawn_points
        self.tokens = []

    def set_tokens(self, tokens):
        self.tokens = list(tokens)

    def is_occupied(self, q, r, visible_tokens=None):
        return any(getattr(token, "q", None) == q and getattr(token, "r", None) == r for token in self.tokens)


class DummyEngine:
    def __init__(self, board, players, turn=1):
        self.board = board
        self.tokens = []
        self.players = players
        self.turn = turn
        self.visibility_updated = False

    def update_all_players_visibility(self, players):
        self.visibility_updated = True


class DummyToken:
    def __init__(self, token_id, owner, q, r):
        self.id = token_id
        self.owner = owner
        self.q = q
        self.r = r
        self.fuel = 5
        self.maxFuel = 10
        self.currentCombatStrength = 4
        self.maxCombatStrength = 10


@pytest.fixture
def commander():
    economy = EconomySystem()
    economy.add_economic_points(100)
    player = Player(2, "Polska", "Dowódca")
    player.economy = economy
    return player


@pytest.fixture
def stub_token_ai(monkeypatch):
    executions = []

    class StubAI:
        def __init__(self, token):
            self.token = token

        def execute_turn(self, engine, player, share):
            executions.append((self.token.id, share))
            return 0

    monkeypatch.setattr("ai.commander.commander_ai.create_token_ai", lambda token: StubAI(token))
    return executions


def test_reinforcement_spawn_success(monkeypatch, commander, stub_token_ai):
    commander.ai_reinforcement_queue = [
        {
            "unit_type": "P",
            "unit_size": "Pluton",
            "priority": 10,
            "quality": "standard",
        }
    ]

    board = DummyBoard({"Polska": ["0,0", "1,0"]})
    engine = DummyEngine(board, [commander], turn=5)
    board.set_tokens(engine.tokens)

    ai = CommanderAI(commander)
    ai.execute_turn(engine)

    assert len(engine.tokens) == 1, "Nowy żeton powinien zostać dodany do silnika"
    spawned_token = engine.tokens[0]
    assert (spawned_token.q, spawned_token.r) == (0, 0)
    assert spawned_token.owner == f"{commander.id} ({commander.nation})"

    history = getattr(commander, "ai_reinforcement_history", [])
    assert len(history) == 1
    cost = history[0]["cost"]
    remaining = commander.economy.get_points()["economic_points"]
    assert remaining == 100 - cost
    assert getattr(commander, "punkty_ekonomiczne", None) == remaining

    assert commander.ai_reinforcement_queue == []
    assert len(stub_token_ai) == 1
    assert engine.visibility_updated is True


def test_reinforcement_waits_for_budget(monkeypatch, commander, stub_token_ai):
    commander.economy.economic_points = 10
    commander.ai_reinforcement_queue = [
        {
            "unit_type": "P",
            "unit_size": "Pluton",
            "priority": 5,
        }
    ]

    board = DummyBoard({"Polska": ["0,0"]})
    engine = DummyEngine(board, [commander], turn=3)
    board.set_tokens(engine.tokens)

    ai = CommanderAI(commander)
    ai.execute_turn(engine)

    assert len(engine.tokens) == 0
    assert len(getattr(commander, "ai_reinforcement_queue", [])) == 1
    assert not hasattr(commander, "ai_reinforcement_history")
    assert commander.economy.get_points()["economic_points"] == 10
    assert stub_token_ai == []


def test_reinforcement_blocked_by_spawn(monkeypatch, commander, stub_token_ai):
    commander.ai_reinforcement_queue = [
        {
            "unit_type": "P",
            "priority": 7,
        }
    ]

    board = DummyBoard({"Polska": ["0,0"]})
    occupant = DummyToken("old", f"{commander.id} ({commander.nation})", 0, 0)
    engine = DummyEngine(board, [commander], turn=4)
    engine.tokens.append(occupant)
    board.set_tokens(engine.tokens)

    ai = CommanderAI(commander)
    ai.execute_turn(engine)

    assert len(engine.tokens) == 1
    assert engine.tokens[0].id == "old"
    queue = getattr(commander, "ai_reinforcement_queue", [])
    assert len(queue) == 1
    assert not hasattr(commander, "ai_reinforcement_history")
    assert len(stub_token_ai) == 1
    assert stub_token_ai[0][0] == "old"