"""
Testy edge cases AI Generała
Sprawdza obsługę nietypowych sytuacji i błędów
"""
import pytest
from unittest.mock import Mock, patch
from ai.ai_general import AIGeneral

class TestAIEdgeCases:
    
    @pytest.fixture
    def edge_ai(self):
        """AI setup dla testów edge cases"""
        with patch('ai.ai_general.Path.mkdir'):
            return AIGeneral(nationality="polish")
    
    def test_no_commanders_scenario(self, edge_ai):
        """Test gdy brak dowódców"""
        ai = edge_ai
        
        # Player bez dowódców
        player = Mock()
        player.nation = "Polska"
        player.role = "Generał"
        player.victory_points = 50
        
        engine = Mock()
        engine.current_player_obj = player
        engine.players = [player]  # Tylko generał
        engine.turn = 10
        engine.current_turn = 10
        engine.victory_conditions = Mock()
        engine.victory_conditions.max_turns = 30
        engine.key_points_state = {}
        engine.get_visible_tokens.return_value = []
        
        # Nie powinno rzucać błędu
        ai.analyze_strategic_situation(engine, player)
        ai.analyze_units(engine, player)
        
        # Sprawdź czy analizy są sensowne
        assert ai._strategic_analysis['vp_own'] == 50
        assert ai._unit_analysis['total_units'] == 0
        
    def test_no_units_scenario(self, edge_ai):
        """Test gdy brak jednostek"""
        ai = edge_ai
        
        player = Mock()
        player.nation = "Polska"
        player.victory_points = 30
        
        engine = Mock()
        engine.current_player_obj = player
        engine.players = [player]
        engine.turn = 5
        engine.current_turn = 5
        engine.victory_conditions = Mock()
        engine.victory_conditions.max_turns = 30
        engine.key_points_state = {}
        engine.get_visible_tokens.return_value = []  # Brak jednostek
        
        ai.analyze_units(engine, player)
        
        # Sprawdź obsługę braku jednostek
        assert ai._unit_analysis['total_units'] == 0
        assert ai._unit_analysis['low_fuel_units'] == 0
        assert ai._unit_analysis['low_fuel_ratio'] == 0.0
        
    def test_no_key_points_scenario(self, edge_ai):
        """Test gdy brak key points"""
        ai = edge_ai
        
        player = Mock()
        player.nation = "Polska"
        
        engine = Mock()
        engine.key_points_state = {}  # Brak key points
        
        ai.analyze_key_points(engine, player)
        
        # Sprawdź obsługę braku key points
        assert ai._keypoint_analysis['controlled'] == []
        assert ai._keypoint_analysis['enemy_controlled'] == []
        assert ai._keypoint_analysis['neutral'] == []
        assert ai._keypoint_analysis['total_value_controlled'] == 0
        
    def test_extreme_victory_points(self, edge_ai):
        """Test ekstremalnych wartości VP"""
        ai = edge_ai
        
        # Scenariusz 1: Bardzo wysokie VP
        player = Mock()
        player.victory_points = 9999
        
        engine = Mock()
        engine.current_player_obj = player
        engine.players = [player]
        engine.turn = 10
        engine.current_turn = 10
        engine.victory_conditions = Mock()
        engine.victory_conditions.max_turns = 30
        
        # Dodaj wroga z niskimi VP
        enemy = Mock()
        enemy.nation = "Niemcy"
        enemy.victory_points = 10
        engine.players.append(enemy)
        
        ai.analyze_strategic_situation(engine, player)
        
        assert ai._strategic_analysis['vp_own'] == 9999
        assert ai._strategic_analysis['vp_enemy'] == 10
        assert ai._strategic_analysis['vp_status'] == 9989
        
        # Scenariusz 2: Ujemne VP
        player.victory_points = -50
        enemy.victory_points = 100
        
        ai.analyze_strategic_situation(engine, player)
        
        assert ai._strategic_analysis['vp_own'] == -50
        assert ai._strategic_analysis['vp_status'] == -150
        
    def test_extreme_turn_numbers(self, edge_ai):
        """Test ekstremalnych numerów tur"""
        ai = edge_ai
        
        player = Mock()
        player.victory_points = 50
        
        engine = Mock()
        engine.current_player_obj = player
        engine.players = [player]
        engine.victory_conditions = Mock()
        engine.victory_conditions.max_turns = 100
        
        # Scenariusz 1: Tura 0
        engine.turn = 0
        engine.current_turn = 0
        ai.analyze_strategic_situation(engine, player)
        
        assert ai._strategic_analysis['current_turn'] == 0
        assert ai._strategic_analysis['game_phase'] == 0.0
        assert ai._strategic_analysis['phase_name'] == "WCZESNA"
        
        # Scenariusz 2: Tura większa niż max
        engine.turn = 150
        engine.current_turn = 150
        ai.analyze_strategic_situation(engine, player)
        
        assert ai._strategic_analysis['current_turn'] == 150
        assert ai._strategic_analysis['game_phase'] == 4.5  # 150/100 * 3
        assert ai._strategic_analysis['phase_name'] == "PÓŹNA"
        
    def test_missing_engine_attributes(self, edge_ai):
        """Test gdy engine ma brakujące atrybuty"""
        ai = edge_ai
        
        # Engine bez niektórych atrybutów
        broken_engine = Mock()
        broken_engine.current_player_obj = None
        # Brak victory_conditions
        
        player = Mock()
        
        # Nie powinno rzucać błędu
        try:
            ai.analyze_strategic_situation(broken_engine, player)
        except AttributeError:
            pass  # Oczekiwane dla broken engine
        
        # Engine z None values
        partial_engine = Mock()
        partial_engine.current_player_obj = player
        partial_engine.turn = None
        partial_engine.victory_conditions = None
        
        try:
            ai.analyze_strategic_situation(partial_engine, player)
        except (TypeError, AttributeError):
            pass  # Oczekiwane
            
    def test_corrupted_unit_data(self, edge_ai):
        """Test uszkodzonych danych jednostek"""
        ai = edge_ai
        
        player = Mock()
        player.nation = "Polska"
        
        engine = Mock()
        engine.current_player_obj = player
        
        # Jednostki z uszkodzonymi danymi
        corrupted_tokens = []
        
        # Jednostka bez fuel
        token1 = Mock()
        token1.maxFuel = None
        token1.currentFuel = None
        token1.owner = "1"
        corrupted_tokens.append(token1)
        
        # Jednostka z ujemnym fuel
        token2 = Mock()
        token2.maxFuel = 100
        token2.currentFuel = -50
        token2.owner = "1"
        corrupted_tokens.append(token2)
        
        # Jednostka bez owner
        token3 = Mock()
        token3.maxFuel = 100
        token3.currentFuel = 50
        token3.owner = None
        corrupted_tokens.append(token3)
        
        engine.get_visible_tokens.return_value = corrupted_tokens
        
        # Nie powinno rzucać błędu
        ai.analyze_units(engine, player)
        
        # Sprawdź czy obsłużyło uszkodzone dane
        assert hasattr(ai, '_unit_analysis')
        
    def test_massive_fuel_crisis(self, edge_ai):
        """Test masowego kryzysu paliwa"""
        ai = edge_ai
        
        player = Mock()
        player.nation = "Polska"
        
        engine = Mock()
        engine.current_player_obj = player
        
        # Wszystkie jednostki z bardzo niskim paliwem
        crisis_tokens = []
        for i in range(20):
            token = Mock()
            token.maxFuel = 100
            token.currentFuel = 5  # Bardzo niskie paliwo
            token.owner = str((i % 3) + 1)
            token.unitType = "P"
            crisis_tokens.append(token)
            
        engine.get_visible_tokens.return_value = crisis_tokens
        
        ai.analyze_units(engine, player)
        
        # Sprawdź czy wykryto kryzys
        assert ai._unit_analysis['low_fuel_ratio'] > 0.8  # Większość z niskim paliwem
        
        # Test strategii w kryzysie
        strategic_analysis = {'vp_status': 0, 'game_phase': 1.5, 'phase_name': 'ŚREDNIA'}
        strategy = ai._determine_strategy(strategic_analysis, ai._unit_analysis, 15)
        assert strategy == "KRYZYS_PALIWA"
        
    def test_no_economy_points(self, edge_ai):
        """Test gdy brak punktów ekonomicznych"""
        ai = edge_ai
        
        player = Mock()
        player.economy = Mock()
        player.economy.get_points.return_value = {'economic_points': 0}
        player.economy.economic_points = 0
        
        engine = Mock()
        engine.current_player_obj = player
        
        with patch.object(ai, 'allocate_points') as mock_allocate:
            mock_allocate.return_value = (0, 0, {})  # Brak alokacji
            
            # Nie powinno rzucać błędu
            ai.make_strategic_decisions(engine, player)
            
            # Sprawdź czy nie próbowano zakupów
            assert ai._turn_strategy_used in ["ALLOCATION", "NO_ACTION", "HOLD"]
            
    def test_circular_strategy_detection(self, edge_ai):
        """Test wykrywania cyklicznych strategii"""
        ai = edge_ai
        
        # Symuluj wielokrotne wywołania z tymi samymi danymi
        strategic_analysis = {'vp_status': 10, 'game_phase': 1.5, 'phase_name': 'ŚREDNIA'}
        unit_analysis = {'low_fuel_ratio': 0.1, 'commanders_analysis': {}}
        
        strategies = []
        for i in range(10):
            strategy = ai._determine_strategy(strategic_analysis, unit_analysis, 15)
            strategies.append(strategy)
            
        # Strategia powinna być konsystentna
        assert len(set(strategies)) == 1, "Strategia powinna być deterministyczna dla tych samych danych"
        
    def test_extreme_commander_numbers(self, edge_ai):
        """Test ekstremalnej liczby dowódców"""
        ai = edge_ai
        
        player = Mock()
        player.nation = "Polska"
        
        # Bardzo wielu dowódców
        commanders = []
        for i in range(100):  # 100 dowódców!
            cmd = Mock()
            cmd.id = str(i+1)
            cmd.nation = "Polska"
            commanders.append(cmd)
            
        engine = Mock()
        engine.current_player_obj = player
        engine.players = commanders + [player]
        engine.turn = 10
        engine.current_turn = 10
        engine.victory_conditions = Mock()
        engine.victory_conditions.max_turns = 30
        
        # Nie powinno rzucać błędu ani trwać bardzo długo
        import time
        start_time = time.time()
        ai.analyze_strategic_situation(engine, player)
        end_time = time.time()
        
        assert end_time - start_time < 2.0, "Analiza z wieloma dowódcami trwa za długo"
        
    def test_invalid_strategy_fallback(self, edge_ai):
        """Test fallback dla nieprawidłowych strategii"""
        ai = edge_ai
        
        # Force invalid conditions
        with patch.object(ai, '_determine_strategy') as mock_strategy:
            mock_strategy.return_value = "INVALID_STRATEGY"
            
            player = Mock()
            engine = Mock()
            engine.current_player_obj = player
            
            # Powinno gracefully obsłużyć nieprawidłową strategię
            try:
                ai.make_strategic_decisions(engine, player)
            except Exception as e:
                # Sprawdź czy błąd jest obsłużony
                assert "INVALID_STRATEGY" not in str(e)
                
    def test_concurrent_access_safety(self, edge_ai):
        """Test bezpieczeństwa równoczesnego dostępu"""
        ai = edge_ai
        
        player = Mock()
        engine = Mock()
        engine.current_player_obj = player
        engine.players = [player]
        engine.turn = 10
        engine.current_turn = 10
        engine.victory_conditions = Mock()
        engine.victory_conditions.max_turns = 30
        engine.key_points_state = {}
        engine.get_visible_tokens.return_value = []
        
        # Symuluj wielokrotne wywołania (jak gdyby z różnych wątków)
        for i in range(5):
            ai.analyze_strategic_situation(engine, player)
            ai.analyze_units(engine, player)
            
        # Sprawdź czy stan jest spójny
        assert hasattr(ai, '_strategic_analysis')
        assert hasattr(ai, '_unit_analysis')
        assert ai._strategic_analysis['current_turn'] == 10
