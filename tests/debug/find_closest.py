#!/usr/bin/env python3
"""
🔍 ZNAJDŹ NAJBLIŻSZE PARY
Szukamy jednostek które mogą się widzieć/atakować
"""

from engine.engine import GameEngine

def find_closest_pairs():
    """Znajdź najbliższe pary wrogów"""
    
    print("🔍 NAJBLIŻSZE PARY WROGÓW")
    print("="*50)
    
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=False
    )
    
    board = getattr(game_engine, 'board', None)
    if not board:
        print("❌ Brak board")
        return
    
    polish_tokens = [t for t in game_engine.tokens if '(Polska)' in t.owner]
    german_tokens = [t for t in game_engine.tokens if '(Niemcy)' in t.owner]
    
    print(f"📊 Jednostek polskich: {len(polish_tokens)}")
    print(f"📊 Jednostek niemieckich: {len(german_tokens)}")
    
    # Znajdź najbliższe pary
    closest_pairs = []
    
    for polish in polish_tokens:
        for german in german_tokens:
            distance = board.hex_distance(
                (polish.q, polish.r),
                (german.q, german.r)
            )
            closest_pairs.append((distance, polish, german))
    
    # Posortuj po odległości
    closest_pairs.sort(key=lambda x: x[0])
    
    print(f"\n🎯 TOP 10 NAJBLIŻSZYCH PAR:")
    for i, (distance, polish, german) in enumerate(closest_pairs[:10]):
        polish_sight = polish.stats.get('sight', 0)
        german_sight = german.stats.get('sight', 0)
        
        polish_attack_range = polish.stats.get('attack', {}).get('range', 1) if isinstance(polish.stats.get('attack', {}), dict) else 1
        german_attack_range = german.stats.get('attack', {}).get('range', 1) if isinstance(german.stats.get('attack', {}), dict) else 1
        
        can_polish_see = distance <= polish_sight
        can_german_see = distance <= german_sight
        can_polish_attack = distance <= polish_attack_range
        can_german_attack = distance <= german_attack_range
        
        print(f"   {i+1}. ODLEGŁOŚĆ: {distance} hexów")
        print(f"      🇵🇱 {polish.id} (q={polish.q}, r={polish.r})")
        print(f"         👁️ Wzrok: {polish_sight} ({'✅' if can_polish_see else '❌'})")
        print(f"         🎯 Atak: {polish_attack_range} ({'✅' if can_polish_attack else '❌'})")
        print(f"      🇩🇪 {german.id} (q={german.q}, r={german.r})")
        print(f"         👁️ Wzrok: {german_sight} ({'✅' if can_german_see else '❌'})")
        print(f"         🎯 Atak: {german_attack_range} ({'✅' if can_german_attack else '❌'})")
        
        if can_polish_see or can_german_see or can_polish_attack or can_german_attack:
            print(f"      🔥 MOŻLIWA WALKA!")
        print()
    
    return closest_pairs[0] if closest_pairs else None

if __name__ == "__main__":
    closest = find_closest_pairs()