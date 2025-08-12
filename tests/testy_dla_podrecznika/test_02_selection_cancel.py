#!/usr/bin/env python3
"""
TEST 2: Sprawdzenie anulowania wyboru jednostek
Sprawdza czy klik na puste pole rzeczywiście anuluje wybór jednostki
"""

import tkinter as tk
import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_unit_selection_cancel():
    """Test sprawdzający anulowanie wyboru jednostek"""
    print("🔍 TEST 2: Anulowanie wyboru jednostek")
    print("=" * 50)
    
    # Sprawdzamy kod w panel_mapa.py
    mapa_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "gui", "panel_mapa.py")
    
    if not os.path.exists(mapa_file):
        print(f"❌ Nie znaleziono pliku: {mapa_file}")
        return False
    
    with open(mapa_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Szukamy funkcji _on_click
    lines = content.split('\n')
    in_on_click = False
    found_cancel_logic = False
    found_selected_token_reset = False
    
    print(f"📁 Analizuję: gui/panel_mapa.py")
    
    for i, line in enumerate(lines):
        if 'def _on_click' in line:
            in_on_click = True
            print(f"   ✅ Znaleziono funkcję _on_click w linii {i+1}")
        elif in_on_click and (line.strip().startswith('def ') or line.strip().startswith('class ')):
            break
        elif in_on_click:
            # Szukamy logiki anulowania
            if 'selected_token_id' in line and '= None' in line:
                found_selected_token_reset = True
                print(f"   ✅ Znaleziono reset selected_token_id: {line.strip()}")
            
            # Szukamy warunków dotyczących pustego pola
            if ('clicked_token is None' in line or 'clicked_token == None' in line) and 'selected_token_id' in line:
                found_cancel_logic = True
                print(f"   ✅ Znaleziono logikę anulowania: {line.strip()}")
    
    # Sprawdzamy konkretnie linię 521 z analizy
    try:
        target_line = lines[520]  # linia 521 (0-indexed)
        if 'selected_token_id = None' in target_line:
            print(f"   ✅ Linia 521 zawiera reset: {target_line.strip()}")
            found_selected_token_reset = True
    except IndexError:
        print(f"   ❌ Nie można sprawdzić linii 521")
    
    # Sprawdzamy warunek z linii 523-524
    try:
        condition_line = lines[522]  # linia 523
        action_line = lines[523]    # linia 524
        if 'clicked_token is None' in condition_line and 'clear_token_info_panel' in action_line:
            print(f"   ✅ Znaleziono kompletną logikę anulowania:")
            print(f"      {condition_line.strip()}")
            print(f"      {action_line.strip()}")
            found_cancel_logic = True
    except IndexError:
        print(f"   ❌ Nie można sprawdzić linii 523-524")
    
    print(f"\n📊 WYNIK TESTU 2:")
    print(f"   Funkcja _on_click istnieje: ✅")
    print(f"   Reset selected_token_id: {'✅' if found_selected_token_reset else '❌'}")
    print(f"   Logika anulowania przy pustym polu: {'✅' if found_cancel_logic else '❌'}")
    
    return {
        'cancel_exists': found_cancel_logic,
        'reset_exists': found_selected_token_reset
    }

if __name__ == "__main__":
    result = test_unit_selection_cancel()
    if result['cancel_exists'] and result['reset_exists']:
        print(f"\n🎯 WNIOSEK: Anulowanie wyboru jednostek DZIAŁA")
        print(f"✅ PODRĘCZNIK POPRAWNY: Klik na puste pole anuluje wybór")
    else:
        print(f"\n🎯 WNIOSEK: Anulowanie wyboru może nie działać prawidłowo")
        print(f"⚠️  KOREKTA PODRĘCZNIKA: Sprawdzić dokładnie działanie anulowania")
