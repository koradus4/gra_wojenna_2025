"""Test parsowania stringowych kluczy KP (jak w map_data.json)."""
from ai.tokens.specialized_ai import SupplySpecialist, get_shared_intel_memory


class MockToken:
    def __init__(self):
        self.id = "Z_TEST"
        self.owner = "Test"
        self.stats = {"unitType": "Z"}
        self.q = 0
        self.r = 0


class MockBoardWithStringKeys:
    """Board z kluczami jako stringi "q,r" (jak w map_data.json)."""
    key_points = {
        "5,5": {"type": "miasto", "value": 10},
        "10,10": {"type": "miasto", "value": 20},
        "2,2": {"type": "miasto", "value": 5},
    }

    def hex_distance(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])


def test_string_keys_parsing():
    """Sprawdza, czy specjalista poprawnie parsuje stringowe klucze KP."""
    token = MockToken()
    specialist = SupplySpecialist(token, get_shared_intel_memory())

    context = {
        "board": MockBoardWithStringKeys(),
        "position": (0, 0),
        "danger_zones": {},
    }

    context = specialist.extend_context(context)

    # Powinien wybrać (2,2) - najlepszy score
    target_kp = context.get("supply_target_kp")
    print(f"✅ Wybrany KP: {target_kp}")
    print(f"✅ Scoring details: {context.get('kp_scoring_details')}")
    print(f"✅ Human note: {context.get('human_note')}")
    
    assert target_kp == (2, 2), f"Expected (2,2), got {target_kp}"
    assert "human_note" in context, "Brak human_note!"
    note = context["human_note"]
    assert note is not None and "Cel KP" in note
    assert "(2, 2)" in note


if __name__ == "__main__":
    test_string_keys_parsing()
    print("\n🎉 Test parsowania stringowych kluczy przeszedł!")
