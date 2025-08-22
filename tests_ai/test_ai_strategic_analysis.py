"""
Testy analizy strategicznej AI Generała - FAZA 1
Sprawdza czy AI prawidłowo analizuje VP, Key Points i fazę gry
"""
import pytest
from unittest.mock import Mock, MagicMock
from ai.ai_general import AIGeneral

class TestStrategicAnalysis:
    
    @pytest.fixture
    def ai_general(self):
        return AIGeneral(nationality="polish")
    
    @pytest.fixture
    def mock_player(self):
        player = Mock()
        player.nation = "Polska"
        player.victory_points = 50
        player.economy = Mock()
        player.economy.get_points.return_value = {'economic_points': 100, 'special_points': 20}
        return player
    
    @pytest.fixture
    def mock_game_engine(self):
        engine = Mock()
        engine.turn = 10
        engine.current_turn = 10
        
        # Mock victory conditions
        engine.victory_conditions = Mock()
        engine.victory_conditions.max_turns = 30
        
        # Mock players with VP
        enemy_player = Mock()
        enemy_player.nation = "Niemcy"
        enemy_player.victory_points = 30
        
        engine.players = [enemy_player]
        
        # Mock Key Points
        engine.key_points_state = {
            'hex_1': {'controlled_by': 'Polska', 'value': 10, 'type': 'Factory'},
            'hex_2': {'controlled_by': 'Niemcy', 'value': 15, 'type': 'Resource'},
            'hex_3': {'controlled_by': None, 'value': 5, 'type': 'Town'}
        }
        
        return engine
    
    def test_analyze_strategic_situation_basic(self, ai_general, mock_game_engine, mock_player):
        """Test podstawowej analizy strategicznej"""
        result = ai_general.analyze_strategic_situation(mock_game_engine, mock_player)
        
        assert result is not None
        assert 'vp_own' in result
        assert 'vp_enemy' in result
        assert 'vp_status' in result
        assert 'current_turn' in result
        assert 'max_turns' in result
        assert 'game_phase' in result
        assert 'key_points_our' in result
        
    def test_vp_analysis_winning(self, ai_general, mock_game_engine, mock_player):
        """Test analizy VP gdy wygrywamy"""
        mock_player.victory_points = 80
        mock_game_engine.players[0].victory_points = 60
        
        result = ai_general.analyze_strategic_situation(mock_game_engine, mock_player)
        
        assert result['vp_own'] == 80
        assert result['vp_enemy'] == 60
        assert result['vp_status'] == 20  # 80 - 60
        assert result['vp_situation'] == "WYGRYWAMY"
        
    def test_vp_analysis_losing(self, ai_general, mock_game_engine, mock_player):
        """Test analizy VP gdy przegrywamy"""
        mock_player.victory_points = 40
        mock_game_engine.players[0].victory_points = 70
        
        result = ai_general.analyze_strategic_situation(mock_game_engine, mock_player)
        
        assert result['vp_status'] == -30  # 40 - 70
        assert result['vp_situation'] == "PRZEGRYWAMY"
        
    def test_game_phase_analysis(self, ai_general, mock_game_engine, mock_player):
        """Test analizy fazy gry"""
        # Wczesna faza (tura 5/30)
        mock_game_engine.turn = 5
        mock_game_engine.current_turn = 5
        result = ai_general.analyze_strategic_situation(mock_game_engine, mock_player)
        assert result['phase_name'] == "WCZESNA"
        assert result['game_phase'] <= 1.0
        
        # Średnia faza (tura 15/30)
        mock_game_engine.turn = 15
        mock_game_engine.current_turn = 15
        result = ai_general.analyze_strategic_situation(mock_game_engine, mock_player)
        assert result['phase_name'] == "ŚREDNIA"
        assert 1.0 < result['game_phase'] <= 2.0
        
        # Późna faza (tura 25/30)
        mock_game_engine.turn = 25
        mock_game_engine.current_turn = 25
        result = ai_general.analyze_strategic_situation(mock_game_engine, mock_player)
        assert result['phase_name'] == "PÓŹNA"
        assert result['game_phase'] > 2.0
        
    def test_key_points_analysis(self, ai_general, mock_game_engine, mock_player):
        """Test analizy Key Points"""
        result = ai_general.analyze_strategic_situation(mock_game_engine, mock_player)
        
        assert result['key_points_our'] == 1     # Jedna Polska
        assert result['key_points_enemy'] == 1   # Jedna Niemcy  
        assert result['key_points_neutral'] == 1 # Jedna neutralna
        assert result['key_points_income'] == 10 # Dochód z polskiego KP
        
    def test_units_analysis_per_commander(self, ai_general, mock_game_engine, mock_player):
        """Test analizy jednostek per dowódca"""
        # Mock tokens
        mock_tokens = []
        for i in range(3):
            token = Mock()
            token.maxFuel = 100
            token.currentFuel = 20 if i == 0 else 80  # Pierwsza z niskim paliwem
            token.combat_value = 5
            token.unitType = "P"
            token.owner = "1"  # Dowódca 1
            token.id = f"token_{i}"
            mock_tokens.append(token)
            
        mock_game_engine.get_visible_tokens.return_value = mock_tokens
        
        ai_general.analyze_units(mock_game_engine, mock_player)
        
        analysis = ai_general._unit_analysis
        assert analysis['total_units'] == 3
        assert analysis['low_fuel_units'] == 1
        assert analysis['avg_combat_value'] == 5.0
        assert '1' in analysis['commanders_analysis']
        
        commander_data = analysis['commanders_analysis']['1']
        assert commander_data['total'] == 3
        assert commander_data['low_fuel'] == 1
        assert commander_data['avg_combat'] == 5.0
        assert commander_data['low_fuel_ratio'] == 1/3
