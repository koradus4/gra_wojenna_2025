import unittest

from core.unit_factory import (
    compute_unit_stats,
    SUPPORT_UPGRADES,
    TRANSPORT_TYPES,
    PRICE_DEFAULTS,
    MOVE_DEFAULTS,
    RANGE_DEFAULTS,
    ATTACK_DEFAULTS,
    COMBAT_DEFAULTS,
    DEFENSE_DEFAULTS,
    MAINTENANCE_DEFAULTS,
    SIGHT_DEFAULTS,
    ALLOWED_SUPPORT,
)


def manual_compute(unit_type, unit_size, supports):
    """Manualne odtworzenie algorytmu (źródło prawdy logiki) do porównania z compute_unit_stats.

    Zasady:
      1. Bazowe tabele.
      2. Pierwszy transport (z TRANSPORT_TYPES) – movement bonus natychmiast.
      3. Dokładnie jedna kara -1 movement z pierwszego wsparcia o movement < 0 (nie transport).
      4. attack/combat/price/maintenance/defense sumowane dla wszystkich wsparć (transport doliczany na końcu: purchase+maintenance+defense – movement już wcześniej).
      5. range – najwyższy bonus z wsparć (bez transportu – bo 0).
    """
    move = MOVE_DEFAULTS.get(unit_type, 0)
    attack_range = RANGE_DEFAULTS.get(unit_type, 0)
    attack_value = ATTACK_DEFAULTS.get(unit_size, {}).get(unit_type, 0)
    combat_value = COMBAT_DEFAULTS.get(f"{unit_type}__{unit_size}", 0)
    defense_value = DEFENSE_DEFAULTS.get(unit_size, {}).get(unit_type, 0)
    maintenance = MAINTENANCE_DEFAULTS.get(unit_size, {}).get(unit_type, 0)
    price = PRICE_DEFAULTS.get(unit_size, {}).get(unit_type, 0)
    sight = SIGHT_DEFAULTS.get(unit_type, 0)

    transport = None
    for s in supports:
        if s in TRANSPORT_TYPES:
            transport = s
            move += SUPPORT_UPGRADES[transport]["movement"]
            break

    movement_penalty_used = False
    max_range_bonus = 0
    for s in supports:
        if s == transport:
            continue
        upg = SUPPORT_UPGRADES.get(s)
        if not upg:
            continue
        if upg["movement"] < 0 and not movement_penalty_used:
            move -= 1
            movement_penalty_used = True
        attack_value += upg["attack"]
        combat_value += upg["combat"]
        price += upg["purchase"]
        maintenance += upg["unit_maintenance"]
        defense_value += upg["defense"]
        max_range_bonus = max(max_range_bonus, upg["range"])

    if max_range_bonus:
        attack_range += max_range_bonus

    if transport:
        t = SUPPORT_UPGRADES[transport]
        maintenance += t["unit_maintenance"]
        price += t["purchase"]
        defense_value += t["defense"]

    return dict(move=move, attack_range=attack_range, attack_value=attack_value,
                combat_value=combat_value, defense_value=defense_value,
                maintenance=maintenance, price=price, sight=sight)


class TestUnitFactoryParity(unittest.TestCase):
    def test_basic_parity_selected_combinations(self):
        # Sprawdź kilka reprezentatywnych typów i rozmiarów oraz kombinacji wsparć
        unit_types = ["P", "AL", "TC", "K", "Z"]
        sizes = ["Pluton", "Kompania"]
        for ut in unit_types:
            allowed = ALLOWED_SUPPORT.get(ut, [])
            # Zbuduj kilka przykładowych zestawów wsparć (do 4, aby test był szybki)
            test_support_sets = [
                [],
                allowed[:1],
                allowed[:2],
            ]
            # Dodaj kombinację z transportem jeśli istnieje
            transport = next((t for t in TRANSPORT_TYPES if t in allowed), None)
            if transport:
                test_support_sets.append([transport])
                # transport + jedno ciężkie wsparcie jeśli dostępne
                heavy = next((s for s in allowed if s not in TRANSPORT_TYPES and SUPPORT_UPGRADES[s]["movement"] < 0), None)
                if heavy:
                    test_support_sets.append([transport, heavy])
            for size in sizes:
                for supports in test_support_sets:
                    with self.subTest(unit_type=ut, size=size, supports=supports):
                        calc = compute_unit_stats(ut, size, supports)
                        manual = manual_compute(ut, size, supports)
                        self.assertEqual(calc.move, manual['move'])
                        self.assertEqual(calc.attack_range, manual['attack_range'])
                        self.assertEqual(calc.attack_value, manual['attack_value'])
                        self.assertEqual(calc.combat_value, manual['combat_value'])
                        self.assertEqual(calc.defense_value, manual['defense_value'])
                        self.assertEqual(calc.maintenance, manual['maintenance'])
                        self.assertEqual(calc.price, manual['price'])
                        self.assertEqual(calc.sight, manual['sight'])


if __name__ == "__main__":
    unittest.main()
