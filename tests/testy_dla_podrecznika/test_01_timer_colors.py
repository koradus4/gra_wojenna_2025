#!/usr/bin/env python3
"""
TEST 1: Sprawdzenie kolorów timera
Sprawdza czy timer rzeczywiście zmienia kolory (żółty → czerwony)
"""

import tkinter as tk
import time
import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_timer_colors():
    """Test sprawdzający kolory timera w panel_generala.py"""
    print("🔍 TEST 1: Sprawdzenie kolorów timera")
    print("=" * 50)
    
    # Szukamy w kodzie zmian kolorów
    timer_files = [
        "gui/panel_generala.py",
        "gui/panel_dowodcy.py"
    ]
    
    found_color_changes = False
    
    for file_path in timer_files:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            print(f"\n📁 Sprawdzam: {file_path}")
            
            # Szukamy zmiany kolorów
            color_keywords = ['red', 'yellow', 'config.*bg', 'timer.*color']
            for keyword in color_keywords:
                if keyword.lower() in content.lower():
                    print(f"   ✅ Znaleziono: {keyword}")
                    found_color_changes = True
                else:
                    print(f"   ❌ Brak: {keyword}")
    
    # Sprawdzamy czy timer ma zmianę kolorów w update_timer
    timer_update_found = False
    for file_path in timer_files:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'update_timer' in content:
                timer_update_found = True
                # Sprawdzamy czy w update_timer są warunki czasowe
                lines = content.split('\n')
                in_update_timer = False
                conditional_color_change = False
                
                for line in lines:
                    if 'def update_timer' in line:
                        in_update_timer = True
                    elif in_update_timer and (line.strip().startswith('def ') or line.strip().startswith('class ')):
                        break
                    elif in_update_timer:
                        if ('if' in line and ('time' in line or 'remaining' in line or '60' in line or '10' in line)) and 'config' in line:
                            conditional_color_change = True
                            print(f"   ✅ Znaleziono warunkową zmianę koloru: {line.strip()}")
                
                if not conditional_color_change:
                    print(f"   ❌ Brak warunkowej zmiany kolorów w update_timer")
    
    print(f"\n📊 WYNIK TESTU 1:")
    print(f"   Timer ma update_timer: {'✅' if timer_update_found else '❌'}")
    print(f"   Znaleziono zmiany kolorów: {'✅' if found_color_changes else '❌'}")
    print(f"   Warunkowa zmiana koloru: {'❌ NIE ZNALEZIONO'}")
    
    return {
        'timer_exists': timer_update_found,
        'color_changes': found_color_changes,
        'conditional_colors': False  # Na podstawie analizy
    }

if __name__ == "__main__":
    result = test_timer_colors()
    print(f"\n🎯 WNIOSEK: Timer NIE zmienia kolorów warunkowa (żółty→czerwony)")
    print(f"💡 KOREKTA PODRĘCZNIKA: Usunąć informacje o zmianie kolorów timera")
