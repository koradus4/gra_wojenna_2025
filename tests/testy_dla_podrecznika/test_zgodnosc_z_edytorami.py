#!/usr/bin/env python3
"""
Test spójności podręcznika z edytorami
Sprawdza czy podręcznik jest aktualny po potencjalnych zmianach z edytorów
"""

import os
import sys
import json
import re
from pathlib import Path

# Dodaj ścieżkę do głównego katalogu
sys.path.append(str(Path(__file__).parent.parent))

def test_editor_compatibility():
    """Test głównej zgodności podręcznika z edytorami"""
    
    print("🔄 TEST SPÓJNOŚCI PODRĘCZNIKA Z EDYTORAMI")
    print("=" * 60)
    
    # 1. Sprawdź brakujące sekcje
    missing_sections = check_missing_sections()
    
    # 2. Sprawdź zasięgi jednostek
    range_inconsistencies = check_unit_ranges()
    
    # 3. Sprawdź key points
    key_point_inconsistencies = check_key_points()
    
    # 4. Sprawdź typy terenu
    terrain_inconsistencies = check_terrain_types()
    
    # 5. Sprawdź system wsparcia
    support_system_missing = check_support_system()
    
    # Podsumowanie
    print("\n📊 PODSUMOWANIE ANALIZY:")
    print("=" * 40)
    
    total_issues = (len(missing_sections) + len(range_inconsistencies) + 
                   len(key_point_inconsistencies) + len(terrain_inconsistencies) + 
                   len(support_system_missing))
    
    if total_issues == 0:
        print("✅ Podręcznik jest w pełni zgodny z edytorami")
        return True
    else:
        print(f"❌ Znaleziono {total_issues} problemów ze spójnością")
        print("🔄 Podręcznik WYMAGA aktualizacji po użyciu edytorów")
        return False

def check_missing_sections():
    """Sprawdza brakujące sekcje w podręczniku"""
    
    print("\n🔍 SPRAWDZENIE BRAKUJĄCYCH SEKCJI:")
    print("-" * 40)
    
    manual_path = Path(__file__).parent.parent.parent / "PODRECZNIK_GRY_HUMAN.md"
    
    try:
        with open(manual_path, 'r', encoding='utf-8') as f:
            manual_content = f.read()
    except FileNotFoundError:
        print("❌ Nie można znaleźć podręcznika!")
        return ["manual_not_found"]
    
    missing_sections = []
    
    # Sprawdź sekcje, które powinny być w podręczniku
    required_sections = [
        "system wsparcia",
        "upgrade",
        "drużyna granatników",
        "sekcja ckm",
        "sekcja km.ppanc",
        "obserwator",
        "ciągnik artyleryjski",
        "most",  # nowy typ key point
        "balansowanie armii",
        "automatyczne tworzenie armii"
    ]
    
    for section in required_sections:
        if section.lower() not in manual_content.lower():
            missing_sections.append(section)
            print(f"❌ Brakuje sekcji: {section}")
    
    if not missing_sections:
        print("✅ Wszystkie wymagane sekcje są obecne")
    else:
        print(f"❌ Brakuje {len(missing_sections)} sekcji!")
    
    return missing_sections

def check_unit_ranges():
    """Sprawdza zgodność zasięgów jednostek"""
    
    print("\n🔍 SPRAWDZENIE ZASIĘGÓW JEDNOSTEK:")
    print("-" * 40)
    
    # Zasięgi z podręcznika
    manual_ranges = {
        "P": 2,   # Piechota
        "AL": 4,  # Artyleria lekka
        "K": 1,   # Kawaleria
        "R": 1,   # Zwiad
        "TL": 1,  # Czołgi lekkie
        "TS": 2,  # Czołgi średnie
        "TŚ": 2,  # Czołgi ciężkie
        "Z": 1    # Zaopatrzenie
    }
    
    inconsistencies = []
    
    # Sprawdź zasięgi z tokenów
    tokens_path = Path(__file__).parent.parent.parent / "assets" / "tokens"
    
    if not tokens_path.exists():
        print("⚠️ Katalog tokenów nie istnieje - brak danych do porównania")
        return ["tokens_missing"]
    
    actual_ranges = {}
    
    # Przejdź przez wszystkie tokeny
    for nation_dir in tokens_path.iterdir():
        if nation_dir.is_dir() and nation_dir.name in ["Polska", "Niemcy"]:
            for token_dir in nation_dir.iterdir():
                if token_dir.is_dir():
                    token_json = token_dir / "token.json"
                    if token_json.exists():
                        try:
                            with open(token_json, 'r', encoding='utf-8') as f:
                                token_data = json.load(f)
                            
                            unit_type = token_data.get("unitType", "")
                            attack_range = token_data.get("attack", {}).get("range", 0)
                            
                            if unit_type in manual_ranges:
                                if unit_type not in actual_ranges:
                                    actual_ranges[unit_type] = set()
                                actual_ranges[unit_type].add(attack_range)
                                
                        except json.JSONDecodeError:
                            continue
    
    # Porównaj zasięgi
    for unit_type, expected_range in manual_ranges.items():
        if unit_type in actual_ranges:
            ranges_in_tokens = actual_ranges[unit_type]
            if len(ranges_in_tokens) > 1:
                inconsistencies.append(f"{unit_type}: różne zasięgi w tokenach: {ranges_in_tokens}")
                print(f"❌ {unit_type}: różne zasięgi w tokenach: {ranges_in_tokens}")
            elif expected_range not in ranges_in_tokens:
                actual_range = list(ranges_in_tokens)[0]
                inconsistencies.append(f"{unit_type}: podręcznik={expected_range}, tokeny={actual_range}")
                print(f"❌ {unit_type}: podręcznik={expected_range}, tokeny={actual_range}")
            else:
                print(f"✅ {unit_type}: zasięg zgodny ({expected_range})")
        else:
            print(f"⚠️ {unit_type}: brak tokenów do porównania")
    
    return inconsistencies

