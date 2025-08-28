#!/usr/bin/env python3
"""
Test AI Observer Launcher GUI
"""
import sys
sys.path.append('.')

from ai_observer_launcher import AIObserverLauncher

def test_gui():
    print("🧪 TEST GUI LAUNCHER")
    try:
        launcher = AIObserverLauncher()
        print("✅ GUI launcher utworzony")
        
        # Pokaż okno na 10 sekund
        launcher.root.after(10000, lambda: [
            print("⏰ Test zakończony - zamykam GUI"),
            launcher.root.quit()
        ])
        
        print("🎮 Uruchamiam GUI na 10 sekund...")
        launcher.run()
        print("✅ Test GUI zakończony")
        
    except Exception as e:
        print(f"❌ Błąd test GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gui()
