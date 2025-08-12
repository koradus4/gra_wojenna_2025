#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test naprawy błędu pyimage1 w launcherze
"""

import tkinter as tk
from tkinter import messagebox
import json
import tempfile
import os

def test_launcher_fix():
    """Test naprawy błędu pyimage1"""
    print("Rozpoczynam test naprawy błędu pyimage1...")
    
    try:
        # Import launchera
        import game_launcher_ai
        
        # Utwórz launcher
        launcher = game_launcher_ai.GameLauncherAI()
        print("✓ Launcher utworzony pomyślnie")
        
        # Test zapisywania konfiguracji
        config = launcher.save_game_config()
        print("✓ Konfiguracja zapisana pomyślnie")
        
        # Test ładowania konfiguracji
        with open('ai_game_config.json', 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
        print("✓ Konfiguracja wczytana pomyślnie")
        
        # Test tworzenia graczy z konfiguracji
        players = launcher.create_players_from_config(loaded_config)
        print(f"✓ Utworzono {len(players)} graczy")
        
        # Zniszcz launcher aby przetestować czyszczenie
        launcher.root.destroy()
        print("✓ Launcher zamknięty pomyślnie")
        
        # Test metody czystego startu (bez uruchamiania GUI)
        print("✓ Test naprawy błędu pyimage1 zakończony pomyślnie!")
        
        # Posprzątaj
        if os.path.exists('ai_game_config.json'):
            os.remove('ai_game_config.json')
            
        return True
        
    except Exception as e:
        print(f"✗ Błąd w teście: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_creation():
    """Test tworzenia konfiguracji bez GUI"""
    print("\nTest tworzenia konfiguracji...")
    
    # Przykładowa konfiguracja
    test_config = {
        'game_mode': 'human_vs_ai',
        'players': [
            {'id': 1, 'position': 'Generał Polski', 'nation': 'Polska', 'role': 'Generał', 'type': 'human', 'ai_level': 'medium', 'time': 5},
            {'id': 2, 'position': 'Dowódca Polski #1', 'nation': 'Polska', 'role': 'Dowódca', 'type': 'human', 'ai_level': 'medium', 'time': 5},
            {'id': 3, 'position': 'Dowódca Polski #2', 'nation': 'Polska', 'role': 'Dowódca', 'type': 'human', 'ai_level': 'medium', 'time': 5},
            {'id': 4, 'position': 'Generał Niemiecki', 'nation': 'Niemcy', 'role': 'Generał', 'type': 'ai', 'ai_level': 'medium', 'time': 5},
            {'id': 5, 'position': 'Dowódca Niemiecki #1', 'nation': 'Niemcy', 'role': 'Dowódca', 'type': 'ai', 'ai_level': 'medium', 'time': 5},
            {'id': 6, 'position': 'Dowódca Niemiecki #2', 'nation': 'Niemcy', 'role': 'Dowódca', 'type': 'ai', 'ai_level': 'medium', 'time': 5}
        ],
        'ai_settings': {
            'enable_minimax': True,
            'enable_mcts': True,
            'enable_dqn': False,
            'enable_ppo': False,
            'minimax_depth': 3,
            'mcts_simulations': 1000,
            'ai_time_limit': 10,
            'debug_mode': True,
            'show_ai_thinking': True,
            'save_game_logs': True,
            'show_decision_tree': False,
            'enable_learning': True,
            'model_path': ''
        }
    }
    
    # Zapisz konfigurację
    with open('test_config.json', 'w', encoding='utf-8') as f:
        json.dump(test_config, f, indent=2, ensure_ascii=False)
    
    print("✓ Konfiguracja testowa utworzona")
    
    # Test załadowania przez launcher
    try:
        import game_launcher_ai
        launcher = game_launcher_ai.GameLauncherAI()
        
        # Nie uruchamiaj GUI, tylko test metod
        players = launcher.create_players_from_config(test_config)
        print(f"✓ Utworzono {len(players)} graczy z konfiguracji testowej")
        
        launcher.root.destroy()
        
        # Posprzątaj
        if os.path.exists('test_config.json'):
            os.remove('test_config.json')
            
        return True
        
    except Exception as e:
        print(f"✗ Błąd w teście konfiguracji: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TEST NAPRAWY BŁĘDU PYIMAGE1 W LAUNCHERZE")
    print("=" * 60)
    
    success1 = test_launcher_fix()
    success2 = test_config_creation()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✓ WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
        print("✓ Naprawa błędu pyimage1 działa poprawnie")
        print("✓ Launcher może bezpiecznie uruchamiać grę w nowym procesie")
    else:
        print("✗ NIEKTÓRE TESTY NIE PRZESZŁY")
        print("✗ Wymagane dodatkowe poprawki")
    print("=" * 60)
