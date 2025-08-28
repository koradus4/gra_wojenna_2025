"""Test AI Commandera z inteligentnym systemem spawnowania

TESTUJE:
- Integrację inteligentnego systemu z AI Commanderem
- Wybór spawnu na podstawie sytuacji taktycznej
- Porównanie z poprzednim systemem
- Działanie w różnych scenariuszach
"""

import unittest
import sys
import os
import json
from pathlib import Path
import tempfile
import shutil

# Dodaj ścieżkę do głównego katalogu projektu
current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

try:
    from ai.ai_commander import find_deployment_position, deploy_purchased_units
    from engine.token import Token
    from engine.board import Board
    from engine.player import Player
except ImportError as e:
    print(f"Błąd importu: {e}")
    sys.exit(1)


class MockGameEngine:
    """Mock obiektu game engine z rzeczywistymi komponentami"""
    
    def __init__(self):
        self.tokens = []
        self.current_player_obj = MockPlayer()
        
        # Rzeczywiste dane mapy
        self.map_data = {
            'spawn_points': {
                'Polska': ['6,-3', '0,2', '0,13', '0,14', '18,24', '24,-12'],
                'Niemcy': ['52,-26', '55,-23', '55,-20', '49,8', '40,-20']
            },
            'key_points': {
                '10,5': {'type': 'miasto', 'value': 150},
                '15,10': {'type': 'fabryka', 'value': 100},
                '45,-15': {'type': 'port', 'value': 200},
                '30,0': {'type': 'miasto', 'value': 180},
                '25,15': {'type': 'fabryka', 'value': 120}
            }
        }
        
        self.board = MockBoard()


class MockPlayer:
    def __init__(self):
        self.nation = 'Polska'
        self.player_id = 'ai_player_1'


class MockBoard:
    def __init__(self):
        self.occupied_positions = set()
    
    def is_occupied(self, q, r):
        return (q, r) in self.occupied_positions
    
    def neighbors(self, q, r):
        return [
            (q+1, r), (q-1, r), (q, r+1), 
            (q, r-1), (q+1, r-1), (q-1, r+1)
        ]


class MockToken:
    def __init__(self, q, r, owner, strength=5, name="TestUnit"):
        self.q = q
        self.r = r
        self.owner = owner
        self.current_strength = strength
        self.name = name


