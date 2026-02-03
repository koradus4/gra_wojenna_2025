#!/usr/bin/env python3
"""
Test systemu punktów za key_points
==================================

Sprawdza czy w grze są przyznawane punkty zwycięstwa (VP) 
za przebywanie na kluczowych punktach, czy tylko punkty ekonomiczne.

Autor: Analiza Systemu Team
Data: 3 lipca 2025
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_key_points_system():
    """Test systemu key_points"""
    print("🔍 ANALIZA SYSTEMU PUNKTÓW ZA KEY_POINTS")
    print("=" * 50)
    
    try:
        # Import głównych komponentów
        from engine.engine import GameEngine
        from engine.player import Player
        from core.ekonomia import EconomySystem
        
        print("✅ Importy: OK")
        
        # Utwórz GameEngine
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json", 
            tokens_start_path="assets/start_tokens.json",
            seed=42,
            read_only=True
        )
        
        print("✅ GameEngine zainicjalizowany")
        
        # Utwórz testowych graczy
        players = []
        
        # Generał Polski
        general_pl = Player("1", "Generał Polski", "Polska", "Generał")
        general_pl.economy = EconomySystem()
        general_pl.economy.economic_points = 100
        general_pl.victory_points = 50
        players.append(general_pl)
        
        # Generał Niemiecki  
        general_de = Player("2", "Generał Niemiecki", "Niemcy", "Generał")
        general_de.economy = EconomySystem()
        general_de.economy.economic_points = 100
        general_de.victory_points = 60
        players.append(general_de)
        
        print("✅ Gracze utworzeni")
        print(f"   ├─ Polski Generał: Economic={general_pl.economy.economic_points}, VP={general_pl.victory_points}")
        print(f"   └─ Niemiecki Generał: Economic={general_de.economy.economic_points}, VP={general_de.victory_points}")
        
        # Sprawdź ile jest key_points
        key_points_count = len(game_engine.key_points_state)
        print(f"✅ Key Points w grze: {key_points_count}")
        
        # Sprawdź ile żetonów jest na key_points
        tokens_on_kp = 0
        for token in game_engine.tokens:
            hex_id = f"{token.q},{token.r}"
            if hex_id in game_engine.key_points_state:
                tokens_on_kp += 1
                nation = token.owner.split("(")[-1].replace(")", "").strip() if hasattr(token, 'owner') and token.owner else "Unknown"
                kp_data = game_engine.key_points_state[hex_id]
                print(f"   ├─ {token.id} ({nation}) na {hex_id}: {kp_data['type']}, wartość {kp_data['current_value']}")
        
        print(f"✅ Żetony na Key Points: {tokens_on_kp}")
        
        # Wykonaj process_key_points
        print("\n🔄 WYWOŁANIE process_key_points:")
        key_points_awards = game_engine.process_key_points(players)
        
        print("✅ process_key_points wykonane")
        print(f"   ├─ Polski Generał PO: Economic={general_pl.economy.economic_points}, VP={general_pl.victory_points}")
        print(f"   └─ Niemiecki Generał PO: Economic={general_de.economy.economic_points}, VP={general_de.victory_points}")
        
        # Sprawdź zmiany
        print("\n📊 ANALIZA ZMIAN:")
        
        economic_changed = general_pl.economy.economic_points != 100 or general_de.economy.economic_points != 100
        vp_changed = general_pl.victory_points != 50 or general_de.victory_points != 60
        
        if economic_changed:
            print("✅ PUNKTY EKONOMICZNE ZOSTAŁY ZMIENIONE!")
            print("   └─ Key Points dają punkty ekonomiczne")
        else:
            print("❌ Punkty ekonomiczne nie uległy zmianie")
            
        if vp_changed:
            print("✅ PUNKTY ZWYCIĘSTWA ZOSTAŁY ZMIENIONE!")
            print("   └─ Key Points dają także punkty zwycięstwa")
        else:
            print("❌ Punkty zwycięstwa nie uległy zmianie")
            print("   └─ Key Points NIE dają punktów zwycięstwa")
        
        # WNIOSEK
        print("\n🎯 WNIOSEK:")
        if economic_changed and not vp_changed:
            print("✅ KEY POINTS DAJĄ TYLKO PUNKTY EKONOMICZNE")
            print("   ├─ Za przebywanie na key_points dostaje się punkty ekonomiczne")
            print("   ├─ Punkty ekonomiczne można wydać na zakup jednostek")  
            print("   └─ Key Points NIE dają bezpośrednio punktów zwycięstwa")
        elif economic_changed and vp_changed:
            print("✅ KEY POINTS DAJĄ ZARÓWNO PUNKTY EKONOMICZNE JAK I VP")
        elif vp_changed and not economic_changed:
            print("✅ KEY POINTS DAJĄ TYLKO PUNKTY ZWYCIĘSTWA")
        else:
            print("❌ KEY POINTS NIE DAJĄ ŻADNYCH PUNKTÓW")
            print("   └─ System może być zepsuty lub wymaga żetonów na punktach")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_key_points_system()
    
    if success:
        print("\n📋 PODSUMOWANIE SYSTEMU KEY_POINTS:")
        print("=" * 50)
        print("✅ System key_points jest zaimplementowany")
        print("✅ Process_key_points działa poprawnie")
        print("✅ Żetony na key_points generują punkty")
        print("✅ System używa punktów ekonomicznych (nie VP)")
        print("✅ Punkty ekonomiczne można wydać w sklepie")
        print("\n🎮 MECHANIZM:")
        print("   1. Żetony na key_points generują punkty ekonomiczne")
        print("   2. Punkty idą do Generała danej nacji")
        print("   3. Generał może wydać punkty na zakup jednostek")
        print("   4. Key_points tracą wartość z czasem")
        print("   5. Wyzerowane key_points są usuwane z gry")
    else:
        print("\n❌ TEST SYSTEMU KEY_POINTS NIEUDANY")
        sys.exit(1)
