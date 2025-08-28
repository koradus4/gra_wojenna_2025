#!/usr/bin/env python3
"""
KOMPLETNY TEST PRZEPŁYWU ZAKUPÓW AI GENERAL → AI COMMANDER
Testuje cały proces krok po kroku z szczegółowym logowaniem
"""

import sys
import os
import json
import csv
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock
import unittest

# Dodaj główny folder do path
sys.path.append(str(Path(__file__).parent.parent))

class AIGeneralPurchaseFlowTest(unittest.TestCase):
    """Test kompletnego przepływu zakupów AI"""
    
    def setUp(self):
        """Przygotowanie do testów"""
        self.test_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_log_file = f"logs/test_ai_flow_{self.test_timestamp}.csv"
        self.tokens_path = Path("assets/tokens")
        
        # Utwórz folder logs jeśli nie istnieje
        Path("logs").mkdir(exist_ok=True)
        
        # Przygotuj plik logów CSV
        with open(self.test_log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'test_phase', 'component', 'action', 'status', 
                'details', 'data', 'error_msg'
            ])
        
        print(f"🧪 [TEST SETUP] Rozpoczynam kompletny test AI flow")
        print(f"📝 [TEST SETUP] Log file: {self.test_log_file}")
        self.log_test_event("SETUP", "TestSuite", "initialize", "SUCCESS", "Test suite initialized")
    
    def log_test_event(self, phase, component, action, status, details, data=None, error_msg=None):
        """Loguje zdarzenie testowe do CSV"""
        try:
            with open(self.test_log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    phase,
                    component,
                    action,
                    status,
                    details,
                    json.dumps(data) if data else "",
                    error_msg or ""
                ])
        except Exception as e:
            print(f"❌ [LOG ERROR] {e}")
    
    def create_mock_game_engine(self):
        """Tworzy mock game engine z realistycznymi danymi"""
        print("🎮 [MOCK] Tworzę mock game engine...")
        
        # Mock Players
        mock_general = Mock()
        mock_general.id = 4  # Niemiecki generał
        mock_general.nation = "Niemcy"
        mock_general.role = "Generał"
        mock_general.economy = Mock()
        mock_general.economy.economic_points = 150  # Wystarczająco na zakupy
        mock_general.economy.get_points.return_value = {'economic_points': 150}
        mock_general.economy.subtract_points = Mock()
        
        mock_commander_5 = Mock()
        mock_commander_5.id = 5
        mock_commander_5.nation = "Niemcy"
        mock_commander_5.role = "Dowódca"
        mock_commander_5.economy = Mock()
        mock_commander_5.economy.economic_points = 20
        mock_commander_5.economy.get_points.return_value = {'economic_points': 20}
        
        mock_commander_6 = Mock()
        mock_commander_6.id = 6
        mock_commander_6.nation = "Niemcy" 
        mock_commander_6.role = "Dowódca"
        mock_commander_6.economy = Mock()
        mock_commander_6.economy.economic_points = 15
        mock_commander_6.economy.get_points.return_value = {'economic_points': 15}
        
        # Mock Game Engine
        mock_engine = Mock()
        mock_engine.players = [mock_general, mock_commander_5, mock_commander_6]
        mock_engine.current_player_obj = mock_general
        mock_engine.turn = 5
        mock_engine.turn_number = 5
        mock_engine.current_turn = 5
        mock_engine.tokens = []
        mock_engine.key_points_state = {}
        
        # Mock victory_points as integers
        mock_general.victory_points = 0
        mock_commander_5.victory_points = 0  
        mock_commander_6.victory_points = 0
        
        # Mock Board
        mock_board = Mock()
        mock_board.tokens = []
        mock_board.is_occupied.return_value = False
        mock_board.neighbors.return_value = [(10, 10), (11, 10), (9, 10)]
        mock_board.hex_distance.return_value = 5
        mock_engine.board = mock_board
        
        # Mock visible tokens (jednostki na mapie)
        mock_tokens = []
        for i in range(3):  # 3 jednostki dla dowódcy 5
            token = Mock()
            token.id = f"existing_unit_{i}"
            token.owner = "5 (Niemcy)"
            token.nation = "Niemcy"
            token.unitType = "P" if i < 2 else "Z"  # 2 piechoty, 1 zaopatrzenie
            token.maxFuel = 100
            token.currentFuel = 30 if i == 0 else 80  # Jedna z niskim paliwem
            token.combat_value = 4
            token.q = 10 + i
            token.r = 10
            mock_tokens.append(token)
        
        mock_engine.get_visible_tokens.return_value = mock_tokens
        
        # Mock map data
        mock_engine.map_data = {
            'spawn_points': {
                'Niemcy': ['40,-10', '41,-10', '42,-10']
            }
        }
        
        self.log_test_event("MOCK", "GameEngine", "create", "SUCCESS", 
                           f"Created mock with {len(mock_tokens)} units", 
                           {"general_pe": 150, "commanders": 2, "units": len(mock_tokens)})
        
        return mock_engine, mock_general, [mock_commander_5, mock_commander_6]
    
    def test_01_ai_general_analysis_phase(self):
        """Test fazy analizy AI Generała"""
        print("\n🔍 [TEST 1] FAZA ANALIZY AI GENERAŁA")
        
        try:
            from ai.ai_general import AIGeneral
            
            mock_engine, mock_general, commanders = self.create_mock_game_engine()
            
            ai_general = AIGeneral("Niemcy")
            ai_general.debug = True
            
            # Test analizy ekonomii
            print("💰 [TEST 1.1] Analiza ekonomii...")
            ai_general.analyze_economy(mock_general)
            self.log_test_event("ANALYSIS", "AIGeneral", "analyze_economy", "SUCCESS", 
                               "Economy analysis completed")
            
            # Test analizy jednostek
            print("🪖 [TEST 1.2] Analiza jednostek...")
            ai_general.analyze_units(mock_engine, mock_general)
            
            # Sprawdź czy analiza została zapisana
            unit_analysis = getattr(ai_general, '_unit_analysis', {})
            self.assertIsNotNone(unit_analysis)
            self.assertIn('total_units', unit_analysis)
            self.assertIn('low_fuel_ratio', unit_analysis)
            
            print(f"📊 [TEST 1.2] Wyniki analizy: {unit_analysis}")
            self.log_test_event("ANALYSIS", "AIGeneral", "analyze_units", "SUCCESS", 
                               "Unit analysis completed", unit_analysis)
            
            # Test analizy strategicznej
            print("🎯 [TEST 1.3] Analiza strategiczna...")
            strategic = ai_general.analyze_strategic_situation(mock_engine, mock_general)
            self.assertIsNotNone(strategic)
            
            self.log_test_event("ANALYSIS", "AIGeneral", "analyze_strategic", "SUCCESS", 
                               "Strategic analysis completed", strategic)
            
            print("✅ [TEST 1] Faza analizy zakończona pomyślnie")
            
        except Exception as e:
            self.log_test_event("ANALYSIS", "AIGeneral", "test_phase", "ERROR", 
                               "Analysis phase failed", error_msg=str(e))
            self.fail(f"Test analizy nie powiódł się: {e}")
    
    def test_02_ai_general_decision_making(self):
        """Test podejmowania decyzji przez AI Generała"""
        print("\n🧠 [TEST 2] PODEJMOWANIE DECYZJI AI GENERAŁA")
        
        try:
            from ai.ai_general import AIGeneral, EconAction
            
            mock_engine, mock_general, commanders = self.create_mock_game_engine()
            
            ai_general = AIGeneral("Niemcy")
            ai_general.debug = True
            
            # Wykonaj analizę najpierw
            ai_general.analyze_economy(mock_general)
            ai_general.analyze_units(mock_engine, mock_general)
            ai_general.analyze_strategic_situation(mock_engine, mock_general)
            
            # Test decyzji ekonomicznej
            print("💡 [TEST 2.1] Podejmowanie decyzji ekonomicznej...")
            action, metrics = ai_general.decide_action(mock_general, mock_engine)
            
            self.assertIsInstance(action, EconAction)
            self.assertIsInstance(metrics, dict)
            
            print(f"🎯 [TEST 2.1] Decyzja: {action.name}")
            print(f"📊 [TEST 2.1] Metryki: {metrics}")
            
            self.log_test_event("DECISION", "AIGeneral", "decide_action", "SUCCESS", 
                               f"Decision: {action.name}", metrics)
            
            # Test strategii
            strategic = getattr(ai_general, '_strategic_analysis', {})
            unit_analysis = getattr(ai_general, '_unit_analysis', {})
            strategy = ai_general._determine_strategy(strategic, unit_analysis, 3)
            
            print(f"🎯 [TEST 2.2] Strategia: {strategy}")
            self.log_test_event("DECISION", "AIGeneral", "determine_strategy", "SUCCESS", 
                               f"Strategy: {strategy}")
            
            print("✅ [TEST 2] Podejmowanie decyzji zakończone pomyślnie")
            
        except Exception as e:
            self.log_test_event("DECISION", "AIGeneral", "test_phase", "ERROR", 
                               "Decision phase failed", error_msg=str(e))
            self.fail(f"Test decyzji nie powiódł się: {e}")
    
    def test_03_ai_general_purchase_execution(self):
        """Test wykonania zakupów przez AI Generała"""
        print("\n🛒 [TEST 3] WYKONANIE ZAKUPÓW AI GENERAŁA")
        
        try:
            from ai.ai_general import AIGeneral
            
            mock_engine, mock_general, commanders = self.create_mock_game_engine()
            
            ai_general = AIGeneral("Niemcy")
            ai_general.debug = True
            
            # Wykonaj pełną analizę
            ai_general.analyze_economy(mock_general)
            ai_general.analyze_units(mock_engine, mock_general)
            ai_general.analyze_strategic_situation(mock_engine, mock_general)
            
            # Test zbierania stanu
            print("📊 [TEST 3.1] Zbieranie stanu...")
            state = ai_general._gather_state(mock_engine, mock_general, commanders)
            self.assertIsInstance(state, dict)
            self.assertIn('global', state)
            self.assertIn('per_commander', state)
            
            print(f"📈 [TEST 3.1] Stan: {state}")
            self.log_test_event("PURCHASE", "AIGeneral", "gather_state", "SUCCESS", 
                               "State gathered", state)
            
            # Test planowania zakupów
            print("📋 [TEST 3.2] Planowanie zakupów...")
            purchase_plans = ai_general.plan_purchases(100, commanders, max_purchases=2, state=state)
            self.assertIsInstance(purchase_plans, list)
            
            if purchase_plans:
                print(f"📦 [TEST 3.2] Zaplanowano {len(purchase_plans)} zakupów:")
                for i, plan in enumerate(purchase_plans):
                    print(f"  {i+1}. {plan.get('name', plan.get('type'))} dla dowódcy {plan.get('commander_id')} (koszt: {plan.get('cost')})")
                
                self.log_test_event("PURCHASE", "AIGeneral", "plan_purchases", "SUCCESS", 
                                   f"Planned {len(purchase_plans)} purchases", purchase_plans)
                
                # Test wykonania zakupu
                print("💳 [TEST 3.3] Wykonanie zakupu...")
                first_plan = purchase_plans[0]
                
                # Wyczyść folder przed testem
                folder_path = Path(f"assets/tokens/nowe_dla_{first_plan['commander_id']}")
                if folder_path.exists():
                    shutil.rmtree(folder_path)
                
                success = ai_general.purchase_unit_programmatically(mock_general, first_plan)
                self.assertTrue(success, "Zakup powinien się powieść")
                
                # Sprawdź czy token został utworzony
                self.assertTrue(folder_path.exists(), "Folder dla dowódcy powinien istnieć")
                
                token_folders = list(folder_path.glob("*/"))
                self.assertGreater(len(token_folders), 0, "Powinien istnieć folder z tokenem")
                
                token_json = token_folders[0] / "token.json"
                self.assertTrue(token_json.exists(), "Plik token.json powinien istnieć")
                
                # Sprawdź zawartość tokenu
                with open(token_json, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
                
                self.assertIn('id', token_data)
                self.assertIn('unitType', token_data)
                self.assertIn('owner', token_data)
                self.assertEqual(str(token_data['owner']), str(first_plan['commander_id']))
                
                print(f"✅ [TEST 3.3] Token utworzony: {token_data['id']}")
                self.log_test_event("PURCHASE", "AIGeneral", "purchase_unit", "SUCCESS", 
                                   f"Unit purchased: {token_data['unitType']}", token_data)
            else:
                print("⚠️ [TEST 3.2] Brak zaplanowanych zakupów")
                self.log_test_event("PURCHASE", "AIGeneral", "plan_purchases", "WARNING", 
                                   "No purchases planned")
            
            print("✅ [TEST 3] Wykonanie zakupów zakończone pomyślnie")
            
        except Exception as e:
            self.log_test_event("PURCHASE", "AIGeneral", "test_phase", "ERROR", 
                               "Purchase phase failed", error_msg=str(e))
            self.fail(f"Test zakupów nie powiódł się: {e}")
    
    def test_04_ai_commander_deployment(self):
        """Test wdrożenia jednostek przez AI Commandera"""
        print("\n🎖️ [TEST 4] WDROŻENIE JEDNOSTEK AI COMMANDER")
        
        try:
            from ai.ai_commander import deploy_purchased_units, create_and_deploy_token
            
            mock_engine, mock_general, commanders = self.create_mock_game_engine()
            
            # Upewnij się że istnieje token do wdrożenia
            commander_id = 5
            folder_path = Path(f"assets/tokens/nowe_dla_{commander_id}")
            
            if not folder_path.exists() or not list(folder_path.glob("*/")):
                print("📦 [TEST 4.0] Tworzę testowy token do wdrożenia...")
                
                # Stwórz testowy token
                from ai.ai_general import AIGeneral
                ai_general = AIGeneral("Niemcy")
                
                test_plan = {
                    'type': 'P',
                    'size': 'Pluton',
                    'cost': 30,
                    'commander_id': commander_id,
                    'name': 'Piechota Pluton',
                    'supports': []
                }
                
                success = ai_general.purchase_unit_programmatically(mock_general, test_plan)
                self.assertTrue(success, "Testowy token powinien zostać utworzony")
                
                self.log_test_event("DEPLOYMENT", "Test", "create_test_token", "SUCCESS", 
                                   f"Test token created for commander {commander_id}")
            
            # Test skanowania folderów
            print("📂 [TEST 4.1] Skanowanie folderów zakupionych jednostek...")
            purchased_files = []
            if folder_path.exists():
                for token_folder in folder_path.glob("*/"):
                    token_json = token_folder / "token.json"
                    if token_json.exists():
                        purchased_files.append(str(token_json))
            
            print(f"📋 [TEST 4.1] Znaleziono {len(purchased_files)} tokenów do wdrożenia")
            self.log_test_event("DEPLOYMENT", "AICommander", "scan_folders", "SUCCESS", 
                               f"Found {len(purchased_files)} tokens", {"files": purchased_files})
            
            if purchased_files:
                # Test wczytania danych tokenu
                print("📄 [TEST 4.2] Wczytywanie danych tokenu...")
                with open(purchased_files[0], 'r', encoding='utf-8') as f:
                    unit_data = json.load(f)
                
                print(f"📊 [TEST 4.2] Dane tokenu: {unit_data['unitType']} {unit_data['unitSize']}")
                self.log_test_event("DEPLOYMENT", "AICommander", "load_token_data", "SUCCESS", 
                                   f"Loaded: {unit_data['unitType']}", unit_data)
                
                # Test znajdowania pozycji deployment
                print("📍 [TEST 4.3] Znajdowanie pozycji deployment...")
                from ai.ai_commander import find_deployment_position
                
                position = find_deployment_position(unit_data, mock_engine, commander_id)
                if position:
                    print(f"✅ [TEST 4.3] Pozycja znaleziona: {position}")
                    self.log_test_event("DEPLOYMENT", "AICommander", "find_position", "SUCCESS", 
                                       f"Position: {position}")
                    
                    # Test tworzenia tokenu na mapie
                    print("🎯 [TEST 4.4] Tworzenie tokenu na mapie...")
                    success = create_and_deploy_token(unit_data, position, mock_engine, commander_id)
                    
                    if success:
                        print("✅ [TEST 4.4] Token pomyślnie wdrożony")
                        self.log_test_event("DEPLOYMENT", "AICommander", "deploy_token", "SUCCESS", 
                                           f"Token deployed at {position}")
                        
                        # Sprawdź czy token został dodany do gry
                        self.assertGreater(len(mock_engine.board.tokens), 0, 
                                         "Token powinien być dodany do board.tokens")
                    else:
                        print("❌ [TEST 4.4] Błąd wdrożenia tokenu")
                        self.log_test_event("DEPLOYMENT", "AICommander", "deploy_token", "ERROR", 
                                           "Token deployment failed")
                else:
                    print("❌ [TEST 4.3] Nie znaleziono pozycji deployment")
                    self.log_test_event("DEPLOYMENT", "AICommander", "find_position", "ERROR", 
                                       "No deployment position found")
                
                # Test pełnego deployment
                print("🔄 [TEST 4.5] Pełny deployment...")
                initial_board_tokens = len(mock_engine.board.tokens)
                deployed_count = deploy_purchased_units(mock_engine, commander_id)
                
                print(f"📈 [TEST 4.5] Wdrożono {deployed_count} jednostek")
                self.log_test_event("DEPLOYMENT", "AICommander", "full_deployment", "SUCCESS", 
                                   f"Deployed {deployed_count} units")
                
                # Sprawdź czy folder został wyczyszczony
                remaining_files = list(folder_path.glob("*/"))
                print(f"🧹 [TEST 4.6] Pozostałe pliki po deployment: {len(remaining_files)}")
                
            else:
                print("⚠️ [TEST 4.1] Brak tokenów do wdrożenia")
                self.log_test_event("DEPLOYMENT", "AICommander", "scan_folders", "WARNING", 
                                   "No tokens found for deployment")
            
            print("✅ [TEST 4] Wdrożenie jednostek zakończone pomyślnie")
            
        except Exception as e:
            self.log_test_event("DEPLOYMENT", "AICommander", "test_phase", "ERROR", 
                               "Deployment phase failed", error_msg=str(e))
            self.fail(f"Test wdrożenia nie powiódł się: {e}")
    
    def test_05_complete_integration_flow(self):
        """Test kompletnego przepływu integracji"""
        print("\n🔄 [TEST 5] KOMPLETNY PRZEPŁYW INTEGRACJI")
        
        try:
            from ai.ai_general import AIGeneral
            from ai.ai_commander import deploy_purchased_units
            
            mock_engine, mock_general, commanders = self.create_mock_game_engine()
            
            # KROK 1: AI General pełna tura
            print("🤖 [TEST 5.1] AI General - pełna tura...")
            ai_general = AIGeneral("Niemcy")
            ai_general.debug = True
            
            initial_pe = mock_general.economy.get_points()['economic_points']
            print(f"💰 [TEST 5.1] PE na początku: {initial_pe}")
            
            # Wyczyść foldery przed testem
            for cmd in commanders:
                folder_path = Path(f"assets/tokens/nowe_dla_{cmd.id}")
                if folder_path.exists():
                    shutil.rmtree(folder_path)
            
            # Wykonaj turę AI Generała
            ai_general.make_turn(mock_engine)
            
            final_pe = mock_general.economy.get_points()['economic_points']
            print(f"💰 [TEST 5.1] PE na końcu: {final_pe}")
            
            self.log_test_event("INTEGRATION", "AIGeneral", "full_turn", "SUCCESS", 
                               f"PE: {initial_pe} -> {final_pe}")
            
            # KROK 2: Sprawdź czy powstały tokeny
            print("📦 [TEST 5.2] Sprawdzanie utworzonych tokenów...")
            created_tokens = []
            
            for cmd in commanders:
                folder_path = Path(f"assets/tokens/nowe_dla_{cmd.id}")
                if folder_path.exists():
                    token_folders = list(folder_path.glob("*/"))
                    for token_folder in token_folders:
                        token_json = token_folder / "token.json"
                        if token_json.exists():
                            with open(token_json, 'r', encoding='utf-8') as f:
                                token_data = json.load(f)
                            created_tokens.append({
                                'commander': cmd.id,
                                'type': token_data.get('unitType'),
                                'size': token_data.get('unitSize'),
                                'id': token_data.get('id')
                            })
            
            print(f"📋 [TEST 5.2] Utworzono {len(created_tokens)} tokenów:")
            for token in created_tokens:
                print(f"  - Dowódca {token['commander']}: {token['type']} {token['size']}")
            
            self.log_test_event("INTEGRATION", "CheckTokens", "created_tokens", "SUCCESS", 
                               f"Created {len(created_tokens)} tokens", created_tokens)
            
            # KROK 3: AI Commander deployment
            print("🎖️ [TEST 5.3] AI Commander - deployment...")
            total_deployed = 0
            
            for cmd in commanders:
                print(f"👤 [TEST 5.3] Deployment dla dowódcy {cmd.id}...")
                deployed = deploy_purchased_units(mock_engine, cmd.id)
                total_deployed += deployed
                print(f"✅ [TEST 5.3] Wdrożono {deployed} jednostek")
            
            print(f"📈 [TEST 5.3] Łącznie wdrożono: {total_deployed} jednostek")
            self.log_test_event("INTEGRATION", "AICommander", "total_deployment", "SUCCESS", 
                               f"Total deployed: {total_deployed}")
            
            # KROK 4: Sprawdź stan końcowy
            print("🏁 [TEST 5.4] Stan końcowy...")
            final_board_tokens = len(mock_engine.board.tokens)
            
            # Sprawdź czy foldery zostały wyczyszczone
            remaining_folders = []
            for cmd in commanders:
                folder_path = Path(f"assets/tokens/nowe_dla_{cmd.id}")
                if folder_path.exists():
                    remaining = list(folder_path.glob("*/"))
                    if remaining:
                        remaining_folders.append((cmd.id, len(remaining)))
            
            print(f"🎯 [TEST 5.4] Tokeny na mapie: {final_board_tokens}")
            print(f"🧹 [TEST 5.4] Pozostałe foldery: {remaining_folders}")
            
            self.log_test_event("INTEGRATION", "FinalState", "check_state", "SUCCESS", 
                               f"Board tokens: {final_board_tokens}, Remaining folders: {len(remaining_folders)}")
            
            # Podsumowanie
            success_metrics = {
                'pe_spent': initial_pe - final_pe,
                'tokens_created': len(created_tokens),
                'tokens_deployed': total_deployed,
                'final_board_tokens': final_board_tokens,
                'folders_cleaned': len(commanders) - len(remaining_folders)
            }
            
            print("🎉 [TEST 5] PODSUMOWANIE INTEGRACJI:")
            print(f"  💰 Wydane PE: {success_metrics['pe_spent']}")
            print(f"  📦 Utworzone tokeny: {success_metrics['tokens_created']}")
            print(f"  🎯 Wdrożone tokeny: {success_metrics['tokens_deployed']}")
            print(f"  🎮 Tokeny na mapie: {success_metrics['final_board_tokens']}")
            print(f"  🧹 Wyczyszczone foldery: {success_metrics['folders_cleaned']}")
            
            self.log_test_event("INTEGRATION", "Complete", "summary", "SUCCESS", 
                               "Complete integration test finished", success_metrics)
            
            print("✅ [TEST 5] Kompletny przepływ integracji zakończony pomyślnie")
            
        except Exception as e:
            self.log_test_event("INTEGRATION", "Complete", "test_phase", "ERROR", 
                               "Integration test failed", error_msg=str(e))
            self.fail(f"Test integracji nie powiódł się: {e}")
    
    def tearDown(self):
        """Czyszczenie po testach"""
        print(f"\n🧹 [CLEANUP] Czyszczenie po testach...")
        
        # Wyczyść foldery testowe
        cleanup_folders = [
            "assets/tokens/nowe_dla_4",
            "assets/tokens/nowe_dla_5", 
            "assets/tokens/nowe_dla_6"
        ]
        
        for folder in cleanup_folders:
            folder_path = Path(folder)
            if folder_path.exists():
                try:
                    shutil.rmtree(folder_path)
                    print(f"🗑️ [CLEANUP] Usunięto: {folder}")
                except Exception as e:
                    print(f"⚠️ [CLEANUP] Błąd usuwania {folder}: {e}")
        
        self.log_test_event("CLEANUP", "TestSuite", "cleanup", "SUCCESS", "Test cleanup completed")
        print(f"📝 [CLEANUP] Kompletny log zapisany w: {self.test_log_file}")

if __name__ == "__main__":
    # Uruchom testy
    print("🚀 ROZPOCZYNAM KOMPLETNY TEST AI PURCHASE FLOW")
    print("="*60)
    
    unittest.main(verbosity=2)
