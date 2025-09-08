#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 4 Dedicated Test Launcher - specjalnie dla testów Phase 4 AI"""

import sys
import os
import argparse
import json
from pathlib import Path

# Ensure UTF-8 output
if sys.platform == 'win32':
    try:
        # Try to set UTF-8 encoding for Windows console
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        # Fallback to ASCII-safe characters
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.engine import GameEngine, update_all_players_visibility, clear_temp_visibility
from engine.player import Player
from core.ekonomia import EconomySystem
from core.tura import TurnManager
from core.zwyciestwo import VictoryConditions
from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander

def clean_test_data():
    """Czyści dane testowe (ASCII-safe)"""
    print("PHASE 4 TEST - CZYSZCZENIE DANYCH...")
    print("="*50)
    
    # Czyszczenie logów
    logs_dir = Path("logs")
    if logs_dir.exists():
        cleaned_files = 0
        for root, dirs, files in os.walk(logs_dir):
            for file in files:
                file_path = Path(root) / file
                try:
                    file_path.unlink()
                    cleaned_files += 1
                except Exception as e:
                    print(f"Błąd usuwania {file_path}: {e}")
        
        print(f"Usunieto {cleaned_files} plikow logow")
    
    # Czyszczenie requests
    requests_dir = Path("data/requests")
    if requests_dir.exists():
        cleaned_requests = 0
        for req_file in requests_dir.glob("*.json"):
            try:
                req_file.unlink()
                cleaned_requests += 1
            except Exception as e:
                print(f"Błąd usuwania {req_file}: {e}")
        
        print(f"Usunieto {cleaned_requests} plikow requests")
    
    print("CZYSZCZENIE ZAKONCZONE")
    print("="*50)

