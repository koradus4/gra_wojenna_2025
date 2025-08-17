#!/usr/bin/env python3
"""
Prosty test sprawdzenia dostępnych jednostek w sklepie
"""

import sys
from pathlib import Path

# Sprawdź czy plik sklepu istnieje
sklep_path = Path("gui/token_shop.py")
if not sklep_path.exists():
    print(f"❌ Plik {sklep_path} nie istnieje!")
    sys.exit(1)

print("🔍 ANALIZA PLIKU SKLEPU JEDNOSTEK")
print("=" * 40)

# Przeczytaj i analizuj plik sklepu
with open(sklep_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Znajdź definicję unit_type_order
import re

pattern = r'self\.unit_type_order\s*=\s*\[(.*?)\]'
match = re.search(pattern, content, re.DOTALL)

if not match:
    print("❌ Nie znaleziono definicji unit_type_order!")
    sys.exit(1)

unit_data = match.group(1)
print("✓ Znaleziono definicję unit_type_order")

# Wyciągnij jednostki
unit_pattern = r'\("([^"]+)",\s*"([^"]+)",\s*(True|False)\)'
units = re.findall(unit_pattern, unit_data)

print(f"\n📋 ZNALEZIONE JEDNOSTKI ({len(units)} typów):")
print("-" * 50)

dostepne = 0
niedostepne = 0

for full_name, code, is_active in units:
    active = is_active == 'True'
    status = "✅ DOSTĘPNA" if active else "❌ NIEDOSTĘPNA"
    print(f"{code:3} | {full_name:25} | {status}")
    
    if active:
        dostepne += 1
    else:
        niedostepne += 1

print(f"\n📊 PODSUMOWANIE:")
print(f"Wszystkich jednostek: {len(units)}")
print(f"Dostępnych: {dostepne}")
print(f"Niedostępnych: {niedostepne}")
print(f"Procent dostępności: {dostepne/len(units)*100:.1f}%")

# Sprawdź czy wszystkie są dostępne
if dostepne == len(units):
    print("\n🎉 SUKCES: Wszystkie jednostki są dostępne w sklepie!")
    print("✅ Można kupować każdy typ jednostki z edytora tokenów.")
else:
    print(f"\n⚠️ UWAGA: {niedostepne} jednostek jest niedostępnych")
    print("🔧 Niektóre jednostki z edytora nie są dostępne w sklepie.")

# Porównaj z edytorem tokenów
editor_path = Path("edytory/token_editor_prototyp.py")
if editor_path.exists():
    print(f"\n🔍 PORÓWNANIE Z EDYTOREM TOKENÓW:")
    print("-" * 35)
    
    with open(editor_path, 'r', encoding='utf-8') as f:
        editor_content = f.read()
    
    # Znajdź jednostki w edytorze
    editor_pattern = r'\("([^"]+)",\s*"([^"]+)",\s*tk\.NORMAL\)'
    editor_units = re.findall(editor_pattern, editor_content)
    
    print(f"Jednostek w edytorze: {len(editor_units)}")
    print(f"Jednostek w sklepie: {len(units)}")
    
    # Sprawdź czy wszystkie z edytora są w sklepie
    editor_codes = set(code for _, code in editor_units)
    shop_codes = set(code for _, code, _ in units)
    
    missing_in_shop = editor_codes - shop_codes
    extra_in_shop = shop_codes - editor_codes
    
    if missing_in_shop:
        print(f"❌ Brakuje w sklepie: {missing_in_shop}")
    if extra_in_shop:
        print(f"➕ Dodatkowo w sklepie: {extra_in_shop}")
    
    if not missing_in_shop and not extra_in_shop:
        print("✅ Sklep ma dokładnie te same jednostki co edytor!")

print(f"\n🏁 KONIEC ANALIZY")
