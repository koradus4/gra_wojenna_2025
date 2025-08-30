"""
Test systemu graduowanej widoczności - POZIOM 1
Testuje podstawowe funkcjonalności detection_level
"""
import sys
import os

# Dodaj główny katalog do path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_detection_level_calculation():
    """Test obliczania poziomu detekcji"""
    print("🧪 TEST: Detection Level Calculation")
    
    try:
        # Import z pełną ścieżką
        sys.path.append(os.path.join(project_root, 'engine'))
        from action_refactored_clean import VisionService
        
        # Test przypadki
        test_cases = [
            (0, 5, 1.0),    # Odległość 0 = pełna detekcja
            (1, 5, 0.87),   # Blisko - wysoka detekcja
            (3, 5, 0.55),   # Średnio - średnia detekcja  
            (4, 5, 0.30),   # Daleko - niska detekcja
            (5, 5, 0.0),    # Poza zasięgiem = 0
            (6, 5, 0.0),    # Poza zasięgiem = 0
        ]
        
        all_passed = True
        for distance, sight, expected in test_cases:
            result = VisionService.calculate_detection_level(distance, sight)
            passed = abs(result - expected) < 0.1  # Tolerancja 10%
            
            print(f"   Distance {distance}, Sight {sight}: {result:.2f} (expected ~{expected}) {'✅' if passed else '❌'}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("✅ Test detection calculation: PASSED")
        else:
            print("❌ Test detection calculation: FAILED")
            
        return all_passed
    except Exception as e:
        print(f"❌ Test detection calculation: ERROR - {e}")
        return False

def test_detection_filter():
    """Test filtrowania informacji o wrogach"""
    print("\n🧪 TEST: Detection Filter")
    
    try:
        # Import z pełną ścieżką
        sys.path.append(os.path.join(project_root, 'engine'))
        from action_refactored_clean import VisionService
        
        # Mock token
        class MockToken:
            def __init__(self):
                self.id = "GE_TANK_001"
                self.q = 5
                self.r = 3
                self.combat_value = 7
                self.stats = {'nation': 'Niemcy', 'type': 'tank'}
        
        token = MockToken()
        
        # Test różnych poziomów detekcji
        test_cases = [
            (1.0, 'FULL'),      # Pełna informacja
            (0.7, 'PARTIAL'),   # Częściowa informacja 
            (0.3, 'MINIMAL'),   # Minimalna informacja
        ]
        
        all_passed = True
        for detection_level, expected_quality in test_cases:
            result = apply_detection_filter(token, detection_level)
            quality = result.get('info_quality', 'UNKNOWN')
            passed = quality == expected_quality
            
            print(f"   Detection {detection_level}: {quality} {'✅' if passed else '❌'}")
            if detection_level >= 0.8:
                print(f"      Full info: CV={result.get('combat_value')}, Type={result.get('type')}")
            elif detection_level >= 0.5:
                print(f"      Partial info: CV={result.get('combat_value')}, Type={result.get('type')}")
            else:
                print(f"      Minimal info: CV={result.get('combat_value')}, Type={result.get('type')}")
            
            if not passed:
                all_passed = False
        
        if all_passed:
            print("✅ Test detection filter: PASSED")
        else:
            print("❌ Test detection filter: FAILED")
            
        return all_passed
    except Exception as e:
        print(f"❌ Test detection filter: ERROR - {e}")
        return False

def test_vision_service_integration():
    """Test integracji z VisionService"""
    print("\n🧪 TEST: VisionService Integration")
    
    try:
        # Mock objects
        class MockBoard:
            def hex_distance(self, pos1, pos2):
                return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
                
        class MockToken:
            def __init__(self, token_id, q, r, owner, sight=3):
                self.id = token_id
                self.q = q
                self.r = r
                self.owner = owner
                self.stats = {'sight': sight}
                
        class MockPlayer:
            def __init__(self):
                self.temp_visible_hexes = set()
                self.temp_visible_tokens = set()
                self.temp_visible_token_data = {}
                
        class MockEngine:
            def __init__(self):
                self.board = MockBoard()
                self.tokens = [
                    MockToken("PL_INF_01", 0, 0, "2 (Polska)", sight=3),
                    MockToken("GE_TANK_01", 2, 1, "5 (Niemcy)", sight=2),
                    MockToken("GE_INF_01", 4, 0, "5 (Niemcy)", sight=1),
                ]
        
        from engine.action_refactored_clean import VisionService
        
        engine = MockEngine()
        player = MockPlayer()
        observing_token = engine.tokens[0]  # Polski token
        visible_hexes = {(2, 1), (4, 0)}  # Pozycje wrogów
        
        # Test dodawania wrogich tokenów z detection level
        VisionService._add_visible_enemy_tokens(engine, player, observing_token, visible_hexes)
        
        # Sprawdź wyniki
        detected_count = len(player.temp_visible_tokens)
        detection_data_count = len(player.temp_visible_token_data)
        
        print(f"   Detected tokens: {detected_count}")
        print(f"   Detection data entries: {detection_data_count}")
        
        for token_id, data in player.temp_visible_token_data.items():
            detection_level = data.get('detection_level', 0.0)
            distance = data.get('distance', 0)
            print(f"   {token_id}: detection={detection_level:.2f}, distance={distance}")
        
        passed = detected_count == 2 and detection_data_count == 2
        
        if passed:
            print("✅ Test VisionService integration: PASSED")
        else:
            print("❌ Test VisionService integration: FAILED")
            
        return passed
    except Exception as e:
        print(f"❌ Test VisionService integration: ERROR - {e}")
        return False

def test_ai_detection_usage():
    """Test użycia detection w AI Commander"""
    print("\n🧪 TEST: AI Detection Usage")
    
    try:
        from ai.ai_commander import find_enemies_in_range
        
        # Mock objects (uproszczona wersja)
        class MockBoard:
            def hex_distance(self, pos1, pos2):
                return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))
                
        class MockToken:
            def __init__(self, token_id, q, r, owner, cv=5, sight=2):
                self.id = token_id
                self.q = q
                self.r = r
                self.owner = owner
                self.combat_value = cv
                self.stats = {'attack': {'range': 2}, 'sight': sight}
                
        class MockPlayer:
            def __init__(self):
                self.visible_token_data = {
                    'GE_TANK_01': {'detection_level': 0.8, 'distance': 1},
                    'GE_INF_01': {'detection_level': 0.3, 'distance': 2}
                }
                
        class MockEngine:
            def __init__(self):
                self.board = MockBoard()
                self.tokens = [
                    MockToken("PL_INF_01", 5, 5, "2 (Polska)", sight=3),
                    MockToken("GE_TANK_01", 6, 6, "5 (Niemcy)", cv=7),
                    MockToken("GE_INF_01", 7, 7, "5 (Niemcy)", cv=4),
                ]
                self.current_player_obj = MockPlayer()
        
        engine = MockEngine()
        unit = {
            'token': engine.tokens[0],
            'q': 5, 'r': 5
        }
        
        # Test find_enemies_in_range z nowym systemem
        enemies = find_enemies_in_range(unit, engine, 2)
        
        print(f"   Found enemies: {len(enemies)}")
        for enemy in enemies:
            detection = enemy.get('detection_level', 1.0)
            cv = enemy.get('cv', 'unknown')
            print(f"   Enemy {enemy['id']}: detection={detection:.2f}, cv={cv}")
        
        # Sprawdź czy AI używa detection level
        has_detection_data = any('detection_level' in enemy for enemy in enemies)
        
        if has_detection_data:
            print("✅ Test AI detection usage: PASSED")
        else:
            print("❌ Test AI detection usage: FAILED")
            
        return has_detection_data
    except Exception as e:
        print(f"❌ Test AI detection usage: ERROR - {e}")
        return False

def run_all_tests():
    """Uruchom wszystkie testy systemu graduowanej widoczności"""
    print("🎯 SYSTEM GRADUOWANEJ WIDOCZNOŚCI - POZIOM 1")
    print("=" * 60)
    
    test_results = []
    
    test_results.append(test_detection_level_calculation())
    test_results.append(test_detection_filter()) 
    test_results.append(test_vision_service_integration())
    test_results.append(test_ai_detection_usage())
    
    print("\n" + "=" * 60)
    print("📊 PODSUMOWANIE TESTÓW")
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {total - passed}")
    print(f"📈 Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 WSZYSTKIE TESTY PRZESZŁY! System graduowanej widoczności działa poprawnie.")
    else:
        print(f"\n⚠️  {total - passed} testów nie przeszło. Sprawdź implementację.")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()
