#!/usr/bin/env python3
"""
QUICK OBSERVER - szybkie uruchomienie obserwacji AI bez GUI
Automatyczne ustawienia:
- Wszystkie AI włączone
- 15s pauzy
- Auto-kontynuacja
- Pełny monitoring
- 3 tury dla szybkich testów
"""

import sys
from pathlib import Path

# Dodaj główny folder do path
sys.path.append(str(Path(__file__).parent.parent))

def quick_observer():
    """Szybka obserwacja z predefiniowanymi ustawieniami"""
    print("⚡ QUICK OBSERVER - SZYBKA OBSERWACJA AI")
    print("="*60)
    
    # Predefiniowane ustawienia
    observer_config = {
        'pause_duration': 15,      # 15s pauzy
        'auto_continue': True,     # Auto-kontynuacja
        'show_map_details': True,  # Pokaż mapę
        'monitor_folders': True,   # Monitor folderów
        'verbose_logging': True    # Verbose logi
    }
    
    print("🔧 KONFIGURACJA QUICK OBSERVER:")
    print("-" * 40)
    print(f"⏱️ Pauza po turze AI: {observer_config['pause_duration']}s")
    print(f"🔄 Auto-kontynuuj: {'TAK' if observer_config['auto_continue'] else 'NIE'}")
    print(f"🗺️ Szczegóły mapy: {'TAK' if observer_config['show_map_details'] else 'NIE'}")
    print(f"📁 Monitor folderów: {'TAK' if observer_config['monitor_folders'] else 'NIE'}")
    print(f"📝 Verbose logging: {'TAK' if observer_config['verbose_logging'] else 'NIE'}")
    print()
    
    print("🤖 AI PLAYERS (wszystkie włączone):")
    print("  ✅ Polski Generał")
    print("  ✅ Niemiecki Generał")
    print("  ✅ Polski Dowódca 1")
    print("  ✅ Polski Dowódca 2")
    print("  ✅ Niemiecki Dowódca 1")
    print("  ✅ Niemiecki Dowódca 2")
    print()
    
    print(f"🎮 USTAWIENIA GRY:")
    print(f"  🔢 Maksymalne tury: 3")
    print(f"  🏆 Tryb zwycięstwa: turns")
    print()
    
    # Zastosuj observer patches
    print("🐵 APLIKOWANIE OBSERVER PATCHES...")
    try:
        from utils.ai_observer_patches import apply_observer_patches
        success = apply_observer_patches(observer_config)
        
        if success:
            print("✅ Observer patches zastosowane!")
        else:
            print("⚠️ Błąd observer patches - kończyę")
            return
            
    except Exception as e:
        print(f"❌ Błąd observer patches: {e}")
        return
    
    # Uruchom grę
    print("🎮 URUCHAMIANIE GRY Z QUICK OBSERVER...")
    try:
        from main_ai import GameLauncher
        
        # Utwórz launcher bez GUI
        launcher = GameLauncher()
        
        # Wszystkie AI włączone
        launcher.ai_polish_general.set(True)
        launcher.ai_german_general.set(True)
        launcher.ai_polish_commander_1.set(True)
        launcher.ai_polish_commander_2.set(True)
        launcher.ai_german_commander_1.set(True)
        launcher.ai_german_commander_2.set(True)
        
        # Krótka gra
        launcher.max_turns.set("3")
        launcher.victory_mode.set("turns")
        
        # Zamknij GUI i uruchom grę
        launcher.root.destroy()
        launcher.launch_game_with_settings()
        
        # Podsumowanie
        try:
            from utils.ai_observer_patches import show_final_summary
            show_final_summary()
        except Exception as e:
            print(f"⚠️ Błąd podsumowania: {e}")
            
    except Exception as e:
        print(f"❌ Błąd uruchamiania quick observer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_observer()
