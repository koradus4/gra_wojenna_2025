"""Test finalny AI Commander - bez nadmiaru debugowania"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Dodaj główny katalog do path

from engine.engine import GameEngine
from ai.ai_commander import make_tactical_turn

def test_ai_final():
    """Test AI Commander z minimalnymi logami"""
    try:
        print("🧪 TEST FINALNY AI COMMANDER...")
        
        # Załaduj grę
        engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json", 
            tokens_start_path="assets/start_tokens.json"
        )
        
        # Nie ładujemy save file - używamy świeżej gry
        # success = engine.load_state("archive/backup_files/autosave_20250817_122513.json")
        
        print(f"✅ Gra załadowana: {len(engine.tokens)} tokenów")
        
        # Test dla gracza 2 (Polska)
        print("\n🚀 TEST Polska (id=2)...")
        make_tactical_turn(engine, player_id=2)
        
        # Test dla gracza 5 (Niemcy)  
        print("\n🚀 TEST Niemcy (id=5)...")
        make_tactical_turn(engine, player_id=5)
        
        print("\n✅ Testy zakończone!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_ai_final()
