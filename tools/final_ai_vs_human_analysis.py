#!/usr/bin/env python3
"""
KOŃCOWA ANALIZA: Które TYPY jednostek AI może sprawnie kontrolować vs HUMAN
Na podstawie problemów z D_Pluton__2_Dow_dztwo_Einheit i logiki garnizonu
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def final_unit_types_analysis():
    """Końcowa analiza typów jednostek AI vs HUMAN"""
    print("🎯 KOŃCOWA ANALIZA: TYPY JEDNOSTEK AI vs HUMAN CONTROL")
    print("=" * 70)
    
    # Wczytaj definicje jednostek
    try:
        with open("assets/tokens/index.json", "r", encoding="utf-8") as f:
            units_data = json.load(f)
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return
    
    # Kategoryzacja według typu i charakterystyki
    unit_categories = {
        'D': {'name': 'DOWÓDCY', 'units': [], 'ai_rating': 2, 'human_rating': 9},
        'P': {'name': 'PLUTONY', 'units': [], 'ai_rating': 8, 'human_rating': 6},
        'Z': {'name': 'BATALIONY', 'units': [], 'ai_rating': 9, 'human_rating': 5},
        'K': {'name': 'KOMPANIE', 'units': [], 'ai_rating': 8, 'human_rating': 6},
        'AC': {'name': 'ARMOURED CARS', 'units': [], 'ai_rating': 7, 'human_rating': 6},
        'AL': {'name': 'ARTILLERY', 'units': [], 'ai_rating': 6, 'human_rating': 7},
        'TL': {'name': 'TANKS LIGHT', 'units': [], 'ai_rating': 7, 'human_rating': 6},
    }
    
    # Przypisz jednostki do kategorii
    for unit in units_data:
        unit_type = unit.get('unitType', 'Unknown')
        if unit_type in unit_categories:
            unit_categories[unit_type]['units'].append(unit)
    
    print("📊 OCENA SKUTECZNOŚCI KONTROLI (1-10):")
    print("=" * 50)
    
    for type_code, category in unit_categories.items():
        units = category['units']
        if not units:
            continue
            
        # Statystyki kategorii
        avg_move = sum(u.get('move', 0) for u in units) / len(units)
        avg_combat = sum(u.get('combat_value', 0) for u in units) / len(units)
        avg_defense = sum(u.get('defense_value', 0) for u in units) / len(units)
        
        print(f"\n🔹 {category['name']} ({type_code}) - {len(units)} jednostek:")
        print(f"   📊 Średnie: {avg_move:.1f} MP, {avg_combat:.1f} CV, {avg_defense:.1f} DV")
        print(f"   🤖 AI Control Rating: {category['ai_rating']}/10")
        print(f"   👤 Human Control Rating: {category['human_rating']}/10")
        
        # Szczegółowe uzasadnienie
        if type_code == 'D':
            print(f"   ❌ AI PROBLEMY: System garnizonu, wymaga wsparcia, blokuje ruch")
            print(f"   ✅ HUMAN PLUS: Może ręcznie zarządzać wsparciem i taktyką")
        elif type_code == 'Z':
            print(f"   ✅ AI PLUS: Wysoka mobilność (6.6 MP), jasna rola bojowa")
            print(f"   ⚠️ HUMAN: Może być przytłoczony ilością jednostek")
        elif type_code == 'P':
            print(f"   ✅ AI PLUS: Średnia mobilność (4.2 MP), standardowe jednostki")
            print(f"   ⚠️ HUMAN: Wymaga mikromanagementu wielu jednostek")
        elif type_code == 'AL':
            print(f"   ⚠️ AI PROBLEMY: Wymaga pozycjonowania, zasięg ataku")
            print(f"   ✅ HUMAN PLUS: Lepsza taktyka artylerii")
    
    print(f"\n🎖️ SZCZEGÓLNY PRZYPADEK - DOWÓDCA:")
    print(f"   ID: D_Pluton__2_Dow_dztwo_Einheit")
    print(f"   🚫 PROBLEM AI: INSUFFICIENT_SUPPORT - nie może znaleźć wsparcia")
    print(f"   📍 Pozycja: (15, -7) - kluczowy punkt strategiczny")
    print(f"   ⚙️ Wymaga: 1-2 jednostki wsparcia do ruchu")
    print(f"   🎯 ROZWIĄZANIE: Przełączenie na kontrolę HUMAN")
    
    print(f"\n🎮 REKOMENDACJE PODZIAŁU KONTROLI:")
    print("=" * 45)
    
    print(f"\n👤 HUMAN POWINIEN KONTROLOWAĆ:")
    print(f"   🎖️ DOWÓDCÓW (typ D) - system garnizonu AI nie działa")
    print(f"   🎯 ARTYLЕРIĘ (AL, TL) - wymaga pozycjonowania")
    print(f"   🏰 Jednostki specjalne - wymaga taktyki")
    print(f"   📍 Kluczowe pozycje - strategiczne decyzje")
    
    print(f"\n🤖 AI MOŻE SPRAWNIE KONTROLOWAĆ:")
    print(f"   ⚡ BATALIONY (Z) - wysoka mobilność, jasne role")
    print(f"   ⚔️ PLUTONY (P) - standardowe jednostki bojowe")
    print(f"   🚗 KOMPANIE (K) - mobilne jednostki")
    print(f"   🛡️ ARMOURED CARS (AC) - rozpoznanie i wsparcie")
    
    print(f"\n🎯 TRYB HYBRYDOWY (ZALECANY):")
    print(f"   👤 Human: Dowództwo strategiczne (D, AL, TL)")
    print(f"   🤖 AI: Wykonanie taktyczne (Z, P, K, AC)")
    print(f"   📊 Proporcja: ~20% Human, ~80% AI")
    
    print(f"\n🚨 NATYCHMIASTOWE DZIAŁANIE:")
    print(f"   1. Przełącz D_Pluton__2_Dow_dztwo_Einheit na kontrolę HUMAN")
    print(f"   2. Human ręcznie przydziela wsparcie z pobliskich jednostek")
    print(f"   3. AI kontroluje pozostałe jednostki bojowe")
    print(f"   4. Monitoruj logi garrison_problems.csv")
    
    print(f"\n🔧 POTRZEBNE MODYFIKACJE KODU:")
    print(f"   • Flaga unit['human_controlled'] = True dla dowódców")
    print(f"   • Wyłączenie wsparcie_garnizonu.py dla jednostek HUMAN")
    print(f"   • Interface wyboru kontroli w GUI")
    print(f"   • Osobne przetwarzanie HUMAN vs AI units")

if __name__ == "__main__":
    final_unit_types_analysis()