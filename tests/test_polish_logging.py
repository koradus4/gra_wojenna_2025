#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test polskiego systemu logowania AI (pytest)
"""

import sys
from pathlib import Path

# Dodaj ścieżkę do głównego katalogu projektu
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))


def test_polish_logging():
    """Test czy polski logger działa i generuje polskie nagłówki"""
    try:
        # Import modułów
        from utils.session_manager import SessionManager
        from utils.ai_commander_logger_zaawansowany import ZaawansowanyLoggerAI

        print("🚀 Test polskiego systemu logowania AI...")

        # Inicjalizacja session manager
        session_manager = SessionManager()
        session_dir = session_manager.get_current_session_dir()
        print(f"📁 Session directory: {session_dir}")

        # Inicjalizacja polskiego loggera
        logger = ZaawansowanyLoggerAI(session_dir)
        print("✅ ZaawansowanyLoggerAI zainicjalizowany")

        # Test loggera strategicznego
        print("\n📋 Test 1: Logger decyzji strategicznych")
        strategia_dane = {
            'decision_type': 'TEST_STRATEGIC_LOG',
            'decision_scope': 'UNIT_ANALYSIS',
            'priority_level': 'HIGH',
            'context_factors': 'test_units=5, test_scouts=2',
            'expected_outcome': 'SUCCESSFUL_TEST',
            'confidence_level': 'HIGH',
            'time_horizon': 'IMMEDIATE',
            'resource_commitment': 'LOW',
            'decision_rationale': 'Test polskiego logowania strategicznego',
            'vp_impact_projection': 'POSITIVE',
            'turn': '1',
            'nation': 'TESTOWA'
        }
        logger.loguj_decyzje_strategiczna(strategia_dane)
        print("✅ Log strategiczny zapisany")

        # Test loggera wydajności
        print("\n⚡ Test 2: Logger wydajności")
        wydajnosc_dane = {
            'decision_delay_ms': 150,
            'calculations_performed': 10,
            'algorithms_used': 'TEST_ALGORITHM',
            'memory_usage_mb': 45.2,
            'cpu_utilization_percent': 25.5,
            'decision_tree_depth': 3,
            'alternatives_evaluated': 2,
            'optimization_iterations': 1,
            'ai_confidence': 0.85,
            'applied_learning_rate': 0.1,
            'current_model_accuracy': 0.9,
            'success_prediction_indicator': 0.8,
            'triggered_adaptive_behavior': False,
            'error_recovery_attempts': 0,
            'system_stability_indicator': 1.0,
            'nation': 'TESTOWA'
        }
        logger.loguj_wydajnosc(wydajnosc_dane)
        print("✅ Log wydajności zapisany")

        # Test loggera analizy zwycięstwa
        print("\n🏆 Test 3: Logger analizy zwycięstwa")
        zwyciestwo_dane = {
            'vp_trajectory': 'ASCENDING',
            'vp_gap_analysis': 15,
            'victory_probability': 0.75,
            'identified_victory_path': 'ELIMINATION',
            'victory_conditions_progress': 0.6,
            'time_pressure_factor': 0.3,
            'active_endgame_strategy': False,
            'victory_point_opportunities': 3,
            'elimination_target_priorities': 'GERMANY_FIRST',
            'strategic_keypoint_value': 120,
            'predicted_victory_timeline': '8_TURNS',
            'defeat_risk_assessment': 0.15,
            'nation': 'TESTOWA'
        }
        logger.loguj_analize_zwyciestwa(zwyciestwo_dane)
        print("✅ Log analizy zwycięstwa zapisany")

        # Sprawdź czy pliki zostały utworzone
        print("\n📊 Sprawdzanie utworzonych plików:")
        ai_dir = session_dir / "ai_commander_zaawansowany"

        # Sprawdź decyzje strategiczne
        decyzje_dir = ai_dir / "decyzje_strategiczne"
        assert decyzje_dir.exists(), "Katalog decyzji strategicznych nie istnieje"
        csv_files = list(decyzje_dir.glob("*.csv"))
        assert csv_files, "Brak plików CSV w decyzjach strategicznych"

        # Sprawdź wydajność AI
        wydajnosc_dir = ai_dir / "wydajnosc_ai"
        assert wydajnosc_dir.exists(), "Katalog wydajności AI nie istnieje"
        csv_files = list(wydajnosc_dir.glob("*.csv"))
        assert csv_files, "Brak plików CSV w wydajności AI"

        # Sprawdź analizę zwycięstwa
        zwyciestwo_dir = ai_dir / "analiza_zwyciestwa"
        assert zwyciestwo_dir.exists(), "Katalog analizy zwycięstwa nie istnieje"
        csv_files = list(zwyciestwo_dir.glob("*.csv"))
        assert csv_files, "Brak plików CSV w analizie zwycięstwa"

        # Sprawdź logger walki
        walka_dir = ai_dir / "walka_ai"
        # Logger walki może nie mieć danych bez zdarzenia, ale katalog powinien istnieć po inicjalizacji
        assert walka_dir.exists(), "Katalog loggera walki nie istnieje"

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e
