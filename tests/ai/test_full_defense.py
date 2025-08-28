#!/usr/bin/env python3
"""
Test pełnej strategii defensywnej AI Commander
Symuluje scenariusz bitwy z zagrożeniami i obroną
"""

import sys
from pathlib import Path

# Dodaj ścieżkę projektu do sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ai.ai_commander import (
    make_tactical_turn,
    get_my_units,
    assess_defensive_threats,
    plan_defensive_retreat,
    defensive_coordination
)


def create_battle_scenario():
    """Tworzy scenariusz bitwy z zagrożonymi jednostkami"""
    
    # Mock board z hex distance calculation
    class MockBoard:
        def __init__(self):
            self.tokens = []
            self.occupied_hexes = set()
        
        def is_occupied(self, q, r):
            return (q, r) in self.occupied_hexes
        
        def neighbors(self, q, r):
            return [
                (q + 1, r), (q - 1, r),
                (q, r + 1), (q, r - 1),
                (q + 1, r - 1), (q - 1, r + 1)
            ]
        
        def hex_distance(self, pos1, pos2):
            q1, r1 = pos1
            q2, r2 = pos2
            return max(abs(q1 - q2), abs(r1 - r2), abs((q1 + r1) - (q2 + r2)))
    
    # Mock player
    class MockPlayer:
        def __init__(self, nation, player_id):
            self.nation = nation
            self.id = player_id
    
    # Mock token z pełnymi danymi
    class MockToken:
        def __init__(self, token_id, owner, q, r, combat_value=5, mp=3, fuel=5):
            self.id = token_id
            self.owner = owner
            self.q = q
            self.r = r
            self.combat_value = combat_value
            self.currentFuel = fuel
            self.maxFuel = fuel
            self.stats = {
                'combat_value': combat_value,
                'move': mp,
                'maintenance': fuel,
                'label': token_id
            }
    
    # Utwórz engine
    engine = type('MockEngine', (), {})()
    engine.board = MockBoard()
    engine.current_player_obj = MockPlayer("Polska", 2)
    engine.tokens = []
    
    # Dane mapy
    engine.map_data = {
        'key_points': {
            '15,10': {'type': 'miasto', 'value': 100},
            '25,15': {'type': 'fortyfikacja', 'value': 150},
            '10,5': {'type': 'węzeł komunikacyjny', 'value': 75}
        },
        'spawn_points': {
            'Polska': ['5,5', '6,6', '12,8'],
            'Niemcy': ['30,20', '35,25', '40,30']
        }
    }
    
    # Scenariusz: Polskie jednostki pod presją niemieckich sił
    # Grupa 1: Główne siły polskie przy mieście
    polish_main = [
        MockToken("PL_Main_01", "2 (Polska)", 14, 11, 8, 3, 6),  # Blisko miasta
        MockToken("PL_Main_02", "2 (Polska)", 16, 9, 6, 3, 5),   # Wsparcie
        MockToken("PL_Main_03", "2 (Polska)", 13, 12, 7, 3, 4),  # Obrona flanki
    ]
    
    # Grupa 2: Straż przednia - zagrożone jednostki
    polish_forward = [
        MockToken("PL_Scout_01", "2 (Polska)", 20, 12, 4, 4, 3), # Bardzo zagrożony
        MockToken("PL_Scout_02", "2 (Polska)", 18, 14, 5, 3, 4), # Średnio zagrożony
    ]
    
    # Grupa 3: Rezerwa przy spawn point
    polish_reserve = [
        MockToken("PL_Reserve_01", "2 (Polska)", 8, 7, 6, 3, 5),
    ]
    
    # Niemieckie siły - główne zagrożenie
    german_main = [
        MockToken("DE_Panzer_01", "3 (Niemcy)", 22, 10, 12, 2, 8), # Groźny pancerny
        MockToken("DE_Panzer_02", "3 (Niemcy)", 24, 13, 10, 2, 7), # Drugi pancerny
        MockToken("DE_Infantry_01", "3 (Niemcy)", 21, 14, 8, 3, 5), # Wsparcie
    ]
    
    # Niemiecka grupa flanki
    german_flank = [
        MockToken("DE_Flank_01", "3 (Niemcy)", 26, 17, 6, 3, 4),
        MockToken("DE_Flank_02", "3 (Niemcy)", 28, 15, 7, 3, 5),
    ]
    
    all_tokens = polish_main + polish_forward + polish_reserve + german_main + german_flank
    engine.board.tokens = all_tokens
    engine.tokens = all_tokens
    
    # Zajmij hexagony
    for token in all_tokens:
        engine.board.occupied_hexes.add((token.q, token.r))
    
    return engine


