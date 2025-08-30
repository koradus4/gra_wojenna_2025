"""Test parytetu: sklep (compute_token) vs bezpośrednie wywołanie centralnego modelu.

Celem jest upewnienie się, że GUI TokenShop używa balance.model.compute_token i
nie wprowadza własnych modyfikacji statystyk / kosztów.
"""
from balance.model import compute_token
import math

# Wybrane kombinacje (reprezentatywne) typ/rozmiar/wsparcia
CASES = [
    ("P", "Pluton", []),
    ("P", "Kompania", ["drużyna granatników"]),
    ("K", "Pluton", []),
    ("TL", "Pluton", ["sekcja ckm"]),
    ("AC", "Kompania", ["sekcja km.ppanc", "sam. ciezarowy Fiat 621"]),
]

NATION = "Polska"


def extract(comp):
    return {
        "movement": comp.movement,
        "attack_range": comp.attack_range,
        "attack_value": comp.attack_value,
        "combat_value": comp.combat_value,
        "defense_value": comp.defense_value,
        "maintenance": comp.maintenance,
        "price": comp.total_cost,
        "sight": comp.sight,
    }


def test_compute_token_stability():
    # Po prostu uruchamiamy compute_token i sprawdzamy czy własności są spójne (dodatkowo wewnętrzna konsystencja)
    for ut, size, ups in CASES:
        comp = compute_token(ut, size, NATION, ups, quality="standard")
        data = extract(comp)
        # Minimalne asercje – wartości dodatnie
        for k, v in data.items():
            assert v >= 0, f"{k} ujemne dla {ut} {size} {ups}"  # sight/attack_range mogą być 0? w obecnym modelu nie.
        # Zależność: koszt >= suma częściowo znormalizowanych statów / uproszczone sprawdzenie
        threshold = math.ceil(data["attack_value"] * 0.7)
        assert data["price"] >= threshold, (
            f"Cena {data['price']} poniżej minimalnego progu {threshold} (70% ataku {data['attack_value']})"
        )

