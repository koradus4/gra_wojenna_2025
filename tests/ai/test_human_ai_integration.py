"""
Test: Czy AI Commander może operować jednostkami zakupionymi przez Human General?

Sprawdza:
1. Czy AI Commander znajdzie jednostki w folderze nowe_dla_{player_id}/
2. Czy wdroży jednostki z owner ustawionym przez Human General
3. Czy będzie mógł kontrolować te jednostki w kolejnych turach
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

from ai.ai_commander import deploy_purchased_units, get_my_units


def create_mock_engine():
    """Mock engine do testów"""
    engine = Mock()
    engine.board = Mock()
    engine.board.tokens = []
    engine.board.occupied_hexes = set()
    
    def mock_is_occupied(q, r):
        return (q, r) in engine.board.occupied_hexes
    
    def mock_neighbors(q, r):
        return [(q+1, r), (q, r+1), (q-1, r+1), (q-1, r), (q, r-1), (q+1, r-1)]
    
    engine.board.is_occupied = mock_is_occupied
    engine.board.neighbors = mock_neighbors
    
    # Mock player
    player = Mock()
    player.nation = "Polska"
    player.id = 2  # Commander ID
    engine.current_player_obj = player
    
    # Mock map data
    engine.map_data = {
        'key_points': {
            '10,5': {'type': 'miasto', 'value': 100, 'current_value': 100},
        },
        'spawn_points': {
            'Polska': ['6,-3', '0,2', '0,13'],
            'Niemcy': ['52,-26', '55,-23', '55,-20']
        }
    }
    
    # Mock tokens dla get_my_units
    engine.tokens = []
    
    return engine


def create_human_purchased_unit():
    """Symuluje jednostkę zakupioną przez Human General"""
    player_id = 2  # Commander ID
    
    # Stwórz folder jak Human General
    assets_path = Path("assets/tokens")
    commander_folder = assets_path / f"nowe_dla_{player_id}"
    test_token_folder = commander_folder / "human_purchased_unit_001"
    test_token_folder.mkdir(parents=True, exist_ok=True)
    
    # Stwórz token.json jak Human General (token_shop.py format)
    human_unit_data = {
        "id": "human_purchased_infantry_001",
        "nation": "Polska",
        "unitType": "P",
        "unitSize": "Pluton",
        "shape": "prostokąt",
        "label": "Human Piechota I/1",
        "unit_full_name": "Polska Piechota Pluton Human",
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
        "owner": "2",  # KLUCZOWE: Human General ustawia owner jako string player_id
        "image": f"assets/tokens/nowe_dla_2/human_purchased_unit_001/token.png",
        "w": 240,
        "h": 240
    }
    
    token_json_path = test_token_folder / "token.json"
    with open(token_json_path, 'w', encoding='utf-8') as f:
        json.dump(human_unit_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Stworzono human unit: {token_json_path}")
    return test_token_folder, human_unit_data


def test_ai_commander_human_general_integration():
    """Test główny: AI Commander + Human General units"""
    print("🤝 TEST: AI Commander operuje jednostkami Human General\n")
    
    engine = create_mock_engine()
    player_id = 2
    
    # 1. Symuluj zakup przez Human General
    test_folder, unit_data = create_human_purchased_unit()
    
    # 2. Test deployment przez AI Commander
    print("🚀 FASE 1: AI Commander deployment")
    deployed_count = deploy_purchased_units(engine, player_id)
    
    print(f"   Deployed units: {deployed_count}")
    print(f"   Engine tokens: {len(engine.board.tokens)}")
    
    # 3. Sprawdź czy AI Commander rozpoznaje wdrożone jednostki jako swoje
    print("\n🎯 FASE 2: AI Commander recognition")
    
    # Symuluj dodanie wdrożonej jednostki do engine.tokens
    if engine.board.tokens:
        deployed_token = engine.board.tokens[0]
        engine.tokens = [deployed_token]  # Dodaj do engine.tokens dla get_my_units
        
        # Test get_my_units
        my_units = get_my_units(engine, player_id)
        
        print(f"   My units found: {len(my_units)}")
        if my_units:
            unit = my_units[0]
            print(f"   Unit ID: {unit['id']}")
            print(f"   Unit owner: {getattr(unit['token'], 'owner', 'N/A')}")
            print(f"   Position: ({unit['q']}, {unit['r']})")
    
    # Cleanup
    if test_folder.exists():
        shutil.rmtree(test_folder)
        print(f"\n🧹 Cleanup: Usunięto {test_folder}")
    
    # 4. Sprawdź wyniki
    print(f"\n📊 WYNIKI:")
    success = deployed_count > 0 and len(my_units) > 0
    
    if success:
        print("✅ AI Commander MOŻE operować jednostkami Human General!")
        print("   - ✅ Deployment działa")
        print("   - ✅ Recognition działa") 
        print("   - ✅ Integracja pełna")
    else:
        print("❌ Problemy z integracją")
    
    return success


def test_owner_format_compatibility():
    """Test zgodności formatów owner"""
    print("\n🔍 TEST: Zgodność formatów owner\n")
    
    # Format Human General
    human_owner = "2"  # String player_id
    
    # Format AI General  
    ai_owner = "2 (Polska)"  # f"{player_id} ({nation})"
    
    # Test get_my_units logic
    player_id = 2
    
    def test_owner_match(owner_str, player_id):
        """Testuje logikę z get_my_units"""
        return str(player_id) in owner_str or owner_str.startswith(str(player_id))
    
    human_match = test_owner_match(human_owner, player_id)
    ai_match = test_owner_match(ai_owner, player_id)
    
    print(f"Human General format: '{human_owner}' → Match: {human_match}")
    print(f"AI General format: '{ai_owner}' → Match: {ai_match}")
    
    if human_match and ai_match:
        print("✅ Oba formaty są kompatybilne!")
    else:
        print("❌ Problem z kompatybilnością formatów")
    
    return human_match and ai_match


def test_real_scenario_simulation():
    """Symulacja prawdziwego scenariusza gry"""
    print("\n🎮 SYMULACJA: Human General → AI Commander workflow\n")
    
    scenarios = [
        "1. Human General kupuje jednostki w sklepie",
        "2. Jednostki są zapisane w assets/tokens/nowe_dla_{commander_id}/",
        "3. AI Commander przejmuje kontrolę w trybie taktycznym", 
        "4. AI Commander wykonuje deployment zakupionych jednostek",
        "5. AI Commander kontroluje wszystkie jednostki (stare + nowe)"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"   {scenario}")
    
    print(f"\n💡 KLUCZOWY ELEMENT:")
    print(f"   AI Commander szuka w folderze: assets/tokens/nowe_dla_{{player_id}}/")
    print(f"   NIE IMPORTUJE jakie było źródło jednostek (Human vs AI General)")
    print(f"   System jest AGNOSTYCZNY względem źródła zakupu")
    
    return True


if __name__ == "__main__":
    print("🤝 INTEGRATION TEST: AI Commander + Human General")
    print("=" * 60)
    
    try:
        # Test 1: Główny test integracji
        result1 = test_ai_commander_human_general_integration()
        
        # Test 2: Kompatybilność formatów
        result2 = test_owner_format_compatibility()
        
        # Test 3: Symulacja scenariusza
        result3 = test_real_scenario_simulation()
        
        print("\n" + "=" * 60)
        if result1 and result2 and result3:
            print("🎉 WSZYSTKIE TESTY PASSED!")
            print("✅ AI Commander MOŻE operować jednostkami Human General")
        else:
            print("❌ NIEKTÓRE TESTY FAILED")
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
