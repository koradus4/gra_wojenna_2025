#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rajdów AI z optymalizacją trybu ruchu na rzeczywistych danych
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.engine import GameEngine
from engine.save_manager import load_game
from ai.ai_commander import AICommander
from ai.rajdy_ai import opportunistic_capture_phase, evaluate_movement_mode_for_raid
import json

def test_rajdy_on_real_game():
    """Test rajdów AI na rzeczywistych danych gry"""
    
    print("🎯 TEST RAJDÓW AI NA RZECZYWISTYCH DANYCH")
    print("="*60)
    
    # Wczytaj zapisaną grę
    try:
        game_engine = GameEngine(
            "data/map_data.json",
            "assets/tokens/index.json", 
            "assets/start_tokens.json"
        )
        
        save_path = "saves/after_deployment.json"
        if not os.path.exists(save_path):
            print("❌ Brak zapisanej gry!")
            return
            
        print(f"📁 Wczytuję grę z: {save_path}")
        if load_game(save_path, game_engine):
            print("✅ Gra wczytana pomyślnie!")
        else:
            print("❌ Błąd wczytywania gry!")
            return
            
    except Exception as e:
        print(f"❌ Błąd inicjalizacji: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Sprawdź wszystkich graczy
    print("\n👥 GRACZE W GRZE:")
    print("-"*40)
    for i, player in enumerate(game_engine.players):
        is_ai = hasattr(player, 'is_ai_commander') or player.name.startswith('AI')
        role = "AI" if is_ai else "HUMAN"
        print(f"  {i+1}. {player.name} (ID: {player.player_id}) - {role}")
    
    # Sprawdź key pointy
    print("\n🗝️  KEY POINTY:")
    print("-"*40)
    kp_state = getattr(game_engine, 'key_points_state', {})
    if kp_state:
        for hex_id, kp in kp_state.items():
            value = kp.get('current_value', 0)
            owner = kp.get('owner', 'WOLNY')
            print(f"  {hex_id}: wartość={value}, właściciel={owner}")
    else:
        print("  ❌ Brak danych o key pointach!")
    
    # Sprawdź tokeny wszystkich graczy
    print("\n🪖 TOKENY NA MAPIE:")
    print("-"*40)
    player_tokens = {}
    for token in game_engine.tokens:
        pid = token.player_id
        if pid not in player_tokens:
            player_tokens[pid] = []
        player_tokens[pid].append(token)
    
    for pid, tokens in player_tokens.items():
        player_name = "UNKNOWN"
        for p in game_engine.players:
            if p.player_id == pid:
                player_name = p.name
                break
        print(f"  Gracz {pid} ({player_name}): {len(tokens)} tokenów")
        for token in tokens[:3]:  # Pokaż pierwsze 3
            mp = getattr(token, 'currentMovePoints', 0)
            fuel = getattr(token, 'currentFuel', 0)
            mode = getattr(token, 'movement_mode', 'unknown')
            print(f"    🪖 {token.id[:25]:25} pos=({token.q},{token.r}) MP={mp} Fuel={fuel} Mode={mode}")
    
    # Znajdź gracza AI
    ai_players = []
    for player in game_engine.players:
        if hasattr(player, 'is_ai_commander') or player.name.startswith('AI'):
            ai_players.append(player)
    
    if not ai_players:
        print("\n❌ Nie znaleziono graczy AI! Sprawdźmy czy są tokeny bez właściciela...")
        # Sprawdź czy są tokeny które mogłyby należeć do AI
        orphaned_tokens = [t for t in game_engine.tokens if t.player_id not in [p.player_id for p in game_engine.players]]
        if orphaned_tokens:
            print(f"  🔍 Znaleziono {len(orphaned_tokens)} tokenów bez właściciela")
        return
    
    for ai_player in ai_players:
        print(f"\n🤖 ANALIZA GRACZA AI: {ai_player.name}")
        print("="*50)
        
        # Utwórz AI Commander
        try:
            ai_commander = AICommander(game_engine, ai_player.player_id)
            game_engine.current_player_commander = ai_commander
            game_engine.current_player_obj = ai_player
        except Exception as e:
            print(f"❌ Błąd tworzenia AI Commander: {e}")
            continue
        
        # Pobierz jednostki AI
        ai_units = []
        for token in game_engine.tokens:
            if token.player_id == ai_player.player_id:
                unit_dict = {
                    'id': token.id,
                    'q': token.q,
                    'r': token.r,
                    'mp': getattr(token, 'currentMovePoints', 0),
                    'fuel': getattr(token, 'currentFuel', 0),
                    'base_mp': getattr(token, 'maxMovePoints', 0),
                    'token': token
                }
                ai_units.append(unit_dict)
        
        print(f"🎪 Jednostek AI: {len(ai_units)}")
        
        if not ai_units:
            print("❌ Brak jednostek AI!")
            continue
        
        # Pokaż stan jednostek
        print("\n📊 STAN JEDNOSTEK AI:")
        print("-"*40)
        for unit in ai_units:
            mp = unit.get('mp', 0)
            fuel = unit.get('fuel', 0)
            zasieg = min(mp, fuel)
            tryb = getattr(unit.get('token'), 'movement_mode', 'unknown')
            print(f"🪖 {unit['id'][:25]:25} MP={mp:2} Fuel={fuel:2} Zasięg={zasieg:2} Tryb={tryb}")
        
        # Sprawdź warunki rajdów
        print("\n🔍 ANALIZA WARUNKÓW RAJDÓW:")
        print("-"*40)
        
        # 1. Czy są wolne key pointy?
        free_kps = []
        if kp_state:
            for hex_id, kp in kp_state.items():
                if kp.get('current_value', 0) > 0:
                    try:
                        q, r = map(int, hex_id.split(','))
                        # Sprawdź czy nie jest zajęty przez żaden token
                        occupied = False
                        for t in game_engine.tokens:
                            if t.q == q and t.r == r:
                                occupied = True
                                break
                        if not occupied:
                            free_kps.append((hex_id, q, r, kp))
                    except Exception:
                        continue
        
        print(f"  🗝️  Wolne key pointy: {len(free_kps)}")
        for hex_id, q, r, kp in free_kps:
            value = kp.get('current_value', 0)
            print(f"    {hex_id} ({q},{r}): wartość={value}")
        
        # 2. Sprawdź zasięgi jednostek do celów
        print("\n  📏 ANALIZA ZASIĘGÓW:")
        for unit in ai_units[:5]:  # Pierwszych 5 jednostek
            unit_pos = (unit['q'], unit['r'])
            zasieg = min(unit['mp'], unit['fuel'])
            print(f"    🪖 {unit['id'][:20]:20} pos={unit_pos} zasięg={zasieg}")
            
            for hex_id, q, r, kp in free_kps[:3]:  # Pierwsze 3 cele
                try:
                    dist = game_engine.board.hex_distance(unit_pos, (q, r))
                    value = kp.get('current_value', 0)
                    score = value / dist if dist > 0 else 0
                    can_reach = dist <= zasieg
                    worthy = score >= 1.2  # FREE_KEYPOINT_VALUE_DISTANCE_FACTOR
                    
                    status = "✅" if (can_reach and worthy) else "❌"
                    print(f"      {status} Cel {hex_id}: dystans={dist}, wartość={value}, score={score:.2f}, może_dosięgnąć={can_reach}, opłacalny={worthy}")
                except Exception as e:
                    print(f"      ❌ Błąd analizy {hex_id}: {e}")
        
        # 3. Test rzeczywistych rajdów
        print("\n🚀 WYKONANIE RAJDÓW:")
        print("-"*40)
        
        try:
            captured = opportunistic_capture_phase(game_engine, ai_units, ai_player.player_id)
            print(f"✅ Rajdy zakończone! Przejęto {len(captured)} punktów:")
            if captured:
                for hex_id in captured:
                    print(f"  🏆 {hex_id}")
            else:
                print("  ⚠️  Brak przejętych punktów - sprawdź logi powyżej")
        except Exception as e:
            print(f"❌ Błąd wykonywania rajdów: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n🎊 ANALIZA ZAKOŃCZONA!")

if __name__ == "__main__":
    test_rajdy_on_real_game()
