"""
Testy systemu logowania AI Generała - FAZA 2
Sprawdza czy wszystkie logi są prawidłowo zapisywane
"""
import pytest
import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from ai.ai_general import AIGeneral

class TestAILogging:
    
    @pytest.fixture
    def ai_general(self):
        with patch('ai.ai_general.Path.mkdir'):  # Nie tworzymy prawdziwych folderów
            ai = AIGeneral(nationality="polish")
        return ai
    
    @pytest.fixture
    def temp_log_file(self):
        """Tymczasowy plik CSV do testów"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = Path(f.name)
        yield temp_path
        temp_path.unlink()  # Usuń po teście
    
    def test_economy_log_creation(self, ai_general, temp_log_file):
        """Test tworzenia logu ekonomii"""
        ai_general._economy_log_file = temp_log_file
        
        # Inicjalizuj plik z nagłówkiem
        ai_general._init_economy_log()
        
        # Test logowania
        ai_general.log_economy_turn(
            turn=5,
            pe_start=100,
            pe_allocated=40,
            pe_spent_purchases=30,
            strategy_used='COMBO'
        )
        
        # Sprawdź czy plik został utworzony i zawiera dane
        assert temp_log_file.exists()
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1
        row = rows[0]
        assert row['turn'] == '5'
        assert row['pe_start'] == '100'
        assert row['pe_allocated'] == '40'
        assert row['pe_spent_purchases'] == '30'
        assert row['pe_total_used'] == '70'  # 40 + 30
        assert row['pe_remaining'] == '30'    # 100 - 70
        assert row['strategy_used'] == 'COMBO'
        assert row['nation'] == 'Polska'
        
    def test_keypoints_log_creation(self, ai_general, temp_log_file):
        """Test tworzenia logu Key Points"""
        ai_general._keypoints_log_file = temp_log_file
        
        # Inicjalizuj plik z nagłówkiem
        ai_general._init_keypoints_log()
        
        # Mock Key Points state
        key_points_state = {
            'hex_1': {
                'type': 'Factory',
                'value': 15,
                'controlled_by': 'Polska',
                'income_generated': 15
            },
            'hex_2': {
                'type': 'Resource',
                'value': 10,
                'controlled_by': 'Niemcy',
                'income_generated': 0
            }
        }
        
        ai_general.log_keypoints_turn(turn=3, key_points_state=key_points_state)
        
        # Sprawdź zawartość
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 2
        
        # Sprawdź pierwszy Key Point
        row1 = rows[0]
        assert row1['hex_id'] == 'hex_1'
        assert row1['kp_type'] == 'Factory'
        assert row1['kp_value_start'] == '15'
        assert row1['kp_controlled_by'] == 'Polska'
        
    def test_strategy_log_creation(self, ai_general, temp_log_file):
        """Test tworzenia logu strategii"""
        ai_general._strategy_log_file = temp_log_file
        
        # Inicjalizuj plik z nagłówkiem
        ai_general._init_strategy_log()
        
        # Ustaw dane kontekstowe
        ai_general._unit_analysis = {
            'low_fuel_ratio': 0.25,
            'total_units': 12,
            'commanders_analysis': {'1': {}, '2': {}}
        }
        ai_general._strategic_analysis = {
            'game_phase': 1.8,
            'phase_name': 'ŚREDNIA',
            'vp_situation': 'WYGRYWAMY'
        }
        
        ai_general.log_strategy_decision(
            turn=7,
            decision='COMBO',
            rule_used='strategic_combo_EKSPANSJA',
            reasoning='Strategia ekspansji w średniej fazie'
        )
        
        # Sprawdź zawartość
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1
        row = rows[0]
        assert row['decision'] == 'COMBO'
        assert row['rule_used'] == 'strategic_combo_EKSPANSJA'
        assert row['low_fuel_ratio'] == '0.25'
        assert row['total_units'] == '12'
        assert row['commanders_count'] == '2'
        
        # Sprawdź context JSON
        context = json.loads(row['context'])
        assert context['phase'] == 'ŚREDNIA'
        assert context['vp_situation'] == 'WYGRYWAMY'
        
    def test_logging_system_initialization(self, ai_general):
        """Test inicjalizacji systemu logowania"""
        # Sprawdź czy wszystkie pliki logów są ustawione
        assert hasattr(ai_general, '_economy_log_file')
        assert hasattr(ai_general, '_keypoints_log_file')
        assert hasattr(ai_general, '_strategy_log_file')
        
        # Sprawdź czy ścieżki zawierają nazwę nacji
        assert 'polska' in str(ai_general._economy_log_file).lower()
        assert 'polska' in str(ai_general._keypoints_log_file).lower()
        assert 'polska' in str(ai_general._strategy_log_file).lower()
        
    def test_economy_log_with_strategic_data(self, ai_general, temp_log_file):
        """Test logowania ekonomii z danymi strategicznymi"""
        ai_general._economy_log_file = temp_log_file
        
        # Inicjalizuj plik z nagłówkiem
        ai_general._init_economy_log()
        
        ai_general._strategic_analysis = {
            'vp_own': 60,
            'vp_enemy': 45,
            'vp_status': 15
        }
        
        ai_general.log_economy_turn(
            turn=10,
            pe_start=80,
            pe_allocated=20,
            pe_spent_purchases=45,
            strategy_used='DESPERACJA'
        )
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            
        assert row['vp_own'] == '60'
        assert row['vp_enemy'] == '45'
        assert row['vp_status'] == '15'
        
    def test_logging_handles_errors_gracefully(self, ai_general):
        """Test czy logowanie gracefully obsługuje błędy"""
        # Ustaw nieprawidłową ścieżkę
        ai_general._economy_log_file = Path("/invalid/path/file.csv")
        
        # Nie powinno rzucać wyjątku
        try:
            ai_general.log_economy_turn(1, 100, 50, 30, 'TEST')
        except Exception as e:
            pytest.fail(f"Logowanie nie powinno rzucać wyjątku: {e}")
            
    def test_csv_headers_are_correct(self, ai_general, temp_log_file):
        """Test czy nagłówki CSV są prawidłowe"""
        ai_general._economy_log_file = temp_log_file
        ai_general._init_economy_log()
        
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
        expected_headers = [
            'timestamp', 'turn', 'nation', 'pe_start', 'pe_allocated',
            'pe_spent_purchases', 'pe_total_used', 'pe_remaining',
            'strategy_used', 'vp_own', 'vp_enemy', 'vp_status'
        ]
        
        assert headers == expected_headers
