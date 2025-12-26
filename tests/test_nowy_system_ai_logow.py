# -*- coding: utf-8 -*-
"""
Test nowego systemu zaawansowanego logowania AI Commander
"""

import sys
sys.path.append('.')

from utils.ai_commander_logger_zaawansowany import ZaawansowanyLoggerAI
from utils.session_manager import SessionManager
from pathlib import Path
import time

def test_nowego_systemu():
    """Test kompletnego systemu zaawansowanego logowania"""
    
    print("🧪 TEST NOWEGO SYSTEMU LOGOWANIA AI COMMANDER")
    print("=" * 60)
    
    # KROK 1: Test SessionManager z nowymi ścieżkami
    print("\n📁 KROK 1: Test SessionManager")
    session_dir = SessionManager.get_current_session_dir()
    print(f"✅ Katalog sesji: {session_dir}")
    
    specialized_dirs = SessionManager.get_specialized_ai_logs_dir()
    print("✅ Katalogi specjalistyczne:")
    for typ, sciezka in specialized_dirs.items():
        print(f"   🗂️ {typ}: {sciezka}")
    
    # KROK 2: Test ZaawansowanyLoggerAI
    print("\n🤖 KROK 2: Test ZaawansowanyLoggerAI")
    logger = ZaawansowanyLoggerAI(session_dir)
    print("✅ Logger zainicjalizowany")
    
    # KROK 3: Test decyzji strategicznych
    print("\n🎯 KROK 3: Test decyzji strategicznych")
    dane_strategiczne = {
        'turn': 5,
        'nation': 'Niemcy',
        'decision_type': 'Ofensywa_Agresywna',
        'decision_scope': 'Globalny',
        'priority_level': 'Wysoki',
        'context_factors': 'Przewaga liczebna na wschodzie',
        'confidence_level': 'Bardzo_Wysoki',
        'time_horizon': '3-4 tury',
        'resource_commitment': '80% sił',
        'risk_assessment': 'Umiarkowane',
        'success_probability': '85%',
        'vp_impact_projection': '+15 VP',
        'economic_impact': 'Wysokie koszty PE'
    }
    
    logger.loguj_decyzje_strategiczna(dane_strategiczne)
    print("✅ Decyzja strategiczna zapisana")
    
    # KROK 4: Test akcji taktycznych
    print("\n🎖️ KROK 4: Test akcji taktycznych")
    dane_taktyczne = {
        'turn': 5,
        'phase': 3,
        'nation': 'Niemcy',
        'action_category': 'Skoordynowany_Atak',
        'unit_primary': 'PANZER_001',
        'units_supporting': 'INF_002,ART_003',
        'coordination_required': True,
        'formation_type': 'Atak_Wspierany',
        'terrain_advantage': 'Neutralny',
        'execution_time_ms': 125.5,
        'unit_synergy_score': 0.85,
        'tactical_innovation': 'Standardowe',
        'risk_mitigation': 'Pełne',
        'fallback_plan_ready': True
    }
    
    logger.loguj_akcje_taktyczna(dane_taktyczne)
    print("✅ Akcja taktyczna zapisana")
    
    # KROK 5: Test decyzji ekonomicznych
    print("\n💰 KROK 5: Test decyzji ekonomicznych")
    dane_ekonomiczne = {
        'turn': 5,
        'nation': 'Niemcy',
        'budget_available': 150,
        'budget_allocated': 120,
        'spending_category': 'Ruch_Jednostek',
        'cost_per_action': 2.5,
        'expected_roi': '1.4x',
        'opportunity_cost': 30,
        'budget_pressure_level': 'Średni',
        'pe_efficiency_score': 0.78,
        'emergency_spending': False,
        'investment_horizon': 'Krótkoterminowy',
        'economic_strategy_alignment': 'Wysoki'
    }
    
    logger.loguj_decyzje_ekonomiczna(dane_ekonomiczne)
    print("✅ Decyzja ekonomiczna zapisana")
    
    # KROK 6: Test analizy wywiadu
    print("\n🎭 KROK 6: Test analizy wywiadu")
    dane_wywiadu = {
        'turn': 5,
        'nation': 'Niemcy',
        'intelligence_type': 'Ruch_Wroga',
        'source_reliability': 0.85,
        'information_freshness': 'Świeże',
        'enemy_units_spotted': 8,
        'threat_assessment_change': 'Wzrost zagrożenia',
        'intel_confidence_level': 'Wysokie',
        'actionable_intelligence': True,
        'prediction_accuracy_historical': 0.72,
        'enemy_pattern_recognition': 'Rozpoznany_Wzorzec_A',
        'deception_likelihood': 'Niska'
    }
    
    logger.loguj_analize_wywiadu(dane_wywiadu)
    print("✅ Analiza wywiadu zapisana")
    
    # KROK 7: Test wydajności
    print("\n⚡ KROK 7: Test wydajności AI")
    dane_wydajnosci = {
        'turn': 5,
        'nation': 'Niemcy',
        'decision_latency_ms': 89.3,
        'calculations_performed': 1250,
        'algorithms_used': 'PathFind,TargetEval,RiskAssess',
        'memory_usage_mb': 45.2,
        'cpu_utilization_pct': 23.8,
        'alternatives_evaluated': 12,
        'ai_confidence_score': 0.89,
        'prediction_success_rate': 0.76,
        'system_stability_index': 0.95
    }
    
    logger.loguj_wydajnosc(dane_wydajnosci)
    print("✅ Metryki wydajności zapisane")
    
    # KROK 8: Test analizy zwycięstwa
    print("\n🏆 KROK 8: Test analizy zwycięstwa")
    dane_zwyciestwa = {
        'turn': 5,
        'nation': 'Niemcy',
        'vp_trajectory': 'Wzrostowa',
        'vp_gap_analysis': '+8 VP przewagi',
        'victory_probability': 0.65,
        'path_to_victory_identified': True,
        'victory_conditions_progress': '45%',
        'time_pressure_factor': 'Średni',
        'endgame_strategy_active': False,
        'victory_point_opportunities': 3,
        'key_points_strategic_value': 'Wysokie',
        'defeat_risk_assessment': 'Niskie'
    }
    
    logger.loguj_analize_zwyciestwa(dane_zwyciestwa)
    print("✅ Analiza zwycięstwa zapisana")
    
    # KROK 9: Statystyki
    print("\n📊 KROK 9: Statystyki logów")
    stats = logger.pobierz_statystyki()
    
    for typ, info in stats.items():
        print(f"📋 {typ}:")
        print(f"   📄 Plik: {info['plik']}")
        print(f"   📝 Wierszy: {info['wiersze']}")
        print(f"   📁 Ścieżka: {info['sciezka']}")
    
    print("\n🎉 TEST ZAKOŃCZONY POMYŚLNIE!")
    print(f"📁 Wszystkie logi w: {session_dir}/ai_commander_zaawansowany/")
    
    return True

if __name__ == "__main__":
    test_nowego_systemu()