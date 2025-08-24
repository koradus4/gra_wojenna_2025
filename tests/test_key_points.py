"""Test key points - sprawdzenie czy AI znajduje key points w zasięgu"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine.engine import GameEngine

def test_key_points():
    """Sprawdź key points dostępne dla AI"""
    try:
        print("🗺️ TEST KEY POINTS...")
        
        # Załaduj grę
        base_dir = os.path.dirname(os.path.dirname(__file__))
        engine = GameEngine(
            map_path=os.path.join(base_dir, "data/map_data.json"),
            tokens_index_path=os.path.join(base_dir, "assets/tokens/index.json"), 
            tokens_start_path=os.path.join(base_dir, "assets/start_tokens.json")
        )
        
        print(f"✅ Gra załadowana: {len(engine.tokens)} tokenów")
        
        # Sprawdź key points
        key_points = getattr(engine, 'key_points_state', {})
        print(f"🎯 Key points: {len(key_points)}")
        
        for hex_id, kp_data in list(key_points.items())[:5]:
            print(f"   {hex_id}: {kp_data}")
        
        # Sprawdź jednostkę testową
        test_unit = None
        for token in engine.tokens:
            if getattr(token, 'id', '') == 'AL_Kompania__2_Dywizjon_Artylerii':
                test_unit = {
                    'id': getattr(token, 'id', ''),
                    'q': getattr(token, 'q', 0),
                    'r': getattr(token, 'r', 0),
                    'mp': getattr(token, 'currentMovePoints', 0)
                }
                break
        
        if test_unit:
            print(f"\n🔍 ANALIZA DLA {test_unit['id']}:")
            print(f"   Pozycja: ({test_unit['q']}, {test_unit['r']})")
            print(f"   MP: {test_unit['mp']}")
            
            unit_pos = (test_unit['q'], test_unit['r'])
            
            # Sprawdź key points w zasięgu
            reachable_kp = []
            for hex_id, kp_data in key_points.items():
                try:
                    parts = hex_id.split('_')
                    if len(parts) >= 2:
                        kp_q = int(parts[0])
                        kp_r = int(parts[1])
                        kp_pos = (kp_q, kp_r)
                        
                        dist = abs(kp_pos[0] - unit_pos[0]) + abs(kp_pos[1] - unit_pos[1])
                        
                        if dist <= test_unit['mp']:
                            reachable_kp.append({
                                'hex_id': hex_id,
                                'pos': kp_pos,
                                'distance': dist
                            })
                except (ValueError, IndexError):
                    continue
            
            print(f"\n📍 Key points w zasięgu MP ({test_unit['mp']}):")
            if reachable_kp:
                for kp in sorted(reachable_kp, key=lambda x: x['distance'])[:5]:
                    print(f"   {kp['hex_id']} na {kp['pos']} (dystans: {kp['distance']})")
            else:
                print("   ❌ BRAK key points w zasięgu!")
                print("   💡 Dlatego AI używa fallback celów tylko 1 hex dalej")
        
        print("\n✅ Test zakończony!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_key_points()
