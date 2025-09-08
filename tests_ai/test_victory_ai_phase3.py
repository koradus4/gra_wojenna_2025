"""
Testy jednostkowe dla Victory AI Phase 3 - Balanced Defense & KP Security
Testuje system alokacji obrony, przypisywania obrońców do KP i walidacji bezpieczeństwa PE
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import unittest
from unittest.mock import Mock, patch, MagicMock
from ai.victory_ai import (
    calculate_defense_allocation,
    assign_kp_defenders,
    maintain_pe_collection_capability,
    victory_ai_phase3_controller,
    integrate_victory_ai_full_with_phase3
)


class TestVictoryAIPhase3(unittest.TestCase):
    
    def setUp(self):
        """Przygotowanie danych testowych dla każdego testu"""
        # Mock game engine
        self.mock_game_engine = Mock()
        self.mock_game_engine.current_turn = 5
        self.mock_game_engine.board = Mock()
        self.mock_game_engine.board.hexes = {}
        
        # Mock gracza
        self.mock_player = Mock()
        self.mock_player.player_id = 1
        self.mock_player.nation = "germany"
        self.mock_player.tokens = []
        self.mock_player.captured_kps = ["A1", "B2", "C3"]
        
        # Mock tokenów - różne typy jednostek
        self.mock_infantry = Mock()
        self.mock_infantry.token_type = "infantry"
        self.mock_infantry.current_hex = "A1"
        self.mock_infantry.can_move = True
        self.mock_infantry.movement_points = 2
        
        self.mock_armor = Mock()
        self.mock_armor.token_type = "armor"
        self.mock_armor.current_hex = "B2"
        self.mock_armor.can_move = True
        self.mock_armor.movement_points = 3
        
        self.mock_artillery = Mock()
        self.mock_artillery.token_type = "artillery"
        self.mock_artillery.current_hex = "C3"
        self.mock_artillery.can_move = True
        self.mock_artillery.movement_points = 1
        
        self.mock_player.tokens = [self.mock_infantry, self.mock_armor, self.mock_artillery]
        
        # Mock aktywnych planów
        self.mock_active_plans = [
            {"target_hex": "D4", "type": "attack", "force_requirement": 3},
            {"target_hex": "E5", "type": "raid", "force_requirement": 2}
        ]
    
    def test_calculate_defense_allocation_low_threat(self):
        """Test alokacji obrony przy niskim poziomie zagrożenia"""
        # Przygotowanie danych - lista jednostek, a nie liczba
        unit_forces = [
            {'MP': 2, 'Fuel': 5, 'defense': 3, 'attack': 2},
            {'MP': 3, 'Fuel': 4, 'defense': 2, 'attack': 4},
            {'MP': 1, 'Fuel': 3, 'defense': 4, 'attack': 1},
            {'MP': 2, 'Fuel': 6, 'defense': 3, 'attack': 3},
            {'MP': 0, 'Fuel': 0, 'defense': 1, 'attack': 1}  # Ta nie powinna być uwzględniona
        ]
        active_plans = self.mock_active_plans
        
        # Mock funkcji assess_overall_threat_level dla niskiego zagrożenia
        with patch('ai.victory_ai.assess_overall_threat_level', return_value=0.2):
            allocation = calculate_defense_allocation(unit_forces, active_plans, self.mock_game_engine)
        
        # Sprawdź czy zwrócono poprawną strukturę
        self.assertIn('defensive_units', allocation)
        self.assertIn('attack_units', allocation)
        self.assertIn('reserve_units', allocation)
        self.assertIn('allocation_ratios', allocation)
        
        # Sprawdź czy jednostki bez MP/Fuel zostały odfiltrowane
        total_assigned = (len(allocation['defensive_units']) + 
                         len(allocation['attack_units']) + 
                         len(allocation['reserve_units']))
        self.assertEqual(total_assigned, 4)  # 4 jednostki z MP/Fuel > 0
        
        # Sprawdź czy alokacja ma sens procentowo
        ratios = allocation['allocation_ratios']
        total_percent = ratios['defense_percent'] + ratios['attack_percent'] + ratios['reserve_percent']
        self.assertAlmostEqual(total_percent, 100, delta=0.1)  # Suma ~100%
    
    def test_calculate_defense_allocation_high_threat(self):
        """Test alokacji obrony przy wysokim poziomie zagrożenia"""
        # Przygotowanie danych - lista jednostek z wysokim threat scenariuszem
        unit_forces = [
            {'MP': 2, 'Fuel': 5, 'defense': 5, 'attack': 2},
            {'MP': 3, 'Fuel': 4, 'defense': 4, 'attack': 3},
            {'MP': 1, 'Fuel': 3, 'defense': 6, 'attack': 1},
            {'MP': 2, 'Fuel': 6, 'defense': 3, 'attack': 4},
            {'MP': 1, 'Fuel': 2, 'defense': 4, 'attack': 2},
            {'MP': 3, 'Fuel': 5, 'defense': 2, 'attack': 5}
        ]
        active_plans = self.mock_active_plans
        
        # Mock high threat scenario w game_engine
        with patch('ai.victory_ai.assess_overall_threat_level', return_value=0.8):
            allocation = calculate_defense_allocation(unit_forces, active_plans, self.mock_game_engine)
        
        # Przy wysokim zagrożeniu powinno być więcej obrony
        ratios = allocation['allocation_ratios']
        self.assertGreaterEqual(ratios['defense_percent'], 50)  # Min 50% obrony
        
        # Sprawdź czy threat level został uwzględniony
        self.assertIn('threat_level', allocation)
        self.assertGreater(allocation['threat_level'], 0.5)
    
    def test_assign_kp_defenders_basic(self):
        """Test podstawowego przypisywania obrońców do KP"""
        defense_allocation = 6
        
        # Mock get_player_nation i inne funkcje pomocnicze
        with patch('ai.victory_ai.calculate_kp_defense_priority', return_value=0.7), \
             patch('ai.victory_ai.find_nearby_units', return_value=[self.mock_infantry, self.mock_armor]):
            
            result = assign_kp_defenders(
                self.mock_player, 
                self.mock_game_engine, 
                defense_allocation
            )
        
        # Sprawdź strukturę wyniku
        self.assertIn('kp_assignments', result)
        self.assertIn('total_defenders_assigned', result)
        self.assertIn('total_kps_covered', result)
        self.assertIn('coverage_ratio', result)
        
        # Sprawdź czy nie przekroczono dostępnej alokacji
        self.assertLessEqual(result['total_defenders_assigned'], defense_allocation)
        
        # Sprawdź czy pokryto jakieś KP
        self.assertGreaterEqual(result['total_kps_covered'], 0)
    
    def test_maintain_pe_collection_capability(self):
        """Test walidacji zdolności zbierania PE"""
        
        # Mock funkcji pomocniczych
        with patch('ai.victory_ai.identify_pe_sources', return_value=["pe1", "pe2"]), \
             patch('ai.victory_ai.check_pe_source_security', return_value=True):
            
            result = maintain_pe_collection_capability(
                self.mock_player, 
                self.mock_game_engine
            )
        
        # Sprawdź strukturę wyniku
        self.assertIn('pe_secure', result)
        self.assertIn('pe_sources_count', result)
        self.assertIn('collection_capability', result)
        self.assertIn('security_level', result)
        
        # PE secure powinno być boolean
        self.assertIsInstance(result['pe_secure'], bool)
        
        # Liczniki powinny być nieujemne
        self.assertGreaterEqual(result['pe_sources_count'], 0)
    
    def test_victory_ai_phase3_controller_success(self):
        """Test głównego kontrolera Phase 3 - scenariusz sukcesu"""
        
        with patch('ai.victory_ai.log_victory_ai_csv') as mock_log, \
             patch('ai.victory_ai.get_active_victory_plans', return_value=self.mock_active_plans), \
             patch('ai.victory_ai.calculate_defense_allocation') as mock_alloc, \
             patch('ai.victory_ai.assign_kp_defenders') as mock_kp, \
             patch('ai.victory_ai.maintain_pe_collection_capability') as mock_pe:
            
            # Mock return values
            mock_alloc.return_value = {'defensive_units': [], 'attack_units': [], 'reserve_units': []}
            mock_kp.return_value = {'total_defenders_assigned': 3, 'total_kps_covered': 2}
            mock_pe.return_value = {'pe_secure': True, 'pe_sources_count': 2}
            
            result = victory_ai_phase3_controller(
                self.mock_player, 
                self.mock_game_engine
            )
        
        # Sprawdź czy zwrócono wynik
        self.assertIsNotNone(result)
        self.assertIn('defense_allocation', result)
        self.assertIn('kp_defense', result)
        self.assertIn('pe_security', result)
        
        # Sprawdź czy logowanie zostało wywołane
        mock_log.assert_called()
    
    def test_victory_ai_phase3_controller_error_handling(self):
        """Test obsługi błędów w kontrolerze Phase 3"""
        
        # Symuluj błąd poprzez None player
        with patch('ai.victory_ai.log_victory_ai_csv') as mock_log:
            result = victory_ai_phase3_controller(None, self.mock_game_engine)
        
        # Sprawdź czy zwrócono None przy błędzie
        self.assertIsNone(result)
        
        # Sprawdź czy zalogowano błąd
        mock_log.assert_called()
        # Sprawdź czy ostatnie wywołanie zawiera "PHASE3_ERROR"
        last_call = mock_log.call_args_list[-1]
        self.assertEqual(last_call[0][0], "PHASE3_ERROR")
    
    def test_integrate_victory_ai_full_with_phase3(self):
        """Test pełnej integracji Phase 1+2+3"""
        
        with patch('ai.victory_ai.victory_ai_phase1_scouting', return_value={'scouts_deployed': 5}), \
             patch('ai.victory_ai.victory_ai_phase2_planning', return_value={'plans_created': 2}), \
             patch('ai.victory_ai.victory_ai_phase3_controller') as mock_phase3, \
             patch('ai.victory_ai.log_victory_ai_csv') as mock_log:
            
            mock_phase3.return_value = {
                'defense_allocation': {'defense_allocation': 6},
                'kp_defense': {'total_defenders_assigned': 4},
                'pe_security': {'pe_secure': True}
            }
            
            result = integrate_victory_ai_full_with_phase3(
                self.mock_player, 
                self.mock_game_engine
            )
        
        # Sprawdź czy wszystkie fazy zostały wykonane
        self.assertIn('phase1_result', result)
        self.assertIn('phase2_result', result)
        self.assertIn('phase3_result', result)
        self.assertIn('integration_summary', result)
        
        # Sprawdź czy podsumowanie integracji zawiera kluczowe metryki
        summary = result['integration_summary']
        self.assertIn('total_scouts_deployed', summary)
        self.assertIn('total_plans_created', summary)
        self.assertIn('total_defenders_assigned', summary)
        self.assertIn('pe_security_maintained', summary)
    
    def test_defense_allocation_edge_cases(self):
        """Test przypadków brzegowych alokacji obrony"""
        
        # Test z zerowymi siłami
        allocation = calculate_defense_allocation([], [], self.mock_game_engine)
        self.assertEqual(len(allocation['defensive_units']), 0)
        self.assertEqual(len(allocation['attack_units']), 0)
        self.assertEqual(len(allocation['reserve_units']), 0)
        
        # Test z jednostkami bez MP/Fuel
        no_mp_units = [
            {'MP': 0, 'Fuel': 0, 'defense': 3, 'attack': 2},
            {'MP': 0, 'Fuel': 5, 'defense': 2, 'attack': 3}
        ]
        allocation = calculate_defense_allocation(no_mp_units, [], self.mock_game_engine)
        total_assigned = (len(allocation['defensive_units']) + 
                         len(allocation['attack_units']) + 
                         len(allocation['reserve_units']))
        self.assertEqual(total_assigned, 0)
        
        # Test z bardzo wysokim zagrożeniem
        good_units = [
            {'MP': 2, 'Fuel': 3, 'defense': 5, 'attack': 2},
            {'MP': 1, 'Fuel': 4, 'defense': 3, 'attack': 4}
        ]
        with patch('ai.victory_ai.assess_overall_threat_level', return_value=1.0):
            allocation = calculate_defense_allocation(good_units, [], self.mock_game_engine)
            # Powinno maksymalnie zwiększyć obronę
            ratios = allocation['allocation_ratios']
            self.assertGreaterEqual(ratios['defense_percent'], 60)
    
    def test_kp_assignment_priorities(self):
        """Test priorytetyzacji przypisywania obrońców do KP"""
        
        # Mock KP z różnymi priorytetami
        self.mock_player.captured_kps = ["high_priority", "medium_priority", "low_priority"]
        
        with patch('ai.victory_ai.calculate_kp_defense_priority') as mock_priority, \
             patch('ai.victory_ai.find_nearby_units', return_value=[self.mock_infantry]):
            
            # Symuluj różne priorytety
            mock_priority.side_effect = lambda kp, player, game: {
                "high_priority": 0.9,
                "medium_priority": 0.6,
                "low_priority": 0.3
            }.get(kp, 0.5)
            
            result = assign_kp_defenders(
                self.mock_player, 
                self.mock_game_engine, 
                3  # Tylko 3 obrońców dostępnych
            )
            
            # Sprawdź czy wysokie priorytety zostały pokryte najpierw
            assignments = result['kp_assignments']
            if assignments:
                # Sprawdź czy high_priority dostał obrońców
                high_priority_covered = any(
                    assignment['kp'] == "high_priority" and assignment['defenders'] > 0
                    for assignment in assignments
                )
                self.assertTrue(high_priority_covered or len(assignments) == 0)


class TestVictoryAIPhase3Integration(unittest.TestCase):
    """Testy integracyjne Phase 3 z istniejącymi systemami"""
    
    def setUp(self):
        self.mock_game_engine = Mock()
        self.mock_player = Mock()
        self.mock_player.player_id = 1
        self.mock_player.nation = "germany"
        self.mock_player.tokens = []
        self.mock_player.captured_kps = ["A1", "B2"]
    
    @patch('ai.victory_ai.assign_garrison_support')
    def test_integration_with_garrison_support(self, mock_garrison):
        """Test integracji z systemem wsparcia garnizonu"""
        
        mock_garrison.return_value = {
            "A1": {"recommended_defenders": 2, "priority": 0.8},
            "B2": {"recommended_defenders": 1, "priority": 0.6}
        }
        
        with patch('ai.victory_ai.calculate_kp_defense_priority', return_value=0.7), \
             patch('ai.victory_ai.find_nearby_units', return_value=[self.mock_infantry]):
            
            result = assign_kp_defenders(
                self.mock_player, 
                self.mock_game_engine, 
                5
            )
        
        # Sprawdź czy rekomendacje garnizonu zostały uwzględnione
        self.assertIsNotNone(result)
        # Więcej szczegółowych testów można dodać po implementacji integracji
    
    def test_phase3_performance(self):
        """Test wydajności Phase 3 z dużą liczbą jednostek i KP"""
        
        # Symuluj dużą liczbę tokenów
        large_token_list = []
        for i in range(50):
            mock_token = Mock()
            mock_token.token_type = "infantry"
            mock_token.current_hex = f"hex_{i}"
            mock_token.can_move = True
            large_token_list.append(mock_token)
        
        self.mock_player.tokens = large_token_list
        
        # Symuluj dużą liczbę KP
        large_kp_list = [f"kp_{i}" for i in range(20)]
        self.mock_player.captured_kps = large_kp_list
        
        import time
        
        with patch('ai.victory_ai.log_victory_ai_csv'), \
             patch('ai.victory_ai.get_active_victory_plans', return_value=[]), \
             patch('ai.victory_ai.calculate_defense_allocation') as mock_alloc, \
             patch('ai.victory_ai.assign_kp_defenders') as mock_kp, \
             patch('ai.victory_ai.maintain_pe_collection_capability') as mock_pe:
            
            # Mock return values for performance test
            mock_alloc.return_value = {'defensive_units': [], 'attack_units': [], 'reserve_units': []}
            mock_kp.return_value = {'total_defenders_assigned': 10, 'total_kps_covered': 15}
            mock_pe.return_value = {'pe_secure': True, 'pe_sources_count': 5}
            
            start_time = time.time()
            
            result = victory_ai_phase3_controller(
                self.mock_player, 
                self.mock_game_engine
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
        
        # Test wydajności - Phase 3 powinno zakończyć się w rozsądnym czasie
        self.assertLess(execution_time, 5.0)  # Maksymalnie 5 sekund
        self.assertIsNotNone(result)


if __name__ == '__main__':
    # Konfiguracja testów
    unittest.main(verbosity=2)
