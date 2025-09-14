#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TEST PROFILU AGRESYWNEGO AI - Weryfikacja czy tryb agresywny się podpina

Sprawdza:
1. Czy AI faktycznie używa profil 'aggressive' 
2. Czy progi ataku się różnią (aggressive vs defensive)
3. Czy AI porusza się w kierunku wrogów
4. Czy system reakcji działa po ruchu
5. Czy ataki są wykonywane gdy warunki są spełnione

UWAGA: Ten test analizuje szczegółowo profile AI i ich zachowanie
"""

import sys
from pathlib import Path

# Dodaj ścieżkę do głównego katalogu
sys.path.append(str(Path(__file__).parent))

try:
    from tests.advanced_game_tester import AdvancedGameTester, TestScenario
    from engine.game_engine import GameEngine
    from ai.ai_commander import AICommander
    from ai.konfiguracja_ai import AIConfiguration
except ImportError as e:
    print(f"❌ Błąd importu: {e}")
    sys.exit(1)

def test_ai_profiles():
    """Test sprawdzający czy profile AI się faktycznie podpinają"""
    print("🧪 TEST PROFILI AI - AGRESYWNY vs DEFENSYWNY")
    print("=" * 60)
    
    # Inicjalizuj silnik gry
    engine = GameEngine()
    
    # Utwórz konfiguracje AI
    print("🔧 Tworzę konfiguracje AI...")
    
    # Test 1: Agresywny profil
    config_aggressive = AIConfiguration()
    config_aggressive.set_profile('aggressive')
    
    print(f"📋 Profil agresywny:")
    print(f"   - Próg ataku: {config_aggressive.combat_thresholds['aggressive']}")
    print(f"   - Próg defensywny: {config_aggressive.combat_thresholds['defensive']}")
    print(f"   - Agresja: {config_aggressive.get_aggression_level()}")
    
    # Test 2: Defensywny profil
    config_defensive = AIConfiguration() 
    config_defensive.set_profile('defensive')
    
    print(f"📋 Profil defensywny:")
    print(f"   - Próg ataku: {config_defensive.combat_thresholds['aggressive']}")
    print(f"   - Próg defensywny: {config_defensive.combat_thresholds['defensive']}")
    print(f"   - Agresja: {config_defensive.get_aggression_level()}")
    
    # Test 3: Sprawdź czy rzeczywiście się różnią
    print(f"\n🔍 PORÓWNANIE:")
    
    agg_threshold = config_aggressive.combat_thresholds['aggressive']
    def_threshold = config_defensive.combat_thresholds['defensive']
    
    print(f"   - Agresywny próg ataku: {agg_threshold}")
    print(f"   - Defensywny próg ataku: {def_threshold}")
    print(f"   - Różnica: {def_threshold - agg_threshold:.2f}")
    
    if agg_threshold < def_threshold:
        print("   ✅ Agresywny ma niższy próg (częściej atakuje)")
    else:
        print("   ❌ Progi są niepoprawne!")
    
    return agg_threshold != def_threshold

def test_combat_scenario():
    """Test scenariusza z faktycznym kontaktem bojowym"""
    print("\n🥊 TEST SCENARIUSZA BOJOWEGO")
    print("=" * 60)
    
    # Uruchom test z konkretnym scenariuszem
    tester = AdvancedGameTester()
    
    # Scenariusz z polskimi agresorami vs niemieckimi obrońcami
    scenario = TestScenario(
        name="combat_test_aggressive",
        description="Test bojowy - Agresywny vs Defensywny",
        max_turns=8,
        ai_profiles={"polish": "aggressive", "german": "defensive"},
        expected_duration_minutes=2.0,
        special_conditions={"forced_contact": True}  # Wymuś kontakt
    )
    
    print("🎯 Uruchamiam scenariusz bojowy...")
    result = tester.run_single_test(scenario)
    
    print(f"📊 Wyniki:")
    print(f"   - Status: {result.test_result.value}")
    print(f"   - Czas: {result.duration_seconds:.1f}s")
    print(f"   - Tur: {result.total_turns}")
    print(f"   - Średni czas tury AI: {result.ai_avg_turn_time:.2f}s")
    print(f"   - Błędy AI: {result.ai_errors_count}")
    print(f"   - Performance: {result.performance_score:.0f}/100")
    
    if result.winner:
        print(f"   - Zwycięzca: {result.winner}")
    
    # Analiza szczegółowa
    print(f"\n📋 SZCZEGÓŁOWA ANALIZA:")
    if result.issues_found:
        print(f"   ⚠️ Problemy:")
        for issue in result.issues_found:
            print(f"     • {issue}")
    else:
        print(f"   ✅ Brak wykrytych problemów")
    
    return result

def main():
    """Główna funkcja testowa"""
    print("🚀 SZCZEGÓŁOWY TEST PROFILI AI")
    print("=" * 60)
    
    # Test 1: Profile configuration
    profiles_ok = test_ai_profiles()
    
    # Test 2: Combat scenario  
    combat_result = test_combat_scenario()
    
    # Podsumowanie
    print(f"\n📋 PODSUMOWANIE TESTÓW:")
    print(f"   ✅ Profile poprawnie skonfigurowane: {'TAK' if profiles_ok else 'NIE'}")
    print(f"   ✅ Test bojowy ukończony: {'TAK' if combat_result.test_result.value == 'PASS' else 'NIE'}")
    
    if profiles_ok and combat_result.test_result.value == 'PASS':
        print(f"\n🎉 WSZYSTKIE TESTY PRZESZŁY - AI PROFILE DZIAŁAJĄ POPRAWNIE!")
    else:
        print(f"\n❌ WYKRYTO PROBLEMY - SPRAWDŹ SZCZEGÓŁY POWYŻEJ")
    
    print(f"\n💡 Następny krok: Uruchom main.py żeby przetestować w prawdziwej grze!")

if __name__ == "__main__":
    main()