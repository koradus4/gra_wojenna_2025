#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST: Jakie rozkazy dostaje AI Commander w praktyce
"""

import sys
import os
import json
from pathlib import Path

# Dodaj ścieżkę do głównego folderu projektu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander

def create_mock_game_engine():
    """Tworzy mock game_engine z realistycznymi danymi"""
    
    # Mock players - Polscy dowódcy (ID 2, 3) i niemieccy (ID 5, 6)
    players = []
    
    # Polski generał (ID 1)
    players.append(type('obj', (), {
        'id': 1, 'nation': 'Polska', 'role': 'Generał',
        'economy': type('obj', (), {
            'get_points': lambda: {'economic_points': 80, 'special_points': 10}
        })()
    })())
    
    # Polscy dowódcy
    players.append(type('obj', (), {'id': 2, 'nation': 'Polska', 'role': 'Dowódca'})())
    players.append(type('obj', (), {'id': 3, 'nation': 'Polska', 'role': 'Dowódca'})())
    
    # Niemieccy gracze
    players.append(type('obj', (), {'id': 4, 'nation': 'Niemcy', 'role': 'Generał'})())
    players.append(type('obj', (), {'id': 5, 'nation': 'Niemcy', 'role': 'Dowódca'})())
    players.append(type('obj', (), {'id': 6, 'nation': 'Niemcy', 'role': 'Dowódca'})())
    
    # Mock tokens dla polskich dowódców
    tokens = []
    
    # Jednostki dla dowódcy ID=2 (na pozycjach [8,4] i [9,5])
    tokens.append(type('obj', (), {
        'id': 'polish_infantry_1', 'owner': '2 (Polska)', 'q': 8, 'r': 4,
        'currentMovePoints': 3, 'currentFuel': 8, 'combat_value': 4
    })())
    tokens.append(type('obj', (), {
        'id': 'polish_tank_1', 'owner': '2 (Polska)', 'q': 9, 'r': 5,
        'currentMovePoints': 4, 'currentFuel': 6, 'combat_value': 6
    })())
    
    # Jednostki dla dowódcy ID=3 (na pozycjach [12,8] i [13,9])
    tokens.append(type('obj', (), {
        'id': 'polish_artillery_1', 'owner': '3 (Polska)', 'q': 12, 'r': 8,
        'currentMovePoints': 2, 'currentFuel': 5, 'combat_value': 8
    })())
    tokens.append(type('obj', (), {
        'id': 'polish_recon_1', 'owner': '3 (Polska)', 'q': 13, 'r': 9,
        'currentMovePoints': 5, 'currentFuel': 9, 'combat_value': 2
    })())
    
    # Mock board z prostym pathfinding
    board = type('obj', (), {
        'find_path': lambda start, end, **kwargs: [start, end] if start != end else [start],
        'is_occupied': lambda q, r: False,
        'neighbors': lambda q, r: [(q+1,r), (q-1,r), (q,r+1), (q,r-1)]
    })()
    
    # Mock key points
    key_points_state = {
        '15_-7': {'position': [15, -7], 'value': 100, 'type': 'miasto', 'controlled_by': None},
        '28_3': {'position': [28, 3], 'value': 75, 'type': 'węzeł', 'controlled_by': None},
        '43_-14': {'position': [43, -14], 'value': 150, 'type': 'fortyfikacja', 'controlled_by': None}
    }
    
    # Mock game engine
    game_engine = type('obj', (), {
        'players': players,
        'tokens': tokens,
        'board': board,
        'key_points_state': key_points_state,
        'current_player_obj': players[0],  # Polski generał
        'turn_number': 3,
        'current_turn': 3
    })()
    
    return game_engine

def test_orders_generation():
    """Test 1: AI General wydaje rozkazy"""
    print("🎯 === TEST 1: AI GENERAL WYDAJE ROZKAZY ===")
    
    # Stwórz AI General dla Polski
    ai_general = AIGeneral("polish")
    
    # Mock game engine
    game_engine = create_mock_game_engine()
    
    # Wydaj rozkazy
    print("📋 AI General wydaje rozkazy...")
    orders = ai_general.issue_strategic_orders(
        game_engine=game_engine, 
        current_turn=3
    )
    
    if orders:
        print("✅ Rozkazy wydane pomyślnie!")
        print(f"📊 Strategia: {orders.get('strategy_type', 'UNKNOWN')}")
        print(f"🔢 Tura: {orders.get('turn', 'UNKNOWN')}")
        print("\n📋 Rozkazy per dowódca:")
        
        for commander_id, order in orders.get('orders', {}).items():
            print(f"  👤 {commander_id}:")
            print(f"    🎯 Misja: {order.get('mission_type', 'UNKNOWN')}")
            print(f"    📍 Cel: {order.get('target_hex', 'UNKNOWN')}")
            print(f"    ⚡ Priorytet: {order.get('priority', 'UNKNOWN')}")
            print(f"    ⏰ Wygasa na turze: {order.get('expires_turn', 'UNKNOWN')}")
            print(f"    📈 Status: {order.get('status', 'UNKNOWN')}")
    else:
        print("❌ Nie udało się wydać rozkazów!")
    
    return orders

def test_orders_reception():
    """Test 2: AI Commander odbiera rozkazy"""
    print("\n🎯 === TEST 2: AI COMMANDER ODBIERA ROZKAZY ===")
    
    # Sprawdź czy plik rozkazów istnieje
    orders_file = Path("data/strategic_orders.json")
    if not orders_file.exists():
        print("❌ Plik rozkazów nie istnieje!")
        return None
    
    # Stwórz AI Commander dla dowódcy ID=2 (Polski)
    mock_player_2 = type('obj', (), {
        'id': 2, 'nation': 'Polska', 'role': 'Dowódca'
    })()
    
    ai_commander_2 = AICommander(mock_player_2)
    
    # Odbierz rozkazy
    current_turn = 3
    order = ai_commander_2.receive_orders(current_turn=current_turn)
    
    print(f"📞 Dowódca {mock_player_2.id} (Polska) sprawdza rozkazy na turze {current_turn}...")
    
    if order:
        print("✅ Rozkaz otrzymany!")
        print(f"  🎯 Typ misji: {order.get('mission_type', 'UNKNOWN')}")
        print(f"  📍 Docelowy hex: {order.get('target_hex', 'UNKNOWN')}")
        print(f"  ⚡ Priorytet: {order.get('priority', 'UNKNOWN')}")
        print(f"  ⏰ Wydany na turze: {order.get('issued_turn', 'UNKNOWN')}")
        print(f"  ⏰ Wygasa na turze: {order.get('expires_turn', 'UNKNOWN')}")
        print(f"  📋 Kontekst strategiczny: {order.get('strategy_context', 'UNKNOWN')}")
        print(f"  📈 Status: {order.get('status', 'UNKNOWN')}")
    else:
        print("❌ Brak rozkazów lub rozkaz wygasł/nieaktywny")
    
    # Test dla dowódcy ID=3
    print(f"\n📞 Dowódca 3 (Polska) sprawdza rozkazy na turze {current_turn}...")
    mock_player_3 = type('obj', (), {
        'id': 3, 'nation': 'Polska', 'role': 'Dowódca'
    })()
    
    ai_commander_3 = AICommander(mock_player_3)
    order_3 = ai_commander_3.receive_orders(current_turn=current_turn)
    
    if order_3:
        print("✅ Rozkaz otrzymany!")
        print(f"  🎯 Typ misji: {order_3.get('mission_type', 'UNKNOWN')}")
        print(f"  📍 Docelowy hex: {order_3.get('target_hex', 'UNKNOWN')}")
        print(f"  ⚡ Priorytet: {order_3.get('priority', 'UNKNOWN')}")
    else:
        print("❌ Brak rozkazów lub rozkaz wygasł/nieaktywny")
    
    return order

def analyze_order_types():
    """Test 3: Analiza typów rozkazów"""
    print("\n🎯 === TEST 3: ANALIZA TYPÓW ROZKAZÓW ===")
    
    # Odczytaj aktualny plik rozkazów
    orders_file = Path("data/strategic_orders.json")
    if not orders_file.exists():
        print("❌ Plik rozkazów nie istnieje!")
        return
    
    try:
        with open(orders_file, 'r', encoding='utf-8') as f:
            orders_data = json.load(f)
        
        print("📋 Analiza aktualnych rozkazów:")
        print(f"  📅 Timestamp: {orders_data.get('timestamp', 'UNKNOWN')}")
        print(f"  🔢 Tura: {orders_data.get('turn', 'UNKNOWN')}")
        print(f"  📊 Typ strategii: {orders_data.get('strategy_type', 'UNKNOWN')}")
        
        print("\n🎯 Dostępne typy misji w kodzie AI General:")
        mission_types = [
            "SECURE_KEYPOINT - Zabezpiecz kluczowy punkt (early game)",
            "INTEL_GATHERING - Zwiększ rozpoznanie (mid game)", 
            "DEFEND_KEYPOINTS - Broń kluczowych punktów (late game, prowadząc)",
            "ATTACK_ENEMY_VP - Atakuj victory points przeciwnika (late game, przegrywając)"
        ]
        
        for mission in mission_types:
            print(f"  🎯 {mission}")
        
        print("\n📋 Aktualne rozkazy per dowódca:")
        orders = orders_data.get('orders', {})
        for commander_id, order_data in orders.items():
            print(f"  👤 {commander_id}:")
            print(f"    🎯 Misja: {order_data.get('mission_type', 'UNKNOWN')}")
            print(f"    📍 Cel: {order_data.get('target_hex', 'UNKNOWN')}")
            
            # Sprawdź co robi Commander z tym rozkazem
            mission_type = order_data.get('mission_type', 'UNKNOWN')
            if mission_type == 'SECURE_KEYPOINT':
                print(f"    🤖 Commander wykonuje: Ruch w kierunku key point (zabezpieczenie)")
            elif mission_type == 'INTEL_GATHERING':
                print(f"    🤖 Commander wykonuje: Ruch w kierunku key point (rozpoznanie)")
            elif mission_type == 'DEFEND_KEYPOINTS':
                print(f"    🤖 Commander wykonuje: Ruch w kierunku key point (obrona)")
            elif mission_type == 'ATTACK_ENEMY_VP':
                print(f"    🤖 Commander wykonuje: Ruch w kierunku key point (atak)")
            else:
                print(f"    🤖 Commander wykonuje: Fallback - autonomiczny target search")
                
        print("\n⚠️ PROBLEM 'LEMMINGÓW':")
        print("   Wszystkie typy misji powodują identyczne zachowanie!")
        print("   Commander zawsze robi: move_towards(unit, strategic_order['target_hex'])")
        print("   Niezależnie od mission_type - zawsze ten sam algorytm ruchu.")
        
    except Exception as e:
        print(f"❌ Błąd odczytu pliku rozkazów: {e}")

def test_commander_execution():
    """Test 4: Jak Commander wykonuje rozkazy w praktyce"""
    print("\n🎯 === TEST 4: WYKONANIE ROZKAZÓW PRZEZ COMMANDERA ===")
    
    # Mock game engine z prostym board
    game_engine = create_mock_game_engine()
    
    # Symuluj sytuację gdzie Commander otrzymał rozkaz
    mock_strategic_order = {
        'mission_type': 'SECURE_KEYPOINT',
        'target_hex': [15, -7],
        'priority': 'HIGH',
        'expires_turn': 8,
        'issued_turn': 3,
        'status': 'ACTIVE'
    }
    
    print("📋 Symulowany rozkaz strategiczny:")
    print(f"  🎯 Misja: {mock_strategic_order['mission_type']}")
    print(f"  📍 Cel: {mock_strategic_order['target_hex']}")
    
    # Pobierz jednostki dowódcy (z mock game_engine)
    from ai.ai_commander import get_my_units
    my_units = get_my_units(game_engine, player_id=2)
    
    print(f"\n🪖 Jednostki dowódcy ID=2: {len(my_units)}")
    for unit in my_units:
        print(f"  • {unit['id']}: pozycja ({unit['q']}, {unit['r']}), MP={unit['mp']}, Fuel={unit['fuel']}")
    
    print(f"\n🎯 Co robi Commander:")
    print(f"1. Odczytuje target_hex = {mock_strategic_order['target_hex']}")
    print(f"2. Dla każdej jednostki wywołuje: move_towards(unit, {mock_strategic_order['target_hex']})")
    print(f"3. find_path() szuka ścieżki z pozycji jednostki do {mock_strategic_order['target_hex']}")
    print(f"4. Wykonuje MoveAction do najbliższego możliwego hexu w kierunku celu")
    
    print(f"\n🔍 KLUCZOWE ODKRYCIE:")
    print(f"   ❌ mission_type '{mock_strategic_order['mission_type']}' jest IGNOROWANY!")
    print(f"   ❌ Commander nie różnicuje między SECURE_KEYPOINT a INTEL_GATHERING")
    print(f"   ❌ Commander nie różnicuje między DEFEND_KEYPOINTS a ATTACK_ENEMY_VP")
    print(f"   ✅ Commander zawsze robi to samo: ruch w kierunku target_hex")
    
    print(f"\n💡 POTENCJALNE ULEPSZENIA:")
    print(f"   • SECURE_KEYPOINT: agresywny ruch, formation attack")
    print(f"   • INTEL_GATHERING: rozproszone jednostki, zwiększona mobilność")
    print(f"   • DEFEND_KEYPOINTS: formation defense, wybór pozycji obronnych")
    print(f"   • ATTACK_ENEMY_VP: koncentracja siły, prioritet fast units")

if __name__ == "__main__":
    print("🔍 === ANALIZA ROZKAZÓW AI COMMANDER ===\n")
    
    # Uruchom testy
    orders = test_orders_generation()
    if orders:
        order_received = test_orders_reception()
        analyze_order_types()
        test_commander_execution()
    
    print("\n🎉 === ANALIZA ZAKOŃCZONA ===")
