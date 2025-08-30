"""
Test systemu graduowanej widoczności - POZIOM 1 - PROSTY
"""

def calculate_detection_level(distance, max_sight):
    """Replika funkcji z VisionService"""
    if distance >= max_sight or max_sight <= 0:
        return 0.0
        
    base_ratio = 1.0 - (distance / max_sight)
    detection_level = min(1.0, base_ratio ** 0.6)
    
    return detection_level

def apply_detection_filter(token, detection_level=1.0):
    """Replika funkcji filtrującej"""
    if detection_level >= 0.8:
        return {
            'id': token['id'],
            'combat_value': token['combat_value'],
            'info_quality': 'FULL'
        }
    elif detection_level >= 0.5:
        return {
            'id': f"CONTACT_{token['id'][-3:]}",
            'combat_value': f"~{token['combat_value']-2}-{token['combat_value']+2}",
            'info_quality': 'PARTIAL'
        }
    else:
        return {
            'id': "UNKNOWN_CONTACT",
            'combat_value': "???",
            'info_quality': 'MINIMAL'
        }

def test_detection_level_calculation():
    """Test obliczania poziomu detekcji"""
    print("🧪 TEST: Detection Level Calculation")
    
    test_cases = [
        (0, 5, 1.0),    # Odległość 0 = pełna detekcja
        (1, 5, 0.87),   # Blisko - wysoka detekcja
        (3, 5, 0.55),   # Średnio - średnia detekcja  
        (4, 5, 0.30),   # Daleko - niska detekcja
        (5, 5, 0.0),    # Poza zasięgiem = 0
    ]
    
    all_passed = True
    for distance, sight, expected in test_cases:
        result = calculate_detection_level(distance, sight)
        passed = abs(result - expected) < 0.1  # Tolerancja 10%
        
        print(f"   Distance {distance}, Sight {sight}: {result:.2f} (expected ~{expected}) {'✅' if passed else '❌'}")
        if not passed:
            all_passed = False
    
    return all_passed

def test_detection_filter():
    """Test filtrowania informacji"""
    print("\n🧪 TEST: Detection Filter")
    
    token = {
        'id': 'GE_TANK_001',
        'combat_value': 7
    }
    
    test_cases = [
        (1.0, 'FULL'),
        (0.7, 'PARTIAL'),
        (0.3, 'MINIMAL'),
    ]
    
    all_passed = True
    for detection_level, expected_quality in test_cases:
        result = apply_detection_filter(token, detection_level)
        quality = result.get('info_quality')
        passed = quality == expected_quality
        
        print(f"   Detection {detection_level}: {quality} {'✅' if passed else '❌'}")
        print(f"      CV: {result.get('combat_value')}, ID: {result.get('id')}")
        
        if not passed:
            all_passed = False
    
    return all_passed

def test_integration_concept():
    """Test koncepcji integracji z grą"""
    print("\n🧪 TEST: Integration Concept")
    
    # Symulacja scenariusza gry
    scenarios = [
        {"enemy_distance": 1, "sight_range": 4, "expected_info": "FULL"},
        {"enemy_distance": 2, "sight_range": 4, "expected_info": "PARTIAL"},
        {"enemy_distance": 3, "sight_range": 4, "expected_info": "MINIMAL"},
        {"enemy_distance": 4, "sight_range": 4, "expected_info": "NONE"},
    ]
    
    all_passed = True
    for scenario in scenarios:
        distance = scenario["enemy_distance"]
        sight = scenario["sight_range"]
        expected = scenario["expected_info"]
        
        detection_level = calculate_detection_level(distance, sight)
        
        if detection_level >= 0.8:
            info_type = "FULL"
        elif detection_level >= 0.5:
            info_type = "PARTIAL"
        elif detection_level > 0.0:
            info_type = "MINIMAL"
        else:
            info_type = "NONE"
        
        passed = info_type == expected
        print(f"   Enemy at distance {distance} (sight {sight}): {info_type} {'✅' if passed else '❌'}")
        
        if not passed:
            all_passed = False
    
    return all_passed

def run_simple_test():
    """Uruchom prosty test systemu"""
    print("🎯 SYSTEM GRADUOWANEJ WIDOCZNOŚCI - POZIOM 1 - TEST PROSTY")
    print("=" * 65)
    
    test_results = []
    test_results.append(test_detection_level_calculation())
    test_results.append(test_detection_filter())
    test_results.append(test_integration_concept())
    
    print("\n" + "=" * 65)
    print("📊 PODSUMOWANIE")
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {total - passed}")
    print(f"📈 Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 KONCEPCJA DZIAŁA! Można kontynuować implementację w prawdziwej grze.")
    else:
        print(f"\n⚠️  {total - passed} testów nie przeszło.")
    
    return passed == total

if __name__ == "__main__":
    run_simple_test()
