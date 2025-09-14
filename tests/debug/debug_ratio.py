#!/usr/bin/env python3
"""
🎲 DEBUG COMBAT RATIO
Sprawdzamy jak liczony jest combat ratio
"""

from engine.engine import GameEngine

def debug_combat_ratio():
    """Debug obliczania ratio"""
    
    print("🎲 DEBUG COMBAT RATIO")  
    print("="*50)
    
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=False
    )
    
    # Znajdź jednostki
    cavalry = None
    infantry = None
    
    for token in game_engine.tokens:
        if token.id == "K_Pluton__3_Oddzia_Jazdy":
            cavalry = token
        elif token.id == "P_Batalion__6_Infanterie_Regiment":
            infantry = token
    
    print(f"🐎 KAWALERIA: {cavalry.id}")
    print(f"   ⚔️ Attack: {cavalry.stats.get('attack', {})}")
    print(f"   🛡️ Defense: {cavalry.stats.get('defense_value', 0)}")
    print(f"   ❤️ HP: {getattr(cavalry, 'combat_value', 0)}")
    
    print(f"\n🪖 PIECHOTA: {infantry.id}")
    print(f"   ⚔️ Attack: {infantry.stats.get('attack', {})}")
    print(f"   🛡️ Defense: {infantry.stats.get('defense_value', 0)}")
    print(f"   ❤️ HP: {getattr(infantry, 'combat_value', 0)}")
    
    # Ręczne obliczenie ratio
    cav_attack = cavalry.stats.get('attack', {}).get('value', 0)
    inf_defense = infantry.stats.get('defense_value', 0)
    
    print(f"\n🎲 OBLICZENIE RATIO:")
    print(f"   Cavalry Attack Value: {cav_attack}")
    print(f"   Infantry Defense Value: {inf_defense}")
    
    if inf_defense > 0:
        manual_ratio = cav_attack / inf_defense
        print(f"   Manual Ratio: {cav_attack} / {inf_defense} = {manual_ratio:.2f}")
    else:
        print(f"   Manual Ratio: Nie można dzielić przez 0")
    
    # Sprawdź czy to jest ratio porównane z progiem
    threshold = 0.72
    print(f"\n📊 PORÓWNANIE Z PROGIEM:")
    print(f"   Próg (aggressive): {threshold}")
    print(f"   Calculated ratio: {manual_ratio:.2f} {'✅' if manual_ratio >= threshold else '❌'}")
    
    return cavalry, infantry

if __name__ == "__main__":
    debug_combat_ratio()