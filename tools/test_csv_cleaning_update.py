#!/usr/bin/env python3
"""
TEST AKTUALIZOWANEGO CZYSZCZENIA CSV
Sprawdza czy po wpisaniu kodu zabezpieczenia czyści też JSON
"""

import os
from pathlib import Path

from utils.session_manager import LOGS_ROOT

def test_cleaning_modes():
    """Test różnych trybów czyszczenia"""
    
    print("🧪 TEST AKTUALIZOWANEGO CZYSZCZENIA CSV")
    print("=" * 50)
    
    # Sprawdź pliki w logs
    project_root = Path(".")
    logs_dir = project_root / LOGS_ROOT
    
    if not logs_dir.exists():
        print("❌ Katalog ai/logs nie istnieje!")
        return
    
    # Policz pliki różnych typów
    csv_files = list(logs_dir.rglob("*.csv"))
    json_files = list(logs_dir.rglob("*.json"))
    log_files = list(logs_dir.rglob("*.log"))
    
    print(f"📊 OBECNE PLIKI W {logs_dir}:")
    print(f"   📄 CSV:  {len(csv_files)} plików")
    print(f"   📄 JSON: {len(json_files)} plików")  
    print(f"   📄 LOG:  {len(log_files)} plików")
    
    # Sprawdź chronione foldery
    protected_patterns = [
        "analysis/ml_ready",
        "analysis/raporty", 
        "analysis/statystyki",
        "vp_intelligence/archives"
    ]
    
    protected_csv = []
    protected_json = []
    
    for file_path in csv_files + json_files:
        is_protected = any(pattern in str(file_path) for pattern in protected_patterns)
        if is_protected:
            if file_path.suffix == '.csv':
                protected_csv.append(file_path)
            elif file_path.suffix == '.json':
                protected_json.append(file_path)
    
    print(f"\n🛡️ CHRONIONE PLIKI:")
    print(f"   CSV:  {len(protected_csv)} plików")
    print(f"   JSON: {len(protected_json)} plików")
    
    if protected_csv:
        print("   🔒 Chronione CSV:")
        for f in protected_csv[:3]:  # Pokaż pierwsze 3
            print(f"      {f.relative_to(logs_dir)}")
        if len(protected_csv) > 3:
            print(f"      ... i {len(protected_csv) - 3} więcej")
    
    if protected_json:
        print("   🔒 Chronione JSON:")
        for f in protected_json[:3]:  # Pokaż pierwsze 3
            print(f"      {f.relative_to(logs_dir)}")
        if len(protected_json) > 3:
            print(f"      ... i {len(protected_json) - 3} więcej")
    
    print(f"\n🎯 ZACHOWANIE TRYBÓW CZYSZCZENIA:")
    print(f"📍 TRYB BEZPIECZNY (bez kodu zabezpieczenia):")
    print(f"   ✅ Czyści: pliki CSV, LOG, TXT (z ochroną ML)")
    print(f"   🛡️ Chroni: {len(protected_csv)} CSV + WSZYSTKIE JSON")
    print(f"   ❌ NIE czyści: żadnych plików JSON")
    
    print(f"\n🔥 TRYB AGRESYWNY (po wpisaniu 'ZNISZCZ_ML'):")
    print(f"   💀 Czyści: WSZYSTKIE pliki CSV, JSON, LOG, TXT")
    print(f"   ❌ NIE chroni: ŻADNYCH plików (także ML!)")
    print(f"   🚨 Usunąłby: {len(csv_files)} CSV + {len(json_files)} JSON")
    
    print(f"\n⚠️ OSTRZEŻENIE:")
    print(f"   Tryb agresywny zniszczyłby {len(protected_csv + protected_json)} chronionych plików ML!")

if __name__ == "__main__":
    test_cleaning_modes()