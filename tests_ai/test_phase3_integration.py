"""
Test integracyjny Victory AI Phase 3 w rzeczywistej grze
Uruchamia pełną integrację Phase 1+2+3 aby sprawdzić czy system działa w praktyce
"""

import sys
import os
import unittest
from pathlib import Path

# Dodaj główny katalog projektu do ścieżki
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import głównego systemu gry
from ai.victory_ai import integrate_victory_ai_full_with_phase3, log_victory_ai_csv

class TestVictoryAIPhase3Integration(unittest.TestCase):
    """Test klasa dla integracji Victory AI Phase 3"""
    
    def test_victory_ai_phase3_integration(self):
        """Test integracyjny Phase 3 w rzeczywistej grze"""
        print("🎯 Rozpoczynam test integracyjny Victory AI Phase 3...")
        
        try:
            # Import game engine
            from engine.engine import GameEngine
            from engine.player import Player
            
            # Stwórz podstawową grę testową z poprawnymi ścieżkami relatywnymi
            project_root = Path(__file__).parent.parent
            map_path = project_root / "data" / "map_data.json"
            tokens_index_path = project_root / "assets" / "tokens" / "index.json"
            tokens_start_path = project_root / "assets" / "start_tokens.json"
            
            game_engine = GameEngine(str(map_path), str(tokens_index_path), str(tokens_start_path))
            game_engine.current_turn = 1
            
            # Stwórz gracza testowego
            player = Player(player_id=1, nation="germany", role="human")
            player.captured_kps = ["A1", "B2", "C3"]  # Symulacja posiadanych KP
            
            # Dodaj podstawowe tokeny z poprawnymi statystykami
            from engine.token import Token
            
            infantry_stats = {'move': 2, 'combat_value': 3, 'maintenance': 5}
            token1 = Token("infantry_1", "germany", infantry_stats, 1, 1)
            token1.movePoints = 2
            token1.fuel = 5
            
            armor_stats = {'move': 3, 'combat_value': 5, 'maintenance': 4}
            token2 = Token("armor_1", "germany", armor_stats, 2, 2)  
            token2.movePoints = 3
            token2.fuel = 4
            
            player.tokens = [token1, token2]
            game_engine.players = [player]
            
            print(f"🎮 Gracz {player.id} ({player.nation})")
            print(f"📍 KP kontrolowane: {len(player.captured_kps)}")
            print(f"🪖 Jednostki: {len(player.tokens)}")
            
            # Przygotuj dane dla Victory AI
            my_units = []
            for token in player.tokens:
                unit_data = {
                    'token': token,
                    'unit_id': getattr(token, 'id', 'UNKNOWN'),
                    'unitType': 'infantry',  # Simplified
                    'position': (getattr(token, 'q', 0), getattr(token, 'r', 0)),
                    'MP': getattr(token, 'currentMovePoints', 0),
                    'Fuel': getattr(token, 'currentFuel', 0),
                    'combat_value': getattr(token, 'combat_value', 0),
                    'moved_capture': False
                }
                my_units.append(unit_data)
            
            # Uruchom Victory AI Phase 1+2+3
            result = integrate_victory_ai_full_with_phase3(game_engine, my_units, player.id)
            
            if result:
                print("\n✅ Victory AI Phase 3 wykonane pomyślnie!")
                
                # Wyświetl wyniki Phase 1
                phase1 = result.get('phase1_result', {})
                print(f"🎯 Phase 1: {phase1.get('scouts_deployed', 0)} scouts deployed")
                
                # Wyświetl wyniki Phase 2  
                phase2 = result.get('phase2_result', {})
                print(f"⚔️ Phase 2: {phase2.get('active_plans', 0)} active plans")
                
                # Wyświetl wyniki Phase 3
                phase3 = result.get('phase3_result', {})
                if phase3:
                    defense_alloc = phase3.get('defense_allocation', {})
                    kp_defense = phase3.get('kp_defense', {})
                    pe_security = phase3.get('pe_security', {})
                    
                    print(f"🛡️ Phase 3 Defense:")
                    print(f"   • Defenders assigned: {kp_defense.get('total_defenders_assigned', 0)}")
                    print(f"   • KPs covered: {kp_defense.get('total_kps_covered', 0)}")
                    print(f"   • PE security: {pe_security.get('pe_secure', False)}")
                    
                    # Wyświetl podsumowanie integracji
                    integration = result.get('integration_summary', {})
                    print(f"\n📊 Integration Summary:")
                    print(f"   • Total scouts: {integration.get('total_scouts_deployed', 0)}")
                    print(f"   • Total plans: {integration.get('total_plans_created', 0)}")
                    print(f"   • Total defenders: {integration.get('total_defenders_assigned', 0)}")
                    print(f"   • PE secure: {integration.get('pe_security_maintained', False)}")
                
                print("\n🎉 Test zakończony sukcesem!")
                self.assertTrue(True)
            else:
                print("❌ Victory AI Phase 3 zwrócił None - błąd!")
                self.fail("Victory AI Phase 3 zwrócił None")
                
        except Exception as e:
            print(f"❌ Błąd podczas testu: {e}")
            import traceback
            traceback.print_exc()
            self.fail(f"Test failed with exception: {e}")


