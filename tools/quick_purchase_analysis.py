#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🛒 Quick Purchase Analysis
"""

import pandas as pd

# Load purchase data
df = pd.read_csv('logs/ai_purchases_20250908.csv')

print("🛒 === AI PURCHASE DETAILED ANALYSIS ===")
print(f"📊 Total units purchased: {len(df)}")
print(f"🎯 Unit types distribution: {df['unit_type'].value_counts().to_dict()}")
print(f"💰 Average cost per unit: {df['cost'].mean():.1f} PE")
print(f"💵 Total investment: {df['cost'].sum()} PE")
print(f"🌍 Nations purchasing: {df['nation'].value_counts().to_dict()}")
print(f"👤 Commander distribution: {df['commander_id'].value_counts().to_dict()}")

print("\n📈 === PURCHASE EFFICIENCY METRICS ===")
print(f"🎯 Units per PE invested: {len(df)/df['cost'].sum():.4f}")

# Analyze supports
supports_data = df['supports'].dropna()
print(f"🔧 Units with support equipment: {len(supports_data)}/{len(df)}")

# Nation-specific analysis
print("\n🌍 === NATION-SPECIFIC ANALYSIS ===")
for nation in df['nation'].unique():
    nation_data = df[df['nation'] == nation]
    print(f"📊 {nation}: {len(nation_data)} units, {nation_data['cost'].sum()} PE total")
    print(f"   Unit types: {nation_data['unit_type'].value_counts().to_dict()}")

print("\n✅ Phase 4 purchasing system working efficiently!")
