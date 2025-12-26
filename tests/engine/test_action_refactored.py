"""
Testy dla refaktoryzowanych akcji
"""

import pytest
import sys
import os
import random

# Dodaj główny katalog do path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.action_refactored_clean import (
    ActionResult, BaseAction, MoveAction, CombatAction,
    MovementValidator, PathfindingService, VisionService,
    CombatCalculator, CombatResolver
)


class TestActionResult:
    """Testy klasy ActionResult"""
    
    def test_action_result_creation(self):
        result = ActionResult(True, "Success")
        assert result.success is True
        assert result.message == "Success"
        assert result.data == {}
    
    def test_action_result_with_data(self):
        data = {'position': (1, 2), 'cost': 5}
        result = ActionResult(False, "Failed", data)
        assert result.success is False
        assert result.message == "Failed"
        assert result.data == data


class TestMovementValidator:
    """Testy walidatora ruchu"""
    
    def test_validate_basic_movement_no_token(self):
        # Mock engine
        class MockEngine:
            class MockBoard:
                def get_tile(self, q, r):
                    return None
            board = MockBoard()
            tokens = []
        
        engine = MockEngine()
        valid, msg = MovementValidator.validate_basic_movement(None, 0, 0, engine)
        assert not valid
        assert msg == "Brak żetonu."
    
    def test_validate_basic_movement_no_destination_tile(self):
        # Mock token
        class MockToken:
            pass
        
        # Mock engine
        class MockEngine:
            class MockBoard:
                def get_tile(self, q, r):
                    return None
            board = MockBoard()
            tokens = []
        
        token = MockToken()
        engine = MockEngine()
        valid, msg = MovementValidator.validate_basic_movement(token, 0, 0, engine)
        assert not valid
        assert msg == "Brak pola docelowego."


class TestCombatCalculator:
    """Testy kalkulatora walki"""
    
    def test_calculate_combat_result_basic(self):
        # Mock tokens
        class MockToken:
            def __init__(self, stats, q=0, r=0):
                self.stats = stats
                self.q = q
                self.r = r
        
        # Mock engine
        class MockEngine:
            class MockBoard:
                def get_tile(self, q, r):
                    class MockTile:
                        defense_mod = 0
                    return MockTile()
                
                def hex_distance(self, pos1, pos2):
                    return 1
            board = MockBoard()
        
        attacker = MockToken({
            'attack': {'value': 10, 'range': 1}
        })
        defender = MockToken({
            'defense_value': 5,
            'attack': {'range': 1}
        })
        engine = MockEngine()
        
        result = CombatCalculator.calculate_combat_result(attacker, defender, engine)
        
        assert 'attack_result' in result
        assert 'defense_result' in result
        assert 'can_counterattack' in result
        assert result['can_counterattack'] is True
        assert result['distance'] == 1

    def test_calculate_combat_result_no_counterattack(self):
        class MockToken:
            def __init__(self, stats, q=0, r=0):
                self.stats = stats
                self.q = q
                self.r = r

        class MockEngine:
            class MockBoard:
                def get_tile(self, q, r):
                    class MockTile:
                        defense_mod = 0
                    return MockTile()

                def hex_distance(self, pos1, pos2):
                    return 3
            board = MockBoard()

        attacker = MockToken({'attack': {'value': 10, 'range': 3}}, q=0, r=0)
        defender = MockToken({'defense_value': 5, 'attack': {'range': 1}}, q=3, r=0)
        engine = MockEngine()

        result = CombatCalculator.calculate_combat_result(attacker, defender, engine)

        assert result['distance'] == 3
        assert result['defense_range'] == 1
        assert result['can_counterattack'] is False
        assert result['defense_result'] == 0


class TestBaseAction:
    """Testy bazowej klasy akcji"""
    
    def test_base_action_creation(self):
        class TestAction(BaseAction):
            def execute(self, engine):
                return ActionResult(True, "Test")
        
        action = TestAction("token123")
        assert action.token_id == "token123"
    
    def test_find_token(self):
        class TestAction(BaseAction):
            def execute(self, engine):
                return ActionResult(True, "Test")
        
        # Mock token
        class MockToken:
            def __init__(self, token_id):
                self.id = token_id
        
        # Mock engine
        class MockEngine:
            def __init__(self):
                self.tokens = [MockToken("token1"), MockToken("token2")]
        
        action = TestAction("token1")
        engine = MockEngine()
        
        token = action._find_token(engine, "token1")
        assert token is not None
        assert token.id == "token1"
        
        token = action._find_token(engine, "nonexistent")
        assert token is None


