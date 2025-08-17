#!/usr/bin/env python3
"""
Test sprawdzający, czy AI z fog of war poprawnie wykrywa tylko widoczne jednostki.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.engine import GameEngine
from engine.player import Player
from engine.token import Token
from main_ai_vs_human import LearningAICommander

def test_fog_of_war():
    """Test fog of war - AI widzi tylko jednostki w zasięgu"""
    print("🌫️ TEST: Fog of War - AI widzi tylko jednostki w zasięgu")
    print("=" * 70)
    
    # Utwórz silnik gry z domyślnymi ścieżkami
    try:
        engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens",
            tokens_start_path="assets/start_tokens.json"
        )
    except Exception as e:
        print(f"   ⚠️ Używam minimalną konfigurację GameEngine (błąd: {e})")
        # Stwórz minimalny silnik dla testów
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
    
    # Utwórz dwóch graczy
    ai_player = Player("AI_General", "Germany", "general")
    human_player = Player("Human_Player", "Poland", "general")
    
    # Dodaj jednostkę niemiecką (AI) - ona będzie "szpiegiem"
    german_scout = Token("German_Scout", f"{ai_player.id} ({ai_player.nation})", 
                        {"move": 3, "combat_value": 2, "sight": 5}, 10, 10)
    
    # Dodaj jednostki polskie na różnych odległościach
    polish_close = Token("Polish_Close", f"{human_player.id} ({human_player.nation})", 
                        {"move": 2, "combat_value": 3, "sight": 3}, 12, 12)  # Odległość 4 (widoczny)
    
    polish_far = Token("Polish_Far", f"{human_player.id} ({human_player.nation})", 
                      {"move": 2, "combat_value": 3, "sight": 3}, 20, 20)  # Odległość 20 (niewidoczny)
    
    polish_medium = Token("Polish_Medium", f"{human_player.id} ({human_player.nation})", 
                         {"move": 2, "combat_value": 3, "sight": 3}, 16, 16)  # Odległość 12 (niewidoczny)
    
    # Dodaj jednostki do silnika
    engine.tokens = [german_scout, polish_close, polish_far, polish_medium]
    
    # Utwórz AI dowódcę
    ai_commander = LearningAICommander(ai_player, engine, difficulty='medium')
    
    print("\n🎯 KONFIGURACJA TESTOWA:")
    print(f"   AI Scout: {german_scout.id} na ({german_scout.q}, {german_scout.r})")
    print(f"   Zasięg widzenia: {german_scout.stats.get('sight', 5)}")
    print(f"   Polskie jednostki:")
    print(f"     - {polish_close.id} na ({polish_close.q}, {polish_close.r}) - odległość: {ai_commander._calculate_distance(german_scout, polish_close)}")
    print(f"     - {polish_medium.id} na ({polish_medium.q}, {polish_medium.r}) - odległość: {ai_commander._calculate_distance(german_scout, polish_medium)}")
    print(f"     - {polish_far.id} na ({polish_far.q}, {polish_far.r}) - odległość: {ai_commander._calculate_distance(german_scout, polish_far)}")
    
    print("\n🔍 TEST WYKRYWANIA WROGÓW Z FOG OF WAR:")
    print("-" * 50)
    enemy_units = ai_commander._get_enemy_units()
    
    print(f"\n📊 WYNIKI TESTU FOG OF WAR:")
    print(f"   ✅ AI wykryło {len(enemy_units)} widocznych wrogów")
    print(f"   ✅ Oczekiwane: 1 widoczny wróg (tylko Polish_Close)")
    
    if len(enemy_units) == 1:
        visible_enemy = enemy_units[0]
        if visible_enemy.id == "Polish_Close":
            print(f"   🎯 SUKCES: AI widzi tylko bliskiego wroga ({visible_enemy.id})")
            print(f"   🌫️ Fog of War DZIAŁA - dalekie jednostki są ukryte!")
        else:
            print(f"   ❌ BŁĄD: AI widzi złego wroga ({visible_enemy.id})")
    elif len(enemy_units) == 0:
        print(f"   ❌ BŁĄD: AI nie widzi żadnych wrogów (powinno widzieć 1)")
    else:
        print(f"   ❌ BŁĄD: AI widzi {len(enemy_units)} wrogów zamiast 1")
        print(f"   Lista widocznych wrogów:")
        for enemy in enemy_units:
            distance = ai_commander._calculate_distance(german_scout, enemy)
            print(f"     - {enemy.id} (odległość: {distance})")
    
    print("\n🎯 TEST PRÓBY ATAKU Z FOG OF WAR:")
    print("-" * 50)
    
    # Test próby ataku dla niemieckiego skauta
    print(f"\n🔫 Testowanie ataku dla jednostki: {german_scout.id}")
    
    # Symuluj próbę ataku
    try:
        result = ai_commander._try_legal_attack(german_scout)
        print(f"\n📊 WYNIK PRÓBY ATAKU Z FOG OF WAR:")
        print(f"   ✅ Metoda _try_legal_attack zwróciła: {result}")
        
        if result:
            print(f"   🎯 SUKCES: AI próbowało zaatakować widocznego wroga!")
        else:
            print(f"   ⚠️ INFO: AI nie zaatakowało (może brak zasięgu/MP)")
        
    except Exception as e:
        print(f"   ❌ BŁĄD podczas próby ataku: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎯 TEST RUCHU W KIERUNKU WIDOCZNEGO WROGA:")
    print("-" * 50)
    
    try:
        move_target = ai_commander._find_best_move_target(german_scout)
        print(f"\n📊 WYNIK WYSZUKIWANIA CELU RUCHU:")
        
        if move_target:
            print(f"   ✅ AI znalazło cel ruchu: {move_target}")
            print(f"   🎯 AI porusza się w kierunku widocznego wroga!")
        else:
            print(f"   ⚠️ INFO: AI nie znalazło celu ruchu")
            
    except Exception as e:
        print(f"   ❌ BŁĄD podczas wyszukiwania celu ruchu: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("🏁 TEST FOG OF WAR ZAKOŃCZONY")
    
    # Podsumowanie
    success = len(enemy_units) == 1 and (len(enemy_units) == 0 or enemy_units[0].id == "Polish_Close")
    if success:
        print("🎉 SUKCES: Fog of War działa poprawnie!")
    else:
        print("❌ PROBLEM: Fog of War wymaga poprawek!")

if __name__ == "__main__":
    test_fog_of_war()
