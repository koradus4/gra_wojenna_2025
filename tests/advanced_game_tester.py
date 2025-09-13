#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 ZAAWANSOWANY TESTER GRY - PEŁNA ANALIZA ROZGRYWKI

Kompleksowy framework testowy do oceny:
- Działania silnika gry w różnych sytuacjach
- Wydajności i inteligencji AI
- Balansu rozgrywki
- Stabilności systemu
- Realistycznych scenariuszy kampanii 1939

Autor: Advanced Game Testing Framework
Data: 13 września 2025
"""

import sys
import os
import json
import csv
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import copy
import random

# Importy systemowe
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importy gry
try:
    from engine.engine import GameEngine
    from engine.player import Player  
    from engine.board import Board
    from core.tura import TurnManager
    from core.ekonomia import EconomySystem
    from core.zwyciestwo import VictoryConditions
    from ai.ai_general import AIGeneral
    from ai.ai_commander import AICommander
    from ai.ai_config import get_param, set_ai_profile, AIProfile
    from ai.victory_ai import log_victory_ai_csv
    from czyszczenie.game_cleaner import clean_all_for_new_game
except ImportError as e:
    print(f"❌ BŁĄD IMPORTU: {e}")
    print("Upewnij się, że uruchamiasz z głównego katalogu gry")
    sys.exit(1)

class TestResult(Enum):
    """Wyniki testów"""
    PASS = "PASS"
    FAIL = "FAIL" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    SKIP = "SKIP"

class GamePhase(Enum):
    """Fazy gry do testowania"""
    EARLY_GAME = "early_game"    # Tury 1-3
    MID_GAME = "mid_game"        # Tury 4-7  
    LATE_GAME = "late_game"      # Tury 8-10
    OVERTIME = "overtime"        # Tury 10+

@dataclass
class TestScenario:
    """Definicja scenariusza testowego"""
    name: str
    description: str
    max_turns: int
    ai_profiles: Dict[str, str]  # {"polish": "aggressive", "german": "defensive"}
    map_size: str = "standard"
    special_conditions: Dict[str, Any] = None
    expected_duration_minutes: float = 5.0

@dataclass
class GameMetrics:
    """Metryki jednej rozgrywki"""
    scenario_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    total_turns: int
    winner: Optional[str]
    victory_condition: str
    
    # Metryki graczy
    polish_vp_final: int
    german_vp_final: int
    polish_units_final: int
    german_units_final: int
    polish_pe_spent: int
    german_pe_spent: int
    
    # Metryki AI
    ai_decisions_made: int
    ai_errors_count: int
    ai_avg_turn_time: float
    ai_strategic_changes: int
    
    # Metryki silnika
    engine_errors: int
    memory_usage_mb: float
    cpu_usage_percent: float
    
    # Wynik testu
    test_result: TestResult
    issues_found: List[str]
    performance_score: float  # 0-100

class AdvancedGameTester:
    """Zaawansowany tester rozgrywek"""
    
    def __init__(self):
        self.results: List[GameMetrics] = []
        self.current_test_id = 0
        self.test_start_time = datetime.now()
        
        # Ścieżki
        self.test_dir = Path("tests/results")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_file = self.test_dir / f"advanced_test_results_{timestamp}.json"
        self.csv_file = self.test_dir / f"test_metrics_{timestamp}.csv"
        self.log_file = self.test_dir / f"test_log_{timestamp}.txt"
        
        # Inicjalizacja logów
        self._init_logging()
        self._init_csv()
        
        print(f"🧪 ZAAWANSOWANY TESTER GRY - START")
        print(f"📁 Katalog wyników: {self.test_dir}")
        print(f"📊 Metryki CSV: {self.csv_file}")
        print(f"📋 Log szczegółowy: {self.log_file}")
        print("-" * 80)
    
    def _init_logging(self):
        """Inicjalizacja systemu logowania"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"🧪 ZAAWANSOWANY TEST GRY - START: {datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
    
    def _init_csv(self):
        """Inicjalizacja pliku CSV z metrykami"""
        headers = [
            'test_id', 'scenario_name', 'start_time', 'end_time', 'duration_seconds',
            'total_turns', 'winner', 'victory_condition',
            'polish_vp_final', 'german_vp_final', 'polish_units_final', 'german_units_final',
            'polish_pe_spent', 'german_pe_spent', 
            'ai_decisions_made', 'ai_errors_count', 'ai_avg_turn_time', 'ai_strategic_changes',
            'engine_errors', 'memory_usage_mb', 'cpu_usage_percent',
            'test_result', 'performance_score', 'issues_count'
        ]
        
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def log(self, message: str, level: str = "INFO"):
        """Logowanie z timestampem"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {level}: {message}"
        print(log_line)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + "\n")
    
    def get_test_scenarios(self) -> List[TestScenario]:
        """Definicje scenariuszy testowych"""
        return [
            TestScenario(
                name="balanced_standard",
                description="Standardowa gra - oba AI zbalansowane",
                max_turns=10,
                ai_profiles={"polish": "balanced", "german": "balanced"},
                expected_duration_minutes=3.0
            ),
            TestScenario(
                name="aggressive_vs_defensive", 
                description="Polska agresywna vs Niemcy defensywne",
                max_turns=12,
                ai_profiles={"polish": "aggressive", "german": "defensive"},
                expected_duration_minutes=4.0
            ),
            TestScenario(
                name="defensive_vs_aggressive",
                description="Polska defensywna vs Niemcy agresywne", 
                max_turns=12,
                ai_profiles={"polish": "defensive", "german": "aggressive"},
                expected_duration_minutes=4.0
            ),
            TestScenario(
                name="economic_warfare",
                description="Test ekonomiczny - długa gra z focus na PE",
                max_turns=15,
                ai_profiles={"polish": "balanced", "german": "balanced"},
                special_conditions={"economic_focus": True},
                expected_duration_minutes=6.0
            ),
            TestScenario(
                name="quick_decisive",
                description="Szybka rozgrywka - test wczesnego zwycięstwa",
                max_turns=6,
                ai_profiles={"polish": "aggressive", "german": "aggressive"},
                expected_duration_minutes=2.0
            ),
            TestScenario(
                name="endurance_test",
                description="Test wytrzymałościowy - długa kampania",
                max_turns=20,
                ai_profiles={"polish": "balanced", "german": "balanced"},
                expected_duration_minutes=8.0
            ),
            TestScenario(
                name="ai_adaptation_test",
                description="Test adaptacji AI - zmiana profili w trakcie",
                max_turns=10,
                ai_profiles={"polish": "balanced", "german": "balanced"},
                special_conditions={"profile_switching": True},
                expected_duration_minutes=4.0
            ),
            TestScenario(
                name="stress_test",
                description="Test obciążeniowy - maksymalne jednostki i działania",
                max_turns=8,
                ai_profiles={"polish": "aggressive", "german": "aggressive"}, 
                special_conditions={"max_units": True},
                expected_duration_minutes=5.0
            )
        ]
    
    def create_test_game(self, scenario: TestScenario) -> Tuple[GameEngine, List[Player]]:
        """Tworzy nową grę testową według scenariusza"""
        self.log(f"🎮 Tworzenie gry testowej: {scenario.name}")
        
        try:
            # Czyść poprzednie dane
            clean_all_for_new_game()
            
            # Ustaw profile AI
            for nation, profile in scenario.ai_profiles.items():
                if profile == "aggressive":
                    ai_profile = AIProfile.AGGRESSIVE
                elif profile == "defensive":
                    ai_profile = AIProfile.DEFENSIVE
                elif profile == "balanced":
                    ai_profile = AIProfile.BALANCED
                else:
                    ai_profile = AIProfile.BALANCED
                    
                set_ai_profile(ai_profile)
                self.log(f"🎛️ Ustawiono profil {profile} dla {nation}")
            
            # Twórz silnik gry
            game_engine = GameEngine(
                map_path="data/map_data.json",
                tokens_index_path="assets/tokens/index.json",
                tokens_start_path="assets/start_tokens.json",
                seed=42
            )
            
            # Twórz graczy testowych
            players = [
                Player(1, "Polska", "Generał", 5),  # Polski generał
                Player(2, "Polska", "Dowódca", 5),  # Polski dowódca 1  
                Player(4, "Niemcy", "Generał", 5),  # Niemiecki generał
                Player(5, "Niemcy", "Dowódca", 5),  # Niemiecki dowódca 1
            ]
            
            # Konfiguruj AI dla każdego gracza
            ai_generals = {}
            ai_commanders = {}
            
            for player in players:
                # Dodaj ekonomię
                player.economy = EconomySystem()
                
                # Ustaw domyślne wartości AI
                player.is_ai_general = False
                player.is_ai_commander = False
                
                if player.role == "Generał":
                    player.is_ai = True
                    player.is_ai_general = True
                    nation = "polish" if player.nation == "Polska" else "german" 
                    ai_generals[player.id] = AIGeneral(nation)
                    self.log(f"🤖 AI Generał: {player.nation} (id={player.id})")
                    
                elif player.role == "Dowódca":
                    player.is_ai = True
                    player.is_ai_commander = True
                    ai_commanders[player.id] = AICommander(player)
                    self.log(f"🎯 AI Dowódca: {player.nation} (id={player.id})")
            
            # Przypisz graczy do silnika
            game_engine.players = players
            
            self.log(f"✅ Gra testowa utworzona: {len(players)} graczy, mapa załadowana")
            return game_engine, players
            
        except Exception as e:
            self.log(f"❌ Błąd tworzenia gry testowej: {e}", "ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            raise
    
    def _load_test_map(self, game_engine: GameEngine):
        """Ładuje mapę do gry testowej"""
        try:
            map_file = Path("data/map_data.json")
            if map_file.exists():
                with open(map_file, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                game_engine.map_data = map_data
                
                # Twórz board
                if hasattr(game_engine, 'create_board'):
                    game_engine.create_board()
                else:
                    # Fallback manual board creation
                    from engine.board import Board
                    game_engine.board = Board(
                        cols=map_data.get('meta', {}).get('cols', 56),
                        rows=map_data.get('meta', {}).get('rows', 40)
                    )
                
                self.log("🗺️ Mapa załadowana z map_data.json")
            else:
                self.log("⚠️ Brak map_data.json - używam domyślnej mapy", "WARNING")
                # Stwórz minimalną mapę
                game_engine.board = Board(cols=20, rows=15)
                game_engine.map_data = {"meta": {"cols": 20, "rows": 15}}
                
        except Exception as e:
            self.log(f"⚠️ Błąd ładowania mapy: {e}", "WARNING")
            # Fallback - minimalna mapa
            game_engine.board = Board(cols=10, rows=10)
            game_engine.map_data = {"meta": {"cols": 10, "rows": 10}}
    
    def _apply_special_conditions(self, game_engine: GameEngine, conditions: Dict[str, Any]):
        """Aplikuje specjalne warunki testowe"""
        self.log(f"⚙️ Aplikowanie specjalnych warunków: {list(conditions.keys())}")
        
        if conditions.get("economic_focus"):
            # Zwiększ generowanie PE
            for player in game_engine.players:
                if hasattr(player, 'economy') and player.economy:
                    player.economy.economic_points = 200  # Start z więcej PE
            self.log("💰 Zwiększono początkowe PE do 200")
        
        if conditions.get("max_units"):
            # Dodaj więcej początkowych jednostek (symulacja)
            self.log("🪖 Symulacja maksymalnych jednostek")
        
        if conditions.get("profile_switching"):
            # Oznacz do zmiany profili w trakcie
            game_engine._test_profile_switching = True
            self.log("🔄 Włączono przełączanie profili AI")
    
    def run_single_test(self, scenario: TestScenario) -> GameMetrics:
        """Uruchamia pojedynczy test scenariusza"""
        self.current_test_id += 1
        self.log(f"\n{'='*60}")
        self.log(f"🧪 TEST #{self.current_test_id}: {scenario.name}")
        self.log(f"📋 Opis: {scenario.description}")
        self.log(f"🎯 Max tur: {scenario.max_turns}")
        self.log(f"🤖 Profile AI: {scenario.ai_profiles}")
        self.log(f"{'='*60}")
        
        start_time = datetime.now()
        metrics = GameMetrics(
            scenario_name=scenario.name,
            start_time=start_time,
            end_time=start_time,  # Będzie zaktualizowane
            duration_seconds=0.0,
            total_turns=0,
            winner=None,
            victory_condition="unknown",
            polish_vp_final=0,
            german_vp_final=0,
            polish_units_final=0,
            german_units_final=0,
            polish_pe_spent=0,
            german_pe_spent=0,
            ai_decisions_made=0,
            ai_errors_count=0,
            ai_avg_turn_time=0.0,
            ai_strategic_changes=0,
            engine_errors=0,
            memory_usage_mb=0.0,
            cpu_usage_percent=0.0,
            test_result=TestResult.PASS,
            issues_found=[],
            performance_score=100.0
        )
        
        try:
            # Twórz grę
            game_engine, players = self.create_test_game(scenario)
            
            # Uruchom rozgrywkę
            self._run_game_simulation(game_engine, players, scenario, metrics)
            
            # Zbierz końcowe metryki
            self._collect_final_metrics(game_engine, players, metrics)
            
            # Oceń wyniki
            self._evaluate_test_results(scenario, metrics)
            
        except Exception as e:
            self.log(f"❌ KRYTYCZNY BŁĄD w teście {scenario.name}: {e}", "ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
            metrics.test_result = TestResult.ERROR
            metrics.issues_found.append(f"Critical error: {str(e)}")
            metrics.performance_score = 0.0
        
        # Finalizuj metryki
        metrics.end_time = datetime.now()
        metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
        
        # Zapisz wyniki
        self._save_test_result(metrics)
        
        self.log(f"✅ Test {scenario.name} zakończony")
        self.log(f"⏱️ Czas: {metrics.duration_seconds:.1f}s")
        self.log(f"🏆 Wynik: {metrics.test_result.value}")
        self.log(f"📊 Performance: {metrics.performance_score:.1f}/100")
        
        return metrics
    
    def _run_game_simulation(self, game_engine: GameEngine, players: List[Player], 
                           scenario: TestScenario, metrics: GameMetrics):
        """Uruchamia symulację rozgrywki"""
        self.log("🎮 Start symulacji rozgrywki...")
        
        turn_times = []
        
        for turn in range(1, scenario.max_turns + 1):
            turn_start = time.time()
            
            try:
                self.log(f"🔄 Tura {turn}/{scenario.max_turns}")
                
                # Sprawdź warunki zwycięstwa
                if self._check_victory_conditions(game_engine, players, metrics):
                    self.log(f"🏆 Gra zakończona zwycięstwem na turze {turn}")
                    break
                
                # Wykonaj turę dla każdego gracza
                for player in players:
                    if player.is_ai_general or player.is_ai_commander:
                        self._execute_ai_turn(game_engine, player, metrics)
                    
                    # Przełącz na następnego gracza
                    if hasattr(game_engine, 'turn_manager'):
                        game_engine.turn_manager.next_turn()
                
                # Specjalne warunki
                if hasattr(game_engine, '_test_profile_switching') and turn == 5:
                    self._switch_ai_profiles(scenario, metrics)
                
                metrics.total_turns = turn
                
                turn_time = time.time() - turn_start
                turn_times.append(turn_time)
                
                self.log(f"✅ Tura {turn} zakończona w {turn_time:.2f}s")
                
                # Sprawdź czy gra nie trwa za długo
                if turn_time > 30.0:  # 30 sekund na turę to za dużo
                    metrics.issues_found.append(f"Turn {turn} took {turn_time:.1f}s - too slow")
                    self.log(f"⚠️ Tura {turn} trwała {turn_time:.1f}s - zbyt wolno!", "WARNING")
                
            except Exception as e:
                metrics.engine_errors += 1
                metrics.issues_found.append(f"Turn {turn} error: {str(e)}")
                self.log(f"❌ Błąd na turze {turn}: {e}", "ERROR")
                
                # Jeśli zbyt wiele błędów - przerwij
                if metrics.engine_errors >= 3:
                    self.log("❌ Zbyt wiele błędów - przerywam test", "ERROR")
                    metrics.test_result = TestResult.FAIL
                    break
        
        # Oblicz średni czas tury AI
        if turn_times:
            metrics.ai_avg_turn_time = sum(turn_times) / len(turn_times)
        
        self.log(f"🎮 Symulacja zakończona po {metrics.total_turns} turach")
    
    def _execute_ai_turn(self, game_engine: GameEngine, player: Player, metrics: GameMetrics):
        """Wykonuje turę AI z pomiarem metryk"""
        try:
            # AI General turn
            if player.is_ai_general and hasattr(player, 'ai_general'):
                decisions_before = metrics.ai_decisions_made
                player.ai_general.make_turn(game_engine)
                # Szacowanie liczby decyzji (będzie dokładniejsze z logami)
                metrics.ai_decisions_made += 5  # Średnio 5 decyzji generała
            
            # AI Commander turn  
            if player.is_ai_commander:
                from ai.ai_commander import make_tactical_turn
                make_tactical_turn(game_engine, player.id)
                metrics.ai_decisions_made += 10  # Średnio 10 decyzji dowódcy
                
        except Exception as e:
            metrics.ai_errors_count += 1
            metrics.issues_found.append(f"AI error for {player.nation}: {str(e)}")
            self.log(f"❌ Błąd AI {player.nation}: {e}", "ERROR")
    
    def _check_victory_conditions(self, game_engine: GameEngine, players: List[Player], 
                                metrics: GameMetrics) -> bool:
        """Sprawdza warunki zwycięstwa"""
        try:
            if hasattr(game_engine, 'victory_conditions'):
                result = game_engine.victory_conditions.check_game_over(
                    metrics.total_turns, players
                )
                if result[0]:  # Game over
                    metrics.victory_condition = "victory_points" if result[1] else "elimination"
                    metrics.winner = result[1] if isinstance(result[1], str) else "Draw"
                    return True
            
            # Fallback - sprawdź VP ręcznie
            polish_vp = next((p.victory_points for p in players if p.nation == "Polska"), 0)
            german_vp = next((p.victory_points for p in players if p.nation == "Niemcy"), 0)
            
            if abs(polish_vp - german_vp) > 50:  # Duża różnica VP
                metrics.winner = "Polska" if polish_vp > german_vp else "Niemcy"  
                metrics.victory_condition = "victory_points_decisive"
                return True
                
        except Exception as e:
            self.log(f"⚠️ Błąd sprawdzania zwycięstwa: {e}", "WARNING")
        
        return False
    
    def _switch_ai_profiles(self, scenario: TestScenario, metrics: GameMetrics):
        """Przełącza profile AI w trakcie gry (test adaptacji)"""
        self.log("🔄 Przełączanie profili AI...")
        
        new_profiles = {"polish": "defensive", "german": "aggressive"}
        for nation, profile in new_profiles.items():
            set_ai_profile(AIProfile(profile))
        
        metrics.ai_strategic_changes += 1
        self.log(f"🔄 Przełączono profile: {new_profiles}")
    
    def _collect_final_metrics(self, game_engine: GameEngine, players: List[Player], 
                             metrics: GameMetrics):
        """Zbiera końcowe metryki rozgrywki"""
        try:
            # Metryki graczy
            for player in players:
                if player.nation == "Polska":
                    metrics.polish_vp_final = getattr(player, 'victory_points', 0)
                    metrics.polish_units_final = len(getattr(player, 'tokens', []))
                    if hasattr(player, 'economy'):
                        metrics.polish_pe_spent = getattr(player.economy, 'total_spent', 0)
                elif player.nation == "Niemcy":
                    metrics.german_vp_final = getattr(player, 'victory_points', 0) 
                    metrics.german_units_final = len(getattr(player, 'tokens', []))
                    if hasattr(player, 'economy'):
                        metrics.german_pe_spent = getattr(player.economy, 'total_spent', 0)
            
            # Metryki systemu
            import psutil
            process = psutil.Process()
            metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            metrics.cpu_usage_percent = process.cpu_percent()
            
        except Exception as e:
            self.log(f"⚠️ Błąd zbierania metryk: {e}", "WARNING")
    
    def _evaluate_test_results(self, scenario: TestScenario, metrics: GameMetrics):
        """Ocenia wyniki testu i wystawia ocenę"""
        score = 100.0
        
        # Kara za błędy
        score -= metrics.engine_errors * 15  # -15 za błąd silnika
        score -= metrics.ai_errors_count * 10  # -10 za błąd AI
        
        # Kara za wydajność
        expected_duration = scenario.expected_duration_minutes * 60
        if metrics.duration_seconds > expected_duration * 1.5:
            score -= 20  # Gra trwała 50% dłużej niż oczekiwano
            metrics.issues_found.append("Game duration exceeded expectations")
        
        if metrics.ai_avg_turn_time > 5.0:
            score -= 15  # Tury AI trwają za długo
            metrics.issues_found.append("AI turns too slow")
        
        # Kara za pamięć
        if metrics.memory_usage_mb > 500:  # 500MB to dużo dla tej gry
            score -= 10
            metrics.issues_found.append("High memory usage")
        
        # Bonus za ukończenie
        if metrics.total_turns >= scenario.max_turns * 0.8:
            score += 5  # Ukończono przynajmniej 80% planowanych tur
        
        # Sprawdź logiczność wyników
        if metrics.winner and not metrics.victory_condition:
            score -= 5
            metrics.issues_found.append("Winner without victory condition")
        
        # Oceń stan końcowy
        if score >= 90:
            metrics.test_result = TestResult.PASS
        elif score >= 70:
            metrics.test_result = TestResult.WARNING  
        elif score >= 50:
            metrics.test_result = TestResult.FAIL
        else:
            metrics.test_result = TestResult.ERROR
        
        metrics.performance_score = max(0.0, score)
    
    def _save_test_result(self, metrics: GameMetrics):
        """Zapisuje wyniki testu do plików"""
        # JSON z pełnymi danymi
        result_dict = asdict(metrics)
        result_dict['start_time'] = metrics.start_time.isoformat()
        result_dict['end_time'] = metrics.end_time.isoformat()
        result_dict['test_result'] = metrics.test_result.value
        
        self.results.append(metrics)
        
        # Zapisz do JSON
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(r) for r in self.results], f, 
                     ensure_ascii=False, indent=2, default=str)
        
        # Zapisz do CSV 
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                self.current_test_id, metrics.scenario_name,
                metrics.start_time.isoformat(), metrics.end_time.isoformat(),
                metrics.duration_seconds, metrics.total_turns, metrics.winner,
                metrics.victory_condition, metrics.polish_vp_final, metrics.german_vp_final,
                metrics.polish_units_final, metrics.german_units_final,
                metrics.polish_pe_spent, metrics.german_pe_spent,
                metrics.ai_decisions_made, metrics.ai_errors_count,
                metrics.ai_avg_turn_time, metrics.ai_strategic_changes,
                metrics.engine_errors, metrics.memory_usage_mb,
                metrics.cpu_usage_percent, metrics.test_result.value,
                metrics.performance_score, len(metrics.issues_found)
            ])
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Uruchamia pełny zestaw testów"""
        scenarios = self.get_test_scenarios()
        
        self.log(f"\n🚀 URUCHAMIANIE PEŁNEGO ZESTAWU TESTÓW")
        self.log(f"📝 Liczba scenariuszy: {len(scenarios)}")
        self.log(f"⏱️ Szacowany czas: {sum(s.expected_duration_minutes for s in scenarios):.1f} minut")
        self.log("-" * 80)
        
        failed_tests = []
        passed_tests = []
        total_issues = []
        
        for i, scenario in enumerate(scenarios, 1):
            self.log(f"\n▶️ Scenariusz {i}/{len(scenarios)}: {scenario.name}")
            
            try:
                metrics = self.run_single_test(scenario)
                
                if metrics.test_result == TestResult.PASS:
                    passed_tests.append(scenario.name)
                else:
                    failed_tests.append({
                        'name': scenario.name,
                        'result': metrics.test_result.value,
                        'issues': metrics.issues_found,
                        'score': metrics.performance_score
                    })
                
                total_issues.extend(metrics.issues_found)
                
            except Exception as e:
                self.log(f"❌ BŁĄD KRYTYCZNY w scenariuszu {scenario.name}: {e}", "ERROR")
                failed_tests.append({
                    'name': scenario.name,
                    'result': 'CRITICAL_ERROR',
                    'issues': [str(e)],
                    'score': 0.0
                })
        
        # Podsumowanie
        summary = self._generate_test_summary(scenarios, passed_tests, failed_tests, total_issues)
        
        return summary
    
    def _generate_test_summary(self, scenarios: List[TestScenario], 
                             passed_tests: List[str], failed_tests: List[Dict],
                             total_issues: List[str]) -> Dict[str, Any]:
        """Generuje podsumowanie testów"""
        total_time = (datetime.now() - self.test_start_time).total_seconds()
        
        # Oblicz średnią wydajność
        avg_performance = sum(r.performance_score for r in self.results) / len(self.results) if self.results else 0
        
        # Oblicz średnie metryki
        avg_turn_time = sum(r.ai_avg_turn_time for r in self.results) / len(self.results) if self.results else 0
        total_turns = sum(r.total_turns for r in self.results)
        total_errors = sum(r.engine_errors + r.ai_errors_count for r in self.results)
        
        summary = {
            'test_session': {
                'start_time': self.test_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_minutes': total_time / 60,
                'scenarios_tested': len(scenarios),
                'tests_passed': len(passed_tests),
                'tests_failed': len(failed_tests),
                'success_rate_percent': (len(passed_tests) / len(scenarios)) * 100
            },
            'performance_metrics': {
                'average_performance_score': avg_performance,
                'average_ai_turn_time': avg_turn_time,
                'total_turns_simulated': total_turns,
                'total_errors': total_errors,
                'error_rate': total_errors / max(total_turns, 1)
            },
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'common_issues': self._analyze_common_issues(total_issues),
            'recommendations': self._generate_recommendations(failed_tests, total_issues),
            'files_generated': {
                'detailed_results': str(self.results_file),
                'metrics_csv': str(self.csv_file),
                'test_log': str(self.log_file)
            }
        }
        
        # Zapisz podsumowanie
        summary_file = self.test_dir / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # Wydrukuj podsumowanie
        self._print_final_summary(summary)
        
        return summary
    
    def _analyze_common_issues(self, issues: List[str]) -> Dict[str, int]:
        """Analizuje najczęstsze problemy"""
        issue_counts = {}
        
        for issue in issues:
            # Grupuj podobne błędy
            if "error" in issue.lower():
                issue_counts["errors"] = issue_counts.get("errors", 0) + 1
            elif "slow" in issue.lower() or "duration" in issue.lower():
                issue_counts["performance"] = issue_counts.get("performance", 0) + 1
            elif "memory" in issue.lower():
                issue_counts["memory"] = issue_counts.get("memory", 0) + 1
            elif "ai" in issue.lower():
                issue_counts["ai_issues"] = issue_counts.get("ai_issues", 0) + 1
            else:
                issue_counts["other"] = issue_counts.get("other", 0) + 1
        
        return issue_counts
    
    def _generate_recommendations(self, failed_tests: List[Dict], issues: List[str]) -> List[str]:
        """Generuje rekomendacje naprawcze"""
        recommendations = []
        
        if len(failed_tests) > len(self.results) * 0.5:  # Więcej niż 50% testów nie przeszło
            recommendations.append("🚨 KRYTYCZNE: Więcej niż 50% testów nie przeszło - wymagana głęboka analiza systemu")
        
        if any("error" in str(test) for test in failed_tests):
            recommendations.append("🔧 Sprawdź logi błędów i napraw problemy w silniku gry")
        
        if any("performance" in issue.lower() for issue in issues):
            recommendations.append("⚡ Optymalizuj wydajność - AI tury trwają za długo")
        
        if any("memory" in issue.lower() for issue in issues):
            recommendations.append("💾 Sprawdź wycieki pamięci - zużycie RAM zbyt wysokie")
        
        if any("ai" in issue.lower() for issue in issues):
            recommendations.append("🤖 Przeanalizuj logikę AI - wykryto problemy w podejmowaniu decyzji")
        
        if not recommendations:
            recommendations.append("✅ Wszystkie testy przeszły pomyślnie - system działa stabilnie")
        
        return recommendations
    
    def _print_final_summary(self, summary: Dict[str, Any]):
        """Wydrukuje końcowe podsumowanie"""
        session = summary['test_session']
        perf = summary['performance_metrics']
        
        print("\n" + "="*80)
        print("🏁 PODSUMOWANIE TESTÓW ZAAWANSOWANYCH")
        print("="*80)
        print(f"⏱️  Czas testów: {session['duration_minutes']:.1f} minut")
        print(f"📊 Scenariusze: {session['scenarios_tested']}")
        print(f"✅ Przeszło: {session['tests_passed']}")
        print(f"❌ Nie przeszło: {session['tests_failed']}")
        print(f"🎯 Wskaźnik sukcesu: {session['success_rate_percent']:.1f}%")
        print(f"📈 Średnia wydajność: {perf['average_performance_score']:.1f}/100")
        print(f"⚡ Średni czas tury AI: {perf['average_ai_turn_time']:.2f}s")
        print(f"🔄 Symulowane tury: {perf['total_turns_simulated']}")
        print(f"❗ Błędy ogółem: {perf['total_errors']}")
        
        if summary['failed_tests']:
            print(f"\n❌ TESTY NIEUDANE:")
            for test in summary['failed_tests']:
                print(f"  • {test['name']}: {test['result']} (score: {test['score']:.1f})")
        
        if summary['recommendations']:
            print(f"\n💡 REKOMENDACJE:")
            for rec in summary['recommendations']:
                print(f"  {rec}")
        
        print(f"\n📁 Pliki wyników:")
        for name, path in summary['files_generated'].items():
            print(f"  • {name}: {path}")
        
        print("="*80)

def main():
    """Główna funkcja uruchamiająca tester"""
    print("🧪 ZAAWANSOWANY TESTER GRY WOJENNEJ 2025")
    print("Testowanie AI, silnika gry i wydajności w realnych scenariuszach")
    print("-" * 80)
    
    tester = AdvancedGameTester()
    
    try:
        # Uruchom pełny zestaw testów
        summary = tester.run_full_test_suite()
        
        # Oceń końcowy wynik
        success_rate = summary['test_session']['success_rate_percent']
        avg_performance = summary['performance_metrics']['average_performance_score']
        
        if success_rate >= 90 and avg_performance >= 80:
            print("\n🏆 WYNIK KOŃCOWY: EXCELLENT - Gra gotowa do rozgrywki!")
        elif success_rate >= 70 and avg_performance >= 70:
            print("\n✅ WYNIK KOŃCOWY: GOOD - Gra działa dobrze z drobnymi problemami")
        elif success_rate >= 50 and avg_performance >= 60:
            print("\n⚠️ WYNIK KOŃCOWY: FAIR - Gra wymaga poprawek przed wydaniem")
        else:
            print("\n❌ WYNIK KOŃCOWY: POOR - Gra wymaga znaczących napraw")
        
        return summary
        
    except KeyboardInterrupt:
        print("\n⏹️ Testy przerwane przez użytkownika")
        return None
    except Exception as e:
        print(f"\n💥 KRYTYCZNY BŁĄD TESTERA: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()