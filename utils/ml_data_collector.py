"""
ML Data Collector - System zbierania danych do uczenia maszynowego
================================================================

Zbiera dane strategiczne, taktyczne i gameplay do osobnych plików CSV
w katalogu ai/logs/dane_ml/ - dane permanentne, nie podlegają rotacji sesji.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json

from .session_manager import LOGS_ROOT


class MLDataCollector:
    """System zbierania danych ML z automatyczną organizacją w kategorie"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logs_root = self.project_root / LOGS_ROOT
        self.ml_data_dir = self.logs_root / "dane_ml"
        self.strategiczne_dir = self.ml_data_dir / "strategiczne"
        self.taktyczne_dir = self.ml_data_dir / "taktyczne"
        self.gameplay_dir = self.ml_data_dir / "gameplay"

        # Utwórz wszystkie katalogi
        for directory in [self.strategiczne_dir, self.taktyczne_dir, self.gameplay_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def log_strategic_decision(self, player_id: str, decision: str, 
                             context: Dict[str, Any], outcome: str) -> bool:
        """
        Rejestruje decyzję strategiczną AI (generałowie)
        
        Args:
            player_id: ID gracza AI (np. "AI_General_Polish")
            decision: Typ decyzji (np. "attack_priority_change")  
            context: Kontekst decyzji (siły, zasoby, etc.)
            outcome: Wynik decyzji ("successful", "failed", "pending")
        """
        filepath = self.strategiczne_dir / "ai_decyzje_analiza.csv"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'player_id': player_id,
            'decision_type': decision,
            'context_json': json.dumps(context, ensure_ascii=False),
            'outcome': outcome,
            'game_phase': self._get_current_game_phase()
        }
        
        return self._write_csv_row(filepath, data, [
            'timestamp', 'player_id', 'decision_type', 'context_json', 'outcome', 'game_phase'
        ])
    
    def log_tactical_move(self, commander_id: str, action: str, 
                         target_info: Dict[str, Any], success_rate: float) -> bool:
        """
        Rejestruje ruch taktyczny AI (dowódcy)
        
        Args:
            commander_id: ID dowódcy AI (np. "AI_Commander_1_Polish")
            action: Typ akcji (np. "flanking_maneuver", "direct_assault")
            target_info: Info o celu (pozycja, siła, etc.)
            success_rate: Przewidywana szansa sukcesu (0.0-1.0)
        """
        filepath = self.taktyczne_dir / "combat_decisions.csv"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'commander_id': commander_id,
            'action_type': action,
            'target_info_json': json.dumps(target_info, ensure_ascii=False),
            'predicted_success': success_rate,
            'turn_number': self._get_current_turn()
        }
        
        return self._write_csv_row(filepath, data, [
            'timestamp', 'commander_id', 'action_type', 'target_info_json', 
            'predicted_success', 'turn_number'
        ])
    
    def log_gameplay_metrics(self, game_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Rejestruje metryki gameplay (balansing, wydajność)
        
        Args:
            game_id: ID sesji gry
            metrics: Słownik z metrykami (czas tury, akcje, wyniki)
        """
        filepath = self.gameplay_dir / "turn_statistics.csv"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'game_id': game_id,
            'metrics_json': json.dumps(metrics, ensure_ascii=False),
            'players_count': metrics.get('players_count', 0),
            'ai_count': metrics.get('ai_count', 0),
            'turn_duration_seconds': metrics.get('turn_duration', 0)
        }
        
        return self._write_csv_row(filepath, data, [
            'timestamp', 'game_id', 'metrics_json', 'players_count', 'ai_count', 'turn_duration_seconds'
        ])
    
    def log_force_ratio_trend(self, polish_strength: float, german_strength: float, 
                             trend_analysis: Dict[str, Any]) -> bool:
        """
        Rejestruje trendy stosunków sił militarnych
        
        Args:
            polish_strength: Siła polska (0.0-1.0)
            german_strength: Siła niemiecka (0.0-1.0)  
            trend_analysis: Analiza trendu (kierunek, prędkość zmian)
        """
        filepath = self.strategiczne_dir / "force_ratio_trends.csv"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'polish_strength': polish_strength,
            'german_strength': german_strength,
            'strength_ratio': polish_strength / german_strength if german_strength > 0 else 999,
            'trend_analysis_json': json.dumps(trend_analysis, ensure_ascii=False),
            'turn_number': self._get_current_turn()
        }
        
        return self._write_csv_row(filepath, data, [
            'timestamp', 'polish_strength', 'german_strength', 'strength_ratio', 
            'trend_analysis_json', 'turn_number'
        ])
    
    def _write_csv_row(self, filepath: Path, data: Dict[str, Any], fieldnames: list) -> bool:
        """Zapisuje wiersz do pliku CSV z automatycznym tworzeniem nagłówków"""
        try:
            file_exists = filepath.exists()
            
            with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Jeśli plik nie istnieje, zapisz nagłówki
                if not file_exists:
                    writer.writeheader()
                    print(f"[ML_DATA] Utworzono nowy plik: {filepath.name}")
                
                writer.writerow(data)
                return True
                
        except Exception as e:
            print(f"[ML_DATA] Błąd zapisu do {filepath.name}: {e}")
            return False
    
    def _get_current_game_phase(self) -> str:
        """Określa aktualną fazę gry (early/mid/late)"""
        # TODO: Integracja z TurnManager
        return "unknown"
    
    def _get_current_turn(self) -> int:
        """Zwraca numer aktualnej tury"""
        # TODO: Integracja z TurnManager  
        return 0
    
    def get_ml_data_stats(self) -> Dict[str, int]:
        """Zwraca statystyki zebranych danych ML"""
        stats = {
            'strategiczne_pliki': 0,
            'taktyczne_pliki': 0,
            'gameplay_pliki': 0,
            'total_files': 0
        }
        
        for category_dir, key in [
            (self.strategiczne_dir, 'strategiczne_pliki'),
            (self.taktyczne_dir, 'taktyczne_pliki'), 
            (self.gameplay_dir, 'gameplay_pliki')
        ]:
            if category_dir.exists():
                csv_files = list(category_dir.glob('*.csv'))
                stats[key] = len(csv_files)
                stats['total_files'] += len(csv_files)
        
        return stats


# Singleton instance dla łatwego użycia
_ml_collector_instance = None

def get_ml_collector() -> MLDataCollector:
    """Zwraca singleton instance MLDataCollector"""
    global _ml_collector_instance
    if _ml_collector_instance is None:
        _ml_collector_instance = MLDataCollector()
    return _ml_collector_instance


if __name__ == "__main__":
    # Test MLDataCollector
    print("🧪 TEST ML DATA COLLECTOR")
    print("-" * 50)
    
    collector = MLDataCollector()
    
    # Test 1: Dane strategiczne
    print("📊 Test danych strategicznych...")
    success = collector.log_strategic_decision(
        player_id="AI_General_Polish_TEST",
        decision="prioritize_defense",
        context={"enemy_pressure": 0.8, "own_resources": 0.6, "turn": 5},
        outcome="successful"
    )
    print(f"Wynik: {'✅' if success else '❌'}")
    
    # Test 2: Dane taktyczne  
    print("⚔️ Test danych taktycznych...")
    success = collector.log_tactical_move(
        commander_id="AI_Commander_1_Polish_TEST",
        action="flanking_attack",
        target_info={"hex": "D4", "enemy_strength": 3, "terrain": "forest"},
        success_rate=0.75
    )
    print(f"Wynik: {'✅' if success else '❌'}")
    
    # Test 3: Dane gameplay
    print("🎮 Test danych gameplay...")
    success = collector.log_gameplay_metrics(
        game_id="TEST_SESSION_001",
        metrics={
            "turn_duration": 45.2,
            "players_count": 2, 
            "ai_count": 4,
            "actions_performed": 12
        }
    )
    print(f"Wynik: {'✅' if success else '❌'}")
    
    # Test 4: Statystyki
    print("📈 Statystyki danych ML:")
    stats = collector.get_ml_data_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("✅ Test MLDataCollector zakończony")