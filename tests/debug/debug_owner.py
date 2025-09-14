#!/usr/bin/env python3
"""
🔍 DEBUG OWNER PROBLEM
Sprawdzamy dlaczego my_owner nie pasuje do token.owner
"""

from engine.engine import GameEngine
from ai.ai_config import set_player_ai_profile, AIProfile
from ai.ai_commander import get_player_nation

def debug_owner_problem():
    """Debug problemu z owner matchingiem"""
    
    print("🔍 DEBUG - OWNER PROBLEM")
    print("="*50)
    
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=False
    )
    
    # Test gracza 2 i 3
    for player_id in [2, 3]:
        print(f"\n🧪 TEST GRACZA {player_id}:")
        
        # Sprawdź co zwraca get_player_nation
        nation = get_player_nation(game_engine, player_id)
        my_owner = f"{player_id} ({nation})"
        print(f"   my_owner = '{my_owner}'")
        
        # Sprawdź co mają tokeny tego gracza
        for token in game_engine.tokens:
            if str(player_id) in token.owner:
                print(f"   token.owner = '{token.owner}'")
                print(f"   Czy pasuje: {token.owner == my_owner}")
                break

if __name__ == "__main__":
    debug_owner_problem()