from balance.model import compute_token
from ai.ai_general import AIGeneral  # zakładam klasę AIGeneral istnieje

class DummyPlayer:  # minimalny obiekt do wywołania purchase_unit_programmatically jeśli potrzebne
    class Econ:
        def __init__(self):
            self._pts = 1000
        def get_points(self):
            return {'economic_points': self._pts}
        def subtract_points(self, c):
            self._pts -= c
    economy = Econ()

# Jeśli AIGeneral ma dużo wymagań, test ograniczamy do compute_token bez AI.

def test_balance_module_basic():
    c = compute_token("P", "Pluton", "Polska", ["drużyna granatników"])
    assert c.movement >= 1 and c.total_cost >= c.base_cost
