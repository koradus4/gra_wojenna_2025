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
    def _none(self, template, remaining):
        return [], 0
    monkeypatch.setattr(AIGeneral, 'select_supports_for_unit', _none)


def _plan(ai_gen, pts, commanders, state):
    return ai_gen.plan_purchases(pts, commanders, max_purchases=1, state=state)


def test_heuristic_mobility(ai_gen, commander_list):
    # Brak K i TS -> powinien wybrać Kawalerię lub Sam. pancerny
    state = {
        'global': {'unit_counts_by_type': {'Z':1,'AL':1,'P':3}, 'total_units':5},
        'per_commander': {},
        'enemy': {'unit_counts_by_type': {}, 'total_units':0, 'has_artillery':False, 'has_armor':False}
    }
    purchases = _plan(ai_gen, 120, commander_list, state)
    assert purchases, 'Brak zakupu'
    assert purchases[0]['type'] in {'K','TS'}, 'Powinna zostać wybrana jednostka mobilna (K lub TS)'


def test_heuristic_diversity(ai_gen, commander_list):
    # Wszystkie kluczowe typy obecne, brak czołgów ciężkich np. -> dywersyfikacja weźmie typ o najniższym count
    state = {
        'global': {'unit_counts_by_type': {'Z':1,'AL':1,'P':4,'K':1,'TS':1}, 'total_units':8},
        'per_commander': {},
        'enemy': {'unit_counts_by_type': {}, 'total_units':0, 'has_artillery':False, 'has_armor':False}
    }
    purchases = _plan(ai_gen, 300, commander_list, state)
    assert purchases, 'Brak zakupu'
    # Dopuszczamy każdy typ którego count==0 w template przy budżecie (np. TL/TŚ/TC/AC/AP jeśli nie ma)
    chosen = purchases[0]['type']
    # Musi być jednym z typów które mają count 0 w stanie
    zero_types = [t for t in ['TC','TŚ','TL','AC','AP'] if t not in state['global']['unit_counts_by_type']]
    if zero_types:  # jeśli są nowe typy
        assert chosen in zero_types, f'Dywersyfikacja powinna wybrać nowy typ (wybrano {chosen}, dostępne {zero_types})'
    else:
        # Jeśli wszystko już jest, dowolny najniższy count – akceptujemy cokolwiek
        assert chosen is not None
