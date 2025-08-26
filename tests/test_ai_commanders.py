#!/usr/bin/env python3
"""
Test script - AI Commanders with Human Generals
"""

from core.tura import TurnManager
from engine.player import Player
from core.ekonomia import EconomySystem
from engine.engine import GameEngine, update_all_players_visibility
from core.zwyciestwo import VictoryConditions
from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander
from utils.game_cleaner import clean_all_for_new_game
import time


def create_test_game():
    """Tworzy grę testową z AI dowódcami i human generałami"""
    print("🎮 Tworzenie gry testowej: AI Dowódcy + Human Generałowie")
    
    # Wyczyszczenie środowiska
    clean_all_for_new_game()
    
    # Inicjalizacja silnika gry
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json",
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=True
    )
    
    # Utworzenie graczy
    players = [
        Player(1, "Polska", "Generał", 120),      # Human
        Player(2, "Polska", "Dowódca", 60),       # AI
        Player(3, "Polska", "Dowódca", 60),       # AI
        Player(4, "Niemcy", "Generał", 120),      # Human
        Player(5, "Niemcy", "Dowódca", 60),       # AI
        Player(6, "Niemcy", "Dowódca", 60),       # AI
    ]
    
    # Dodanie ekonomii dla wszystkich graczy
    for p in players:
        p.economy = EconomySystem()
    
    # Udostępnienie graczy w silniku
    game_engine.players = players
    
    # Aktualizacja widoczności
    update_all_players_visibility(players, game_engine.tokens, game_engine.board)
    
    # Synchronizacja punktów ekonomicznych
    for p in players:
        if hasattr(p, 'punkty_ekonomiczne'):
            p.punkty_ekonomiczne = p.economy.get_points()['economic_points']
    
    # Menedżer tur
    turn_manager = TurnManager(players, game_engine=game_engine)
    
    # Utworzenie AI dowódców dla odpowiednich graczy
    ai_commanders = {}
    for p in players:
        if p.role == "Dowódca":
            ai_commanders[p.id] = AICommander(p)
            print(f"✅ Utworzono AI Commander dla gracza {p.id} ({p.nation} {p.role})")
    
    # Warunki zwycięstwa
    victory_conditions = VictoryConditions(max_turns=10)  # Krótszy test
    
    print(f"\n🎯 Konfiguracja graczy:")
    for p in players:
        ai_type = "AI" if p.role == "Dowódca" else "HUMAN"
        print(f"   - ID:{p.id} {p.nation} {p.role} [{ai_type}]")
    
    return game_engine, players, turn_manager, ai_commanders, victory_conditions


def run_test_game():
    """Uruchamia test z AI dowódcami"""
    game_engine, players, turn_manager, ai_commanders, victory_conditions = create_test_game()
    
    print(f"\n🚀 Uruchamianie testu - maksymalnie {victory_conditions.max_turns} tur")
    print("=" * 60)
    
    turn_count = 0
    
    while True:
        turn_count += 1
        print(f"\n🔄 TURA {turn_count}")
        print("-" * 40)
        
        # Sprawdzenie warunków zwycięstwa
        if victory_conditions.check_game_over(turn_count):
            print(f"⏰ Osiągnięto limit {victory_conditions.max_turns} tur")
            print(victory_conditions.get_victory_message())
            break
        
        # Przetwarzanie każdego gracza w turze
        for current_player in players:
            print(f"\n👤 Gracz {current_player.id}: {current_player.nation} {current_player.role}")
            
            if current_player.role == "Dowódca":
                # AI Commander wykonuje turę
                try:
                    ai_commander = ai_commanders[current_player.id]
                    print(f"🤖 AI Commander {current_player.id} wykonuje turę...")
                    
                    # POPRAWKA: Ustaw aktywnego gracza w GameEngine
                    game_engine.current_player_obj = current_player
                    
                    # Symulacja czasu na analizę
                    time.sleep(0.5)
                    
                    # AI wykonuje turę
                    ai_commander.make_tactical_turn(game_engine)
                    print(f"✅ AI Commander {current_player.id} zakończył turę")
                    
                except Exception as e:
                    print(f"❌ Błąd AI Commander {current_player.id}: {e}")
                    
            else:
                # Human General - symulacja lub skip
                print(f"👨‍💼 Human General {current_player.id} - SKIPPED (test mode)")
                time.sleep(0.2)
        
        # Aktualizacja widoczności po turze
        update_all_players_visibility(players, game_engine.tokens, game_engine.board)
        
        # Limit bezpieczeństwa
        if turn_count >= victory_conditions.max_turns:
            print(f"\n⏰ Osiągnięto limit {victory_conditions.max_turns} tur - koniec testu")
            break
    
    print(f"\n📊 TEST ZAKOŃCZONY po {turn_count} turach")
    print("=" * 60)
    
    # Sprawdzenie logów
    print("\n📁 Sprawdzanie wygenerowanych logów...")
    import os
    
    log_dirs = ["logs/ai_commander", "logs/ai_general", "logs/game_actions"]
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            files = os.listdir(log_dir)
            if files:
                print(f"   {log_dir}: {len(files)} plików")
                for f in files[:3]:  # Pokazuj pierwsze 3
                    print(f"     - {f}")
                if len(files) > 3:
                    print(f"     ... i {len(files)-3} więcej")
            else:
                print(f"   {log_dir}: brak plików")
        else:
            print(f"   {log_dir}: katalog nie istnieje")


if __name__ == "__main__":
    try:
        run_test_game()
    except KeyboardInterrupt:
        print("\n⚠️  Test przerwany przez użytkownika")
    except Exception as e:
        print(f"\n❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
