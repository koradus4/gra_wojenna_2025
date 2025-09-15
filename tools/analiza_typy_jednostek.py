#!/usr/bin/env python3
"""
ANALIZA TYPÓW JEDNOSTEK: Które AI obsługuje sprawnie vs Human
Szczególnie w kontekście problemu z D_Pluton__2_Dow_dztwo_Einheit
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_unit_types_ai_vs_human():
    """Analiza jakimi typami jednostek AI vs Human lepiej zarządza"""
    print("🎯 ANALIZA TYPÓW JEDNOSTEK: AI vs HUMAN")
    print("=" * 60)
    
    # Wczytaj definicje jednostek
    try:
        with open("assets/tokens/index.json", "r", encoding="utf-8") as f:
            units_data = json.load(f)
    except Exception as e:
        print(f"❌ Nie można wczytać index.json: {e}")
        return
    
    # Analiza problemu z D_Pluton__2_Dow_dztwo_Einheit
    print("\n1️⃣ PROBLEM Z DOWÓDCĄ:")
    problem_unit = None
    for unit in units_data:
        if unit.get('id') == 'D_Pluton__2_Dow_dztwo_Einheit':
            problem_unit = unit
            break
    
    if problem_unit:
        print(f"🎖️ DOWÓDCA: {problem_unit['id']}")
        print(f"   📍 Pozycja: (15, -7)")
        print(f"   🚶 Mobilność: {problem_unit.get('move', 0)} MP")
        print(f"   ⛽ Paliwo: {problem_unit.get('maintenance', 0)}")
        print(f"   🛡️ Obrona: {problem_unit.get('defense_value', 0)}")
        print(f"   ⚔️ Wartość bojowa: {problem_unit.get('combat_value', 0)}")
        print(f"   👁️ Widoczność: {problem_unit.get('sight', 0)}")
        print(f"   💰 Koszt: {problem_unit.get('price', 0)}")
        print(f"   📋 Typ: {problem_unit.get('unitType', 'N/A')}")
        print(f"   📏 Rozmiar: {problem_unit.get('unitSize', 'N/A')}")
    
    # Kategoryzacja typów jednostek
    unit_types = {}
    for unit in units_data:
        unit_type = unit.get('unitType', 'Unknown')
        if unit_type not in unit_types:
            unit_types[unit_type] = []
        unit_types[unit_type].append(unit)
    
    print(f"\n2️⃣ TYPY JEDNOSTEK W GRZE:")
    for unit_type, units in unit_types.items():
        avg_move = sum(u.get('move', 0) for u in units) / len(units)
        avg_combat = sum(u.get('combat_value', 0) for u in units) / len(units)
        avg_defense = sum(u.get('defense_value', 0) for u in units) / len(units)
        
        print(f"🔹 TYP {unit_type}: {len(units)} jednostek")
        print(f"   📊 Średnia mobilność: {avg_move:.1f}")
        print(f"   ⚔️ Średnia wartość bojowa: {avg_combat:.1f}")
        print(f"   🛡️ Średnia obrona: {avg_defense:.1f}")
    
    print(f"\n3️⃣ ANALIZA PROBLEMU GARNIZONU:")
    print("❌ PROBLEM: D_Pluton__2_Dow_dztwo_Einheit")
    print("   • Status: INSUFFICIENT_SUPPORT")
    print("   • Potrzebuje: 1-2 jednostki wsparcia")
    print("   • Znajduje: 0 jednostek wsparcia")
    print("   • Pozycja: (15, -7) - punkt kluczowy")
    
    print(f"\n4️⃣ CHARAKTERYSTYKA TYPÓW JEDNOSTEK:")
    
    # Analiza według mobilności
    high_mobility = [u for u in units_data if u.get('move', 0) >= 6]
    medium_mobility = [u for u in units_data if 3 <= u.get('move', 0) < 6]
    low_mobility = [u for u in units_data if u.get('move', 0) < 3]
    
    print(f"\n📱 MOBILNOŚĆ:")
    print(f"🚀 Wysoką (≥6 MP): {len(high_mobility)} jednostek")
    print(f"🚶 Średnią (3-5 MP): {len(medium_mobility)} jednostek") 
    print(f"🐌 Niską (<3 MP): {len(low_mobility)} jednostek")
    
    # Analiza dowódców
    commanders = [u for u in units_data if u.get('unitType') == 'D']
    print(f"\n🎖️ DOWÓDCY ({len(commanders)} jednostek):")
    for cmd in commanders:
        move = cmd.get('move', 0)
        combat = cmd.get('combat_value', 0)
        defense = cmd.get('defense_value', 0)
        nation = cmd.get('nation', 'Unknown')
        mobility_category = "🚀" if move >= 6 else "🚶" if move >= 3 else "🐌"
        print(f"   {mobility_category} {cmd['id']}: {move}MP, {combat}CV, {defense}DV ({nation})")
    
    print(f"\n5️⃣ WNIOSKI - JAKIE TYPY AI OBSŁUGUJE LEPIEJ:")
    
    print(f"\n✅ AI SPRAWNIE OBSŁUGUJE:")
    print(f"   🚀 Jednostki mobilne (≥6 MP) - mogą szybko przemieszczać się po mapie")
    print(f"   ⚔️ Jednostki bojowe (P, Z, K, T, AC, AL) - mają jasne role taktyczne")
    print(f"   🎯 Jednostki o jasnej roli - artyleria, pancerne, piechota")
    print(f"   📊 Jednostki z dobrymi statystykami ruchu/walki")
    
    print(f"\n⚠️ AI MA PROBLEMY Z:")
    print(f"   🎖️ DOWÓDCAMI (typ D) - wymagają wsparcia garnizonu")
    print(f"   🐌 Jednostki niskę mobilne (<3 MP) - trudno przemieścić")
    print(f"   🏰 Jednostki garnizonu - złożona logika wsparcia")
    print(f"   📍 Jednostki specjalne - wymagają szczególnej obsługi")
    
    print(f"\n👤 HUMAN LEPIEJ OBSŁUGUJE:")
    print(f"   🎖️ DOWÓDCÓW - może manual zarządzać wsparciem")
    print(f"   🏗️ Jednostki wsparcia - może ręcznie przydzielać")
    print(f"   📋 Jednostki specjalne - intuicyjna obsługa")
    print(f"   🎯 Taktykę garnizonu - może planować długoterminowo")
    
    print(f"\n6️⃣ REKOMENDACJE:")
    print(f"   🤖 AI: Mobilne jednostki bojowe (P, Z, K, AC, AL)")
    print(f"   👤 HUMAN: Dowódcy, jednostki wsparcia, garnizony")
    print(f"   🎮 TRYB MIESZANY: AI kontroluje wojska, Human kontroluje dowództwo")

if __name__ == "__main__":
    analyze_unit_types_ai_vs_human()