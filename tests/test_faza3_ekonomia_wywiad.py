#!/usr/bin/env python3
"""
Test FAZA 3: Logowanie ekonomii i wywiadu
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ai.ai_commander import AICommander
from ai.ekonomia_ai import log_economic_decision, optimize_budget
from ai.rozpoznanie_ai import log_intelligence_analysis, gather_reconnaissance
from utils.session_manager import SessionManager

class MockGameEngine:
    def __init__(self):
        self.current_turn = 7
        self.current_phase = 2
        self.board = None
        self.turn_number = 7
        self.key_points_state = {
            '10,15': {'current_value': 3, 'position': (10, 15)},
            '20,25': {'current_value': 2, 'position': (20, 25)}
        }
        
class MockPlayer:
    def __init__(self, name="Niemcy"):
        self.name = name
        self.nation = name
        self.id = 1
        self.punkty_ekonomiczne = 150
        
class MockToken:
    def __init__(self, unit_id, pos, unit_type='INF'):
        self.id = unit_id
        self.q, self.r = pos
        self.unit_type = unit_type
        self.combat_value = 4
        self.currentFuel = 2
        self.maxFuel = 4
        self.stats = {
            'combat_value': 4,
            'maintenance': 4,
            'attack': {'value': 3},
            'defense_value': 2
        }
        self.owner = "1 (Niemcy)"

def test_faza3_ekonomia_wywiad():
    """Test FAZA 3: Logowanie decyzji ekonomicznych i analizy wywiadu"""
    
    print("🧪 TEST FAZA 3: EKONOMIKA I WYWIAD - ZAAWANSOWANE LOGOWANIE")
    print("=" * 80)
    
    # KROK 1: Przygotowanie środowiska
    print("\n⚙️ KROK 1: Przygotowanie środowiska testowego")
    
    # Utwórz mock obiekty
    mock_engine = MockGameEngine()
    mock_player = MockPlayer()
    
    # Utwórz AI Commander
    ai_commander = AICommander(mock_player)
    print("✅ AI Commander utworzony")
    
    # KROK 2: Test logowania decyzji ekonomicznych
    print("\n💰 KROK 2: Test logowania decyzji ekonomicznych")
    
    # Test bezpośredniego logowania
    log_economic_decision(ai_commander, 'BUDGET_PLANNING', {
        'available_budget': 150,
        'allocated_budget': 120,
        'expense_category': 'UNIT_PURCHASES',
        'expected_return': 180,
        'opportunity_cost': 30,
        'budget_pressure': 'MEDIUM',
        'pe_efficiency': 0.8,
        'resource_shortage': False,
        'emergency_expenses': False,
        'investment_horizon': 'SHORT_TERM',
        'cost_benefit_analysis': 'Positive ROI expected',
        'budget_deviation': 0,
        'economic_strategy_alignment': 'ALIGNED'
    })
    print("✅ Bezpośrednie logowanie ekonomiczne wykonane")
    
    # Test funkcji optimize_budget
    try:
        # Mock funkcji get_my_units
        def mock_get_my_units(game_engine, player_id):
            return [
                {'token': MockToken('unit_001', (5, 10), 'INF')},
                {'token': MockToken('unit_002', (8, 12), 'ART')},
                {'token': MockToken('unit_003', (15, 8), 'CAV')}
            ]
        
        # Patch the function temporarily
        import ai.ekonomia_ai
        original_get_my_units = getattr(ai.ekonomia_ai, 'get_my_units', lambda x, y: [])
        ai.ekonomia_ai.get_my_units = mock_get_my_units
        
        # Test optymalizacji budżetu
        budget_plan = optimize_budget(ai_commander, mock_engine)
        print(f"✅ Optymalizacja budżetu: {budget_plan.get('reason', 'N/A')}")
        
        # Przywróć oryginalną funkcję
        ai.ekonomia_ai.get_my_units = original_get_my_units
        
    except Exception as e:
        print(f"⚠️ Błąd testu optymalizacji budżetu: {e}")
    
    # KROK 3: Test logowania analizy wywiadu
    print("\n🔍 KROK 3: Test logowania analizy wywiadu")
    
    # Test bezpośredniego logowania wywiadu
    log_intelligence_analysis(ai_commander, 'ENEMY_MOVEMENT_ANALYSIS', {
        'source_reliability': 0.85,
        'information_freshness': 'CURRENT',
        'enemy_units_spotted': 4,
        'predicted_enemy_moves': 'ADVANCE_TO_KEYPOINT',
        'threat_assessment_change': 'INCREASED',
        'counter_intelligence_detected': False,
        'surprise_probability': 0.3,
        'information_gaps': 'MODERATE',
        'intelligence_confidence': 0.8,
        'actionable_intelligence': True,
        'intelligence_sharing': 'COMMAND_LEVEL',
        'historical_prediction_accuracy': 0.75,
        'enemy_pattern_recognition': 'AGGRESSIVE_PATTERN',
        'deception_probability': 0.1
    })
    print("✅ Bezpośrednie logowanie wywiadu wykonane")
    
    # Test funkcji gather_reconnaissance
    try:
        # Mock current_player_obj z visible_tokens
        class MockCurrentPlayer:
            def __init__(self):
                self.visible_tokens = [
                    MockToken('enemy_001', (12, 18), 'INF'),
                    MockToken('enemy_002', (25, 30), 'ART')
                ]
                # Ustaw inne właścicieli
                for token in self.visible_tokens:
                    token.owner = "2 (Sowiety)"
        
        mock_engine.current_player_obj = MockCurrentPlayer()
        
        recon_data = gather_reconnaissance(ai_commander, mock_engine)
        print(f"✅ Rozpoznanie: wykryto {recon_data.get('enemy_count', 0)} wrogów")
        
    except Exception as e:
        print(f"⚠️ Błąd testu rozpoznania: {e}")
    
    # KROK 4: Sprawdzenie utworzonych plików
    print("\n📊 KROK 4: Sprawdzenie logów")
    
    try:
        session_manager = SessionManager()
        current_session = session_manager.get_current_session_dir()
        
        ai_logs_dir = current_session / 'ai_commander_zaawansowany'
        
        # Sprawdź pliki ekonomiczne
        economic_dir = ai_logs_dir / 'decyzje_ekonomiczne'
        if economic_dir.exists():
            economic_files = list(economic_dir.glob('*.csv'))
            print(f"✅ ekonomiczne: {len(economic_files)} plików")
            
            if economic_files:
                # Policz wiersze w pliku
                with open(economic_files[0], 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                print(f"   - wierszy danych: {len(lines) - 1}")  # -1 dla nagłówka
        
        # Sprawdź pliki wywiadowcze
        intelligence_dir = ai_logs_dir / 'analiza_wywiadu'
        if intelligence_dir.exists():
            intelligence_files = list(intelligence_dir.glob('*.csv'))
            print(f"✅ wywiad: {len(intelligence_files)} plików")
            
            if intelligence_files:
                # Policz wiersze w pliku
                with open(intelligence_files[0], 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                print(f"   - wierszy danych: {len(lines) - 1}")  # -1 dla nagłówka
        
    except Exception as e:
        print(f"⚠️ Błąd sprawdzania logów: {e}")
    
    print("\n🎉 TEST FAZA 3 ZAKOŃCZONY!")

if __name__ == "__main__":
    test_faza3_ekonomia_wywiad()