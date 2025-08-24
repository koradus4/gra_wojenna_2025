"""
Test systemu strategicznych rozkazów w rzeczywistej grze
"""
import sys
from pathlib import Path

# Dodaj ścieżkę do głównego projektu
sys.path.append(str(Path(__file__).parent.parent))

def test_real_game_strategic_orders():
    """Test systemu rozkazów z prawdziwymi komponentami gry"""
    
    print("=== TEST STRATEGICZNYCH ROZKAZÓW W RZECZYWISTEJ GRZE ===\n")
    
    try:
        # Import prawdziwych komponentów gry
        from engine.engine import GameEngine
        from engine.player import Player
        from ai.ai_general import AIGeneral
        from ai.ai_commander import make_tactical_turn
        from unittest.mock import patch
        
        print("✅ Zaimportowano komponenty gry")
        
    except ImportError as e:
        print(f"❌ Błąd importu komponentów gry: {e}")
        return False
    
    try:
        # 1. Utwórz GameEngine (minimalny setup)
        print("\n1. Tworzenie GameEngine...")
        engine = GameEngine()
        
        # 2. Utwórz graczy AI (Germany i Soviet)
        print("2. Tworzenie graczy AI...")
        germany_player = Player(2, "germany", "general")  # General
        soviet_player = Player(3, "soviet", "commander")   # Commander
        
        # Dodaj graczy do engine
        engine.players = {2: germany_player, 3: soviet_player}
        engine.current_player_obj = germany_player
        engine.turn_number = 8  # Tura testowa
        
        print(f"   ✅ Germany (General): ID={germany_player.id}")
        print(f"   ✅ Soviet (Commander): ID={soviet_player.id}")
        
        # 3. Test AI General wydaje rozkazy
        print("\n3. AI General wydaje strategiczne rozkazy...")
        ai_general = AIGeneral("germany")
        
        # Symuluj analizę strategiczną (ustaw fazę gry)
        ai_general._strategic_analysis = {
            'game_phase': 1.5,  # Mid game
            'vp_status': 0,
            'phase_name': 'MID_GAME'
        }
        
        # Wydaj rozkazy
        orders_file = Path("data/strategic_orders.json")
        orders = ai_general.issue_strategic_orders(orders_file, current_turn=8)
        
        if orders:
            print(f"   ✅ General wydał rozkazy:")
            print(f"      Strategia: {orders.get('strategy_type', 'UNKNOWN')}")
            print(f"      Tura: {orders.get('turn', 'UNKNOWN')}")
            
            # Sprawdź rozkaz dla Soviet
            soviet_order = orders.get('orders', {}).get('soviet')
            if soviet_order:
                print(f"      Rozkaz dla Soviet: {soviet_order['mission_type']} -> {soviet_order['target_hex']}")
            else:
                print("   ❌ Brak rozkazu dla Soviet")
                return False
        else:
            print("   ❌ General nie wydał rozkazów")
            return False
            
        # 4. Test AI Commander odbiera i wykonuje rozkazy
        print("\n4. AI Commander odbiera i wykonuje rozkazy...")
        
        # Przełącz na Soviet Commander
        engine.current_player_obj = soviet_player
        
        # Mock funkcji move_towards żeby nie wykonywać prawdziwych ruchów
        with patch('ai.ai_commander.move_towards') as mock_move:
            mock_move.return_value = True
            
            # Mock get_my_units żeby zwrócić testowe jednostki
            with patch('ai.ai_commander.get_my_units') as mock_units:
                test_units = [
                    {'id': 'test_unit_1', 'mp': 3, 'fuel': 50, 'x': 10, 'y': 10},
                    {'id': 'test_unit_2', 'mp': 2, 'fuel': 30, 'x': 15, 'y': 15}
                ]
                mock_units.return_value = test_units
                
                # Wykonaj turę AI Commander
                make_tactical_turn(engine, player_id=3)
                
                # Sprawdź czy move_towards został wywołany z celem strategicznym
                if mock_move.called:
                    print("   ✅ AI Commander wykonał ruchy")
                    
                    # Sprawdź argumenty wywołania
                    calls = mock_move.call_args_list
                    for i, call in enumerate(calls):
                        unit, target, game_engine = call[0]
                        print(f"      Jednostka {i+1}: {unit['id']} -> cel {target}")
                        
                        # Sprawdź czy cel to cel strategiczny czy key_point
                        if target == soviet_order['target_hex']:
                            print(f"      ✅ Jednostka używa celu strategicznego!")
                        else:
                            print(f"      🔄 Jednostka używa celu autonomicznego (fallback)")
                else:
                    print("   ❌ AI Commander nie wykonał ruchów")
                    return False
        
        # 5. Test wygasania rozkazów
        print("\n5. Test wygasania rozkazów...")
        
        # Symuluj przejście do tury gdy rozkaz wygasa
        future_turn = orders['orders']['soviet']['expires_turn'] + 1
        engine.turn_number = future_turn
        
        with patch('ai.ai_commander.get_my_units') as mock_units:
            mock_units.return_value = test_units
            
            with patch('ai.ai_commander.find_target') as mock_find_target:
                mock_find_target.return_value = [20, 20]  # Key point fallback
                
                with patch('ai.ai_commander.move_towards') as mock_move:
                    mock_move.return_value = True
                    
                    # Wykonaj turę gdy rozkaz wygasł
                    make_tactical_turn(engine, player_id=3)
                    
                    # Sprawdź czy używa find_target (fallback)
                    if mock_find_target.called:
                        print("   ✅ Rozkaz wygasł - AI Commander przeszedł na tryb autonomiczny")
                    else:
                        print("   ❌ Rozkaz nie wygasł gdy powinien")
                        return False
        
        # 6. Cleanup
        print("\n6. Cleanup...")
        if orders_file.exists():
            orders_file.unlink()
            print("   ✅ Usunięto plik rozkazów")
        
        print("\n✅ WSZYSTKIE TESTY W RZECZYWISTEJ GRZE PRZESZŁY POMYŚLNIE!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas testów: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategic_coordination():
    """Test koordynacji między AI General a AI Commander"""
    
    print("\n=== TEST KOORDYNACJI AI GENERAL ↔ AI COMMANDER ===\n")
    
    try:
        from ai.ai_general import AIGeneral
        from ai.ai_commander import AICommander
        from unittest.mock import Mock
        
        # 1. Różne fazy gry - różne strategie
        phases = [
            (1.0, 0, "EXPANSION", "SECURE_KEYPOINT"),      # Early game
            (1.5, 0, "SCOUTING", "INTEL_GATHERING"),        # Mid game  
            (2.5, 1, "DEFENSIVE", "DEFEND_KEYPOINTS"),      # Late game - winning
            (2.5, -1, "AGGRESSIVE", "ATTACK_ENEMY_VP")      # Late game - losing
        ]
        
        orders_file = Path("data/test_coordination.json")
        
        for game_phase, vp_status, expected_strategy, expected_mission in phases:
            print(f"Testowanie fazy {game_phase}, VP status {vp_status}...")
            
            # AI General analizuje i wydaje rozkazy
            general = AIGeneral("germany")
            general._strategic_analysis = {
                'game_phase': game_phase,
                'vp_status': vp_status,
                'phase_name': f'PHASE_{game_phase}'
            }
            
            orders = general.issue_strategic_orders(orders_file, current_turn=10)
            
            # Sprawdź czy strategia jest zgodna z oczekiwaniami
            if orders:
                actual_strategy = orders.get('strategy_type', 'UNKNOWN')
                germany_order = orders.get('orders', {}).get('germany', {})
                actual_mission = germany_order.get('mission_type', 'UNKNOWN')
                
                if actual_strategy == expected_strategy and actual_mission == expected_mission:
                    print(f"   ✅ Faza {game_phase}: {actual_strategy} -> {actual_mission}")
                else:
                    print(f"   ❌ Faza {game_phase}: Oczekiwano {expected_strategy}->{expected_mission}, "
                          f"otrzymano {actual_strategy}->{actual_mission}")
                    return False
            else:
                print(f"   ❌ Faza {game_phase}: Brak rozkazów")
                return False
        
        # Cleanup
        if orders_file.exists():
            orders_file.unlink()
        
        print("\n✅ TEST KOORDYNACJI ZAKOŃCZONY POMYŚLNIE!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd testu koordynacji: {e}")
        return False

if __name__ == "__main__":
    print("TESTY SYSTEMU STRATEGICZNYCH ROZKAZÓW W RZECZYWISTEJ GRZE\n")
    
    # Test 1: Rzeczywista gra
    success1 = test_real_game_strategic_orders()
    
    # Test 2: Koordynacja strategiczna
    success2 = test_strategic_coordination()
    
    if success1 and success2:
        print("\n🎉 WSZYSTKIE TESTY ZAKOŃCZONE POMYŚLNIE!")
        sys.exit(0)
    else:
        print("\n❌ NIEKTÓRE TESTY NIE PRZESZŁY")
        sys.exit(1)
