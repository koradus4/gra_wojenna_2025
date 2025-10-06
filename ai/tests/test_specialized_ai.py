"""Testy jednostkowe dla modułu specjalizacji żetonów.

Weryfikują logikę SupplySpecialist oraz infrastrukturę specjalistów.
"""
from __future__ import annotations

from typing import Dict

import pytest

from ai.tokens.specialized_ai import (
    ArtillerySpecialist,
    CavalrySpecialist,
    GenericSpecialist,
    InfantrySpecialist,
    SupplySpecialist,
    TankSpecialist,
    build_specialist,
    create_token_ai,
    get_shared_intel_memory,
)
from ai.tokens.token_ai import TokenAI


class DummyToken:
    def __init__(self, unit_type: str | None = None):
        self.id = f"{unit_type or 'GEN'}_ID"
        self.owner = "Test (NationX)"
        self.stats: Dict[str, object] = {
            "unitType": unit_type,
            "move": 4,
            "maintenance": 4,
            "combat_value": 6,
            "attack": {"range": 1, "value": 4},
        }
        self.q = 0
        self.r = 0
        self.maxMovePoints = 4
        self.currentMovePoints = 4
        self.maxFuel = 4
        self.currentFuel = 4
        self.combat_value = 6

    def can_attack(self, _mode: str = "normal") -> bool:  # pragma: no cover - test helper
        return True

    def record_attack(self, _mode: str = "normal") -> None:  # pragma: no cover - test helper
        return None

    def is_artillery(self) -> bool:  # pragma: no cover - test helper
        return False


@pytest.mark.parametrize(
    "unit_type,expected",
    [
        ("Z", SupplySpecialist),
        ("K", CavalrySpecialist),
        ("P", InfantrySpecialist),
        ("C", TankSpecialist),
        ("AL", ArtillerySpecialist),
        (None, GenericSpecialist),
    ],
)
def test_build_specialist_returns_expected_class(unit_type, expected):
    """Weryfikuje, że fabryka specjalistów zwraca właściwą klasę."""
    token = DummyToken(unit_type)
    specialist = build_specialist(token, get_shared_intel_memory())
    assert isinstance(specialist, expected)


def test_supply_specialist_chooses_best_kp():
    """Sprawdza, czy SupplySpecialist wybiera KP według scoringu: wartość/(dystans+1) - zagrożenie*3."""
    token = DummyToken("Z")
    specialist = build_specialist(token, get_shared_intel_memory())

    # Mockujemy board z KP
    class MockBoard:
        key_points = {
            (5, 5): {"value": 10},
            (10, 10): {"value": 20},
            (2, 2): {"value": 5},
        }

        def hex_distance(self, a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

    context = {
        "board": MockBoard(),
        "position": (0, 0),
        "danger_zones": {},
    }
    context = specialist.extend_context(context)

    # Scoring: (2,2): 5/(2+1)=1.67, (5,5): 10/(10+1)=0.91, (10,10): 20/(20+1)=0.95
    # Najlepszy powinien być (2,2)
    assert context.get("supply_target_kp") == (2, 2)


def test_supply_specialist_locks_kp_for_3_turns():
    """Weryfikuje, że po wyborze KP specjalista nie zmienia celu przez 3 tury."""
    token = DummyToken("Z")
    specialist = build_specialist(token, get_shared_intel_memory())

    class MockBoard:
        key_points = {
            (5, 5): {"value": 10},
            (10, 10): {"value": 100},  # Znacznie lepszy, ale dalej
        }

        def hex_distance(self, a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

    context = {
        "board": MockBoard(),
        "position": (0, 0),
        "danger_zones": {},
        "friendly_tokens": [],
    }

    # Pierwsza tura – wybór najlepszego KP (scoring preferuje (10,10))
    context = specialist.extend_context(context)
    first_kp = context.get("supply_target_kp")
    assert first_kp in [(5, 5), (10, 10)]  # Akceptujemy dowolny wybór

    # Symulujemy 2 kolejne tury – cel nie powinien się zmienić
    for _ in range(2):
        specialist.on_turn_start({})
        context = specialist.extend_context(context)
        assert context.get("supply_target_kp") == first_kp, "KP zmienił się przed upływem 3 tur"


def test_supply_specialist_avoids_combat():
    """Weryfikuje, że konwój usuwa atak i dodaje wycofanie."""
    token = DummyToken("Z")
    specialist = build_specialist(token, get_shared_intel_memory())

    context = {
        "current_fuel": 4,
        "max_fuel": 4,
        "danger_zones": {(0, 0): 0},
        "position": (0, 0),
    }
    actions = specialist.adjust_actions(["attack", "maneuver"], "normal", context, pe_budget=3)

    assert "attack" not in actions
    assert "withdraw" in actions
    assert "pacyfista" in context.get("specialist_flags", set())


def test_supply_specialist_prioritizes_fuel():
    """Sprawdza, że przy niskim paliwie dodawany jest refuel_minimum."""
    token = DummyToken("Z")
    specialist = build_specialist(token, get_shared_intel_memory())

    context = {
        "current_fuel": 2,
        "max_fuel": 6,
        "danger_zones": {(0, 0): 0},
        "position": (0, 0),
    }
    actions = specialist.adjust_actions([], "normal", context, pe_budget=3)

    assert actions and actions[0] == "refuel_minimum"
    assert "niski_poziom_paliwa" in context.get("specialist_flags", set())
    assert "human_note" in context


def test_create_token_ai_binds_specialist():
    """Weryfikuje, że fabryka create_token_ai tworzy AI z przypisanym specjalistą."""
    token = DummyToken("K")
    ai_instance = create_token_ai(token)

    assert isinstance(ai_instance, TokenAI)
    assert ai_instance.specialist is not None
    assert isinstance(ai_instance.specialist, CavalrySpecialist)
