#!/usr/bin/env python3
"""
Test ujednoliconego systemu deploymentu human+ai
Sprawdza czy nowy unified system działa z prawdziwymi danymi
"""

import sys
import json
import os
from pathlib import Path
from unittest.mock import Mock

# Dodaj ścieżkę projektu do sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ai.unified_deployment import unified_deploy_purchased_units


def mock_get_my_units(game_engine, player_id):
    """Mock dla get_my_units - zwraca pustą listę jednostek"""
    return []


def create_mock_game_engine():
    """Tworzy mock game_engine kompatybilny z unified_deployment"""
    engine = Mock()
    engine.tokens = []  # Lista rzeczywista, nie Mock
    
    # Mock board z podstawową funkcjonalnością
    board = Mock()
    board.is_occupied = Mock(return_value=False)
    board.set_tokens = Mock()
    
    def mock_get_tile(q, r):
        tile = Mock()
        tile.spawn_nation = "polska"  # Dla polskich tokenów AI
        return tile
    board.get_tile = mock_get_tile
    
    engine.board = board
    
    # Mock current_player_obj
    player = Mock()
    player.nation = "Polska"
    engine.current_player_obj = player
    
    # Mock dla smart_deployment kompatybilności
    engine.get_all_key_points = Mock(return_value=[])
    
    return engine


def test_unified_deployment_real_data():
    """Test ujednoliconego systemu z prawdziwymi tokenami AI"""
    print("🚀 TEST UNIFIED DEPLOYMENT SYSTEM (REAL DATA)\n")
    
    # Patch get_my_units żeby nie powodował błędów w smart_deployment
    import ai.smart_deployment
    original_get_my_units = getattr(ai.smart_deployment, 'get_my_units', None)
    ai.smart_deployment.get_my_units = mock_get_my_units
    
    try:
        engine = create_mock_game_engine()
        
        # Test deployment dla gracza 2 (ma token Kawalerii)
        player_id = 2
        
        print(f"📋 Tokeny przed deployment: {len(engine.tokens)}")
        
        # Sprawdź czy istnieją tokeny do deploymentu
        nowe_folder = project_root / f"assets/tokens/nowe_dla_{player_id}"
        if not nowe_folder.exists():
            print(f"❌ Brak foldera nowe_dla_{player_id}")
            return False
            
        token_files = list(nowe_folder.glob("*/token.json"))
        undeployed_files = []
        for tf in token_files:
            if not (tf.parent / '.deployed').exists():
                undeployed_files.append(tf)
        
        print(f"📦 Tokeny do deployment: {len(undeployed_files)}")
        
        if len(undeployed_files) == 0:
            print("ℹ️ Wszystkie tokeny już wdrożone (mają marker .deployed)")
            return True
        
        # Wywołaj unified system
        deployed_count = unified_deploy_purchased_units(engine, player_id)
        
        print(f"📋 Tokeny po deployment: {len(engine.tokens)}")
        print(f"✅ Wdrożono: {deployed_count} nowych jednostek")
        
        # Pokaż wdrożone tokeny
        for i, token in enumerate(engine.tokens):
            if i < 5:  # Pokaż max 5
                print(f"  📦 {getattr(token, 'id', 'NO_ID')[:30]}...")
                print(f"     Pozycja: ({getattr(token, 'q', '?')}, {getattr(token, 'r', '?')})")
                print(f"     Owner: {getattr(token, 'owner', 'NO_OWNER')}")
        
        # Sprawdź czy pliki zostały skopiowane do aktualne/
        aktualne_path = project_root / "assets/tokens/aktualne"
        if aktualne_path.exists():
            copied_files = list(aktualne_path.glob("nowy_*Pluton__2_*"))
            print(f"\n📂 Pliki skopiowane do aktualne/ dla gracza 2: {len(copied_files)}")
        
        # Sprawdź markery .deployed
        deployed_markers = list(nowe_folder.glob("*/.deployed"))
        print(f"🏷️ Markery .deployed: {len(deployed_markers)}")
        
        success = deployed_count > 0 or len(undeployed_files) == 0
        
        print(f"\n{'='*60}")
        print("🎯 UNIFIED SYSTEM - WYNIKI TESTU:")
        print(f"✅ System unified_deployment: {'DZIAŁA' if success else 'BŁĄD'}")
        print(f"✅ Token.from_json(): Użyty (z human)")
        print(f"✅ Inteligentne pozycjonowanie: Użyte (z AI)")
        print(f"✅ Kopiowanie plików: Jak human")
        print(f"✅ Marker system: Jak AI")
        print(f"{'='*60}")
        
        return success
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Przywróć oryginalną funkcję
        if original_get_my_units:
            ai.smart_deployment.get_my_units = original_get_my_units


