#!/usr/bin/env python3
"""
Test porównawczy - różnica między starym (wszystkie wrogowie) a nowym (fog of war) systemem.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.engine import GameEngine
from engine.player import Player
from engine.token import Token
from main_ai_vs_human import LearningAICommander

def test_old_vs_new_system():
    """Test porównawczy - stary vs nowy system"""
    print("⚔️ TEST PORÓWNAWCZY: Stary vs Nowy system wykrywania wrogów")
    print("=" * 80)
    
    # Utwórz silnik gry z minimalną konfigurację
    engine = GameEngine.__new__(GameEngine)
    engine.tokens = []
    engine.players = []
    engine.current_player = None
    engine.turn_number = 1
    
    # Dodaj minimalną planszę
    class MinimalBoard:
        def hex_distance(self, pos1, pos2):
            q1, r1 = pos1
            q2, r2 = pos2
            return max(abs(q1 - q2), abs(r1 - r2), abs(q1 - q2 + r1 - r2))
        
        def get_tile(self, q, r):
            # Symuluj że wszystkie pozycje są dostępne
            class MockTile:
                def __init__(self):
                    self.move_mod = 1
            return MockTile()
        
        def neighbors(self, q, r):
            return [(q+1, r), (q-1, r), (q, r+1), (q, r-1), (q+1, r-1), (q-1, r+1)]
    
    engine.board = MinimalBoard()
    
    # Utwórz graczy
    ai_player = Player("AI_General", "Germany", "general")
    human_player = Player("Human_Player", "Poland", "general")
    
    # Dodaj jednostki niemieckie (AI) w centrum
    german_unit1 = Token("German_HQ", f"{ai_player.id} ({ai_player.nation})", 
                        {"move": 2, "combat_value": 4, "sight": 6}, 15, 15)
    
    german_unit2 = Token("German_Scout", f"{ai_player.id} ({ai_player.nation})", 
                        {"move": 4, "combat_value": 2, "sight": 8}, 16, 16)
    
    # Dodaj jednostki polskie na różnych odległościach
    polish_close = Token("Polish_Close", f"{human_player.id} ({human_player.nation})", 
                        {"move": 2, "combat_value": 3, "sight": 3}, 18, 18)  # Odległość 6 - widoczny dla German_Scout
    
    polish_medium = Token("Polish_Medium", f"{human_player.id} ({human_player.nation})", 
                         {"move": 2, "combat_value": 3, "sight": 3}, 25, 25)  # Odległość 20 - niewidoczny
    
    polish_far = Token("Polish_Far", f"{human_player.id} ({human_player.nation})", 
                      {"move": 2, "combat_value": 3, "sight": 3}, 30, 30)  # Odległość 30 - bardzo daleko
    
    polish_very_far = Token("Polish_VeryFar", f"{human_player.id} ({human_player.nation})", 
                           {"move": 2, "combat_value": 3, "sight": 3}, 50, 50)  # Odległość 70 - poza mapą
    
    # Dodaj jednostki do silnika
    engine.tokens = [german_unit1, german_unit2, polish_close, polish_medium, polish_far, polish_very_far]
    
    print(f"\n🎯 KONFIGURACJA TESTOWA:")
    print(f"   Jednostki niemieckie (AI):")
    print(f"     - {german_unit1.id} na ({german_unit1.q}, {german_unit1.r}) - zasięg: {german_unit1.stats.get('sight', 5)}")
    print(f"     - {german_unit2.id} na ({german_unit2.q}, {german_unit2.r}) - zasięg: {german_unit2.stats.get('sight', 5)}")
    print(f"   Jednostki polskie:")
    
    ai_commander = LearningAICommander(ai_player, engine, difficulty='medium')
    
    for polish_unit in [polish_close, polish_medium, polish_far, polish_very_far]:
        dist1 = ai_commander._calculate_distance(german_unit1, polish_unit)
        dist2 = ai_commander._calculate_distance(german_unit2, polish_unit)
        min_dist = min(dist1, dist2)
        print(f"     - {polish_unit.id} na ({polish_unit.q}, {polish_unit.r}) - odległość: {min_dist}")
    
    print(f"\n🔍 TEST NOWEGO SYSTEMU (FOG OF WAR):")
    print("-" * 60)
    
    # Test nowego systemu
    visible_enemies = ai_commander._get_enemy_units()
    
    print(f"\n📊 WYNIKI NOWEGO SYSTEMU:")
    print(f"   ✅ Widoczni wrogowie: {len(visible_enemies)}")
    if visible_enemies:
        for i, enemy in enumerate(visible_enemies, 1):
            min_dist = min([ai_commander._calculate_distance(enemy, german_unit1), 
                           ai_commander._calculate_distance(enemy, german_unit2)])
            print(f"     {i}. {enemy.id} (odległość: {min_dist})")
    
    # Symulacja starego systemu (wszystkie wrogowie)
    print(f"\n🕰️ SYMULACJA STAREGO SYSTEMU (wszystkie wrogowie):")
    print("-" * 60)
    
    all_enemies = []
    for token in engine.tokens:
        if token.owner == f"{ai_player.id} ({ai_player.nation})":
            continue
        if token.owner.endswith(f"({ai_player.nation})"):
            continue
        if "(" in token.owner and ")" in token.owner:
            owner_nation = token.owner.split("(")[1].split(")")[0]
            if owner_nation != ai_player.nation:
                all_enemies.append(token)
    
    print(f"   📊 Stary system widział by: {len(all_enemies)} wrogów")
    if all_enemies:
        for i, enemy in enumerate(all_enemies, 1):
            min_dist = min([ai_commander._calculate_distance(enemy, german_unit1), 
                           ai_commander._calculate_distance(enemy, german_unit2)])
            print(f"     {i}. {enemy.id} (odległość: {min_dist})")
    
    print(f"\n🎯 ANALIZA PORÓWNAWCZA:")
    print("-" * 60)
    print(f"   Stary system: {len(all_enemies)} wrogów (wszystkie jednostki)")
    print(f"   Nowy system: {len(visible_enemies)} wrogów (tylko widoczne)")
    print(f"   Różnica: {len(all_enemies) - len(visible_enemies)} wrogów jest ukrytych")
    
    if len(visible_enemies) < len(all_enemies):
        print(f"   🎉 SUKCES: Fog of War ukrywa {len(all_enemies) - len(visible_enemies)} wrogów!")
        print(f"   🌫️ AI nie widzi jednostek przeciwnika poza zasięgiem swoich jednostek")
    else:
        print(f"   ❌ PROBLEM: Fog of War nie działa - AI widzi wszystkich wrogów")
    
    print(f"\n🏁 TEST PORÓWNAWCZY ZAKOŃCZONY")
    print("=" * 80)

if __name__ == "__main__":
    test_old_vs_new_system()
