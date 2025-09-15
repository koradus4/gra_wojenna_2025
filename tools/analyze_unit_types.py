#!/usr/bin/env python3
"""
ANALIZA TYPÓW JEDNOSTEK: Porównanie balance/model.py vs rzeczywiste jednostki w grze
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def analyze_unit_types():
    """Analiza wszystkich typów jednostek w systemie"""
    
    # 1. TYPY W balance/model.py
    from balance.model import BASE_STATS, UNIT_TYPE_FULL, ALLOWED_SUPPORT
    
    balance_types = set(BASE_STATS.keys())
    
    # 2. TYPY W edytorze tokenów  
    editor_types = {"P", "K", "TC", "TŚ", "TL", "TS", "AC", "AL", "AP", "Z", "D", "G"}
    
    # 3. TYPY W rzeczywistych tokenach
    try:
        with open("assets/tokens/index.json", "r", encoding="utf-8") as f:
            tokens_data = json.load(f)
        actual_types = set(token.get('unitType', 'UNKNOWN') for token in tokens_data)
    except Exception as e:
        print(f"❌ Nie można wczytać index.json: {e}")
        actual_types = set()
    
    # 4. TYPY W core/unit_factory.py (jeśli istnieje)
    try:
        from core.unit_factory import RANGE_DEFAULTS
        factory_types = set(RANGE_DEFAULTS.keys())
    except Exception:
        factory_types = set()
    
    print("🎯 ANALIZA TYPÓW JEDNOSTEK")
    print("=" * 60)
    
    print(f"\n📊 LICZBA TYPÓW W SYSTEMACH:")
    print(f"   balance/model.py:     {len(balance_types)} typów")
    print(f"   Token Editor:         {len(editor_types)} typów")  
    print(f"   Rzeczywiste tokeny:   {len(actual_types)} typów")
    print(f"   core/unit_factory.py: {len(factory_types)} typów")
    
    print(f"\n📋 TYPY W BALANCE/MODEL.PY:")
    for t in sorted(balance_types):
        name = UNIT_TYPE_FULL.get(t, f"UNKNOWN({t})")
        stats = BASE_STATS[t]
        print(f"   {t:3} - {name:15} (MP:{stats['movement']}, AV:{stats['attack_value']}, CV:{stats['combat_value']})")
    
    print(f"\n📋 TYPY W TOKEN EDITOR:")
    for t in sorted(editor_types):
        status = "✅" if t in balance_types else "❌ BRAK"
        print(f"   {t:3} - {status}")
    
    print(f"\n📋 TYPY W RZECZYWISTYCH TOKENACH:")
    for t in sorted(actual_types):
        status = "✅" if t in balance_types else "❌ BRAK"
        count = sum(1 for token in tokens_data if token.get('unitType') == t)
        print(f"   {t:3} - {status} ({count} tokenów)")
    
    if factory_types:
        print(f"\n📋 TYPY W CORE/UNIT_FACTORY.PY:")
        for t in sorted(factory_types):
            status = "✅" if t in balance_types else "❌ BRAK"
            print(f"   {t:3} - {status}")
    
    # ANALIZA RÓŻNIC
    print(f"\n🔍 ANALIZA RÓŻNIC:")
    
    missing_in_balance = editor_types - balance_types
    if missing_in_balance:
        print(f"❌ BRAK W BALANCE/MODEL.PY: {sorted(missing_in_balance)}")
        for t in sorted(missing_in_balance):
            print(f"   → {t} występuje w edytorze ale nie ma definicji w balance/model.py")
    
    missing_in_actual = balance_types - actual_types  
    if missing_in_actual:
        print(f"❌ NIEUŻYWANE W GRZE: {sorted(missing_in_actual)}")
        for t in sorted(missing_in_actual):
            name = UNIT_TYPE_FULL.get(t, "UNKNOWN")
            print(f"   → {t} ({name}) jest zdefiniowany ale nie ma tokenów")
    
    extra_in_actual = actual_types - balance_types
    if extra_in_actual:
        print(f"❌ BRAK DEFINICJI: {sorted(extra_in_actual)}")
        for t in sorted(extra_in_actual):
            count = sum(1 for token in tokens_data if token.get('unitType') == t)
            print(f"   → {t} ma {count} tokenów ale brak definicji w balance/model.py")
    
    # ANALIZA ALLOWED_SUPPORT
    print(f"\n🛠️ ANALIZA DOZWOLONYCH WSPARĆ:")
    
    all_types_with_support = set(ALLOWED_SUPPORT.keys())
    missing_support = editor_types - all_types_with_support
    
    if missing_support:
        print(f"❌ BRAK WSPARCIA DLA: {sorted(missing_support)}")
        for t in sorted(missing_support):
            print(f"   → {t} nie ma zdefiniowanych dozwolonych wsparć")
    
    print(f"✅ TYPY Z WSPARCIEM: {sorted(all_types_with_support)}")
    
    # REKOMENDACJE
    print(f"\n💡 REKOMENDACJE:")
    
    if missing_in_balance:
        print(f"1. DODAJ DO balance/model.py:")
        for t in sorted(missing_in_balance):
            print(f'   "{t}": {{"movement": ?, "attack_range": ?, "attack_value": ?, "combat_value": ?, "defense_value": ?, "sight": ?}},')
    
    if missing_support:
        print(f"2. DODAJ WSPARCIE w ALLOWED_SUPPORT:")
        for t in sorted(missing_support):
            print(f'   "{t}": [...],  # Dodaj dozwolone wsparcia')
    
    if extra_in_actual:
        print(f"3. SPRAWDŹ TOKENY: {sorted(extra_in_actual)} mają tokeny ale brak definicji")
    
    return {
        'balance_types': balance_types,
        'editor_types': editor_types,
        'actual_types': actual_types,
        'missing_in_balance': missing_in_balance,
        'extra_in_actual': extra_in_actual
    }

if __name__ == "__main__":
    analyze_unit_types()