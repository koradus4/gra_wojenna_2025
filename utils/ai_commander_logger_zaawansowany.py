# -*- coding: utf-8 -*-
"""
Zaawansowany system logowania AI Commander z polskimi nazwami
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

from .ai_logger_config_pl import POLISH_CONFIG, NAZWY_PLIKOW, POLISH_COLUMN_MAPPING


class PolskiLoggerBazowy:
    """Klasa bazowa dla wszystkich polskich loggerów"""
    
    def __init__(self, katalog_sesji: Path):
        self.katalog_sesji = Path(katalog_sesji)
        self.config = POLISH_CONFIG
        
    def tlumacz_nazwe_kolumny(self, eng_name: str) -> str:
        """Tłumaczy nazwę kolumny z angielskiego na polski"""
        return self.config['nazwy_kolumn'].get(eng_name, eng_name)
        
    def tlumacz_wartosc_enum(self, kategoria: str, wartosc: str) -> str:
        """Tłumaczy wartości enum na polskie"""
        if kategoria in self.config['wartosci_enum']:
            return self.config['wartosci_enum'][kategoria].get(wartosc, wartosc)
        return wartosc
    
    def przygotuj_katalog(self, nazwa_katalogu: str) -> Path:
        """Tworzy katalog dla konkretnego typu logów"""
        katalog = self.katalog_sesji / "ai_commander_zaawansowany" / nazwa_katalogu
        katalog.mkdir(parents=True, exist_ok=True)
        return katalog
    
    def zapisz_wiersz_csv(self, sciezka_pliku: Path, dane: Dict[str, Any], kolumny: List[str]):
        """Zapisuje wiersz do pliku CSV z polskimi nazwami kolumn"""
        plik_istnieje = sciezka_pliku.exists()
        
        # Tłumaczenie nazw kolumn
        polskie_kolumny = [self.tlumacz_nazwe_kolumny(col) for col in kolumny]
        
        # Tłumaczenie danych
        polskie_dane = {}
        for eng_key, value in dane.items():
            polski_key = self.tlumacz_nazwe_kolumny(eng_key)
            polskie_dane[polski_key] = value
        
        with open(sciezka_pliku, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=polskie_kolumny)
            
            # Nagłówki tylko jeśli plik nie istnieje
            if not plik_istnieje:
                writer.writeheader()
            
            # Uzupełnienie brakujących wartości
            wiersz = {}
            for kolumna in polskie_kolumny:
                wiersz[kolumna] = polskie_dane.get(kolumna, 'N/A')
            
            writer.writerow(wiersz)


class LoggerDecyzjiStrategicznych(PolskiLoggerBazowy):
    """Logger dla decyzji strategicznych"""
    
    KOLUMNY = [
        'timestamp', 'turn', 'nation', 'decision_type', 'decision_scope', 'priority_level',
        'context_factors', 'expected_outcome', 'actual_outcome', 'confidence_level',
        'time_horizon', 'resource_commitment', 'alternative_considered', 'decision_rationale',
        'risk_assessment', 'success_probability', 'strategic_goal_alignment', 
        'vp_impact_projection', 'economic_impact'
    ]
    
    def __init__(self, katalog_sesji: Path):
        super().__init__(katalog_sesji)
        self.katalog = self.przygotuj_katalog('decyzje_strategiczne')
        # Prosty cache do deduplikacji wpisów strategicznych (klucz -> ostatnia_tura lub timestamp)
        self._dedupe_cache: Dict[str, Any] = {}
        self._dedupe_size_limit = 512
        
    def loguj(self, dane: Dict[str, Any]):
        """Loguje decyzję strategiczną"""
        dzisiaj = datetime.now().strftime("%Y%m%d")
        nazwa_pliku = f"decyzje_strategiczne_{dzisiaj}.csv"
        sciezka = self.katalog / nazwa_pliku
        
        # Dodanie timestamp jeśli brak
        if 'timestamp' not in dane:
            dane['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # WSTRZYKNIĘCIE NUMERU TURY (jeśli brak) z kontekstu
        if 'turn' not in dane or dane.get('turn') in (None, ''):
            try:
                from utils.turn_context import get_current_turn
                turn_no = get_current_turn()
                if turn_no:
                    dane['turn'] = turn_no
            except Exception:
                pass
        
        # Tłumaczenie enum values
        if 'decision_type' in dane:
            dane['decision_type'] = self.tlumacz_wartosc_enum('typy_decyzji', dane['decision_type'])
        if 'confidence_level' in dane:
            dane['confidence_level'] = self.tlumacz_wartosc_enum('poziomy_pewnosci', dane['confidence_level'])

        # DEDUPLIKACJA: pomiń duplikaty w obrębie tej samej tury dla tego samego klucza
        try:
            key_fields = (
                str(dane.get('decision_type', '')),
                str(dane.get('decision_scope', '')),
                str(dane.get('nation', '')),
                str(dane.get('context_factors', ''))
            )
            key = "|".join(key_fields)
            tura = dane.get('turn')
            last_val = self._dedupe_cache.get(key)
            if last_val is not None and (tura is not None and last_val == tura):
                # Duplikat w tej samej turze – pomijamy zapis
                return
            # Aktualizacja cache, ograniczenie rozmiaru
            self._dedupe_cache[key] = tura if tura is not None else dane.get('timestamp')
            if len(self._dedupe_cache) > self._dedupe_size_limit:
                # Proste czyszczenie: usuń 1/3 najstarszych kluczy
                try:
                    for k in list(self._dedupe_cache.keys())[: self._dedupe_size_limit // 3]:
                        self._dedupe_cache.pop(k, None)
                except Exception:
                    self._dedupe_cache.clear()
        except Exception:
            pass
        
        self.zapisz_wiersz_csv(sciezka, dane, self.KOLUMNY)


class LoggerAkcjiTaktycznych(PolskiLoggerBazowy):
    """Logger dla akcji taktycznych"""
    
    KOLUMNY = [
        'timestamp', 'turn', 'correlation_id', 'phase', 'nation', 'action_category', 'unit_primary', 
        'units_supporting', 'action_complexity', 'coordination_required', 'formation_type',
        'terrain_advantage', 'enemy_response_expected', 'success_indicators', 
        'execution_time_ms', 'micro_decisions_count', 'unit_synergy_score',
        'tactical_innovation', 'risk_mitigation', 'fallback_plan_ready',
        # DODATKOWE POLA DOT. ZAOPATRZENIA/PE (strukturalne)
        'resupply_budget_available', 'resupply_pe_spent', 'pe_spent_fuel', 'pe_spent_combat',
        'before_fuel', 'after_fuel', 'before_cv', 'after_cv', 'global_pe_remaining',
        'resupply_total_need',
        # Pola diagnostyczne
        'action_type', 'validate_status', 'error_code', 'human_rules_check',
        'unit_id', 'target_id', 'from_hex_q', 'from_hex_r', 'to_hex_q', 'to_hex_r',
        'ratio', 'threshold', 'decision', 'reason',
        # Nowe pola diagnostyczne ruchu i walki
        'nearest_reachable_dist', 'nearest_reachable_hex_q', 'nearest_reachable_hex_r', 'obstacle_hint',
        'threshold_adjusted', 'resupply_reason'
    ]
    
    def __init__(self, katalog_sesji: Path):
        super().__init__(katalog_sesji)
        self.katalog = self.przygotuj_katalog('akcje_taktyczne')
        
    def loguj(self, dane: Dict[str, Any]):
        """Loguje akcję taktyczną"""
        dzisiaj = datetime.now().strftime("%Y%m%d")
        nazwa_pliku = f"akcje_taktyczne_{dzisiaj}.csv"
        sciezka = self.katalog / nazwa_pliku
        
        if 'timestamp' not in dane:
            dane['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # WSTRZYKNIĘCIE NUMERU TURY (jeśli brak) z kontekstu
        if 'turn' not in dane or dane.get('turn') in (None, ''):
            try:
                from utils.turn_context import get_current_turn
                turn_no = get_current_turn()
                if turn_no:
                    dane['turn'] = turn_no
            except Exception:
                pass
        # WSTRZYKNIĘCIE correlation_id (jeśli dostępny)
        try:
            from utils.turn_context import get_correlation_id
            corr = get_correlation_id()
            if corr and 'correlation_id' not in dane:
                dane['correlation_id'] = corr
        except Exception:
            pass
        
        # Tłumaczenie kategorii akcji
        if 'action_category' in dane:
            dane['action_category'] = self.tlumacz_wartosc_enum('kategorie_akcji', dane['action_category'])
        
        self.zapisz_wiersz_csv(sciezka, dane, self.KOLUMNY)


class LoggerDecyzjiEkonomicznych(PolskiLoggerBazowy):
    """Logger dla decyzji ekonomicznych"""
    
    KOLUMNY = [
        'timestamp', 'turn', 'nation', 'budget_available', 'budget_allocated',
        'spending_category', 'cost_per_action', 'expected_roi', 'actual_roi',
        'opportunity_cost', 'budget_pressure_level', 'pe_efficiency_score',
        'resource_scarcity_factor', 'emergency_spending', 'investment_horizon',
        'cost_benefit_analysis', 'budget_variance', 'economic_strategy_alignment'
    ]
    
    def __init__(self, katalog_sesji: Path):
        super().__init__(katalog_sesji)
        self.katalog = self.przygotuj_katalog('decyzje_ekonomiczne')
        
    def loguj(self, dane: Dict[str, Any]):
        """Loguje decyzję ekonomiczną"""
        dzisiaj = datetime.now().strftime("%Y%m%d")
        nazwa_pliku = f"decyzje_ekonomiczne_{dzisiaj}.csv"
        sciezka = self.katalog / nazwa_pliku
        
        if 'timestamp' not in dane:
            dane['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # WSTRZYKNIĘCIE NUMERU TURY (jeśli brak) z kontekstu
        if 'turn' not in dane or dane.get('turn') in (None, ''):
            try:
                from utils.turn_context import get_current_turn
                turn_no = get_current_turn()
                if turn_no:
                    dane['turn'] = turn_no
            except Exception:
                pass
        
        # Tłumaczenie kategorii wydatków
        if 'spending_category' in dane:
            dane['spending_category'] = self.tlumacz_wartosc_enum('kategorie_wydatkow', dane['spending_category'])
        
        self.zapisz_wiersz_csv(sciezka, dane, self.KOLUMNY)


class LoggerAnalizyWywiadu(PolskiLoggerBazowy):
    """Logger dla analizy wywiadu"""
    
    KOLUMNY = [
        'timestamp', 'turn', 'nation', 'intelligence_type', 'source_reliability',
        'information_freshness', 'enemy_units_spotted', 'enemy_movements_predicted',
        'threat_assessment_change', 'counter_intelligence_detected', 'strategic_surprise_probability',
        'information_gaps', 'intel_confidence_level', 'actionable_intelligence',
        'intelligence_sharing', 'prediction_accuracy_historical', 'enemy_pattern_recognition',
        'deception_likelihood'
    ]
    
    def __init__(self, katalog_sesji: Path):
        super().__init__(katalog_sesji)
        self.katalog = self.przygotuj_katalog('analiza_wywiadu')
        
    def loguj(self, dane: Dict[str, Any]):
        """Loguje analizę wywiadu"""
        dzisiaj = datetime.now().strftime("%Y%m%d")
        nazwa_pliku = f"analiza_wywiadu_{dzisiaj}.csv"
        sciezka = self.katalog / nazwa_pliku
        
        if 'timestamp' not in dane:
            dane['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # WSTRZYKNIĘCIE NUMERU TURY (jeśli brak) z kontekstu
        if 'turn' not in dane or dane.get('turn') in (None, ''):
            try:
                from utils.turn_context import get_current_turn
                turn_no = get_current_turn()
                if turn_no:
                    dane['turn'] = turn_no
            except Exception:
                pass
        
        # Tłumaczenie typu informacji
        if 'intelligence_type' in dane:
            dane['intelligence_type'] = self.tlumacz_wartosc_enum('typy_wywiadu', dane['intelligence_type'])
        
        self.zapisz_wiersz_csv(sciezka, dane, self.KOLUMNY)


class LoggerWydajnosci(PolskiLoggerBazowy):
    """Logger dla metryk wydajności AI"""
    
    KOLUMNY = [
        'timestamp', 'turn', 'nation', 'decision_latency_ms', 'calculations_performed',
        'algorithms_used', 'memory_usage_mb', 'cpu_utilization_pct', 'decision_tree_depth',
        'alternatives_evaluated', 'optimization_iterations', 'ai_confidence_score',
        'learning_rate_applied', 'model_accuracy_current', 'prediction_success_rate',
        'adaptive_behavior_triggered', 'error_recovery_attempts', 'system_stability_index'
    ]
    
    def __init__(self, katalog_sesji: Path):
        super().__init__(katalog_sesji)
        self.katalog = self.przygotuj_katalog('wydajnosc_ai')
        
    def loguj(self, dane: Dict[str, Any]):
        """Loguje metryki wydajności"""
        dzisiaj = datetime.now().strftime("%Y%m%d")
        nazwa_pliku = f"wydajnosc_ai_{dzisiaj}.csv"
        sciezka = self.katalog / nazwa_pliku
        
        if 'timestamp' not in dane:
            dane['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # WSTRZYKNIĘCIE NUMERU TURY (jeśli brak) z kontekstu
        if 'turn' not in dane or dane.get('turn') in (None, ''):
            try:
                from utils.turn_context import get_current_turn
                turn_no = get_current_turn()
                if turn_no:
                    dane['turn'] = turn_no
            except Exception:
                pass
        
        self.zapisz_wiersz_csv(sciezka, dane, self.KOLUMNY)


class LoggerAnalizyZwyciestwa(PolskiLoggerBazowy):
    """Logger dla analizy zwycięstwa"""
    
    KOLUMNY = [
        'timestamp', 'turn', 'nation', 'vp_trajectory', 'vp_gap_analysis',
        'victory_probability', 'path_to_victory_identified', 'victory_conditions_progress',
        'time_pressure_factor', 'endgame_strategy_active', 'victory_point_opportunities',
        'elimination_targets_priority', 'key_points_strategic_value', 'victory_timeline_projection',
        'defeat_risk_assessment'
    ]
    
    def __init__(self, katalog_sesji: Path):
        super().__init__(katalog_sesji)
        self.katalog = self.przygotuj_katalog('analiza_zwyciestwa')
        
    def loguj(self, dane: Dict[str, Any]):
        """Loguje analizę zwycięstwa"""
        dzisiaj = datetime.now().strftime("%Y%m%d")
        nazwa_pliku = f"analiza_zwyciestwa_{dzisiaj}.csv"
        sciezka = self.katalog / nazwa_pliku
        
        if 'timestamp' not in dane:
            dane['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # WSTRZYKNIĘCIE NUMERU TURY (jeśli brak) z kontekstu
        if 'turn' not in dane or dane.get('turn') in (None, ''):
            try:
                from utils.turn_context import get_current_turn
                turn_no = get_current_turn()
                if turn_no:
                    dane['turn'] = turn_no
            except Exception:
                pass
        
        self.zapisz_wiersz_csv(sciezka, dane, self.KOLUMNY)


class LoggerWalk(PolskiLoggerBazowy):
    """Logger dla zdarzeń walki (CV przed/po)"""

    KOLUMNY = [
        'timestamp', 'turn', 'correlation_id', 'nation', 'attacker_id', 'defender_id',
        'attacker_cv_before', 'attacker_cv_after', 'defender_cv_before', 'defender_cv_after',
        'outcome', 'hex_q', 'hex_r', 'notes'
    ]

    def __init__(self, katalog_sesji: Path):
        super().__init__(katalog_sesji)
        self.katalog = self.przygotuj_katalog('walka_ai')

    def loguj(self, dane: Dict[str, Any]):
        """Loguje zdarzenie walki z CV przed/po"""
        dzisiaj = datetime.now().strftime("%Y%m%d")
        nazwa_pliku = f"walka_ai_{dzisiaj}.csv"
        sciezka = self.katalog / nazwa_pliku

        if 'timestamp' not in dane:
            dane['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # WSTRZYKNIĘCIE NUMERU TURY (jeśli brak) z kontekstu
        if 'turn' not in dane or dane.get('turn') in (None, ''):
            try:
                from utils.turn_context import get_current_turn
                turn_no = get_current_turn()
                if turn_no:
                    dane['turn'] = turn_no
            except Exception:
                pass
        # WSTRZYKNIĘCIE correlation_id (jeśli dostępny)
        try:
            from utils.turn_context import get_correlation_id
            corr = get_correlation_id()
            if corr and 'correlation_id' not in dane:
                dane['correlation_id'] = corr
        except Exception:
            pass

        self.zapisz_wiersz_csv(sciezka, dane, self.KOLUMNY)


class ZaawansowanyLoggerAI:
    """Główna klasa łącząca wszystkie loggery"""
    
    def __init__(self, katalog_sesji: Path):
        self.katalog_sesji = Path(katalog_sesji)
        
        # Inicjalizacja wszystkich loggerów
        self.loggery = {
            'strategiczne': LoggerDecyzjiStrategicznych(katalog_sesji),
            'taktyczne': LoggerAkcjiTaktycznych(katalog_sesji),
            'ekonomiczne': LoggerDecyzjiEkonomicznych(katalog_sesji),
            'wywiad': LoggerAnalizyWywiadu(katalog_sesji),
            'wydajnosc': LoggerWydajnosci(katalog_sesji),
            'zwyciestwo': LoggerAnalizyZwyciestwa(katalog_sesji),
            'walka': LoggerWalk(katalog_sesji)
        }
    
    def loguj_decyzje_strategiczna(self, dane: Dict[str, Any]):
        """Loguje decyzję strategiczną"""
        self.loggery['strategiczne'].loguj(dane)
        
    def loguj_akcje_taktyczna(self, dane: Dict[str, Any]):
        """Loguje akcję taktyczną"""
        self.loggery['taktyczne'].loguj(dane)
        
    def loguj_decyzje_ekonomiczna(self, dane: Dict[str, Any]):
        """Loguje decyzję ekonomiczną"""
        self.loggery['ekonomiczne'].loguj(dane)
        
    def loguj_analize_wywiadu(self, dane: Dict[str, Any]):
        """Loguje analizę wywiadu"""
        self.loggery['wywiad'].loguj(dane)
        
    def loguj_wydajnosc(self, dane: Dict[str, Any]):
        """Loguje metryki wydajności"""
        self.loggery['wydajnosc'].loguj(dane)
        
    def loguj_analize_zwyciestwa(self, dane: Dict[str, Any]):
        """Loguje analizę zwycięstwa"""
        self.loggery['zwyciestwo'].loguj(dane)

    def loguj_walke(self, dane: Dict[str, Any]):
        """Loguje zdarzenie walki (CV przed/po)"""
        self.loggery['walka'].loguj(dane)
    
    def pobierz_statystyki(self) -> Dict[str, Dict[str, Any]]:
        """Zwraca statystyki wszystkich logów"""
        stats = {}
        dzisiaj = datetime.now().strftime("%Y%m%d")
        
        for typ, logger in self.loggery.items():
            nazwa_pliku = f"{NAZWY_PLIKOW[typ]}_{dzisiaj}.csv"
            sciezka = logger.katalog / nazwa_pliku
            
            if sciezka.exists():
                # Liczenie wierszy
                with open(sciezka, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    wiersze = sum(1 for row in reader) - 1  # -1 dla nagłówka
                
                stats[typ] = {
                    'plik': nazwa_pliku,
                    'wiersze': wiersze,
                    'sciezka': str(sciezka)
                }
            else:
                stats[typ] = {
                    'plik': nazwa_pliku,
                    'wiersze': 0,
                    'sciezka': 'Brak pliku'
                }
        
        return stats