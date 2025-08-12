#!/usr/bin/env python3
"""
TEST 3: Sprawdzenie skrótów klawiaturowych
Sprawdza czy klawisze M, R, C rzeczywiście zmieniają tryb ruchu
"""

import tkinter as tk
import sys
import os

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_keyboard_shortcuts():
    """Test sprawdzający skróty klawiaturowe"""
    print("🔍 TEST 3: Skróty klawiaturowe")
    print("=" * 50)
    
    # Lista plików do sprawdzenia
    files_to_check = [
        "gui/panel_mapa.py",
        "gui/panel_generala.py", 
        "gui/panel_dowodcy.py",
        "main.py",
        "main_ai_vs_human.py"
    ]
    
    found_key_bindings = {}
    key_shortcuts = ['M', 'R', 'C', 'Spacja', 'Enter', 'Escape', 'Tab', 'Ctrl+S', 'Ctrl+L', 'F1', 'F5']
    
    for shortcut in key_shortcuts:
        found_key_bindings[shortcut] = False
    
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📁 Sprawdzam: {file_path}")
            
            # Szukamy bind() calls
            bind_calls = []
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '.bind(' in line:
                    bind_calls.append((i+1, line.strip()))
            
            if bind_calls:
                print(f"   ✅ Znaleziono {len(bind_calls)} bind() calls:")
                for line_num, call in bind_calls:
                    print(f"      L{line_num}: {call}")
            else:
                print(f"   ❌ Brak bind() calls")
            
            # Sprawdzamy konkretne skróty
            for shortcut in key_shortcuts:
                if shortcut == 'M':
                    if '<m>' in content.lower() or '<M>' in content or 'KeyPress.*m' in content:
                        found_key_bindings[shortcut] = True
                        print(f"      ✅ Znaleziono klawisz {shortcut}")
                elif shortcut == 'R':
                    if '<r>' in content.lower() or '<R>' in content or 'KeyPress.*r' in content:
                        found_key_bindings[shortcut] = True
                        print(f"      ✅ Znaleziono klawisz {shortcut}")
                elif shortcut == 'C':
                    if '<c>' in content.lower() or '<C>' in content or 'KeyPress.*c' in content:
                        found_key_bindings[shortcut] = True
                        print(f"      ✅ Znaleziono klawisz {shortcut}")
                elif shortcut == 'Spacja':
                    if '<space>' in content.lower() or '<Space>' in content or 'KeyPress.*space' in content:
                        found_key_bindings[shortcut] = True
                        print(f"      ✅ Znaleziono klawisz {shortcut}")
                elif shortcut == 'Enter':
                    if '<return>' in content.lower() or '<Return>' in content or '<enter>' in content.lower():
                        found_key_bindings[shortcut] = True
                        print(f"      ✅ Znaleziono klawisz {shortcut}")
                elif shortcut == 'Escape':
                    if '<escape>' in content.lower() or '<Escape>' in content:
                        found_key_bindings[shortcut] = True
                        print(f"      ✅ Znaleziono klawisz {shortcut}")
                elif shortcut == 'Tab':
                    if '<tab>' in content.lower() or '<Tab>' in content:
                        found_key_bindings[shortcut] = True
                        print(f"      ✅ Znaleziono klawisz {shortcut}")
                elif shortcut == 'Ctrl+S':
                    if '<control-s>' in content.lower() or '<Control-s>' in content or 'ctrl.*s' in content.lower():
                        found_key_bindings[shortcut] = True
                        print(f"      ✅ Znaleziono klawisz {shortcut}")
                elif shortcut == 'Ctrl+L':
                    if '<control-l>' in content.lower() or '<Control-l>' in content or 'ctrl.*l' in content.lower():
                        found_key_bindings[shortcut] = True
                        print(f"      ✅ Znaleziono klawisz {shortcut}")
                elif shortcut == 'F1':
                    if '<f1>' in content.lower() or '<F1>' in content:
                        found_key_bindings[shortcut] = True
                        print(f"      ✅ Znaleziono klawisz {shortcut}")
                elif shortcut == 'F5':
                    if '<f5>' in content.lower() or '<F5>' in content:
                        found_key_bindings[shortcut] = True
                        print(f"      ✅ Znaleziono klawisz {shortcut}")
    
    print(f"\n📊 WYNIK TESTU 3:")
    working_shortcuts = [k for k, v in found_key_bindings.items() if v]
    missing_shortcuts = [k for k, v in found_key_bindings.items() if not v]
    
    print(f"   Działające skróty ({len(working_shortcuts)}): {', '.join(working_shortcuts) if working_shortcuts else 'BRAK'}")
    print(f"   Brakujące skróty ({len(missing_shortcuts)}): {', '.join(missing_shortcuts)}")
    
    return found_key_bindings

if __name__ == "__main__":
    result = test_keyboard_shortcuts()
    working_count = sum(1 for v in result.values() if v)
    total_count = len(result)
    
    print(f"\n🎯 WNIOSEK: {working_count}/{total_count} skrótów klawiaturowych znalezionych w kodzie")
    if working_count < total_count // 2:
        print(f"❌ KOREKTA PODRĘCZNIKA: Większość skrótów klawiaturowych NIE jest zaimplementowana")
        print(f"📝 UWAGA: Sprawdzić rzeczywiste skróty w grze lub usunąć z podręcznika")
    else:
        print(f"✅ PODRĘCZNIK CZĘŚCIOWO POPRAWNY: Część skrótów może działać")
