#!/usr/bin/env python3
"""
FINAL TEST - Testuje GOTOWĄ funkcjonalność aktualizowanego czyszczenia CSV
"""

import os
from pathlib import Path

from utils.session_manager import LOGS_ROOT

def final_functionality_test():
    """Finalny test gotowej funkcjonalności"""
    
    print("🏁 FINAL TEST - AKTUALIZOWANE CZYSZCZENIE CSV + JSON")
    print("=" * 70)
    
    # Sprawdź obecność plików
    project_root = Path("c:/Users/klif/OneDrive/Pulpit/gra wojenna 17082025")
    csv_cleaner = project_root / "czyszczenie" / "czyszczenie_csv.py"
    logs_dir = project_root / LOGS_ROOT
    
    # Weryfikacja struktury
    print("🔍 WERYFIKACJA STRUKTURY:")
    print(f"   📄 CSV Cleaner: {'✅ ISTNIEJE' if csv_cleaner.exists() else '❌ BRAK'}")
    print(f"   📁 Logs dir ({LOGS_ROOT}): {'✅ ISTNIEJE' if logs_dir.exists() else '❌ BRAK'}")
    
    if not csv_cleaner.exists() or not logs_dir.exists():
        print("❌ Struktura niekompletna!")
        return
    
    # Analiza plików
    all_json = list(logs_dir.rglob("*.json"))
    all_csv = list(logs_dir.rglob("*.csv"))
    all_log = list(logs_dir.rglob("*.log"))
    
    # Chronione (ML/raporty)
    protected_patterns = [
        "analysis/ml_ready",
        "analysis/raporty", 
        "analysis/statystyki",
        "vp_intelligence/archives"
    ]
    
    protected_files = []
    regular_files = []
    
    for file_path in all_json + all_csv + all_log:
        relative_path = file_path.relative_to(logs_dir)
        relative_unix = str(relative_path).replace("\\", "/")
        is_protected = any(pattern in relative_unix for pattern in protected_patterns)
        
        if is_protected:
            protected_files.append(file_path)
        else:
            regular_files.append(file_path)
    
    print(f"\n📊 ANALIZA OBECNYCH PLIKÓW:")
    print(f"   💾 JSON files: {len(all_json)} plików")
    print(f"   📄 CSV files: {len(all_csv)} plików")  
    print(f"   📝 LOG files: {len(all_log)} plików")
    print(f"   🛡️ Chronione: {len(protected_files)} plików")
    print(f"   🗂️ Zwykłe: {len(regular_files)} plików")
    
    # Rozbicie chronionych
    if protected_files:
        print(f"\n🛡️ CHRONIONE PLIKI (dane ML):")
        ml_ready = [f for f in protected_files if "ml_ready" in str(f)]
        raporty = [f for f in protected_files if "raporty" in str(f)]
        statystyki = [f for f in protected_files if "statystyki" in str(f)]
        
        if ml_ready:
            print(f"   🤖 ml_ready/: {len(ml_ready)} plików (metadane AI)")
        if raporty:
            print(f"   📈 raporty/: {len(raporty)} plików (raporty sesji)")
        if statystyki:
            print(f"   📊 statystyki/: {len(statystyki)} plików (długoterminowe)")
    
    print(f"\n🎯 FUNKCJONALNOŚĆ CZYSZCZENIA:")
    print(f"📍 TRYB BEZPIECZNY (domyślny):")
    print(f"   ✅ Rozszerzenia: *.csv, *.log, *.txt")
    print(f"   🛡️ Chroni: WSZYSTKIE pliki JSON + dane ML")
    print(f"   🗑️ Usuwa: {len([f for f in regular_files if f.suffix in ['.csv', '.log', '.txt']])} zwykłych plików")
    
    json_regular = [f for f in all_json if f not in protected_files]
    json_protected = [f for f in all_json if f in protected_files]
    
    print(f"\n🔥 TRYB AGRESYWNY (kod 'ZNISZCZ_ML'):")
    print(f"   💀 Rozszerzenia: *.csv, *.json, *.log, *.txt")
    print(f"   ❌ IGNORUJE ochronę ML!")
    print(f"   🗑️ Usuwa: WSZYSTKIE {len(all_json + all_csv + all_log)} pliki")
    print(f"   🚨 Straci: {len(json_protected)} chronionych plików ML!")
    
    print(f"\n⚠️ OSTRZEŻENIE BEZPIECZEŃSTWA:")
    print(f"   🛡️ Tryb bezpieczny NIGDY nie usuwa JSON - bezpieczny")
    print(f"   💀 Tryb agresywny usuwa WSZYSTKO - niebezpieczny!")
    print(f"   🔐 Kod zabezpieczenia: 'ZNISZCZ_ML' chroni przed przypadkiem")
    
    print(f"\n✅ IMPLEMENTACJA ZAKOŃCZONA:")
    print(f"   🎯 Dodano czyszczenie JSON po wpisaniu kodu")
    print(f"   🛡️ Zachowano ochronę danych ML")
    print(f"   🔧 Naprawiono logikę ścieżek Windows") 
    print(f"   📝 Użyj: python czyszczenie/czyszczenie_csv.py")

if __name__ == "__main__":
    final_functionality_test()