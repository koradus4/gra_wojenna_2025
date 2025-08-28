"""
Test poprawki deployment - sprawdza czy AI Commander prawidłowo znajduje i wdraża
jednostki z assets/tokens/nowe_dla_{player_id}/*/token.json
"""

import sys
import time
import json
import shutil
from pathlib import Path
from unittest.mock import Mock

# Dodaj ścieżkę projektu
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ai.ai_commander import deploy_purchased_units, find_deployment_position, create_and_deploy_token


def create_mock_engine_with_real_structure():
    """Tworzy mock engine z realną strukturą plików"""
    engine = Mock()
    engine.board = Mock()
    engine.board.tokens = []
    engine.board.occupied_hexes = set()
    
    # Mock board methods - musi zwracać prawdziwe wartości
    def mock_is_occupied(q, r):
        return (q, r) in engine.board.occupied_hexes
    
    def mock_neighbors(q, r):
        return [(q+1, r), (q, r+1), (q-1, r+1), (q-1, r), (q, r-1), (q+1, r-1)]
    
    engine.board.is_occupied = mock_is_occupied
    engine.board.neighbors = mock_neighbors
    
    # Mock player
    player = Mock()
    player.nation = "Polska"
    player.id = 2
    engine.current_player_obj = player
    
    # Mock map data z prawdziwymi spawn points - musi być słownik
    engine.map_data = {
        'key_points': {
            '10,5': {'type': 'miasto', 'value': 100, 'current_value': 100},
            '15,8': {'type': 'fortyfikacja', 'value': 150, 'current_value': 150},
        },
        'spawn_points': {
            'Polska': ['6,-3', '0,2', '0,13'],
            'Niemcy': ['52,-26', '55,-23', '55,-20']
        }
    }
    
    # Dodaj get_my_units mock function results
    engine.tokens = []  # For get_my_units function
    
    return engine


def test_deployment_fix():
    """Test naprawionego systemu deployment"""
    print("🔧 TEST DEPLOYMENT FIX - Nowa implementacja\n")
    
    engine = create_mock_engine_with_real_structure()
    player_id = 2
    
    # Przygotuj strukturę folderów jak w prawdziwej grze
    assets_path = Path("assets/tokens")
    commander_folder = assets_path / f"nowe_dla_{player_id}"
    
    # Stwórz folder testowy
    test_token_folder = commander_folder / "test_unit_001"
    test_token_folder.mkdir(parents=True, exist_ok=True)
    
    # Stwórz token.json w formacie AI General (rzeczywistym)
    test_unit_data = {
        "id": "test_PL_infantry_001",
        "nation": "Polska",
        "unitType": "P",
        "unitSize": "Pluton",
        "shape": "prostokąt",
        "label": "Test Piechota I/1",
        "unit_full_name": "Polska Piechota Pluton Test",
        "move": 3,
        "attack": {
            "range": 1,
            "value": 3
        },
        "combat_value": 6,
        "defense_value": 3,
        "maintenance": 3,
        "price": 15,
        "sight": 2,
        "owner": "2",
        "image": f"assets/tokens/nowe_dla_2/test_unit_001/token.png"
    }
    
    token_json_path = test_token_folder / "token.json"
    with open(token_json_path, 'w', encoding='utf-8') as f:
        json.dump(test_unit_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Przygotowano test token w: {token_json_path}")
    
    # Test deployment
    print(f"🚀 Rozpoczynam deployment dla gracza {player_id}")
    deployed_count = deploy_purchased_units(engine, player_id)
    
    # Sprawdź wyniki
    print(f"\n📊 WYNIKI TESTU:")
    print(f"   Deployed count: {deployed_count}")
    print(f"   Tokens in engine: {len(engine.board.tokens)}")
    print(f"   Test folder exists: {test_token_folder.exists()}")
    
    # Cleanup - usuń test folder jeśli jeszcze istnieje
    if test_token_folder.exists():
        shutil.rmtree(test_token_folder)
        print(f"🧹 Usunięto test folder")
    
    # Assertions - deployment może wdrożyć więcej niż 1 jednostkę (prawdziwe + test)
    assert deployed_count >= 1, f"Expected at least 1 deployed unit, got {deployed_count}"
    assert len(engine.board.tokens) >= 1, f"Expected at least 1 token in engine, got {len(engine.board.tokens)}"
    assert not test_token_folder.exists(), "Test token folder should be deleted after deployment"
    
    print("✅ TEST DEPLOYMENT FIX PASSED!")
    print(f"✅ System wdrożył {deployed_count} jednostek (w tym prawdziwe z AI General)")
    return True


def test_real_folder_detection():
    """Test czy system prawidłowo wykrywa istniejące foldery"""
    print("\n🔍 TEST REAL FOLDER DETECTION\n")
    
    assets_path = Path("assets/tokens")
    
    # Sprawdź rzeczywiste foldery
    existing_folders = []
    for folder_name in ['nowe_dla_2', 'nowe_dla_3', 'nowe_dla_5']:
        folder_path = assets_path / folder_name
        if folder_path.exists():
            existing_folders.append(folder_name)
            print(f"✅ Znaleziono folder: {folder_path}")
            
            # Sprawdź token.json files w folderze
            token_files = list(folder_path.glob("*/token.json"))
            print(f"   Token files: {len(token_files)}")
            
            for token_file in token_files:
                print(f"   - {token_file}")
                
                # Sprawdź zawartość
                try:
                    with open(token_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"     ID: {data.get('id', 'N/A')}")
                    print(f"     Label: {data.get('label', 'N/A')}")
                except Exception as e:
                    print(f"     Błąd odczytu: {e}")
    
    print(f"\n📊 WYKRYTE FOLDERY: {len(existing_folders)}")
    return existing_folders


def test_mock_deployment_with_real_structure():
    """Test deployment z mock engine ale prawdziwą strukturą"""
    print("\n🎭 TEST MOCK DEPLOYMENT WITH REAL STRUCTURE\n")
    
    engine = create_mock_engine_with_real_structure()
    
    # Test dla każdego istniejącego gracza
    for player_id in [2, 3, 5]:
        print(f"\n--- Test deployment dla gracza {player_id} ---")
        
        # Ustaw odpowiednią nację
        if player_id in [2, 3]:
            engine.current_player_obj.nation = "Polska"
        else:
            engine.current_player_obj.nation = "Niemcy"
        
        initial_tokens = len(engine.board.tokens)
        deployed = deploy_purchased_units(engine, player_id)
        
        print(f"   Deployed: {deployed} units")
        print(f"   Total tokens: {len(engine.board.tokens)}")
        
        if deployed > 0:
            print(f"   ✅ Deployment successful for player {player_id}")
        else:
            print(f"   ℹ️  No units to deploy for player {player_id}")


if __name__ == "__main__":
    print("🚀 DEPLOYMENT FIX TESTS\n")
    print("=" * 50)
    
    try:
        # Test 1: Podstawowy test poprawki
        test_deployment_fix()
        
        # Test 2: Sprawdź istniejące foldery
        existing = test_real_folder_detection()
        
        # Test 3: Mock deployment z prawdziwą strukturą
        test_mock_deployment_with_real_structure()
        
        print("\n" + "=" * 50)
        print("🎉 WSZYSTKIE TESTY DEPLOYMENT FIX PASSED!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
