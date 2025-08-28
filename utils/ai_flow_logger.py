#!/usr/bin/env python3
"""
ENHANCED LOGGING SYSTEM dla AI General i AI Commander
Rozszerzenie istniejących klas o szczegółowe logowanie całego procesu
"""

import csv
import json
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

class AIFlowLogger:
    """Szczegółowy logger dla przepływu AI General → AI Commander"""
    
    def __init__(self, nation: str = "Unknown"):
        self.nation = nation
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path("logs/ai_flow")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Pliki logów
        self.main_log = self.log_dir / f"ai_flow_{nation}_{self.session_id}.csv"
        self.purchase_log = self.log_dir / f"purchases_{nation}_{self.session_id}.csv"
        self.deployment_log = self.log_dir / f"deployment_{nation}_{self.session_id}.csv"
        self.debug_log = self.log_dir / f"debug_{nation}_{self.session_id}.csv"
        
        self._init_log_files()
        
        print(f"📝 [AI FLOW LOGGER] Inicjalizacja dla {nation}")
        print(f"📁 [AI FLOW LOGGER] Logi w: {self.log_dir}")
    
    def _init_log_files(self):
        """Inicjalizuje pliki logów z nagłówkami"""
        
        # Main flow log
        with open(self.main_log, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'turn', 'phase', 'component', 'action', 'status',
                'details', 'metrics_json', 'error_msg'
            ])
        
        # Purchase log
        with open(self.purchase_log, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'turn', 'commander_id', 'unit_type', 'unit_size',
                'cost', 'pe_before', 'pe_after', 'folder_created', 'json_created',
                'image_created', 'supports', 'purchase_reason', 'success', 'error_msg'
            ])
        
        # Deployment log
        with open(self.deployment_log, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'turn', 'commander_id', 'token_id', 'unit_type',
                'deploy_position_q', 'deploy_position_r', 'source_folder',
                'deployment_reason', 'board_added', 'folder_cleaned', 'success', 'error_msg'
            ])
        
        # Debug log
        with open(self.debug_log, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'turn', 'component', 'function', 'event',
                'data_json', 'stack_trace'
            ])
    
    def log_main_event(self, turn: int, phase: str, component: str, action: str, 
                      status: str, details: str, metrics: Dict = None, error_msg: str = None):
        """Loguje główne wydarzenie w przepływie AI"""
        try:
            with open(self.main_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.datetime.now().isoformat(),
                    turn,
                    phase,
                    component,
                    action,
                    status,
                    details,
                    json.dumps(metrics) if metrics else "",
                    error_msg or ""
                ])
        except Exception as e:
            print(f"❌ [LOGGER] Błąd logowania main event: {e}")
    
    def log_purchase_event(self, turn: int, commander_id: int, unit_type: str, unit_size: str,
                          cost: int, pe_before: int, pe_after: int, folder_created: bool,
                          json_created: bool, image_created: bool, supports: List = None,
                          purchase_reason: str = "", success: bool = True, error_msg: str = None):
        """Loguje szczegóły zakupu jednostki"""
        try:
            with open(self.purchase_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.datetime.now().isoformat(),
                    turn,
                    commander_id,
                    unit_type,
                    unit_size,
                    cost,
                    pe_before,
                    pe_after,
                    folder_created,
                    json_created,
                    image_created,
                    ';'.join(supports) if supports else "",
                    purchase_reason,
                    success,
                    error_msg or ""
                ])
        except Exception as e:
            print(f"❌ [LOGGER] Błąd logowania purchase: {e}")
    
    def log_deployment_event(self, turn: int, commander_id: int, token_id: str, unit_type: str,
                           deploy_position: tuple, source_folder: str, deployment_reason: str = "",
                           board_added: bool = False, folder_cleaned: bool = False,
                           success: bool = True, error_msg: str = None):
        """Loguje szczegóły wdrożenia jednostki"""
        try:
            deploy_q, deploy_r = deploy_position if deploy_position else (None, None)
            
            with open(self.deployment_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.datetime.now().isoformat(),
                    turn,
                    commander_id,
                    token_id,
                    unit_type,
                    deploy_q,
                    deploy_r,
                    source_folder,
                    deployment_reason,
                    board_added,
                    folder_cleaned,
                    success,
                    error_msg or ""
                ])
        except Exception as e:
            print(f"❌ [LOGGER] Błąd logowania deployment: {e}")
    
    def log_debug_event(self, turn: int, component: str, function: str, event: str,
                       data: Any = None, stack_trace: str = None):
        """Loguje zdarzenia debugowe"""
        try:
            with open(self.debug_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.datetime.now().isoformat(),
                    turn,
                    component,
                    function,
                    event,
                    json.dumps(data, default=str) if data else "",
                    stack_trace or ""
                ])
        except Exception as e:
            print(f"❌ [LOGGER] Błąd logowania debug: {e}")
    
    def log_folder_scan(self, turn: int, base_path: str, folders_found: Dict):
        """Loguje wyniki skanowania folderów z tokenami"""
        self.log_debug_event(turn, "FileSystem", "scan_folders", "folder_scan_results", {
            "base_path": str(base_path),
            "folders_found": folders_found,
            "total_tokens": sum(len(tokens) for tokens in folders_found.values())
        })
    
    def log_token_creation_details(self, turn: int, token_data: Dict, file_paths: Dict):
        """Loguje szczegóły tworzenia plików tokena"""
        self.log_debug_event(turn, "TokenCreation", "create_files", "token_files_created", {
            "token_id": token_data.get('id'),
            "unit_type": token_data.get('unitType'),
            "json_path": file_paths.get('json'),
            "image_path": file_paths.get('image'),
            "folder_path": file_paths.get('folder')
        })
    
    def generate_summary_report(self, turn: int):
        """Generuje raport podsumowujący dla tury"""
        try:
            summary_file = self.log_dir / f"summary_{self.nation}_{self.session_id}_turn_{turn}.json"
            
            # Zbierz statystyki z logów
            purchases_count = 0
            deployments_count = 0
            errors_count = 0
            
            # Przeczytaj logi zakupów
            if self.purchase_log.exists():
                with open(self.purchase_log, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if int(row['turn']) == turn:
                            purchases_count += 1
                            if row['success'].lower() != 'true':
                                errors_count += 1
            
            # Przeczytaj logi deployment
            if self.deployment_log.exists():
                with open(self.deployment_log, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if int(row['turn']) == turn:
                            deployments_count += 1
                            if row['success'].lower() != 'true':
                                errors_count += 1
            
            summary = {
                "session_id": self.session_id,
                "nation": self.nation,
                "turn": turn,
                "timestamp": datetime.datetime.now().isoformat(),
                "statistics": {
                    "purchases_count": purchases_count,
                    "deployments_count": deployments_count,
                    "errors_count": errors_count,
                    "success_rate": (purchases_count + deployments_count - errors_count) / max(purchases_count + deployments_count, 1)
                },
                "log_files": {
                    "main_log": str(self.main_log),
                    "purchase_log": str(self.purchase_log),
                    "deployment_log": str(self.deployment_log),
                    "debug_log": str(self.debug_log)
                }
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"📊 [AI FLOW LOGGER] Raport podsumowujący: {summary_file}")
            return summary
            
        except Exception as e:
            print(f"❌ [LOGGER] Błąd generowania raportu: {e}")
            return None

# Globalna instancja loggera (będzie używana przez AI classes)
_ai_flow_logger = None

def get_ai_flow_logger(nation: str = "Unknown") -> AIFlowLogger:
    """Pobiera globalną instancję AI Flow Logger"""
    global _ai_flow_logger
    if _ai_flow_logger is None or _ai_flow_logger.nation != nation:
        _ai_flow_logger = AIFlowLogger(nation)
    return _ai_flow_logger

def log_ai_event(nation: str, turn: int, phase: str, component: str, action: str,
                status: str, details: str, metrics: Dict = None, error_msg: str = None):
    """Globalna funkcja do logowania wydarzeń AI"""
    logger = get_ai_flow_logger(nation)
    logger.log_main_event(turn, phase, component, action, status, details, metrics, error_msg)

def log_purchase_debug(nation: str, turn: int, **kwargs):
    """Globalna funkcja do logowania zakupów"""
    logger = get_ai_flow_logger(nation)
    logger.log_purchase_event(turn, **kwargs)

def log_deployment_debug(nation: str, turn: int, **kwargs):
    """Globalna funkcja do logowania deployment"""
    logger = get_ai_flow_logger(nation)
    logger.log_deployment_event(turn, **kwargs)

if __name__ == "__main__":
    # Test loggera
    print("🧪 Testowanie AI Flow Logger...")
    
    logger = AIFlowLogger("TestNation")
    
    # Test różnych typów logów
    logger.log_main_event(1, "ANALYSIS", "AIGeneral", "analyze_units", "SUCCESS", 
                         "Analiza zakończona", {"units": 5, "low_fuel": 2})
    
    logger.log_purchase_event(1, 5, "P", "Pluton", 30, 150, 120, True, True, True,
                             ["sekcja km.ppanc"], "Brak piechoty", True)
    
    logger.log_deployment_event(1, 5, "test_token_123", "P", (10, 15), 
                               "/assets/tokens/nowe_dla_5/", "Auto deployment", 
                               True, True, True)
    
    # Generuj raport
    summary = logger.generate_summary_report(1)
    print(f"✅ Test zakończony. Summary: {summary}")
