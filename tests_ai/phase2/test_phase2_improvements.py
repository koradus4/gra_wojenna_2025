#!/usr/bin/env python3
"""Test ulepszeń FAZA 2 - analiza pathfindingu AI"""

import os
import sys
sys.path.append(os.path.abspath('.'))

def test_target_selection_improvements():
    """Test ulepszonego algorithmu selekcji celów"""
    print("🔄 [PHASE 2 TEST] Testowanie ulepszeń AI target selection...")
    
    # Import potrzebnych modułów
    try:
        from ai.wybor_celow import find_target
        from engine.board import Board
        from engine.token import Token
        print("✅ Moduły załadowane pomyślnie")
    except ImportError as e:
        print(f"❌ Błąd importu: {e}")
        return
    
    # Symulacja planszy
    print("🏗️ Tworzenie testowej planszy...")
    # Użyj istniejącego pliku map_data.json
    board = Board('data/map_data.json')
    
    # Symulacja game_engine z board
    class MockGameEngine:
        def __init__(self, board):
            self.board = board
            self.current_player_obj = None
            
    game_engine = MockGameEngine(board)
    
    # Dodaj kilka key points
    board.key_points = {
        "0,0": {"current_value": 50, "priority": "medium"},
        "2,1": {"current_value": 80, "priority": "high"}, 
        "1,3": {"current_value": 30, "priority": "low"},
        "-1,2": {"current_value": 70, "priority": "high"},
        "3,0": {"current_value": 10, "priority": "low"}
    }
    
    # Symulacja jednostki
    test_unit = {
        'id': 'TEST_UNIT_001',
        'type': 'infantry',
        'mp': 6,
        'fuel': 100,
        'q': 0, 'r': 0
    }
    
    print("🎯 Testowanie find_target z ulepszeniami...")
    
    # Mock funkcji find_path (zawsze zwraca ścieżkę o długości distance)
    def mock_find_path(from_pos, to_pos, max_mp=None, max_fuel=None):
        if max_mp is None or max_mp < 1:
            return None
        # Oblicz dystans hex
        q1, r1 = from_pos
        q2, r2 = to_pos
        distance = max(abs(q1-q2), abs(r1-r2), abs((q1-r1)-(q2-r2)))
        if distance <= max_mp:
            return [(0,0)] * (distance + 1)  # Ścieżka o odpowiedniej długości
        return None
    
    board.find_path = mock_find_path
    
    # Test z różnymi poziomami MP
    for mp_level in [1, 3, 6, 10]:
        test_unit['mp'] = mp_level
        print(f"\n--- Test z MP={mp_level} ---")
        
        target = find_target(test_unit, game_engine)
        if target:
            print(f"✅ Znaleziono cel: {target}")
        else:
            print("❌ Brak dostępnego celu")
    
    print("\n🔍 Sprawdzanie logów diagnostycznych...")
    
    # Sprawdź czy logi zostały utworzone
    log_dir = "logs/ai_commander"
    if os.path.exists(log_dir):
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.csv')]
        if log_files:
            print(f"✅ Znaleziono {len(log_files)} plików logów")
            for log_file in log_files:
                file_path = os.path.join(log_dir, log_file)
                if os.path.getsize(file_path) > 100:  # Większy niż header
                    print(f"  📊 {log_file}: {os.path.getsize(file_path)} bajtów")
        else:
            print("⚠️ Brak plików CSV w katalogu logs")
    else:
        print("⚠️ Katalog logs/ai_commander nie istnieje")

def analyze_recent_logs():
    """Analiza najnowszych logów po testach"""
    print("\n📈 [LOG ANALYSIS] Analiza zebranych danych diagnostycznych...")
    
    try:
        import pandas as pd
        import glob
        
        log_files = glob.glob("logs/ai_commander/actions_*.csv")
        if not log_files:
            print("❌ Brak plików logów do analizy")
            return
            
        # Wczytaj najnowszy plik
        latest_log = max(log_files, key=os.path.getctime)
        print(f"📂 Analizuje: {latest_log}")
        
        df = pd.read_csv(latest_log)
        
        # Filtruj target_analysis
        target_df = df[df['action_type'] == 'target_analysis'].copy()
        
        if len(target_df) == 0:
            print("⚠️ Brak danych target_analysis w logach")
            return
            
        print(f"\n🎯 Analiza {len(target_df)} zapisów target_analysis:")
        
        # Statystyki podstawowe
        success_rate = (target_df['target_search_best_score'] > 0).mean() * 100
        print(f"  📊 Sukces rate: {success_rate:.1f}%")
        
        if 'pathfinding_failures' in target_df.columns:
            avg_failures = target_df['pathfinding_failures'].mean()
            print(f"  🚫 Średnie niepowodzenia pathfinding: {avg_failures:.1f}")
            
        if 'valid_candidates' in target_df.columns:
            avg_valid = target_df['valid_candidates'].mean()
            avg_total = target_df['total_candidates'].mean()
            print(f"  🎯 Średnie kandydatów: {avg_valid:.1f} ważnych z {avg_total:.1f} całkowitych")
            
        # Sprawdź dystanse
        valid_distances = target_df[target_df['target_search_best_distance'] < 777]['target_search_best_distance']
        if len(valid_distances) > 0:
            print(f"  📏 Średnia dystans do celu: {valid_distances.mean():.1f}")
            print(f"  📏 Max dystans: {valid_distances.max()}")
            
    except ImportError:
        print("❌ Pandas nie jest dostępne, pomijam analizę")
    except Exception as e:
        print(f"❌ Błąd podczas analizy: {e}")

if __name__ == "__main__":
    print("🚀 [PHASE 2] Test ulepszeń AI - pathfinding i target selection")
    print("=" * 60)
    
    test_target_selection_improvements()
    analyze_recent_logs()
    
    print("\n✅ Test zakończony! Sprawdź logi w katalogu logs/ai_commander/")
