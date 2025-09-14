#!/usr/bin/env python3
"""
🔥 TEST COMBAT - POPRAWIONE MAPOWANIE GRACZY
Testuje czy AI z aggressive profilem będzie atakować
"""

from engine.engine import GameEngine
from engine.player import Player
from ai.ai_config import set_player_ai_profile, AIProfile, get_param
from ai.walka_ai import ai_attempt_combat
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')

def test_combat_with_correct_players():
    """Test combatu z poprawnymi ID graczy"""
    
    print("🔥 TEST COMBAT - POPRAWIONE MAPOWANIE")
    print("="*50)
    
    # Tworzymy GameEngine
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json",
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=False  # Nie read-only żeby mogły być walki
    )
    
    # POPRAWIONE MAPOWANIE - zgodnie z rzeczywistymi graczami na mapie
    # Polska dowódcy: 2, 3 = aggressive (próg ataku 0.72)
    # Niemiecki dowódcy: 5, 6 = defensive (próg ataku 1.68)
    set_player_ai_profile(2, AIProfile.AGGRESSIVE)  # Polska dowódca 1
    set_player_ai_profile(3, AIProfile.AGGRESSIVE)  # Polska dowódca 2
    set_player_ai_profile(5, AIProfile.DEFENSIVE)   # German dowódca 1  
    set_player_ai_profile(6, AIProfile.DEFENSIVE)   # German dowódca 2
    
    print("✅ Profile ustawione:")
    print(f"   Gracz 2 (Polska): aggressive → próg {get_param('COMBAT.MINIMUM_ATTACK_RATIO', 1.2, player_id=2)}")
    print(f"   Gracz 3 (Polska): aggressive → próg {get_param('COMBAT.MINIMUM_ATTACK_RATIO', 1.2, player_id=3)}")
    print(f"   Gracz 5 (Niemcy): defensive → próg {get_param('COMBAT.MINIMUM_ATTACK_RATIO', 1.2, player_id=5)}")
    print(f"   Gracz 6 (Niemcy): defensive → próg {get_param('COMBAT.MINIMUM_ATTACK_RATIO', 1.2, player_id=6)}")
    
    # Sprawdźmy jednostki każdego gracza
    players_units = {}
    for token in game_engine.tokens:
        owner = token.owner
        if owner not in players_units:
            players_units[owner] = []
        players_units[owner].append(token)
    
    print(f"\n📊 Jednostki per gracz:")
    for owner, units in players_units.items():
        print(f"   {owner}: {len(units)} jednostek")
    
    # Testujemy combat dla każdego gracza
    print(f"\n🎯 TESTOWANIE COMBAT:")
    
    combat_attempts = 0
    for token in game_engine.tokens:
        # Wyciągnij player_id z ownera (np "2 (Polska)" → 2)
        owner_parts = token.owner.split(' ')
        if owner_parts[0].isdigit():
            player_id = int(owner_parts[0])
            
            # Tylko dla graczy z profilami 
            if player_id in [2, 3, 5, 6]:
                print(f"\n🔍 Testuje combat dla jednostki {token.id} (gracz {player_id}):")
                
                # Sprawdź próg ataku dla tego gracza
                threshold = get_param('COMBAT.MINIMUM_ATTACK_RATIO', 1.2, player_id=player_id)
                print(f"   📊 Próg ataku: {threshold}")
                
                # Przygotuj unit dict dla ai_attempt_combat
                unit_dict = {
                    'id': token.id,
                    'token': token,
                    'q': token.q,
                    'r': token.r
                }
                
                # Testuj combat
                combat_attempts += 1
                result = ai_attempt_combat(unit_dict, game_engine, player_id)
                print(f"   ⚔️ Wynik combat: {result}")
                
                if combat_attempts >= 5:  # Ograniczmy do 5 prób żeby nie spamować
                    break
    
    return game_engine

if __name__ == "__main__":
    game = test_combat_with_correct_players()