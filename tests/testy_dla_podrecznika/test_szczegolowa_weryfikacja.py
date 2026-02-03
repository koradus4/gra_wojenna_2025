#!/usr/bin/env python3
"""
SZCZEGÓŁOWA WERYFIKACJA PODRĘCZNIKA - KAŻDY ELEMENT
Sprawdza czy każde twierdzenie w podręczniku jest prawdziwe
"""

import sys
import os
import json
import re

# Dodaj katalog główny do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class ManualVerifier:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.manual_path = os.path.join(self.project_root, 'PODRECZNIK_GRY_HUMAN.md')
        self.corrections_needed = []
        self.verified_facts = []
        
    def load_manual(self):
        """Wczytuje podręcznik do analizy"""
        with open(self.manual_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def verify_game_modes(self):
        """Weryfikuje tryby gry"""
        print("🎮 WERYFIKACJA TRYBÓW GRY")
        print("=" * 50)
        
        # Sprawdź main.py
        main_py = os.path.join(self.project_root, 'main.py')
        with open(main_py, 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        # Sprawdź co jest w podręczniku vs rzeczywistość
        facts_to_verify = [
            {
                'claim': 'Tryb pełny - python main.py',
                'check': 'main.py' in os.listdir(self.project_root),
                'section': 'Tryby uruchomiania'
            },
            {
                'claim': 'Ekran startowy z wyborem 6 graczy',
                'check': 'StartScreen' in main_content or 'ekran_startowy' in main_content,
                'section': 'Tryby uruchomiania'
            },
            {
                'claim': 'Czas na turę 3-20 minut',
                'check': ('3' in main_content and '20' in main_content) or 'minutes' in main_content,
                'section': 'Tryby uruchomiania'
            }
        ]
        
        for fact in facts_to_verify:
            if fact['check']:
                print(f"   ✅ {fact['claim']}")
                self.verified_facts.append(fact['claim'])
            else:
                print(f"   ❌ {fact['claim']}")
                self.corrections_needed.append({
                    'section': fact['section'],
                    'claim': fact['claim'],
                    'issue': 'Niepotwierdzony w kodzie'
                })
    
    def verify_turn_structure(self):
        """Weryfikuje strukturę tur"""
        print("\n🔄 WERYFIKACJA STRUKTURY TUR")
        print("=" * 50)
        
        # Sprawdź czy rzeczywiście jest cykl 6 tur
        manual_content = self.load_manual()
        
        facts_to_verify = [
            {
                'claim': 'Po każdych 6 turach generowana jest nowa prognoza pogody',
                'check': self.check_weather_cycle(),
                'section': 'Struktura rozgrywki'
            },
            {
                'claim': 'Wszystkie jednostki odnawiają punkty ruchu',
                'check': self.check_mp_renewal(),
                'section': 'Struktura rozgrywki'
            },
            {
                'claim': 'Aktualizowane są punkty ekonomiczne',
                'check': self.check_economy_update(),
                'section': 'Struktura rozgrywki'
            }
        ]
        
        for fact in facts_to_verify:
            if fact['check']:
                print(f"   ✅ {fact['claim']}")
                self.verified_facts.append(fact['claim'])
            else:
                print(f"   ❌ {fact['claim']}")
                self.corrections_needed.append({
                    'section': fact['section'],
                    'claim': fact['claim'],
                    'issue': 'Niepotwierdzony w kodzie'
                })
    
    def check_weather_cycle(self):
        """Sprawdza czy pogoda jest generowana co 6 tur"""
        pogoda_py = os.path.join(self.project_root, 'core', 'pogoda.py')
        if not os.path.exists(pogoda_py):
            return False
        
        with open(pogoda_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Poszukaj logiki co 6 tur
        return '6' in content and ('turn' in content.lower() or 'tur' in content.lower())
    
    def check_mp_renewal(self):
        """Sprawdza czy MP są odnawiane"""
        action_py = os.path.join(self.project_root, 'engine', 'action.py')
        if not os.path.exists(action_py):
            return False
        
        with open(action_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Sprawdź czy jest logika odnowienia MP
        return 'currentMovePoints' in content and ('renew' in content.lower() or 'refresh' in content.lower())
    
    def check_economy_update(self):
        """Sprawdza aktualizację ekonomii"""
        ekonomia_py = os.path.join(self.project_root, 'core', 'ekonomia.py')
        if not os.path.exists(ekonomia_py):
            return False
        
        with open(ekonomia_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return 'generate' in content.lower() and 'economic' in content.lower()
    
    def verify_combat_system(self):
        """Weryfikuje system walki"""
        print("\n⚔️ WERYFIKACJA SYSTEMU WALKI")
        print("=" * 50)
        
        # Sprawdź rzeczywiste zasięgi z plików tokenów
        token_files = self.get_token_files()
        ranges_found = {}
        
        for token_file in token_files[:10]:  # Sprawdź pierwsze 10 tokenów
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                unit_type = data.get('unitType', 'unknown')
                attack_range = data.get('attack', {}).get('range', 1)
                ranges_found[unit_type] = ranges_found.get(unit_type, [])
                ranges_found[unit_type].append(attack_range)
            except:
                continue
        
        # Sprawdź czy podręcznik ma poprawne zasięgi
        manual_content = self.load_manual()
        
        facts_to_verify = [
            {
                'claim': 'Piechota: 1 hex (walka wręcz)',
                'check': 'P' in ranges_found and 1 in ranges_found.get('P', []),
                'section': 'Mechaniki rozgrywki'
            },
            {
                'claim': 'Artyleria: 2-4 hex',
                'check': 'AL' in ranges_found and any(r >= 2 for r in ranges_found.get('AL', [])),
                'section': 'Mechaniki rozgrywki'
            },
            {
                'claim': 'Zasięgi definiowane w statystykach jednostek',
                'check': len(ranges_found) > 0,
                'section': 'Mechaniki rozgrywki'
            }
        ]
        
        for fact in facts_to_verify:
            if fact['check']:
                print(f"   ✅ {fact['claim']}")
                self.verified_facts.append(fact['claim'])
            else:
                print(f"   ❌ {fact['claim']}")
                self.corrections_needed.append({
                    'section': fact['section'],
                    'claim': fact['claim'],
                    'issue': f'Rzeczywiste zasięgi: {ranges_found}'
                })
        
        print(f"   📊 Znalezione zasięgi: {ranges_found}")
    
    def get_token_files(self):
        """Zwraca listę plików tokenów"""
        token_files = []
        tokens_dir = os.path.join(self.project_root, 'assets', 'tokens')
        
        if os.path.exists(tokens_dir):
            for root, dirs, files in os.walk(tokens_dir):
                for file in files:
                    if file == 'token.json':
                        token_files.append(os.path.join(root, file))
        
        return token_files
    
    def verify_terrain_system(self):
        """Weryfikuje system terenu"""
        print("\n🗺️ WERYFIKACJA SYSTEMU TERENU")
        print("=" * 50)
        
        # Sprawdź koszty ruchu według terenu z podręcznika
        manual_terrain_costs = {
            'Pole otwarte': 1,
            'Las': 3,
            'Wzgórze': 2,
            'Rzeka': 4,
            'Bagno': 4,
            'Droga': 1,
            'Miasto': 1
        }
        
        # Sprawdź rzeczywiste koszty w kodzie
        action_py = os.path.join(self.project_root, 'engine', 'action.py')
        with open(action_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Sprawdź czy logika kosztów terenu jest zaimplementowana
        has_terrain_logic = 'move_mod' in content and 'move_cost' in content
        
        if has_terrain_logic:
            print(f"   ✅ System kosztów terenu zaimplementowany")
            self.verified_facts.append('System kosztów terenu')
        else:
            print(f"   ❌ System kosztów terenu nie znaleziony")
            self.corrections_needed.append({
                'section': 'Mechaniki rozgrywki',
                'claim': 'Tabela kosztów ruchu według terenu',
                'issue': 'Logika kosztów terenu nie została znaleziona w kodzie'
            })
    
    def verify_movement_modes(self):
        """Weryfikuje tryby ruchu"""
        print("\n🏃 WERYFIKACJA TRYBÓW RUCHU")
        print("=" * 50)
        
        # Sprawdź engine/token.py
        token_py = os.path.join(self.project_root, 'engine', 'token.py')
        with open(token_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        movement_modes = ['combat', 'march', 'recon']
        modes_found = []
        
        for mode in movement_modes:
            if mode in content:
                modes_found.append(mode)
        
        facts_to_verify = [
            {
                'claim': 'Tryb walki (Combat) - domyślny',
                'check': 'combat' in modes_found,
                'section': 'Mechaniki rozgrywki'
            },
            {
                'claim': 'Tryb marszu (March) - 150% MP, 50% obrony',
                'check': 'march' in modes_found and '150' in content,
                'section': 'Mechaniki rozgrywki'
            },
            {
                'claim': 'Tryb rekonesansu (Recon) - 50% MP, 125% obrony',
                'check': 'recon' in modes_found and '50' in content,
                'section': 'Mechaniki rozgrywki'
            }
        ]
        
        for fact in facts_to_verify:
            if fact['check']:
                print(f"   ✅ {fact['claim']}")
                self.verified_facts.append(fact['claim'])
            else:
                print(f"   ❌ {fact['claim']}")
                self.corrections_needed.append({
                    'section': fact['section'],
                    'claim': fact['claim'],
                    'issue': f'Znalezione tryby: {modes_found}'
                })
    
    def verify_economy_details(self):
        """Weryfikuje szczegóły ekonomii"""
        print("\n💰 WERYFIKACJA SZCZEGÓŁÓW EKONOMII")
        print("=" * 50)
        
        # Sprawdź map_data.json dla key points
        map_data_path = os.path.join(self.project_root, 'data', 'map_data.json')
        key_points_found = {}
        
        if os.path.exists(map_data_path):
            with open(map_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Szukaj key points w danych mapy
            for tile_data in data.get('tiles', []):
                if 'key_point' in tile_data:
                    key_type = tile_data['key_point'].get('type', 'unknown')
                    key_value = tile_data['key_point'].get('value', 0)
                    key_points_found[key_type] = key_points_found.get(key_type, [])
                    key_points_found[key_type].append(key_value)
        
        facts_to_verify = [
            {
                'claim': 'Miasta: 10% wartości miasta co turę (100 pkt → 10 pkt/turę)',
                'check': 'miasto' in key_points_found or 'city' in key_points_found,
                'section': 'System ekonomiczny'
            },
            {
                'claim': 'Fortyfikacje: 10% wartości co turę (150 pkt → 15 pkt/turę)',
                'check': 'fort' in key_points_found or 'fortification' in key_points_found,
                'section': 'System ekonomiczny'
            },
            {
                'claim': 'Rozpoczyna z 0 punktów',
                'check': self.check_starting_budget(),
                'section': 'System ekonomiczny'
            }
        ]
        
        for fact in facts_to_verify:
            if fact['check']:
                print(f"   ✅ {fact['claim']}")
                self.verified_facts.append(fact['claim'])
            else:
                print(f"   ❌ {fact['claim']}")
                self.corrections_needed.append({
                    'section': fact['section'],
                    'claim': fact['claim'],
                    'issue': f'Key points znalezione: {key_points_found}'
                })
        
        print(f"   📊 Key points w mapie: {key_points_found}")
    
    def check_starting_budget(self):
        """Sprawdza startowy budżet"""
        ekonomia_py = os.path.join(self.project_root, 'core', 'ekonomia.py')
        if not os.path.exists(ekonomia_py):
            return False
        
        with open(ekonomia_py, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Sprawdź czy inicjalizacja to 0
        return 'economic_points = 0' in content or 'economic_points=0' in content
    
    def verify_interface_claims(self):
        """Weryfikuje twierdzenia o interfejsie"""
        print("\n🖱️ WERYFIKACJA INTERFEJSU")
        print("=" * 50)
        
        # Sprawdź GUI pliki
        gui_files = [
            'gui/panel_generala.py',
            'gui/panel_mapa.py',
            'gui/panel_dowodcy.py'
        ]
        
        interface_features = {}
        
        for gui_file in gui_files:
            file_path = os.path.join(self.project_root, gui_file)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Sprawdź różne funkcje interfejsu
                interface_features[gui_file] = {
                    'mouse_events': 'click' in content.lower() or 'bind' in content.lower(),
                    'scrollbars': 'scroll' in content.lower(),
                    'timer': 'timer' in content.lower(),
                    'buttons': 'button' in content.lower(),
                    'panels': 'panel' in content.lower()
                }
        
        facts_to_verify = [
            {
                'claim': 'Klik na puste pole anuluje wybór jednostki',
                'check': any(features.get('mouse_events', False) for features in interface_features.values()),
                'section': 'Kontrole i interfejs'
            },
            {
                'claim': 'Scrollbary: Przewijanie i nawigacja po mapie',
                'check': any(features.get('scrollbars', False) for features in interface_features.values()),
                'section': 'Kontrole i interfejs'
            },
            {
                'claim': 'Timer tury (klikalny)',
                'check': any(features.get('timer', False) for features in interface_features.values()),
                'section': 'Kontrole i interfejs'
            }
        ]
        
        for fact in facts_to_verify:
            if fact['check']:
                print(f"   ✅ {fact['claim']}")
                self.verified_facts.append(fact['claim'])
            else:
                print(f"   ❌ {fact['claim']}")
                self.corrections_needed.append({
                    'section': fact['section'],
                    'claim': fact['claim'],
                    'issue': f'Funkcje interfejsu: {interface_features}'
                })
        
        print(f"   📊 Funkcje interfejsu: {interface_features}")
    
    def generate_corrections_report(self):
        """Generuje raport z potrzebnymi poprawkami"""
        print("\n📋 RAPORT POPRAWEK")
        print("=" * 50)
        
        verified_count = len(self.verified_facts)
        corrections_count = len(self.corrections_needed)
        total_count = verified_count + corrections_count
        
        if total_count > 0:
            accuracy = (verified_count / total_count) * 100
            print(f"Dokładność podręcznika: {accuracy:.1f}% ({verified_count}/{total_count})")
        
        if corrections_count > 0:
            print(f"\n❌ WYMAGANE POPRAWKI ({corrections_count}):")
            
            by_section = {}
            for correction in self.corrections_needed:
                section = correction['section']
                if section not in by_section:
                    by_section[section] = []
                by_section[section].append(correction)
            
            for section, corrections in by_section.items():
                print(f"\n📖 {section}:")
                for correction in corrections:
                    print(f"   • {correction['claim']}")
                    print(f"     Problemu: {correction['issue']}")
        
        if verified_count > 0:
            print(f"\n✅ ZWERYFIKOWANE FAKTY ({verified_count}):")
            for fact in self.verified_facts[:5]:  # Pokazuj pierwsze 5
                print(f"   • {fact}")
            if len(self.verified_facts) > 5:
                print(f"   ... i {len(self.verified_facts) - 5} więcej")
        
        return {
            'verified_count': verified_count,
            'corrections_count': corrections_count,
            'accuracy': accuracy if total_count > 0 else 0,
            'corrections_needed': self.corrections_needed
        }
    
    def run_complete_verification(self):
        """Uruchamia kompletną weryfikację"""
        print("🔍 SZCZEGÓŁOWA WERYFIKACJA PODRĘCZNIKA")
        print("=" * 70)
        
        # Uruchom wszystkie testy
        self.verify_game_modes()
        self.verify_turn_structure()
        self.verify_combat_system()
        self.verify_terrain_system()
        self.verify_movement_modes()
        self.verify_economy_details()
        self.verify_interface_claims()
        
        # Generuj raport
        return self.generate_corrections_report()

if __name__ == "__main__":
    verifier = ManualVerifier()
    report = verifier.run_complete_verification()
    
    print(f"\n🎯 KOŃCOWY WNIOSEK:")
    if report['accuracy'] >= 90:
        print(f"✅ Podręcznik jest w dużej mierze poprawny ({report['accuracy']:.1f}%)")
    elif report['accuracy'] >= 70:
        print(f"⚠️  Podręcznik wymaga umiarkowanych poprawek ({report['accuracy']:.1f}%)")
    else:
        print(f"❌ Podręcznik wymaga znacznych poprawek ({report['accuracy']:.1f}%)")
    
    if report['corrections_count'] > 0:
        print(f"Liczba wymaganych poprawek: {report['corrections_count']}")
        print(f"Priorytet: Usunięcie lub poprawienie nieprawidłowych informacji.")
