"""Test MP jednostek - sprawdzenie rzeczywistych wartości"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # Dodaj główny katalog do path

from engine.engine import GameEngine
from engine.player import Player

def test_unit_mp():
    """Sprawdź MP różnych typów jednostek"""
    try:
        print("🔍 SPRAWDZANIE MP JEDNOSTEK...")
        
        # Załaduj grę
        engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json", 
            tokens_start_path="assets/start_tokens.json"
        )
        
        print(f"✅ Gra załadowana: {len(engine.tokens)} tokenów")
        
        # Grupuj jednostki według typu
        unit_types = {}
        
        for token in engine.tokens:
            token_id = getattr(token, 'id', 'Unknown')
            mp = getattr(token, 'currentMovePoints', 0)
            fuel = getattr(token, 'currentFuel', 0)
            owner = str(getattr(token, 'owner', ''))
            
            # Wyciągnij typ jednostki (prefix)
            unit_type = token_id.split('_')[0] if '_' in token_id else 'Other'
            
            if unit_type not in unit_types:
                unit_types[unit_type] = []
            
            unit_types[unit_type].append({
                'id': token_id,
                'mp': mp,
                'fuel': fuel,
                'owner': owner
            })
        
        # Pokaż statystyki dla każdego typu
        print("\n📊 STATYSTYKI MP WEDŁUG TYPÓW:")
        for unit_type, units in sorted(unit_types.items()):
            if units:
                mp_values = [u['mp'] for u in units]
                avg_mp = sum(mp_values) / len(mp_values)
                max_mp = max(mp_values)
                min_mp = min(mp_values)
                
                print(f"\n{unit_type}:")
                print(f"  Ilość: {len(units)}")
                print(f"  MP: min={min_mp}, max={max_mp}, avg={avg_mp:.1f}")
                
                # Pokaż przykłady
                for unit in units[:3]:
                    print(f"    {unit['id'][:30]:<30} MP:{unit['mp']} Fuel:{unit['fuel']} {unit['owner']}")
                
                if len(units) > 3:
                    print(f"    ... i {len(units)-3} więcej")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_unit_mp()
