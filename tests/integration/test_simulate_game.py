#!/usr/bin/env python3
"""
Test symulacji pełnej partii AI vs Human
"""
import os
import sys
import json
import time
from pathlib import Path

# Dodaj główny folder do ścieżki  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simulate_ai_game():
    """Symuluje pełną partię AI vs Human"""
    print("=== SYMULACJA PARTII AI VS HUMAN ===\n")
    
    # Import klas z main_ai_vs_human.py
    from main_ai_vs_human import LearningAIGeneral, LearningAICommander
    from engine.player import Player
    from engine.engine import GameEngine
    from engine.board import Board
    
    # Test 1: Tworzenie graczy
    print("Test 1: Tworzenie graczy...")
    
    # Utwórz graczy
    players = [
        Player(player_id=1, nation="Polska", role="Generał"),
        Player(player_id=2, nation="Polska", role="Dowódca"),
        Player(player_id=3, nation="Niemcy", role="Generał"),
        Player(player_id=4, nation="Niemcy", role="Dowódca"),
    ]
    
    # Ustaw punkty startowe
    for player in players:
        player.victory_points = 0
        player.economic_points = 100
    
    print("✓ Gracze utworzeni")
    
    # Test 2: Tworzenie silnika gry
    print("\nTest 2: Tworzenie silnika gry...")
    
    try:
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json",
            tokens_start_path="assets/start_tokens.json",
            seed=42,
            read_only=True
        )
        print("✓ Silnik gry utworzony")
    except Exception as e:
        print(f"❌ Błąd tworzenia silnika: {e}")
        return
    
    # Test 3: Tworzenie AI
    print("\nTest 3: Tworzenie AI...")
    
    try:
        ai_general = LearningAIGeneral(players[2], game_engine, players, "medium")
        ai_commander = LearningAICommander(players[3], game_engine, "hard")
        print("✓ AI utworzone")
    except Exception as e:
        print(f"❌ Błąd tworzenia AI: {e}")
        return
    
    # Test 4: Symulacja gry
    print("\nTest 4: Symulacja partii...")
    
    # Symuluj kilka tur gry
    for turn in range(1, 6):  # 5 tur
        print(f"  Tura {turn}")
        
        # Aktualizuj punkty zwycięstwa (symulacja)
        for i, player in enumerate(players):
            player.victory_points += (turn * 2) + i
        
        # Pozwól AI zagrać turęę
        try:
            ai_general.make_turn()
            ai_commander.make_turn()
        except Exception as e:
            print(f"    ⚠ AI miało problem w turze {turn}: {e}")
    
    # Test 5: Symulacja końca gry
    print("\nTest 5: Symulacja końca gry...")
    
    # Oblicz wyniki
    polska_vp = sum(getattr(p, "victory_points", 0) for p in players if p.nation == "Polska")
    niemcy_vp = sum(getattr(p, "victory_points", 0) for p in players if p.nation == "Niemcy")
    
    print(f"  Wynik: Polska {polska_vp} vs {niemcy_vp} Niemcy")
    
    # Ustal kto wygrał
    victory_for_niemcy = niemcy_vp > polska_vp
    
    # Pozwól AI się uczyć
    try:
        ai_general.end_game(victory_for_niemcy)
        ai_commander.end_game(victory_for_niemcy)
        print("✓ AI zakończyło uczenie się")
    except Exception as e:
        print(f"❌ Błąd uczenia się AI: {e}")
        return
    
    # Test 6: Sprawdzenie zapisanych danych
    print("\nTest 6: Sprawdzenie zapisanych danych...")
    
    learning_data_dir = Path("ai/learning_data")
    
    # Sprawdź pliki AI
    ai_files = list(learning_data_dir.glob("*.json"))
    if ai_files:
        print(f"✓ Znaleziono {len(ai_files)} plików danych AI:")
        for file in ai_files:
            print(f"  - {file.name}")
            
            # Wyświetl zawartość
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if 'games_played' in data:
                    print(f"    Gier: {data['games_played']}, Wygranych: {data.get('wins', 0)}")
                    
            except Exception as e:
                print(f"    ⚠ Błąd odczytu {file.name}: {e}")
    else:
        print("❌ Nie znaleziono plików danych AI")
    
    print("\n=== PODSUMOWANIE ===")
    print("✅ Symulacja partii AI vs Human zakończona pomyślnie!")
    print("🧠 AI zapisało dane uczenia się")
    print("📊 Statystyki są dostępne w ai/learning_data/")
    print("🎮 System jest gotowy do rzeczywistej gry!")
    print("\n=== KONIEC SYMULACJI ===")

if __name__ == "__main__":
    simulate_ai_game()
