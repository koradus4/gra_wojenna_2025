# -*- coding: utf-8 -*-
"""
test_ai_module.py – testy szkieletu modułu AI (Faza 1 + Faza 2).

Sprawdza:
  1. Import głównych klas AI
  2. Instancjonowanie agentów
  3. StateAdapter – poprawność formatu wyjściowego (stub bez silnika)
  4. DecisionQueue – kolejkowanie i priorytety
  5. Evaluator – ocena ruchu / ataku
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# 1. Import klas
# ---------------------------------------------------------------------------

def test_ai_imports():
    """Weryfikuje, że wszystkie główne klasy AI można zaimportować."""
    from ai import BaseAgent, TacticalAgent, StrategicAgent
    from ai.state_adapter import StateAdapter
    from ai.evaluator import Evaluator
    from ai.decision_queue import DecisionQueue

    assert BaseAgent is not None
    assert TacticalAgent is not None
    assert StrategicAgent is not None
    assert StateAdapter is not None
    assert Evaluator is not None
    assert DecisionQueue is not None


# ---------------------------------------------------------------------------
# 2. Instancjonowanie agentów
# ---------------------------------------------------------------------------

def test_tactical_agent_init():
    from ai.tactical_agent import TacticalAgent
    agent = TacticalAgent(player_id=1, nation="Polska", difficulty="normal", seed=42)
    assert agent.player_id == 1
    assert agent.nation == "Polska"
    assert agent.difficulty == "normal"
    assert agent.seed == 42


def test_strategic_agent_init():
    from ai.strategic_agent import StrategicAgent
    agent = StrategicAgent(player_id=0, nation="Niemcy", difficulty="hard")
    assert agent.player_id == 0
    assert agent.nation == "Niemcy"


# ---------------------------------------------------------------------------
# 3. TacticalAgent.decide – pusty stan
# ---------------------------------------------------------------------------

def test_tactical_agent_decide_empty_state():
    from ai.tactical_agent import TacticalAgent
    agent = TacticalAgent(player_id=1, nation="Polska", seed=0)
    state = {
        "turn": 1,
        "player": {"id": 1, "role": "dowódca", "nation": "Polska"},
        "economy": {"points": 0},
        "key_points": [],
        "self_tokens": [],
        "enemy_visible": [],
        "map": {"cols": 10, "rows": 10},
    }
    actions = agent.decide(state)
    assert isinstance(actions, list)
    assert len(actions) == 0


def test_tactical_agent_decide_generates_move():
    """Agent powinien wygenerować ruch do key pointa, gdy żeton jest w jego zasięgu."""
    from ai.tactical_agent import TacticalAgent
    agent = TacticalAgent(player_id=1, nation="Polska", seed=0)
    state = {
        "turn": 1,
        "player": {"id": 1, "role": "dowódca", "nation": "Polska"},
        "economy": {"points": 0},
        "key_points": [
            {"q": 2, "r": 0, "type": "city", "current": 100, "initial": 100, "ours": False}
        ],
        "self_tokens": [
            {
                "id": "P_INF_1",
                "q": 0,
                "r": 0,
                "cv": 5,
                "dv": 3,
                "mp": 5,
                "max_mp": 5,
                "fuel": 10,
                "atk": 4,
                "rng": 1,
                "sight": 2,
                "price": 10,
                "nation": "Polska",
                "movement_mode": "combat",
            }
        ],
        "enemy_visible": [],
        "map": {"cols": 10, "rows": 10},
    }
    actions = agent.decide(state)
    assert len(actions) >= 1
    move_actions = [a for a in actions if a["type"] == "move"]
    assert len(move_actions) == 1
    assert move_actions[0]["token_id"] == "P_INF_1"


# ---------------------------------------------------------------------------
# 4. StrategicAgent.decide – pusty stan
# ---------------------------------------------------------------------------

def test_strategic_agent_decide_empty_state():
    from ai.strategic_agent import StrategicAgent
    agent = StrategicAgent(player_id=0, nation="Polska")
    state = {
        "turn": 1,
        "player": {"id": 0, "role": "generał", "nation": "Polska"},
        "economy": {"points": 50},
        "key_points": [],
        "self_tokens": [],
        "enemy_visible": [],
        "map": {"cols": 10, "rows": 10},
    }
    actions = agent.decide(state)
    assert isinstance(actions, list)


def test_strategic_agent_generates_directive():
    """Agent powinien wygenerować dyrektywę dla pilnego key pointa."""
    from ai.strategic_agent import StrategicAgent
    agent = StrategicAgent(player_id=0, nation="Polska")
    state = {
        "turn": 1,
        "player": {"id": 0, "role": "generał", "nation": "Polska"},
        "economy": {"points": 50},
        "key_points": [
            {
                "q": 3,
                "r": -1,
                "type": "city",
                "current": 10,
                "initial": 100,
                "ours": True,
            }
        ],
        "self_tokens": [],
        "enemy_visible": [],
        "map": {"cols": 10, "rows": 10},
    }
    actions = agent.decide(state)
    directives = [a for a in actions if a["type"] == "directive"]
    assert len(directives) >= 1
    assert directives[0]["target_q"] == 3
    assert directives[0]["target_r"] == -1


# ---------------------------------------------------------------------------
# 5. DecisionQueue
# ---------------------------------------------------------------------------

def test_decision_queue_priority():
    from ai.decision_queue import DecisionQueue
    q = DecisionQueue()
    q.add({"type": "move", "token_id": "A"})
    q.add({"type": "combat", "attacker_id": "A", "defender_id": "B"})
    actions = q.pop_all()
    # combat ma wyższy priorytet niż move
    assert actions[0]["type"] == "combat"
    assert actions[1]["type"] == "move"


def test_decision_queue_filter():
    from ai.decision_queue import DecisionQueue
    q = DecisionQueue()
    q.add({"type": "move", "token_id": "A"})
    q.add({"type": "move", "token_id": "B"})
    q.add({"type": "combat", "attacker_id": "A", "defender_id": "C"})
    q.remove_type("move")
    actions = q.pop_all()
    assert len(actions) == 1
    assert actions[0]["type"] == "combat"


def test_decision_queue_empty_after_pop():
    from ai.decision_queue import DecisionQueue
    q = DecisionQueue()
    q.add({"type": "move", "token_id": "X"})
    q.pop_all()
    assert len(q) == 0


# ---------------------------------------------------------------------------
# 6. Evaluator
# ---------------------------------------------------------------------------

def test_evaluator_score_move_no_key_points():
    from ai.evaluator import Evaluator
    ev = Evaluator()
    token = {"id": "T1", "q": 0, "r": 0, "cv": 5, "rng": 1, "mp": 5}
    state = {
        "key_points": [],
        "enemy_visible": [],
        "self_tokens": [token],
    }
    score = ev.score_move(token, 1, 0, state, move_cost=1)
    assert isinstance(score, float)


def test_evaluator_should_attack_strong_vs_weak():
    from ai.evaluator import Evaluator
    ev = Evaluator()
    attacker = {"cv": 10}
    defender = {"cv": 3}
    assert ev.should_attack(attacker, defender) is True


def test_evaluator_should_not_attack_weak_vs_strong():
    from ai.evaluator import Evaluator
    ev = Evaluator()
    attacker = {"cv": 2}
    defender = {"cv": 20}
    assert ev.should_attack(attacker, defender) is False
