#!/usr/bin/env python3
"""
SZYBKI TEST AI COMMANDER z prawdziwymi danymi
"""

import sys
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Dodaj główny katalog do path

from engine.engine import GameEngine
from engine.player import Player
from ai.ai_commander import AICommander, make_tactical_turn

def test_ai_with_real_data():
    """Test AI Commander z prawdziwymi danymi gry"""
    print("🧪 TEST AI COMMANDER z prawdziwymi danymi...")
    
    try:
        # Stwórz engine z prawdziwymi danymi
        engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json",
            tokens_start_path="assets/start_tokens.json"
        )
        
        # Stwórz gracza testowego
        test_player = Player(2, "Polska", "Dowódca", 300)
        engine.current_player_obj = test_player
        
        print(f"✅ Gra załadowana:")
        print(f"   Tokeny: {len(engine.tokens)}")
        print(f"   Key points: {len(getattr(engine, 'key_points_state', {}))}")
        
        # Sprawdź ile jednostek ma player 2 (Polska)
        my_tokens = [t for t in engine.tokens if "Polska" in str(getattr(t, 'owner', ''))]
        print(f"   Polskie jednostki: {len(my_tokens)}")
        
        if my_tokens:
            for i, token in enumerate(my_tokens[:3]):  # Pokaż pierwsze 3
                print(f"     {i+1}. {getattr(token, 'id', 'No_ID')} at ({getattr(token, 'q', '?')},{getattr(token, 'r', '?')}) MP:{getattr(token, 'currentMovePoints', 0)}")
        
        # URUCHOM AI COMMANDER
        print("\n🚀 URUCHAMIAM AI COMMANDER...")
        
        # Zapamiętaj pozycje przed ruchem
        before_positions = {}
        for token in my_tokens:
            token_id = getattr(token, 'id', 'No_ID')
            q = getattr(token, 'q', None)
            r = getattr(token, 'r', None)
            before_positions[token_id] = (q, r)
        
        make_tactical_turn(engine)
        
        # Sprawdź pozycje po ruchu
        moves_made = 0
        for token in my_tokens:
            token_id = getattr(token, 'id', 'No_ID')
            q = getattr(token, 'q', None)
            r = getattr(token, 'r', None)
            before_pos = before_positions.get(token_id, (None, None))
            
            if before_pos != (q, r):
                print(f"[RUCH] {token_id}: {before_pos} -> ({q},{r})")
                moves_made += 1
        
        if moves_made == 0:
            print("[INFO] Żadna jednostka się nie przesunęła")
        
        print("✅ AI Commander zakończył turę!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_ai_with_real_data()