def analyze_battle_situation(engine):
    """Analizuje sytuację na polu bitwy"""
    print("📊 ANALIZA SYTUACJI BOJOWEJ")
    print("=" * 50)
    
    # Polskie jednostki
    polish_units = []
    german_units = []
    
    for token in engine.board.tokens:
        if "Polska" in token.owner:
            polish_units.append(token)
        elif "Niemcy" in token.owner:
            german_units.append(token)
    
    print(f"🇵🇱 SIŁY POLSKIE: {len(polish_units)} jednostek")
    total_polish_combat = 0
    for unit in polish_units:
        print(f"  {unit.id}: pos({unit.q},{unit.r}) combat={unit.combat_value} fuel={unit.currentFuel}")
        total_polish_combat += unit.combat_value
    
    print(f"\n🇩🇪 SIŁY NIEMIECKIE: {len(german_units)} jednostek")
    total_german_combat = 0
    for unit in german_units:
        print(f"  {unit.id}: pos({unit.q},{unit.r}) combat={unit.combat_value}")
        total_german_combat += unit.combat_value
    
    print(f"\n⚔️ BILANS SIŁ:")
    print(f"  Polska: {total_polish_combat} punktów bojowych")
    print(f"  Niemcy: {total_german_combat} punktów bojowych")
    print(f"  Stosunek: 1:{total_german_combat/total_polish_combat:.2f} (na niekorzyść Polski)")
    print()


def test_defensive_strategy():
    """Test pełnej strategii defensywnej"""
    print("🛡️ TEST STRATEGII DEFENSYWNEJ AI COMMANDER")
    print("=" * 60)
    
    # Stwórz scenariusz
    engine = create_battle_scenario()
    
    # Analizuj sytuację
    analyze_battle_situation(engine)
    
    # Pobierz polskie jednostki w formacie AI
    my_units = []
    for token in engine.board.tokens:
        if "Polska" in token.owner:
            my_units.append({
                'id': token.id,
                'q': token.q,
                'r': token.r,
                'combat_value': token.combat_value,
                'mp': token.stats.get('move', 3),
                'fuel': token.currentFuel
            })
    
    print("🔍 FAZA 1: OCENA ZAGROŻEŃ")
    print("-" * 30)
    
    # Oceń zagrożenia
    threat_assessment = assess_defensive_threats(my_units, engine)
    
    high_threat_units = []
    medium_threat_units = []
    low_threat_units = []
    
    for unit_id, assessment in threat_assessment.items():
        threat_level = assessment['threat_level']
        enemy_count = len(assessment['threatening_enemies'])
        safe_point = assessment['nearest_safe_point']
        
        print(f"  {unit_id}:")
        print(f"    Zagrożenie: {threat_level}")
        print(f"    Wrogowie w pobliżu: {enemy_count}")
        print(f"    Najbliższy punkt bezpieczeństwa: {safe_point}")
        
        if threat_level > 10:
            high_threat_units.append(unit_id)
        elif threat_level > 5:
            medium_threat_units.append(unit_id)
        else:
            low_threat_units.append(unit_id)
    
    print(f"\n📈 PODSUMOWANIE ZAGROŻEŃ:")
    print(f"  🔴 Wysokie zagrożenie: {len(high_threat_units)} jednostek")
    print(f"  🟡 Średnie zagrożenie: {len(medium_threat_units)} jednostek")
    print(f"  🟢 Niskie zagrożenie: {len(low_threat_units)} jednostek")
    
    # Plan obrony
    print(f"\n🛡️ FAZA 2: PLANOWANIE OBRONY")
    print("-" * 30)
    
    threatened_units = [u for u in my_units if threat_assessment.get(u['id'], {}).get('threat_level', 0) > 5]
    
    if threatened_units:
        retreat_plan = plan_defensive_retreat(threatened_units, threat_assessment, engine)
        print(f"Plan odwrotu dla {len(threatened_units)} zagrożonych jednostek:")
        for unit_id, retreat_pos in retreat_plan.items():
            original_pos = next(u for u in my_units if u['id'] == unit_id)
            print(f"  {unit_id}: ({original_pos['q']},{original_pos['r']}) -> {retreat_pos}")
    
    # Koordynacja defensywna
    print(f"\n🏰 FAZA 3: KOORDYNACJA OBRONY")
    print("-" * 30)
    
    defensive_groups = defensive_coordination(my_units, threat_assessment, engine)
    
    for key_point, group in defensive_groups.items():
        point_data = engine.map_data['key_points'].get(f"{key_point[0]},{key_point[1]}", {})
        point_type = point_data.get('type', 'unknown')
        point_value = point_data.get('value', 0)
        
        print(f"  📍 {point_type.title()} {key_point} (wartość: {point_value}):")
        print(f"    Broni: {len(group)} jednostek")
        for unit in group:
            distance = abs(unit['q'] - key_point[0]) + abs(unit['r'] - key_point[1])
            print(f"      {unit['id']} (dystans: {distance})")
    
    print(f"\n💡 REKOMENDACJE STRATEGICZNE:")
    if len(high_threat_units) > 0:
        print(f"  🚨 NATYCHMIASTOWY ODWRÓT jednostek: {', '.join(high_threat_units)}")
    if len(medium_threat_units) > 0:
        print(f"  ⚠️ WZMOCNIJ OBRONĘ jednostek: {', '.join(medium_threat_units)}")
    if len(defensive_groups) > 0:
        print(f"  🏰 SKONCENTRUJ OBRONĘ wokół {len(defensive_groups)} punktów kluczowych")
    
    print(f"\n✅ Test strategii defensywnej zakończony pomyślnie!")


if __name__ == "__main__":
    test_defensive_strategy()
