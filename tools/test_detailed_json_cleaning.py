#!/usr/bin/env python3
"""
SZCZEGÓŁOWY TEST AKTUALIZOWANEGO CZYSZCZENIA CSV
Sprawdza dokładnie co zostanie usunięte w każdym trybie
"""

import os
from pathlib import Path

from utils.session_manager import LOGS_ROOT

def detailed_test():
    """Szczegółowy test trybów czyszczenia"""
    
    print("🔍 SZCZEGÓŁOWY TEST CZYSZCZENIA CSV + JSON")
    print("=" * 60)
    
    # Sprawdź pliki w logs
    project_root = Path(".")
    logs_dir = project_root / LOGS_ROOT
    
    if not logs_dir.exists():
        print("❌ Katalog ai/logs nie istnieje!")
        return
    
    # Znajdź wszystkie pliki JSON
    all_json_files = list(logs_dir.rglob("*.json"))
    
    # Kategorie folderów chronionych
    protected_patterns = [
        "analysis/ml_ready",      # Dane ML gotowe do analizy
        "analysis/raporty",       # Raporty analityczne  
        "analysis/statystyki",    # Statystyki ML
        "vp_intelligence/archives"  # Archiwa punktów zwycięstwa
    ]
    
    # Rozdziel pliki na chronione i niechronione
    protected_json = []
    regular_json = []
    
    for json_file in all_json_files:
        # Używaj relative path z konwersją separatorów Windows -> Unix (tak jak w rzeczywistym kodzie)
        relative_path = json_file.relative_to(logs_dir)
        relative_unix = str(relative_path).replace("\\", "/")
        is_protected = any(pattern in relative_unix for pattern in protected_patterns)
        
        if is_protected:
            protected_json.append(json_file)
        else:
            regular_json.append(json_file)
    
    print(f"📊 ANALIZA PLIKÓW JSON W {logs_dir}:")
    print(f"   💾 Wszystkich JSON: {len(all_json_files)}")
    print(f"   🛡️ Chronionych:     {len(protected_json)}")  
    print(f"   🗂️ Zwykłych:        {len(regular_json)}")
    
    print(f"\n🛡️ CHRONIONE PLIKI JSON (dane ML):")
    for file_path in protected_json:
        folder = file_path.parent.name
        print(f"   🔒 {folder}/ → {file_path.name}")
    
    print(f"\n🗂️ ZWYKŁE PLIKI JSON (logi gry):")
    folders = {}
    for file_path in regular_json:
        folder_path = file_path.parent
        folder_name = str(folder_path.relative_to(logs_dir))
        if folder_name not in folders:
            folders[folder_name] = []
        folders[folder_name].append(file_path.name)
    
    for folder, files in folders.items():
        print(f"   📁 {folder}/ → {len(files)} plików")
        if len(files) <= 3:
            for file in files:
                print(f"      📄 {file}")
        else:
            for file in files[:2]:
                print(f"      📄 {file}")
            print(f"      ... i {len(files) - 2} więcej")
    
    print(f"\n🎯 ZACHOWANIE CZYSZCZENIA:")
    print(f"📍 TRYB BEZPIECZNY (domyślny):")
    print(f"   ✅ Usunie: 0 plików JSON (ŻADNYCH!)")
    print(f"   🛡️ Ochroni: WSZYSTKIE {len(all_json_files)} plików JSON")
    print(f"   📝 Czyści tylko: CSV, LOG, TXT (z ochroną ML)")
    
    print(f"\n🔥 TRYB AGRESYWNY ('ZNISZCZ_ML'):")
    print(f"   💀 Usunie: WSZYSTKIE {len(all_json_files)} plików JSON")
    print(f"   🚨 Straci: {len(protected_json)} CHRONIONYCH plików ML!")
    print(f"   ⚠️ To znaczy utratę danych ML i raportów!")
    
    if protected_json:
        print(f"\n⚠️ OSTRZEŻENIE - UTRACONE DANE ML:")
        ml_folders = set(f.parent.name for f in protected_json)
        for folder in ml_folders:
            count = len([f for f in protected_json if f.parent.name == folder])
            print(f"   🔥 {folder}/ → {count} plików")

if __name__ == "__main__":
    detailed_test()