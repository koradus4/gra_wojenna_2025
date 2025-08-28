#!/usr/bin/env python3
"""
GRAJ Z PEŁNYM LOGOWANIEM AI
Uruchamia grę z wszystkimi patchami logowania AI
"""

import sys
import os
from pathlib import Path

# Dodaj główny folder do path
sys.path.append(str(Path(__file__).parent.parent))

def main():
    print("🎮 URUCHAMIANIE GRY Z PEŁNYM LOGOWANIEM AI")
    print("="*60)
    
    # Krok 1: Zastosuj monkey patches
    print("🐵 [STEP 1] Aplikowanie monkey patches...")
    try:
        from utils.ai_monkey_patch import apply_all_ai_patches
        apply_all_ai_patches()
        print("✅ [STEP 1] Monkey patches zastosowane pomyślnie!")
    except Exception as e:
        print(f"❌ [STEP 1] Błąd monkey patch: {e}")
        return False
    
    # Krok 2: Przygotuj foldery logów
    print("\n📁 [STEP 2] Przygotowywanie folderów logów...")
    try:
        logs_dir = Path("logs")
        ai_flow_dir = logs_dir / "ai_flow"
        ai_flow_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ [STEP 2] Folder logów: {ai_flow_dir}")
    except Exception as e:
        print(f"❌ [STEP 2] Błąd tworzenia folderów: {e}")
        return False
    
    # Krok 3: Sprawdź czy istnieją AI
    print("\n🤖 [STEP 3] Sprawdzanie dostępności AI...")
    try:
        from ai.ai_general import AIGeneral
        from ai.ai_commander import make_tactical_turn
        print("✅ [STEP 3] AI General dostępny")
        print("✅ [STEP 3] AI Commander dostępny")
    except Exception as e:
        print(f"❌ [STEP 3] Błąd importu AI: {e}")
        return False
    
    # Krok 4: Uruchom główną grę
    print("\n🚀 [STEP 4] Uruchamianie głównej gry...")
    try:
        # Import i uruchomienie main.py
        import main
        print("✅ [STEP 4] Gra uruchomiona pomyślnie!")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ [STOP] Gra zatrzymana przez użytkownika")
        return True
        
    except Exception as e:
        print(f"❌ [STEP 4] Błąd uruchamiania gry: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_logging_info():
    """Pokazuje informacje o systemie logowania"""
    print("\n📝 INFORMACJE O LOGOWANIU:")
    print("-" * 40)
    print("🎯 Logi AI będą zapisywane w:")
    print("  📁 logs/ai_flow/")
    print("     ├── ai_flow_{nation}_{timestamp}.csv     - główne zdarzenia")
    print("     ├── purchases_{nation}_{timestamp}.csv   - szczegóły zakupów")
    print("     ├── deployment_{nation}_{timestamp}.csv  - szczegóły deployment")
    print("     ├── debug_{nation}_{timestamp}.csv       - zdarzenia debug")
    print("     └── summary_{nation}_{timestamp}_turn_{X}.json - raporty")
    print()
    print("🔍 Logowane zdarzenia:")
    print("  🛒 AI General: analiza, decyzje, zakupy, tworzenie tokenów")
    print("  🎖️  AI Commander: deployment, pozycjonowanie, czyszczenie")
    print("  📊 Raporty: podsumowania per tura, statystyki sukcesu")
    print()
    print("💡 Aby przejrzeć logi podczas gry:")
    print("  - Otwórz drugi terminal")
    print("  - Przejdź do folderu logs/ai_flow/")
    print("  - Użyj: tail -f *.csv (Linux/macOS) lub Get-Content *.csv -Wait (PowerShell)")

def cleanup_old_logs():
    """Opcjonalne czyszczenie starych logów"""
    try:
        ai_flow_dir = Path("logs/ai_flow")
        if ai_flow_dir.exists():
            old_files = list(ai_flow_dir.glob("*"))
            if old_files:
                print(f"\n🧹 Znaleziono {len(old_files)} starych plików logów")
                answer = input("❓ Czy wyczyścić stare logi? (t/N): ").lower()
                
                if answer in ['t', 'tak', 'y', 'yes']:
                    for file in old_files:
                        try:
                            if file.is_file():
                                file.unlink()
                            elif file.is_dir():
                                import shutil
                                shutil.rmtree(file)
                        except Exception as e:
                            print(f"⚠️ Nie można usunąć {file}: {e}")
                    
                    print("✅ Stare logi wyczyszczone")
                else:
                    print("📁 Zachowano stare logi")
    except Exception as e:
        print(f"⚠️ Błąd czyszczenia logów: {e}")

if __name__ == "__main__":
    print("🎯 GRAJ GRĘ WOJENNĄ Z PEŁNYM DEBUGIEM AI")
    print("Autor: GitHub Copilot & User")
    print("Data:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    show_logging_info()
    cleanup_old_logs()
    
    print("\n" + "="*60)
    print("🎮 ROZPOCZYNAM GRĘ...")
    print("="*60)
    
    success = main()
    
    if success:
        print("\n" + "="*60)
        print("✅ GRA ZAKOŃCZONA POMYŚLNIE")
        print("📝 Sprawdź logi w folderze logs/ai_flow/")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ WYSTĄPIŁY BŁĘDY")
        print("🔍 Sprawdź komunikaty powyżej")
        print("="*60)
