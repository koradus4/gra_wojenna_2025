#!/usr/bin/env python3
"""
TEST 5: Sprawdzenie startowego budżetu
Sprawdza czy gracze mają określony startowy budżet na początku gry
"""

import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_starting_budget():
    """Test sprawdzający startowy budżet graczy"""
    print("🔍 TEST 5: Startowy budżet graczy")
    print("=" * 50)
    
    # Lista plików do sprawdzenia
    files_to_check = [
        "core/ekonomia.py",
        "engine/player.py", 
        "main.py",
        "main_ai_vs_human.py",
        "gui/ekran_startowy.py"
    ]
    
    starting_budget_info = {}
    
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📁 Sprawdzam: {file_path}")
            
            # Szukamy inicjalizacji punktów ekonomicznych
            lines = content.split('\n')
            found_initialization = False
            
            for i, line in enumerate(lines):
                # Szukamy ustawienia economic_points
                if 'economic_points' in line and ('=' in line or '__init__' in line):
                    print(f"   L{i+1}: {line.strip()}")
                    found_initialization = True
                    
                    # Wyciągnij wartość
                    if '=' in line and not '==' in line:
                        parts = line.split('=')
                        if len(parts) >= 2:
                            value_part = parts[-1].strip()
                            if value_part.isdigit():
                                starting_budget_info[file_path] = int(value_part)
                                print(f"      ✅ Startowy budżet: {value_part}")
                            elif value_part == '0':
                                starting_budget_info[file_path] = 0
                                print(f"      ⚠️  Startowy budżet: 0 (może być uzupełniany później)")
                            else:
                                print(f"      ❓ Wartość: {value_part}")
            
            if not found_initialization:
                print(f"   ❌ Brak inicjalizacji economic_points")
    
    # Sprawdzamy konkretnie klasę EconomySystem
    ekonomia_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core", "ekonomia.py")
    if os.path.exists(ekonomia_file):
        with open(ekonomia_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n🔍 Szczegółowa analiza core/ekonomia.py:")
        
        # Znajdź klasę EconomySystem
        lines = content.split('\n')
        in_init = False
        init_value = None
        
        for i, line in enumerate(lines):
            if 'class EconomySystem' in line:
                print(f"   ✅ Znaleziono klasę EconomySystem w linii {i+1}")
            elif 'def __init__' in line:
                in_init = True
                print(f"   ✅ Znaleziono __init__ w linii {i+1}")
            elif in_init and line.strip().startswith('def '):
                break
            elif in_init and 'self.economic_points' in line and '=' in line:
                parts = line.split('=')
                if len(parts) >= 2:
                    init_value = parts[-1].strip()
                    print(f"      ✅ Inicjalizacja: self.economic_points = {init_value}")
                    break
        
        if init_value == '0':
            print(f"   ⚠️  Economic points inicjalizowane na 0")
            print(f"   🔍 Sprawdzamy czy są dodawane później...")
            
            # Szukamy generate_economic_points lub add_economic_points
            if 'generate_economic_points' in content:
                print(f"      ✅ Znaleziono generate_economic_points()")
            if 'add_economic_points' in content:
                print(f"      ✅ Znaleziono add_economic_points()")
    
    # Sprawdzamy czy gracze dostają punkty na starcie
    main_files = ["main.py", "main_ai_vs_human.py"]
    for file_path in main_files:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'economic_points' in content:
                print(f"\n🔍 Sprawdzam inicjalizację graczy w {file_path}:")
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'economic_points' in line and ('=' in line or 'generate' in line):
                        print(f"   L{i+1}: {line.strip()}")
    
    print(f"\n📊 WYNIK TESTU 5:")
    
    if starting_budget_info:
        print(f"   Znalezione wartości startowe:")
        for file, value in starting_budget_info.items():
            print(f"      {os.path.basename(file)}: {value} punktów")
    else:
        print(f"   ❌ Nie znaleziono konkretnych wartości startowego budżetu")
    
    # Sprawdzamy domyślną wartość
    if 'core/ekonomia.py' in starting_budget_info:
        default_value = starting_budget_info['core/ekonomia.py']
        if default_value == 0:
            print(f"   ⚠️  Domyślny budżet: 0 (uzupełniany podczas gry)")
        else:
            print(f"   ✅ Domyślny budżet: {default_value} punktów")
    
    return starting_budget_info

if __name__ == "__main__":
    result = test_starting_budget()
    
    has_fixed_budget = any(v > 0 for v in result.values())
    
    if has_fixed_budget:
        print(f"\n🎯 WNIOSEK: Gracze mają określony startowy budżet")
        print(f"✅ PODRĘCZNIK POPRAWNY: Startowy budżet jest określony na początku gry")
    else:
        print(f"\n🎯 WNIOSEK: Budżet inicjalizowany na 0, uzupełniany podczas gry")
        print(f"❌ KOREKTA PODRĘCZNIKA: Startowy budżet to 0, punkty generowane w trakcie gry")
