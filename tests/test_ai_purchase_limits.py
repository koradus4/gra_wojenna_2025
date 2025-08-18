"""Testy ograniczeń zakupów AI: limit liczby i niski budżet."""
from ai.ai_general import AIGeneral
from core.unit_factory import PRICE_DEFAULTS

class DummyCommander:
    def __init__(self, i):
        self.id = i
        self.nation = 'Polska'
        self.role = 'Dowódca'

def test_ai_respects_max_purchases_limit():
    a = AIGeneral('polish')
    commanders = [DummyCommander(1), DummyCommander(2)]
    max_p = 5
    plans = a.plan_purchases(available_points=1000, commanders=commanders, max_purchases=max_p)
    assert len(plans) <= max_p
    # Dopóki nie pokryje wszystkich kombinacji, nie powinno dublować par typ+rozmiar
    pairs = [(p['type'], p['size']) for p in plans]
    assert len(pairs) == len(set(pairs)), "Nie oczekiwano duplikatów przy małym limicie zakupów"


def test_ai_low_budget_filters_expensive_units():
    a = AIGeneral('polish')
    commanders = [DummyCommander(1), DummyCommander(2)]
    budget = 60  # bardzo mały budżet
    plans = a.plan_purchases(available_points=budget, commanders=commanders, max_purchases=50)
    # Suma wydatków nie przekracza budżetu
    total_cost = sum(p['cost'] for p in plans)
    assert total_cost <= budget, f"Wydano {total_cost} > budżet {budget}"
    # Żadna baza kosztu (bez wsparć) nie powinna przekraczać budżet*1.2 ze względu na filtr w plan_purchases
    limit = budget * 1.2
    for p in plans:
        base_cost = PRICE_DEFAULTS[p['size']][p['type']]
        assert base_cost <= limit, f"Jednostka {p['type']} {p['size']} (base {base_cost}) przekracza limit {limit}"
    # Jeżeli nic nie kupiono (możliwa sytuacja) test wciąż przechodzi — sprawdzamy tylko warunki ograniczeń
