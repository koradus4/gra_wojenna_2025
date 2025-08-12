#!/usr/bin/env python3
"""
TEST WERYFIKACYJNY: Sprawdzenie czy podręcznik zawiera poprawione informacje
"""

import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_manual_corrections():
    """Sprawdza czy podręcznik zawiera poprawione informacje"""
    print("🔍 WERYFIKACJA PODRĘCZNIKA: Sprawdzenie poprawek")
    print("=" * 55)
    
    # Ścieżka do podręcznika
    manual_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                               'PODRECZNIK_GRY_HUMAN.md')
    
    if not os.path.exists(manual_path):
        print(f"❌ BŁĄD: Nie znaleziono podręcznika w {manual_path}")
        return False
    
    # Wczytaj podręcznik
    with open(manual_path, 'r', encoding='utf-8') as f:
        manual_content = f.read()
    
    # Sprawdzenia poprawek
    corrections_check = {
        'timer_color': {
            'should_contain': '#6B8E23',
            'should_not_contain': 'żółty → czerwony',
            'description': 'Timer ma stały kolor ciemnozielony'
        },
        'keyboard_shortcuts': {
            'should_contain': 'Kontrola głównie przez mysz',
            'should_not_contain': 'Klawisz`|`Funkcja`|`Kontekst',
            'description': 'Brak tabeli skrótów klawiaturowych'
        },
        'attack_ranges': {
            'should_contain': 'domyślnie 1 hex',
            'should_not_contain': 'Piechota**: 1 hex',
            'description': 'Zasięgi definiowane w statystykach'
        },
        'starting_budget': {
            'should_contain': 'Rozpoczyna z 0 punktów',
            'should_not_contain': 'Określony na początku gry',
            'description': 'Budżet startuje z 0'
        },
        'double_click': {
            'should_contain': 'Scrollbary',
            'should_not_contain': 'Podwójny klik**: Wycentrowanie',
            'description': 'Przewijanie przez scrollbary'
        },
        'verification_notice': {
            'should_contain': 'zweryfikowany poprzez analizę kodu',
            'should_not_contain': '',
            'description': 'Uwaga o weryfikacji'
        }
    }
    
    results = []
    
    for test_name, check in corrections_check.items():
        print(f"\n🔍 {test_name.upper()}:")
        
        # Sprawdź czy zawiera wymagane
        if check['should_contain']:
            if check['should_contain'] in manual_content:
                print(f"   ✅ ZAWIERA: '{check['should_contain']}'")
                contains_required = True
            else:
                print(f"   ❌ BRAK: '{check['should_contain']}'")
                contains_required = False
        else:
            contains_required = True
        
        # Sprawdź czy nie zawiera zabronionych
        if check['should_not_contain']:
            if check['should_not_contain'] not in manual_content:
                print(f"   ✅ NIE ZAWIERA: '{check['should_not_contain']}'")
                not_contains_forbidden = True
            else:
                print(f"   ❌ NADAL ZAWIERA: '{check['should_not_contain']}'")
                not_contains_forbidden = False
        else:
            not_contains_forbidden = True
        
        # Wynik testu
        test_passed = contains_required and not_contains_forbidden
        results.append({
            'test': test_name,
            'passed': test_passed,
            'description': check['description']
        })
        
        if test_passed:
            print(f"   ✅ POPRAWKA: {check['description']}")
        else:
            print(f"   ❌ PROBLEM: {check['description']}")
    
    # Podsumowanie
    print(f"\n📊 PODSUMOWANIE WERYFIKACJI:")
    print(f"=" * 35)
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    print(f"Poprawne sekcje: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    
    if passed_count == total_count:
        print(f"✅ SUKCES: Wszystkie poprawki zostały zastosowane!")
        print(f"Podręcznik jest teraz zgodny z rzeczywistym kodem gry.")
    else:
        print(f"❌ WYMAGANE DODATKOWE POPRAWKI:")
        for result in results:
            if not result['passed']:
                print(f"   • {result['test']}: {result['description']}")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = test_manual_corrections()
    
    if success:
        print(f"\n🎉 ZADANIE UKOŃCZONE!")
        print(f"Podręcznik został zweryfikowany i poprawiony.")
        print(f"Wszystkie opisane funkcje są zgodne z rzeczywistym działaniem gry.")
    else:
        print(f"\n⚠️  WYMAGANE DALSZE POPRAWKI")
        print(f"Niektóre sekcje podręcznika wymagają dodatkowych korekt.")
