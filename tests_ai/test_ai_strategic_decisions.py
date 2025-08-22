"""
Testy strategicznych decyzji AI Generała - FAZA 3 & 4
Sprawdza nową logikę decide_action z 5 strategiami i elastycznym budżetem
"""
import pytest
from unittest.mock import Mock
from ai.ai_general import AIGeneral, EconAction, BUDGET_STRATEGIES

class TestStrategicDecisions:
    
    @pytest.fixture
    def ai_general(self):
        ai = AIGeneral(nationality="polish")
        # Ustaw analizy strategiczne
        ai._strategic_analysis = {
            'vp_own': 50,
            'vp_enemy': 40,
            'vp_status': 10,
            'game_phase': 1.5,
            'phase_name': 'ŚREDNIA'
        }
        ai._unit_analysis = {
            'low_fuel_ratio': 0.1,
            'commanders_analysis': {
                '1': {'low_fuel_ratio': 0.1},
                '2': {'low_fuel_ratio': 0.15}
            }
        }
        return ai
    
    @pytest.fixture
    def mock_player(self):
        player = Mock()
        player.economy = Mock()
        player.economy.get_points.return_value = {'economic_points': 100}
        return player
    
    @pytest.fixture  
    def mock_game_engine(self):
        engine = Mock()
        engine.get_visible_tokens.return_value = [Mock() for _ in range(8)]  # 8 jednostek
        return engine
        
    def test_strategy_development_early_game(self, ai_general):
        """Test strategii ROZWÓJ w wczesnej fazie gry"""
        ai_general._strategic_analysis['game_phase'] = 0.8
        ai_general._unit_analysis['commanders_analysis'] = {
            '1': {'low_fuel_ratio': 0.1}  # Niski kryzys paliwa
        }
        
        strategy = ai_general._determine_strategy(
            ai_general._strategic_analysis,
            ai_general._unit_analysis,
            8
        )
        
        assert strategy == 'ROZWÓJ'
        
    def test_strategy_fuel_crisis(self, ai_general):
        """Test strategii KRYZYS_PALIWA"""
        ai_general._unit_analysis['commanders_analysis'] = {
            '1': {'low_fuel_ratio': 0.4},  # >0.3 = kryzys paliwa
            '2': {'low_fuel_ratio': 0.2}
        }
        
        strategy = ai_general._determine_strategy(
            ai_general._strategic_analysis,
            ai_general._unit_analysis,
            8
        )
        
        assert strategy == 'KRYZYS_PALIWA'
        
    def test_strategy_desperation_late_game_losing(self, ai_general):
        """Test strategii DESPERACJA - późna gra + przegrywamy VP"""
        ai_general._strategic_analysis.update({
            'game_phase': 2.5,  # Późna faza
            'vp_status': -20    # Przegrywamy VP
        })
        ai_general._unit_analysis['commanders_analysis'] = {
            '1': {'low_fuel_ratio': 0.1}  # Brak kryzysu paliwa
        }
        
        strategy = ai_general._determine_strategy(
            ai_general._strategic_analysis,
            ai_general._unit_analysis,
            8
        )
        
        assert strategy == 'DESPERACJA'
        
    def test_strategy_protection_late_game_winning(self, ai_general):
        """Test strategii OCHRONA - późna gra + wygrywamy VP"""
        ai_general._strategic_analysis.update({
            'game_phase': 2.2,  # Późna faza
            'vp_status': 15     # Wygrywamy VP
        })
        ai_general._unit_analysis['commanders_analysis'] = {
            '1': {'low_fuel_ratio': 0.1}  # Brak kryzysu paliwa
        }
        
        strategy = ai_general._determine_strategy(
            ai_general._strategic_analysis,
            ai_general._unit_analysis,
            8
        )
        
        assert strategy == 'OCHRONA'
        
    def test_strategy_expansion_mid_game(self, ai_general):
        """Test strategii EKSPANSJA - średnia faza"""
        ai_general._strategic_analysis.update({
            'game_phase': 1.8,  # Średnia faza
            'vp_status': 5      # Lekko wygrywamy
        })
        ai_general._unit_analysis['commanders_analysis'] = {
            '1': {'low_fuel_ratio': 0.2}  # Brak kryzysu paliwa
        }
        
        strategy = ai_general._determine_strategy(
            ai_general._strategic_analysis,
            ai_general._unit_analysis,
            8
        )
        
        assert strategy == 'EKSPANSJA'
        
    def test_decision_combo_sufficient_budget(self, ai_general, mock_player, mock_game_engine):
        """Test decyzji COMBO przy wystarczającym budżecie"""
        mock_player.economy.get_points.return_value = {'economic_points': 120}
        
        action, metrics = ai_general.decide_action(mock_player, mock_game_engine)
        
        assert action == EconAction.COMBO
        assert 'allocate_budget' in metrics
        assert 'purchase_budget' in metrics
        assert metrics['allocate_budget'] >= 20
        assert metrics['purchase_budget'] >= 20
        
    def test_decision_hold_insufficient_budget(self, ai_general, mock_player, mock_game_engine):
        """Test decyzji HOLD przy niskim budżecie"""
        mock_player.economy.get_points.return_value = {'economic_points': 25}  # < MIN_BUY
        
        action, metrics = ai_general.decide_action(mock_player, mock_game_engine)
        
        assert action == EconAction.HOLD
        assert metrics['rule'] == 'econ<MIN_BUY'
        
    def test_budget_ratios_development(self, ai_general):
        """Test proporcji budżetu dla strategii ROZWÓJ"""
        ratios = BUDGET_STRATEGIES['ROZWÓJ']
        
        assert ratios['reserve'] == 0.20    # 20%
        assert ratios['allocate'] == 0.40   # 40%
        assert ratios['purchase'] == 0.40   # 40%
        assert sum(ratios.values()) == 1.0  # 100%
        
    def test_budget_ratios_fuel_crisis(self, ai_general):
        """Test proporcji budżetu dla strategii KRYZYS_PALIWA"""
        ratios = BUDGET_STRATEGIES['KRYZYS_PALIWA']
        
        assert ratios['allocate'] == 0.70   # 70% na alokację (uzupełnienia)
        assert ratios['purchase'] == 0.15   # 15% na zakupy
        assert ratios['reserve'] == 0.15    # 15% rezerwa
        
    def test_budget_ratios_desperation(self, ai_general):
        """Test proporcji budżetu dla strategii DESPERACJA"""
        ratios = BUDGET_STRATEGIES['DESPERACJA']
        
        assert ratios['purchase'] == 0.65   # 65% na zakupy (agresja)
        assert ratios['allocate'] == 0.25   # 25% na alokację
        assert ratios['reserve'] == 0.10    # 10% rezerwa
        
    def test_metrics_contain_strategy_info(self, ai_general, mock_player, mock_game_engine):
        """Test czy metryki zawierają informacje strategiczne"""
        action, metrics = ai_general.decide_action(mock_player, mock_game_engine)
        
        assert 'strategy_name' in metrics
        assert 'budget_ratios' in metrics
        assert 'game_phase' in metrics
        assert 'vp_status' in metrics
        assert metrics['strategy_name'] in BUDGET_STRATEGIES.keys()
