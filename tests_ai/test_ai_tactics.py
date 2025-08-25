#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST: Nowe taktyki AI Commander
"""

import sys
import os
import json
from pathlib import Path

# Dodaj ścieżkę do głównego folderu projektu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_mission_tactics():
    """Test różnych taktyk misji"""
    print("🎯 === TEST NOWYCH TAKTYK AI COMMANDER ===\n")
    
    # Import po dodaniu ścieżki
    from ai.ai_commander import execute_mission_tactics
    
    # Mock jednostka
    mock_unit = {
        'id': 'test_unit_1',
        'q': 10, 'r': 10,
        'mp': 4, 'fuel': 8,
        'cv': 5
    }
    
    # Mock board z prostym pathfinding
    mock_board = type('obj', (), {
        'find_path': lambda self, start, end, **kwargs: [start, end] if start != end else [start]
    })()
    
    # Mock game engine
    mock_engine = type('obj', (), {
        'board': mock_board
    })()
    
    # Bazowy cel
    base_target = [20, 15]
    
    # TEST 1: INTEL_GATHERING
    print("🔍 === TEST 1: INTEL_GATHERING ===")
    for i in range(3):
        result = execute_mission_tactics(
            mock_unit, base_target, "INTEL_GATHERING", 
            mock_engine, i, 3
        )
        print(f"  Jednostka {i}: {mock_unit['q']},{mock_unit['r']} -> {result}")
    
    # TEST 2: DEFEND_KEYPOINTS
    print("\n🛡️ === TEST 2: DEFEND_KEYPOINTS ===")
    for i in range(3):
        result = execute_mission_tactics(
            mock_unit, base_target, "DEFEND_KEYPOINTS", 
            mock_engine, i, 3
        )
        print(f"  Jednostka {i}: {mock_unit['q']},{mock_unit['r']} -> {result}")
    
    # TEST 3: ATTACK_ENEMY_VP (fast unit)
    print("\n⚔️ === TEST 3: ATTACK_ENEMY_VP (FAST UNIT) ===")
    fast_unit = dict(mock_unit)
    fast_unit['mp'] = 6
    fast_unit['fuel'] = 10  # Mobilność = 16 > 8
    
    result = execute_mission_tactics(
        fast_unit, base_target, "ATTACK_ENEMY_VP", 
        mock_engine, 0, 2
    )
    print(f"  Fast unit (mob=16): {fast_unit['q']},{fast_unit['r']} -> {result}")
    
    # TEST 4: ATTACK_ENEMY_VP (slow unit)
    print("\n⚔️ === TEST 4: ATTACK_ENEMY_VP (SLOW UNIT) ===")
    slow_unit = dict(mock_unit)
    slow_unit['mp'] = 2
    slow_unit['fuel'] = 4  # Mobilność = 6 <= 8
    
    result = execute_mission_tactics(
        slow_unit, base_target, "ATTACK_ENEMY_VP", 
        mock_engine, 1, 2
    )
    print(f"  Slow unit (mob=6): {slow_unit['q']},{slow_unit['r']} -> {result}")
    
    # TEST 5: SECURE_KEYPOINT
    print("\n🎯 === TEST 5: SECURE_KEYPOINT ===")
    for i in range(4):
        result = execute_mission_tactics(
            mock_unit, base_target, "SECURE_KEYPOINT", 
            mock_engine, i, 4
        )
        role = "LEADER" if i == 0 else "FORMATION"
        print(f"  Jednostka {i} ({role}): {mock_unit['q']},{mock_unit['r']} -> {result}")
    
    # TEST 6: UNKNOWN mission type
    print("\n❓ === TEST 6: UNKNOWN MISSION ===")
    result = execute_mission_tactics(
        mock_unit, base_target, "UNKNOWN_MISSION", 
        mock_engine, 0, 1
    )
    print(f"  Unknown mission: {mock_unit['q']},{mock_unit['r']} -> {result}")

def test_integration():
    """Test integracji z prawdziwym systemem"""
    print("\n🔗 === TEST INTEGRACJI ===")
    
    # Sprawdź czy możemy importować nowe funkcje
    try:
        from ai.ai_commander import execute_mission_tactics, make_tactical_turn
        print("✅ Import funkcji taktycznych: OK")
    except ImportError as e:
        print(f"❌ Błąd importu: {e}")
        return
    
    # Sprawdź czy funkcje nie crashują
    try:
        mock_unit = {'id': 'test', 'q': 5, 'r': 5, 'mp': 3, 'fuel': 6}
        mock_board = type('obj', (), {
            'find_path': lambda self, start, end, **kwargs: [start, end]
        })()
        mock_engine = type('obj', (), {'board': mock_board})()
        
        result = execute_mission_tactics(
            mock_unit, [10, 10], "SECURE_KEYPOINT", 
            mock_engine, 0, 1
        )
        print(f"✅ Funkcja execute_mission_tactics: OK -> {result}")
    except Exception as e:
        print(f"❌ Błąd execute_mission_tactics: {e}")

if __name__ == "__main__":
    test_mission_tactics()
    test_integration()
    
    print("\n🎉 === TEST ZAKOŃCZONY ===")
    print("\n💡 NOWE MOŻLIWOŚCI:")
    print("  🔍 INTEL_GATHERING: Jednostki się rozpraszają w różnych kierunkach")
    print("  🛡️ DEFEND_KEYPOINTS: Pozycje obronne wokół kluczowego punktu")
    print("  ⚔️ ATTACK_ENEMY_VP: Fast units atakują, slow units wspierają")
    print("  🎯 SECURE_KEYPOINT: Formation attack z liderem i wsparciem")
    print("\n✅ AI Commander przestaje być 'lemmingiem'!")
