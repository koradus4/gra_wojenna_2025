#!/usr/bin/env python3
"""Test debugowania AI General alokacji punktów"""

import sys
sys.path.append('.')

from engine.engine import GameEngine
from ai.ai_general import AIGeneral
from engine.player import Player

def test_ai_general_allocation():
    print('🔧 Testing AI General allocation...')
    
    try:
        # Użyj realnych danych
        engine = GameEngine(
            map_path='data/map_data.json',
            tokens_index_path='assets/tokens/index.json', 
            tokens_start_path='assets/start_tokens.json',
            seed=123
        )
        
        print(f'🔧 Engine loaded, tokens count: {len(engine.tokens)}')
        
        # Znajdź graczy polskich  
        polish_general = None
        polish_commanders = []
        
        # Utwórz generała polskiego ręcznie (id=1)
        polish_general = Player(1, 'Polska', 'Generał', 5, '')
        class MockEconomy:
            def __init__(self):
                self.economic_points = 200
            def get_points(self):
                return {'economic_points': self.economic_points}
            def generate_economic_points(self):
                pass
            def add_special_points(self):
                pass
        polish_general.economy = MockEconomy()
        polish_general.is_ai = True
        print(f'🔧 Created Polish General: {polish_general.nation} (id={polish_general.id}) with 200 PE')
        
        # Znajdź dowódców polskich z tokenów
        for token in engine.tokens[:15]:  # Sprawdź pierwsze 15
            if hasattr(token, 'owner') and token.owner and 'Polska' in token.owner:
                parts = token.owner.split('(')
                if len(parts) == 2:
                    nation = parts[1].replace(')', '').strip()
                    player_id = int(parts[0].strip())
                    
                    # Znajdź dowódców polskich (id=2,3)
                    if player_id in [2, 3] and not any(cmd.id == player_id for cmd in polish_commanders):
                        commander = Player(player_id, nation, 'Dowódca', 5, '')
                        class MockEconomy:
                            def __init__(self):
                                self.economic_points = 10  # Małe punkty przed alokacją
                            def get_points(self):
                                return {'economic_points': self.economic_points}
                        commander.economy = MockEconomy()
                        commander.is_ai_commander = True
                        polish_commanders.append(commander)
                        print(f'🔧 Created Polish Commander: {commander.nation} (id={commander.id}) with 10 PE')
                    
                    if len(polish_commanders) == 2:  # Mamy już 2 dowódców
                        break
        
        if not polish_general:
            print('❌ Nie znaleziono generała polskiego')
            return
            
        if not polish_commanders:
            print('❌ Nie znaleziono dowódców polskich')
            return
        
        # Dodaj graczy do silnika
        all_players = [polish_general] + polish_commanders
        engine.players = all_players
        engine.current_player_obj = polish_general
        
        print(f'🔧 Setup: General ma {polish_general.economy.economic_points} PE')
        for cmd in polish_commanders:
            print(f'🔧 Setup: Commander {cmd.id} ma {cmd.economy.economic_points} PE')
        
        # Test AI General
        ai_general = AIGeneral("polish")
        ai_general.make_turn(engine)
        
        print(f'🔧 After AI turn: General ma {polish_general.economy.economic_points} PE')
        for cmd in polish_commanders:
            print(f'🔧 After AI turn: Commander {cmd.id} ma {cmd.economy.economic_points} PE')
        
    except Exception as e:
        print(f'❌ ERROR: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_general_allocation()
