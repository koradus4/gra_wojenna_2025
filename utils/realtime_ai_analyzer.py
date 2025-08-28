#!/usr/bin/env python3
"""
REAL-TIME AI LOG ANALYZER
Analizuje logi AI w czasie rzeczywistym podczas gry
"""

import csv
import json
import time
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict, deque
import threading
import sys

class RealTimeAIAnalyzer:
    """Analizator logów AI w czasie rzeczywistym"""
    
    def __init__(self, logs_dir="logs/ai_flow"):
        self.logs_dir = Path(logs_dir)
        self.running = False
        self.stats = defaultdict(lambda: defaultdict(int))
        self.recent_events = deque(maxlen=50)  # Ostatnie 50 zdarzeń
        self.last_file_sizes = {}
        self.watch_thread = None
        
        print(f"📊 [ANALYZER] Inicjalizacja analizatora logów AI")
        print(f"📁 [ANALYZER] Folder: {self.logs_dir}")
    
    def start_monitoring(self):
        """Rozpoczyna monitorowanie logów"""
        if self.running:
            print("⚠️ [ANALYZER] Monitorowanie już działa")
            return
        
        self.running = True
        self.watch_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.watch_thread.start()
        print("🔄 [ANALYZER] Monitorowanie rozpoczęte")
    
    def stop_monitoring(self):
        """Zatrzymuje monitorowanie"""
        self.running = False
        if self.watch_thread:
            self.watch_thread.join(timeout=2)
        print("⏹️ [ANALYZER] Monitorowanie zatrzymane")
    
    def _monitor_loop(self):
        """Główna pętla monitorowania"""
        while self.running:
            try:
                self._check_for_new_events()
                time.sleep(1)  # Sprawdzaj co sekundę
            except Exception as e:
                print(f"❌ [ANALYZER] Błąd monitorowania: {e}")
                time.sleep(5)  # Czekaj dłużej po błędzie
    
    def _check_for_new_events(self):
        """Sprawdza nowe zdarzenia w plikach logów"""
        if not self.logs_dir.exists():
            return
        
        # Znajdź pliki CSV
        csv_files = list(self.logs_dir.glob("*.csv"))
        
        for csv_file in csv_files:
            try:
                current_size = csv_file.stat().st_size
                last_size = self.last_file_sizes.get(str(csv_file), 0)
                
                if current_size > last_size:
                    # Plik się powiększył - czytaj nowe linie
                    self._read_new_lines(csv_file, last_size)
                    self.last_file_sizes[str(csv_file)] = current_size
                    
            except Exception as e:
                print(f"⚠️ [ANALYZER] Błąd czytania {csv_file}: {e}")
    
    def _read_new_lines(self, csv_file, start_pos):
        """Czyta nowe linie z pliku CSV"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                f.seek(start_pos)
                content = f.read()
                
            if not content.strip():
                return
            
            # Podziel na linie i przetwórz
            lines = content.strip().split('\n')
            
            # Określ typ pliku po nazwie
            file_type = self._get_file_type(csv_file.name)
            
            for line in lines:
                if line.strip():
                    self._process_log_line(line, file_type, csv_file.name)
                    
        except Exception as e:
            print(f"⚠️ [ANALYZER] Błąd przetwarzania linii: {e}")
    
    def _get_file_type(self, filename):
        """Określa typ pliku logów"""
        if filename.startswith('ai_flow_'):
            return 'main'
        elif filename.startswith('purchases_'):
            return 'purchase'
        elif filename.startswith('deployment_'):
            return 'deployment'
        elif filename.startswith('debug_'):
            return 'debug'
        else:
            return 'unknown'
    
    def _process_log_line(self, line, file_type, filename):
        """Przetwarza pojedynczą linię loga"""
        try:
            # Parsuj CSV
            import io
            reader = csv.reader(io.StringIO(line))
            row = next(reader)
            
            if file_type == 'main':
                self._process_main_event(row, filename)
            elif file_type == 'purchase':
                self._process_purchase_event(row, filename)
            elif file_type == 'deployment':
                self._process_deployment_event(row, filename)
            elif file_type == 'debug':
                self._process_debug_event(row, filename)
                
        except Exception as e:
            print(f"⚠️ [ANALYZER] Błąd parsowania linii: {e}")
    
    def _process_main_event(self, row, filename):
        """Przetwarza główne zdarzenie AI"""
        try:
            if len(row) < 6:
                return
            
            timestamp, turn, phase, component, action, status = row[:6]
            details = row[6] if len(row) > 6 else ""
            
            event = {
                'timestamp': timestamp,
                'turn': turn,
                'phase': phase,
                'component': component,
                'action': action,
                'status': status,
                'details': details,
                'file': filename,
                'type': 'main'
            }
            
            self.recent_events.append(event)
            self.stats['main'][f"{component}_{action}"] += 1
            self.stats['status'][status] += 1
            
            # Wyświetl ważne zdarzenia
            if action in ['purchase_unit_complete', 'deploy_complete', 'turn_complete']:
                self._display_event(event)
                
        except Exception as e:
            print(f"⚠️ [ANALYZER] Błąd main event: {e}")
    
    def _process_purchase_event(self, row, filename):
        """Przetwarza zdarzenie zakupu"""
        try:
            if len(row) < 10:
                return
            
            timestamp, turn, commander_id, unit_type, unit_size, cost = row[:6]
            pe_before, pe_after, folder_created, json_created = row[6:10]
            success = row[12] if len(row) > 12 else "True"
            
            event = {
                'timestamp': timestamp,
                'turn': turn,
                'commander_id': commander_id,
                'unit_type': unit_type,
                'unit_size': unit_size,
                'cost': cost,
                'pe_spent': int(pe_before) - int(pe_after) if pe_before.isdigit() and pe_after.isdigit() else 0,
                'success': success.lower() == 'true',
                'type': 'purchase'
            }
            
            self.recent_events.append(event)
            self.stats['purchases']['total'] += 1
            self.stats['purchases'][f"{unit_type}_{unit_size}"] += 1
            
            if event['success']:
                self.stats['purchases']['successful'] += 1
                self._display_purchase(event)
            else:
                self.stats['purchases']['failed'] += 1
                
        except Exception as e:
            print(f"⚠️ [ANALYZER] Błąd purchase event: {e}")
    
    def _process_deployment_event(self, row, filename):
        """Przetwarza zdarzenie deployment"""
        try:
            if len(row) < 8:
                return
            
            timestamp, turn, commander_id, token_id, unit_type = row[:5]
            deploy_q, deploy_r = row[5:7]
            success = row[11] if len(row) > 11 else "True"
            
            event = {
                'timestamp': timestamp,
                'turn': turn,
                'commander_id': commander_id,
                'token_id': token_id,
                'unit_type': unit_type,
                'position': (deploy_q, deploy_r),
                'success': success.lower() == 'true',
                'type': 'deployment'
            }
            
            self.recent_events.append(event)
            self.stats['deployments']['total'] += 1
            
            if event['success']:
                self.stats['deployments']['successful'] += 1
                self._display_deployment(event)
            else:
                self.stats['deployments']['failed'] += 1
                
        except Exception as e:
            print(f"⚠️ [ANALYZER] Błąd deployment event: {e}")
    
    def _process_debug_event(self, row, filename):
        """Przetwarza zdarzenie debug"""
        try:
            if len(row) < 5:
                return
            
            timestamp, turn, component, function, event_type = row[:5]
            
            self.stats['debug'][f"{component}_{function}"] += 1
            self.stats['debug']['total'] += 1
            
        except Exception as e:
            print(f"⚠️ [ANALYZER] Błąd debug event: {e}")
    
    def _display_event(self, event):
        """Wyświetla ważne zdarzenie"""
        time_str = event['timestamp'].split('T')[1][:8] if 'T' in event['timestamp'] else event['timestamp']
        print(f"🔔 [{time_str}] {event['component']} {event['action']} - {event['status']}")
        if event['details']:
            print(f"   ℹ️  {event['details']}")
    
    def _display_purchase(self, event):
        """Wyświetla zdarzenie zakupu"""
        time_str = event['timestamp'].split('T')[1][:8] if 'T' in event['timestamp'] else event['timestamp']
        print(f"🛒 [{time_str}] ZAKUP: {event['unit_type']} {event['unit_size']} dla dowódcy {event['commander_id']}")
        print(f"   💰 Koszt: {event['cost']} PE (wydano: {event['pe_spent']})")
    
    def _display_deployment(self, event):
        """Wyświetla zdarzenie deployment"""
        time_str = event['timestamp'].split('T')[1][:8] if 'T' in event['timestamp'] else event['timestamp']
        print(f"🎯 [{time_str}] WDROŻENIE: {event['unit_type']} na pozycji {event['position']}")
        print(f"   👤 Dowódca: {event['commander_id']}, Token: {event['token_id'][:20]}...")
    
    def show_stats(self):
        """Wyświetla aktualne statystyki"""
        print("\n" + "="*60)
        print("📊 STATYSTYKI AI W CZASIE RZECZYWISTYM")
        print("="*60)
        
        # Statystyki główne
        print("\n🎯 GŁÓWNE ZDARZENIA:")
        for event_type, count in self.stats['status'].items():
            print(f"  {event_type}: {count}")
        
        # Statystyki zakupów
        if self.stats['purchases']:
            print("\n🛒 ZAKUPY:")
            total = self.stats['purchases']['total']
            successful = self.stats['purchases']['successful']
            failed = self.stats['purchases']['failed']
            success_rate = (successful / total * 100) if total > 0 else 0
            
            print(f"  Łącznie: {total}")
            print(f"  Udane: {successful} ({success_rate:.1f}%)")
            print(f"  Nieudane: {failed}")
            
            print("  Typy jednostek:")
            for unit_type, count in self.stats['purchases'].items():
                if unit_type not in ['total', 'successful', 'failed']:
                    print(f"    {unit_type}: {count}")
        
        # Statystyki deployment
        if self.stats['deployments']:
            print("\n🎖️ WDROŻENIA:")
            total = self.stats['deployments']['total']
            successful = self.stats['deployments']['successful']
            failed = self.stats['deployments']['failed']
            success_rate = (successful / total * 100) if total > 0 else 0
            
            print(f"  Łącznie: {total}")
            print(f"  Udane: {successful} ({success_rate:.1f}%)")
            print(f"  Nieudane: {failed}")
        
        # Ostatnie zdarzenia
        print(f"\n📋 OSTATNIE ZDARZENIA ({len(self.recent_events)}):")
        for event in list(self.recent_events)[-10:]:  # Ostatnie 10
            time_str = event['timestamp'].split('T')[1][:8] if 'T' in event['timestamp'] else event['timestamp']
            
            if event['type'] == 'purchase':
                print(f"  [{time_str}] 🛒 {event['unit_type']} {event['unit_size']} → Cmd {event['commander_id']}")
            elif event['type'] == 'deployment':
                print(f"  [{time_str}] 🎯 {event['unit_type']} → {event['position']}")
            else:
                action = event.get('action', 'unknown')
                status = event.get('status', 'unknown')
                print(f"  [{time_str}] ⚙️  {action} - {status}")
        
        print("="*60)
    
    def save_report(self, filename=None):
        """Zapisuje raport do pliku"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_analysis_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'stats': dict(self.stats),
            'recent_events': list(self.recent_events),
            'monitoring_duration': 'unknown'  # TODO: dodaj czas monitorowania
        }
        
        try:
            self.logs_dir.mkdir(exist_ok=True)
            report_path = self.logs_dir / filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"💾 [ANALYZER] Raport zapisany: {report_path}")
            return report_path
            
        except Exception as e:
            print(f"❌ [ANALYZER] Błąd zapisu raportu: {e}")
            return None

def main():
    """Główna funkcja analizatora"""
    print("📊 REAL-TIME AI LOG ANALYZER")
    print("="*50)
    
    analyzer = RealTimeAIAnalyzer()
    
    try:
        analyzer.start_monitoring()
        
        print("\n🔄 Monitorowanie logów AI uruchomione!")
        print("💡 Komendy:")
        print("  's' - pokaż statystyki")
        print("  'r' - zapisz raport")
        print("  'q' - wyjście")
        print("-" * 30)
        
        while True:
            try:
                command = input().strip().lower()
                
                if command == 'q':
                    break
                elif command == 's':
                    analyzer.show_stats()
                elif command == 'r':
                    analyzer.save_report()
                elif command == 'help' or command == 'h':
                    print("💡 Dostępne komendy: s (stats), r (report), q (quit)")
                    
            except KeyboardInterrupt:
                break
                
    finally:
        analyzer.stop_monitoring()
        print("\n📊 Analizator zatrzymany")

if __name__ == "__main__":
    main()
