#!/usr/bin/env python3
"""Auto-test 10-rundowej gry AI vs AI z opcjami czyszczenia"""

import sys
import os
import argparse
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.engine import GameEngine, update_all_players_visibility, clear_temp_visibility
from engine.player import Player
from core.ekonomia import EconomySystem
from core.tura import TurnManager
from core.zwyciestwo import VictoryConditions
from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander

def clean_old_data():
    """Czyści stare CSV i zakupione żetony"""
    print("🧹 CZYSZCZENIE STARYCH DANYCH...")
    print("="*50)
    
    # Czyszczenie CSV
    try:
        from czyszczenie.czyszczenie_csv import clean_csv_files
        print("📄 Czyszczenie starych CSV...")
        clean_csv_files()
        print("✅ CSV wyczyszczone!")
    except Exception as e:
        print(f"⚠️ Błąd czyszczenia CSV: {e}")
    
    print()
    
    # Czyszczenie żetonów
    try:
        from czyszczenie.czyszczenie_zakupionych_zetonow import TokenFolderCleaner
        print("🪙 Czyszczenie zakupionych żetonów...")
        cleaner = TokenFolderCleaner()
        cleaner.clean_folders(force=True)  # Force aby nie pytać
        print("✅ Żetony wyczyszczone!")
    except Exception as e:
        print(f"⚠️ Błąd czyszczenia żetonów: {e}")
    
    print("="*50)
    print("✅ DANE WYCZYSZCZONE - GOTOWE DO NOWEJ ANALIZY!")
    print("="*50)
    print()

