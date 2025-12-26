#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Szybki test gry AI vs AI z indywidualnymi profilami
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import time

def quick_ai_vs_ai_test():
    """Programowo ustaw AI vs AI i uruchom test"""
    
    print("🎯 SZYBKI TEST AI VS AI Z INDYWIDUALNYMI PROFILAMI")
    print("=" * 60)
    
    try:
        # Import głównej klasy GameLauncher
        import sys
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", "main.py")
        main_module = importlib.util.module_from_spec(spec)
        sys.modules["main"] = main_module
        spec.loader.exec_module(main_module)
        
        # Stwórz instancję w trybie testowym
        root = tk.Tk()
        root.withdraw()  # Ukryj główne okno
        
        launcher = main_module.GameLauncher()
        launcher.root.withdraw()  # Ukryj okno launchera
        
        print("✅ Launcher załadowany")
        
        # Ustaw AI dla wszystkich graczy z różnymi profilami
        launcher.ai_polish_general.set(True)
        launcher.ai_german_general.set(True) 
        launcher.ai_polish_commander_1.set(True)
        launcher.ai_polish_commander_2.set(True)
        launcher.ai_german_commander_1.set(True)
        launcher.ai_german_commander_2.set(True)
        
        # Ustaw różne profile dla różnych graczy
        launcher.profile_polish_general.set("🔥 Aggressive")       # Agresywny polski generał
        launcher.profile_german_general.set("🛡️ Defensive")       # Defensywny niemiecki generał
        launcher.profile_polish_commander_1.set("🎯 Balanced")     # Zbalansowany dowódca
        launcher.profile_polish_commander_2.set("🔥 Aggressive")   # Agresywny dowódca
        launcher.profile_german_commander_1.set("🛡️ Defensive")   # Defensywny dowódca
        launcher.profile_german_commander_2.set("🎯 Balanced")     # Zbalansowany dowódca
        
        print("✅ AI ustawione dla wszystkich graczy z profilami:")
        print("   🇵🇱 Polski Generał: 🔥 Aggressive")
        print("   🇩🇪 Niemiecki Generał: 🛡️ Defensive")
        print("   🇵🇱 Polski Dowódca 1: 🎯 Balanced")
        print("   🇵🇱 Polski Dowódca 2: 🔥 Aggressive")
        print("   🇩🇪 Niemiecki Dowódca 1: 🛡️ Defensive")
        print("   🇩🇪 Niemiecki Dowódca 2: 🎯 Balanced")
        
        # Test konwersji profili
        profiles_to_test = [
            ("🔥 Aggressive", "aggressive"),
            ("🛡️ Defensive", "defensive"), 
            ("🎯 Balanced", "balanced")
        ]
        
        print("\n🔄 Test konwersji profili:")
        for display, expected in profiles_to_test:
            converted = launcher._convert_display_to_value(display)
            status = "✅" if converted == expected else "❌"
            print(f"   '{display}' → '{converted}' {status}")
        
        # Ustawienia gry na szybką rozgrywkę
        launcher.max_turns.set("5")  # Tylko 5 tur dla testu
        launcher.victory_mode.set("turns")
        
        print("\n🎮 Ustawienia gry:")
        print("   Maksymalne tury: 5")
        print("   Tryb zwycięstwa: turns") 
        
        print("\n🚀 Rozpoczynanie gry AI vs AI...")
        print("💡 Obserwuj różnice w zachowaniu różnych profili AI!")
        print("   - Aggressive: szybkie ataki, ryzykowne ruchy")  
        print("   - Defensive: ostrożność, większe garnizony")
        print("   - Balanced: zrównoważone podejście")
        
        # Uruchom grę (w tle)
        try:
            launcher.launch_game_with_settings()
            print("✅ Gra uruchomiona pomyślnie!")
        except Exception as e:
            print(f"❌ Błąd uruchamiania gry: {e}")
            return False
        
        launcher.root.destroy()
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        return False

if __name__ == "__main__":
    success = quick_ai_vs_ai_test()
    if success:
        print("\n🎉 TEST ZAKOŃCZONY POMYŚLNIE!")
        print("💡 Gra AI vs AI z indywidualnymi profilami została uruchomiona")
    else:
        print("\n🔥 BŁĄD W TEŚCIE!")