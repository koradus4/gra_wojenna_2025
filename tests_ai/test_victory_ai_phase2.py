"""Testy dla Victory AI Phase 2 - Multi-turn Attack Planning"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any

# Import testowanych funkcji
from ai.victory_ai import (
    create_attack_plan,
    execute_attack_phase, 
    validate_plan_continuation,
    victory_ai_phase2_controller,
    integrate_victory_ai_full,
    ATTACK_PLAN_CACHE,
    cleanup_old_plans
)

class TestAttackPlanCreation:
    """Testy tworzenia planów ataku"""
    
    def test_create_attack_plan_valid_input(self):
        """Test tworzenia planu ataku z prawidłowymi danymi"""
        # Mock data
        target_cluster = [
            {'position': (25, 0), 'combat_value': 5, 'owner': 'German'},
            {'position': (26, 0), 'combat_value': 3, 'owner': 'German'}
        ]
        available_forces = [
            {'unit_id': 'unit1', 'position': (20, 0), 'mp': 3, 'combat_value': 8},
            {'unit_id': 'unit2', 'position': (21, 0), 'mp': 2, 'combat_value': 6},
            {'unit_id': 'unit3', 'position': (22, 0), 'mp': 4, 'combat_value': 7}
        ]
        
        mock_engine = Mock()
        player_id = 2
        current_turn = 5
        
        # Execute
        plan = create_attack_plan(target_cluster, available_forces, mock_engine, player_id, current_turn)
        
        # Verify
        assert plan['status'] != 'INVALID'
        assert plan['player_id'] == player_id
        assert plan['created_turn'] == current_turn
        assert plan['target_center'] == (25, 0)  # Średnia pozycji target cluster
        assert len(plan['assigned_forces']) <= 8  # Maksymalnie 8 jednostek
        assert plan['current_phase'] == 'POSITIONING'
        assert 'POSITIONING' in plan['phases']
        assert 'CONCENTRATION' in plan['phases']
        assert 'ATTACK' in plan['phases']
        assert 'EXPLOITATION' in plan['phases']
        
        # Plan powinien być w cache
        assert plan['plan_id'] in ATTACK_PLAN_CACHE
    
    def test_create_attack_plan_empty_input(self):
        """Test tworzenia planu z pustymi danymi"""
        plan = create_attack_plan([], [], Mock(), 1, 1)
        
        assert plan['status'] == 'INVALID'
        assert plan['reason'] == 'No targets or forces'
    
    def test_attack_plan_phases_structure(self):
        """Test struktury faz planu ataku"""
        target_cluster = [{'position': (30, 5), 'combat_value': 4}]
        available_forces = [{'unit_id': 'test', 'position': (25, 5), 'mp': 3}]
        
        plan = create_attack_plan(target_cluster, available_forces, Mock(), 1, 10)
        
        # Sprawdź że wszystkie fazy mają odpowiednią strukturę
        for phase_name, phase_data in plan['phases'].items():
            assert 'turn_range' in phase_data
            assert 'objective' in phase_data
            assert 'status' in phase_data
            assert phase_data['status'] == 'PENDING'
            
            # Sprawdź logiczną kolejność tur
            turn_start, turn_end = phase_data['turn_range']
            assert turn_start >= 11  # Current turn + 1
            assert turn_end >= turn_start


class TestPlanValidation:
    """Testy walidacji planów"""
    
    def test_validate_plan_continuation_success(self):
        """Test walidacji gdy plan powinien być kontynuowany"""
        # Mock plan
        plan = {
            'plan_id': 'test-plan',
            'assigned_forces': [
                {'unit_id': 'unit1'}, {'unit_id': 'unit2'}, {'unit_id': 'unit3'}
            ],
            'target_cluster': [
                {'position': (30, 0), 'combat_value': 5}
            ],
            'target_center': (30, 0)
        }
        
        # Mock current units (wszystkie assigned forces nadal istnieją)
        my_units = [
            {'unit_id': 'unit1', 'mp': 2},
            {'unit_id': 'unit2', 'mp': 3}, 
            {'unit_id': 'unit3', 'mp': 1},
            {'unit_id': 'other', 'mp': 2}
        ]
        
        # Mock game engine
        mock_engine = Mock()
        
        # Mock scan_visible_enemies (znalezione wrogowie w target area)
        with pytest.MonkeyPatch().context() as m:
            m.setattr('ai.victory_ai.scan_visible_enemies', 
                     lambda units, engine: [{'position': (30, 0), 'combat_value': 5}])
            m.setattr('ai.victory_ai.evaluate_combat_opportunity',
                     lambda cluster, forces: {'recommendation': 'ATTACK', 'force_ratio': 1.5})
            
            result = validate_plan_continuation(plan, my_units, mock_engine)
            
        assert result == True
    
    def test_validate_plan_continuation_heavy_losses(self):
        """Test walidacji gdy zbyt duże straty"""
        plan = {
            'plan_id': 'test-plan', 
            'assigned_forces': [
                {'unit_id': 'unit1'}, {'unit_id': 'unit2'}, {'unit_id': 'unit3'},
                {'unit_id': 'unit4'}, {'unit_id': 'unit5'}
            ],
            'target_cluster': [{'position': (30, 0)}],
            'target_center': (30, 0)
        }
        
        # Tylko 2 z 5 assigned units nadal istnieje (40% strat)
        my_units = [
            {'unit_id': 'unit1', 'mp': 2},
            {'unit_id': 'unit2', 'mp': 3}
        ]
        
        result = validate_plan_continuation(plan, my_units, Mock())
        
        assert result == False  # Zbyt duże straty (60% > 40% threshold)


class TestPhase2Controller:
    """Testy głównego kontrolera Phase 2"""
    
    def test_victory_ai_phase2_controller_no_plans(self):
        """Test Phase 2 gdy nie ma aktywnych planów"""
        # Clear cache przed testem
        ATTACK_PLAN_CACHE.clear()
        
        mock_engine = Mock()
        mock_engine.current_turn = 5
        
        my_units = [
            {'unit_id': 'unit1', 'mp': 3, 'moved_capture': False}
        ]
        
        # Mock Phase 1 results (brak opportunities)
        with pytest.MonkeyPatch().context() as m:
            m.setattr('ai.victory_ai.victory_ai_phase1_controller',
                     lambda engine, units, player_id: {
                         'recommended_actions': [],
                         'combat_opportunities': 0
                     })
            
            result = victory_ai_phase2_controller(mock_engine, my_units, player_id=2)
        
        assert result['phase'] == 'MULTI_TURN_ATTACK_PLANNING'
        assert result['active_plans'] == 0
        assert result['new_plans_created'] == 0
        assert result['plans_executed'] == 0
    
    def test_victory_ai_phase2_controller_creates_new_plan(self):
        """Test Phase 2 tworzący nowy plan z opportunity"""
        mock_engine = Mock()
        mock_engine.current_turn = 8
        
        my_units = [
            {'unit_id': f'unit{i}', 'mp': 3, 'moved_capture': False} 
            for i in range(10)  # Wystarczająco dużo units
        ]
        
        # Mock Phase 1 results z high-confidence opportunity
        mock_phase1_results = {
            'recommended_actions': [{
                'action': 'PLAN_ATTACK',
                'target_cluster': 0,
                'confidence': 0.8  # High confidence
            }],
            'threat_clusters': [[
                {'position': (35, 10), 'combat_value': 6, 'owner': 'German'}
            ]]
        }
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr('ai.victory_ai.victory_ai_phase1_controller',
                     lambda engine, units, player_id: mock_phase1_results)
            
            result = victory_ai_phase2_controller(mock_engine, my_units, player_id=3)
        
        assert result['new_plans_created'] >= 1
        assert len(result['phase_actions']) > 0
        
        # Sprawdź że plan został rzeczywiście utworzony
        new_plan_actions = [a for a in result['phase_actions'] if a.get('action') == 'NEW_PLAN_CREATED']
        assert len(new_plan_actions) >= 1


class TestFullIntegration:
    """Testy pełnej integracji Victory AI"""
    
    def test_integrate_victory_ai_full(self):
        """Test pełnej integracji Phase 1 + Phase 2"""
        mock_engine = Mock()
        my_units = [{'unit_id': 'test', 'mp': 2}]
        player_id = 1
        
        # Mock results dla obu faz
        mock_phase1 = {
            'scouts_deployed': 2,
            'enemies_detected': 3,
            'combat_opportunities': 1,
            'recommended_actions': []
        }
        
        mock_phase2 = {
            'active_plans': 0,
            'new_plans_created': 0,
            'phase_actions': []
        }
        
        with pytest.MonkeyPatch().context() as m:
            m.setattr('ai.victory_ai.victory_ai_phase1_controller',
                     lambda engine, units, player_id: mock_phase1)
            m.setattr('ai.victory_ai.victory_ai_phase2_controller', 
                     lambda engine, units, player_id: mock_phase2)
            
            result = integrate_victory_ai_full(mock_engine, my_units, player_id)
        
        assert result['victory_ai_active'] == True
        assert 'phase1' in result
        assert 'phase2' in result
        assert result['total_opportunities'] == 1
        assert result['active_attack_plans'] == 0
        assert 'recommended_actions' in result


class TestPlanCleanup:
    """Testy czyszczenia starych planów"""
    
    def test_cleanup_old_plans(self):
        """Test usuwania starych i zakończonych planów"""
        # Setup - dodaj plany do cache
        ATTACK_PLAN_CACHE.clear()
        
        # Plan completed 3 tury temu (powinien być usunięty)
        ATTACK_PLAN_CACHE['old-completed'] = {
            'player_id': 1,
            'status': 'COMPLETED',
            'created_turn': 5
        }
        
        # Plan bardzo stary (10 tur, powinien być usunięty)
        ATTACK_PLAN_CACHE['very-old'] = {
            'player_id': 1, 
            'status': 'PLANNING',
            'created_turn': 2
        }
        
        # Plan recent completed (powinien zostać)
        ATTACK_PLAN_CACHE['recent-completed'] = {
            'player_id': 1,
            'status': 'COMPLETED', 
            'created_turn': 10
        }
        
        # Plan dla innego gracza (powinien zostać)
        ATTACK_PLAN_CACHE['other-player'] = {
            'player_id': 2,
            'status': 'COMPLETED',
            'created_turn': 5
        }
        
        # Execute cleanup dla player 1, current turn 12
        cleanup_old_plans(player_id=1, current_turn=12)
        
        # Verify
        remaining_plans = list(ATTACK_PLAN_CACHE.keys())
        assert 'old-completed' not in remaining_plans  # Usunięty (completed > 2 turns ago)
        assert 'very-old' not in remaining_plans       # Usunięty (> 8 turns old)
        assert 'recent-completed' in remaining_plans   # Zostaje (completed tylko 2 tury temu)
        assert 'other-player' in remaining_plans       # Zostaje (inny gracz)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
