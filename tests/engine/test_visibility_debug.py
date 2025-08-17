#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug get_visible_tokens - sprawdzanie widoczności
"""

from engine.player import Player
from ai.commanders.ai_field_commander import AIFieldCommander  
from core.ekonomia import EconomySystem
from engine.engine import GameEngine
from engine.board import Board

try:
    # Game engine
    board = Board('data/map_data.json')
    game_engine = GameEngine(
        'data/map_data.json',
        'assets/tokens/index.json', 
        'assets/start_tokens.json',
        seed=42,
        read_only=True
    )

    # Polski AI Dowódca
    pl_commander = Player(2, 'Polska', 'Dowódca', 300)
    pl_commander.economy = EconomySystem()
    pl_commander.commander = AIFieldCommander(pl_commander, difficulty='medium', debug_mode=True)  

    # Niemiecki AI Dowódca
    de_commander = Player(5, 'Niemcy', 'Dowódca', 300)
    de_commander.economy = EconomySystem()
    de_commander.commander = AIFieldCommander(de_commander, difficulty='medium', debug_mode=True)

    # Dodaj do engine
    game_engine.players = [pl_commander, de_commander]

    print('=== DEBUG WIDOCZNOŚCI TOKENÓW ===')
    
    print(f'Total tokenów w grze: {len(game_engine.tokens)}')
    
    # Test visible tokens dla polskiego dowódcy
    print(f'\n🇵🇱 POLSKI DOWÓDCA (ID={pl_commander.id}, Nation={pl_commander.nation}):')
    visible_tokens_pl = pl_commander.commander.get_visible_tokens(game_engine)
    print(f'  Widocznych tokenów: {len(visible_tokens_pl)}')
    
    # Sprawdź wszystkich właścicieli widocznych tokenów
    pl_expected = f"{pl_commander.id} ({pl_commander.nation})"
    print(f'  Expected owner: "{pl_expected}"')
    
    owners_count = {}
    for token in visible_tokens_pl:
        owner = token.owner
        owners_count[owner] = owners_count.get(owner, 0) + 1
    
    print(f'  Widoczni właściciele:')
    for owner, count in sorted(owners_count.items()):
        is_own = '(OWN)' if owner == pl_expected else ''
        is_same_nation = '(SAME_NATION)' if pl_commander.nation in owner else ''
        is_enemy_nation = '(ENEMY_NATION)' if pl_commander.nation not in owner else ''
        print(f'    "{owner}": {count} tokenów {is_own}{is_same_nation}{is_enemy_nation}')
    
    # Ręczny test enemy detection
    print(f'\n  Ręczny test wykrywania wrogów:')
    manual_enemies = []
    for token in visible_tokens_pl:
        if token.owner != pl_expected:
            # Jest to wróg?
            if pl_commander.nation not in token.owner:  # Inna nacja
                manual_enemies.append(token)
    
    print(f'    Ręcznie wykrytych wrogów: {len(manual_enemies)}')
    for enemy in manual_enemies[:3]:
        print(f'      - {getattr(enemy, "id", "BRAK")} owner="{enemy.owner}"')

except Exception as e:
    print('Błąd:', e)
    import traceback
    traceback.print_exc()
