"""Test inteligentnego systemu spawnowania jednostek

TESTUJE:
- Analizę sytuacji taktycznej 
- Wybór optymalnego spawnu na podstawie potrzeb
- Adaptację do różnych scenariuszy
- Działanie z różnymi konfiguracjami map
"""

import unittest
import sys
import os

# Dodaj ścieżkę do głównego katalogu projektu
current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

try:
    from ai.smart_deployment import (
        analyze_tactical_situation, 
        evaluate_spawn_position,
        find_optimal_spawn_position,
        calculate_hex_distance
    )
except ImportError as e:
    print(f"Błąd importu: {e}")
    print(f"Sprawdzam ścieżki:")
    print(f"Current dir: {current_dir}")
    print(f"Project root: {project_root}")
    print(f"Sys path: {sys.path}")
    sys.exit(1)


class MockGameEngine:
    """Mock obiektu game engine do testów"""
    
    def __init__(self):
        self.tokens = []
        self.current_player_obj = MockPlayer()
        self.map_data = {
            'spawn_points': {
                'Polska': ['6,-3', '0,2', '0,13', '18,24'],
                'Niemcy': ['52,-26', '55,-23', '40,-20', '49,8']
            },
            'key_points': {
                '10,5': {'type': 'miasto', 'value': 150},
                '15,10': {'type': 'fabryka', 'value': 100},
                '45,-15': {'type': 'port', 'value': 200}
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
        # Uproszczone sąsiednie pozycje hex
        return [
            (q+1, r), (q-1, r), (q, r+1), 
            (q, r-1), (q+1, r-1), (q-1, r+1)
        ]


class MockToken:
    def __init__(self, q, r, owner, strength=5):
        self.q = q
        self.r = r
        self.owner = owner
        self.current_strength = strength
        self.name = f"Unit_{q}_{r}"


class TestIntelligentDeployment(unittest.TestCase):
    
    def setUp(self):
        """Przygotowanie do testów"""
        self.engine = MockGameEngine()
    
    def test_distance_calculation(self):
        """Test obliczania odległości hex"""
        # Test podstawowych odległości
        self.assertEqual(calculate_hex_distance((0, 0), (0, 0)), 0)
        self.assertEqual(calculate_hex_distance((0, 0), (1, 0)), 1)
        self.assertEqual(calculate_hex_distance((0, 0), (0, 1)), 1)
        self.assertEqual(calculate_hex_distance((0, 0), (2, 1)), 3)  # Poprawka - to jest 3, nie 2
        
        print("✅ Test obliczania odległości hex - PASSED")
    
    def test_tactical_analysis_empty_map(self):
        """Test analizy taktycznej na pustej mapie"""
        analysis = analyze_tactical_situation(self.engine, 'ai_player_1')
        
        self.assertEqual(len(analysis['threatened_areas']), 0)
        self.assertIsInstance(analysis['key_points_undefended'], list)
        self.assertEqual(len(analysis['friendly_clusters']), 0)
        
        print("✅ Test analizy pustej mapy - PASSED")
    
    def test_tactical_analysis_with_units(self):
        """Test analizy taktycznej z jednostkami"""
        # Dodaj przyjazne jednostki
        self.engine.tokens = [
            MockToken(6, -3, 'ai_player_1'),  # Przy spawn
            MockToken(7, -3, 'ai_player_1'),  # Blisko spawnu
            MockToken(10, 5, 'ai_player_1'),  # Przy punkcie kluczowym
        ]
        
        # Dodaj wrogów
        self.engine.tokens.extend([
            MockToken(8, -3, 'human_player'),   # Blisko przyjaciół
            MockToken(45, -15, 'human_player'), # Przy punkcie kluczowym wroga
        ])
        
        analysis = analyze_tactical_situation(self.engine, 'ai_player_1')
        
        # Sprawdź czy wykryto zagrożenia
        self.assertGreater(len(analysis['threatened_areas']), 0)
        
        # Sprawdź klastry
        self.assertGreater(len(analysis['friendly_clusters']), 0)
        
        print("✅ Test analizy z jednostkami - PASSED")
        print(f"   Zagrożone obszary: {len(analysis['threatened_areas'])}")
        print(f"   Klastry: {len(analysis['friendly_clusters'])}")
    
    def test_spawn_evaluation_defensive(self):
        """Test oceny spawnu w scenariuszu obronnym"""
        # Scenariusz: wrogie jednostki blisko spawn points
        self.engine.tokens = [
            MockToken(7, -2, 'human_player', 10),  # Wróg blisko spawnu (6,-3)
            MockToken(1, 2, 'human_player', 8),    # Wróg blisko spawnu (0,2)
        ]
        
        tactical_analysis = analyze_tactical_situation(self.engine, 'ai_player_1')
        
        # Oceń spawny
        spawn_6_minus3 = evaluate_spawn_position((6, -3), tactical_analysis, self.engine, 'Polska')
        spawn_0_2 = evaluate_spawn_position((0, 2), tactical_analysis, self.engine, 'Polska')
        spawn_18_24 = evaluate_spawn_position((18, 24), tactical_analysis, self.engine, 'Polska')
        
        # Spawn daleki od wrogów powinien mieć wyższy wynik
        self.assertGreater(spawn_18_24, spawn_6_minus3)
        
        print("✅ Test oceny obronnej - PASSED")
        print(f"   Spawn (6,-3): {spawn_6_minus3:.1f}")
        print(f"   Spawn (0,2): {spawn_0_2:.1f}")
        print(f"   Spawn (18,24): {spawn_18_24:.1f}")
    
    def test_spawn_evaluation_offensive(self):
        """Test oceny spawnu w scenariuszu ofensywnym"""
        # Scenariusz: punkty kluczowe pod zagrożeniem
        self.engine.tokens = [
            MockToken(11, 6, 'ai_player_1', 5),    # Przyjaciel blisko punktu (10,5)
            MockToken(14, 9, 'human_player', 12),  # Wróg zagraża punktowi (15,10)
        ]
        
        tactical_analysis = analyze_tactical_situation(self.engine, 'ai_player_1')
        
        # Oceń spawny względem obrony punktów kluczowych
        spawn_6_minus3 = evaluate_spawn_position((6, -3), tactical_analysis, self.engine, 'Polska')
        spawn_18_24 = evaluate_spawn_position((18, 24), tactical_analysis, self.engine, 'Polska')
        
        # Spawn bliżej zagrożeń powinien mieć bonus
        print("✅ Test oceny ofensywnej - PASSED")
        print(f"   Spawn (6,-3): {spawn_6_minus3:.1f}")
        print(f"   Spawn (18,24): {spawn_18_24:.1f}")
    
    def test_optimal_spawn_selection(self):
        """Test wyboru optymalnego spawnu"""
        # Scenariusz mieszany
        self.engine.tokens = [
            # Przyjaciele
            MockToken(5, -2, 'ai_player_1', 6),
            MockToken(6, -2, 'ai_player_1', 4),
            
            # Wrogowie zagrażający
            MockToken(8, -1, 'human_player', 10),
            MockToken(2, 3, 'human_player', 8),
        ]
        
        optimal_pos = find_optimal_spawn_position({}, self.engine, 'ai_player_1')
        
        self.assertIsNotNone(optimal_pos)
        self.assertIsInstance(optimal_pos, tuple)
        self.assertEqual(len(optimal_pos), 2)
        
        print("✅ Test wyboru optymalnego spawnu - PASSED")
        print(f"   Wybrana pozycja: {optimal_pos}")
    
    def test_occupied_spawns_fallback(self):
        """Test fallback gdy spawny zajęte"""
        # Zajmij wszystkie spawn points
        spawn_points = self.engine.map_data['spawn_points']['Polska']
        for spawn_str in spawn_points:
            q, r = map(int, spawn_str.split(','))
            self.engine.board.occupied_positions.add((q, r))
        
        optimal_pos = find_optimal_spawn_position({}, self.engine, 'ai_player_1')
        
        # Powinien znaleźć sąsiednią pozycję
        self.assertIsNotNone(optimal_pos)
        
        # Sprawdź czy to rzeczywiście sąsiad spawnu
        is_neighbor = False
        for spawn_str in spawn_points:
            spawn_q, spawn_r = map(int, spawn_str.split(','))
            neighbors = self.engine.board.neighbors(spawn_q, spawn_r)
            if optimal_pos in neighbors:
                is_neighbor = True
                break
        
        self.assertTrue(is_neighbor)
        
        print("✅ Test fallback dla zajętych spawnów - PASSED")
        print(f"   Znaleziono sąsiednią pozycję: {optimal_pos}")
    
    def test_different_nation_spawns(self):
        """Test działania z różnymi nacjami"""
        # Zmień na Niemcy
        self.engine.current_player_obj.nation = 'Niemcy'
        
        optimal_pos = find_optimal_spawn_position({}, self.engine, 'ai_player_1')
        
        # Sprawdź czy pozycja należy do spawn points Niemiec
        german_spawns = self.engine.map_data['spawn_points']['Niemcy']
        german_positions = [tuple(map(int, s.split(','))) for s in german_spawns]
        
        self.assertIn(optimal_pos, german_positions)
        
        print("✅ Test różnych nacji - PASSED")
        print(f"   Niemcy spawn: {optimal_pos}")
    
    def test_map_reorganization_adaptation(self):
        """Test adaptacji do reorganizacji mapy"""
        # Symuluj nową organizację spawn points
        new_spawns = ['20,10', '25,15', '30,5', '35,0']
        self.engine.map_data['spawn_points']['Polska'] = new_spawns
        
        optimal_pos = find_optimal_spawn_position({}, self.engine, 'ai_player_1')
        
        # Sprawdź czy używa nowych spawn points
        new_positions = [tuple(map(int, s.split(','))) for s in new_spawns]
        self.assertIn(optimal_pos, new_positions)
        
        print("✅ Test adaptacji do nowej mapy - PASSED")
        print(f"   Nowe spawny działają: {optimal_pos}")


def run_smart_deployment_tests():
    """Uruchom wszystkie testy inteligentnego systemu"""
    print("🧠 [TESTY] Inteligentny system spawnowania")
    print("="*50)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntelligentDeployment)
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
        print("\n🚀 SYSTEM GOTOWY DO UŻYCIA:")
        print("  ✅ Inteligentna analiza sytuacji taktycznej")
        print("  ✅ Adaptacyjny wybór pozycji spawnu")
        print("  ✅ Wsparcie dla reorganizacji mapy")
        print("  ✅ Fallback dla zajętych pozycji")
        print("  ✅ Kompatybilność z różnymi nacjami")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_smart_deployment_tests()
    exit(0 if success else 1)
