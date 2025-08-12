#!/usr/bin/env python3
"""
Debug test systemu key_points
=============================

Szczegółowa analiza dlaczego punkty nie są przyznawane.

Autor: Debug Team
Data: 3 lipca 2025
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def debug_key_points():
    """Debug systemu key_points"""
    print("🔍 DEBUG SYSTEMU KEY_POINTS")
    print("=" * 40)
    
    try:
        from engine.engine import GameEngine
        from engine.player import Player
        from core.ekonomia import EconomySystem
        
        # Utwórz GameEngine
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json", 
            tokens_start_path="assets/start_tokens.json",
            seed=42,
            read_only=True
        )
        
        # Utwórz testowych graczy - WAŻNE: role z małych liter!
        players = []
        
        general_pl = Player("1", "Polski Generał", "Polska", "generał")  # małe g!
        general_pl.economy = EconomySystem()
        general_pl.economy.economic_points = 100
        players.append(general_pl)
        
        general_de = Player("4", "Niemiecki Generał", "Niemcy", "generał")  # małe g!
        general_de.economy = EconomySystem()
        general_de.economy.economic_points = 100
        players.append(general_de)
        
        print("✅ Gracze z poprawną rolą 'generał'")
        
        # Sprawdź filtrowanie generałów
        generals = {p.nation: p for p in players if getattr(p, 'role', '').lower() == 'generał'}
        print(f"✅ Znalezionych generałów: {len(generals)}")
        for nation, general in generals.items():
            print(f"   ├─ {nation}: {general.name} (id={general.id})")
        
        # Sprawdź żetony na key_points szczegółowo
        print("\n🔍 SZCZEGÓŁOWA ANALIZA ŻETONÓW:")
        tokens_by_pos = {(t.q, t.r): t for t in game_engine.tokens}
        
        key_points_with_tokens = 0
        for hex_id, kp in game_engine.key_points_state.items():
            q, r = map(int, hex_id.split(","))
            token = tokens_by_pos.get((q, r))
            
            if token and hasattr(token, 'owner') and token.owner:
                key_points_with_tokens += 1
                nation = token.owner.split("(")[-1].replace(")", "").strip()
                general = generals.get(nation)
                
                print(f"   Hex {hex_id}: {kp['type']}, wartość {kp['current_value']}")
                print(f"      ├─ Żeton: {token.id}")
                print(f"      ├─ Owner: '{token.owner}'")
                print(f"      ├─ Wyciągnięta nacja: '{nation}'")
                print(f"      ├─ Znaleziony generał: {general.name if general else 'BRAK'}")
                if general:
                    give = int(0.1 * kp['initial_value'])
                    if give < 1:
                        give = 1
                    print(f"      ├─ Ma economy: {hasattr(general, 'economy')}")
                    print(f"      └─ Powinien dostać: {give} punktów")
                else:
                    print(f"      └─ ❌ BRAK GENERAŁA dla nacji '{nation}'!")
        
        print(f"\n✅ Key Points z żetonami: {key_points_with_tokens}")
        
        # Sprawdź początkowe punkty
        print(f"\n📊 PUNKTY PRZED:")
        for nation, general in generals.items():
            print(f"   {nation}: {general.economy.economic_points}")
        
        # Wywołaj process_key_points
        print("\n🔄 WYWOŁANIE process_key_points...")
        key_points_awards = game_engine.process_key_points(players)
        
        # Sprawdź końcowe punkty
        print(f"\n📊 PUNKTY PO:")
        for nation, general in generals.items():
            print(f"   {nation}: {general.economy.economic_points}")
        
        # Sprawdź czy key_points straciły wartość
        print(f"\n📊 WARTOŚCI KEY_POINTS PO PROCESIE:")
        for hex_id, kp in game_engine.key_points_state.items():
            if (int(hex_id.split(",")[0]), int(hex_id.split(",")[1])) in tokens_by_pos:
                print(f"   {hex_id}: {kp['current_value']} (było {kp['initial_value']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    debug_key_points()
