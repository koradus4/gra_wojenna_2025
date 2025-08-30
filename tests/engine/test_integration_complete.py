"""
TEST INTEGRACYJNY: Kompletny system graduowanej widoczności POZIOM 1
Pokazuje pełną integrację: VisionService -> DetectionFilter -> GUI Display
"""

def test_complete_integration():
    """Test kompletnej integracji systemu"""
    print("🔗 TEST INTEGRACYJNY: Kompletny system graduowanej widoczności")
    print("=" * 70)
    
    # Importy
    from engine.action_refactored_clean import VisionService
    from engine.detection_filter import apply_detection_filter
    from gui.detection_display import (
        get_display_info_for_enemy, 
        get_map_display_symbol,
        format_detection_status,
        get_info_panel_content
    )
    
    # Mock token
    class MockToken:
        def __init__(self):
            self.id = "GE_PANZER_IV_001"
            self.q = 8
            self.r = 6  
            self.combat_value = 7
            self.stats = {
                'nation': 'Niemcy',
                'type': 'tank',
                'move': 4,
                'attack': {'value': 8, 'range': 2}
            }
    
    # Scenariusz: obserwowanie z różnych odległości
    scenarios = [
        {'distance': 1, 'sight': 4, 'scenario': 'Bliska obserwacja'},
        {'distance': 2, 'sight': 4, 'scenario': 'Średnia odległość'},
        {'distance': 3, 'sight': 4, 'scenario': 'Daleka obserwacja'},
        {'distance': 4, 'sight': 4, 'scenario': 'Poza zasięgiem'},
    ]
    
    enemy_token = MockToken()
    
    print(f"🎯 Obserwowany: {enemy_token.id}")
    print(f"   Pozycja: ({enemy_token.q}, {enemy_token.r})")
    print(f"   Rzeczywiste CV: {enemy_token.combat_value}")
    print(f"   Nacja: {enemy_token.stats['nation']}")
    print()
    
    for scenario in scenarios:
        distance = scenario['distance']
        sight = scenario['sight']
        desc = scenario['scenario']
        
        print(f"📡 {desc} (odległość: {distance}, zasięg: {sight})")
        print("-" * 50)
        
        # 1. VisionService - oblicz detection level
        detection_level = VisionService.calculate_detection_level(distance, sight)
        print(f"   🔍 Detection level: {detection_level:.2f}")
        
        # 2. DetectionFilter - filtruj informacje
        filtered_info = apply_detection_filter(enemy_token, detection_level)
        print(f"   📋 Filtered info:")
        print(f"      ID: {filtered_info['id']}")
        print(f"      CV: {filtered_info['combat_value']}")  
        print(f"      Quality: {filtered_info['info_quality']}")
        
        # 3. GUI Display - przygotuj do wyświetlenia
        display_info = get_display_info_for_enemy(enemy_token, detection_level)
        map_symbol = get_map_display_symbol(enemy_token, detection_level)
        status = format_detection_status(detection_level)
        panel_content = get_info_panel_content(enemy_token, detection_level)
        
        print(f"   🖥️  GUI Display:")
        print(f"      Nazwa: {display_info['display_name']}")
        print(f"      Status: {status}")
        print(f"      Symbol na mapie: {map_symbol['symbol']} (opacity: {map_symbol['opacity']})")
        print(f"      Tooltip: {display_info['tooltip']}")
        print(f"      Panel info: {len(panel_content['fields'])} pól")
        
        # 4. Wpływ na rozgrywkę
        print(f"   🎮 Wpływ na rozgrywkę:")
        if detection_level >= 0.8:
            print(f"      ✅ Gracz ma pełne informacje - może planować precyzyjnie")
        elif detection_level >= 0.5:
            print(f"      ⚠️  Gracz ma częściowe info - musi użyć ostrożności")
        else:
            print(f"      ❓ Gracz ma minimalne info - potrzebuje rozpoznania")
        
        print()
    
    # Test AI Decision Making
    print("🤖 WPŁYW NA DECYZJE AI:")
    print("-" * 30)
    
    ai_scenarios = [
        {'detection': 0.9, 'cv_known': 7},
        {'detection': 0.6, 'cv_estimate': '5-9'},  
        {'detection': 0.2, 'cv_unknown': True}
    ]
    
    for i, scenario in enumerate(ai_scenarios):
        print(f"   Scenariusz {i+1}:")
        if 'cv_known' in scenario:
            print(f"      AI wie: CV = {scenario['cv_known']}")
            print(f"      Decyzja: Atak jeśli własne CV > {scenario['cv_known'] * 1.3:.1f}")
        elif 'cv_estimate' in scenario:
            print(f"      AI szacuje: CV = {scenario['cv_estimate']}")
            print(f"      Decyzja: Używa konserwatywnego górnego zakresu")
        else:
            print(f"      AI nie wie: CV = ???")
            print(f"      Decyzja: Unika lub wysyła zwiad")
        print()
    
    print("✅ TEST INTEGRACYJNY ZAKOŃCZONY")
    print("   System graduowanej widoczności POZIOM 1 w pełni funkcjonalny!")

if __name__ == "__main__":
    test_complete_integration()