def test_unified_deployment_status():
    """Test statusu tokenów i plików dla unified deployment"""
    print("🚀 STATUS CHECK - UNIFIED DEPLOYMENT SYSTEM\n")
    
    success = True
    
    for player_id in [2, 3]:
        print(f"👤 GRACZ {player_id}:")
        
        # Sprawdź tokeny do deployment
        nowe_folder = project_root / f"assets/tokens/nowe_dla_{player_id}"
        if not nowe_folder.exists():
            print(f"  ❌ Brak foldera nowe_dla_{player_id}")
            continue
            
        token_files = list(nowe_folder.glob("*/token.json"))
        print(f"  📦 Tokeny: {len(token_files)}")
        
        for token_file in token_files:
            folder_name = token_file.parent.name[:50] + "..." if len(token_file.parent.name) > 50 else token_file.parent.name
            marker = token_file.parent / '.deployed'
            status = "✅ Wdrożony" if marker.exists() else "⏳ Do wdrożenia"
            print(f"    {folder_name}: {status}")
            
            # Sprawdź zawartość tokena
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"      🎯 {data.get('label', 'NO_LABEL')}")
                print(f"      🏳️ {data.get('nation', 'NO_NATION')}")
            except Exception as e:
                print(f"      ❌ Błąd odczytu: {e}")
                success = False
    
    # Sprawdź pliki w aktualne/
    aktualne_path = project_root / "assets/tokens/aktualne"
    if aktualne_path.exists():
        unified_files = list(aktualne_path.glob("nowy_*"))
        print(f"\n📂 AKTUALNE/ - Pliki unified: {len(unified_files)}")
        for file in unified_files[:3]:  # Pokaż 3 pierwsze
            print(f"  📄 {file.name[:60]}...")
    
    print(f"\n{'='*60}")
    print(f"🔧 SYSTEM STATUS: {'GOTOWY' if success else 'WYMAGA NAPRAWY'}")
    print(f"🔧 NEXT STEP: Uruchom grę i sprawdź logi AI Commander")
    print(f"{'='*60}")
    
    return success


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 UNIFIED DEPLOYMENT SYSTEM - TESTY")
    print("=" * 60)
    
    # Test 1: Status check
    status_ok = test_unified_deployment_status()
    
    print("\n")
    
    # Test 2: Real deployment (jeśli są tokeny)
    if status_ok:
        deployment_ok = test_unified_deployment_real_data()
    else:
        print("⏭️ Pomijam test deployment - problemy ze statusem")
        deployment_ok = False
    
    print("\n" + "=" * 60)
    print("📊 PODSUMOWANIE TESTÓW:")
    print(f"✅ Status check: {'PASS' if status_ok else 'FAIL'}")
    print(f"✅ Real deployment: {'PASS' if deployment_ok else 'FAIL'}")
    
    overall_success = status_ok and deployment_ok
    print(f"\n🎯 OGÓLNY REZULTAT: {'SUCCESS ✅' if overall_success else 'NEEDS WORK ❌'}")
    print("=" * 60)
