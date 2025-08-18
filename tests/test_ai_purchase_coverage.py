"""Test: AI plan_purchases powinno pokrywać wszystkie kombinacje typ+rozmiar z PRICE_DEFAULTS przy dużym budżecie.
"""
from ai.ai_general import AIGeneral
from core.unit_factory import PRICE_DEFAULTS

class DummyCommander:
    def __init__(self, i):
        self.id = i
        self.nation = 'Polska'
        self.role = 'Dowódca'

def test_ai_purchase_full_coverage():
    budget = 5000  # wystarczająco duży aby kupić wszystkie typy/rozmiary przynajmniej raz
    a = AIGeneral('polish')
    commanders = [DummyCommander(1), DummyCommander(2)]
    # duży limit zakupów żeby nie obciąć wcześniej
    plans = a.plan_purchases(budget, commanders, max_purchases=200)

    planned_pairs = {(p['type'], p['size']) for p in plans}
    expected_pairs = {(t, size) for size, mapping in PRICE_DEFAULTS.items() for t in mapping.keys()}

    # diagnostyka w razie niepowodzenia
    missing = expected_pairs - planned_pairs
    assert not missing, f"Brakujące kombinacje: {sorted(missing)} (uzyskano {len(planned_pairs)} / oczekiwano {len(expected_pairs)})"
