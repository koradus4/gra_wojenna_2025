"""
DEMO: System graduowanej widoczności w grze
Pokazuje jak działa POZIOM 1 implementacji
"""
import sys
import os

# Dodaj do path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def demo_graduated_visibility():
    """Demonstracja systemu graduowanej widoczności"""
    print("🎮 DEMO: System graduowanej widoczności w grze")
    print("=" * 60)
    
    # Import prawdziwych modułów
    from engine.action_refactored_clean import VisionService
    from engine.detection_filter import apply_detection_filter
    
    # Symulacja scenariusza bojowego
    print("\n📍 SCENARIUSZ: Polski żołnierz obserwuje niemieckie jednostki")
    print("   Pozycja obserwatora: (5, 5)")
    print("   Zasięg wzroku: 4 heksy")
    print()
    
    # Mock token dla demonstracji
    class MockToken:
        def __init__(self, token_id, q, r, nation, unit_type, cv):
            self.id = token_id
            self.q = q
            self.r = r
            self.combat_value = cv
            self.stats = {
                'nation': nation,
                'type': unit_type
            }
    
    # Jednostki niemieckie na różnych odległościach
    enemy_units = [
        MockToken("GE_TANK_01", 6, 5, "Niemcy", "tank", 8),      # Odległość 1
        MockToken("GE_INF_01", 7, 6, "Niemcy", "infantry", 4),   # Odległość 2  
        MockToken("GE_ART_01", 8, 8, "Niemcy", "artillery", 6),  # Odległość 3
        MockToken("GE_REC_01", 9, 9, "Niemcy", "recon", 3),      # Odległość 4+
    ]
    
    observer_pos = (5, 5)
    sight_range = 4
    
    print("🔍 ANALIZA WIDOCZNOŚCI:")
    print()
    
    for enemy in enemy_units:
        enemy_pos = (enemy.q, enemy.r)
        
        # Oblicz odległość (hex distance)
        distance = max(abs(observer_pos[0] - enemy_pos[0]), 
                      abs(observer_pos[1] - enemy_pos[1]))
        
        # Oblicz detection level
        detection_level = VisionService.calculate_detection_level(distance, sight_range)
        
        # Zastosuj filtr
        filtered_info = apply_detection_filter(enemy, detection_level)
        
        # Wyświetl wyniki
        print(f"📡 {enemy.id} na pozycji {enemy_pos}")
        print(f"   📏 Odległość: {distance} heksów")
        print(f"   🎯 Detection level: {detection_level:.2f}")
        print(f"   ℹ️  Informacje gracza:")
        print(f"      ID: {filtered_info['id']}")
        print(f"      Combat Value: {filtered_info['combat_value']}")
        print(f"      Jakość info: {filtered_info['info_quality']}")
        
        # Interpretacja dla gracza
        if detection_level >= 0.8:
            print("      ✅ PEŁNA IDENTYFIKACJA - wszystkie szczegóły widoczne")
        elif detection_level >= 0.5:
            print("      ⚠️  CZĘŚCIOWA IDENTYFIKACJA - niektóre dane niepewne")
        else:
            print("      ❓ KONTAKT NIEOKREŚLONY - minimalne informacje")
        print()
    
    # Demonstracja wpływu na AI
    print("🤖 WPŁYW NA DECYZJE AI:")
    print()
    
    for enemy in enemy_units[:2]:  # Tylko pierwsze dwa
        enemy_pos = (enemy.q, enemy.r)
        distance = max(abs(observer_pos[0] - enemy_pos[0]), 
                      abs(observer_pos[1] - enemy_pos[1]))
        detection_level = VisionService.calculate_detection_level(distance, sight_range)
        filtered_info = apply_detection_filter(enemy, detection_level)
        
        cv_info = filtered_info['combat_value']
        
        print(f"🎯 Cel: {filtered_info['id']}")
        if isinstance(cv_info, int):
            print(f"   AI wie dokładnie: CV = {cv_info}")
            print(f"   Decyzja: {'Atakuj' if cv_info < 6 else 'Ostrożnie'}")
        elif isinstance(cv_info, str) and '~' in cv_info:
            print(f"   AI szacuje: CV = {cv_info}")
            print(f"   Decyzja: Użyj konserwatywnych założeń")
        else:
            print(f"   AI nie wie: CV = {cv_info}")
            print(f"   Decyzja: Unikaj lub rozpoznawaj")
        print()
    
    print("✅ DEMO ZAKOŃCZONE")
    print("   System graduowanej widoczności POZIOM 1 działa poprawnie!")

if __name__ == "__main__":
    demo_graduated_visibility()
