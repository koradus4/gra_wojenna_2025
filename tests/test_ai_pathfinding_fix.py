#!/usr/bin/env python3
"""
Test naprawy AI pathfinding - sprawdza czy AI wybiera realistyczne cele
"""

import sys
import os
# Dodaj ścieżkę do głównego katalogu projektu  
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from engine.engine import GameEngine
from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander

def test_ai_realistic_targets():
    """Test czy AI wybiera cele w zasięgu MP jednostek"""
    try:
        print("=== TEST AI PATHFINDING FIX ===")
        
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
        
        # Tworzenie gracza polskiego
        player_polska = Player(
            player_id=2, 
            nation="Polska", 
            role="Dowódca",
            economy=EconomySystem()
        )
        
        # Tworzenie gracza niemieckiego  
        player_niemcy = Player(
            player_id=6,
            nation="Niemcy",
            role="Dowódca",
            economy=EconomySystem()
        )
        
        # Dodaj graczy do silnika
        engine.players = [player_polska, player_niemcy]
        
        # Przypisz tokeny do graczy - dodaj puste listy tokens
        player_polska.tokens = []
        player_niemcy.tokens = []
        
        # Przypisz tokeny do graczy
        for token in engine.tokens:
            if hasattr(token, 'owner'):
                if token.owner == 2:
                    player_polska.tokens.append(token)
                elif token.owner == 6:
                    player_niemcy.tokens.append(token)
        
        print(f"Gracz Polska: {len(player_polska.tokens)} tokenow")
        print(f"Gracz Niemcy: {len(player_niemcy.tokens)} tokenow")
        
        # Test AI Commander dla gracza niemieckiego
        engine.current_player_id = 6
        engine.current_player_obj = player_niemcy
        
        ai_commander = AICommander(player_niemcy)
        
        # Ustaw strategiczny rozkaz przez setattr
        ai_commander.strategic_orders = [{"type": "SECURE_KEYPOINT", "target": [39, 0]}]
        
        print("\n=== PRZED NAPRAWĄ - ANALIZA JEDNOSTEK ===")
        
        # Sprawdź jednostki gracza 6
        moves_attempted = 0
        moves_successful = 0
        realistic_rejections = 0
        
        for token in player_niemcy.tokens:
            if hasattr(token, 'currentMovePoints'):
                mp = getattr(token, 'currentMovePoints', 0)
                fuel = getattr(token, 'currentFuel', 0)
                pos = (token.q, token.r)
                target = (39, 0)
                
                # Oblicz dystans heksowy
                hex_distance = abs(pos[0] - target[0]) + abs(pos[1] - target[1]) + abs((pos[0] + pos[1]) - (target[0] + target[1]))
                hex_distance = hex_distance // 2
                max_reach = min(mp, fuel)
                
                print(f"[ANALIZA] {token.id}: MP={mp}, Fuel={fuel}, Dystans={hex_distance}, Zasięg={max_reach}")
                
                if hex_distance > max_reach:
                    print(f"  -> NIEREALISTYCZNY CEL (dystans > zasięg)")
                    realistic_rejections += 1
                else:
                    print(f"  -> REALISTYCZNY CEL")
        
        # Zapisz pozycje początkowe
        initial_positions = {}
        for token in player_niemcy.tokens:
            initial_positions[token.id] = (token.q, token.r)
            print(f"POZYCJA PRZED: {token.id} = ({token.q}, {token.r})")
        
        print(f"\nNierealistyczne cele: {realistic_rejections}")
        
        # Test wykonania tury AI
        print("\n=== WYKONANIE TURY AI ===")
        
        try:
            ai_commander.make_tactical_turn(engine)
            
            print("\n=== POZYCJE PO WYKONANIU AI ===")
            # Policz udane ruchy po wykonaniu tury
            for token in player_niemcy.tokens:
                start_pos = initial_positions.get(token.id)
                current_pos = (token.q, token.r)
                print(f"POZYCJA PO: {token.id} = ({token.q}, {token.r})")
                if start_pos and start_pos != current_pos:
                    moves_successful += 1
                    print(f"RUCH: {token.id} ({start_pos}) -> ({current_pos})")
                    
            print(f"\nWYNIKI:")
            print(f"Udane ruchy: {moves_successful}")
            print(f"Odrzucone cele nierealistyczne: {realistic_rejections}")
            
            # Oblicz procentową poprawę
            total_tokens = len([t for t in player_niemcy.tokens if hasattr(t, 'currentMovePoints')])
            success_rate = (moves_successful / total_tokens * 100) if total_tokens > 0 else 0
            
            print(f"Skuteczność AI: {success_rate:.1f}%")
            
            if realistic_rejections > 0:
                print("AI POPRAWNIE ODRZUCA NIEREALISTYCZNE CELE")
            else:
                print("Wszystkie cele byly realistyczne")
                
            if success_rate > 0:
                print("AI WYKONUJE RUCHY")
            else:
                print("AI nie wykonalo zadnych ruchow")
                
        except Exception as e:
            print(f"BLAD podczas wykonywania AI: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"BLAD TESTU: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_realistic_targets()
