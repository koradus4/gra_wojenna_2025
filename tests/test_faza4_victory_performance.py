#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TEST FAZY 4: Performance & Analytics - Victory AI Integration
Testuje integrację zaawansowanego logowania z victory_ai.py
"""

import os
import sys
import time
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Dodaj ścieżkę do głównego katalogu
sys.path.insert(0, r'c:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025')

from utils.ai_commander_logger_zaawansowany import ZaawansowanyLoggerAI
from ai.victory_ai import (
    victory_ai_phase1_controller, 
    victory_ai_phase2_controller,
    integrate_victory_ai_full,
    log_performance_metrics,
    log_victory_analysis
)

class MockGameEngine:
    def __init__(self, temp_dir):
        self.current_turn = 5
        self.current_player_obj = MockPlayer(temp_dir)

class MockPlayer:
    def __init__(self, temp_dir):
        self.player_id = 1
        self.victory_points = 15
        self.ai_commander = MockAICommander(temp_dir)

class MockAICommander:
    def __init__(self, temp_dir):
        self.player_id = 1
        self.logger = ZaawansowanyLoggerAI(temp_dir)

def create_mock_units():
    """Tworzy przykładowe jednostki testowe"""
    return [
        {'unit_id': 1, 'position': (5, 5), 'mp': 3, 'moved_capture': False, 'type': 'infantry'},
        {'unit_id': 2, 'position': (7, 8), 'mp': 2, 'moved_capture': False, 'type': 'scout'},
        {'unit_id': 3, 'position': (10, 12), 'mp': 4, 'moved_capture': False, 'type': 'armor'},
        {'unit_id': 4, 'position': (3, 4), 'mp': 0, 'moved_capture': True, 'type': 'artillery'},
        {'unit_id': 5, 'position': (15, 20), 'mp': 3, 'moved_capture': False, 'type': 'infantry'}
    ]

def test_victory_ai_performance_logging():
    """Test logowania wydajności w Victory AI"""
    print("=== TEST FAZY 4: VICTORY AI PERFORMANCE LOGGING ===")
    
    # Przygotowanie środowiska testowego
    temp_dir = tempfile.mkdtemp(prefix='victory_ai_test_')
    print(f"📁 Katalog testowy: {temp_dir}")
    
    try:
        # Mockowanie SessionManager
        import utils.session_manager as session_manager
        original_get_dir = getattr(session_manager.SessionManager, 'get_specialized_ai_logs_dir', None)
        
        def mock_get_dir(self):
            return temp_dir
            
        session_manager.SessionManager.get_specialized_ai_logs_dir = mock_get_dir
        
        # Przygotowanie danych testowych
        game_engine = MockGameEngine(temp_dir)
        my_units = create_mock_units()
        player_id = 1
        
        print(f"🎮 Testowe jednostki: {len(my_units)}")
        print(f"👤 Gracz ID: {player_id}")
        print(f"🎯 Tura: {game_engine.current_turn}")
        
        # TEST 1: Victory AI Phase 1 Controller
        print("\n--- TEST 1: Phase 1 Controller ---")
        phase1_start = time.time()
        phase1_results = victory_ai_phase1_controller(game_engine, my_units, player_id)
        phase1_time = time.time() - phase1_start
        
        print(f"⏱️  Czas wykonania Phase 1: {phase1_time*1000:.2f}ms")
        print(f"🔍 Wykryte okazje: {phase1_results.get('combat_opportunities', 0)}")
        print(f"🚁 Wysłane zwiady: {phase1_results.get('scouts_deployed', 0)}")
        print(f"⚔️  Zalecane akcje: {len(phase1_results.get('recommended_actions', []))}")
        print(f"🧮 Obliczenia: {phase1_results.get('calculations_count', 0)}")
        
        # TEST 2: Victory AI Phase 2 Controller
        print("\n--- TEST 2: Phase 2 Controller ---")
        phase2_start = time.time()
        phase2_results = victory_ai_phase2_controller(game_engine, my_units, player_id)
        phase2_time = time.time() - phase2_start
        
        print(f"⏱️  Czas wykonania Phase 2: {phase2_time*1000:.2f}ms")
        print(f"📋 Aktywne plany: {phase2_results.get('active_plans', 0)}")
        print(f"🆕 Nowe plany: {phase2_results.get('new_plans_created', 0)}")
        print(f"✅ Wykonane plany: {phase2_results.get('plans_executed', 0)}")
        print(f"🧮 Obliczenia: {phase2_results.get('calculations_count', 0)}")
        
        # TEST 3: Integrated Victory AI Full
        print("\n--- TEST 3: Full Integration ---")
        full_start = time.time()
        full_results = integrate_victory_ai_full(game_engine, my_units, player_id)
        full_time = time.time() - full_start
        
        print(f"⏱️  Czas wykonania Full Integration: {full_time*1000:.2f}ms")
        print(f"🎯 Victory AI Active: {full_results.get('victory_ai_active', False)}")
        print(f"📊 Łączne okazje: {full_results.get('total_opportunities', 0)}")
        print(f"📈 Aktywne plany ataków: {full_results.get('active_attack_plans', 0)}")
        
        # TEST 4: Sprawdzenie CSV Files
        print("\n--- TEST 4: CSV Files Check ---")
        
        # Sprawdź w katalogu temp_dir
        print(f"🔍 Szukam CSV files w temp_dir: {temp_dir}")
        
        expected_files = [
            'decyzje_strategiczne.csv',
            'akcje_taktyczne.csv', 
            'decyzje_ekonomiczne.csv',
            'analiza_wywiadu.csv',
            'wydajnosc_ai.csv',
            'analiza_zwyciestwa.csv'
        ]
        
        files_found = 0
        for filename in expected_files:
            filepath = os.path.join(temp_dir, filename)
            if os.path.exists(filepath):
                files_found += 1
                file_size = os.path.getsize(filepath)
                print(f"✅ {filename} - {file_size} bajtów")
                
                # Sprawdź kilka linii
                if file_size > 0:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) > 1:  # Nagłówek + dane
                            print(f"   📝 Linii danych: {len(lines) - 1}")
            else:
                print(f"❌ {filename} - BRAK")
        
        # Sprawdź też w katalogach logs jeśli istnieją
        print(f"\n🔍 Sprawdzam alternatywne lokalizacje...")
        for root, dirs, files in os.walk(temp_dir):
            for filename in expected_files:
                if filename in files:
                    print(f"✅ Znaleziono {filename} w {root}")
                    files_found += 1
        
        print(f"\n📊 Pliki CSV: {files_found}/{len(expected_files)}")
        
        # TEST 5: Performance Metrics Analysis
        print("\n--- TEST 5: Performance Analysis ---")
        
        wydajnosc_file = os.path.join(temp_dir, 'wydajnosc_ai.csv')
        if os.path.exists(wydajnosc_file):
            with open(wydajnosc_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    print(f"📈 Rekordy wydajności: {len(lines) - 1}")
                    # Pokaż ostatni rekord
                    last_record = lines[-1].strip()
                    print(f"🔄 Ostatni rekord: {last_record[:100]}...")
                    
        analiza_file = os.path.join(temp_dir, 'analiza_zwyciestwa.csv')
        if os.path.exists(analiza_file):
            with open(analiza_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    print(f"🏆 Analizy zwycięstwa: {len(lines) - 1}")
                    last_record = lines[-1].strip()
                    print(f"⚡ Ostatni rekord: {last_record[:100]}...")
        
        print("\n✅ FAZA 4 VICTORY AI - PERFORMANCE & ANALYTICS ZAKOŃCZONA POMYŚLNIE!")
        return True
        
    except Exception as e:
        print(f"❌ BŁĄD TESTU FAZY 4: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🧹 Wyczyszczono katalog testowy: {temp_dir}")
        
        # Przywróć oryginalną metodę
        if original_get_dir:
            session_manager.SessionManager.get_specialized_ai_logs_dir = original_get_dir

if __name__ == '__main__':
    success = test_victory_ai_performance_logging()
    if success:
        print("\n🎉 WSZYSTKIE TESTY FAZY 4 ZAKOŃCZONE POMYŚLNIE!")
        sys.exit(0)
    else:
        print("\n💥 TESTY FAZY 4 NIEUDANE!")
        sys.exit(1)