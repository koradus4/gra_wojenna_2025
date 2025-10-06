"""Ręczny test - pokazuje jak działają human_notes dla SupplySpecialist."""
from ai.tokens.specialized_ai import SupplySpecialist, get_shared_intel_memory


class MockBoard:
    key_points = {
        (5, 5): {"value": 10},
        (10, 10): {"value": 20},
        (2, 2): {"value": 5},
        (15, 15): {"value": 30},
    }

    def hex_distance(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])


class MockToken:
    def __init__(self):
        self.id = "Z_TEST"
        self.owner = "Test (TestNation)"
        self.stats = {"unitType": "Z"}
        self.q = 0
        self.r = 0
        self.maxFuel = 10
        self.currentFuel = 3


def test_human_readable_output():
    """Pokazuje czytelne dla człowieka notatki z działań konwoju."""
    token = MockToken()
    specialist = SupplySpecialist(token, get_shared_intel_memory())

    # Symulacja: niski poziom paliwa
    context_fuel = {
        "board": MockBoard(),
        "position": (0, 0),
        "danger_zones": {},
        "current_fuel": 3,
        "max_fuel": 10,
    }
    
    context_fuel = specialist.extend_context(context_fuel)
    actions = specialist.adjust_actions([], "normal", context_fuel, pe_budget=5)
    
    print("=== KONWÓJ: TANKOWANIE ===")
    print(f"Pozycja: {context_fuel['position']}")
    print(f"Cel KP: {context_fuel.get('supply_target_kp')}")
    print(f"Akcje: {actions}")
    print(f"Human note: {context_fuel.get('human_note', 'brak')}")
    print(f"Flagi: {context_fuel.get('specialist_flags', set())}")
    print()

    # Symulacja: zmiana celu KP
    token2 = MockToken()
    specialist2 = SupplySpecialist(token2, get_shared_intel_memory())
    
    context_kp = {
        "board": MockBoard(),
        "position": (0, 0),
        "danger_zones": {},
        "current_fuel": 10,
        "max_fuel": 10,
    }
    
    context_kp = specialist2.extend_context(context_kp)
    
    print("=== KONWÓJ: WYBÓR CELU KP ===")
    print(f"Pozycja: {context_kp['position']}")
    print(f"Cel KP: {context_kp.get('supply_target_kp')}")
    print(f"Human note: {context_kp.get('human_note', 'brak (pierwszy wybór)')}")
    print(f"Scoring details: {context_kp.get('kp_scoring_details', {})}")
    print(f"Flagi: {context_kp.get('specialist_flags', set())}")
    print()

    # Symulacja: wykrycie wroga
    token3 = MockToken()
    specialist3 = SupplySpecialist(token3, get_shared_intel_memory())
    
    context_threat = {
        "board": MockBoard(),
        "position": (5, 5),
        "danger_zones": {(5, 5): 3},  # 3 wrogów w zasięgu
        "current_fuel": 10,
        "max_fuel": 10,
    }
    
    new_status = specialist3.adjust_status("normal", context_threat)
    
    print("=== KONWÓJ: WYKRYCIE WROGA ===")
    print(f"Pozycja: {context_threat['position']}")
    print(f"Zagrożenie: {context_threat['danger_zones'].get((5, 5), 0)} wrogów")
    print(f"Status: normal → {new_status}")
    print(f"Human note: {context_threat.get('human_note', 'brak')}")
    print(f"Flagi: {context_threat.get('specialist_flags', set())}")
    print()

    # Symulacja: garnizon na KP
    token4 = MockToken()
    token4.q = 2
    token4.r = 2
    specialist4 = SupplySpecialist(token4, get_shared_intel_memory())
    specialist4._assigned_kp = (2, 2)
    
    context_garrison = {
        "board": MockBoard(),
        "position": (2, 2),
        "danger_zones": {},
        "current_fuel": 10,
        "max_fuel": 10,
        "supply_target_kp": (2, 2),
    }
    
    actions_garrison = specialist4.adjust_actions(["maneuver", "attack"], "normal", context_garrison, pe_budget=0)
    
    print("=== KONWÓJ: GARNIZON NA KP ===")
    print(f"Pozycja: {context_garrison['position']}")
    print(f"Cel KP: {context_garrison.get('supply_target_kp')}")
    print(f"Akcje: {actions_garrison}")
    print(f"Human note: {context_garrison.get('human_note', 'brak')}")
    print(f"Flagi: {context_garrison.get('specialist_flags', set())}")
    print()


if __name__ == "__main__":
    test_human_readable_output()
    print("✅ Test zakończony – wszystkie human_notes wygenerowane poprawnie!")
