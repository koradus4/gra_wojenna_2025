"""Test: AI plan_purchases powinno pokrywać wszystkie kombinacje typ+rozmiar z PRICE_DEFAULTS przy dużym budżecie."""
import pytest
from ai.ai_general import AIGeneral
from core.unit_factory import PRICE_DEFAULTS

@pytest.mark.ai_economy
def test_ai_purchase_full_coverage():
    budget = 5000
    a = AIGeneral('polish')
    class DummyCommander:
        def __init__(self, i):
            self.id = i
            self.nation = 'Polska'
            self.role = 'Dowódca'
    commanders = [DummyCommander(1), DummyCommander(2)]
    plans = a.plan_purchases(budget, commanders, max_purchases=200)
    planned_pairs = {(p['type'], p['size']) for p in plans}
    expected_pairs = {(t, size) for size, mapping in PRICE_DEFAULTS.items() for t in mapping.keys()}
    missing = expected_pairs - planned_pairs
    assert not missing, f"Brakujące kombinacje: {sorted(missing)} (uzyskano {len(planned_pairs)} / oczekiwano {len(expected_pairs)})"
