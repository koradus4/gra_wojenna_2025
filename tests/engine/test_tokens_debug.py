#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test debugowania tokenów dla AI Dowódcy
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

    # AI Commander
    commander = Player(2, 'Polska', 'Dowódca', 300)
    commander.economy = EconomySystem()
    commander.commander = AIFieldCommander(commander, difficulty='medium', debug_mode=True)  

    # Dodaj do engine
    game_engine.players = [commander]

    print('=== ANALIZA TOKENÓW DLA AI DOWÓDCY ===')
    print('Wszystkich tokenów w grze:', len(game_engine.tokens))
    
    # Sprawdź context
    context = commander.commander.get_decision_context(game_engine)
    print('Own tokens w context:', len(context['own_tokens']))
    print('Enemy tokens w context:', len(context['enemy_tokens']))
    
    print()
    print('PLAYER INFO:')
    print('  ID:', commander.id)
    print('  Nation:', commander.nation)
    print('  Role:', commander.role)
    print('  Name:', commander.name)
    
    # Sprawdź expected owner
    expected_owner = f'{commander.id} ({commander.nation})'
    print()
    print('Expected owner:', expected_owner)
    
    # Sprawdź czy są tokeny dla tego gracza
    print()
    print('ANALIZA PIERWSZYCH 10 TOKENÓW:')
    matching = 0
    for i, token in enumerate(game_engine.tokens[:10]):
        nation = getattr(token, 'nation', 'BRAK')
        matches = 'MATCH!' if token.owner == expected_owner else ''
        if token.owner == expected_owner:
            matching += 1
        print(f'  Token {i}: owner="{token.owner}", nation="{nation}" {matches}')
    
    print()
    print('SPRAWDZENIE WSZYSTKICH WŁAŚCICIELI:')
    all_owners = set(token.owner for token in game_engine.tokens)
    for owner in sorted(all_owners):
        count = sum(1 for t in game_engine.tokens if t.owner == owner)
        match_str = ' <-- TO NASZ GRACZ!' if owner == expected_owner else ''
        print(f'  "{owner}": {count} tokenów{match_str}')
    
    print()
    print('PODSUMOWANIE:')
    print('  Matching tokens dla naszego gracza:', matching)
    print('  Total tokens:', len(game_engine.tokens))
    
    if matching == 0:
        print()
        print('❌ PROBLEM: AI Dowódca nie ma żadnych jednostek do sterowania!')
        print('   Dlatego nie podejmuje decyzji o ruchu/walce.')

except Exception as e:
    print('Błąd:', e)
    import traceback
    traceback.print_exc()
