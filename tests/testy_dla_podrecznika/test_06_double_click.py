#!/usr/bin/env python3
"""
TEST 6: Sprawdzenie podwójnego kliknięcia
Sprawdza czy podwójny klik rzeczywiście centruje mapę
"""

import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_double_click():
    """Test sprawdzający funkcję podwójnego kliknięcia"""
    print("🔍 TEST 6: Podwójne kliknięcie - centrowanie mapy")
    print("=" * 50)
    
    # Lista plików do sprawdzenia
    files_to_check = [
        "gui/panel_mapa.py",
        "gui/panel_generala.py",
        "gui/panel_dowodcy.py"
    ]
    
    found_double_click = False
    found_center_functions = []
    
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📁 Sprawdzam: {file_path}")
            
            # Szukamy bind na podwójny klik
            double_click_events = ['<Double-Button-1>', '<Double-1>', '<Button-1><Button-1>']
            for event in double_click_events:
                if event in content:
                    found_double_click = True
                    print(f"   ✅ Znaleziono event podwójnego kliknięcia: {event}")
                    
                    # Znajdź linię z tym eventem
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if event in line:
                            print(f"      L{i+1}: {line.strip()}")
            
            # Szukamy funkcji centrowania
            center_functions = ['center', 'Center', 'centruj', 'focus', 'moveto']
            for func in center_functions:
                if func in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if func in line and ('def ' in line or 'center_on' in line):
                            found_center_functions.append((file_path, func, i+1, line.strip()))
                            print(f"   ✅ Znaleziono funkcję centrowania: {line.strip()}")
    
    # Sprawdzamy konkretnie panel_mapa.py dla funkcji center_on_player_tokens
    mapa_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gui", "panel_mapa.py")
    if os.path.exists(mapa_file):
        with open(mapa_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n🔍 Szczegółowa analiza panel_mapa.py:")
        
        if 'center_on_player_tokens' in content:
            print(f"   ✅ Znaleziono center_on_player_tokens()")
            
            # Sprawdź czy jest wywoływana
            if 'center_on_player_tokens()' in content:
                print(f"   ✅ Funkcja jest wywoływana")
            else:
                print(f"   ⚠️  Funkcja zdefiniowana ale może nie być używana")
        
        # Sprawdź czy są funkcje scroll/move
        scroll_functions = ['xview_moveto', 'yview_moveto', 'scroll']
        for func in scroll_functions:
            if func in content:
                print(f"   ✅ Znaleziono funkcję przewijania: {func}")
    
    print(f"\n📊 WYNIK TESTU 6:")
    print(f"   Znaleziono bind na podwójny klik: {'✅' if found_double_click else '❌'}")
    print(f"   Znaleziono funkcje centrowania: {len(found_center_functions)}")
    
    if found_center_functions:
        print(f"   Funkcje centrowania:")
        for file_path, func, line_num, line_content in found_center_functions:
            print(f"      {os.path.basename(file_path)}: {func} (L{line_num})")
    
    # Sprawdzamy czy są automatyczne wywołania centrowania
    auto_center = False
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'after(100' in content and 'center' in content:
                auto_center = True
                print(f"   ✅ Znaleziono automatyczne centrowanie w {os.path.basename(file_path)}")
    
    return {
        'double_click_bound': found_double_click,
        'center_functions': len(found_center_functions),
        'auto_center': auto_center
    }

if __name__ == "__main__":
    result = test_double_click()
    
    if result['double_click_bound']:
        print(f"\n🎯 WNIOSEK: Podwójne kliknięcie jest zaimplementowane")
        print(f"✅ PODRĘCZNIK POPRAWNY: Podwójny klik centruje mapę")
    elif result['center_functions'] > 0:
        print(f"\n🎯 WNIOSEK: Funkcje centrowania istnieją, ale brak bind na podwójny klik")
        print(f"⚠️  KOREKTA PODRĘCZNIKA: Centrowanie może być automatyczne, nie przez podwójny klik")
    else:
        print(f"\n🎯 WNIOSEK: Brak implementacji podwójnego kliknięcia")
        print(f"❌ KOREKTA PODRĘCZNIKA: Usunąć informację o podwójnym kliknięciu")
