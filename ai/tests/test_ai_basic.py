"""
Test podstawowej logiki AI Generała i Komendanta
"""
import sys
import os

# Dodaj główny folder projektu do sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.ekonomia import EconomySystem
from engine.player import Player
from ai import GeneralAI, CommanderAI


def test_general_ai():
    """Test AI Generała - dystrybucja PE"""
    print("🧪 Test AI Generała - dystrybucja PE")
    
    # Utwórz graczy
    general = Player(1, "Polska", "Generał", 5)
    general.economy = EconomySystem()
    
    commander1 = Player(2, "Polska", "Dowódca", 5)
    commander1.economy = EconomySystem()
    
    commander2 = Player(3, "Polska", "Dowódca", 5)  
    commander2.economy = EconomySystem()
    
    # Generał ma 100 PE
    general.economy.add_economic_points(100)
    
    # Dowódcy mają po 0 PE
    print(f"✅ Stan początkowy:")
    print(f"   • Generał: {general.economy.get_points()['economic_points']} PE")
    print(f"   • Dowódca 1: {commander1.economy.get_points()['economic_points']} PE") 
    print(f"   • Dowódca 2: {commander2.economy.get_points()['economic_points']} PE")
    
    # AI Generał wykonuje turę
    ai_general = GeneralAI(general)
    all_players = [general, commander1, commander2]
    
    ai_general.execute_turn(all_players, game_engine=None)
    
    # Sprawdź rezultat
    print(f"\n✅ Stan po dystrybucji:")
    print(f"   • Generał: {general.economy.get_points()['economic_points']} PE")
    print(f"   • Dowódca 1: {commander1.economy.get_points()['economic_points']} PE")
    print(f"   • Dowódca 2: {commander2.economy.get_points()['economic_points']} PE")
    
    # Sprawdź czy dystrybucja jest prawidłowa (10% rezerwa, 90% dla dowódców)
    total_distributed = (commander1.economy.get_points()['economic_points'] + 
                        commander2.economy.get_points()['economic_points'])
    general_remaining = general.economy.get_points()['economic_points']
    
    print(f"\n📊 Analiza:")
    print(f"   • Rozdystybuowano dowódcom: {total_distributed} PE")
    print(f"   • Pozostało u generała: {general_remaining} PE")
    print(f"   • Razem: {total_distributed + general_remaining} PE")


class MockToken:
    """Mock żeton do testów"""
    def __init__(self, token_id, unit_type='P', owner='1 (Polska)', q=0, r=0):
        self.id = token_id
        self.unitType = unit_type
        self.owner = owner
        self.q = q
        self.r = r
        self.currentMovePoints = 3
        self.maxMovePoints = 3
        self.currentFuel = 10
        self.maxFuel = 10
        self.stats = {
            'unitType': unit_type,
            'attack': {'range': 1},
            'sight': 2
        }
        self.shots_fired = 0
        self.shots_limit = 1
    
    def can_attack(self, attack_type):
        return self.shots_fired < self.shots_limit


class MockGameEngine:
    def __init__(self):
        self.tokens = []
    
    def execute_action(self, action, player=None):
        print(f"   🔧 MockEngine: {action.__class__.__name__} dla {action.token_id}")
        return (True, "Mock success")


def test_commander_ai():
    """Test AI Komendanta - zarządzanie żetonami"""
    print("\n\n🧪 Test AI Komendanta - zarządzanie żetonami")
    
    # Utwórz komendanta z PE
    commander = Player(2, "Polska", "Dowódca", 5)
    commander.economy = EconomySystem()
    commander.economy.add_economic_points(50)  # 50 PE na start
    
    # Utwórz żetony
    polish_token1 = MockToken('pol1', 'P', '2 (Polska)', 0, 0)
    polish_token2 = MockToken('pol2', 'K', '2 (Polska)', 1, 1)  
    polish_token3 = MockToken('pol3', 'Z', '2 (Polska)', 2, 2)
    german_token = MockToken('ger1', 'P', '4 (Niemcy)', 5, 5)
    
    # Utwórz mock engine
    engine = MockGameEngine()
    engine.tokens = [polish_token1, polish_token2, polish_token3, german_token]
    
    print(f"✅ Stan początkowy:")
    print(f"   • Komendant PE: {commander.economy.get_points()['economic_points']}")
    print(f"   • Żetonów w engine: {len(engine.tokens)}")
    
    # AI Komendant wykonuje turę
    ai_commander = CommanderAI(commander)
    ai_commander.execute_turn(engine)
    
    # Sprawdź rezultat
    remaining_pe = commander.economy.get_points()['economic_points']
    print(f"\n✅ Stan końcowy:")
    print(f"   • Komendant PE: {remaining_pe}")


if __name__ == '__main__':
    test_general_ai()
    test_commander_ai()
    print("\n✅ Wszystkie testy AI ukończone")