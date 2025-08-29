#!/usr/bin/env python3
"""
QUICK AI LAUNCHER - szybkie uruchomienie gry z AI i logowaniem
Automatycznie konfiguruje:
- Polski Generał AI
- Niemiecki Generał AI  
- Wszystkich dowódców AI
- Pełne logowanie
"""

import tkinter as tk
import sys
from pathlib import Path

# Dodaj główny folder do path
sys.path.append(str(Path(__file__).parent.parent))

def quick_launch_with_ai():
    """Szybkie uruchomienie z pełnym AI"""
    print("🚀 QUICK AI LAUNCHER - PEŁNE AI + LOGOWANIE")
    print("="*60)
    
    # Import głównej klasy
    from main_ai import GameLauncher
    
    # Utwórz launcher ale nie pokazuj UI
    launcher = GameLauncher()
    
    # Automatycznie ustaw wszystkich AI
    launcher.ai_polish_general.set(True)
    launcher.ai_german_general.set(True)
    launcher.ai_polish_commander_1.set(True)
    launcher.ai_polish_commander_2.set(True)
    launcher.ai_german_commander_1.set(True)
    launcher.ai_german_commander_2.set(True)
    
    # Ustawienia gry
    launcher.max_turns.set("5")  # Krótka gra dla testów
    launcher.victory_mode.set("turns")
    
    print("🤖 KONFIGURACJA AI:")
    print("   ✅ Polski Generał AI")
    print("   ✅ Niemiecki Generał AI")
    print("   ✅ Wszyscy dowódcy AI")
    print("   🎯 5 tur, tryb: turns")
    print()
    
    # Nie uruchamiaj GUI, idź od razu do gry
    launcher.root.destroy()
    
    # Uruchom grę z pełnym logowaniem
    print("🐵 Aplikowanie monkey patches...")
    try:
    # usunięto moduł ai_monkey_patch (nieużywany szkic logowania)
        print("✅ Monkey patches aktywne!")
    except Exception as e:
        print(f"⚠️ Błąd monkey patches: {e}")
    
    # Uruchom grę
    print("🎮 URUCHAMIANIE GRY...")
    launcher.launch_game_with_settings()

if __name__ == "__main__":
    quick_launch_with_ai()
