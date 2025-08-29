#!/usr/bin/env python3
"""REAL-TIME AI LOG ANALYZER (przeniesione z folderu czyszczenie/)
Uruchomienie: python tools/realtime_ai_analyzer.py
"""
import csv
import json
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict, deque
import threading
import io

class RealTimeAIAnalyzer:
    def __init__(self, logs_dir="logs/ai_flow"):
        self.logs_dir = Path(logs_dir)
        self.running = False
        self.stats = defaultdict(lambda: defaultdict(int))
        self.recent_events = deque(maxlen=50)
        self.last_file_sizes = {}
        self.watch_thread = None

    def start_monitoring(self):
        if self.running:
            return
        self.running = True
        self.watch_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.watch_thread.start()

    def stop_monitoring(self):
        self.running = False
        if self.watch_thread:
            self.watch_thread.join(timeout=2)

    def _monitor_loop(self):
        while self.running:
            try:
                self._check_for_new_events()
                time.sleep(1)
            except Exception:
                time.sleep(5)

    def _check_for_new_events(self):
        if not self.logs_dir.exists():
            return
        for csv_file in self.logs_dir.glob('*.csv'):
            try:
                current_size = csv_file.stat().st_size
                last_size = self.last_file_sizes.get(str(csv_file), 0)
                if current_size > last_size:
                    self._read_new_lines(csv_file, last_size)
                    self.last_file_sizes[str(csv_file)] = current_size
            except Exception:
                pass

    def _read_new_lines(self, csv_file, start_pos):
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                f.seek(start_pos)
                content = f.read()
            if not content.strip():
                return
            file_type = self._get_file_type(csv_file.name)
            for line in content.strip().split('\n'):
                if line.strip():
                    self._process_log_line(line, file_type, csv_file.name)
        except Exception:
            pass

    def _get_file_type(self, filename):
        if filename.startswith('ai_flow_'):
            return 'main'
        if filename.startswith('purchases_'):
            return 'purchase'
        if filename.startswith('deployment_'):
            return 'deployment'
        if filename.startswith('debug_'):
            return 'debug'
        return 'unknown'

    def _process_log_line(self, line, file_type, filename):
        try:
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
        except Exception:
            pass

    def _process_main_event(self, row, filename):
        if len(row) < 6:
            return
        timestamp, turn, phase, component, action, status = row[:6]
        details = row[6] if len(row) > 6 else ''
        event = {'timestamp': timestamp, 'turn': turn, 'phase': phase, 'component': component,
                 'action': action, 'status': status, 'details': details, 'file': filename, 'type': 'main'}
        self.recent_events.append(event)
        self.stats['main'][f"{component}_{action}"] += 1
        self.stats['status'][status] += 1

    def _process_purchase_event(self, row, filename):
        if len(row) < 10:
            return
        timestamp, turn, commander_id, unit_type, unit_size, cost = row[:6]
        pe_before, pe_after, folder_created, json_created = row[6:10]
        success = row[12] if len(row) > 12 else 'True'
        event = {'timestamp': timestamp, 'turn': turn, 'commander_id': commander_id,
                 'unit_type': unit_type, 'unit_size': unit_size, 'cost': cost,
                 'pe_spent': int(pe_before) - int(pe_after) if pe_before.isdigit() and pe_after.isdigit() else 0,
                 'success': success.lower() == 'true', 'type': 'purchase'}
        self.recent_events.append(event)
        self.stats['purchases']['total'] += 1
        self.stats['purchases'][f"{unit_type}_{unit_size}"] += 1
        if event['success']:
            self.stats['purchases']['successful'] += 1
        else:
            self.stats['purchases']['failed'] += 1

    def _process_deployment_event(self, row, filename):
        if len(row) < 8:
            return
        timestamp, turn, commander_id, token_id, unit_type = row[:5]
        deploy_q, deploy_r = row[5:7]
        success = row[11] if len(row) > 11 else 'True'
        event = {'timestamp': timestamp, 'turn': turn, 'commander_id': commander_id,
                 'token_id': token_id, 'unit_type': unit_type, 'position': (deploy_q, deploy_r),
                 'success': success.lower() == 'true', 'type': 'deployment'}
        self.recent_events.append(event)
        self.stats['deployments']['total'] += 1
        if event['success']:
            self.stats['deployments']['successful'] += 1
        else:
            self.stats['deployments']['failed'] += 1

    def _process_debug_event(self, row, filename):
        if len(row) < 5:
            return
        timestamp, turn, component, function, event_type = row[:5]
        self.stats['debug'][f"{component}_{function}"] += 1
        self.stats['debug']['total'] += 1

    def show_stats(self):
        print("\n==== STATY AI ====")
        print("STATUSY:")
        for s, c in self.stats['status'].items():
            print(f"  {s}: {c}")
        print("ZAKUPY:")
        if self.stats['purchases']:
            total = self.stats['purchases']['total']
            succ = self.stats['purchases']['successful']
            fail = self.stats['purchases']['failed']
            print(f"  total={total} succ={succ} fail={fail}")
        print("DEPLOY:")
        if self.stats['deployments']:
            total = self.stats['deployments']['total']
            succ = self.stats['deployments']['successful']
            fail = self.stats['deployments']['failed']
            print(f"  total={total} succ={succ} fail={fail}")
        print("Ostatnie:")
        for ev in list(self.recent_events)[-5:]:
            print(f"  {ev['type']} {ev.get('action') or ev.get('unit_type')} -> {ev.get('status','')}")

    def save_report(self, filename=None):
        if not filename:
            filename = f"ai_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report = {'timestamp': datetime.now().isoformat(), 'stats': dict(self.stats), 'recent_events': list(self.recent_events)}
        self.logs_dir.mkdir(exist_ok=True)
        path = self.logs_dir / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return path


def main():
    a = RealTimeAIAnalyzer()
    a.start_monitoring()
    print("Analyzer running. Commands: s=stats r=report q=quit")
    try:
        while True:
            cmd = input().strip().lower()
            if cmd == 'q':
                break
            if cmd == 's':
                a.show_stats()
            if cmd == 'r':
                p = a.save_report()
                print(f"zapisano {p}")
    except KeyboardInterrupt:
        pass
    finally:
        a.stop_monitoring()

if __name__ == '__main__':
    main()
