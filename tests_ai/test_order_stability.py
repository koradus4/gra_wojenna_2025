"""
Test systemu stabilności rozkazów AI General
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.ai_general import AIGeneral
from pathlib import Path
import json
import datetime

def test_order_stability():
    """Test podstawowych funkcji stabilności rozkazów"""
    print("🧪 === TEST SYSTEMU STABILNOŚCI ROZKAZÓW ===\n")
    
    # Stwórz mock AI General
    general = AIGeneral("polish", "medium")
    
    # Mock commander
    mock_commander = type('obj', (), {
        'id': 3,
        'nation': 'Polska'
    })()
    
    # Mock game_engine z prostymi tokenami
    mock_tokens = [
        type('obj', (), {'owner': '3 (Polska)', 'q': 10, 'r': 5, 'combat_value': 80, 'max_combat_value': 100})(),
        type('obj', (), {'owner': '3 (Polska)', 'q': 11, 'r': 6, 'combat_value': 90, 'max_combat_value': 100})(),
        type('obj', (), {'owner': '5 (Niemcy)', 'q': 20, 'r': 10, 'combat_value': 100, 'max_combat_value': 100})(),
    ]
    
    mock_engine = type('obj', (), {
        'tokens': mock_tokens
    })()
    
    # Test 1: Brak poprzedniego rozkazu - powinien wydać
    print("📋 Test 1: Brak poprzedniego rozkazu")
    should_issue, reason = general.should_issue_new_order(
        mock_commander, [15, -7], 25.0, 5, mock_engine
    )
    print(f"Wynik: {should_issue}, Powód: {reason}")
    assert should_issue == True, "Powinien wydać rozkaz gdy brak poprzedniego"
    print("✅ PASS\n")
    
    # Stwórz mock poprzedniego rozkazu w pliku
    orders_data = {
        "timestamp": "2025-08-25_12:00:00",
        "turn": 2,
        "strategy_type": "EXPANSION", 
        "orders": {
            "polska_commander_3": {
                "mission_type": "SECURE_KEYPOINT",
                "target_hex": [20, 10],
                "priority": "HIGH",
                "expires_turn": 7,
                "issued_turn": 2,
                "status": "ACTIVE",
                "strategy_context": "EXPANSION"
            }
        }
    }
    
    # Zapisz mock rozkaz
    Path("data").mkdir(exist_ok=True)
    with open("data/strategic_orders.json", 'w', encoding='utf-8') as f:
        json.dump(orders_data, f, indent=2)
    
    # Test 2: Cooling down - za wcześnie na nowy rozkaz
    print("📋 Test 2: Cooling down (za wcześnie)")
    should_issue, reason = general.should_issue_new_order(
        mock_commander, [15, -7], 25.0, 4, mock_engine  # Turn 4, ostatni wydany turn 2
    )
    print(f"Wynik: {should_issue}, Powód: {reason}")
    assert should_issue == False, "Nie powinien wydać rozkazu w czasie cooling down"
    assert "Cooling down" in reason, "Powód powinien wspominać cooling down"
    print("✅ PASS\n")
    
    # Test 3: Po cooling down - powinien wydać
    print("📋 Test 3: Po cooling down (można wydać)")
    should_issue, reason = general.should_issue_new_order(
        mock_commander, [15, -7], 25.0, 6, mock_engine  # Turn 6, ostatni wydany turn 2
    )
    print(f"Wynik: {should_issue}, Powód: {reason}")
    assert should_issue == True, "Powinien wydać rozkaz po cooling down"
    print("✅ PASS\n")
    
    # Test 4: Blisko celu - nie powinien zmieniać rozkazu
    print("📋 Test 4: Blisko obecnego celu (mission completion)")
    # Zmień pozycję jednostek blisko celu [20, 10]
    mock_tokens_close = [
        type('obj', (), {'owner': '3 (Polska)', 'q': 18, 'r': 9, 'combat_value': 80, 'max_combat_value': 100})(),
        type('obj', (), {'owner': '3 (Polska)', 'q': 19, 'r': 10, 'combat_value': 90, 'max_combat_value': 100})(),
    ]
    mock_engine_close = type('obj', (), {
        'tokens': mock_tokens_close
    })()
    
    should_issue, reason = general.should_issue_new_order(
        mock_commander, [15, -7], 25.0, 6, mock_engine_close
    )
    print(f"Wynik: {should_issue}, Powód: {reason}")
    assert should_issue == False, "Nie powinien wydać rozkazu gdy blisko celu"
    assert "Close to completing" in reason, "Powód powinien wspominać completion"
    print("✅ PASS\n")
    
    # Test 5: Emergency - wróg w pobliżu
    print("📋 Test 5: Emergency - wróg w pobliżu")
    mock_tokens_enemy = [
        type('obj', (), {'owner': '3 (Polska)', 'q': 10, 'r': 5, 'combat_value': 80, 'max_combat_value': 100})(),
        type('obj', (), {'owner': '5 (Niemcy)', 'q': 12, 'r': 6, 'combat_value': 100, 'max_combat_value': 100})(),
        type('obj', (), {'owner': '5 (Niemcy)', 'q': 13, 'r': 7, 'combat_value': 100, 'max_combat_value': 100})(),
        type('obj', (), {'owner': '5 (Niemcy)', 'q': 14, 'r': 8, 'combat_value': 100, 'max_combat_value': 100})(),
    ]
    mock_engine_enemy = type('obj', (), {
        'tokens': mock_tokens_enemy
    })()
    
    should_issue, reason = general.should_issue_new_order(
        mock_commander, [15, -7], 15.0, 4, mock_engine_enemy  # Turn 4 (normalnie cooling down)
    )
    print(f"Wynik: {should_issue}, Powód: {reason}")
    assert should_issue == True, "Powinien wydać rozkaz w emergency"
    assert "EMERGENCY" in reason, "Powód powinien wspominać emergency"
    print("✅ PASS\n")
    
    print("🎉 === WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE! ===")
    
    # Cleanup
    if Path("data/strategic_orders.json").exists():
        Path("data/strategic_orders.json").unlink()

if __name__ == "__main__":
    test_order_stability()
