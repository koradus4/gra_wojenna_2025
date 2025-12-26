#!/usr/bin/env python3
"""
🔍 DEBUG RANGES - Sprawdzamy zasięgi ataku i wzroku
"""

from engine.engine import GameEngine

def debug_ranges():
    """Debug zasięgów jednostek"""
    
    print("🔍 DEBUG - ZASIĘGI JEDNOSTEK")
    print("="*50)
    
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=False
    )
    
    # Sprawdź kilka jednostek z różnych graczy
    test_players = ['2 (Polska)', '3 (Polska)', '5 (Niemcy)', '6 (Niemcy)']
    
    for test_owner in test_players:
        print(f"\n👤 GRACZ {test_owner}:")
        count = 0
        for token in game_engine.tokens:
            if token.owner == test_owner:
                count += 1
                if count <= 2:  # Tylko pierwsze 2 jednostki na gracza
                    attack_info = token.stats.get('attack', {})
                    attack_range = attack_info.get('range', 1) if isinstance(attack_info, dict) else 1
                    sight = token.stats.get('sight', 0)
                    
                    print(f"   🎖️ {token.id}")
                    print(f"      📍 Pozycja: q={token.q}, r={token.r}")
                    print(f"      👁️ Wzrok: {sight}")
                    print(f"      🎯 Zasięg ataku: {attack_range}")
                    print(f"      ⚔️ Attack stats: {attack_info}")
    
    # Sprawdź odległości między wrogimi jednostkami
    print(f"\n📏 ODLEGŁOŚCI MIĘDZY WROGAMI:")
    polish_tokens = [t for t in game_engine.tokens if '(Polska)' in t.owner]
    german_tokens = [t for t in game_engine.tokens if '(Niemcy)' in t.owner]
    
    if polish_tokens and german_tokens:
        polish_sample = polish_tokens[0]
        german_sample = german_tokens[0]
        
        board = getattr(game_engine, 'board', None)
        if board:
            distance = board.hex_distance(
                (polish_sample.q, polish_sample.r),
                (german_sample.q, german_sample.r)
            )
            print(f"   Przykład: {polish_sample.id} do {german_sample.id}")
            print(f"   Odległość: {distance} hexów")
            print(f"   Polski position: ({polish_sample.q}, {polish_sample.r})")
            print(f"   Niemiecki position: ({german_sample.q}, {german_sample.r})")

if __name__ == "__main__":
    debug_ranges()