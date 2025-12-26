"""
Główny test runner dla wszystkich testów AI
"""
import sys
import os

# Dodaj główny folder projektu do sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def run_all_tests():
    """Uruchamia wszystkie testy AI"""
    print("🧪 URUCHAMIANIE WSZYSTKICH TESTÓW AI")
    print("=" * 50)
    
    # Test podstawowej logiki AI
    try:
        print("\n1️⃣ Test podstawowej logiki AI (Generał + Komendant)")
        import test_ai_basic
        test_ai_basic.test_general_ai()
        test_ai_basic.test_commander_ai()
        print("✅ Test podstawowej logiki AI - PASSED")
    except Exception as e:
        print(f"❌ Test podstawowej logiki AI - FAILED: {e}")
    
    # Test logiki tokenów
    try:
        print("\n2️⃣ Test logiki tokenów (autonomiczne zachowania)")
        import test_token_ai
        test_token_ai.test_token_creation()
        test_token_ai.test_enemy_detection()
        test_token_ai.test_supply_behavior()
        test_token_ai.test_full_turn()
        print("✅ Test logiki tokenów - PASSED")
    except Exception as e:
        print(f"❌ Test logiki tokenów - FAILED: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 WSZYSTKIE TESTY AI UKOŃCZONE")

if __name__ == "__main__":
    run_all_tests()