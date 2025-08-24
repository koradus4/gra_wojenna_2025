"""Headless AI gra - automatyczne testy wszystkich AI bez GUI"""

import sys
import os
# Dodaj root project do path
root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, root_dir)

from engine.engine import GameEngine
from engine.player import Player
from ai.ai_commander import AICommander
from ai.ai_general import AIGeneral
from core.tura import TurnManager
from core.ekonomia import EconomySystem
import time

def run_headless_ai_game():
    """Uruchom pełną grę z AI bez GUI"""
    try:
        print("🤖 HEADLESS AI GAME - AUTOMATYCZNA GRA WSZYSTKICH AI")
        print("=" * 60)
        
        # Załaduj grę
        engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json", 
            tokens_start_path="assets/start_tokens.json"
        )
        
        print(f"✅ Gra załadowana: {len(engine.tokens)} tokenów")
        
        # Stwórz graczy
        players = [
            Player(1, "Polska", "Generał", 2000),
            Player(2, "Polska", "Dowódca", 300),
            Player(3, "Polska", "Dowódca", 300),
            Player(4, "Niemcy", "Generał", 2000),
            Player(5, "Niemcy", "Dowódca", 300),
            Player(6, "Niemcy", "Dowódca", 300),
        ]
        
        # Dodaj ekonomię do wszystkich graczy
        for player in players:
            player.economy = EconomySystem()
        
        # Ustaw wszystkich jako AI
        ai_generals = {}
        ai_commanders = {}
        
        for player in players:
            if player.role == "Generał":
                player.is_ai = True
                nationality = "polish" if player.nation == "Polska" else "german"
                ai_generals[player.id] = AIGeneral(nationality)
                print(f"🧠 AI Generał: {player.nation} (id={player.id})")
            else:
                player.is_ai_commander = True
                ai_commanders[player.id] = AICommander(player)
                print(f"⚔️  AI Dowódca: {player.nation} (id={player.id})")
        
        # Turn manager
        turn_manager = TurnManager(players)
        
        print(f"\n🎮 ROZPOCZYNAM AUTOMATYCZNĄ GRĘ...")
        print(f"📊 Graczy: {len(players)}, AI Generałów: {len(ai_generals)}, AI Dowódców: {len(ai_commanders)}")
        
        # Główna pętla gry
        max_turns = 2  # TYLKO 2 TURY na debugging
        turn_count = 0
        
        while turn_count < max_turns:
            turn_count += 1
            print(f"\n" + "="*40)
            print(f"🕰️  TURA {turn_count}")
            print(f"="*40)
            
            # Przejdź przez wszystkich graczy w turze
            players_in_turn = 0
            while players_in_turn < len(players):
                current_player = turn_manager.get_current_player()
                engine.current_player_obj = current_player
                
                print(f"\n👤 {current_player.nation} {current_player.role} (id={current_player.id})")
                
                if hasattr(current_player, 'is_ai') and current_player.is_ai and current_player.id in ai_generals:
                    print(f"🧠 Tura AI Generała...")
                    ai_general = ai_generals[current_player.id]
                    if current_player.role == "Generał":
                        current_player.economy.generate_economic_points()
                        current_player.economy.add_special_points()
                    ai_general.make_turn(engine)
                    
                elif hasattr(current_player, 'is_ai_commander') and current_player.is_ai_commander and current_player.id in ai_commanders:
                    print(f"⚔️  Tura AI Dowódcy...")
                    ai_commander = ai_commanders[current_player.id]
                    ai_commander.make_tactical_turn(engine)
                
                # Następny gracz
                is_full_turn_end = turn_manager.next_turn()
                players_in_turn += 1
                
                if is_full_turn_end:
                    break
                    
                # Krótka pauza dla czytelności
                time.sleep(0.1)
            
            print(f"\n✅ Tura {turn_count} zakończona")
            
            # Sprawdź warunki zwycięstwa
            if turn_count >= max_turns:
                print(f"\n🏁 KONIEC TESTU po {max_turns} turach")
                break
        
        # Podsumowanie
        print(f"\n" + "="*60)
        print(f"📊 PODSUMOWANIE AUTOMATYCZNEJ GRY")
        print(f"="*60)
        print(f"Rozegrano tur: {turn_count}")
        print(f"Graczy AI: {len(ai_generals) + len(ai_commanders)}")
        
        for player in players:
            points = getattr(player, 'victory_points', 0)
            print(f"{player.nation} {player.role} (id={player.id}): {points} punktów zwycięstwa")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd gry: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    run_headless_ai_game()
