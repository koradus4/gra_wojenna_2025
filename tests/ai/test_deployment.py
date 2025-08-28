#!/usr/bin/env python3
"""
Test deployment zakupionych jednostek
"""

import sys
import json
from pathlib import Path

# Dodaj ścieżkę projektu do sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ai.ai_commander import deploy_purchased_units


def create_mock_engine_for_deployment():
    """Tworzy mock game_engine do testów deployment"""
    
    # Mock board
    class MockBoard:
        def __init__(self):
            self.tokens = []
            self.occupied_hexes = set()
        
        def is_occupied(self, q, r):
            return (q, r) in self.occupied_hexes
        
        def neighbors(self, q, r):
            """Zwraca sąsiadujące hexagony"""
            return [
                (q + 1, r), (q - 1, r),
                (q, r + 1), (q, r - 1),
                (q + 1, r - 1), (q - 1, r + 1)
            ]
    
    # Mock player
    class MockPlayer:
        def __init__(self, nation, player_id):
            self.nation = nation
            self.id = player_id
    
    # Utwórz engine
    engine = type('MockEngine', (), {})()
    engine.board = MockBoard()
    engine.current_player_obj = MockPlayer("Polska", 2)
    engine.tokens = []
    
    # Dane mapy z punktami spawn
    engine.map_data = {
        'key_points': {
            '10,5': {'type': 'miasto', 'value': 100},
            '15,8': {'type': 'fortyfikacja', 'value': 150},
        },
        'spawn_points': {
            'Polska': ['6,-3', '0,2', '0,13'],  # Spawn points dla Polski
            'Niemcy': ['52,-26', '55,-23', '55,-20']
        }
    }
    
    return engine


def test_deployment():
    """Test wdrażania zakupionych jednostek"""
    print("🚀 TEST DEPLOYMENT ZAKUPIONYCH JEDNOSTEK\n")
    
    engine = create_mock_engine_for_deployment()
    
    # Stwórz plik z zakupionymi jednostkami
    test_file = "nowe_dla_polska_test.json"
    purchased_units = [
        {
            "id": "nowe_PL_001",
            "label": "Piechota I/1",
            "stats": {
                "unit_type": "P",
                "size": "Pluton",
                "combat_value": 6,
                "maintenance": 3,
                "movement": 3,
                "label": "Piechota I/1"
            }
        },
        {
            "id": "nowe_PL_002", 
            "label": "Artyleria AL/1",
            "stats": {
                "unit_type": "AL",
                "size": "Pluton",
                "combat_value": 8,
                "maintenance": 4,
                "movement": 2,
                "label": "Artyleria AL/1"
            }
        }
    ]
    
    # Zapisz plik testowy
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(purchased_units, f, indent=2, ensure_ascii=False)
    
    print(f"Stworzono plik testowy: {test_file}")
    print(f"Zawiera {len(purchased_units)} jednostek do wdrożenia")
    
    # Wykonaj deployment
    deployed_count = deploy_purchased_units(engine, 2)
    
    print(f"\n✅ Wdrożono {deployed_count} jednostek")
    print(f"Żetony na planszy: {len(engine.board.tokens)}")
    
    # Pokaż pozycje wdrożonych jednostek
    for token in engine.board.tokens:
        print(f"  {token.id}: pozycja ({token.q}, {token.r})")
    
    # Sprawdź czy plik został usunięty
    import os
    if not os.path.exists(test_file):
        print(f"✅ Plik {test_file} został poprawnie usunięty po deployment")
    else:
        print(f"⚠️ Plik {test_file} nadal istnieje")


if __name__ == "__main__":
    test_deployment()
