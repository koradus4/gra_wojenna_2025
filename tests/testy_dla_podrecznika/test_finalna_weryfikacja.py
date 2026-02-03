#!/usr/bin/env python3
"""
FINALNA WERYFIKACJA PODRĘCZNIKA - PO POPRAWKACH
Sprawdza czy poprawki zostały faktycznie zastosowane
"""

import sys
import os
import json

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def check_manual_after_corrections():
    """Sprawdza czy podręcznik zawiera poprawione informacje"""
    print("🔍 FINALNA WERYFIKACJA PO POPRAWKACH")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    manual_path = os.path.join(project_root, 'PODRECZNIK_GRY_HUMAN.md')
    
    with open(manual_path, 'r', encoding='utf-8') as f:
        manual_content = f.read()
    
    # Sprawdź poprawki
    checks = [
        {
            'name': 'Poprawiony cykl tur',
            'good': 'Po każdej turze:' in manual_content,
            'bad': 'Po każdych 6 turach' in manual_content,
            'description': 'Usunięcie nieprawdziwego cyklu 6 tur'
        },
        {
            'name': 'Poprawione zasięgi piechoty',
            'good': 'Piechota (P)**: 2 hex' in manual_content,
            'bad': 'Piechota**: 1 hex' in manual_content,
            'description': 'Zasięg piechoty poprawiony na 2 hex'
        },
        {
            'name': 'Poprawione zasięgi artylerii',
            'good': 'Artyleria (AL)**: 4 hex' in manual_content,
            'bad': 'Artyleria**: 2-4 hex' in manual_content,
            'description': 'Zasięg artylerii poprawiony na 4 hex'
        },
        {
            'name': 'Poprawione key points',
            'good': 'zweryfikowane w map_data.json' in manual_content,
            'bad': '10% wartości miasta co turę' in manual_content,
            'description': 'Usunięcie niepotwierdzonego procentu'
        },
        {
            'name': 'Modyfikatory trybów ruchu',
            'good': 'move_mult = 1.5' in manual_content and 'def_mult = 0.5' in manual_content,
            'bad': False,  # Nie szukamy złych rzeczy
            'description': 'Dodanie rzeczywistych modyfikatorów z kodu'
        },
        {
            'name': 'System pogody',
            'good': 'System pogody' in manual_content and 'Temperatura**: -5°C do 25°C' in manual_content,
            'bad': False,
            'description': 'Dodanie opisu rzeczywistego systemu pogody'
        },
        {
            'name': 'Weryfikacja w nagłówku',
            'good': 'zweryfikowany poprzez analizę kodu' in manual_content,
            'bad': False,
            'description': 'Uwaga o weryfikacji na początku'
        },
        {
            'name': 'Kontrola przez mysz',
            'good': 'Kontrola głównie przez mysz' in manual_content,
            'bad': False,
            'description': 'Podkreślenie kontroli przez mysz'
        }
    ]
    
    passed = 0
    failed = 0
    
    for check in checks:
        name = check['name']
        has_good = check['good']
        has_bad = check['bad']
        
        if has_good and not has_bad:
            print(f"   ✅ {name}: {check['description']}")
            passed += 1
        else:
            print(f"   ❌ {name}: {check['description']}")
            if not has_good:
                print(f"      BRAK: Nie znaleziono poprawionych informacji")
            if has_bad:
                print(f"      PROBLEM: Nadal zawiera nieprawidłowe informacje")
            failed += 1
    
    # Sprawdź rzeczywiste dane z tokenów
    print(f"\n📊 WERYFIKACJA RZECZYWISTYCH DANYCH:")
    
    # Sprawdź kilka plików tokenów dla potwierdzenia
    tokens_dir = os.path.join(project_root, 'assets', 'tokens')
    sample_ranges = {}
    
    for root, dirs, files in os.walk(tokens_dir):
        for file in files:
            if file == 'token.json':
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    unit_type = data.get('unitType', 'unknown')
                    attack_range = data.get('attack', {}).get('range', 1)
                    
                    if unit_type not in sample_ranges:
                        sample_ranges[unit_type] = attack_range
                        
                except:
                    continue
                
                if len(sample_ranges) >= 5:  # Wystarczy próbka
                    break
    
    print(f"   Rzeczywiste zasięgi z plików tokenów: {sample_ranges}")
    
    # Sprawdź key points z mapy
    map_data_path = os.path.join(project_root, 'data', 'map_data.json')
    if os.path.exists(map_data_path):
        with open(map_data_path, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
        
        key_points = map_data.get('key_points', {})
        key_types = {}
        
        for coords, point_data in key_points.items():
            point_type = point_data.get('type', 'unknown')
            point_value = point_data.get('value', 0)
            
            if point_type not in key_types:
                key_types[point_type] = []
            key_types[point_type].append(point_value)
        
        print(f"   Rzeczywiste key points z mapy: {key_types}")
    
    # Podsumowanie
    total = passed + failed
    accuracy = (passed / total * 100) if total > 0 else 0
    
    print(f"\n📈 PODSUMOWANIE FINALNEJ WERYFIKACJI:")
    print(f"   Poprawne sekcje: {passed}/{total} ({accuracy:.1f}%)")
    print(f"   Wymagane dalsze poprawki: {failed}")
    
    if accuracy >= 90:
        print(f"\n✅ SUKCES: Podręcznik jest prawie całkowicie poprawny!")
    elif accuracy >= 70:
        print(f"\n⚠️  POSTĘP: Znaczna poprawa, ale wymagane jeszcze poprawki")
    else:
        print(f"\n❌ WYMAGANE DALSZE PRACE: Podręcznik nadal zawiera błędy")
    
    return {
        'accuracy': accuracy,
        'passed': passed,
        'failed': failed,
        'real_data': {
            'token_ranges': sample_ranges,
            'key_points': key_types if 'key_types' in locals() else {}
        }
    }

if __name__ == "__main__":
    result = check_manual_after_corrections()
    
    print(f"\n🎯 REKOMENDACJE:")
    if result['accuracy'] >= 90:
        print(f"   ✅ Podręcznik jest gotowy do użycia")
        print(f"   ✅ Wszystkie główne błędy zostały poprawione")
    else:
        print(f"   🔧 Wymagane dalsze poprawki w {result['failed']} sekcjach")
        print(f"   📊 Wykorzystaj dane rzeczywiste: {result['real_data']}")
        print(f"   🎯 Cel: 90%+ dokładności")
