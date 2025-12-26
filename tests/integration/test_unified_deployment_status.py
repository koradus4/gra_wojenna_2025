#!/usr/bin/env python3
"""
Prosty test statusu unified deployment - bez mocków, tylko sprawdzanie stanu plików
"""

import sys
import json
from pathlib import Path

# Dodaj ścieżkę projektu do sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def check_unified_deployment_status():
    """Sprawdza status tokenów AI dla unified deployment systemu"""
    print("🚀 UNIFIED DEPLOYMENT - STATUS CHECK\n")
    
    total_tokens = 0
    total_deployed = 0
    
    for player_id in [2, 3]:
        print(f"👤 GRACZ {player_id}:")
        
        # Sprawdź folder nowe_dla_X
        nowe_folder = project_root / f"assets/tokens/nowe_dla_{player_id}"
        if not nowe_folder.exists():
            print(f"  ❌ Brak foldera nowe_dla_{player_id}")
            continue
        
        token_files = list(nowe_folder.glob("*/token.json"))
        player_tokens = len(token_files)
        total_tokens += player_tokens
        
        print(f"  📦 Tokeny: {player_tokens}")
        
        deployed_count = 0
        for token_file in token_files:
            folder_name = token_file.parent.name
            if len(folder_name) > 60:
                display_name = folder_name[:57] + "..."
            else:
                display_name = folder_name
                
            # Sprawdź marker .deployed
            marker = token_file.parent / '.deployed'
            if marker.exists():
                status = "✅ Wdrożony"
                deployed_count += 1
            else:
                status = "⏳ Do wdrożenia"
            
            print(f"    📄 {display_name}")
            print(f"       Status: {status}")
            
            # Sprawdź dane tokena
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                label = data.get('label', 'NO_LABEL')
                nation = data.get('nation', 'NO_NATION')
                print(f"       🎯 {label}")
                print(f"       🏳️ {nation}")
            except Exception as e:
                print(f"       ❌ Błąd odczytu JSON: {e}")
        
        total_deployed += deployed_count
        print(f"  📊 Status: {deployed_count}/{player_tokens} wdrożonych\n")
    
    # Sprawdź pliki w aktualne/
    aktualne_path = project_root / "assets/tokens/aktualne" 
    unified_files_count = 0
    if aktualne_path.exists():
        unified_files = list(aktualne_path.glob("nowy_*"))
        unified_files_count = len(unified_files)
        print(f"📂 AKTUALNE/ - Pliki unified: {unified_files_count}")
        
        # Pokaż kilka przykładów
        for i, file in enumerate(unified_files[:3]):
            extension = file.suffix
            name = file.name
            if len(name) > 60:
                display_name = name[:57] + "..."
            else:
                display_name = name
            print(f"  📄 {display_name}")
    
    print(f"\n{'='*60}")
    print("🎯 PODSUMOWANIE UNIFIED DEPLOYMENT:")
    print(f"📦 Łączna liczba tokenów AI: {total_tokens}")
    print(f"✅ Tokeny już wdrożone: {total_deployed}")
    print(f"⏳ Tokeny do wdrożenia: {total_tokens - total_deployed}")
    print(f"📂 Pliki w aktualne/: {unified_files_count}")
    
    if total_tokens == 0:
        status = "❌ BRAK TOKENÓW DO TESTÓW"
    elif total_deployed == total_tokens:
        status = "✅ WSZYSTKIE WDROŻONE"
    else:
        status = "⏳ GOTOWE DO TESTÓW"
    
    print(f"🔧 Status systemu: {status}")
    print(f"{'='*60}")
    
    return {
        'total_tokens': total_tokens,
        'deployed_tokens': total_deployed,
        'pending_tokens': total_tokens - total_deployed,
        'aktualne_files': unified_files_count,
        'ready_for_test': total_tokens > total_deployed
    }


if __name__ == "__main__":
    result = check_unified_deployment_status()
    
    print("\n📋 NASTĘPNE KROKI:")
    if result['ready_for_test']:
        print("1. 🚀 Uruchom grę")  
        print("2. 🤖 Rozpocznij turę AI Commander")
        print("3. 👀 Sprawdź logi - szukaj [UNIFIED] zamiast [DEPLOY]")
        print("4. 🗺️ Verify - tokeny powinny pojawić się na mapie")
        print("5. 📁 Check - pliki w aktualne/ + markery .deployed")
    elif result['total_tokens'] == 0:
        print("1. 🛠️ Uruchom AI General żeby zakupił tokeny")
        print("2. 📦 Sprawdź czy pojawiają się w nowe_dla_X/")
        print("3. 🔄 Uruchom ten test ponownie")
    else:
        print("1. ✅ Wszystkie tokeny już wdrożone")
        print("2. 🧹 Usuń markery .deployed żeby przetestować ponownie")
        print("3. 🔄 Lub uruchom AI General dla nowych tokenów")
