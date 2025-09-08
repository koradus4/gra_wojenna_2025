#!/usr/bin/env python3
"""Quick Phase 4 Test Runner - uruchamia testy Phase 4 z auto_game_10_turns.py"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Główna funkcja test runnera"""
    
    print("🧪 QUICK PHASE 4 TEST RUNNER")
    print("="*50)
    
    # Znajdź root path
    root_path = Path(__file__).parent.parent
    tests_dir = root_path / "tests"
    
    # Sprawdź czy test istnieje
    test_file = tests_dir / "test_phase4_integration.py"
    
    if not test_file.exists():
        print(f"❌ Test file nie znaleziony: {test_file}")
        return False
    
    print(f"📄 Znaleziono test: {test_file.name}")
    print(f"📁 W katalogu: {tests_dir}")
    print()
    
    # Opcje testowania
    print("🔧 DOSTĘPNE OPCJE:")
    print("1. 🚀 Szybki test (2 rundy)")
    print("2. 🏁 Pełny test (10 rund) - może trwać kilka minut")
    print("3. 🔍 Tylko analiza modułów (bez gry)")
    print()
    
    choice = input("Wybierz opcję (1-3) lub Enter dla opcji 1: ").strip()
    
    if not choice:
        choice = "1"
    
    # Przygotuj zmienne środowiskowe
    env = os.environ.copy()
    
    if choice == "1":
        print("🚀 Uruchamianie szybkiego testu Phase 4...")
        env['SKIP_FULL_TEST'] = 'true'
        
    elif choice == "2":
        print("🏁 Uruchamianie pełnego testu Phase 4...")
        env['SKIP_FULL_TEST'] = 'false'
        confirm = input("⚠️ Pełny test może trwać kilka minut. Kontynuować? (y/N): ")
        if confirm.lower() != 'y':
            print("⏹️ Test anulowany przez użytkownika")
            return False
            
    elif choice == "3":
        print("🔍 Uruchamianie tylko analizy modułów...")
        env['SKIP_FULL_TEST'] = 'true'
        env['ANALYSIS_ONLY'] = 'true'
        
    else:
        print("❌ Nieprawidłowy wybór")
        return False
    
    print()
    
    try:
        # Uruchom test
        result = subprocess.run([
            sys.executable, str(test_file)
        ],
        cwd=str(root_path),
        env=env
        )
        
        print("\n" + "="*50)
        
        if result.returncode == 0:
            print("✅ TESTY ZAKOŃCZONE SUKCESEM!")
            print("🎯 Phase 4 Advanced Logistics AI działa poprawnie")
        else:
            print("⚠️ TESTY ZAKOŃCZONE Z PROBLEMAMI")
            print(f"📊 Kod wyjścia: {result.returncode}")
            print("💡 Sprawdź logi powyżej dla szczegółów")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Błąd uruchamiania testów: {e}")
        return False
    
    finally:
        print("="*50)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