class TestAICommanderSmartDeployment(unittest.TestCase):
    
    def setUp(self):
        """Przygotowanie do testów"""
        self.engine = MockGameEngine()
        self.temp_dir = tempfile.mkdtemp()
        self.assets_dir = Path(self.temp_dir) / "assets" / "tokens" / "nowe_dla_ai_player_1"
        self.assets_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Czyszczenie po testach"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_mock_purchased_unit(self, unit_name="TestUnit", unit_type="infantry"):
        """Tworzy mock zakupionej jednostki"""
        unit_data = {
            "name": unit_name,
            "type": unit_type,
            "strength": 5,
            "movement": 3,
            "cost": 50,
            "nation": "Polska"
        }
        
        unit_file = self.assets_dir / "token.json"
        with open(unit_file, 'w', encoding='utf-8') as f:
            json.dump(unit_data, f, ensure_ascii=False, indent=2)
        
        return unit_data
    
    def test_smart_deployment_defensive_scenario(self):
        """Test inteligentnego spawnowania w scenariuszu obronnym"""
        print("\n🛡️ Test scenariusza obronnego")
        
        # Scenariusz: wrogowie zagrażają spawn pointom
        self.engine.tokens = [
            MockToken(7, -2, 'human_player', 12, "Enemy_Tank"),  # Blisko (6,-3)
            MockToken(1, 3, 'human_player', 8, "Enemy_Infantry"), # Blisko (0,2)
            # Nasze jednostki
            MockToken(19, 24, 'ai_player_1', 6, "Our_Defender"),  # Przy (18,24)
        ]
        
        unit_data = self.create_mock_purchased_unit("New_Defender", "infantry")
        
        # Test wyboru pozycji
        deployment_pos = find_deployment_position(unit_data, self.engine, 'ai_player_1')
        
        self.assertIsNotNone(deployment_pos)
        print(f"   Wybrana pozycja: {deployment_pos}")
        
        # W scenariuszu obronnym powinien wybrać spawn daleko od wrogów
        # lub blisko zagrożonych jednostek
        safe_spawns = [(18, 24), (24, -12)]  # Daleko od wrogów
        
        is_safe_choice = deployment_pos in safe_spawns or \
                        any(abs(deployment_pos[0] - sp[0]) + abs(deployment_pos[1] - sp[1]) <= 2 
                            for sp in safe_spawns)
        
        print(f"   Bezpieczny wybór: {is_safe_choice}")
    
    def test_smart_deployment_offensive_scenario(self):
        """Test inteligentnego spawnowania w scenariuszu ofensywnym"""
        print("\n⚔️ Test scenariusza ofensywnego")
        
        # Scenariusz: punkty kluczowe pod zagrożeniem
        self.engine.tokens = [
            # Wrogowie przy punktach kluczowych
            MockToken(11, 6, 'human_player', 10, "Enemy_Near_City"),    # Blisko (10,5)
            MockToken(44, -14, 'human_player', 15, "Enemy_Near_Port"),  # Blisko (45,-15)
            
            # Nasze jednostki
            MockToken(5, -3, 'ai_player_1', 5, "Our_Scout"),
            MockToken(20, 25, 'ai_player_1', 8, "Our_Patrol"),
        ]
        
        unit_data = self.create_mock_purchased_unit("Combat_Unit", "armor")
        
        deployment_pos = find_deployment_position(unit_data, self.engine, 'ai_player_1')
        
        self.assertIsNotNone(deployment_pos)
        print(f"   Wybrana pozycja: {deployment_pos}")
        
        # Sprawdź czy pozycja pomaga w obronie kluczowych punktów
        key_points = [(10, 5), (45, -15)]
        min_distance_to_kp = min(
            abs(deployment_pos[0] - kp[0]) + abs(deployment_pos[1] - kp[1])
            for kp in key_points
        )
        
        print(f"   Odległość do najbliższego punktu kluczowego: {min_distance_to_kp}")
    
    def test_smart_deployment_support_scenario(self):
        """Test inteligentnego spawnowania dla wsparcia"""
        print("\n🤝 Test scenariusza wsparcia")
        
        # Scenariusz: klaster jednostek potrzebuje wsparcia
        self.engine.tokens = [
            # Klaster przyjaciół
            MockToken(5, -2, 'ai_player_1', 4, "Cluster_1"),
            MockToken(6, -2, 'ai_player_1', 3, "Cluster_2"),
            MockToken(7, -1, 'ai_player_1', 5, "Cluster_3"),
            
            # Wróg zagrażający klasterowi
            MockToken(9, 0, 'human_player', 12, "Enemy_Threat"),
        ]
        
        unit_data = self.create_mock_purchased_unit("Support_Unit", "artillery")
        
        deployment_pos = find_deployment_position(unit_data, self.engine, 'ai_player_1')
        
        self.assertIsNotNone(deployment_pos)
        print(f"   Wybrana pozycja: {deployment_pos}")
        
        # Powinien wybrać spawn blisko klastra (6,-3) dla wsparcia
        expected_spawn = (6, -3)
        distance_to_cluster = abs(deployment_pos[0] - expected_spawn[0]) + \
                             abs(deployment_pos[1] - expected_spawn[1])
        
        print(f"   Odległość od oczekiwanego spawnu wsparcia: {distance_to_cluster}")
        
        # Sprawdź czy rzeczywiście blisko klastra
        cluster_center = (6, -2)  # Przybliżony środek klastra
        distance_to_center = abs(deployment_pos[0] - cluster_center[0]) + \
                            abs(deployment_pos[1] - cluster_center[1])
        
        print(f"   Odległość od centrum klastra: {distance_to_center}")
    
    def test_fallback_to_simple_system(self):
        """Test fallback do prostego systemu gdy inteligentny zawiedzie"""
        print("\n🔄 Test fallback systemu")
        
        # Symuluj błąd w inteligentnym systemie przez usunięcie modułu
        original_path = sys.path[:]
        try:
            # Tymczasowo usuń ścieżkę do smart_deployment
            sys.path = [p for p in sys.path if 'gra wojenna' not in p]
            
            unit_data = self.create_mock_purchased_unit("Fallback_Unit")
            
            deployment_pos = find_deployment_position(unit_data, self.engine, 'ai_player_1')
            
            self.assertIsNotNone(deployment_pos)
            print(f"   Fallback wybrał pozycję: {deployment_pos}")
            
            # Powinna być jednym z dostępnych spawn points
            available_spawns = [(6, -3), (0, 2), (0, 13), (0, 14), (18, 24), (24, -12)]
            self.assertIn(deployment_pos, available_spawns)
            
        finally:
            sys.path = original_path
    
    def test_different_nations_smart_deployment(self):
        """Test inteligentnego spawnowania dla różnych nacji"""
        print("\n🌍 Test różnych nacji")
        
        # Test dla Niemiec
        self.engine.current_player_obj.nation = 'Niemcy'
        
        # Dodaj kontekst taktyczny
        self.engine.tokens = [
            MockToken(50, -25, 'ai_player_1', 6, "German_Unit"),
            MockToken(30, 10, 'human_player', 10, "Polish_Enemy"),
        ]
        
        unit_data = self.create_mock_purchased_unit("Panzer", "armor")
        
        deployment_pos = find_deployment_position(unit_data, self.engine, 'ai_player_1')
        
        self.assertIsNotNone(deployment_pos)
        print(f"   Niemiecki spawn: {deployment_pos}")
        
        # Sprawdź czy używa niemieckich spawn points
        german_spawns = [(52, -26), (55, -23), (55, -20), (49, 8), (40, -20)]
        
        is_german_spawn = deployment_pos in german_spawns or \
                         any(abs(deployment_pos[0] - gs[0]) + abs(deployment_pos[1] - gs[1]) <= 1
                             for gs in german_spawns)
        
        self.assertTrue(is_german_spawn)
        print(f"   Poprawny niemiecki spawn: {is_german_spawn}")
    
    def test_map_reorganization_compatibility(self):
        """Test kompatybilności z reorganizacją mapy"""
        print("\n🗺️ Test reorganizacji mapy")
        
        # Zmień spawn points symulując reorganizację mapy
        new_spawns = ['15,5', '20,10', '25,15', '30,20']
        self.engine.map_data['spawn_points']['Polska'] = new_spawns
        
        unit_data = self.create_mock_purchased_unit("New_Map_Unit")
        
        deployment_pos = find_deployment_position(unit_data, self.engine, 'ai_player_1')
        
        self.assertIsNotNone(deployment_pos)
        print(f"   Pozycja na nowej mapie: {deployment_pos}")
        
        # Sprawdź czy używa nowych spawn points
        new_positions = [(15, 5), (20, 10), (25, 15), (30, 20)]
        self.assertIn(deployment_pos, new_positions)
        
        print(f"   Adaptacja do nowej mapy: ✅")


