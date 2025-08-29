import pytest
from balance.model import compute_token

def test_compute_infantry_platoon():
    s = compute_token("P", "Pluton", "Polska", ["drużyna granatników"])  # jeden upgrade
    assert s.movement >= 1
    assert s.attack_value >= 8  # po modyfikacjach
    assert s.total_cost >= s.base_cost

def test_compute_tank_company():
    s = compute_token("TL", "Kompania", "Polska", [])
    assert s.attack_value >= 10
    assert s.movement >= 1

def test_doctrine_difference():
    p = compute_token("P", "Kompania", "Polska", [])
    g = compute_token("P", "Kompania", "Niemcy", [])
    # Niemcy powinni mieć >= atak lub combat przez doktrynę
    assert g.attack_value >= p.attack_value
    assert g.combat_value >= p.combat_value

@pytest.mark.parametrize("u", ["sekcja ckm", "sekcja km.ppanc"])  # test kumulacji limitu kar ruchu
def test_single_movement_penalty(u):
    s = compute_token("P", "Kompania", "Polska", [u, "drużyna granatników"])  # dwie kary - tylko jedna ma zejść
    assert s.movement >= 1  # nie spada nieograniczenie