def phase4_test_game(turns=3):
    """Testowa gra AI vs AI skupiona na Phase 4"""
    
    print(f"PHASE 4 TEST - {turns} ROUNDS")
    print("="*60)
    
    # GameEngine
    print("Tworzenie GameEngine...")
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=True
    )
    print(f"GameEngine: {len(game_engine.tokens)} tokenów")
    
    # Gracze AI
    print("Konfiguracja graczy AI...")
    players = [
        Player(1, "Polska", "Generał", 5),
        Player(2, "Polska", "Dowódca", 5), 
        Player(3, "Niemcy", "Generał", 5),
        Player(4, "Niemcy", "Dowódca", 5),
    ]
    
    # AI Setup
    ai_generals = {}
    ai_commanders = {}
    
    for player in players:
        player.economy = EconomySystem()
        
        if player.role == "Generał":
            player.is_ai = True
            nation_key = "polish" if player.nation == "Polska" else "german"
            ai_generals[player.id] = AIGeneral(nation_key)
            print(f"AI Generał: {player.nation} (id={player.id})")
            
        elif player.role == "Dowódca":
            player.is_ai_commander = True
            ai_commanders[player.id] = AICommander(player)
            print(f"AI Dowódca: {player.nation} (id={player.id})")
    
    game_engine.players = players
    update_all_players_visibility(players, game_engine.tokens, game_engine.board)
    
    # Turn Manager
    turn_manager = TurnManager(players, game_engine=game_engine)
    turn_manager.ai_generals = ai_generals
    turn_manager.ai_commanders = ai_commanders
    
    # Victory Conditions
    victory_conditions = VictoryConditions(max_turns=turns, victory_mode="turns")
    
    print(f"POCZĄTEK GRY - {turns} TUR")
    print("="*60)
    
    # Tracking Phase 4 Activity
    phase4_activity = {
        'requests_generated': 0,
        'requests_processed': 0,
        'purchases_made': 0,
        'communication_events': 0
    }
    
    # Główna pętla
    turn_count = 0
    while turn_count < turns:
        current_player = turn_manager.get_current_player()
        game_engine.current_player_obj = current_player
        
        print(f"\nTURA {turn_manager.current_turn} - {current_player.nation} {current_player.role} (id={current_player.id})")
        
        update_all_players_visibility(players, game_engine.tokens, game_engine.board)
        
        # AI Turn with Phase 4 tracking
        if hasattr(current_player, 'is_ai') and current_player.is_ai and current_player.id in ai_generals:
            print(f"AI GENERAL: {current_player.nation}")
            
            # Track PE before
            pe_before = current_player.economy.get_points().get('economic_points', 0)
            
            ai_general = ai_generals[current_player.id]
            if current_player.role == "Generał":
                current_player.economy.generate_economic_points()
                current_player.economy.add_special_points()
            
            # Check for requests before processing
            requests_dir = Path("data/requests")
            requests_before = len(list(requests_dir.glob("*.json"))) if requests_dir.exists() else 0
            
            ai_general.make_turn(game_engine)
            
            # Check requests after processing
            requests_after = len(list(requests_dir.glob("*.json"))) if requests_dir.exists() else 0
            
            pe_after = current_player.economy.get_points().get('economic_points', 0)
            pe_spent = pe_before - pe_after
            
            if requests_after < requests_before:
                processed = requests_before - requests_after
                phase4_activity['requests_processed'] += processed
                print(f"  PHASE 4: Przetworzono {processed} requestów")
            
            if pe_spent > 0:
                phase4_activity['purchases_made'] += 1
                print(f"  PHASE 4: General wydał {pe_spent} PE")
            
        elif hasattr(current_player, 'is_ai_commander') and current_player.is_ai_commander and current_player.id in ai_commanders:
            print(f"AI COMMANDER: {current_player.nation}")
            
            # Check requests before turn
            requests_dir = Path("data/requests")
            requests_before = len(list(requests_dir.glob("*.json"))) if requests_dir.exists() else 0
            
            ai_commander = ai_commanders[current_player.id]
            ai_commander.pre_resupply(game_engine)
            ai_commander.make_tactical_turn(game_engine)
            
            # Check requests after turn
            requests_after = len(list(requests_dir.glob("*.json"))) if requests_dir.exists() else 0
            
            if requests_after > requests_before:
                generated = requests_after - requests_before
                phase4_activity['requests_generated'] += generated
                print(f"  PHASE 4: Wygenerowano {generated} requestów")
        
        # Następna tura
        is_full_turn_end = turn_manager.next_turn()
        
        if is_full_turn_end:
            print(f"\nKONIEC RUNDY {turn_count + 1}/{turns}")
            game_engine.process_key_points(players)
            turn_count += 1
        
        game_engine.update_all_players_visibility(players)
        
        if victory_conditions.check_game_over(turn_manager.current_turn, players):
            break
            
        clear_temp_visibility(players)
    
    print("\n" + "="*60)
    print("GRA ZAKONCZONA")
    
    # Analyze Phase 4 results
    print("\nPHASE 4 ACTIVITY SUMMARY:")
    print(f"  Requests generated: {phase4_activity['requests_generated']}")
    print(f"  Requests processed: {phase4_activity['requests_processed']}")
    print(f"  Purchases made: {phase4_activity['purchases_made']}")
    
    # Check generated logs
    print("\nGENEROWANE LOGI:")
    
    logs_count = 0
    csv_count = 0
    
    if os.path.exists("logs"):
        for root, dirs, files in os.walk("logs"):
            for file in files:
                logs_count += 1
                if file.endswith('.csv'):
                    csv_count += 1
                    
                    # Check if Phase 4 related
                    if any(keyword in file.lower() for keyword in ['phase4', 'communication', 'request']):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = len(f.readlines())
                            rel_path = os.path.relpath(file_path, "logs")
                            print(f"  PHASE 4 CSV: {rel_path} ({lines} linii)")
                        except:
                            pass
    
    print(f"Łącznie logów: {logs_count} (w tym {csv_count} CSV)")
    
    # Check communication files
    requests_dir = Path("data/requests")
    if requests_dir.exists():
        req_files = list(requests_dir.glob("*.json"))
        print(f"Request files: {len(req_files)}")
        
        for req_file in req_files:
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"  {req_file.name}: {data.get('type', 'unknown')} request")
            except:
                print(f"  {req_file.name}: błąd odczytu")
    
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description="Phase 4 Test Launcher")
    parser.add_argument('--turns', type=int, default=3, help='Number of turns (default: 3)')
    parser.add_argument('--clean', action='store_true', help='Clean old data before test')
    parser.add_argument('--clean-only', action='store_true', help='Only clean data')
    
    args = parser.parse_args()
    
    if args.clean or args.clean_only:
        clean_test_data()
        
        if args.clean_only:
            return
    
    # Run test game
    phase4_test_game(args.turns)

if __name__ == "__main__":
    main()
