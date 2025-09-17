# -*- coding: utf-8 -*-
"""
Test integracji zaawansowanego logowania z AI Commander
"""

import sys
sys.path.append('.')

from utils.session_manager import SessionManager
from ai.ai_commander import AICommander, execute_mission_tactics
from pathlib import Path
import time

class MockGameEngine:
    """Mock game engine dla testów"""
    def __init__(self):
        self.current_turn = 5
        self.current_phase = 3
        self.board = None
        
class MockPlayer:
    """Mock player dla testów"""
    def __init__(self, name="Niemcy"):
        self.name = name
        self.nation = name  # Dodanie atrybutu nation
        self.id = 1

def test_integracji_ai_commander():
    """Test integracji zaawansowanego logowania z AI Commander"""
    
    print("🧪 TEST INTEGRACJI AI COMMANDER Z ZAAWANSOWANYM LOGOWANIEM")
    print("=" * 70)
    
    # KROK 1: Test inicjalizacji AI Commander z loggerem
    print("\n🤖 KROK 1: Test inicjalizacji AI Commander")
    mock_player = MockPlayer("Niemcy")
    ai_commander = AICommander(mock_player)
    
    if ai_commander.zaawansowany_logger:
        print("✅ AI Commander zainicjalizowany z zaawansowanym loggerem")
    else:
        print("❌ AI Commander bez zaawansowanego loggera")
        return False
    
    # KROK 2: Test logowania decyzji strategicznej
    print("\n🎯 KROK 2: Test logowania decyzji strategicznej")
    mock_engine = MockGameEngine()
    
    ai_commander.strategic_state = "TIED"
    ai_commander._force_strategic_log = True
    
    try:
        result = ai_commander.analyze_strategic_state(mock_engine)
        print("✅ Analiza stanu strategicznego z logowaniem wykonana")
    except Exception as e:
        print(f"⚠️ Błąd analizy strategicznej: {e}")
    
    # KROK 3: Test ręcznego logowania akcji taktycznej
    print("\n🎖️ KROK 3: Test logowania akcji taktycznej")
    mock_unit = {
        'id': 'TEST_PANZER_001',
        'hex_id': 'hex_15_10',
        'q': 15,
        'r': 10
    }
    
    ai_commander._loguj_akcje_taktyczna(
        "MOVE_TO_KEYPOINT",
        "unit_001", 
        (5, 7),
        (8, 10)
    )
    print("✅ Logowanie akcji taktycznej wykonane")
    
    # KROK 4: Test logowania wydajności
    print("\n⚡ KROK 4: Test logowania wydajności AI")
    ai_commander._loguj_wydajnosc_ai("RESPONSE_TIME", 156.7, "Turn execution")
    print("✅ Logowanie wydajności wykonane")
    
    # KROK 5: Test funkcji execute_mission_tactics z logowaniem
    print("\n🎯 KROK 5: Test execute_mission_tactics z logowaniem")
    
    # Dodaj ai_commander do mock_player
    mock_player.ai_commander = ai_commander
    mock_engine.current_player_obj = mock_player
    
    try:
        result = execute_mission_tactics(
            mock_unit, 
            [20, 15], 
            'SECURE_KEYPOINT',
            mock_engine,
            0, 
            3
        )
        print(f"✅ execute_mission_tactics wykonane, wynik: {result}")
    except Exception as e:
        print(f"⚠️ Błąd execute_mission_tactics: {e}")
    
    # KROK 6: Sprawdzenie statystyk
    print("\n📊 KROK 6: Statystyki logów")
    stats = ai_commander.zaawansowany_logger.pobierz_statystyki()
    
    for typ, info in stats.items():
        if info['wiersze'] > 0:
            print(f"✅ {typ}: {info['wiersze']} wierszy")
    
    print("\n🎉 TEST INTEGRACJI ZAKOŃCZONY!")
    return True

if __name__ == "__main__":
    test_integracji_ai_commander()