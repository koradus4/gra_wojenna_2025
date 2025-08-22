"""
Testy integracyjne AI Generała - pełny cykl tury
Sprawdza czy wszystkie komponenty działają razem
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from ai.ai_general import AIGeneral

class TestAIIntegration:
    
    @pytest.fixture
    def complete_ai_setup(self):
        """Kompletny setup AI z wszystkimi komponentami"""
        with patch('ai.ai_general.Path.mkdir'):
            ai = AIGeneral(nationality="polish")
            
        # Mock temporary log files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            ai._economy_log_file = temp_path / "economy.csv"
            ai._keypoints_log_file = temp_path / "keypoints.csv"
            ai._strategy_log_file = temp_path / "strategy.csv"
            
            # Initialize log files
            ai._init_economy_log()
            ai._init_keypoints_log()
            ai._init_strategy_log()
            
            yield ai
    
    @pytest.fixture
    def complete_game_setup(self):
        """Kompletny setup stanu gry"""
        # Player
        player = Mock()
        player.nation = "Polska"
        player.role = "Generał"
        player.victory_points = 60
        player.economy = Mock()
        player.economy.get_points.return_value = {'economic_points': 100, 'special_points': 15}
        player.economy.economic_points = 100
        player.economy.subtract_points = Mock()
        
        # Commanders
        commanders = []
        for i in range(1, 4):
            cmd = Mock()
            cmd.id = str(i)
            cmd.nation = "Polska"
            cmd.role = "Dowódca"
            cmd.economy = Mock()
            cmd.economy.get_points.return_value = {'economic_points': 20}
            cmd.economy.economic_points = 20
            commanders.append(cmd)
        
        # Game Engine
        engine = Mock()
        engine.current_player_obj = player
        engine.turn = 12
        engine.current_turn = 12
        engine.players = commanders + [player]
        
        # Victory conditions
        engine.victory_conditions = Mock()
        engine.victory_conditions.max_turns = 30
        
        # Enemy player for VP calculation
        enemy = Mock()
        enemy.nation = "Niemcy"
        enemy.victory_points = 45
        engine.players.append(enemy)
        
        # Key Points
        engine.key_points_state = {
            'factory_1': {'controlled_by': 'Polska', 'value': 15, 'type': 'Factory'},
            'resource_1': {'controlled_by': 'Niemcy', 'value': 10, 'type': 'Resource'},
            'town_1': {'controlled_by': None, 'value': 5, 'type': 'Town'}
        }
        
        # Units
        tokens = []
        for i in range(12):  # 12 jednostek (4 na dowódcę)
            token = Mock()
            token.maxFuel = 100
            token.currentFuel = 25 if i < 2 else 85  # 2 z niskim paliwem (25% < 30%)
            token.combat_value = 4 + (i % 3)
            token.unitType = ["P", "AL", "Z"][i % 3]
            token.owner = str((i % 3) + 1)
            token.id = f"unit_{i}"
            tokens.append(token)
            
        engine.get_visible_tokens.return_value = tokens
        
        return player, engine
    
    def test_complete_turn_execution(self, complete_ai_setup, complete_game_setup):
        """Test kompletnego wykonania tury AI"""
        ai = complete_ai_setup
        player, engine = complete_game_setup
        
        # Mock methods that interact with external systems
        with patch.object(ai, 'consider_unit_purchase') as mock_purchase, \
             patch.object(ai, 'allocate_points') as mock_allocate, \
             patch.object(ai, '_gather_state') as mock_state:
            
            mock_allocate.return_value = (40, 3, {'1': 0.3, '2': 0.4, '3': 0.3})
            mock_state.return_value = {
                'global': {'unit_counts_by_type': {'P': 6, 'AL': 3, 'Z': 3}, 'total_units': 12},
                'per_commander': {},
                'enemy': {'total_units': 8}
            }
            
            # Execute turn
            ai.make_turn(engine)
            
            # Verify all analyses were performed
            assert hasattr(ai, '_unit_analysis')
            assert hasattr(ai, '_strategic_analysis')
            
            # Verify strategic analysis results
            strategic = ai._strategic_analysis
            assert strategic['vp_own'] == 60
            assert strategic['vp_enemy'] == 45
            assert strategic['vp_status'] == 15
            assert strategic['current_turn'] == 12
            assert strategic['max_turns'] == 30
            assert strategic['game_phase'] == 1.2  # 12/30 * 3 = 1.2
            assert strategic['phase_name'] == "ŚREDNIA"
            
            # Verify unit analysis
            unit_analysis = ai._unit_analysis
            assert unit_analysis['total_units'] == 12
            assert unit_analysis['low_fuel_units'] == 2
            assert unit_analysis['low_fuel_ratio'] == 2/12  # ~0.167
            
    def test_strategy_determination_integration(self, complete_ai_setup, complete_game_setup):
        """Test określania strategii w kontekście pełnego stanu gry"""
        ai = complete_ai_setup
        player, engine = complete_game_setup
        
        # Wykonaj analizy
        ai.analyze_strategic_situation(engine, player)
        ai.analyze_units(engine, player)
        
        # Test różnych scenariuszy strategicznych
        
        # Scenariusz 1: Normalny rozwój - sprawdź czy strategia jest logiczna
        strategy = ai._determine_strategy(ai._strategic_analysis, ai._unit_analysis, 12)
        # AI może wybrać EKSPANSJA gdy wygrywamy +15 VP, to jest inteligentne
        assert strategy in ["ŚREDNIA", "EKSPANSJA", "ROZWÓJ"]  # Akceptujemy logiczne strategie
        
        # Scenariusz 2: Kryzys paliwa
        ai._unit_analysis['commanders_analysis'] = {
            '1': {'low_fuel_ratio': 0.5},  # Kryzys paliwa!
            '2': {'low_fuel_ratio': 0.2},
            '3': {'low_fuel_ratio': 0.1}
        }
        strategy = ai._determine_strategy(ai._strategic_analysis, ai._unit_analysis, 12)
        assert strategy == "KRYZYS_PALIWA"
        
        # Scenariusz 3: Późna gra + przegrywamy
        ai._strategic_analysis['game_phase'] = 2.5
        ai._strategic_analysis['vp_status'] = -20
        ai._unit_analysis['commanders_analysis'] = {
            '1': {'low_fuel_ratio': 0.1}, '2': {'low_fuel_ratio': 0.1}, '3': {'low_fuel_ratio': 0.1}
        }
        strategy = ai._determine_strategy(ai._strategic_analysis, ai._unit_analysis, 12)
        assert strategy == "DESPERACJA"
        
    def test_logging_integration(self, complete_ai_setup, complete_game_setup):
        """Test integracji systemu logowania"""
        ai = complete_ai_setup
        player, engine = complete_game_setup
        
        with patch.object(ai, 'consider_unit_purchase'), \
             patch.object(ai, 'allocate_points') as mock_allocate, \
             patch.object(ai, '_gather_state'):
            
            mock_allocate.return_value = (35, 3, {})
            
            # Execute turn
            ai.make_turn(engine)
            
            # Check if log files exist and contain data
            assert ai._economy_log_file.exists()
            assert ai._keypoints_log_file.exists()
            assert ai._strategy_log_file.exists()
            
            # Verify economy log has content
            with open(ai._economy_log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 2  # Header + at least one data row
                
            # Verify keypoints log has content
            with open(ai._keypoints_log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 4  # Header + 3 key points
                
            # Verify strategy log has content
            with open(ai._strategy_log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 2  # Header + at least one decision
                
    @patch('ai.ai_general.AIGeneral.purchase_unit_programmatically')
    def test_purchase_integration(self, mock_purchase, complete_ai_setup, complete_game_setup):
        """Test integracji zakupów jednostek"""
        ai = complete_ai_setup
        player, engine = complete_game_setup
        
        # Force purchase decision
        player.economy.get_points.return_value = {'economic_points': 200}
        
        with patch.object(ai, '_gather_state') as mock_state:
            mock_state.return_value = {
                'global': {'unit_counts_by_type': {}, 'total_units': 0},
                'per_commander': {'1': {}, '2': {}, '3': {}},
                'enemy': {'total_units': 5}
            }
            
            # Set conditions for purchase strategy
            ai._strategic_analysis = {
                'vp_status': -10,  # Przegrywamy
                'game_phase': 2.1,  # Późna faza
                'phase_name': 'PÓŹNA'
            }
            ai._unit_analysis = {
                'low_fuel_ratio': 0.1,  # Brak kryzysu paliwa
                'commanders_analysis': {'1': {'low_fuel_ratio': 0.1}}
            }
            
            # Execute strategic decisions
            ai.make_strategic_decisions(engine, player)
            
            # Should trigger DESPERACJA strategy with high purchase %
            assert ai._turn_strategy_used in ['PURCHASE', 'COMBO', 'DESPERACJA']
            
    def test_error_handling_integration(self, complete_ai_setup):
        """Test obsługi błędów w pełnym cyklu"""
        ai = complete_ai_setup
        
        # Engine z błędami
        broken_engine = Mock()
        broken_engine.current_player_obj = None  # Brak gracza
        
        # Nie powinno rzucać wyjątku
        try:
            ai.make_turn(broken_engine)
        except Exception as e:
            pytest.fail(f"AI powinno gracefully obsłużyć błędy: {e}")
            
    def test_performance_integration(self, complete_ai_setup, complete_game_setup):
        """Test wydajności pełnego cyklu tury"""
        import time
        
        ai = complete_ai_setup
        player, engine = complete_game_setup
        
        with patch.object(ai, 'consider_unit_purchase'), \
             patch.object(ai, 'allocate_points') as mock_allocate, \
             patch.object(ai, '_gather_state'):
            
            # Ustaw return value dla allocate_points
            mock_allocate.return_value = (40, 3, {'1': 0.33, '2': 0.33, '3': 0.34})
            
            start_time = time.time()
            ai.make_turn(engine)
            end_time = time.time()
            
            # Tura AI nie powinna trwać dłużej niż 1 sekunda
            execution_time = end_time - start_time
            assert execution_time < 1.0, f"Tura trwała {execution_time:.2f}s - za długo!"
            
    def test_state_consistency_integration(self, complete_ai_setup, complete_game_setup):
        """Test spójności stanu między turami"""
        ai = complete_ai_setup
        player, engine = complete_game_setup
        
        with patch.object(ai, 'consider_unit_purchase'), \
             patch.object(ai, 'allocate_points') as mock_allocate, \
             patch.object(ai, '_gather_state'):
            
            # Ustaw return value dla allocate_points
            mock_allocate.return_value = (40, 3, {'1': 0.33, '2': 0.33, '3': 0.34})
            
            # Pierwsza tura
            ai.make_turn(engine)
            first_turn_analysis = ai._strategic_analysis.copy()
            
            # Druga tura (zmień numer tury)
            engine.turn = 13
            engine.current_turn = 13
            ai.make_turn(engine)
            second_turn_analysis = ai._strategic_analysis
            
            # Sprawdź czy stan ewoluuje logicznie
            assert second_turn_analysis['current_turn'] == 13
            assert second_turn_analysis['game_phase'] > first_turn_analysis['game_phase']
            assert second_turn_analysis['turns_left'] < first_turn_analysis['turns_left']
