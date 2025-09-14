#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SZYBKI TEST GRY - Weryfikacja działania AI i rozgrywki

Narzędzie do sprawdzania czy gra działa poprawnie po zmianach:
- Szybki test (5 min) - podstawowe scenariusze AI vs AI
- Pełny test (20 min) - wszystkie tryby i profile AI
- Test wydajnościowy (10 min) - analiza szybkości i pamięci
- Test konkretnego scenariusza - wybrany profil AI

Użycie:
  python szybki_test_gry.py                    # Szybki test
  python szybki_test_gry.py --full            # Pełny test  
  python szybki_test_gry.py --performance     # Test wydajności
  python szybki_test_gry.py --scenario aggressive_vs_defensive
  python szybki_test_gry.py --list-scenarios  # Lista dostępnych testów

IDEALNE PO NAPRAWIE AI - sprawdzi czy Niemcy faktycznie się ruszają!
"""

import sys
import argparse
from pathlib import Path

# Dodaj ścieżkę do głównego katalogu
sys.path.append(str(Path(__file__).parent.parent))

try:
    from tests.advanced_game_tester import AdvancedGameTester, TestScenario
except ImportError as e:
    print(f"❌ Błąd importu: {e}")
    print("Upewnij się, że uruchamiasz z katalogu głównego gry")
    sys.exit(1)

def szybki_test():
    """Szybki test - tylko podstawowe scenariusze (5 minut)"""
    print("⚡ SZYBKI TEST GRY - 3 scenariusze (~5 minut)")
    print("🎯 Sprawdzamy czy AI Niemiec i Polaków działa poprawnie")
    print("-" * 50)
    
    tester = AdvancedGameTester()
    scenarios = [
        TestScenario(
            name="quick_balanced",
            description="Szybki test zbalansowany",
            max_turns=6,
            ai_profiles={"polish": "balanced", "german": "balanced"},
            expected_duration_minutes=1.5
        ),
        TestScenario(
            name="quick_aggressive",
            description="Szybki test agresywny",
            max_turns=5,
            ai_profiles={"polish": "aggressive", "german": "aggressive"},
            expected_duration_minutes=1.0
        ),
        TestScenario(
            name="quick_mixed",
            description="Szybki test mieszany",
            max_turns=6,
            ai_profiles={"polish": "defensive", "german": "aggressive"},
            expected_duration_minutes=1.5
        )
    ]
    
    results = []
    for scenario in scenarios:
        result = tester.run_single_test(scenario)
        results.append(result)
    
    # Szybkie podsumowanie
    passed = sum(1 for r in results if r.test_result.value == "PASS")
    total = len(results)
    
    print(f"\n🏁 WYNIKI SZYBKIEGO TESTU:")
    print(f"✅ Przeszło: {passed}/{total}")
    print(f"📈 Sukces: {passed/total*100:.0f}%")
    
    if passed == total:
        print("🎉 Wszystkie testy przeszły - gra działa poprawnie!")
    elif passed >= total * 0.7:
        print("⚠️ Większość testów przeszła - drobne problemy")
    else:
        print("❌ Poważne problemy - sprawdź logi szczegółowe")
    
    return results

def test_wydajnosci():
    """Test wydajnościowy - analiza szybkości AI (10 minut)"""
    print("⚡ TEST WYDAJNOŚCIOWY - analiza szybkości AI")
    print("🔧 Sprawdzamy czy AI nie zużywa za dużo pamięci i czasu")
    print("-" * 50)
    
    tester = AdvancedGameTester()
    scenarios = [
        TestScenario(
            name="perf_stress_test",
            description="Test obciążeniowy AI",
            max_turns=8,
            ai_profiles={"polish": "aggressive", "german": "aggressive"},
            special_conditions={"max_units": True},
            expected_duration_minutes=3.0
        ),
        TestScenario(
            name="perf_endurance",
            description="Test wytrzymałościowy",
            max_turns=15,
            ai_profiles={"polish": "balanced", "german": "balanced"},
            expected_duration_minutes=5.0
        ),
        TestScenario(
            name="perf_adaptation",
            description="Test adaptacji AI",
            max_turns=10,
            ai_profiles={"polish": "balanced", "german": "balanced"},
            special_conditions={"profile_switching": True},
            expected_duration_minutes=3.0
        )
    ]
    
    results = []
    for scenario in scenarios:
        result = tester.run_single_test(scenario)
        results.append(result)
    
    # Analiza wydajności
    avg_turn_time = sum(r.ai_avg_turn_time for r in results) / len(results)
    max_memory = max(r.memory_usage_mb for r in results)
    total_errors = sum(r.engine_errors + r.ai_errors_count for r in results)
    
    print(f"\n📊 ANALIZA WYDAJNOŚCI:")
    print(f"⏱️ Średni czas tury AI: {avg_turn_time:.2f}s")
    print(f"💾 Maksymalne zużycie pamięci: {max_memory:.1f}MB")
    print(f"❗ Łączne błędy: {total_errors}")
    
    if avg_turn_time < 3.0 and max_memory < 300 and total_errors == 0:
        print("🚀 EXCELLENT - AI jest szybkie i stabilne!")
    elif avg_turn_time < 5.0 and max_memory < 500 and total_errors <= 2:
        print("✅ GOOD - AI działa dobrze")
    else:
        print("⚠️ NEEDS OPTIMIZATION - AI wymaga optymalizacji")
    
    return results

def test_pojedynczego_scenariusza(nazwa_scenariusza: str):
    """Uruchamia pojedynczy wybrany scenariusz"""
    print(f"🎯 TEST WYBRANEGO SCENARIUSZA: {nazwa_scenariusza}")
    print("📋 Szczegółowa analiza konkretnego profilu AI")
    print("-" * 50)
    
    tester = AdvancedGameTester()
    all_scenarios = tester.get_test_scenarios()
    
    # Znajdź scenariusz
    scenario = None
    for s in all_scenarios:
        if s.name == nazwa_scenariusza:
            scenario = s
            break
    
    if not scenario:
        print(f"❌ Nie znaleziono scenariusza: {nazwa_scenariusza}")
        print(f"📝 Dostępne scenariusze:")
        for s in all_scenarios:
            print(f"  • {s.name}: {s.description}")
        return None
    
    result = tester.run_single_test(scenario)
    
    print(f"\n📋 WYNIKI SCENARIUSZA '{nazwa_scenariusza}':")
    print(f"🏆 Wynik: {result.test_result.value}")
    print(f"📊 Performance: {result.performance_score:.1f}/100")
    print(f"⏱️ Czas: {result.duration_seconds:.1f}s")
    print(f"🔄 Tur: {result.total_turns}")
    
    if result.winner:
        print(f"🥇 Zwycięzca: {result.winner}")
    
    if result.issues_found:
        print(f"⚠️ Problemy:")
        for issue in result.issues_found:
            print(f"  • {issue}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Szybki Test Gry - Weryfikacja AI")
    parser.add_argument("--full", action="store_true", 
                       help="Pełny test wszystkich scenariuszy (20 min)")
    parser.add_argument("--performance", action="store_true",
                       help="Test wydajnościowy AI (10 min)") 
    parser.add_argument("--scenario", type=str,
                       help="Test konkretnego scenariusza")
    parser.add_argument("--list-scenarios", action="store_true",
                       help="Pokaż dostępne scenariusze testowe")
    
    args = parser.parse_args()
    
    if args.list_scenarios:
        print("📝 DOSTĘPNE SCENARIUSZE TESTOWE:")
        tester = AdvancedGameTester()
        for scenario in tester.get_test_scenarios():
            print(f"  • {scenario.name}: {scenario.description}")
            print(f"    Profile AI: {scenario.ai_profiles}")
            print(f"    Max tur: {scenario.max_turns}")
            print(f"    Czas: ~{scenario.expected_duration_minutes:.1f} min")
            print()
        return
    
    if args.full:
        # Pełny test wszystkich scenariuszy
        print("🔥 PEŁNY TEST GRY - wszystkie scenariusze (20 min)")
        tester = AdvancedGameTester()
        summary = tester.run_full_test_suite()
        
    elif args.performance:
        # Test wydajnościowy
        results = test_wydajnosci()
        
    elif args.scenario:
        # Pojedynczy scenariusz
        result = test_pojedynczego_scenariusza(args.scenario)
        
    else:
        # Domyślny szybki test
        results = szybki_test()
    
    print(f"\n📁 Szczegółowe wyniki zapisane w: tests/results/")
    print("💡 Użyj --help aby zobaczyć więcej opcji")
    print("\n🎮 Po teście możesz uruchomić prawdziwą grę przez main.py!")

if __name__ == "__main__":
    main()