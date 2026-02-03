#!/usr/bin/env python3
"""
Dokładny test jednostek - precyzyjne porównanie
"""

import re
from pathlib import Path

def extract_shop_units():
    """Wyciąga jednostki ze sklepu"""
    with open("gui/token_shop.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Szukaj unit_type_order
    pattern = r'self\.unit_type_order\s*=\s*\[(.*?)\]'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return []
    
    unit_data = match.group(1)
    unit_pattern = r'\("([^"]+)",\s*"([^"]+)",\s*(True|False)\)'
    units = re.findall(unit_pattern, unit_data)
    
    return [(name, code, active == 'True') for name, code, active in units]

def extract_editor_units():
    """Wyciąga jednostki z edytora tokenów"""
    with open("edytory/token_editor_prototyp.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Szukaj unit_types w sekcji z radiobutton
    # Znajdź sekcję między "unit_types =" a "for text, val, state"
    pattern = r'unit_types\s*=\s*\[(.*?)\]'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return []
    
    unit_data = match.group(1)
    unit_pattern = r'\("([^"]+)",\s*"([^"]+)",\s*tk\.NORMAL\)'
    units = re.findall(unit_pattern, unit_data)
    
    return [(name, code) for name, code in units]

print("🔬 DOKŁADNY TEST PORÓWNANIA JEDNOSTEK")
print("=" * 45)

# Pobierz jednostki
shop_units = extract_shop_units()
editor_units = extract_editor_units()

print(f"📋 JEDNOSTKI W SKLEPIE ({len(shop_units)}):")
print("-" * 35)
shop_codes = set()
for name, code, active in shop_units:
    status = "✅" if active else "❌"
    print(f"{status} {code:3} | {name}")
    if active:
        shop_codes.add(code)

print(f"\n📝 JEDNOSTKI W EDYTORZE ({len(editor_units)}):")
print("-" * 37)
editor_codes = set()
for name, code in editor_units:
    print(f"✓ {code:3} | {name}")
    editor_codes.add(code)

print(f"\n🔍 PORÓWNANIE:")
print("-" * 20)

# Aktywne jednostki w sklepie
active_shop_codes = {code for name, code, active in shop_units if active}

print(f"Dostępnych w sklepie: {len(active_shop_codes)}")
print(f"W edytorze: {len(editor_codes)}")

# Sprawdź różnice
missing_in_shop = editor_codes - active_shop_codes
extra_in_shop = active_shop_codes - editor_codes

if missing_in_shop:
    print(f"❌ Brakuje w sklepie: {missing_in_shop}")
else:
    print("✅ Wszystkie jednostki z edytora są w sklepie!")

if extra_in_shop:
    print(f"➕ Dodatkowo w sklepie: {extra_in_shop}")

# Podsumowanie
print(f"\n🎯 WYNIK KOŃCOWY:")
print("-" * 20)

if len(active_shop_codes) == len(editor_codes) and not missing_in_shop:
    print("🟢 PEŁEN SUKCES!")
    print("✅ Wszystkie jednostki z edytora tokenów są dostępne w sklepie")
    print("✅ Procent dostępności: 100%")
    print("🛒 Gracz może kupić każdy typ jednostki!")
else:
    print("🟡 CZĘŚCIOWY SUKCES")
    print(f"📊 Dostępność: {len(active_shop_codes)}/{len(editor_codes)} = {len(active_shop_codes)/len(editor_codes)*100:.1f}%")

print(f"\n📋 LISTA WSZYSTKICH DOSTĘPNYCH JEDNOSTEK:")
print("-" * 40)
for code in sorted(active_shop_codes):
    unit_name = next(name for name, c, active in shop_units if c == code and active)
    print(f"  🛒 {code} - {unit_name}")
