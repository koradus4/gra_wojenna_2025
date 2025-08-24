"""Test AI Commander - sprawdzenie wykorzystania pełnego MP"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine.engine import GameEngine
from engine.player import Player
from ai.ai_commander import make_tactical_turn

def test_ai_mp_usage():
    """Test czy AI wykorzystuje pełne MP jednostek"""
    try:
        print("🧪 TEST WYKORZYSTANIA MP PRZEZ AI...")
        
        # Załaduj grę
        base_dir = os.path.dirname(os.path.dirname(__file__))
        engine = GameEngine(
            map_path=os.path.join(base_dir, "data/map_data.json"),
            tokens_index_path=os.path.join(base_dir, "assets/tokens/index.json"), 
            tokens_start_path=os.path.join(base_dir, "assets/start_tokens.json")
        )
        
        print(f"✅ Gra załadowana: {len(engine.tokens)} tokenów")
        
        # Sprawdź pozycje przed ruchem dla kilku kluczowych jednostek
        test_units = [
            'AL_Kompania__2_Dywizjon_Artylerii',  # MP:6
            'TL_Pluton__2_Pluton_Tankietek_20250703213014',  # MP:5
            'P_Batalion__3_Pu_k_Piechoty'  # MP:4
        ]
        
        before_positions = {}
        for token in engine.tokens:
            token_id = getattr(token, 'id', '')
            if token_id in test_units:
                q = getattr(token, 'q', None)
                r = getattr(token, 'r', None)
                mp = getattr(token, 'currentMovePoints', 0)
                before_positions[token_id] = {
                    'pos': (q, r),
                    'mp': mp
                }
                print(f"📍 {token_id}: {(q,r)} (MP:{mp})")
        
        # Test dla gracza 2 (Polska)
        print("\n🚀 URUCHAMIAM AI DLA GRACZA 2...")
        make_tactical_turn(engine, player_id=2)
        
        # Sprawdź pozycje po ruchu
        print("\n📊 ANALIZA PRZEMIESZCZEŃ:")
        for token in engine.tokens:
            token_id = getattr(token, 'id', '')
            if token_id in test_units and token_id in before_positions:
                q = getattr(token, 'q', None)
                r = getattr(token, 'r', None)
                
                before_pos = before_positions[token_id]['pos']
                after_pos = (q, r)
                mp = before_positions[token_id]['mp']
                
                # Oblicz dystans (Manhattan distance w hex)
                distance = abs(after_pos[0] - before_pos[0]) + abs(after_pos[1] - before_pos[1])
                
                efficiency = (distance / mp * 100) if mp > 0 else 0
                
                print(f"🚶 {token_id}")
                print(f"   {before_pos} → {after_pos}")
                print(f"   Dystans: {distance} hexów, MP: {mp}, Efektywność: {efficiency:.1f}%")
                
                if distance < mp / 2:
                    print(f"   ⚠️  MARNOTRAWSTWO MP! Jednostka wykorzystała tylko {distance}/{mp} MP")
                elif distance >= mp * 0.8:
                    print(f"   ✅ Dobre wykorzystanie MP!")
                else:
                    print(f"   🟡 Umiarkowane wykorzystanie MP")
        
        print("\n✅ Test zakończony!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_ai_mp_usage()
