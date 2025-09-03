#!/usr/bin/env python3
"""
LAUNCHER ANALIZY PE - Launcher do analizy transferów PE
Automatycznie:
1. Czyści stare CSV i żetony
2. Uruchamia test 10-turowy z naprawionymi PE
3. Analizuje wyniki
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

def main():
    """Główna funkcja launchera"""
    print("🚀 LAUNCHER ANALIZY PE")
    print("=" * 60)
    print("🎯 Analiza transferów PE między Generałami a Dowódcami")
    print("🔧 Z naprawką blokady ujemnych PE")
    print("=" * 60)
    
    parser = argparse.ArgumentParser(description="Launcher analizy PE")
    parser.add_argument('--pomij-czyszczenie', action='store_true',
                       help='Pomiń czyszczenie danych (użyj istniejących)')
    parser.add_argument('--tylko-czyszczenie', action='store_true', 
                       help='Tylko wyczyść dane (nie uruchamiaj testu)')
    parser.add_argument('--szybki', action='store_true',
                       help='Szybki test (3 tury zamiast 10)')
    
    args = parser.parse_args()
    
    # Względne ścieżki z folderu tools
    script_dir = Path(__file__).parent.parent  # Idź poziom wyżej z tools/
    auto_game_script = script_dir / "auto_game_10_turns.py"
    
    if not auto_game_script.exists():
        print(f"❌ BŁĄD: Nie znaleziono {auto_game_script}")
        return 1
    
    try:
        if not args.pomij_czyszczenie:
            print("🧹 KROK 1: CZYSZCZENIE STARYCH DANYCH")
            print("-" * 40)
            
            # Wywołaj czyszczenie
            result = subprocess.run([
                sys.executable, str(auto_game_script), 
                '--clean-only'
            ], cwd=script_dir)
            
            if result.returncode != 0:
                print("⚠️ Błąd podczas czyszczenia, ale kontynuuję...")
            
            if args.tylko_czyszczenie:
                print("✅ CZYSZCZENIE ZAKOŃCZONE!")
                return 0
        
        print("🎮 KROK 2: URUCHAMIANIE TESTU PE")
        print("-" * 40)
        print("🔍 Test transferów PE z naprawką ujemnych PE")
        print("⏱️  10 tur AI vs AI")
        print("📊 Szczegółowe logowanie PE na każdym kroku")
        print()
        
        # Uruchom test z czyszczeniem jeśli nie pominięto
        cmd_args = [sys.executable, str(auto_game_script)]
        if not args.pomij_czyszczenie:
            cmd_args.append('--clean')
        
        result = subprocess.run(cmd_args, cwd=script_dir)
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ TEST ZAKOŃCZONY POMYŚLNIE!")
            print("=" * 60)
            print("📊 ANALIZA WYNIKÓW:")
            print("   • Sprawdź logi PE w terminalu powyżej")
            print("   • Szukaj wpisów: [PE FLOW], [PE AFTER], [PE BLOCK]")
            print("   • Czy nadal występują ujemne PE?")
            print("   • Czy transfery PE działają poprawnie?")
            print()
            print("🔍 KLUCZOWE PYTANIA:")
            print("   1. Czy generałowie przekazują PE dowódcom?")
            print("   2. Czy dowódcy wydają tylko dostępne PE?")
            print("   3. Czy bilans PE się zgadza?")
            print("=" * 60)
            return 0
        else:
            print("\n❌ TEST ZAKOŃCZONY Z BŁĘDEM!")
            return result.returncode
            
    except KeyboardInterrupt:
        print("\n🛑 PRZERWANO PRZEZ UŻYTKOWNIKA")
        return 1
    except Exception as e:
        print(f"\n❌ BŁĄD KRYTYCZNY: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