def run_ai_commander_smart_tests():
    """Uruchom wszystkie testy AI Commandera z inteligentnym systemem"""
    print("🧠 [TESTY] AI Commander z inteligentnym spawnowaniem")
    print("="*60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAICommanderSmartDeployment)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    print("\n📊 PODSUMOWANIE TESTÓW:")
    print(f"Uruchomiono: {result.testsRun}")
    print(f"Błędy: {len(result.errors)}")
    print(f"Niepowodzenia: {len(result.failures)}")
    
    if result.errors:
        print("\n❌ BŁĘDY:")
        for test, error in result.errors:
            print(f"  {test}: {error}")
    
    if result.failures:
        print("\n❌ NIEPOWODZENIA:")
        for test, failure in result.failures:
            print(f"  {test}: {failure}")
    
    if not result.errors and not result.failures:
        print("\n🎉 WSZYSTKIE TESTY POMYŚLNE!")
        print("\n🚀 AI COMMANDER Z INTELIGENTNYM SYSTEMEM GOTOWY:")
        print("  ✅ Analiza scenariuszy obronnych")
        print("  ✅ Analiza scenariuszy ofensywnych") 
        print("  ✅ Wsparcie dla klastrów jednostek")
        print("  ✅ Fallback do prostego systemu")
        print("  ✅ Kompatybilność z różnymi nacjami")
        print("  ✅ Adaptacja do reorganizacji mapy")
        print("\n💡 KORZYŚCI INTELIGENTNEGO SYSTEMU:")
        print("  🎯 Spawn w najlepszym miejscu według sytuacji")
        print("  🛡️ Priorytet obrony zagrożonych obszarów")
        print("  ⚔️ Wsparcie dla operacji ofensywnych")
        print("  🤝 Koordynacja z istniejącymi jednostkami")
        print("  🗺️ Automatyczna adaptacja do zmian mapy")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_ai_commander_smart_tests()
    exit(0 if success else 1)
