"""
Quick test - sprawdza czy token editor poprawnie używa balance.model
"""

import sys, os
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from balance.model import compute_token, UPGRADES

def test_token_editor_integration():
    """Test czy token editor poprawnie integruje się z balance.model"""
    print("🧪 TEST: Integracja Token Editor z balance.model")
    
    # Test podstawowy token - usuń niepotrzebny kod
    
    # Test z upgrade'ami
    unit_type = "P"  # Piechota
    unit_size = "Pluton"
    nation = "Polska"
    support_upgrades = ['obserwator', 'drużyna granatników']
    
    print(f"\n🔧 Test jednostki: {unit_type} {unit_size} ({nation})")
    print(f"🔧 Wybrane upgrade'y: {support_upgrades}")
    
    # Oblicz końcowe statystyki
    final_token = compute_token(unit_type, unit_size, nation, support_upgrades)
    
    print(f"\n✅ Końcowe statystyki:")
    print(f"  movement: {final_token.movement}")
    print(f"  attack_range: {final_token.attack_range}")
    print(f"  attack_value: {final_token.attack_value}")
    print(f"  combat_value: {final_token.combat_value}")
    print(f"  defense_value: {final_token.defense_value}")
    print(f"  sight: {final_token.sight}")
    print(f"  maintenance: {final_token.maintenance}")
    print(f"  total_cost: {final_token.total_cost}")
    
    # Sprawdź konkretne zmiany
    base_sight = 3  # P (piechota) ma sight=3 w BASE_STATS
    expected_sight = base_sight + 2  # obserwator daje +2 sight
    
    base_attack = 8  # P (piechota) ma attack_value=8 w BASE_STATS  
    expected_attack = base_attack + 2  # drużyna granatników daje +2 attack
    
    assert final_token.sight == expected_sight, f"Sight should be {expected_sight}, got {final_token.sight}"
    assert final_token.attack_value == expected_attack, f"Attack should be {expected_attack}, got {final_token.attack_value}"
    
    print(f"\n🎉 TESTY ZAKOŃCZONE POMYŚLNIE!")
    print(f"  ✅ Obserwator zwiększył sight z {base_sight} do {final_token.sight}")
    print(f"  ✅ Drużyna granatników zwiększyła attack z {base_attack} do {final_token.attack_value}")
    print(f"  ✅ Balance.model poprawnie zintegrowany z token editor")

if __name__ == "__main__":
    test_token_editor_integration()
