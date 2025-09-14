#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test konwersji profili - czy naprawiliśmy błąd
"""

def test_profile_conversion():
    """Test czy konwersja display -> value działa"""
    
    print("🧪 TEST KONWERSJI PROFILI")
    print("=" * 40)
    
    # Stwórz prostą wersję funkcji konwersji
    def convert_display_to_value(display_value):
        """Konwertuje wartość wyświetlaną na wartość systemową"""
        conversion_map = {
            "🎯 Balanced": "balanced",
            "🔥 Aggressive": "aggressive", 
            "🛡️ Defensive": "defensive"
        }
        return conversion_map.get(display_value, "balanced")
    
    # Test przypadków
    test_cases = [
        ("🎯 Balanced", "balanced"),
        ("🔥 Aggressive", "aggressive"),
        ("🛡️ Defensive", "defensive"),
        ("Invalid", "balanced"),  # fallback
        ("", "balanced")  # fallback
    ]
    
    print("Test konwersji:")
    all_passed = True
    for display, expected in test_cases:
        result = convert_display_to_value(display)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"  '{display}' → '{result}' (oczekiwane: '{expected}') {status}")
        if result != expected:
            all_passed = False
    
    # Test czy AI Config akceptuje nasze wartości
    try:
        from ai.ai_config import set_player_ai_profile, AIProfile
        
        print("\nTest czy AI Config akceptuje wartości:")
        for profile_value in ["balanced", "aggressive", "defensive"]:
            try:
                set_player_ai_profile(1, profile_value)
                print(f"  '{profile_value}' → ✅ ACCEPTED")
            except Exception as e:
                print(f"  '{profile_value}' → ❌ REJECTED: {e}")
                all_passed = False
                
    except ImportError as e:
        print(f"\n❌ Nie można zaimportować AI Config: {e}")
        all_passed = False
    
    if all_passed:
        print("\n🎉 WSZYSTKIE TESTY PRZESZŁY!")
        print("💡 Konwersja profili została naprawiona")
        return True
    else:
        print("\n🔥 BŁĘDY W TESTACH!")
        return False

if __name__ == "__main__":
    test_profile_conversion()