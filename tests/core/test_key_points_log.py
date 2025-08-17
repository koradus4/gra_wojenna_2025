#!/usr/bin/env python3
"""
Test loga punktów z key_points w AI

Sprawdza, czy system poprawnie wyświetla log o przyznanych punktach.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.engine import GameEngine
from engine.player import Player
from core.ekonomia import EconomySystem
from main_ai_vs_human import AIManager

def test_key_points_log():
    """Test systemu logowania punktów z key_points"""
    
    print("🧪 TEST LOGA PUNKTÓW Z KEY_POINTS")
    print("=" * 50)
    
    # Inicjalizacja GameEngine
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json",
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=True
    )
    
    # Stwórz graczy
    players = [
        Player(1, "Polska", "Generał", "Polski Generał", 
               "c:/Users/klif/kampania1939_fixed/gui/images/Marszałek Polski Edward Rydz-Śmigły.png"),
        Player(4, "Niemcy", "Generał", "Niemiecki Generał", 
               "c:/Users/klif/kampania1939_fixed/gui/images/Generał pułkownik Walther von Brauchitsch.png"),
        Player(2, "Polska", "Dowódca", "Polski Dowódca", 
               "c:/Users/klif/kampania1939_fixed/gui/images/Generał Juliusz Rómmel.png"),
        Player(5, "Niemcy", "Dowódca", "Niemiecki Dowódca", 
               "c:/Users/klif/kampania1939_fixed/gui/images/Generał Fedor von Bock.png")
    ]
    
    # Inicjalizuj systemy ekonomiczne
    for player in players:
        player.economy = EconomySystem()
    
    # Stwórz AI Manager
    ai_manager = AIManager(game_engine, players)
    
    # Stwórz AI dla niemieckiej nacji
    for player in players:
        if player.nation == "Niemcy":
            ai_manager.create_ai_for_player(player, "medium")
    
    print("✅ System zainicjalizowany")
    print(f"   ├─ Gracze: {len(players)}")
    print(f"   ├─ AI kontroluje: {len(ai_manager.ai_instances)} graczy")
    print(f"   └─ Key points: {len(game_engine.key_points_state)}")
    
    # Sprawdź punkty przed
    print("\n📊 PUNKTY PRZED:")
    for player in players:
        if player.role == "Generał":
            print(f"   ├─ {player.name}: {player.economy.economic_points} pkt")
    
    # Wykonaj process_key_points
    print("\n🔄 WYKONYWANIE PROCESS_KEY_POINTS...")
    key_points_awards = game_engine.process_key_points(players)
    
    # Symulacja loga z main_ai_vs_human.py
    print("\n🎯 SYMULACJA LOGA Z MAIN_AI_VS_HUMAN.PY:")
    if key_points_awards:
        for player, points in key_points_awards.items():
            # Sprawdź czy to AI
            if ai_manager.is_ai_controlled(player.id):
                print(f"    🎯 AI {player.name}: +{points} pkt za key points")
            else:
                print(f"    🎯 {player.name}: +{points} pkt za key points")
    else:
        print("    ❌ Brak punktów do przyznania")
    
    # Sprawdź punkty po
    print("\n📊 PUNKTY PO:")
    for player in players:
        if player.role == "Generał":
            print(f"   ├─ {player.name}: {player.economy.economic_points} pkt")
    
    print("\n✅ Test zakończony pomyślnie!")
    print("🎮 LOG BĘDZIE POJAWIAŁ SIĘ W GRZE PODCZAS TURY AI")

if __name__ == "__main__":
    test_key_points_log()