def run_integration_test():
    """Funkcja pomocnicza do uruchamiania testu integracyjnego"""
    print("🎯 Rozpoczynam test integracyjny Victory AI Phase 3...")
    
    try:
        # Import game engine
        from engine.engine import GameEngine
        from engine.player import Player
        
        # Stwórz podstawową grę testową z poprawnymi ścieżkami relatywnymi
        project_root = Path(__file__).parent.parent
        map_path = project_root / "data" / "map_data.json"
        tokens_index_path = project_root / "assets" / "tokens" / "index.json"
        tokens_start_path = project_root / "assets" / "start_tokens.json"
        
        game_engine = GameEngine(str(map_path), str(tokens_index_path), str(tokens_start_path))
        game_engine.current_turn = 1
        
        # Stwórz gracza testowego
        player = Player(player_id=1, nation="germany", role="human")
        player.captured_kps = ["A1", "B2", "C3"]  # Symulacja posiadanych KP
        
        # Dodaj podstawowe tokeny z poprawnymi statystykami
        from engine.token import Token
        
        infantry_stats = {'move': 2, 'combat_value': 3, 'maintenance': 5}
        token1 = Token("infantry_1", "germany", infantry_stats, 1, 1)
        token1.movePoints = 2
        token1.fuel = 5
        
        armor_stats = {'move': 3, 'combat_value': 5, 'maintenance': 4}
        token2 = Token("armor_1", "germany", armor_stats, 2, 2)  
        token2.movePoints = 3
        token2.fuel = 4
        
        player.tokens = [token1, token2]
        game_engine.players = [player]
        
        print(f"🎮 Gracz {player.id} ({player.nation})")
        print(f"📍 KP kontrolowane: {len(player.captured_kps)}")
        print(f"🪖 Jednostki: {len(player.tokens)}")
        
        # Przygotuj dane dla Victory AI
        my_units = []
        for token in player.tokens:
            unit_data = {
                'token': token,
                'unit_id': getattr(token, 'id', 'UNKNOWN'),
                'unitType': 'infantry',  # Simplified
                'position': (getattr(token, 'q', 0), getattr(token, 'r', 0)),
                'MP': getattr(token, 'currentMovePoints', 0),
                'Fuel': getattr(token, 'currentFuel', 0),
                'combat_value': getattr(token, 'combat_value', 0),
                'moved_capture': False
            }
            my_units.append(unit_data)
        
        # Uruchom Victory AI Phase 1+2+3
        result = integrate_victory_ai_full_with_phase3(game_engine, my_units, player.id)
        
        if result:
            print("\n✅ Victory AI Phase 3 wykonane pomyślnie!")
            
            # Wyświetl wyniki Phase 1
            phase1 = result.get('phase1_result', {})
            print(f"🎯 Phase 1: {phase1.get('scouts_deployed', 0)} scouts deployed")
            
            # Wyświetl wyniki Phase 2  
            phase2 = result.get('phase2_result', {})
            print(f"⚔️ Phase 2: {phase2.get('active_plans', 0)} active plans")
            
            # Wyświetl wyniki Phase 3
            phase3 = result.get('phase3_result', {})
            if phase3:
                defense_alloc = phase3.get('defense_allocation', {})
                kp_defense = phase3.get('kp_defense', {})
                pe_security = phase3.get('pe_security', {})
                
                print(f"🛡️ Phase 3 Defense:")
                print(f"   • Defenders assigned: {kp_defense.get('total_defenders_assigned', 0)}")
                print(f"   • KPs covered: {kp_defense.get('total_kps_covered', 0)}")
                print(f"   • PE security: {pe_security.get('pe_secure', False)}")
                
                # Wyświetl podsumowanie integracji
                integration = result.get('integration_summary', {})
                print(f"\n📊 Integration Summary:")
                print(f"   • Total scouts: {integration.get('total_scouts_deployed', 0)}")
                print(f"   • Total plans: {integration.get('total_plans_created', 0)}")
                print(f"   • Total defenders: {integration.get('total_defenders_assigned', 0)}")
                print(f"   • PE secure: {integration.get('pe_security_maintained', False)}")
            
            print("\n🎉 Test zakończony sukcesem!")
            return True
        else:
            print("❌ Victory AI Phase 3 zwrócił None - błąd!")
            return False
            
    except Exception as e:
        print(f"❌ Błąd podczas testu: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Uruchom jako standalone test lub jako unit test
    if len(sys.argv) > 1 and sys.argv[1] == "--unittest":
        unittest.main(argv=[sys.argv[0]])
    else:
        # Uruchom jako standalone
        success = run_integration_test()
        sys.exit(0 if success else 1)
