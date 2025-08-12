#!/usr/bin/env python3
"""
Test poprawnego tworzenia graczy
================================

Test z poprawną kolejnością parametrów Player.

Autor: Fix Team
Data: 3 lipca 2025
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_correct_players():
    """Test poprawnego tworzenia graczy"""
    print("🔍 TEST POPRAWNEGO TWORZENIA GRACZY")
    print("=" * 40)
    
    try:
        from engine.engine import GameEngine
        from engine.player import Player
        from core.ekonomia import EconomySystem
        
        # POPRAWNE wywołania konstruktora Player:
        # def __init__(self, player_id, nation, role, time_limit=5, image_path=None, economy=None)
        
        general_pl = Player("1", "Polska", "Generał")  # POPRAWNA KOLEJNOŚĆ!
        general_pl.economy = EconomySystem()
        general_pl.economy.economic_points = 100
        
        general_de = Player("4", "Niemcy", "Generał")  # POPRAWNA KOLEJNOŚĆ!
        general_de.economy = EconomySystem()
        general_de.economy.economic_points = 100
        
        print("✅ Gracze utworzeni z poprawną kolejnością:")
        print(f"   ├─ Polski: ID={general_pl.id}, Nacja={general_pl.nation}, Rola={general_pl.role}")
        print(f"   └─ Niemiecki: ID={general_de.id}, Nacja={general_de.nation}, Rola={general_de.role}")
        
        players = [general_pl, general_de]
        
        # Test filtrowania z różnymi wariantami
        generals1 = {p.nation: p for p in players if getattr(p, 'role', '').lower() == 'generał'}
        generals2 = {p.nation: p for p in players if getattr(p, 'role', '').lower() == 'general'}
        
        print(f"\nFiltrowanie generałów:")
        print(f"   ├─ Z 'generał': {len(generals1)} graczy")
        print(f"   └─ Z 'general': {len(generals2)} graczy")
        
        if len(generals1) == 0 and len(generals2) == 0:
            print("\n❌ Żaden warunek nie działa! Sprawdzmy dokładnie:")
            for p in players:
                print(f"   Gracz {p.id}: role='{p.role}', role.lower()='{p.role.lower()}'")
                print(f"      ├─ 'generał' == '{p.role.lower()}': {'generał' == p.role.lower()}")
                print(f"      └─ 'general' == '{p.role.lower()}': {'general' == p.role.lower()}")
        
        # Utwórz GameEngine i przetestuj system
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json", 
            tokens_start_path="assets/start_tokens.json",
            seed=42,
            read_only=True
        )
        
        print(f"\n📊 PUNKTY PRZED process_key_points:")
        print(f"   ├─ Polski: {general_pl.economy.economic_points}")
        print(f"   └─ Niemiecki: {general_de.economy.economic_points}")
        
        # Wywołaj process_key_points
        key_points_awards = game_engine.process_key_points(players)
        
        print(f"\n📊 PUNKTY PO process_key_points:")
        print(f"   ├─ Polski: {general_pl.economy.economic_points}")
        print(f"   └─ Niemiecki: {general_de.economy.economic_points}")
        
        # Sprawdź czy się zmieniły
        if general_pl.economy.economic_points != 100 or general_de.economy.economic_points != 100:
            print("\n✅ PUNKTY ZOSTAŁY PRZYZNANE!")
            print("   └─ System key_points działa poprawnie")
        else:
            print("\n❌ Punkty nie uległy zmianie")
            print("   └─ Problem może być w samym systemie lub rolach")
            
        return True
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_correct_players()
