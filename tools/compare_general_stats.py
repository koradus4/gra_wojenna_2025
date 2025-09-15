#!/usr/bin/env python3
"""Porównanie statystyk Generała: balance/model.py vs core/unit_factory.py"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.unit_factory import RANGE_DEFAULTS, MOVE_DEFAULTS, ATTACK_DEFAULTS, DEFENSE_DEFAULTS, SIGHT_DEFAULTS
from balance.model import BASE_STATS

print("🎯 PORÓWNANIE STATYSTYK GENERAŁA (G)")
print("=" * 50)

print("\n📊 DANE Z CORE/UNIT_FACTORY.PY:")
print(f"  RANGE_DEFAULTS['G']: {RANGE_DEFAULTS.get('G', 'BRAK')}")
print(f"  MOVE_DEFAULTS['G']: {MOVE_DEFAULTS.get('G', 'BRAK')}")
print(f"  ATTACK_DEFAULTS['Pluton']['G']: {ATTACK_DEFAULTS.get('Pluton', {}).get('G', 'BRAK')}")
print(f"  DEFENSE_DEFAULTS['Pluton']['G']: {DEFENSE_DEFAULTS.get('Pluton', {}).get('G', 'BRAK')}")
print(f"  SIGHT_DEFAULTS['G']: {SIGHT_DEFAULTS.get('G', 'BRAK')}")

print("\n📊 DANE Z BALANCE/MODEL.PY:")
g_stats = BASE_STATS.get('G', {})
print(f"  movement: {g_stats.get('movement', 'BRAK')}")
print(f"  attack_range: {g_stats.get('attack_range', 'BRAK')}")
print(f"  attack_value: {g_stats.get('attack_value', 'BRAK')}")
print(f"  combat_value: {g_stats.get('combat_value', 'BRAK')}")
print(f"  defense_value: {g_stats.get('defense_value', 'BRAK')}")
print(f"  sight: {g_stats.get('sight', 'BRAK')}")

print("\n🔍 ANALIZA ZGODNOŚCI:")
factory_data = {
    'movement': MOVE_DEFAULTS.get('G'),
    'attack_range': RANGE_DEFAULTS.get('G'),
    'attack_value': ATTACK_DEFAULTS.get('Pluton', {}).get('G'),
    'defense_value': DEFENSE_DEFAULTS.get('Pluton', {}).get('G'),
    'sight': SIGHT_DEFAULTS.get('G')
}

balance_data = {
    'movement': g_stats.get('movement'),
    'attack_range': g_stats.get('attack_range'),
    'attack_value': g_stats.get('attack_value'),
    'defense_value': g_stats.get('defense_value'),
    'sight': g_stats.get('sight')
}

for key in factory_data.keys():
    factory_val = factory_data[key]
    balance_val = balance_data[key]
    status = "✅ OK" if factory_val == balance_val else "❌ RÓŻNICA"
    print(f"  {key:15}: factory={factory_val:2} vs balance={balance_val:2} - {status}")

# Sprawdźmy też combat_value
print(f"\n📋 DODATKOWE INFO:")
# W core/unit_factory.py combat_value pochodzi z COMBAT_DEFAULTS
combat_defaults = {
    "P__Pluton": 8, "P__Kompania": 15, "P__Batalion": 30,
    "K__Pluton": 6, "K__Kompania": 12, "K__Batalion": 24,
    "TC__Pluton": 12, "TC__Kompania": 24, "TC__Batalion": 48,
    "TŚ__Pluton": 10, "TŚ__Kompania": 20, "TŚ__Batalion": 42,
    "TL__Pluton": 8, "TL__Kompania": 16, "TL__Batalion": 36,
    "TS__Pluton": 6, "TS__Kompania": 12, "TS__Batalion": 30,
    "AC__Pluton": 8, "AC__Kompania": 16, "AC__Batalion": 48,
    "AL__Pluton": 6, "AL__Kompania": 12, "AL__Batalion": 42,
    "AP__Pluton": 6, "AP__Kompania": 12, "AP__Batalion": 36,
    "Z__Pluton": 4, "Z__Kompania": 12, "Z__Batalion": 24,
    "D__Pluton": 3, "D__Kompania": 9, "D__Batalion": 18,
    "G__Pluton": 2, "G__Kompania": 6, "G__Batalion": 12,
}

factory_combat = combat_defaults.get("G__Pluton")
balance_combat = g_stats.get('combat_value')
combat_status = "✅ OK" if factory_combat == balance_combat else "❌ RÓŻNICA"
print(f"  combat_value:    factory={factory_combat:2} vs balance={balance_combat:2} - {combat_status}")

print("\n💡 REKOMENDACJE:")
if factory_data['movement'] != balance_data['movement']:
    print(f"  ⚠️  Movement: zmień z {balance_data['movement']} na {factory_data['movement']}")
if factory_data['attack_range'] != balance_data['attack_range']:
    print(f"  ⚠️  Attack_range: zmień z {balance_data['attack_range']} na {factory_data['attack_range']}")
if factory_data['attack_value'] != balance_data['attack_value']:
    print(f"  ⚠️  Attack_value: zmień z {balance_data['attack_value']} na {factory_data['attack_value']}")
if factory_data['defense_value'] != balance_data['defense_value']:
    print(f"  ⚠️  Defense_value: zmień z {balance_data['defense_value']} na {factory_data['defense_value']}")
if factory_data['sight'] != balance_data['sight']:
    print(f"  ⚠️  Sight: zmień z {balance_data['sight']} na {factory_data['sight']}")
if factory_combat != balance_combat:
    print(f"  ⚠️  Combat_value: zmień z {balance_combat} na {factory_combat}")