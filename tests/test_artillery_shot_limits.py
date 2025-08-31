"""
Test systemu ograniczenia strzałów artylerii - 1 atak na turę + opcjonalny reakcyjny
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.token import Token
from engine.action_refactored_clean import CombatAction
from balance.model import compute_token


def test_artillery_shot_limits():
    """Test ograniczenia strzałów artylerii"""
    print("=== TEST OGRANICZENIA STRZAŁÓW ARTYLERII ===\n")
    
    # Stwórz artylerie różnych typów
    artillery_types = [
        ('AL', 'Artyleria lekka'),
        ('AC', 'Artyleria ciężka'), 
        ('AP', 'Artyleria plot')
    ]
    
    for art_type, art_name in artillery_types:
        print(f"🎯 Test {art_name} ({art_type}):")
        
        # Oblicz statystyki
        stats = compute_token(art_type, 'Kompania', 'Polska', [])
        
        # Stwórz token artylerii
        token_stats = {
            'unitType': art_type,
            'move': stats.movement,
            'attack': {'value': stats.attack_value, 'range': stats.attack_range},
            'combat_value': stats.combat_value,
            'defense_value': stats.defense_value,
            'maintenance': stats.maintenance,
            'sight': stats.sight
        }
        
        artillery_token = Token(
            id=f"test_{art_type.lower()}_art",
            owner="1 (Polska)",
            stats=token_stats,
            q=10, r=10
        )
        
        # Test początkowych wartości
        assert artillery_token.shots_fired_this_turn == 0, "Początkowa liczba strzałów powinna być 0"
        assert artillery_token.reaction_shot_used == False, "Strzał reakcyjny na początku powinien być dostępny"
        assert artillery_token.is_artillery() == True, f"{art_type} powinien być rozpoznany jako artyleria"
        
        # Test możliwości ataku na początku tury
        assert artillery_token.can_attack('normal') == True, "Artyleria powinna móc atakować na początku tury"
        assert artillery_token.can_attack('reaction') == True, "Strzał reakcyjny powinien być dostępny"
        
        # Zapisz normalny atak
        artillery_token.record_attack('normal')
        
        # Po normalnym ataku
        assert artillery_token.shots_fired_this_turn == 1, "Po ataku liczba strzałów powinna być 1"
        assert artillery_token.can_attack('normal') == False, "Po ataku normalny strzał powinien być niedostępny"
        assert artillery_token.can_attack('reaction') == True, "Strzał reakcyjny nadal powinien być dostępny"
        
        # Zapisz atak reakcyjny
        artillery_token.record_attack('reaction')
        
        # Po ataku reakcyjnym
        assert artillery_token.reaction_shot_used == True, "Strzał reakcyjny powinien być użyty"
        assert artillery_token.can_attack('reaction') == False, "Po użyciu strzał reakcyjny powinien być niedostępny"
        
        # Reset tury
        artillery_token.reset_turn_actions()
        
        # Po resecie
        assert artillery_token.shots_fired_this_turn == 0, "Po resecie liczba strzałów powinna być 0"
        assert artillery_token.reaction_shot_used == False, "Po resecie strzał reakcyjny powinien być dostępny"
        assert artillery_token.can_attack('normal') == True, "Po resecie normalny atak powinien być dostępny"
        assert artillery_token.can_attack('reaction') == True, "Po resecie strzał reakcyjny powinien być dostępny"
        
        print(f"  ✅ {art_name}: Wszystkie testy przeszły!")
    
    print("\n=== TEST JEDNOSTEK NIE-ARTYLERYJSKICH ===\n")
    
    # Test jednostek nie-artyleryjskich (powinny móc atakować bez ograniczeń)
    non_artillery_types = [
        ('P', 'Piechota'),
        ('TL', 'Czołg lekki'),
        ('K', 'Kawaleria')
    ]
    
    for unit_type, unit_name in non_artillery_types:
        print(f"⚔️ Test {unit_name} ({unit_type}):")
        
        stats = compute_token(unit_type, 'Kompania', 'Polska', [])
        
        token_stats = {
            'unitType': unit_type,
            'move': stats.movement,
            'attack': {'value': stats.attack_value, 'range': stats.attack_range},
            'combat_value': stats.combat_value,
            'defense_value': stats.defense_value,
            'maintenance': stats.maintenance,
            'sight': stats.sight
        }
        
        unit_token = Token(
            id=f"test_{unit_type.lower()}_unit",
            owner="1 (Polska)",
            stats=token_stats,
            q=5, r=5
        )
        
        # Jednostki nie-artyleryjskie nie powinny mieć ograniczeń
        assert unit_token.is_artillery() == False, f"{unit_type} nie powinien być artyleria"
        
        # Powinny móc atakować wielokrotnie
        for i in range(5):
            assert unit_token.can_attack('normal') == True, f"{unit_name} powinien móc atakować bez ograniczeń (próba {i+1})"
            unit_token.record_attack('normal')
        
        # Powinny móc użyć reakcyjnego wielokrotnie
        for i in range(3):
            assert unit_token.can_attack('reaction') == True, f"{unit_name} powinien móc atakować reakcyjnie bez ograniczeń (próba {i+1})"
            unit_token.record_attack('reaction')
        
        print(f"  ✅ {unit_name}: Może atakować bez ograniczeń!")
    
    print("\n=== TEST COMBAT ACTION INTEGRATION ===\n")
    
    # Test czy CombatAction respektuje ograniczenia
    class MockEngine:
        class MockBoard:
            def hex_distance(self, pos1, pos2):
                return 1
        
        board = MockBoard()
        tokens = []
    
    # Stwórz artylerie i cel
    al_stats = compute_token('AL', 'Kompania', 'Polska', [])
    artillery_stats = {
        'unitType': 'AL',
        'move': al_stats.movement,
        'attack': {'value': al_stats.attack_value, 'range': al_stats.attack_range},
        'combat_value': al_stats.combat_value,
        'defense_value': al_stats.defense_value,
        'maintenance': al_stats.maintenance,
        'sight': al_stats.sight
    }
    
    artillery = Token("art_test", "1 (Polska)", artillery_stats, 10, 10)
    artillery.currentMovePoints = 3  # Ma punkty ruchu
    
    target_stats = compute_token('P', 'Pluton', 'Niemcy', [])
    target_token_stats = {
        'unitType': 'P',
        'move': target_stats.movement,
        'attack': {'value': target_stats.attack_value, 'range': target_stats.attack_range},
        'combat_value': target_stats.combat_value,
        'defense_value': target_stats.defense_value,
        'maintenance': target_stats.maintenance,
        'sight': target_stats.sight
    }
    
    target = Token("target_test", "2 (Niemcy)", target_token_stats, 11, 10)
    
    engine = MockEngine()
    engine.tokens = [artillery, target]
    
    # Pierwszy atak powinien się udać
    action1 = CombatAction(artillery.id, target.id, is_reaction=False)
    valid, message = action1._validate_combat(engine, artillery, target)
    assert valid == True, f"Pierwszy atak powinien być możliwy: {message}"
    
    # Symuluj wykonanie ataku
    artillery.record_attack('normal')
    
    # Drugi atak powinien się nie udać
    action2 = CombatAction(artillery.id, target.id, is_reaction=False)
    valid, message = action2._validate_combat(engine, artillery, target)
    assert valid == False, f"Drugi atak normalny powinien być niemożliwy"
    assert "już wystrzeliła" in message, f"Komunikat powinien wspominać o ograniczeniu strzałów: {message}"
    
    # Ale atak reakcyjny powinien być możliwy
    action3 = CombatAction(artillery.id, target.id, is_reaction=True)
    valid, message = action3._validate_combat(engine, artillery, target)
    assert valid == True, f"Atak reakcyjny powinien być możliwy: {message}"
    
    print("✅ Combat Action Integration: Wszystkie testy przeszły!")
    
    print("\n🎯 WSZYSTKIE TESTY SYSTEMU OGRANICZENIA STRZAŁÓW PRZESZŁY POMYŚLNIE!")
    print("\n📋 Podsumowanie systemu:")
    print("• Artyleria (AL, AC, AP): 1 normalny atak + 1 reakcyjny na turę")
    print("• Inne jednostki: bez ograniczeń")
    print("• Reset na początku każdej nowej tury")
    print("• Integracja z CombatAction - automatyczna walidacja")


if __name__ == "__main__":
    test_artillery_shot_limits()
