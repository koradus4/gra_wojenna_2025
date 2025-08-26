#!/usr/bin/env python3
"""Test debugowania AI Commander resupply"""

import sys
sys.path.append('.')

from engine.engine import GameEngine
from ai.ai_commander import AICommander
from engine.player import Player

def test_resupply_debug():
    print('🔧 Testing AI Commander resupply...')
    
    try:
        # Użyj realnych danych
        engine = GameEngine(
            map_path='data/map_data.json',
            tokens_index_path='assets/tokens/index.json', 
            tokens_start_path='assets/start_tokens.json',
            seed=123
        )
        
        print(f'🔧 Engine loaded, tokens count: {len(engine.tokens)}')
        
        # Znajdź pierwszego gracza z tokenami
        player_found = None
        for token in engine.tokens[:5]:  # Sprawdź pierwsze 5
            if hasattr(token, 'owner') and token.owner:
                parts = token.owner.split('(')
                if len(parts) == 2:
                    nation = parts[1].replace(')', '').strip()
                    player_id = parts[0].strip()
                    print(f'🔧 Token {token.id}: owner="{token.owner}" -> id={player_id}, nation={nation}')
                    
                    if not player_found:
                        player_found = Player(int(player_id), nation, 'Dowódca', 5, '')
                        # Dodaj ekonomię
                        class MockEconomy:
                            def __init__(self):
                                self.economic_points = 100
                        player_found.economy = MockEconomy()
                        break
        
        if not player_found:
            print('❌ Nie znaleziono gracza z tokenami')
            return
        
        print(f'🔧 Testing with player: {player_found.nation} (id={player_found.id})')
        
        # Zmniejsz fuel w kilku tokenach dla testu
        tokens_modified = 0
        for token in engine.tokens:
            if hasattr(token, 'owner') and token.owner:
                if f"{player_found.id} ({player_found.nation})" in token.owner:
                    if hasattr(token, 'currentFuel') and hasattr(token, 'maxFuel'):
                        token.currentFuel = max(1, token.currentFuel // 2)  # Zmniejsz o połowę
                        print(f'🔧 Modified {token.id}: fuel -> {token.currentFuel}/{token.maxFuel}')
                        tokens_modified += 1
                        if tokens_modified >= 3:  # Wystarczy 3 tokeny
                            break
        
        # Test AI Commander
        ai = AICommander(player_found)
        ai.pre_resupply(engine)
        
    except Exception as e:
        print(f'❌ ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_resupply_debug()
