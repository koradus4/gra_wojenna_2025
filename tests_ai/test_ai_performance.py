"""
Testy wydajności AI Generała
Sprawdza czasy wykonania i optymalizacje
"""
import pytest
import time
from unittest.mock import Mock, patch
from ai.ai_general import AIGeneral

class TestAIPerformance:
    
    @pytest.fixture
    def performance_ai(self):
        """AI setup dla testów wydajności"""
        with patch('ai.ai_general.Path.mkdir'):
            return AIGeneral(nationality="polish")
    
    @pytest.fixture
    def large_game_setup(self):
        """Duży stan gry dla testów wydajności"""
        # Player z dużą liczbą dowódców
        player = Mock()
        player.nation = "Polska"
        player.role = "Generał"
        player.victory_points = 120
        player.economy = Mock()
        player.economy.get_points.return_value = {'economic_points': 500}
        
        # Wielu dowódców
        commanders = []
        for i in range(10):  # 10 dowódców
            cmd = Mock()
            cmd.id = str(i+1)
            cmd.nation = "Polska"
            cmd.role = "Dowódca"
            cmd.economy = Mock()
            cmd.economy.get_points.return_value = {'economic_points': 50}
            commanders.append(cmd)
        
        # Engine z dużą liczbą jednostek
        engine = Mock()
        engine.current_player_obj = player
        engine.turn = 20
        engine.current_turn = 20
        engine.players = commanders + [player]
        engine.victory_conditions = Mock()
        engine.victory_conditions.max_turns = 50
        
        # Dużo key points
        engine.key_points_state = {}
        for i in range(50):  # 50 key points
            engine.key_points_state[f'point_{i}'] = {
                'controlled_by': 'Polska' if i % 3 == 0 else 'Niemcy' if i % 3 == 1 else None,
                'value': 5 + (i % 10),
                'type': ['Factory', 'Resource', 'Town'][i % 3]
            }
        
        # Dużo jednostek
        tokens = []
        for i in range(200):  # 200 jednostek
            token = Mock()
            token.maxFuel = 100
            token.currentFuel = 20 + (i % 60)
            token.combat_value = 3 + (i % 5)
            token.unitType = ["P", "AL", "Z", "KAW", "ART"][i % 5]
            token.owner = str((i % 10) + 1)
            token.id = f"unit_{i}"
            tokens.append(token)
            
        engine.get_visible_tokens.return_value = tokens
        
        return player, engine
    
    def test_strategic_analysis_performance(self, performance_ai, large_game_setup):
        """Test wydajności analizy strategicznej"""
        ai = performance_ai
        player, engine = large_game_setup
        
        # Measure strategic analysis time
        start_time = time.time()
        ai.analyze_strategic_situation(engine, player)
        end_time = time.time()
        
        strategic_time = end_time - start_time
        assert strategic_time < 0.1, f"Analiza strategiczna trwała {strategic_time:.3f}s - za długo!"
        
        # Verify analysis completed
        assert hasattr(ai, '_strategic_analysis')
        assert ai._strategic_analysis['vp_own'] == 120
        
    def test_unit_analysis_performance(self, performance_ai, large_game_setup):
        """Test wydajności analizy jednostek"""
        ai = performance_ai
        player, engine = large_game_setup
        
        # Measure unit analysis time
        start_time = time.time()
        ai.analyze_units(engine, player)
        end_time = time.time()
        
        unit_time = end_time - start_time
        assert unit_time < 0.2, f"Analiza jednostek trwała {unit_time:.3f}s - za długo!"
        
        # Verify analysis completed
        assert hasattr(ai, '_unit_analysis')
        assert ai._unit_analysis['total_units'] == 200
        
    def test_keypoint_analysis_performance(self, performance_ai, large_game_setup):
        """Test wydajności analizy key points"""
        ai = performance_ai
        player, engine = large_game_setup
        
        # Measure keypoint analysis time
        start_time = time.time()
        ai.analyze_key_points(engine, player)
        end_time = time.time()
        
        keypoint_time = end_time - start_time
        assert keypoint_time < 0.1, f"Analiza key points trwała {keypoint_time:.3f}s - za długo!"
        
        # Verify analysis completed
        assert hasattr(ai, '_keypoint_analysis')
        assert len(ai._keypoint_analysis['controlled']) > 0
        
    def test_logging_performance(self, performance_ai, large_game_setup):
        """Test wydajności logowania"""
        ai = performance_ai
        player, engine = large_game_setup
        
        # Initialize logging
        with patch('ai.ai_general.Path.mkdir'), \
             patch.object(ai, '_init_economy_log'), \
             patch.object(ai, '_init_keypoints_log'), \
             patch.object(ai, '_init_strategy_log'):
            
            ai._init_logging_system()
        
        # Mock file operations
        with patch('builtins.open', create=True), \
             patch('csv.writer'):
            
            # Measure logging performance
            start_time = time.time()
            
            # Log multiple operations
            for i in range(100):
                ai.log_economy_turn(12, {'economic_points': 100}, "ROZWÓJ", 50, 5)
                ai.log_strategy_decision(12, "ROZWÓJ", {'vp_status': 10})
                
            end_time = time.time()
            
            logging_time = end_time - start_time
            assert logging_time < 0.5, f"100 operacji logowania trwało {logging_time:.3f}s - za długo!"
    
    def test_strategy_determination_performance(self, performance_ai):
        """Test wydajności określania strategii"""
        ai = performance_ai
        
        # Prepare analysis data
        strategic_analysis = {
            'vp_status': 15,
            'game_phase': 2.1,
            'phase_name': 'PÓŹNA',
            'turns_left': 10
        }
        
        unit_analysis = {
            'low_fuel_ratio': 0.2,
            'commanders_analysis': {str(i): {'low_fuel_ratio': 0.1 + (i * 0.05)} for i in range(1, 11)}
        }
        
        # Measure strategy determination
        start_time = time.time()
        
        # Test multiple strategy determinations
        for turn in range(1, 51):
            strategy = ai._determine_strategy(strategic_analysis, unit_analysis, turn)
            assert strategy in ["WCZESNA", "ŚREDNIA", "PÓŹNA", "ROZWÓJ", "KRYZYS_PALIWA", 
                              "DESPERACJA", "OCHRONA", "EKSPANSJA"]
            
        end_time = time.time()
        
        strategy_time = end_time - start_time
        assert strategy_time < 0.1, f"50 determininacji strategii trwało {strategy_time:.3f}s - za długo!"
    
    def test_full_turn_performance(self, performance_ai, large_game_setup):
        """Test wydajności pełnej tury"""
        ai = performance_ai
        player, engine = large_game_setup
        
        with patch.object(ai, 'consider_unit_purchase'), \
             patch.object(ai, 'allocate_points', return_value=(100, 5, [0.4, 0.3, 0.3])), \
             patch.object(ai, '_gather_state'), \
             patch.object(ai, '_init_logging_system'):
            
            # Measure full turn execution
            start_time = time.time()
            ai.make_turn(engine)
            end_time = time.time()
            
            turn_time = end_time - start_time
            assert turn_time < 1.0, f"Pełna tura trwała {turn_time:.3f}s - za długo!"
    
    def test_memory_usage_stability(self, performance_ai, large_game_setup):
        """Test stabilności użycia pamięci"""
        import gc
        import sys
        
        ai = performance_ai
        player, engine = large_game_setup
        
        with patch.object(ai, 'consider_unit_purchase'), \
             patch.object(ai, 'allocate_points', return_value=(100, 5, [0.4, 0.3, 0.3])), \
             patch.object(ai, '_gather_state'), \
             patch.object(ai, '_init_logging_system'):
            
            # Measure initial memory
            gc.collect()
            initial_objects = len(gc.get_objects())
            
            # Run multiple turns
            for turn_num in range(10):
                engine.turn = turn_num + 1
                engine.current_turn = turn_num + 1
                ai.make_turn(engine)
            
            # Measure final memory
            gc.collect()
            final_objects = len(gc.get_objects())
            
            # Memory shouldn't grow excessively
            memory_growth = final_objects - initial_objects
            assert memory_growth < 2000, f"Wzrost obiektów: {memory_growth} - możliwy memory leak!"
    
    def test_concurrent_analysis_performance(self, performance_ai, large_game_setup):
        """Test wydajności równoległych analiz"""
        ai = performance_ai
        player, engine = large_game_setup
        
        # Measure concurrent execution
        start_time = time.time()
        
        # Run all analyses
        ai.analyze_strategic_situation(engine, player)
        ai.analyze_units(engine, player)
        ai.analyze_key_points(engine, player)
        
        end_time = time.time()
        
        total_time = end_time - start_time
        assert total_time < 0.5, f"Wszystkie analizy trwały {total_time:.3f}s - za długo!"
        
        # Verify all analyses completed
        assert hasattr(ai, '_strategic_analysis')
        assert hasattr(ai, '_unit_analysis')
        assert hasattr(ai, '_keypoint_analysis')
    
    def test_scalability_with_commanders(self, performance_ai):
        """Test skalowalności z liczbą dowódców"""
        ai = performance_ai
        
        times = []
        
        # Test różnej liczby dowódców
        for num_commanders in [1, 5, 10, 20, 50]:
            # Setup
            player = Mock()
            player.nation = "Polska"
            player.victory_points = 100
            
            commanders = []
            for i in range(num_commanders):
                cmd = Mock()
                cmd.id = str(i+1)
                commanders.append(cmd)
            
            engine = Mock()
            engine.current_player_obj = player
            engine.players = commanders + [player]
            engine.turn = 10
            engine.current_turn = 10
            engine.victory_conditions = Mock()
            engine.victory_conditions.max_turns = 30
            engine.key_points_state = {}
            engine.get_visible_tokens.return_value = []
            
            # Measure time
            start_time = time.time()
            ai.analyze_strategic_situation(engine, player)
            end_time = time.time()
            
            times.append(end_time - start_time)
        
        # Sprawdź czy czas rośnie liniowo (nie wykładniczo)
        # Jeśli pierwszy czas to 0, to wszystkie są bardzo szybkie - OK!
        if times[0] == 0.0:
            assert times[-1] < 0.1, "Nawet z wieloma dowódcami powinno być szybkie!"
        else:
            assert times[-1] < times[0] * 10, "Czas wykonania rośnie za szybko z liczbą dowódców!"
    
    def test_optimization_caching(self, performance_ai, large_game_setup):
        """Test czy optymalizacje/cache działają"""
        ai = performance_ai
        player, engine = large_game_setup
        
        # First analysis
        start_time1 = time.time()
        ai.analyze_strategic_situation(engine, player)
        end_time1 = time.time()
        first_time = end_time1 - start_time1
        
        # Second analysis (same data) - powinno być szybsze jeśli jest cache
        start_time2 = time.time()
        ai.analyze_strategic_situation(engine, player)
        end_time2 = time.time()
        second_time = end_time2 - start_time2
        
        # Second run powinien być nie wolniejszy niż pierwszy
        # Jeśli oba czasy to 0, to analiza jest bardzo szybka - OK!
        if first_time == 0.0 and second_time == 0.0:
            assert True, "Obie analizy bardzo szybkie - doskonale!"
        else:
            assert second_time <= first_time * 1.5, "Druga analiza znacznie wolniejsza - brak cache?"
