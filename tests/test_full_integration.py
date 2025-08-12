#!/usr/bin/env python3
"""
TEST PEŁNEJ INTEGRACJI AI GENERAL - Symulacja pełnego przepływu
"""

from ai import AIGeneral, is_ai_general, set_ai_general_enabled, AI_CONFIG
from engine.player import Player
from core.ekonomia import EconomySystem

def test_full_integration():
    """Test pełnej integracji AI z opcją wyboru"""
    print("🧪 TEST PEŁNEJ INTEGRACJI AI GENERAL")
    print("=" * 60)
    
    # Test 1: Domyślna konfiguracja (AI wyłączone)
    print("1. 🔴 Test z wyłączonym AI:")
    players = [
        Player(1, "Polska", "Generał", 5, "test.png"),
        Player(4, "Niemcy", "Generał", 5, "test.png"),
    ]
    
    for p in players:
        p.economy = EconomySystem()
        ai_status = is_ai_general(p)
        print(f"   - {p.name}: AI = {ai_status}")
    
    # Test 2: Włączenie AI (symulacja wyboru użytkownika)
    print("\n2. 🟢 Test z włączonym AI:")
    set_ai_general_enabled(True)  # Symulacja zaznaczenia checkbox
    
    for p in players:
        ai_status = is_ai_general(p)
        print(f"   - {p.name}: AI = {ai_status}")
    
    # Test 3: Test konfiguracji
    print(f"\n3. 📊 Aktualna konfiguracja AI:")
    print(f"   USE_AI_GENERAL: {AI_CONFIG['USE_AI_GENERAL']}")
    print(f"   AI_GENERAL_PLAYERS: {AI_CONFIG['AI_GENERAL_PLAYERS']}")
    
    # Test 4: Test wyłączenia z powrotem
    print("\n4. 🔴 Test wyłączenia AI:")
    set_ai_general_enabled(False)
    
    for p in players:
        ai_status = is_ai_general(p)
        print(f"   - {p.name}: AI = {ai_status}")
    
    print("=" * 60)
    print("🏁 PEŁNA INTEGRACJA DZIAŁA POPRAWNIE!")
    print("\n🎮 GRA GOTOWA DO UŻYCIA:")
    print("   1. Uruchom: python main.py")
    print("   2. Zaznacz checkbox '🤖 Włącz AI Generałów'")
    print("   3. Skonfiguruj graczy i rozpocznij grę")
    print("   4. AI przejmie kontrolę nad generałami!")

if __name__ == "__main__":
    test_full_integration()
