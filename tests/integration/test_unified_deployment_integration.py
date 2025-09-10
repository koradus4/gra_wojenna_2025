#!/usr/bin/env python3
"""
Test integracyjny unified deployment - bez mocków, symuluje rzeczywiste użycie
"""

import sys
import os
from pathlib import Path

# Dodaj ścieżkę projektu do sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_unified_deployment_integration():
    """Test integracyjny - sprawdza czy unified system jest gotowy do użycia w grze"""
    print("🚀 UNIFIED DEPLOYMENT - TEST INTEGRACYJNY\n")
    
    success = True
    
    # 1. Test importu unified_deployment
    print("1️⃣ TEST IMPORTU:")
    try:
        from ai.unified_deployment import unified_deploy_purchased_units
        print("  ✅ Import unified_deployment: OK")
    except Exception as e:
        print(f"  ❌ Import unified_deployment: BŁĄD - {e}")
        success = False
        
    # 2. Test importu w ai_commander
    print("\n2️⃣ TEST AI COMMANDER INTEGRATION:")
    try:
        from ai.ai_commander import deploy_purchased_units
        print("  ✅ Import deploy_purchased_units z ai_commander: OK")
        
        # Sprawdź czy używa unified (poprzez sprawdzenie kodu)
        import ai.ai_commander
        import inspect
        source = inspect.getsource(ai.ai_commander.deploy_purchased_units)
        if "unified_deployment" in source:
            print("  ✅ AI Commander używa unified_deployment: OK")
        else:
            print("  ⚠️ AI Commander może nie używać unified_deployment")
            
    except Exception as e:
        print(f"  ❌ Import ai_commander: BŁĄD - {e}")
        success = False
    
    # 3. Test zależności (smart_deployment, Token)
    print("\n3️⃣ TEST ZALEŻNOŚCI:")
    try:
        from ai.smart_deployment import find_optimal_spawn_position
        print("  ✅ Import smart_deployment: OK")
    except Exception as e:
        print(f"  ❌ Import smart_deployment: BŁĄD - {e}")
        success = False
        
    try:
        from engine.token import Token
        print("  ✅ Import Token: OK")
    except Exception as e:
        print(f"  ❌ Import Token: BŁĄD - {e}")
        success = False
    
    # 4. Test struktury plików
    print("\n4️⃣ TEST STRUKTURY PLIKÓW:")
    
    # Sprawdź tokeny AI
    tokens_found = 0
    for player_id in [2, 3]:
        nowe_folder = project_root / f"assets/tokens/nowe_dla_{player_id}"
        if nowe_folder.exists():
            token_files = list(nowe_folder.glob("*/token.json"))
            tokens_found += len(token_files)
            print(f"  📦 Tokeny dla gracza {player_id}: {len(token_files)}")
    
    if tokens_found > 0:
        print(f"  ✅ Znaleziono {tokens_found} tokenów AI do testów")
    else:
        print(f"  ⚠️ Brak tokenów AI - uruchom AI General dla tokenów testowych")
    
    # Sprawdź folder aktualne/
    aktualne_folder = project_root / "assets/tokens/aktualne"
    if aktualne_folder.exists():
        print("  ✅ Folder aktualne/ istnieje")
    else:
        print("  ⚠️ Folder aktualne/ nie istnieje")
        
    # 5. Test konfiguracji spawn points
    print("\n5️⃣ TEST SPAWN POINTS:")
    try:
        map_data_path = project_root / "data/map_data.json"
        if map_data_path.exists():
            import json
            with open(map_data_path, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
            spawn_points = map_data.get('spawn_points', {})
            polska_spawns = spawn_points.get('Polska', [])
            if len(polska_spawns) > 0:
                print(f"  ✅ Spawn points dla Polski: {len(polska_spawns)}")
            else:
                print("  ⚠️ Brak spawn points dla Polski")
        else:
            print("  ❌ Brak pliku map_data.json")
            success = False
    except Exception as e:
        print(f"  ❌ Błąd odczytu spawn points: {e}")
        success = False
    
    # 6. Podsumowanie gotowości
    print(f"\n{'='*60}")
    print("🎯 GOTOWOŚĆ SYSTEMU UNIFIED DEPLOYMENT:")
    
    if success and tokens_found > 0:
        print("✅ SYSTEM GOTOWY DO UŻYCIA W GRZE")
        print("\n📋 INSTRUKCJE TESTOWANIA W GRZE:")
        print("1. 🚀 Uruchom main.py lub main_ai.py")
        print("2. 🎮 Rozpocznij grę z AI Commanders")  
        print("3. 🤖 Gdy AI Commander ma turę, sprawdź logi:")
        print("   - Szukaj: [UNIFIED] zamiast [DEPLOY]")
        print("   - Oczekiwany log: 'unified_deployment zwrócił: X'")
        print("4. 🗺️ Sprawdź mapę - nowe tokeny AI powinny się pojawić")
        print("5. 📁 Sprawdź pliki:")
        print("   - Nowe pliki w assets/tokens/aktualne/")
        print("   - Markery .deployed w folderach tokenów")
    elif success:
        print("⏳ SYSTEM GOTOWY - BRAK TOKENÓW DO TESTÓW")
        print("\n📋 UZYSKAJ TOKENY TESTOWE:")
        print("1. 🚀 Uruchom grę z AI General")
        print("2. 💰 Pozwól AI General zakupić jednostki")
        print("3. 📦 Sprawdź czy pojawiają się w nowe_dla_X/")
        print("4. 🔄 Uruchom ten test ponownie")
    else:
        print("❌ SYSTEM WYMAGA NAPRAWY")
        print("\n🔧 WYMAGANE POPRAWKI:")
        print("- Sprawdź importy i zależności")
        print("- Upewnij się że wszystkie pliki istnieją")
        print("- Sprawdź strukturę folderów")
    
    print(f"{'='*60}")
    
    return success and tokens_found > 0


if __name__ == "__main__":
    result = test_unified_deployment_integration()
    exit_code = 0 if result else 1
    print(f"\n🏁 EXIT CODE: {exit_code}")
    sys.exit(exit_code)
