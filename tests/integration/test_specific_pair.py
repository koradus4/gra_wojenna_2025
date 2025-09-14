#!/usr/bin/env python3
"""
🎯 TEST KONKRETNEJ PARY
Test cavalry vs infantry - najbliższy przypadek
"""

from engine.engine import GameEngine
from ai.ai_config import set_player_ai_profile, AIProfile
from ai.walka_ai import ai_attempt_combat

def test_specific_pair():
    """Test konkretnej najbliższej pary"""
    
    print("🎯 TEST KONKRETNEJ PARY WROGÓW")
    print("="*50)
    
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=False
    )
    
    # Ustawienia profile
    set_player_ai_profile(3, AIProfile.AGGRESSIVE)  # Polish cavalry
    set_player_ai_profile(6, AIProfile.DEFENSIVE)   # German infantry
    
    # Znajdź konkretne jednostki
    cavalry = None
    infantry = None
    
    for token in game_engine.tokens:
        if token.id == "K_Pluton__3_Oddzia_Jazdy":
            cavalry = token
        elif token.id == "P_Batalion__6_Infanterie_Regiment":
            infantry = token
    
    if not cavalry or not infantry:
        print("❌ Nie znaleziono jednostek")
        return
    
    print(f"🐎 KAWALERIA: {cavalry.id}")
    print(f"   📍 Pozycja: q={cavalry.q}, r={cavalry.r}")
    print(f"   👁️ Wzrok: {cavalry.stats.get('sight', 0)}")
    print(f"   🎯 Zasięg ataku: {cavalry.stats.get('attack', {}).get('range', 1)}")
    print(f"   ⚔️ Wartość ataku: {cavalry.stats.get('attack', {}).get('value', 0)}")
    
    print(f"\n🪖 PIECHOTA: {infantry.id}")
    print(f"   📍 Pozycja: q={infantry.q}, r={infantry.r}")
    print(f"   👁️ Wzrok: {infantry.stats.get('sight', 0)}")
    print(f"   🎯 Zasięg ataku: {infantry.stats.get('attack', {}).get('range', 1)}")
    print(f"   ⚔️ Wartość ataku: {infantry.stats.get('attack', {}).get('value', 0)}")
    
    # Sprawdź odległość
    board = getattr(game_engine, 'board', None)
    if board:
        distance = board.hex_distance(
            (cavalry.q, cavalry.r),
            (infantry.q, infantry.r)
        )
        print(f"\n📏 ODLEGŁOŚĆ: {distance} hexów")
    
    # Test combat dla cavalerii (gracz 3)
    print(f"\n🔥 TEST COMBAT - KAWALERIA ATAKUJE:")
    unit_dict = {
        'id': cavalry.id,
        'token': cavalry,
        'q': cavalry.q,
        'r': cavalry.r
    }
    
    result = ai_attempt_combat(unit_dict, game_engine, 3)
    print(f"   ✅ Wynik: {result}")
    
    return cavalry, infantry

if __name__ == "__main__":
    test_specific_pair()