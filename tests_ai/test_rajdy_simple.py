#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uproszczony test rajdów AI - sprawdź dlaczego nie działają
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.engine import GameEngine
from engine.player import Player
from ai.ai_commander import AICommander
from ai.rajdy_ai import opportunistic_capture_phase, evaluate_movement_mode_for_raid
import json

def simple_rajdy_test():
    """Uproszczony test rajdów bez wczytywania zapisu"""
    
    print("🎯 UPROSZCZONY TEST RAJDÓW AI")
    print("="*50)
    
    try:
        # Inicjalizuj silnik gry
        game_engine = GameEngine(
            "data/map_data.json",
            "assets/tokens/index.json", 
            "assets/start_tokens.json"
        )
        print("✅ GameEngine zainicjalizowany")
        
        # Sprawdź tokeny
        print(f"🪖 Tokenów na mapie: {len(game_engine.tokens)}")
        
        # Sprawdź key pointy
        kp_state = getattr(game_engine, 'key_points_state', {})
        print(f"🗝️  Key pointów: {len(kp_state)}")
        
        # Pokaż pierwsze tokeny
        print("\n📊 PIERWSZE TOKENY:")
        print("-"*40)
        for i, token in enumerate(game_engine.tokens[:5]):
            mp = getattr(token, 'currentMovePoints', 0)
            fuel = getattr(token, 'currentFuel', 0)
            mode = getattr(token, 'movement_mode', 'unknown')
            owner = getattr(token, 'owner', 'unknown')
            print(f"  {i+1}. {token.id[:30]:30} MP={mp} Fuel={fuel} Owner={owner} Mode={mode}")
        
        # Pokaż pierwsze key pointy
        print("\n🗝️  PIERWSZE KEY POINTY:")
        print("-"*40)
        for i, (hex_id, kp) in enumerate(list(kp_state.items())[:5]):
            value = kp.get('current_value', 0)
            initial = kp.get('initial_value', 0)
            kp_type = kp.get('type', 'unknown')
            print(f"  {i+1}. {hex_id}: wartość={value} (początkowa={initial}) typ={kp_type}")
        
        # Sprawdź czy są wolne key pointy
        print("\n🔍 ANALIZA WOLNYCH KEY POINTÓW:")
        print("-"*40)
        
        free_kps = []
        for hex_id, kp in kp_state.items():
            if kp.get('current_value', 0) > 0:
                try:
                    q, r = map(int, hex_id.split(','))
                    # Sprawdź czy nie jest zajęty
                    occupied = False
                    for token in game_engine.tokens:
                        if token.q == q and token.r == r:
                            occupied = True
                            break
                    if not occupied:
                        free_kps.append((hex_id, q, r, kp))
                except Exception:
                    continue
        
        print(f"Wolnych key pointów: {len(free_kps)}")
        for hex_id, q, r, kp in free_kps[:10]:  # Pokaż pierwszych 10
            value = kp.get('current_value', 0)
            print(f"  {hex_id} ({q},{r}): wartość={value}")
        
        # Stwórz testowego gracza AI
        print("\n🤖 TWORZENIE TESTOWEGO GRACZA AI:")
        print("-"*40)
        
        # Znajdź tokeny do przypisania AI (np. te z owner="unknown" lub wybierz pierwsze)
        ai_tokens = []
        for token in game_engine.tokens:
            if hasattr(token, 'owner') and ('AI' in str(token.owner) or 'unknown' in str(token.owner).lower()):
                ai_tokens.append(token)
        
        if not ai_tokens:
            # Weź pierwsze 5 tokenów dla testu
            ai_tokens = game_engine.tokens[:5]
            print(f"⚠️  Brak tokenów AI, używam pierwszych {len(ai_tokens)} tokenów")
        else:
            print(f"✅ Znaleziono {len(ai_tokens)} tokenów AI")
        
        # Stwórz gracza AI
        ai_player = Player("AI_Test", 999, "AI")  # ID 999 dla testu
        ai_commander = AICommander(ai_player)
        
        # Przypisz tokeny do AI
        for token in ai_tokens:
            token.player_id = 999
        
        # Stwórz unit dicts z PRAWDZIWYM PALIWEM (bez zwiększania)
        ai_units = []
        for token in ai_tokens:
            unit_dict = {
                'id': token.id,
                'q': token.q,
                'r': token.r,
                'mp': getattr(token, 'currentMovePoints', 3),
                'fuel': getattr(token, 'currentFuel', 2),  # Użyj prawdziwego paliwa
                'base_mp': getattr(token, 'maxMovePoints', 6),
                'token': token
            }
            ai_units.append(unit_dict)
        
        print(f"✅ Przygotowano {len(ai_units)} jednostek AI do testu (PRAWDZIWE PALIWO)")
        
        # Test funkcji oceny trybu ruchu
        print("\n🧠 TEST FUNKCJI OCENY TRYBU RUCHU:")
        print("-"*40)
        
        if ai_units and free_kps:
            test_unit = ai_units[0]
            test_targets = [(kp[1], kp[2]) for kp in free_kps[:3]]  # Pierwsze 3 cele
            
            print(f"Testowa jednostka: {test_unit['id'][:30]}")
            for target in test_targets:
                try:
                    optimal_mode, optimal_mp = evaluate_movement_mode_for_raid(test_unit, target, game_engine)
                    dist = game_engine.board.hex_distance((test_unit['q'], test_unit['r']), target)
                    print(f"  Cel {target}: dystans={dist}, tryb={optimal_mode}, MP={optimal_mp}")
                except Exception as e:
                    print(f"  ❌ Błąd dla {target}: {e}")
        
        # Test rzeczywistych rajdów
        print("\n🚀 TEST RZECZYWISTYCH RAJDÓW:")
        print("-"*40)
        
        game_engine.current_player_commander = ai_commander
        game_engine.current_player_obj = ai_player
        
        try:
            # TURA 1: Test z nową logiką wieloturową
            captured = opportunistic_capture_phase(game_engine, ai_units, 999)
            print(f"✅ TURA 1 - Rajdy wykonane! Wynik: {len(captured)} przejętych punktów")
            if captured:
                for hex_id in captured:
                    print(f"  🏆 Przejęto natychmiast: {hex_id}")
            
            # Sprawdź ile jednostek ma assigned_target (plany wieloturowe)
            multiturn_plans = 0
            for unit in ai_units:
                if unit.get('assigned_target'):
                    multiturn_plans += 1
                    print(f"  📋 Plan wieloturowy: {unit.get('id', 'UNKNOWN')[:30]} → {unit['assigned_target']}")
            
            print(f"📋 Planów wieloturowych: {multiturn_plans}")
            print(f"🏆 Natychmiastowych przejęć: {len(captured)}")
            
            if multiturn_plans > 0:
                print("\n🔄 SYMULACJA TURY 2:")
                print("-"*40)
                
                # Resetuj moved_capture flag dla symulacji następnej tury
                for unit in ai_units:
                    unit.pop('moved_capture', None)
                
                # Symuluj uzupełnienie paliwa na początku tury
                for unit in ai_units:
                    token = unit.get('token')
                    if token:
                        token.currentFuel = min(token.currentFuel + 2, unit.get('base_mp', 6) + 3)  # Symulacja uzupełnienia
                        unit['fuel'] = token.currentFuel
                
                # Uruchom ponownie rajdy (symulacja tury 2)
                captured_turn2 = opportunistic_capture_phase(game_engine, ai_units, 999)
                
                print(f"✅ TURA 2 - Rajdy wykonane! Wynik: {len(captured_turn2)} przejętych punktów")
                if captured_turn2:
                    for hex_id in captured_turn2:
                        print(f"  🏆 Przejęto w turze 2: {hex_id}")
                
                # Sprawdź pozostałe plany
                remaining_plans = 0
                for unit in ai_units:
                    if unit.get('assigned_target'):
                        remaining_plans += 1
                        print(f"  📋 Pozostały plan: {unit.get('id', 'UNKNOWN')[:30]} → {unit['assigned_target']}")
                
                print(f"📋 Pozostałych planów: {remaining_plans}")
                print(f"🎯 CAŁKOWITY WYNIK: {len(captured)} (tura 1) + {len(captured_turn2)} (tura 2) = {len(captured) + len(captured_turn2)} przejęć")
            else:
                print("  ⚠️  Brak planów wieloturowych - sprawdź warunki")
                
        except Exception as e:
            print(f"❌ Błąd rajdów: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎊 TEST ZAKOŃCZONY!")

if __name__ == "__main__":
    simple_rajdy_test()
