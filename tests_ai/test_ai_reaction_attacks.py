"""
Test systemu ataków reakcyjnych AI - sprawdza czy AI ma parytet z human players
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai.ai_commander import check_ai_reaction_attacks, log_commander_action


# Mock classes dla testów
class MockToken:
    def __init__(self, token_id, owner, q, r, sight=3, attack_range=1, combat_value=10):
        self.id = token_id
        self.owner = owner
        self.q = q
        self.r = r
        self.combat_value = combat_value
        self.stats = {
            'sight': sight,
            'attack': {'range': attack_range, 'value': 8},
            'defense_value': 6,
            'combat_value': combat_value,
        }


class MockBoard:
    def hex_distance(self, pos1, pos2):
        """Oblicz dystans heksagonalny"""
        q1, r1 = pos1
        q2, r2 = pos2
        return max(abs(q1 - q2), abs(r1 - r2), abs((q1 + r1) - (q2 + r2)))


class MockEngine:
    def __init__(self):
        self.tokens = []
        self.board = MockBoard()
        self.executed_actions = []
    
    def execute_action(self, action):
        """Mock execute_action - zapisuje akcje do listy"""
        self.executed_actions.append({
            'action_type': type(action).__name__,
            'attacker_id': getattr(action, 'token_id', None),
            'defender_id': getattr(action, 'defender_id', None),
            'is_reaction': getattr(action, 'is_reaction', False)
        })
        
        # Mock result object
        class MockResult:
            def __init__(self):
                self.success = True
                self.message = "Mock reaction attack successful"
        
        return MockResult()


def test_ai_reaction_basic():
    """Test podstawowy - AI atakuje po ruchu przeciwnika"""
    print("🧪 TEST: AI Reaction Basic")
    
    # Setup
    engine = MockEngine()
    
    # AI token (Niemcy) - może zaatakować
    ai_token = MockToken("GE_INF_01", "5 (Niemcy)", 5, 5, sight=3, attack_range=2)
    engine.tokens.append(ai_token)
    
    # Human token (Polska) - cel ruchu 
    human_token = MockToken("PL_INF_01", "2 (Polska)", 6, 6, sight=2, attack_range=1)
    engine.tokens.append(human_token)
    
    # Execute reaction check
    check_ai_reaction_attacks(human_token, engine)
    
    # Verify
    reactions = [a for a in engine.executed_actions if a['is_reaction']]
    assert len(reactions) == 1, f"Oczekiwano 1 reakcji, otrzymano {len(reactions)}"
    assert reactions[0]['attacker_id'] == "GE_INF_01", f"Błędny atakujący: {reactions[0]['attacker_id']}"
    assert reactions[0]['defender_id'] == "PL_INF_01", f"Błędny cel: {reactions[0]['defender_id']}"
    
    print("✅ Test basic: AI wykonuje reakcję na ruch przeciwnika")
    return True


def test_ai_reaction_out_of_range():
    """Test - AI nie atakuje gdy cel poza zasięgiem"""
    print("🧪 TEST: AI Reaction Out of Range")
    
    # Setup
    engine = MockEngine()
    
    # AI token - za daleko
    ai_token = MockToken("GE_INF_01", "5 (Niemcy)", 1, 1, sight=2, attack_range=1)
    engine.tokens.append(ai_token)
    
    # Human token - daleko
    human_token = MockToken("PL_INF_01", "2 (Polska)", 10, 10, sight=2, attack_range=1)
    engine.tokens.append(human_token)
    
    # Execute reaction check
    check_ai_reaction_attacks(human_token, engine)
    
    # Verify - nie powinno być reakcji
    reactions = [a for a in engine.executed_actions if a['is_reaction']]
    assert len(reactions) == 0, f"Nie powinno być reakcji, otrzymano {len(reactions)}"
    
    print("✅ Test out of range: AI nie atakuje poza zasięgiem")
    return True


def test_ai_reaction_out_of_sight():
    """Test - AI nie atakuje gdy cel poza zasięgiem wzroku"""
    print("🧪 TEST: AI Reaction Out of Sight")
    
    # Setup
    engine = MockEngine()
    
    # AI token - mały sight
    ai_token = MockToken("GE_INF_01", "5 (Niemcy)", 5, 5, sight=1, attack_range=3)
    engine.tokens.append(ai_token)
    
    # Human token - poza sight ale w attack_range
    human_token = MockToken("PL_INF_01", "2 (Polska)", 7, 7, sight=2, attack_range=1)
    engine.tokens.append(human_token)
    
    # Execute reaction check
    check_ai_reaction_attacks(human_token, engine)
    
    # Verify - nie powinno być reakcji (poza sight)
    reactions = [a for a in engine.executed_actions if a['is_reaction']]
    assert len(reactions) == 0, f"Nie powinno być reakcji (poza sight), otrzymano {len(reactions)}"
    
    print("✅ Test out of sight: AI nie atakuje poza zasięgiem wzroku")
    return True


def test_ai_reaction_same_nation():
    """Test - AI nie atakuje własnych jednostek"""
    print("🧪 TEST: AI Reaction Same Nation")
    
    # Setup
    engine = MockEngine()
    
    # Dwa niemieckie tokeny
    ai_token1 = MockToken("GE_INF_01", "5 (Niemcy)", 5, 5, sight=3, attack_range=2)
    ai_token2 = MockToken("GE_CAV_01", "6 (Niemcy)", 6, 6, sight=2, attack_range=1)
    engine.tokens.extend([ai_token1, ai_token2])
    
    # Execute reaction check - token2 się ruszył
    check_ai_reaction_attacks(ai_token2, engine)
    
    # Verify - nie powinno być reakcji (ta sama nacja)
    reactions = [a for a in engine.executed_actions if a['is_reaction']]
    assert len(reactions) == 0, f"Nie powinno być reakcji (ta sama nacja), otrzymano {len(reactions)}"
    
    print("✅ Test same nation: AI nie atakuje własnych jednostek")
    return True


def test_ai_reaction_multiple_attackers():
    """Test - wielu AI może zaatakować jednego przeciwnika"""
    print("🧪 TEST: AI Multiple Attackers")
    
    # Setup
    engine = MockEngine()
    
    # Dwa AI tokeny (Niemcy) - oba mogą zaatakować
    ai_token1 = MockToken("GE_INF_01", "5 (Niemcy)", 5, 5, sight=3, attack_range=2)
    ai_token2 = MockToken("GE_INF_02", "6 (Niemcy)", 7, 7, sight=3, attack_range=2)
    engine.tokens.extend([ai_token1, ai_token2])
    
    # Human token (Polska) - w zasięgu obu
    human_token = MockToken("PL_INF_01", "2 (Polska)", 6, 6, sight=2, attack_range=1)
    engine.tokens.append(human_token)
    
    # Execute reaction check
    check_ai_reaction_attacks(human_token, engine)
    
    # Verify - oba AI powinny zaatakować
    reactions = [a for a in engine.executed_actions if a['is_reaction']]
    assert len(reactions) == 2, f"Oczekiwano 2 reakcji, otrzymano {len(reactions)}"
    
    attackers = {r['attacker_id'] for r in reactions}
    expected_attackers = {"GE_INF_01", "GE_INF_02"}
    assert attackers == expected_attackers, f"Błędni atakujący: {attackers} vs {expected_attackers}"
    
    print("✅ Test multiple attackers: Wielu AI atakuje jednego przeciwnika")
    return True


def test_ai_reaction_parity_with_gui():
    """Test parytetu - AI używa identycznej logiki jak GUI"""
    print("🧪 TEST: AI Reaction Parity with GUI")
    
    # Setup identyczny jak w gui/panel_mapa.py
    engine = MockEngine()
    
    # AI token z identycznymi parametrami jak w GUI testach
    ai_token = MockToken("GE_INF_01", "5 (Niemcy)", 10, 10, sight=3, attack_range=1)
    engine.tokens.append(ai_token)
    
    # Human token - DOKŁADNIE w zasięgu (distance = 1)
    human_token = MockToken("PL_INF_01", "2 (Polska)", 11, 10, sight=2, attack_range=1)
    engine.tokens.append(human_token)
    
    # Execute reaction check
    check_ai_reaction_attacks(human_token, engine)
    
    # Verify zgodność z GUI:
    # 1. Sprawdza distance <= sight AND distance <= attack_range
    # 2. Wykonuje CombatAction(enemy.id, moved_token.id, is_reaction=True)
    reactions = [a for a in engine.executed_actions if a['is_reaction']]
    assert len(reactions) == 1, f"Parytet z GUI: oczekiwano 1 reakcji, otrzymano {len(reactions)}"
    assert reactions[0]['action_type'] == "CombatAction", f"Parytet z GUI: oczekiwano CombatAction"
    assert reactions[0]['is_reaction'] == True, f"Parytet z GUI: oczekiwano is_reaction=True"
    
    print("✅ Test parity: AI ma identyczną logikę jak GUI")
    return True


def run_all_tests():
    """Uruchom wszystkie testy ataków reakcyjnych AI"""
    print("🚀 URUCHAMIANIE TESTÓW ATAKÓW REAKCYJNYCH AI")
    print("=" * 60)
    
    tests = [
        test_ai_reaction_basic,
        test_ai_reaction_out_of_range,
        test_ai_reaction_out_of_sight,
        test_ai_reaction_same_nation,
        test_ai_reaction_multiple_attackers,
        test_ai_reaction_parity_with_gui
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
                print(f"❌ {test.__name__} FAILED")
        except Exception as e:
            failed += 1
            print(f"💥 {test.__name__} ERROR: {e}")
        print()
    
    print("=" * 60)
    print(f"📊 WYNIKI TESTÓW: {passed} ✅ passed, {failed} ❌ failed")
    
    if failed == 0:
        print("🎉 WSZYSTKIE TESTY PRZESZŁY! AI ma parytet w atakach reakcyjnych.")
    else:
        print("⚠️  NIEKTÓRE TESTY NIE PRZESZŁY - sprawdź implementację.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
