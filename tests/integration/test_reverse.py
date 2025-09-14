#!/usr/bin/env python3
"""
🔄 TEST ODWROTNY - PIECHOTA ATAKUJE KAWALERIĘ
"""

from engine.engine import GameEngine
from ai.ai_config import set_player_ai_profile, AIProfile
from ai.walka_ai import ai_attempt_combat

def test_reverse_attack():
    """Test piechoty atakującej kawalerię"""
    
    print("🔄 TEST ODWROTNY - PIECHOTA → KAWALERIA")
    print("="*50)
    
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=False
    )
    
    # Profile - aggressive dla Niemców
    set_player_ai_profile(6, AIProfile.AGGRESSIVE)  # German piechota
    
    # Znajdź piechote
    infantry = None
    cavalry = None
    for token in game_engine.tokens:
        if token.id == "P_Batalion__6_Infanterie_Regiment":
            infantry = token
        elif token.id == "K_Pluton__3_Oddzia_Jazdy":
            cavalry = token
    
    if not infantry or not cavalry:
        print("❌ Nie znaleziono jednostek")
        return
    
    # Zwiększ zasięg ataku i wzroku piechoty
    if 'attack' not in infantry.stats:
        infantry.stats['attack'] = {}
    infantry.stats['attack']['range'] = 6
    infantry.stats['sight'] = 6  # Zwiększ też sight
    
    print(f"🪖 PIECHOTA: {infantry.id}")
    print(f"   📍 Pozycja: q={infantry.q}, r={infantry.r}")
    print(f"   ⚔️ Atak: {infantry.stats.get('attack', {}).get('value', 0)}")
    
    print(f"\n🐎 KAWALERIA (CEL):")
    print(f"   📍 Pozycja: q={cavalry.q}, r={cavalry.r}")
    print(f"   🛡️ Obrona: {cavalry.stats.get('defense_value', 0)}")
    
    # Oblicz ratio ręcznie
    inf_attack = infantry.stats.get('attack', {}).get('value', 0)
    cav_defense = cavalry.stats.get('defense_value', 0)
    expected_ratio = inf_attack / cav_defense if cav_defense > 0 else 0
    
    print(f"\n🎲 OCZEKIWANY RATIO:")
    print(f"   Infantry Attack: {inf_attack}")
    print(f"   Cavalry Defense: {cav_defense}")
    print(f"   Expected Ratio: {expected_ratio:.2f}")
    print(f"   Próg (aggressive): 0.72")
    print(f"   Czy powinna zaatakować: {'✅' if expected_ratio >= 0.72 else '❌'}")
    
    # Test combat
    print(f"\n🔥 TEST COMBAT:")
    unit_dict = {
        'id': infantry.id,
        'token': infantry,
        'q': infantry.q,
        'r': infantry.r
    }
    
    result = ai_attempt_combat(unit_dict, game_engine, 6)
    print(f"   ✅ Rzeczywisty wynik: {result}")
    
    return result

if __name__ == "__main__":
    result = test_reverse_attack()
    print(f"\n🎯 WYNIK: {'AI ZAATAKOWAŁA!' if result else 'AI NIE ZAATAKOWAŁA'}")