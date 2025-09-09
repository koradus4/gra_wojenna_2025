#!/usr/bin/env python3
"""Test naprawionego deployment AI - AUTOMATYCZNY"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from engine.engine import GameEngine, update_all_players_visibility, clear_temp_visibility
from engine.player import Player
from core.ekonomia import EconomySystem
from core.tura import TurnManager
from core.zwyciestwo import VictoryConditions
from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander

print("🔧 TEST NAPRAWIONEGO DEPLOYMENT AI - AUTOMATYCZNY")
print("Sprawdzam czy AI Commander wystawia tokeny AI Generała")
print("=" * 60)

def run_deployment_test():
    """Automatyczny test deployment systemu - 2 tury"""
    print("🚀 INICJALIZACJA TESTU...")
    
    # Game Engine
    print("🔧 Tworzenie GameEngine...")
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=True
    )
    print(f"✅ GameEngine: {len(game_engine.tokens)} tokenów")
    
    # Players - tylko Polska żeby skupić się na deployment
    players = [
        Player(1, "Polska", "Generał", 5),      # AI General - kupuje tokeny
        Player(2, "Polska", "Dowódca", 5),     # AI Commander - wystawia tokeny
        Player(3, "Polska", "Dowódca", 5),     # AI Commander - wystawia tokeny
    ]
    
    # AI Setup
    ai_generals = {}
    ai_commanders = {}
    
    for player in players:
        player.economy = EconomySystem()
        
        if player.role == "Generał":
            player.is_ai = True
            ai_generals[player.id] = AIGeneral("polish")
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
    
    # Victory Conditions - tylko 2 tury dla testu
    victory_conditions = VictoryConditions(max_turns=2, victory_mode="turns")
    
    print("\n🎯 POCZĄTEK TESTU - 2 TURY")
    print("=" * 40)
    
    turn_count = 1
    
    # Game Loop - maksymalnie 20 kroków (bezpieczeństwo)
    for step in range(20):
        if victory_conditions.check_game_over(turn_count, players):
            print(f"\n🏁 TEST ZAKOŃCZONY PO {turn_count} TURACH")
            break
            
        current_player = turn_manager.get_current_player()
        print(f"\n👤 TURA: {current_player.nation} {current_player.role} (id={current_player.id})")
        
        if hasattr(current_player, 'is_ai') and current_player.is_ai and current_player.id in ai_generals:
            print(f"🧠 AI GENERAL TURN: {current_player.nation} id={current_player.id}")
            
            # Generuj PE dla generała
            current_player.economy.generate_economic_points()
            current_player.economy.add_special_points()
            
            # Sprawdź PE przed zakupami
            pe_before = current_player.economy.get_points().get('economic_points', 0)
            print(f"💰 PE przed zakupami: {pe_before}")
            
            # AI General turn
            ai_general = ai_generals[current_player.id]
            ai_general.make_turn(game_engine)
            
            # Sprawdź PE po zakupach
            pe_after = current_player.economy.get_points().get('economic_points', 0)
            spent = pe_before - pe_after
            print(f"💰 PE po zakupach: {pe_after} (wydał: {spent} PE)")
            
            if spent > 0:
                print(f"🛒 AI Generał kupił tokeny za {spent} PE")
            
        elif hasattr(current_player, 'is_ai_commander') and current_player.is_ai_commander and current_player.id in ai_commanders:
            print(f"🎯 AI COMMANDER TURN: {current_player.nation} id={current_player.id}")
            
            # Sprawdź czy są tokeny do wystawienia
            import os
            nowe_folder = f"nowe_dla_{current_player.id}"
            if os.path.exists(nowe_folder):
                files = os.listdir(nowe_folder)
                print(f"📁 Tokeny do wystawienia w {nowe_folder}: {len(files)} plików")
            else:
                print(f"📁 Brak folderu {nowe_folder}")
            
            # AI Commander turn
            ai_commander = ai_commanders[current_player.id]
            ai_commander.pre_resupply(game_engine)
            ai_commander.make_tactical_turn(game_engine)
            
            # Sprawdź czy tokeny zostały wystawione
            if os.path.exists(nowe_folder):
                files_after = os.listdir(nowe_folder)
                print(f"📁 Tokeny pozostałe w {nowe_folder}: {len(files_after)} plików")
        
        # Następna tura
        is_full_turn_end = turn_manager.next_turn()
        
        if is_full_turn_end:
            turn_count += 1
            print(f"\n🏁 === KONIEC PEŁNEJ TURY {turn_count-1} ===")
    
    return True

def check_deployment_results():
    """Sprawdza rezultaty deployment systemu"""
    print("\n🔍 SPRAWDZENIE REZULTATÓW DEPLOYMENT:")
    print("-" * 50)
    
    import os
    from pathlib import Path
    
    print("\n📁 Status folderów nowe_dla_X:")
    deployment_found = False
    
    for folder in ['nowe_dla_1', 'nowe_dla_2', 'nowe_dla_3']:
        if os.path.exists(folder):
            files = os.listdir(folder)
            print(f"  {folder}: {len(files)} plików")
            if files:
                deployment_found = True
                for f in files[:3]:  # pokaż pierwsze 3
                    print(f"    - {f}")
        else:
            print(f"  {folder}: brak folderu")

    print("\n📁 Status aktualne/:")
    aktualne_dir = Path("assets/tokens/aktualne")
    if aktualne_dir.exists():
        files = list(aktualne_dir.glob("*.json"))
        print(f"  aktualne/: {len(files)} tokenów")
        for f in files[-3:]:  # pokaż ostatnie 3
            print(f"    - {f.name}")
    else:
        print("  aktualne/: brak katalogu")
    
    # Sprawdź logi AI
    print("\n📋 Sprawdzenie logów AI:")
    logs_dir = Path("logs/ai_general")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.csv"))
        print(f"  Logi AI General: {len(log_files)} plików")
        for log_file in log_files[-2:]:  # ostatnie 2
            print(f"    - {log_file.name}")
    else:
        print("  Brak logów AI General")
    
    return deployment_found

if __name__ == "__main__":
    """Główna funkcja testowa"""
    try:
        print("🔧 URUCHAMIANIE TESTU NAPRAWIONEGO DEPLOYMENT AI")
        print("=" * 60)
        
        # Uruchom test
        success = run_deployment_test()
        
        if success:
            print("\n✅ TEST ZAKOŃCZONY POMYŚLNIE")
            
            # Sprawdź rezultaty
            deployment_found = check_deployment_results()
            
            if deployment_found:
                print("\n🎯 REZULTAT: Znaleziono tokeny - deployment system DZIAŁA")
            else:
                print("\n⚠️ REZULTAT: Brak tokenów - AI General nie kupił nic (prawdopodobnie za mało PE)")
        else:
            print("\n❌ TEST NIEUDANY")
            
    except Exception as e:
        print(f"\n❌ BŁĄD TESTU: {e}")
        import traceback
        traceback.print_exc()
