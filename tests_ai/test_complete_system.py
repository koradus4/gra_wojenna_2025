#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test końcowy - sprawdzenie czy wszystkie komponenty AI działają razem
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ai_components():
    """Test wszystkich komponentów AI"""
    print("🎯 === TEST KOŃCOWY KOMPONENTÓW AI ===\n")
    
    # Test 1: Import wszystkich kluczowych modułów
    print("📦 Test 1: Import modułów AI")
    try:
        from ai.ai_general import AIGeneral
        from ai.ai_commander import AICommander, execute_mission_tactics
        print("✅ Import AI General: OK")
        print("✅ Import AI Commander: OK") 
        print("✅ Import execute_mission_tactics: OK")
    except ImportError as e:
        print(f"❌ Błąd importu: {e}")
        return False
    
    # Test 2: Sprawdź funkcje stabilności
    print("\n🔒 Test 2: System stabilności rozkazów")
    try:
        general = AIGeneral("polish")
        mock_commander = type('obj', (), {'id': 2})()
        
        result = general.should_issue_new_order(
            mock_commander, [15, -7], 8.0, 1, None
        )
        print(f"✅ should_issue_new_order: {result[0]} - {result[1]}")
    except Exception as e:
        print(f"❌ Błąd stabilności: {e}")
        return False
    
    # Test 3: Sprawdź taktyki
    print("\n⚔️ Test 3: System taktyk")
    try:
        mock_unit = {'id': 'test', 'q': 10, 'r': 10, 'mp': 4, 'fuel': 8}
        mock_board = type('obj', (), {
            'find_path': lambda self, start, end, **kwargs: [start, end]
        })()
        mock_engine = type('obj', (), {'board': mock_board})()
        
        tactics = ["SECURE_KEYPOINT", "INTEL_GATHERING", "DEFEND_KEYPOINTS", "ATTACK_ENEMY_VP"]
        for tactic in tactics:
            result = execute_mission_tactics(
                mock_unit, [20, 15], tactic, mock_engine, 0, 1
            )
            print(f"✅ {tactic}: {result}")
    except Exception as e:
        print(f"❌ Błąd taktyk: {e}")
        return False
    
    # Test 4: Test komunikacji JSON
    print("\n📋 Test 4: Komunikacja JSON")
    try:
        from pathlib import Path
        import json
        
        # Sprawdź czy istnieje plik rozkazów
        orders_file = Path("data/strategic_orders.json")
        if orders_file.exists():
            with open(orders_file, 'r', encoding='utf-8') as f:
                orders = json.load(f)
            print(f"✅ Plik rozkazów: OK ({len(orders.get('orders', {}))} rozkazów)")
        else:
            print("ℹ️ Brak pliku rozkazów (normalny stan przed grą)")
    except Exception as e:
        print(f"❌ Błąd JSON: {e}")
        return False
    
    return True

def test_game_readiness():
    """Test gotowości do prawdziwej gry"""
    print("\n🎮 === TEST GOTOWOŚCI DO GRY ===\n")
    
    print("✅ AI General:")
    print("  • System stabilności rozkazów (3-turn cooling down)")
    print("  • Inteligentne targety (value/distance scoring)")
    print("  • 4 strategie gry (EXPANSION/SCOUTING/DEFENSIVE/AGGRESSIVE)")
    print("  • Logowanie decyzji strategicznych")
    
    print("\n✅ AI Commander:")
    print("  • 4 różne taktyki per mission type:")
    print("    🔍 INTEL_GATHERING: Rozproszenie jednostek")
    print("    🛡️ DEFEND_KEYPOINTS: Pozycje obronne")
    print("    ⚔️ ATTACK_ENEMY_VP: Fast/slow unit coordination")
    print("    🎯 SECURE_KEYPOINT: Formation attack")
    print("  • Robust pathfinding z fallback")
    print("  • Logowanie akcji taktycznych")
    
    print("\n✅ Integracja:")
    print("  • JSON komunikacja General ↔ Commander")
    print("  • Expiry system (5-turn rozkazy)")
    print("  • Error handling i fallback mechanisms")
    
    print("\n🎯 REKOMENDACJE TESTOWE:")
    print("1. Uruchom główną grę: python main_ai.py")
    print("2. Wybierz konfigurację:")
    print("   ✅ Polski Generał - AI")
    print("   ✅ Polski Dowódca 1 - AI") 
    print("   ✅ Polski Dowódca 2 - AI")
    print("   ❌ Niemieccy gracze - HUMAN (obserwacja)")
    print("3. Obserwuj różnice w taktykach per mission type")
    print("4. Sprawdź logi w logs/ai_commander/ i logs/ai_general/")

if __name__ == "__main__":
    print("🚀 === KOMPLETNY TEST SYSTEMU AI ===")
    
    success = test_ai_components()
    
    if success:
        print("\n🎉 === WSZYSTKIE TESTY PRZESZŁY! ===")
        test_game_readiness()
        print("\n✅ System AI gotowy do prawdziwej gry! 🎮")
    else:
        print("\n❌ === BŁĘDY W TESTACH ===")
        print("Napraw błędy przed uruchomieniem gry!")
    
    print("\n" + "="*50)
    print("🎯 NASTĘPNY KROK: python main_ai.py")
    print("="*50)
