import pytest

from ai.ai_general import AIGeneral

class DummyCommander:
    def __init__(self, cid):
        self.id = cid

@pytest.fixture
def commander_list():
    return [DummyCommander(1)]

@pytest.fixture
def ai_gen():
    return AIGeneral(nationality="polish")

@pytest.fixture(autouse=True)
def no_supports(monkeypatch):
    """Wyłącz dobór wsparć aby nie zmieniać kosztów w testach heurystyk."""
    def _no_supports(self, template, remaining):
        return [], 0
    monkeypatch.setattr(AIGeneral, "select_supports_for_unit", _no_supports)


def _run_plan(ai_gen, pts, commanders, state):
    return ai_gen.plan_purchases(pts, commanders, max_purchases=1, state=state)


def test_heuristic_supply_first(ai_gen, commander_list):
    state = {
        'global': {'unit_counts_by_type': {}, 'total_units': 0},
        'per_commander': {},
        'enemy': {'unit_counts_by_type': {}, 'total_units': 0, 'has_artillery': False, 'has_armor': False}
    }
    purchases = _run_plan(ai_gen, 120, commander_list, state)
    assert purchases, "Brak zaplanowanych zakupów"
    assert purchases[0]['type'] == 'Z', "Pierwszym zakupem powinno być zaopatrzenie kiedy brak go w armii"


def test_heuristic_artillery_when_missing(ai_gen, commander_list):
    state = {
        'global': {'unit_counts_by_type': {'Z': 1}, 'total_units': 1},  # Jest już zaopatrzenie
        'per_commander': {},
        'enemy': {'unit_counts_by_type': {}, 'total_units': 0, 'has_artillery': False, 'has_armor': False}
    }
    purchases = _run_plan(ai_gen, 150, commander_list, state)
    assert purchases, "Brak zaplanowanych zakupów"
    assert purchases[0]['type'] in {'AL','AC','AP'}, "Powinna zostać wybrana artyleria gdy brak własnej"


def test_heuristic_armor_response(ai_gen, commander_list):
    state = {
        'global': {'unit_counts_by_type': {'Z': 1, 'AL': 1}, 'total_units': 2},  # Mamy supply i artylerię
        'per_commander': {},
        'enemy': {'unit_counts_by_type': {'TL': 1}, 'total_units': 1, 'has_artillery': False, 'has_armor': True}
    }
    purchases = _run_plan(ai_gen, 200, commander_list, state)
    assert purchases, "Brak zaplanowanych zakupów"
    assert purchases[0]['type'] in {'TL','TŚ','TS','TC'}, "Powinna zostać wybrana jednostka pancerna w reakcji na pancerz wroga"
