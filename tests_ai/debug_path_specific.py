#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.engine import GameEngine
from engine.board import Board

def test_specific_pathfinding():
    """Testuje konkretny problem z pathfindingiem do (9,-3)."""
    
    # Inicjalizacja game engine
    try:
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json", 
            tokens_start_path="assets/start_tokens.json"
        )
        board = game_engine.board
        print("✅ GameEngine załadowany!")
    except Exception as e:
        print(f"❌ Błąd ładowania GameEngine: {e}")
        return
    
    # Test konkretnych współrzędnych z debugu
    start_pos = (6, 2)  # Pozycja Z_Pluton__2_Batalion_Wsparcia w turze 2
    target_pos = (9, -3)  # Cel rajdu
    
    print(f"\n🔍 DIAGNOZA PATHFINDINGU")
    print(f"Start: {start_pos}")
    print(f"Cel: {target_pos}")
    
    # Sprawdź czy pozycje istnieją na mapie
    start_tile = board.get_tile(*start_pos)
    target_tile = board.get_tile(*target_pos)
    
    print(f"\n📍 TILE CHECK:")
    print(f"Start tile {start_pos}: {start_tile} - terrain: {getattr(start_tile, 'terrain_key', 'NONE') if start_tile else 'MISSING'}")
    print(f"Target tile {target_pos}: {target_tile} - terrain: {getattr(target_tile, 'terrain_key', 'NONE') if target_tile else 'MISSING'}")
    
    if not target_tile:
        print(f"❌ Cel {target_pos} nie istnieje na mapie!")
        return
    
    # Test pathfindingu z różnymi parametrami
    print(f"\n🗺️ PATHFINDING TESTS:")
    
    # Test 1: Podstawowy pathfinding
    path1 = board.find_path(start_pos, target_pos)
    print(f"1. Podstawowy find_path: {path1}")
    
    # Test 2: Z ograniczonym MP/Fuel (jak w combat mode)
    path2 = board.find_path(start_pos, target_pos, max_mp=10, max_fuel=10)
    print(f"2. Combat mode (MP=10, Fuel=10): {path2}")
    
    # Test 3: Z wysokimi limitami (jak w march mode po resupply)
    path3 = board.find_path(start_pos, target_pos, max_mp=15, max_fuel=15)
    print(f"3. March mode expanded (MP=15, Fuel=15): {path3}")
    
    # Test 4: Z fallback do najbliższego
    path4 = board.find_path(start_pos, target_pos, max_mp=10, max_fuel=10, fallback_to_closest=True)
    print(f"4. Z fallback: {path4}")
    
    # Sprawdź dystans
    distance = board.hex_distance(start_pos, target_pos)
    print(f"\n📏 Dystans hex: {distance}")
    
    # Sprawdź sąsiadów celu
    neighbors = board.neighbors(*target_pos)
    print(f"\n👥 Sąsiedzi celu {target_pos}:")
    for neighbor in neighbors:
        tile = board.get_tile(*neighbor)
        occupied = board.is_occupied(*neighbor)
        print(f"  {neighbor}: tile={tile is not None}, occupied={occupied}, terrain={getattr(tile, 'terrain_key', 'NONE') if tile else 'MISSING'}")
    
    # Sprawdź czy cel jest zajęty
    target_occupied = board.is_occupied(*target_pos)
    print(f"\n🚫 Cel zajęty: {target_occupied}")
    
    # Sprawdź move_mod celu
    if target_tile:
        print(f"🏃 Move mod celu: {target_tile.move_mod}")
        if target_tile.move_mod == -1:
            print("❌ Cel ma move_mod=-1 (niedostępny)!")

if __name__ == "__main__":
    test_specific_pathfinding()
