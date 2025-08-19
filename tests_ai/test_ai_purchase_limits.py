"""Testy ograniczeń zakupów AI: limit liczby i niski budżet."""
import pytest
from ai.ai_general import AIGeneral
from core.unit_factory import PRICE_DEFAULTS

class DummyCommander:
    def __init__(self, i):
        self.id = i
        self.nation = 'Polska'
        self.role = 'Dowódca'

@pytest.mark.ai_economy
def test_ai_respects_max_purchases_limit():
    a = AIGeneral('polish')
    commanders = [DummyCommander(1), DummyCommander(2)]
    max_p = 5
    plans = a.plan_purchases(available_points=1000, commanders=commanders, max_purchases=max_p)
    assert len(plans) <= max_p
    pairs = [(p['type'], p['size']) for p in plans]
    assert len(pairs) == len(set(pairs)), "Nie oczekiwano duplikatów przy małym limicie zakupów"

@pytest.mark.ai_economy
def test_ai_low_budget_filters_expensive_units():
    a = AIGeneral('polish')
    commanders = [DummyCommander(1), DummyCommander(2)]
    budget = 60
    plans = a.plan_purchases(available_points=budget, commanders=commanders, max_purchases=50)
    total_cost = sum(p['cost'] for p in plans)
    assert total_cost <= budget, f"Wydano {total_cost} > budżet {budget}"
    limit = budget * 1.2
    for p in plans:
        base_cost = PRICE_DEFAULTS[p['size']][p['type']]
        assert base_cost <= limit, f"Jednostka {p['type']} {p['size']} (base {base_cost}) przekracza limit {limit}"
