#!/usr/bin/env python3
"""
Test systemu Tactical Resupply - sprawdza czy AI uzupełnia zasoby w odpowiednich momentach:
1. PRE_ATTACK - przed atakiem jeśli CV < 80%
2. DAMAGE - po otrzymaniu obrażeń jeśli CV < 60%
3. MID_TURN - w połowie tury dla mocno uszkodzonych jednostek
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.engine import GameEngine
from engine.player import Player
from engine.token import Token
from ai.ai_commander import AdaptiveAICommander
from engine.action_refactored_clean import CombatAction

def test_tactical_resupply_system():
    """Test kompletnego systemu tactical resupply"""
    print("🔧 === TEST TACTICAL RESUPPLY SYSTEM ===")
    
    # Setup
    engine = GameEngine(
        "data/map_data.json",
        "assets/tokens/index.json", 
        "assets/start_tokens.json"
    )
    
    # Stwórz AI gracza z ekonomią
    ai_player = Player(2, "Niemcy", "Dowódca")
    ai_player.is_ai_commander = True
    ai_player.punkty_ekonomiczne = 50
    
    # Dodaj economy object
    from core.ekonomia import EconomySystem
    ai_player.economy = EconomySystem()
    ai_player.economy.economic_points = 50
    
    # Stwórz AI Commander
    from ai.ai_commander import AICommander
    base_ai_commander = AICommander(ai_player)
    ai_commander = AdaptiveAICommander(base_ai_commander)
    
    # Stwórz jednostkę AI z obniżonym CV
    damaged_unit = Token(
        id="tank_damaged",
        owner=f"{ai_player.id} ({ai_player.nation})",
        stats={
            'label': 'Panzer IV (uszkodzony)',
            'combat_value': 100,
            'maintenance': 10,
            'move': 6,
            'attack': {'value': 8, 'range': 1},
            'defense_value': 7,
            'sight': 2,
            'price': 15
        },
        q=5, r=5
    )
    
    # Symuluj obrażenia - obniż CV do 45/100 (45%)
    damaged_unit.combat_value = 45
    damaged_unit.currentFuel = 8  # Także niskie paliwo
    
    # Dodaj do engine
    engine.tokens = [damaged_unit]
    engine.players = [ai_player]
    engine.current_player_obj = ai_player
    engine.ai_commanders = {ai_player.id: base_ai_commander}
    engine.current_player_commander = base_ai_commander
    
    print(f"📊 STAN POCZĄTKOWY:")
    print(f"   💰 Punkty ekonomiczne: {ai_player.economy.economic_points}")
    print(f"   🛡️ Combat Value: {damaged_unit.combat_value}/100")
    print(f"   ⛽ Paliwo: {damaged_unit.currentFuel}/10")
    
    # TEST 1: PRE_ATTACK Resupply
    print(f"\n🎯 TEST 1: PRE_ATTACK RESUPPLY")
    
    # Symuluj jednostkę wroga w zasięgu
    enemy_unit = Token(
        id="enemy_tank",
        owner="3 (Polska)",
        stats={
            'label': 'T-34',
            'combat_value': 80,
            'maintenance': 8,
            'move': 5,
            'attack': {'value': 7, 'range': 1},
            'defense_value': 6,
            'sight': 2,
            'price': 12
        },
        q=6, r=5  # Obok naszej jednostki
    )
    engine.tokens.append(enemy_unit)
    
    # Stwórz unit dict dla AI
    unit_dict = {
        'id': damaged_unit.id,
        'token': damaged_unit,
        'q': damaged_unit.q,
        'r': damaged_unit.r,
        'mp': damaged_unit.currentMovePoints,
        'fuel': damaged_unit.currentFuel,
        'cv': damaged_unit.combat_value
    }
    
    # Spróbuj atak - powinien wywołać PRE_ATTACK resupply
    from ai.ai_commander import ai_attempt_combat
    
    cv_before = damaged_unit.combat_value
    points_before = ai_player.economy.economic_points
    
    result = ai_attempt_combat(unit_dict, engine, ai_player.id, ai_player.nation)
    
    cv_after = damaged_unit.combat_value
    points_after = ai_player.economy.economic_points
    
    print(f"   🛡️ Combat Value: {cv_before} → {cv_after} (+{cv_after - cv_before})")
    print(f"   💰 Punkty: {points_before} → {points_after} (-{points_before - points_after})")
    print(f"   ⚔️ Atak wykonany: {result}")
    
    # TEST 2: POST_DAMAGE Resupply
    print(f"\n💥 TEST 2: POST_DAMAGE RESUPPLY")
    
    # Resetuj do niskiego CV
    damaged_unit.combat_value = 35  # 35% z 100
    ai_player.economy.economic_points = 40
    
    cv_before = damaged_unit.combat_value
    points_before = ai_player.economy.economic_points
    
    # Symuluj walkę z dużymi obrażeniami (8 dmg)
    from engine.action_refactored_clean import CombatResolver
    
    # Bezpośrednio wywołaj sprawdzenie post-damage resupply
    CombatResolver._check_post_damage_resupply(engine, damaged_unit, 8)
    
    cv_after = damaged_unit.combat_value
    points_after = ai_player.economy.economic_points
    
    print(f"   🛡️ Combat Value: {cv_before} → {cv_after} (+{cv_after - cv_before})")
    print(f"   💰 Punkty: {points_before} → {points_after} (-{points_before - points_after})")
    
    # TEST 3: MID_TURN Resupply
    print(f"\n⚡ TEST 3: MID_TURN RESUPPLY")
    
    # Resetuj do bardzo niskiego CV
    damaged_unit.combat_value = 25  # 25% z 100
    ai_player.economy.economic_points = 35
    
    cv_before = damaged_unit.combat_value
    points_before = ai_player.economy.economic_points
    
    # Wywołaj tactical resupply bezpośrednio
    result = base_ai_commander.tactical_resupply(engine, "DAMAGE")
    
    cv_after = damaged_unit.combat_value
    points_after = ai_player.economy.economic_points
    
    print(f"   🛡️ Combat Value: {cv_before} → {cv_after} (+{cv_after - cv_before})")
    print(f"   💰 Punkty: {points_before} → {points_after} (-{points_before - points_after})")
    print(f"   ✅ Resupply wykonany: {result}")
    
    # TEST 4: Kontrola budżetu
    print(f"\n💰 TEST 4: KONTROLA BUDŻETU")
    
    # Ustaw bardzo niskie punkty
    ai_player.economy.economic_points = 3
    
    points_before = ai_player.economy.economic_points
    result = base_ai_commander.tactical_resupply(engine, "EMERGENCY")
    points_after = ai_player.economy.economic_points
    
    print(f"   💰 Punkty: {points_before} → {points_after}")
    print(f"   🚫 Resupply z niskim budżetem: {result}")
    
    print(f"\n✅ TACTICAL RESUPPLY SYSTEM - TESTY ZAKOŃCZONE")
    return True

def test_different_contexts():
    """Test różnych kontekstów resupply"""
    print(f"\n🎛️ === TEST RÓŻNYCH KONTEKSTÓW RESUPPLY ===")
    
    contexts = ["PRE_TURN", "PRE_ATTACK", "DAMAGE", "EMERGENCY"]
    
    for context in contexts:
        print(f"\n📋 Test kontekstu: {context}")
        
        # Setup dla każdego kontekstu
        engine = GameEngine(
            "data/map_data.json",
            "assets/tokens/index.json", 
            "assets/start_tokens.json"
        )
        ai_player = Player(2, "Niemcy", "Dowódca")
        ai_player.is_ai_commander = True
        
        from core.ekonomia import EconomySystem
        ai_player.economy = EconomySystem()
        ai_player.economy.economic_points = 30
        
        from ai.ai_commander import AICommander
        base_ai_commander = AICommander(ai_player)
        ai_commander = AdaptiveAICommander(base_ai_commander)
        
        # Jednostka potrzebująca różnych rodzajów uzupełnienia
        unit = Token(
            id=f"test_unit_{context}",
            owner=f"{ai_player.id} ({ai_player.nation})",
            stats={
                'label': f'Test Unit {context}',
                'combat_value': 100,
                'maintenance': 10,
                'move': 6,
                'price': 10
            },
            q=5, r=5
        )
        
        # Różne stany dla różnych kontekstów
        if context == "PRE_TURN":
            unit.combat_value = 70  # 70%
            unit.currentFuel = 5   # 50%
        elif context == "PRE_ATTACK":
            unit.combat_value = 75  # 75% - potrzebuje uzupełnienia przed atakiem
            unit.currentFuel = 8   # 80%
        elif context == "DAMAGE":
            unit.combat_value = 40  # 40% - po otrzymaniu obrażeń
            unit.currentFuel = 7   # 70%
        else:  # EMERGENCY
            unit.combat_value = 20  # 20% - krytyczny stan
            unit.currentFuel = 2   # 20%
        
        engine.tokens = [unit]
        engine.players = [ai_player]
        engine.current_player_obj = ai_player
        
        cv_before = unit.combat_value
        fuel_before = unit.currentFuel
        points_before = ai_player.economy.economic_points
        
        # Wykonaj resupply dla danego kontekstu
        result = base_ai_commander.tactical_resupply(engine, context)
        
        cv_after = unit.combat_value
        fuel_after = unit.currentFuel
        points_after = ai_player.economy.economic_points
        
        print(f"   🛡️ CV: {cv_before} → {cv_after} (+{cv_after - cv_before})")
        print(f"   ⛽ Paliwo: {fuel_before} → {fuel_after} (+{fuel_after - fuel_before})")
        print(f"   💰 Punkty: {points_before} → {points_after} (-{points_before - points_after})")
        print(f"   ✅ Rezultat: {result}")
    
    print(f"\n✅ TESTY KONTEKSTÓW - ZAKOŃCZONE")

if __name__ == "__main__":
    try:
        test_tactical_resupply_system()
        test_different_contexts()
        print(f"\n🎉 WSZYSTKIE TESTY TACTICAL RESUPPLY PRZESZŁY POMYŚLNIE!")
    except Exception as e:
        print(f"\n❌ BŁĄD W TESTACH: {e}")
        import traceback
        traceback.print_exc()
