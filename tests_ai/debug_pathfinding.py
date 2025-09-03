#!/usr/bin/env python3
"""Debug pathfinding dla punktu (9, -3) - dlaczego AI nie może znaleźć ścieżki"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from engine.engine import GameEngine

def debug_pathfinding():
    print("🔍 DEBUG PATHFINDING:")
    print("=" * 50)
    
    try:
        # Załaduj silnik gry z poprawnymi ścieżkami
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json", 
            tokens_start_path="assets/start_tokens.json"
        )
        
        print(f"✅ GameEngine zainicjalizowany")
        
        # Sprawdź mapę i board
        board = getattr(game_engine, 'board', None)
        if not board:
            print("❌ Brak board w GameEngine")
            return
            
        print(f"✅ Board znaleziony: {type(board)}")
        
        # Sprawdź punkt (9, -3)
        target_q, target_r = 9, -3
        print(f"\n🎯 ANALIZA PUNKTU ({target_q}, {target_r}):")
        print("-" * 30)
        
        # Sprawdź czy hex istnieje
        if hasattr(board, 'get_tile'):
            tile = board.get_tile(target_q, target_r)
            print(f"Tile: {tile}")
            if tile:
                print(f"  Terrain: {getattr(tile, 'terrain', 'BRAK')}")
                print(f"  Occupied: {getattr(tile, 'occupied', 'BRAK')}")
            else:
                print("  ❌ Tile nie istnieje!")
        
        # Sprawdź sąsiadów
        if hasattr(board, 'neighbors'):
            neighbors = board.neighbors(target_q, target_r)
            print(f"Sąsiedzi: {list(neighbors)}")
        
        # Sprawdź czy jest token na tym hex'ie
        all_tokens = getattr(game_engine, 'tokens', [])
        tokens_at_target = []
        for token in all_tokens:
            if getattr(token, 'q', None) == target_q and getattr(token, 'r', None) == target_r:
                tokens_at_target.append(token.id)
        
        if tokens_at_target:
            print(f"❌ Tokeny na ({target_q}, {target_r}): {tokens_at_target}")
        else:
            print(f"✅ Punkt ({target_q}, {target_r}) wolny")
        
        # Sprawdź key point
        kp_state = getattr(game_engine, 'key_points_state', {})
        target_key = f"{target_q},{target_r}"
        if target_key in kp_state:
            kp = kp_state[target_key]
            print(f"✅ Key point {target_key}: wartość={kp.get('current_value', 0)}")
        else:
            print(f"❌ Brak key pointu na {target_key}")
        
        # Przetestuj pathfinding z różnych pozycji
        print(f"\n🗺️ TEST PATHFINDING DO ({target_q}, {target_r}):")
        print("-" * 40)
        
        test_positions = [
            (3, 2),   # P_Pluton
            (3, 3),   # TS_Batalion  
            (3, 4),   # Z_Pluton_Wsparcia
            (3, 5),   # Z_Pluton_Zaopatrzeniowa
            (6, 2),   # Pozycja po ruchu
            (5, 2),   # Pozycja po ruchu
        ]
        
        for start_pos in test_positions:
            print(f"\nOd {start_pos} do ({target_q}, {target_r}):")
            
            # Sprawdź dystans
            if hasattr(board, 'hex_distance'):
                distance = board.hex_distance(start_pos, (target_q, target_r))
                print(f"  Dystans: {distance}")
            
            # Sprawdź pathfinding z różnymi limitami
            if hasattr(board, 'find_path'):
                for mp, fuel in [(3, 4), (10, 15), (16, 20)]:
                    path = board.find_path(start_pos, (target_q, target_r), max_mp=mp, max_fuel=fuel)
                    if path:
                        print(f"  ✅ MP={mp}, Fuel={fuel}: ścieżka długość {len(path)-1}")
                        if len(path) <= 5:  # Pokaż krótkie ścieżki
                            print(f"     Ścieżka: {path}")
                    else:
                        print(f"  ❌ MP={mp}, Fuel={fuel}: brak ścieżki")
            
            # Sprawdź czy start_pos jest dostępny
            if hasattr(board, 'get_tile'):
                start_tile = board.get_tile(start_pos[0], start_pos[1])
                if not start_tile:
                    print(f"  ❌ Start {start_pos} nie istnieje!")
        
        # Sprawdź pathfinding bezpośrednio
        print(f"\n🧪 BEZPOŚREDNI TEST find_path:")
        print("-" * 30)
        
        if hasattr(board, 'find_path'):
            # Test z pozycji (6,2) która była w logu
            start = (6, 2)
            target = (9, -3)
            
            print(f"find_path({start}, {target}):")
            path = board.find_path(start, target, max_mp=10, max_fuel=4)
            print(f"  Wynik: {path}")
            
            if not path:
                # Sprawdź dlaczego
                print(f"  🔍 Debugowanie braku ścieżki:")
                print(f"    Start tile: {board.get_tile(start[0], start[1]) if hasattr(board, 'get_tile') else 'BRAK'}")
                print(f"    Target tile: {board.get_tile(target[0], target[1]) if hasattr(board, 'get_tile') else 'BRAK'}")
                
                # Sprawdź czy w ogóle można się ruszać ze start
                for neighbor_pos in [(6,1), (7,1), (5,1), (6,3), (7,2), (5,3)]:
                    neighbor_path = board.find_path(start, neighbor_pos, max_mp=10, max_fuel=4)
                    print(f"    Do sąsiada {neighbor_pos}: {'✅' if neighbor_path else '❌'}")
        
    except Exception as e:
        print(f"❌ Błąd debugowania: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pathfinding()
