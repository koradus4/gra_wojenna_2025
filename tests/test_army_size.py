#!/usr/bin/env python3
"""
Test sprawdzający czy army creator tworzy właściwą liczbę jednostek
"""

import sys
sys.path.append('edytory')
from prototyp_kreator_armii import ArmyCreatorStudio
import tkinter as tk

# Test krótki bez GUI
app = ArmyCreatorStudio.__new__(ArmyCreatorStudio)
app.unit_templates = {
    'P': {'name': 'Piechota', 'base_cost': 25, 'weight': 0.4},
    'K': {'name': 'Kawaleria', 'base_cost': 30, 'weight': 0.1},
    'TL': {'name': 'Czołg Lekki', 'base_cost': 35, 'weight': 0.15}
}
app.unit_sizes = ['Pluton', 'Kompania', 'Batalion']
app.support_upgrades = {}
app.allowed_support = {'P': [], 'K': [], 'TL': []}

class MockVar:
    def __init__(self, val): 
        self.val = val
    def get(self): 
        return self.val

app.equipment_level = MockVar(50)

print("🔍 TEST ROZMIARÓW ARMII")
print("=" * 40)

# Test 1: Mała armia
print("Test 1: Armia rozmiar 2")
army = app.generate_balanced_army_preview(2, 100)
print(f"Otrzymano: {len(army)} jednostek (oczekiwano: 2)")
for i, unit in enumerate(army):
    print(f"  {i+1}. {unit['type']} - {unit['cost']} VP")

print("\n" + "=" * 40)

# Test 2: Średnia armia  
print("Test 2: Armia rozmiar 5")
army2 = app.generate_balanced_army_preview(5, 200)
print(f"Otrzymano: {len(army2)} jednostek (oczekiwano: 5)")

print("\n" + "=" * 40)

# Test 3: Bardzo mała armia
print("Test 3: Armia rozmiar 1")
army3 = app.generate_balanced_army_preview(1, 50)
print(f"Otrzymano: {len(army3)} jednostek (oczekiwano: 1)")

print("\n🎯 WYNIKI:")
print(f"Test 1 (2 jednostki): {'✅ PASS' if len(army) == 2 else '❌ FAIL'}")
print(f"Test 2 (5 jednostek): {'✅ PASS' if len(army2) == 5 else '❌ FAIL'}")
print(f"Test 3 (1 jednostka): {'✅ PASS' if len(army3) == 1 else '❌ FAIL'}")
