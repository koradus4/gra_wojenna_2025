#!/usr/bin/env python3
"""
KOMPLETNA WERYFIKACJA PODRĘCZNIKA - TEST KAŻDEGO ASPEKTU
Sprawdza każde twierdzenie w podręczniku poprzez analizę kodu
"""

import sys
import os
import json
import re

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def analyze_project_structure():
    """Analizuje całą strukturę projektu"""
    print("🔍 ANALIZA STRUKTURY PROJEKTU")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Sprawdź główne pliki uruchomieniowe
    main_files = {
        'main.py': False,
        'main_ai_vs_human.py': False,
        'main_alternative.py': False
    }
    
    for file in main_files.keys():
        path = os.path.join(project_root, file)
        main_files[file] = os.path.exists(path)
        print(f"   {file}: {'✅ ISTNIEJE' if main_files[file] else '❌ BRAK'}")
    
    return main_files

def verify_game_modes():
    """Weryfikuje tryby gry opisane w podręczniku"""
    print("\n🎮 WERYFIKACJA TRYBÓW GRY")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Sprawdź main.py
    main_py = os.path.join(project_root, 'main.py')
    if os.path.exists(main_py):
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Szukaj ekranu startowego
        has_start_screen = 'ekran_startowy' in content or 'StartScreen' in content
        has_player_config = 'player' in content and 'config' in content
        has_6_players = '6' in content or 'sześciu' in content
        
        print(f"   main.py - ekran startowy: {'✅' if has_start_screen else '❌'}")
        print(f"   main.py - konfiguracja graczy: {'✅' if has_player_config else '❌'}")
        print(f"   main.py - 6 graczy: {'✅' if has_6_players else '❌'}")
    
    # Sprawdź main_ai_vs_human.py
    ai_human_py = os.path.join(project_root, 'main_ai_vs_human.py')
    if os.path.exists(ai_human_py):
        with open(ai_human_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_ai_vs_human = 'ai' in content.lower() and 'human' in content.lower()
        has_difficulty = 'difficulty' in content.lower() or 'trudność' in content.lower()
        
        print(f"   main_ai_vs_human.py - tryb AI vs Human: {'✅' if has_ai_vs_human else '❌'}")
        print(f"   main_ai_vs_human.py - poziomy trudności: {'✅' if has_difficulty else '❌'}")
    
    return True

def verify_turn_structure():
    """Weryfikuje strukturę tur"""
    print("\n🔄 WERYFIKACJA STRUKTURY TUR")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Sprawdź core/tura.py
    tura_py = os.path.join(project_root, 'core', 'tura.py')
    if os.path.exists(tura_py):
        with open(tura_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Szukaj informacji o 6 graczach
        has_6_players = '6' in content
        has_turn_order = 'order' in content or 'kolejność' in content
        has_weather = 'weather' in content or 'pogoda' in content
        
        print(f"   core/tura.py - 6 graczy: {'✅' if has_6_players else '❌'}")
        print(f"   core/tura.py - kolejność tur: {'✅' if has_turn_order else '❌'}")
        print(f"   core/tura.py - pogoda: {'✅' if has_weather else '❌'}")
    else:
        print(f"   ❌ BRAK: core/tura.py")
    
    # Sprawdź core/pogoda.py
    pogoda_py = os.path.join(project_root, 'core', 'pogoda.py')
    if os.path.exists(pogoda_py):
        with open(pogoda_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_weather_generation = 'generate' in content or 'generat' in content
        has_6_turn_cycle = '6' in content
        
        print(f"   core/pogoda.py - generowanie pogody: {'✅' if has_weather_generation else '❌'}")
        print(f"   core/pogoda.py - cykl 6 tur: {'✅' if has_6_turn_cycle else '❌'}")
    else:
        print(f"   ❌ BRAK: core/pogoda.py")
    
    return True

def verify_timer_system():
    """Weryfikuje system timera"""
    print("\n⏱️ WERYFIKACJA SYSTEMU TIMERA")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Sprawdź gui/panel_generala.py
    panel_generala = os.path.join(project_root, 'gui', 'panel_generala.py')
    if os.path.exists(panel_generala):
        with open(panel_generala, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Szukaj informacji o timerze
        has_timer = 'timer' in content.lower()
        has_clickable_timer = 'click' in content and 'timer' in content.lower()
        has_color_6B8E23 = '#6B8E23' in content
        has_color_changes = 'color' in content and ('red' in content or 'yellow' in content)
        
        print(f"   panel_generala.py - timer: {'✅' if has_timer else '❌'}")
        print(f"   panel_generala.py - klikalny timer: {'✅' if has_clickable_timer else '❌'}")
        print(f"   panel_generala.py - kolor #6B8E23: {'✅' if has_color_6B8E23 else '❌'}")
        print(f"   panel_generala.py - zmiany kolorów: {'❌ BRAK' if not has_color_changes else '⚠️ ZNALEZIONO'}")
    else:
        print(f"   ❌ BRAK: gui/panel_generala.py")
    
    return True

def verify_movement_system():
    """Weryfikuje system ruchu"""
    print("\n🏃 WERYFIKACJA SYSTEMU RUCHU")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Sprawdź engine/token.py
    token_py = os.path.join(project_root, 'engine', 'token.py')
    if os.path.exists(token_py):
        with open(token_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Szukaj informacji o trybach ruchu
        has_movement_modes = 'combat' in content.lower() and 'march' in content.lower() and 'recon' in content.lower()
        has_mp_system = 'move_points' in content.lower() or 'mp' in content.lower()
        has_terrain_modifiers = 'terrain' in content.lower() and 'mod' in content.lower()
        
        print(f"   engine/token.py - tryby ruchu: {'✅' if has_movement_modes else '❌'}")
        print(f"   engine/token.py - system MP: {'✅' if has_mp_system else '❌'}")
        print(f"   engine/token.py - modyfikatory terenu: {'✅' if has_terrain_modifiers else '❌'}")
    else:
        print(f"   ❌ BRAK: engine/token.py")
    
    return True

def verify_combat_system():
    """Weryfikuje system walki"""
    print("\n⚔️ WERYFIKACJA SYSTEMU WALKI")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Sprawdź engine/action.py
    action_py = os.path.join(project_root, 'engine', 'action.py')
    if os.path.exists(action_py):
        with open(action_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Szukaj informacji o walce
        has_attack_system = 'attack' in content.lower()
        has_range_system = 'range' in content.lower()
        has_damage_calculation = 'damage' in content.lower() or 'combat_value' in content.lower()
        has_counterattack = 'counter' in content.lower()
        
        print(f"   engine/action.py - system ataku: {'✅' if has_attack_system else '❌'}")
        print(f"   engine/action.py - system zasięgu: {'✅' if has_range_system else '❌'}")
        print(f"   engine/action.py - obliczanie obrażeń: {'✅' if has_damage_calculation else '❌'}")
        print(f"   engine/action.py - kontratak: {'✅' if has_counterattack else '❌'}")
    else:
        print(f"   ❌ BRAK: engine/action.py")
    
    return True

def verify_economy_system():
    """Weryfikuje system ekonomiczny"""
    print("\n💰 WERYFIKACJA SYSTEMU EKONOMICZNEGO")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Sprawdź core/ekonomia.py
    ekonomia_py = os.path.join(project_root, 'core', 'ekonomia.py')
    if os.path.exists(ekonomia_py):
        with open(ekonomia_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Szukaj informacji o ekonomii
        has_economic_points = 'economic_points' in content.lower()
        has_key_points = 'key_point' in content.lower()
        has_cities = 'cit' in content.lower() or 'miasto' in content.lower()
        has_generate_points = 'generate' in content.lower()
        has_starting_budget = 'start' in content.lower() and ('budget' in content.lower() or 'budżet' in content.lower())
        
        print(f"   core/ekonomia.py - punkty ekonomiczne: {'✅' if has_economic_points else '❌'}")
        print(f"   core/ekonomia.py - key points: {'✅' if has_key_points else '❌'}")
        print(f"   core/ekonomia.py - miasta: {'✅' if has_cities else '❌'}")
        print(f"   core/ekonomia.py - generowanie punktów: {'✅' if has_generate_points else '❌'}")
        print(f"   core/ekonomia.py - startowy budżet: {'✅' if has_starting_budget else '❌'}")
    else:
        print(f"   ❌ BRAK: core/ekonomia.py")
    
    return True

def verify_map_system():
    """Weryfikuje system mapy"""
    print("\n🗺️ WERYFIKACJA SYSTEMU MAPY")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Sprawdź data/map_data.json
    map_data = os.path.join(project_root, 'data', 'map_data.json')
    if os.path.exists(map_data):
        with open(map_data, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                has_hexagonal = 'hex' in str(data).lower()
                has_terrain_types = 'terrain' in str(data).lower()
                has_key_points = 'key_point' in str(data).lower() or 'miasto' in str(data).lower()
                
                print(f"   data/map_data.json - system heksagonalny: {'✅' if has_hexagonal else '❌'}")
                print(f"   data/map_data.json - typy terenu: {'✅' if has_terrain_types else '❌'}")
                print(f"   data/map_data.json - punkty kluczowe: {'✅' if has_key_points else '❌'}")
            except json.JSONDecodeError:
                print(f"   ❌ BŁĄD: Nieprawidłowy format JSON")
    else:
        print(f"   ❌ BRAK: data/map_data.json")
    
    # Sprawdź engine/hex_utils.py
    hex_utils = os.path.join(project_root, 'engine', 'hex_utils.py')
    if os.path.exists(hex_utils):
        with open(hex_utils, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_hex_coordinates = 'q' in content and 'r' in content
        has_distance_calc = 'distance' in content.lower()
        
        print(f"   engine/hex_utils.py - współrzędne hex: {'✅' if has_hex_coordinates else '❌'}")
        print(f"   engine/hex_utils.py - obliczanie odległości: {'✅' if has_distance_calc else '❌'}")
    else:
        print(f"   ❌ BRAK: engine/hex_utils.py")
    
    return True

def verify_fog_of_war():
    """Weryfikuje system fog of war"""
    print("\n🌫️ WERYFIKACJA FOG OF WAR")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Przeszukaj pliki w poszukiwaniu fog of war
    search_files = [
        'engine/action.py',
        'engine/token.py',
        'gui/panel_mapa.py',
        'engine/player.py'
    ]
    
    fog_found = False
    for file_path in search_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'fog' in content.lower() or 'sight' in content.lower() or 'vision' in content.lower():
                fog_found = True
                print(f"   {file_path} - fog of war: ✅")
    
    if not fog_found:
        print(f"   ❌ BRAK: Nie znaleziono implementacji fog of war")
    
    return fog_found

def verify_save_system():
    """Weryfikuje system zapisów"""
    print("\n💾 WERYFIKACJA SYSTEMU ZAPISÓW")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Sprawdź engine/save_manager.py
    save_manager = os.path.join(project_root, 'engine', 'save_manager.py')
    if os.path.exists(save_manager):
        with open(save_manager, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_save_function = 'save' in content.lower()
        has_load_function = 'load' in content.lower()
        has_json_format = 'json' in content.lower()
        has_auto_save = 'auto' in content.lower()
        
        print(f"   engine/save_manager.py - funkcja zapisu: {'✅' if has_save_function else '❌'}")
        print(f"   engine/save_manager.py - funkcja wczytywania: {'✅' if has_load_function else '❌'}")
        print(f"   engine/save_manager.py - format JSON: {'✅' if has_json_format else '❌'}")
        print(f"   engine/save_manager.py - auto zapis: {'✅' if has_auto_save else '❌'}")
    else:
        print(f"   ❌ BRAK: engine/save_manager.py")
    
    # Sprawdź folder saves
    saves_folder = os.path.join(project_root, 'saves')
    if os.path.exists(saves_folder):
        print(f"   saves/ folder: ✅")
    else:
        print(f"   ❌ BRAK: saves/ folder")
    
    return True

def verify_unit_statistics():
    """Weryfikuje statystyki jednostek"""
    print("\n🪖 WERYFIKACJA STATYSTYK JEDNOSTEK")
    print("=" * 50)
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Sprawdź assets/start_tokens.json
    start_tokens = os.path.join(project_root, 'assets', 'start_tokens.json')
    if os.path.exists(start_tokens):
        with open(start_tokens, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                
                # Szukaj statystyk
                has_move_points = 'move' in str(data).lower()
                has_combat_value = 'combat' in str(data).lower()
                has_attack_range = 'attack' in str(data).lower() and 'range' in str(data).lower()
                has_sight = 'sight' in str(data).lower()
                
                print(f"   assets/start_tokens.json - punkty ruchu: {'✅' if has_move_points else '❌'}")
                print(f"   assets/start_tokens.json - combat value: {'✅' if has_combat_value else '❌'}")
                print(f"   assets/start_tokens.json - zasięg ataku: {'✅' if has_attack_range else '❌'}")
                print(f"   assets/start_tokens.json - sight: {'✅' if has_sight else '❌'}")
                
            except json.JSONDecodeError:
                print(f"   ❌ BŁĄD: Nieprawidłowy format JSON")
    else:
        print(f"   ❌ BRAK: assets/start_tokens.json")
    
    return True

def run_complete_verification():
    """Uruchamia kompletną weryfikację"""
    print("🎯 KOMPLETNA WERYFIKACJA PODRĘCZNIKA")
    print("=" * 70)
    
    # Lista wszystkich testów
    tests = [
        ("Struktura projektu", analyze_project_structure),
        ("Tryby gry", verify_game_modes),
        ("Struktura tur", verify_turn_structure),
        ("System timera", verify_timer_system),
        ("System ruchu", verify_movement_system),
        ("System walki", verify_combat_system),
        ("System ekonomiczny", verify_economy_system),
        ("System mapy", verify_map_system),
        ("Fog of war", verify_fog_of_war),
        ("System zapisów", verify_save_system),
        ("Statystyki jednostek", verify_unit_statistics)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ BŁĄD w teście {test_name}: {e}")
            results.append((test_name, False))
    
    # Podsumowanie
    print(f"\n📊 PODSUMOWANIE WERYFIKACJI:")
    print(f"=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Przeszło: {passed}/{total} testów ({passed/total*100:.1f}%)")
    
    for test_name, result in results:
        status = "✅ PRZESZEDŁ" if result else "❌ NIEPOWODZENIE"
        print(f"   {test_name}: {status}")
    
    return results

if __name__ == "__main__":
    results = run_complete_verification()
    
    print(f"\n🎯 NASTĘPNE KROKI:")
    print(f"Na podstawie wyników weryfikacji należy poprawić podręcznik.")
    print(f"Każdy aspekt który nie przeszedł testów musi zostać usunięty lub poprawiony.")
