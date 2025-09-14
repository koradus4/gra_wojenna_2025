#!/usr/bin/env python3
"""
🔍 DIAGNOZA - DLACZEGO AI NIE ATAKUJE
Sprawdzamy co się dzieje z jednostkami w grze
"""

from engine.engine import GameEngine
from engine.token import Token
from ai.ai_config import set_player_ai_profile, AIProfile
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')

def diagnose_units():
    """Diagnozuje czy są jednostki na mapie"""
    
    print("🔍 DIAGNOZA - Stan jednostek na mapie")
    print("="*50)
    
    # Tworzymy GameEngine jak w main.py
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json",
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=True
    )
    
    # Ustawiamy profile dla właściwych graczy (dowódcy mają jednostki)
    # Polska dowódcy: 2, 3 = aggressive
    # Niemiecki dowódcy: 5, 6 = defensive
    set_player_ai_profile(2, AIProfile.AGGRESSIVE)  # Polska dowódca 1
    set_player_ai_profile(3, AIProfile.AGGRESSIVE)  # Polska dowódca 2
    set_player_ai_profile(5, AIProfile.DEFENSIVE)   # German dowódca 1  
    set_player_ai_profile(6, AIProfile.DEFENSIVE)   # German dowódca 2
    
    print(f"📊 Tura: {game_engine.turn}")
    print(f"📊 Liczba żetonów: {len(game_engine.tokens)}")
    
    # Sprawdzamy wszystkie żetony
    all_tokens = []
    by_player = {}
    
    for token in game_engine.tokens:
        player_id = token.owner  # Użyj owner zamiast player
        unit_type = token.stats.get('label', token.id)  # Użyj label jako nazwa jednostki
        position = f"q={token.q}, r={token.r}"
        
        all_tokens.append((position, token.id, player_id, unit_type))
        print(f"🎖️ {position}: {unit_type} (owner: {player_id}) - {token.id}")
        
        if player_id not in by_player:
            by_player[player_id] = []
        by_player[player_id].append(unit_type)
    
    print(f"\n📊 Łącznie jednostek na mapie: {len(all_tokens)}")
    
    for player_id, units in sorted(by_player.items()):
        print(f"👤 Gracz {player_id}: {len(units)} jednostek")
        # Grupujemy po typach jednostek
        unit_counts = {}
        for unit in units:
            unit_counts[unit] = unit_counts.get(unit, 0) + 1
        for unit_type, count in unit_counts.items():
            print(f"   - {unit_type}: {count}")
    
    return game_engine

if __name__ == "__main__":
    game_state = diagnose_units()