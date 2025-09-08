"""Test script dla Phase 4 Advanced Logistics AI
Sprawdza integrację wszystkich modułów Phase 4 przed rzeczywistą grą.
"""
import sys
from pathlib import Path

# Dodaj ścieżkę do modułów AI (z katalogu tests)
sys.path.append(str(Path(__file__).parent.parent))

def test_communication_ai_imports():
    """Test importów z communication_ai.py"""
    print("🔧 Testing communication_ai imports...")
    try:
        from ai.communication_ai import (
            analyze_force_requirements,
            generate_reinforcement_request, 
            send_request_to_general,
            commander_logistics_analysis
        )
        print("✅ communication_ai imports successful")
        return True
    except Exception as e:
        print(f"❌ communication_ai import error: {e}")
        return False

def test_general_phase4_imports():
    """Test importów z general_phase4.py"""
    print("🔧 Testing general_phase4 imports...")
    try:
        from ai.general_phase4 import (
            collect_commander_requests,
            prioritize_purchase_decisions,
            execute_adaptive_purchases,
            integrate_phase4_with_general
        )
        print("✅ general_phase4 imports successful")
        return True
    except Exception as e:
        print(f"❌ general_phase4 import error: {e}")
        return False

def test_victory_ai_phase4():
    """Test Victory AI Phase 4 integration"""
    print("🔧 Testing victory_ai Phase 4 integration...")
    try:
        from ai.victory_ai import (
            victory_ai_phase4_controller,
            integrate_victory_ai_complete_system
        )
        print("✅ victory_ai Phase 4 functions available")
        return True
    except Exception as e:
        print(f"❌ victory_ai Phase 4 error: {e}")
        return False

def test_directory_structure():
    """Test wymaganej struktury katalogów"""
    print("🔧 Testing directory structure...")
    
    required_dirs = [
        Path("data/requests"),
        Path("logs/ai_commander"),
        Path("logs/ai_general")
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
            all_exist = False
    
    return all_exist

def test_mock_force_analysis():
    """Test force analysis z mock data"""
    print("🔧 Testing mock force analysis...")
    
    try:
        from ai.communication_ai import analyze_force_requirements
        
        # Mock units data
        mock_units = [
            {
                'unit_id': 'test_1',
                'unit_type': 'I',
                'combat_value': 3,
                'fuel': 50,
                'max_fuel': 100,
                'mp': 2,
                'position': (25, 0)
            },
            {
                'unit_id': 'test_2', 
                'unit_type': 'Z',
                'combat_value': 2,
                'fuel': 80,
                'max_fuel': 100,
                'mp': 3,
                'position': (26, 0)
            }
        ]
        
        # Mock game engine
        class MockGameEngine:
            def __init__(self):
                self.current_turn = 5
                self.tokens = []
                self.key_points_state = {
                    'hex_25_0': {'current_value': 85},
                    'hex_30_5': {'current_value': 70}
                }
                self.current_player_obj = MockPlayer()
        
        class MockPlayer:
            def __init__(self):
                self.nation = 'Test Nation'
        
        mock_engine = MockGameEngine()
        
        # Run analysis
        analysis_result = analyze_force_requirements(mock_units, mock_engine)
        
        print(f"✅ Force analysis completed - Status: {analysis_result.get('status')}")
        print(f"   Units analyzed: {analysis_result.get('current_composition', {}).get('total_units', 0)}")
        print(f"   Urgency level: {analysis_result.get('urgency')}")
        print(f"   Requirements: {len(analysis_result.get('requirements', {}))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock force analysis error: {e}")
        return False

def test_mock_request_generation():
    """Test request generation z mock data"""
    print("🔧 Testing mock request generation...")
    
    try:
        from ai.communication_ai import generate_reinforcement_request
        
        # Mock force requirements
        mock_requirements = {
            'requirements': {
                'infantry_needed': 2,
                'supply_needed': 1,
                'reconnaissance_needed': 1
            },
            'priorities': {
                'COMBAT_REINFORCEMENT': 8,
                'LOGISTICS': 6,
                'RECONNAISSANCE': 7
            },
            'current_composition': {'total_units': 10, 'combat_value_total': 25},
            'threat_analysis': {'threat_level': 'HIGH', 'force_ratio': 0.7},
            'logistics_status': {'avg_fuel_level': 0.6, 'resupply_needed': True}
        }
        
        # Mock game engine
        class MockGameEngine:
            def __init__(self):
                self.current_turn = 5
                self.current_player_obj = MockPlayer()
        
        class MockPlayer:
            def __init__(self):
                self.nation = 'Test Nation'
        
        mock_engine = MockGameEngine()
        
        # Generate request
        request = generate_reinforcement_request(
            mock_requirements, 
            'HIGH', 
            commander_id=101,
            game_engine=mock_engine
        )
        
        print(f"✅ Request generated - ID: {request.get('request_id')}")
        print(f"   Urgency: {request.get('urgency')}")
        print(f"   Unit requests: {len(request.get('unit_requests', []))}")
        print(f"   Justification: {request.get('justification')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock request generation error: {e}")
        return False

def run_all_tests():
    """Run all Phase 4 tests"""
    print("🚀 === PHASE 4 ADVANCED LOGISTICS AI - TESTING ===\n")
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Communication AI Imports", test_communication_ai_imports),
        ("General Phase4 Imports", test_general_phase4_imports),
        ("Victory AI Phase4", test_victory_ai_phase4),
        ("Mock Force Analysis", test_mock_force_analysis),
        ("Mock Request Generation", test_mock_request_generation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))
        print("")
    
    print("🏁 === TEST RESULTS SUMMARY ===")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Phase 4 ready for real game testing!")
    else:
        print("⚠️ Some tests failed. Check errors above before game testing.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