def auto_game_10_turns():
    """Automatyczna gra 10 tur, wszyscy gracze to AI"""
    print("🚀 ROZPOCZYNANIE 10-RUNDOWEJ GRY AI vs AI")
    print("="*60)
    
    # GameEngine
    print("🔧 Tworzenie GameEngine...")
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=True
    )
    print(f"✅ GameEngine: {len(game_engine.tokens)} tokenów")
    
    # Gracze - wszyscy AI
    print("🤖 Konfiguracja graczy AI...")
    players = [
        Player(1, "Polska", "Generał", 5),
        Player(2, "Polska", "Dowódca", 5), 
        Player(3, "Polska", "Dowódca", 5),
        Player(4, "Niemcy", "Generał", 5),
        Player(5, "Niemcy", "Dowódca", 5),
        Player(6, "Niemcy", "Dowódca", 5),
    ]
    
    # AI Setup
    ai_generals = {}
    ai_commanders = {}
    
    for player in players:
        player.economy = EconomySystem()
        
        if player.role == "Generał":
            player.is_ai = True
            if player.nation == "Polska":
                ai_generals[player.id] = AIGeneral("polish")
            else:
                ai_generals[player.id] = AIGeneral("german")
            print(f"🧠 AI Generał: {player.nation} (id={player.id})")
            
        elif player.role == "Dowódca":
            player.is_ai_commander = True
            ai_commanders[player.id] = AICommander(player)
            print(f"🎯 AI Dowódca: {player.nation} (id={player.id})")
    
    game_engine.players = players
    update_all_players_visibility(players, game_engine.tokens, game_engine.board)
    
    # Turn Manager
    turn_manager = TurnManager(players, game_engine=game_engine)
    turn_manager.ai_generals = ai_generals
    turn_manager.ai_commanders = ai_commanders
    
    # Victory Conditions - 10 tur
    victory_conditions = VictoryConditions(max_turns=10, victory_mode="turns")
    
    print("🎯 POCZĄTEK GRY - 10 TUR")
    print("="*60)
    
    # === PE TRACKING - STAN POCZĄTKOWY ===
    print("💰 [PE INITIAL] POCZĄTKOWY STAN PE:")
    for nation in ["Polska", "Niemcy"]:
        nation_players = [p for p in players if p.nation == nation]
        total_pe = sum(p.economy.get_points().get('economic_points', 0) for p in nation_players)
        print(f"  🏛️ {nation} łącznie: {total_pe} PE")
        for p in nation_players:
            pe = p.economy.get_points().get('economic_points', 0)
            print(f"    └─ {p.role} (id={p.id}): {pe} PE")
    print("="*40)
    
    # Główna pętla gry
    turn_count = 0
    while turn_count < 10:
        current_player = turn_manager.get_current_player()
        game_engine.current_player_obj = current_player
        
        print(f"\n📅 TURA {turn_manager.current_turn} - {current_player.nation} {current_player.role} (id={current_player.id})")
        
        # Logowanie stanu key pointów
        game_engine.log_key_points_status(current_player)
        
        update_all_players_visibility(players, game_engine.tokens, game_engine.board)
        
        # AI Turn
        if hasattr(current_player, 'is_ai') and current_player.is_ai and current_player.id in ai_generals:
            print(f"🧠 AI GENERAL TURN: {current_player.nation}")
            
            # === PE TRACKING - PRZED TURĄ GENERAŁA ===
            pe_before_general = current_player.economy.get_points().get('economic_points', 0)
            commanders = [p for p in players if p.nation == current_player.nation and p.role == 'Dowódca']
            cmd_pe_before = {}
            for cmd in commanders:
                cmd_pe_before[cmd.id] = cmd.economy.get_points().get('economic_points', 0)
            
            print(f"💰 [PE BEFORE] Generał {current_player.nation} (id={current_player.id}): {pe_before_general} PE")
            for cmd in commanders:
                print(f"💰 [PE BEFORE] Dowódca {cmd.nation} (id={cmd.id}): {cmd_pe_before[cmd.id]} PE")
            
            ai_general = ai_generals[current_player.id]
            if current_player.role == "Generał":
                current_player.economy.generate_economic_points()
                current_player.economy.add_special_points()
            ai_general.make_turn(game_engine)
            
            # === PE TRACKING - PO TURZE GENERAŁA ===
            pe_after_general = current_player.economy.get_points().get('economic_points', 0)
            cmd_pe_after = {}
            for cmd in commanders:
                cmd_pe_after[cmd.id] = cmd.economy.get_points().get('economic_points', 0)
            
            print(f"💰 [PE AFTER] Generał {current_player.nation} (id={current_player.id}): {pe_after_general} PE")
            for cmd in commanders:
                gained = cmd_pe_after[cmd.id] - cmd_pe_before[cmd.id]
                print(f"💰 [PE AFTER] Dowódca {cmd.nation} (id={cmd.id}): {cmd_pe_after[cmd.id]} PE (zmiana: {gained:+d})")
            
            allocated_total = pe_before_general - pe_after_general
            commanders_gained_total = sum(cmd_pe_after[cmd.id] - cmd_pe_before[cmd.id] for cmd in commanders)
            balance = allocated_total - commanders_gained_total
            
            print(f"📊 [PE FLOW] Generał przekazał: {allocated_total} PE")
            print(f"📊 [PE FLOW] Dowódcy otrzymali łącznie: {commanders_gained_total} PE")
            print(f"📊 [PE FLOW] Bilans (różnica): {balance} PE {'✅ OK' if abs(balance) <= 1 else '❌ BŁĄD'}")
            
        elif hasattr(current_player, 'is_ai_commander') and current_player.is_ai_commander and current_player.id in ai_commanders:
            print(f"🎯 AI COMMANDER TURN: {current_player.nation} id={current_player.id}")
            
            # === PE TRACKING - PRZED TURĄ DOWÓDCY ===
            pe_before_commander = current_player.economy.get_points().get('economic_points', 0)
            print(f"💰 [PE BEFORE] Dowódca {current_player.nation} (id={current_player.id}): {pe_before_commander} PE")
            
            ai_commander = ai_commanders[current_player.id]
            
            # Pre-resupply i tura taktyczna
            ai_commander.pre_resupply(game_engine)
            ai_commander.make_tactical_turn(game_engine)
            
            # === PE TRACKING - PO TURZE DOWÓDCY ===
            pe_after_commander = current_player.economy.get_points().get('economic_points', 0)
            spent = pe_before_commander - pe_after_commander
            print(f"💰 [PE AFTER] Dowódca {current_player.nation} (id={current_player.id}): {pe_after_commander} PE (wydał: {spent} PE)")
            
            if spent > 0:
                print(f"🛒 [PE SPENDING] Dowódca {current_player.id} wydał {spent} PE na resupply/operacje")
        
        # Następna tura
        is_full_turn_end = turn_manager.next_turn()
        
        if is_full_turn_end:
            game_engine.process_key_points(players)
            turn_count += 1
            print(f"🔄 KONIEC RUNDY {turn_count}/10")
            
            # === PE TRACKING - KONIEC RUNDY ===
            print("💰 [PE SUMMARY] STAN PE NA KONIEC RUNDY:")
            for nation in ["Polska", "Niemcy"]:
                nation_players = [p for p in players if p.nation == nation]
                total_pe = sum(p.economy.get_points().get('economic_points', 0) for p in nation_players)
                print(f"  🏛️ {nation} łącznie: {total_pe} PE")
                for p in nation_players:
                    pe = p.economy.get_points().get('economic_points', 0)
                    print(f"    └─ {p.role} (id={p.id}): {pe} PE")
            print("="*40)
        
        game_engine.update_all_players_visibility(players)
        
        # Sprawdź warunki zwycięstwa
        if victory_conditions.check_game_over(turn_manager.current_turn, players):
            print(victory_conditions.get_victory_message())
            break
            
        clear_temp_visibility(players)
    
    print("\n" + "="*60)
    print("🏁 GRA ZAKOŃCZONA")
    
    # Analiza wyników
    victory_info = victory_conditions.get_victory_info()
    print(f"🏆 ZWYCIĘZCA: {victory_info.get('winner_nation', 'REMIS')}")
    
    for p in players:
        vp = getattr(p, "victory_points", 0)
        print(f"📊 {p.nation} {p.role} (id={p.id}): {vp} VP")
    
    print("\n📄 SPRAWDZANIE LOGÓW CSV:")
    csv_files = []
    for root, dirs, files in os.walk("logs"):
        for file in files:
            if file.endswith('.csv') and '20250903' in file:
                csv_path = os.path.join(root, file)
                try:
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        csv_files.append((csv_path, len(lines)))
                except:
                    csv_files.append((csv_path, 0))
    
    csv_files.sort(key=lambda x: x[1], reverse=True)  # Sortuj po liczbie linii
    
    print(f"📈 ZNALEZIONE CSV (dzisiejsze):")
    for csv_path, line_count in csv_files:
        size_kb = os.path.getsize(csv_path) / 1024 if os.path.exists(csv_path) else 0
        print(f"  📁 {csv_path}: {line_count} linii, {size_kb:.1f} KB")
        
        if line_count > 100:  # Duże pliki
            print(f"    🔥 DUŻY PLIK - NAJWAŻNIEJSZY LOG!")
    
    print("="*60)

if __name__ == "__main__":
    # Obsługa argumentów wiersza poleceń
    parser = argparse.ArgumentParser(description="Auto-test 10-rundowej gry AI vs AI")
    parser.add_argument('--clean', action='store_true', 
                       help='Wyczyść stare CSV i żetony przed testem')
    parser.add_argument('--clean-only', action='store_true',
                       help='Tylko wyczyść dane (nie uruchamiaj gry)')
    
    args = parser.parse_args()
    
    # Czyszczenie danych jeśli wybrane
    if args.clean or args.clean_only:
        clean_old_data()
        
        if args.clean_only:
            print("🏁 CZYSZCZENIE ZAKOŃCZONE!")
            sys.exit(0)
    
    # Uruchom test gry
    auto_game_10_turns()