def check_key_points():
    """Sprawdza zgodność key points"""
    
    print("\n🔍 SPRAWDZENIE KEY POINTS:")
    print("-" * 40)
    
    # Key points z podręcznika
    manual_key_points = {
        "miasto": {"count": 8, "value": 100},
        "fortyfikacja": {"count": 1, "value": 150},
        "węzeł komunikacyjny": {"count": 3, "value": 75}
    }
    
    inconsistencies = []
    
    # Sprawdź key points z map_data.json
    map_data_path = Path(__file__).parent.parent.parent / "data" / "map_data.json"
    
    if not map_data_path.exists():
        print("⚠️ Plik map_data.json nie istnieje")
        return ["map_data_missing"]
    
    try:
        with open(map_data_path, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
    except json.JSONDecodeError:
        print("❌ Błąd odczytu map_data.json")
        return ["map_data_error"]
    
    # Zlicz key points z mapy
    actual_key_points = {}
    
    if "key_points" in map_data:
        for kp_type, kp_list in map_data["key_points"].items():
            if kp_type not in actual_key_points:
                actual_key_points[kp_type] = {"count": 0, "values": set()}
            
            actual_key_points[kp_type]["count"] = len(kp_list)
            for kp in kp_list:
                if isinstance(kp, dict) and "value" in kp:
                    actual_key_points[kp_type]["values"].add(kp["value"])
                elif isinstance(kp, (int, float)):
                    actual_key_points[kp_type]["values"].add(kp)
    
    # Sprawdź edytor mapy
    editor_path = Path(__file__).parent.parent.parent / "edytory" / "map_editor_prototyp.py"
    editor_key_points = {}
    
    if editor_path.exists():
        try:
            with open(editor_path, 'r', encoding='utf-8') as f:
                editor_content = f.read()
            
            # Wyciągnij available_key_point_types
            match = re.search(r'available_key_point_types = \{([^}]+)\}', editor_content, re.DOTALL)
            if match:
                types_str = match.group(1)
                for line in types_str.split('\n'):
                    if ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            key = parts[0].strip().strip('"\'')
                            value = parts[1].strip().rstrip(',')
                            try:
                                editor_key_points[key] = int(value)
                            except ValueError:
                                pass
        except Exception as e:
            print(f"⚠️ Błąd analizy edytora mapy: {e}")
    
    # Porównaj dane
    print(f"📋 Podręcznik ma {len(manual_key_points)} typów key points")
    print(f"📋 Mapa ma {len(actual_key_points)} typów key points")
    print(f"📋 Edytor ma {len(editor_key_points)} typów key points")
    
    # Sprawdź czy edytor ma typy nieobecne w podręczniku
    for editor_type, editor_value in editor_key_points.items():
        if editor_type not in manual_key_points:
            inconsistencies.append(f"Edytor ma nowy typ: {editor_type} ({editor_value} pkt)")
            print(f"❌ Edytor ma nowy typ: {editor_type} ({editor_value} pkt)")
    
    # Sprawdź zgodność wartości
    for kp_type, manual_data in manual_key_points.items():
        if kp_type in actual_key_points:
            actual_data = actual_key_points[kp_type]
            if manual_data["count"] != actual_data["count"]:
                inconsistencies.append(f"{kp_type}: podręcznik={manual_data['count']}, mapa={actual_data['count']}")
                print(f"❌ {kp_type}: podręcznik={manual_data['count']}, mapa={actual_data['count']}")
            
            if manual_data["value"] not in actual_data["values"]:
                inconsistencies.append(f"{kp_type}: wartość w podręczniku ({manual_data['value']}) nie występuje na mapie")
                print(f"❌ {kp_type}: wartość w podręczniku ({manual_data['value']}) nie występuje na mapie")
            else:
                print(f"✅ {kp_type}: zgodny")
        else:
            print(f"⚠️ {kp_type}: brak na mapie")
    
    return inconsistencies

def check_terrain_types():
    """Sprawdza zgodność typów terenu"""
    
    print("\n🔍 SPRAWDZENIE TYPÓW TERENU:")
    print("-" * 40)
    
    # Typy terenu z podręcznika
    manual_terrain = {
        "Pole otwarte": {"move_cost": 1, "mod": 0},
        "Las": {"move_cost": 3, "mod": 2},
        "Wzgórze": {"move_cost": 2, "mod": 1},
        "Rzeka": {"move_cost": 4, "mod": 3},
        "Bagno": {"move_cost": 4, "mod": 3},
        "Droga": {"move_cost": 1, "mod": -1},
        "Miasto": {"move_cost": 1, "mod": 0}
    }
    
    inconsistencies = []
    
    # Sprawdź typy terenu z edytora
    editor_path = Path(__file__).parent.parent.parent / "edytory" / "map_editor_prototyp.py"
    editor_terrain = {}
    
    if editor_path.exists():
        try:
            with open(editor_path, 'r', encoding='utf-8') as f:
                editor_content = f.read()
            
            # Wyciągnij TERRAIN_TYPES
            match = re.search(r'TERRAIN_TYPES = \{([^}]+)\}', editor_content, re.DOTALL)
            if match:
                types_str = match.group(1)
                for line in types_str.split('\n'):
                    if ':' in line and '{' in line:
                        terrain_name = line.split(':')[0].strip().strip('"\'')
                        # Wyciągnij move_mod
                        move_match = re.search(r'"move_mod":\s*(\d+)', line)
                        if move_match:
                            move_mod = int(move_match.group(1))
                            editor_terrain[terrain_name] = {"move_mod": move_mod}
        except Exception as e:
            print(f"⚠️ Błąd analizy edytora terenu: {e}")
    
    print(f"📋 Podręcznik ma {len(manual_terrain)} typów terenu")
    print(f"📋 Edytor ma {len(editor_terrain)} typów terenu")
    
    # Sprawdź czy edytor ma typy nieobecne w podręczniku
    for editor_type in editor_terrain:
        # Sprawdź czy jest podobny typ w podręczniku
        found_similar = False
        for manual_type in manual_terrain:
            if (editor_type.lower() in manual_type.lower() or 
                manual_type.lower() in editor_type.lower()):
                found_similar = True
                break
        
        if not found_similar:
            inconsistencies.append(f"Edytor ma nowy typ terenu: {editor_type}")
            print(f"❌ Edytor ma nowy typ terenu: {editor_type}")
    
    if not inconsistencies:
        print("✅ Typy terenu w większości zgodne")
    
    return inconsistencies

def check_support_system():
    """Sprawdza czy system wsparcia jest opisany w podręczniku"""
    
    print("\n🔍 SPRAWDZENIE SYSTEMU WSPARCIA:")
    print("-" * 40)
    
    manual_path = Path(__file__).parent.parent.parent / "PODRECZNIK_GRY_HUMAN.md"
    
    try:
        with open(manual_path, 'r', encoding='utf-8') as f:
            manual_content = f.read().lower()
    except FileNotFoundError:
        return ["manual_not_found"]
    
    missing_support = []
    
    # Lista wsparcia z edytorów
    support_types = [
        "drużyna granatników",
        "sekcja km.ppanc", 
        "sekcja ckm",
        "przodek dwukonny",
        "sam. ciężarowy fiat 621",
        "sam.ciężarowy praga rv",
        "ciągnik artyleryjski",
        "obserwator"
    ]
    
    for support in support_types:
        if support.lower() not in manual_content:
            missing_support.append(support)
            print(f"❌ Brak wsparcia w podręczniku: {support}")
    
    if not missing_support:
        print("✅ System wsparcia jest opisany")
    else:
        print(f"❌ Brakuje {len(missing_support)} typów wsparcia!")
        missing_support.append("system_wsparcia_missing")
    
    return missing_support

def main():
    """Główna funkcja testowa"""
    
    print("🔄 AUTOMATYCZNY TEST SPÓJNOŚCI PODRĘCZNIKA Z EDYTORAMI")
    print("=" * 70)
    print("Data testu:", "5 lipca 2025")
    print("=" * 70)
    
    # Uruchom test
    is_consistent = test_editor_compatibility()
    
    print("\n🎯 OSTATECZNY WYNIK:")
    print("=" * 30)
    
    if is_consistent:
        print("✅ PODRĘCZNIK JEST ZGODNY Z EDYTORAMI")
        print("✅ Można bezpiecznie używać edytorów")
        return 0
    else:
        print("❌ PODRĘCZNIK NIE JEST ZGODNY Z EDYTORAMI")
        print("🔄 WYMAGANA AKTUALIZACJA PODRĘCZNIKA")
        print("⚠️ Użycie edytorów może spowodować nieaktualność podręcznika")
        return 1

if __name__ == "__main__":
    exit(main())
