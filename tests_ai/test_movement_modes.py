#!/usr/bin/env python3
"""
TEST TRYBÓW RUCHU AI COMMANDER
Sprawdza czy AI rzeczywiście zmienia tryby ruchu jednostek
"""

import sys
import os

# Dodaj główny katalog gry do ścieżki
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from engine.engine import GameEngine
from engine.player import Player
from ai.ai_commander import AICommander
from engine.token import Token

def test_movement_modes():
    """Test czy AI Commander zmienia tryby ruchu"""
    print("🧪 TEST TRYBÓW RUCHU AI COMMANDER")
    print("=" * 50)
    
    # 1. SETUP - stwórz podstawową grę
    map_path = os.path.join(project_root, "data", "map_data.json")
    tokens_index = os.path.join(project_root, "assets", "tokens", "index.json")
    tokens_start = os.path.join(project_root, "assets", "start_tokens.json")
    
    game_engine = GameEngine(map_path, tokens_index, tokens_start)
    
    # Dodaj gracza AI (uproszczone)
    ai_player = Player(player_id=1, nation="Polska", role="AI Commander")
    game_engine.current_player = 1
    game_engine.current_player_obj = ai_player
    
    # 2. STWÓRZ TESTOWĄ JEDNOSTKĘ
    test_stats = {
        'move': 10,
        'defense_value': 5,
        'combat_value': 3,
        'maintenance': 20
    }
    
    test_token = Token(
        id="TEST_UNIT",
        owner="Polska_Player_1",
        stats=test_stats,
        q=10,
        r=10,
        movement_mode='combat'  # Start w trybie combat
    )
    
    # Dodaj do gry
    game_engine.tokens = [test_token]
    ai_player.visible_tokens = {test_token}
    
    print(f"✅ Utworzono testową jednostkę: {test_token.id}")
    print(f"📍 Pozycja: ({test_token.q}, {test_token.r})")
    print(f"🎯 Tryb ruchu początkowy: {test_token.movement_mode}")
    print(f"🚶 Punkty ruchu: {test_token.maxMovePoints}")
    
    # 3. TESTUJ FUNKCJE AI
    print("\n🧠 TESTOWANIE FUNKCJI AI...")
    
    # Test 1: scan_for_enemies
    from ai.ai_commander import scan_for_enemies
    unit_pos = (test_token.q, test_token.r)
    enemies = scan_for_enemies(unit_pos, game_engine, range=6)
    print(f"🔍 Wrogów w pobliżu: {len(enemies)}")
    
    # Test 2: choose_movement_mode
    from ai.ai_commander import choose_movement_mode
    unit_dict = {
        'id': test_token.id,
        'q': test_token.q,
        'r': test_token.r,
        'token': test_token,
        'mp': test_token.maxMovePoints,
        'fuel': getattr(test_token, 'currentFuel', 100)
    }
    
    target = (20, 5)  # Cel daleko (powinien wybrać 'march')
    chosen_mode = choose_movement_mode(unit_dict, target, game_engine)
    print(f"🎯 Wybrany tryb dla celu {target}: {chosen_mode}")
    
    # 4. SPRAWDŹ CZY TRYB SIĘ ZMIENIA
    print(f"\n🔧 TESTOWANIE ZMIANY TRYBU...")
    print(f"Tryb PRZED: {test_token.movement_mode}")
    
    # Symuluj zmianę trybu (jak w move_towards)
    if hasattr(test_token, 'movement_mode') and not getattr(test_token, 'movement_mode_locked', False):
        if test_token.movement_mode != chosen_mode:
            old_mode = test_token.movement_mode
            old_mp = test_token.maxMovePoints
            
            test_token.movement_mode = chosen_mode
            test_token.apply_movement_mode()
            
            new_mp = test_token.maxMovePoints
            
            print(f"✅ ZMIANA TRYBU: {old_mode} → {chosen_mode}")
            print(f"✅ ZMIANA MP: {old_mp} → {new_mp}")
            
            return True  # SUKCES!
        else:
            print(f"🔄 Tryb już ustawiony na: {chosen_mode}")
            return False  # Nie zmienił się
    else:
        print(f"❌ NIE MOŻNA ZMIENIĆ TRYBU")
        print(f"   hasattr movement_mode: {hasattr(test_token, 'movement_mode')}")
        print(f"   movement_mode_locked: {getattr(test_token, 'movement_mode_locked', 'BRAK')}")
        return False

def test_ai_commander_full():
    """Test pełnego cyklu AI Commander"""
    print("\n🤖 TEST PEŁNEGO AI COMMANDER")
    print("=" * 50)
    
    # Setup jak wyżej
    map_path = os.path.join(project_root, "data", "map_data.json")
    tokens_index = os.path.join(project_root, "assets", "tokens", "index.json")
    tokens_start = os.path.join(project_root, "assets", "start_tokens.json")
    
    game_engine = GameEngine(map_path, tokens_index, tokens_start)
    
    ai_player = Player(player_id=1, nation="Polska", role="AI Commander")
    game_engine.current_player = 1
    game_engine.current_player_obj = ai_player
    
    # Stwórz jednostkę
    test_stats = {'move': 10, 'defense_value': 5, 'combat_value': 3, 'maintenance': 20}
    test_token = Token(id="TEST_UNIT", owner="Polska_Player_1", stats=test_stats, q=10, r=10, movement_mode='combat')
    
    game_engine.tokens = [test_token]
    ai_player.visible_tokens = {test_token}
    
    # Uruchom AI Commander
    ai_commander = AICommander(ai_player)
    
    print(f"🎯 Tryb PRZED AI: {test_token.movement_mode}")
    
    try:
        # Uruchom turę AI
        ai_commander.play_turn(game_engine, player_id=1)
        print(f"🎯 Tryb PO AI: {test_token.movement_mode}")
        
        return test_token.movement_mode != 'combat'  # Czy się zmienił?
        
    except Exception as e:
        print(f"❌ BŁĄD AI: {e}")
        return False

if __name__ == "__main__":
    print("🚀 URUCHAMIANIE TESTÓW TRYBÓW RUCHU")
    print("=" * 60)
    
    # Test 1: Funkcje bezpośrednio
    test1_result = test_movement_modes()
    
    # Test 2: Pełny AI Commander  
    test2_result = test_ai_commander_full()
    
    # WYNIKI
    print("\n" + "=" * 60)
    print("📊 WYNIKI TESTÓW:")
    print(f"Test funkcji AI: {'✅ ZMIENIA TRYB' if test1_result else '❌ NIE ZMIENIA'}")
    print(f"Test pełnego AI: {'✅ ZMIENIA TRYB' if test2_result else '❌ NIE ZMIENIA'}")
    
    if test1_result and test2_result:
        print("\n🎉 SUKCES! AI Commander zmienia tryby ruchu!")
    elif test1_result and not test2_result:
        print("\n⚠️ Funkcje działają, ale pełny AI nie używa ich!")
    elif not test1_result and test2_result:
        print("\n🤔 Dziwne - AI zmienia tryb ale funkcje nie działają...")
    else:
        print("\n💥 PORAŻKA! AI Commander NIE zmienia trybów ruchu!")
    
    print("=" * 60)
