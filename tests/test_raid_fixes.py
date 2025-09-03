#!/usr/bin/env python3
"""Test script dla analizy poprawek rajdów AI"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.engine import GameEngine
from engine.player import Player
from ai.ai_commander import AICommander
from core.ekonomia import EconomySystem

def test_raid_fixes():
    """Test poprawek rajdów AI"""
    print("🚀 ROZPOCZYNANIE TESTU POPRAWEK RAJDÓW")
    print("="*50)
    
    # Utwórz GameEngine
    print("🔧 Tworzenie GameEngine...")
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=True
    )
    print(f"✅ GameEngine utworzony, tokenów: {len(game_engine.tokens)}")
    
    # Utwórz gracza z AI
    print("🤖 Tworzenie AI Commander...")
    player = Player(2, "Polska", "Dowódca", 5)
    player.is_ai_commander = True
    player.economy = EconomySystem()
    
    ai_commander = AICommander(player)
    print(f"✅ AI Commander utworzony dla gracza {player.id}")
    
    # Ustaw gracza jako aktualnego
    game_engine.current_player_obj = player
    game_engine.players = [player]
    
    # Diagnostyka stanu przed testem
    print("\n📊 DIAGNOSTYKA PRZED TESTEM:")
    polish_tokens = []
    for token in game_engine.tokens:
        owner = getattr(token, 'owner', '')
        if '2 (' in str(owner):  # Tokeny gracza 2
            polish_tokens.append(token)
    
    print(f"• Tokeny gracza 2: {len(polish_tokens)}")
    
    # Sprawdź key pointy
    kp_state = getattr(game_engine, 'key_points_state', {})
    free_kps = []
    for hex_id, kp_data in kp_state.items():
        if kp_data.get('current_value', 0) > 0:
            free_kps.append((hex_id, kp_data))
    
    print(f"• Wolne key pointy: {len(free_kps)}")
    
    # Test rajdów
    print("\n🎯 TESTOWANIE RAJDÓW:")
    try:
        # Najpierw resupply
        print("1. Pre-resupply...")
        ai_commander.pre_resupply(game_engine)
        
        print("2. Wykonanie tury taktycznej...")
        ai_commander.make_tactical_turn(game_engine)
        
        print("✅ Test zakończony pomyślnie!")
        
    except Exception as e:
        print(f"❌ Błąd podczas testu: {e}")
        import traceback
        traceback.print_exc()
    
    # Analiza CSV
    print("\n📄 SPRAWDZANIE LOGÓW CSV:")
    csv_files = []
    for root, dirs, files in os.walk("ai/logs"):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    
    print(f"• Znalezione pliki CSV: {len(csv_files)}")
    for csv_file in csv_files[-3:]:  # Ostatnie 3
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"  {csv_file}: {len(lines)} linii")
                if len(lines) > 1:
                    print(f"    Ostatnia: {lines[-1].strip()[:100]}...")
        except Exception as e:
            print(f"  {csv_file}: Błąd odczytu - {e}")
    
    print("\n🏁 TEST ZAKOŃCZONY")
    print("="*50)

if __name__ == "__main__":
    test_raid_fixes()
