#!/usr/bin/env python3
"""
🔧 ZWIĘKSZ ATTACK RANGE - TYMCZASOWE ROZWIĄZANIE
Testuje czy zwiększenie zasięgu ataku pozwoli AI atakować
"""

from engine.engine import GameEngine
from ai.ai_config import set_player_ai_profile, AIProfile
from ai.walka_ai import ai_attempt_combat

def test_with_increased_range():
    """Test z zwiększonym zasięgiem ataku"""
    
    print("🔧 TEST Z ZWIĘKSZONYM ATTACK RANGE")
    print("="*50)
    
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=False
    )
    
    # Profile
    set_player_ai_profile(3, AIProfile.AGGRESSIVE)  
    
    # Znajdź kawalerię
    cavalry = None
    for token in game_engine.tokens:
        if token.id == "K_Pluton__3_Oddzia_Jazdy":
            cavalry = token
            break
    
    if not cavalry:
        print("❌ Nie znaleziono kawalerii")
        return
    
    # TYMCZASOWO ZWIĘKSZ ATTACK RANGE
    original_range = cavalry.stats.get('attack', {}).get('range', 1)
    print(f"📊 Oryginalny zasięg: {original_range}")
    
    # Zwiększ zasięg do 6 hexów
    if 'attack' not in cavalry.stats:
        cavalry.stats['attack'] = {}
    cavalry.stats['attack']['range'] = 6
    
    new_range = cavalry.stats.get('attack', {}).get('range', 1)
    print(f"📊 Nowy zasięg: {new_range}")
    
    print(f"\n🐎 KAWALERIA: {cavalry.id}")
    print(f"   📍 Pozycja: q={cavalry.q}, r={cavalry.r}")
    print(f"   👁️ Wzrok: {cavalry.stats.get('sight', 0)}")
    print(f"   🎯 Zasięg ataku: {new_range}")
    
    # Test combat
    print(f"\n🔥 TEST COMBAT - ZWIĘKSZONY RANGE:")
    unit_dict = {
        'id': cavalry.id,
        'token': cavalry,
        'q': cavalry.q,
        'r': cavalry.r
    }
    
    result = ai_attempt_combat(unit_dict, game_engine, 3)
    print(f"   ✅ Wynik ataku: {result}")
    
    return result

if __name__ == "__main__":
    result = test_with_increased_range()
    print(f"\n🎯 KOŃCOWY WYNIK: {'SUCCESS' if result else 'FAILED'}")