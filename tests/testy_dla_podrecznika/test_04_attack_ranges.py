#!/usr/bin/env python3
"""
TEST 4: Sprawdzenie zasięgów ataków jednostek
Sprawdza rzeczywiste zasięgi ataków różnych typów jednostek
"""

import sys
import os
import json

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_attack_ranges():
    """Test sprawdzający zasięgi ataków jednostek"""
    print("🔍 TEST 4: Zasięgi ataków jednostek")
    print("=" * 50)
    
    # Sprawdzamy pliki z definicjami jednostek
    unit_files = [
        "assets/tokens/index.json",
        "data/map_data.json"
    ]
    
    ranges_found = {}
    unit_types = {
        'P': 'Piechota',
        'AL': 'Artyleria lekka', 
        'AC': 'Artyleria ciężka',
        'AP': 'Artyleria przeciwlotnicza',
        'TL': 'Czołg lekki',
        'TŚ': 'Czołg średni',
        'TC': 'Czołg ciężki',
        'TS': 'Samochód pancerny',
        'K': 'Kawaleria',
        'L': 'Lotnictwo'
    }
    
    for file_path in unit_files:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
        if os.path.exists(full_path):
            print(f"\n📁 Sprawdzam: {file_path}")
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Jeśli to lista jednostek
                if isinstance(data, list):
                    for unit in data:
                        if isinstance(unit, dict) and 'unitType' in unit:
                            unit_type = unit.get('unitType', '')
                            attack_data = unit.get('attack', {})
                            
                            if isinstance(attack_data, dict) and 'range' in attack_data:
                                attack_range = attack_data['range']
                                unit_name = unit.get('unit', unit.get('label', f'Typ_{unit_type}'))
                                
                                if unit_type not in ranges_found:
                                    ranges_found[unit_type] = []
                                ranges_found[unit_type].append((unit_name, attack_range))
                                
                                print(f"   ✅ {unit_type} ({unit_name}): zasięg {attack_range}")
                            elif isinstance(attack_data, (int, float)):
                                # Stary format gdzie attack to tylko wartość
                                print(f"   ⚠️  {unit_type}: attack={attack_data} (brak zasięgu)")
                            else:
                                print(f"   ❌ {unit_type}: brak danych o zasięgu ataku")
                
            except json.JSONDecodeError:
                print(f"   ❌ Błąd parsowania JSON w {file_path}")
            except Exception as e:
                print(f"   ❌ Błąd odczytu {file_path}: {e}")
        else:
            print(f"   ❌ Nie znaleziono pliku: {file_path}")
    
    # Sprawdzamy kod w action.py
    action_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine", "action.py")
    default_range = None
    
    if os.path.exists(action_file):
        with open(action_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Szukamy domyślnego zasięgu
        if "get('range', 1)" in content:
            default_range = 1
            print(f"\n🔧 Domyślny zasięg ataku w kodzie: {default_range}")
        elif "get('range'," in content:
            # Wyciągnij wartość domyślną
            import re
            match = re.search(r"get\('range',\s*(\d+)\)", content)
            if match:
                default_range = int(match.group(1))
                print(f"\n🔧 Domyślny zasięg ataku w kodzie: {default_range}")
    
    print(f"\n📊 WYNIK TESTU 4:")
    
    # Analizujemy znalezione zasięgi
    for unit_type, ranges in ranges_found.items():
        type_name = unit_types.get(unit_type, unit_type)
        unique_ranges = list(set(r[1] for r in ranges))
        print(f"   {type_name} ({unit_type}): {unique_ranges}")
    
    # Sprawdzamy zgodność z podręcznikiem
    handbook_ranges = {
        'Piechota': [1],
        'Artyleria': [2, 3, 4],
        'Czołgi': [1, 2],
        'Lotnictwo': [3, 4, 5]
    }
    
    print(f"\n🔍 Porównanie z podręcznikiem:")
    for category, expected in handbook_ranges.items():
        print(f"   {category}: oczekiwane {expected}")
        
        # Znajdź odpowiadające typy jednostek
        found_ranges = []
        if category == 'Piechota' and 'P' in ranges_found:
            found_ranges = [r[1] for r in ranges_found['P']]
        elif category == 'Artyleria':
            for unit_type in ['AL', 'AC', 'AP']:
                if unit_type in ranges_found:
                    found_ranges.extend([r[1] for r in ranges_found[unit_type]])
        elif category == 'Czołgi':
            for unit_type in ['TL', 'TŚ', 'TC', 'TS']:
                if unit_type in ranges_found:
                    found_ranges.extend([r[1] for r in ranges_found[unit_type]])
        elif category == 'Lotnictwo' and 'L' in ranges_found:
            found_ranges = [r[1] for r in ranges_found['L']]
        
        if found_ranges:
            unique_found = sorted(list(set(found_ranges)))
            match = set(unique_found).intersection(set(expected))
            print(f"      Znalezione: {unique_found}")
            print(f"      Zgodność: {'✅' if match else '❌'}")
        else:
            print(f"      ❌ Brak danych w plikach")
    
    return {
        'ranges_found': ranges_found,
        'default_range': default_range
    }

if __name__ == "__main__":
    result = test_attack_ranges()
    
    if result['ranges_found']:
        print(f"\n🎯 WNIOSEK: Znaleziono dane o zasięgach ataków")
        print(f"📝 KOREKTA PODRĘCZNIKA: Zaktualizować zasięgi na podstawie rzeczywistych danych")
    else:
        print(f"\n🎯 WNIOSEK: Brak szczegółowych danych o zasięgach w plikach")
        print(f"⚠️  KOREKTA PODRĘCZNIKA: Usunąć konkretne zasięgi lub oznaczyć jako przykładowe")
