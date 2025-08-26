#!/usr/bin/env python3
"""
Test pełnego łańcucha AI: Generał -> alokacja -> Dowódcy -> resupply
"""

import sys
import os
sys.path.append('.')

from engine.engine import GameEngine
from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander
from engine.player import Player

def test_full_ai_chain():
    print("🔧 Testing Full AI Chain: General → Allocation → Commanders → Resupply")
    
    # Załaduj engine z prawidłowymi argumentami
    map_path = 'data/map_data.json'
    tokens_index_path = 'assets/start_tokens.json'
    tokens_start_path = 'assets/tokens'
    
    if not os.path.exists(map_path):
        print("❌ Brak map_data.json")
        return
    
    engine = GameEngine(map_path, tokens_index_path, tokens_start_path)
    engine.load_game()
    print(f"🔧 Engine loaded, tokens count: {len(engine.tokens)}")
    
    # Znajdź graczy polskich i przygotuj prawdziwy test
    real_players = {}
    for player in engine.players:
        if player.nation == 'Polska':
            real_players[player.id] = player
            print(f"🔧 Found Polish player: {player.role} (id={player.id}) with {player.economy.get_points()['economic_points']} PE")
    
    if not real_players:
        print("❌ Brak polskich graczy")
        return
    
    # Znajdź generała (role='Generał')
    general = None
    commanders = []
    
    for player_id, player in real_players.items():
        if player.role == 'Generał':
            general = player
        elif player.role == 'Dowódca':
            commanders.append(player)
    
    if not general:
        print("❌ Brak polskiego generała")
        return
    
    if len(commanders) < 2:
        print("❌ Za mało polskich dowódców")
        return
    
    print(f"✅ Setup: General {general.id} z {general.economy.get_points()['economic_points']} PE")
    for cmd in commanders[:2]:
        print(f"✅ Setup: Commander {cmd.id} z {cmd.economy.get_points()['economic_points']} PE")
    
    # === FAZA 1: AI GENERAL ALOKUJE PUNKTY ===
    print("\n🎯 === FAZA 1: AI GENERAL ALLOCATION ===")
    ai_general = AIGeneral(general)
    
    # Sprawdź punkty przed
    pe_before = general.economy.get_points()['economic_points']
    cmd_pe_before = {cmd.id: cmd.economy.get_points()['economic_points'] for cmd in commanders[:2]}
    
    print(f"💰 Before: General={pe_before}, Commanders={cmd_pe_before}")
    
    # Wykonaj turę AI Generała
    ai_general.make_turn(engine)
    
    # Sprawdź punkty po
    pe_after = general.economy.get_points()['economic_points']
    cmd_pe_after = {cmd.id: cmd.economy.get_points()['economic_points'] for cmd in commanders[:2]}
    
    print(f"💰 After: General={pe_after}, Commanders={cmd_pe_after}")
    
    # Analiza alokacji
    allocated = pe_before - pe_after
    cmd_gained = {cmd.id: cmd_pe_after[cmd.id] - cmd_pe_before[cmd.id] for cmd in commanders[:2]}
    total_gained = sum(cmd_gained.values())
    
    print(f"📊 Allocation analysis:")
    print(f"   General allocated: {allocated} PE")
    print(f"   Commanders gained: {cmd_gained}")
    print(f"   Total gained: {total_gained} PE")
    print(f"   Balance: {allocated - total_gained} PE (should be close to 0)")
    
    if total_gained > 0:
        print("✅ ALOKACJA DZIAŁA!")
    else:
        print("❌ BRAK ALOKACJI!")
        return
    
    # === FAZA 2: AI COMMANDERS RESUPPLY ===
    print("\n🎯 === FAZA 2: AI COMMANDERS RESUPPLY ===")
    
    for commander in commanders[:2]:
        print(f"\n👤 Testing Commander {commander.id}:")
        
        # Znajdź jednostki dowódcy z niskim paliwem
        low_fuel_tokens = []
        all_tokens = []
        
        for token in engine.tokens:
            if hasattr(token, 'owner') and token.owner and str(commander.id) in token.owner:
                all_tokens.append(token)
                if hasattr(token, 'currentFuel') and hasattr(token, 'maxFuel'):
                    if token.currentFuel < token.maxFuel * 0.7:  # Mniej niż 70%
                        low_fuel_tokens.append(token)
        
        print(f"   📊 Total units: {len(all_tokens)}, Low fuel: {len(low_fuel_tokens)}")
        
        if not all_tokens:
            print(f"   ❌ Brak jednostek dla dowódcy {commander.id}")
            continue
        
        # Sprawdź PE przed resupply
        pe_before_resupply = commander.economy.get_points()['economic_points']
        
        # Przykładowe obniżenie paliwa dla testu
        if not low_fuel_tokens and all_tokens:
            test_token = all_tokens[0]
            original_fuel = test_token.currentFuel
            test_token.currentFuel = max(1, test_token.currentFuel // 2)  # Zmniejsz paliwo
            print(f"   🔧 Test: Reduced fuel {original_fuel} → {test_token.currentFuel} for {test_token.id}")
            low_fuel_tokens = [test_token]
        
        # Wykonaj AI Commander resupply
        ai_commander = AICommander(commander)
        resupply_result = ai_commander.pre_resupply(engine)
        
        # Sprawdź wyniki
        pe_after_resupply = commander.economy.get_points()['economic_points']
        pe_spent = pe_before_resupply - pe_after_resupply
        
        print(f"   💰 PE: {pe_before_resupply} → {pe_after_resupply} (spent: {pe_spent})")
        
        if pe_spent > 0:
            print(f"   ✅ RESUPPLY EXECUTED: {pe_spent} PE spent")
        else:
            print(f"   ❌ NO RESUPPLY: 0 PE spent")
    
    print("\n🏆 === FULL AI CHAIN TEST COMPLETE ===")

if __name__ == "__main__":
    test_full_ai_chain()
