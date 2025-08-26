#!/usr/bin/env python3
"""
Prosty test AI bez emoji dla Windows
"""

import sys
import os
# Dodaj ścieżkę do głównego katalogu projektu  
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from engine.engine import GameEngine
from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander

def run_simple_ai_test():
    try:
        print("PROSTY TEST AI - 2 TURY")
        
        # Ścieżki do głównego katalogu projektu
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        map_path = os.path.join(project_root, "data", "map_data.json")
        tokens_index_path = os.path.join(project_root, "assets", "tokens", "index.json")
        tokens_start_path = os.path.join(project_root, "assets", "start_tokens.json")
        
        # Utwórz engine
        engine = GameEngine(
            map_path=map_path,
            tokens_index_path=tokens_index_path, 
            tokens_start_path=tokens_start_path
        )
        print(f"Gra zaladowana: {len(engine.tokens)} tokenow")
        
        # Stwórz graczy ręcznie jak w headless test
        from engine.player import Player
        from core.ekonomia import EconomySystem
        
        players = [
            Player(1, "Polska", "General", 2000),
            Player(2, "Polska", "Dowodca", 300),
            Player(3, "Polska", "Dowodca", 300),
            Player(4, "Niemcy", "General", 2000),
            Player(5, "Niemcy", "Dowodca", 300),
            Player(6, "Niemcy", "Dowodca", 300),
        ]
        
        # Dodaj ekonomię
        for player in players:
            player.economy = EconomySystem()
            player.is_ai = True
        
        # Wykonaj 2 tury AI
        for turn in range(1, 3):
            print(f"\n========== TURA {turn} ==========")
            
            # Generał Polski
            print(f"Polonia General (id=1)")
            player = players[0]  # ID 1
            engine.current_player_obj = player
            nationality = "polish"
            ai_general = AIGeneral(nationality)
            ai_general.player = player
            ai_general.make_turn(engine)
            
            # Dowódcy Polscy
            for i, player_id in enumerate([2, 3]):
                print(f"Polonia Commander (id={player_id})")
                player = players[i+1]  # ID 2,3
                engine.current_player_obj = player
                ai_commander = AICommander(player)
                ai_commander.make_tactical_turn(engine)
            
            # Generał Niemiecki  
            print(f"German General (id=4)")
            player = players[3]  # ID 4
            engine.current_player_obj = player
            nationality = "german"
            ai_general = AIGeneral(nationality)
            ai_general.player = player
            ai_general.make_turn(engine)
            
            # Dowódcy Niemieccy
            for i, player_id in enumerate([5, 6]):
                print(f"German Commander (id={player_id})")
                player = players[i+4]  # ID 5,6
                engine.current_player_obj = player
                ai_commander = AICommander(player)
                ai_commander.make_tactical_turn(engine)
        
        print("\nTEST ZAKONCZONY")
        
    except Exception as e:
        print(f"BLAD TESTU: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_simple_ai_test()