def test_integration_move_action():
    """Test integracyjny akcji ruchu (uproszczony)"""
    # Mock wszystkie potrzebne komponenty
    class MockTile:
        def __init__(self, move_mod=0, defense_mod=0):
            self.move_mod = move_mod
            self.defense_mod = defense_mod
    
    class MockBoard:
        def get_tile(self, q, r):
            return MockTile()
        
        def is_occupied(self, q, r):
            return False
        
        def find_path(self, start, goal, **kwargs):
            return [start, goal]
        
        def hex_distance(self, pos1, pos2):
            return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    class MockToken:
        def __init__(self, token_id, q=0, r=0):
            self.id = token_id
            self.q = q
            self.r = r
            self.owner = "Player1 (Polska)"
            self.stats = {'sight': 2, 'maintenance': 10}
            self.movement_mode = 'combat'
            self.currentMovePoints = 10
            self.maxMovePoints = 10
            self.currentFuel = 10
            self.maxFuel = 10
        
        def apply_movement_mode(self):
            pass
        
        def set_position(self, q, r):
            self.q = q
            self.r = r
    
    class MockPlayer:
        def __init__(self):
            self.id = "Player1"
            self.nation = "Polska"
            self.temp_visible_hexes = set()
            self.temp_visible_tokens = set()
    
    class MockEngine:
        def __init__(self):
            self.board = MockBoard()
            self.tokens = [MockToken("token1")]
            self.players = [MockPlayer()]
    
    # Test
    action = MoveAction("token1", 1, 1)
    engine = MockEngine()
    
    result = action.execute(engine)
    
    assert result.success is True
    assert result.message == "OK"
    assert 'final_position' in result.data
    assert result.data['final_position'] == (1, 1)


def test_combat_resolver_defender_retreats(monkeypatch):
    class MockTile:
        def __init__(self, defense_mod=0):
            self.defense_mod = defense_mod

    class MockBoard:
        def __init__(self, engine):
            self._engine = engine

        def get_tile(self, q, r):
            return MockTile()

        def is_occupied(self, q, r):
            for token in self._engine.tokens:
                if (token.q, token.r) == (q, r):
                    return True
            return False

        def hex_distance(self, pos1, pos2):
            aq, ar = pos1
            bq, br = pos2
            return int((abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) / 2)

    class MockToken:
        def __init__(self, token_id, owner, q=0, r=0, cv=5):
            self.id = token_id
            self.owner = owner
            self.q = q
            self.r = r
            self.combat_value = cv
            self.stats = {
                'combat_value': cv,
                'attack': {'value': 5, 'range': 1},
                'defense_value': 2,
            }

        def set_position(self, q, r):
            self.q = q
            self.r = r

    class MockEngine:
        def __init__(self):
            self.board = MockBoard(self)
            self.tokens = []
            self.players = []
            self.ai_commanders = {}

    engine = MockEngine()
    attacker = MockToken('ATT', '1 (Polska)', q=0, r=0, cv=6)
    defender = MockToken('DEF', '2 (Niemcy)', q=1, r=0, cv=4)
    engine.tokens.extend([attacker, defender])

    start_distance = engine.board.hex_distance((attacker.q, attacker.r), (defender.q, defender.r))

    monkeypatch.setattr(random, 'random', lambda: 0.0)

    combat_result = {
        'attack_result': 5,
        'defense_result': 0,
        'attack_mult': 1.0,
        'defense_mult': 1.0,
        'defense_mod': 0,
        'can_counterattack': False,
        'distance': 1,
        'attack_range': 1,
        'defense_range': 1,
    }

    message = CombatResolver.resolve_combat(engine, attacker, defender, combat_result)

    assert 'cofnął się' in message
    assert defender.combat_value == 1
    assert engine.board.hex_distance((attacker.q, attacker.r), (defender.q, defender.r)) > start_distance
    assert defender in engine.tokens


if __name__ == "__main__":
    pytest.main([__file__])
