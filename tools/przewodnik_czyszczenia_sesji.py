#!/usr/bin/env python3
"""
PRAKTYCZNY PRZEWODNIK: KTÓRE PLIKI CZYŚCIĆ PO SESJI
===================================================
Na podstawie analizy kodu źródłowego i obecnego stanu systemu
"""

from pathlib import Path
from datetime import datetime

def practical_session_cleanup_guide():
    """Praktyczny przewodnik czyszczenia po sesji"""
    
    today = datetime.now().strftime('%Y%m%d')
    timestamp_pattern = datetime.now().strftime('%Y%m%d_%H')
    
    print("🎯 PRAKTYCZNY PRZEWODNIK CZYSZCZENIA SESJI")
    print("=" * 60)
    print(f"📅 Dzisiejsza data: {today}")
    print(f"🕐 Wzorzec timestampu: {timestamp_pattern}* (godzina może się różnić)")
    
    print("\n🎮 PLIKI TWORZONE PODCZAS KAŻDEJ SESJI GRY:")
    print("=" * 50)
    
    session_files = {
        "GŁÓWNE LOGI AKCJI": [
            f"logs/actions_{timestamp_pattern}*.csv",
            "└── 🔧 Tworzone przez: utils/action_logger.py",
            "└── 📝 Zawiera: Wszystkie akcje w grze (ruchy, walki, zakupy)"
        ],
        
        "LOGI AI COMMANDER": [
            f"logs/ai_commander/actions_{today}.csv",
            f"logs/ai_commander/turns_{today}.csv", 
            "└── 🔧 Tworzone przez: ai/logowanie_ai.py",
            "└── 📝 Zawiera: Szczegółowe akcje i podsumowania tur AI"
        ],
        
        "LOGI AI GENERAL": [
            f"logs/ai_purchases_{today}.csv",
            "logs/ai_general/communication_log.csv",
            "logs/ai_general/request_collection.csv", 
            "logs/ai_general/purchase_priorities.csv",
            "logs/ai_general/adaptive_purchases.csv",
            "└── 🔧 Tworzone przez: ai/ekonomia_ai.py, ai/communication_ai.py",  
            "└── 📝 Zawiera: Zakupy AI i komunikacja między AI"
        ],
        
        "NOWY SYSTEM LOGOWANIA (JSON)": [
            f"logs/ai/dowodca/dane_{timestamp_pattern}*.json",
            f"logs/ai/general/dane_{timestamp_pattern}*.json",
            f"logs/ai/strategia/dane_{timestamp_pattern}*.json",
            f"logs/ai/walka/dane_{timestamp_pattern}*.json", 
            f"logs/ai/zaopatrzenie/dane_{timestamp_pattern}*.json",
            f"logs/human/akcje/dane_{timestamp_pattern}*.json",
            f"logs/human/decyzje/dane_{timestamp_pattern}*.json",
            f"logs/game/mechanika/dane_{timestamp_pattern}*.json",
            f"logs/game/bledy/dane_{timestamp_pattern}*.json",
            "└── 🔧 Tworzone przez: Nowy system logowania kategoryzowanego",
            "└── 📝 Zawiera: Szczegółowe logi podzielone na kategorie"
        ],
        
        "PLIKI KONFIGURACYJNE SESJI": [
            "data/strategic_orders.json",
            "assets/tokens/nowe_dla_*/ (całe foldery)",
            "assets/tokens/aktualne/nowy_*.json",
            "└── 🔧 Tworzone przez: System rozkazów i zakupów żetonów",
            "└── 📝 Zawiera: Stan sesji - rozkazy i zakupione żetony"
        ],
        
        "LOGI DEBUGOWANIA": [
            "logs/movement_test.log",
            f"logs/garrison_issues/garrison_problems_{today}.csv",
            "└── 🔧 Tworzone przez: ai/ruch_jednostek.py, ai/wsparcie_garnizonu.py",
            "└── 📝 Zawiera: Debugging ruchów i problemów garnizonów"
        ]
    }
    
    for category, files in session_files.items():
        print(f"\n📁 {category}:")
        for file in files:
            if file.startswith("└──"):
                print(f"   {file}")
            else:
                print(f"   • {file}")
    
    print("\n🛡️ PLIKI ARCHIWALNE - NIGDY NIE CZYŚCIĆ!")
    print("=" * 50)
    archival_files = [
        "logs/analysis/ml_ready/*.csv (datasety ML)",
        "logs/analysis/ml_ready/*_meta.json (metadane ML)", 
        "logs/analysis/raporty/sesja_*.json (raporty sesji)",
        "logs/analysis/statystyki/* (statystyki długoterminowe)",
        "logs/vp_intelligence/archives/* (archiwa VP)"
    ]
    
    for file in archival_files:
        print(f"   🚫 {file}")
    
    print("\n🎯 REKOMENDACJE CZYSZCZENIA:")
    print("=" * 40)
    
    print("\n✅ PO KAŻDEJ SESJI GRY:")
    print("   1. Użyj nowego czyszczenia: python czyszczenie/czyszczenie_csv.py")
    print("   2. TRYB BEZPIECZNY wyczyści pliki sesyjne ale OCHRONI dane ML")
    print("   3. Ręcznie usuń: data/strategic_orders.json") 
    print("   4. Ręcznie usuń: assets/tokens/nowe_dla_*/ (foldery)")
    print("   5. Ręcznie wyczyść: assets/start_tokens.json → []")
    
    print("\n🚨 CZEGO NIGDY NIE ROBIĆ:")
    print("   ❌ NIE używaj starych funkcji: clean_csv_logs(), clean_all_for_new_game()")
    print("   ❌ NIE używaj Ctrl+Shift+L (niszczy dane ML!)")
    print("   ❌ NIE czyść ręcznie logs/analysis/* (bezcenne dane!)")
    
    print("\n🔧 JAK ROZPOZNAĆ PLIKI SESYJNE:")
    print("   📅 Zawierają dzisiejszą datę w nazwie")
    print("   🕐 Wzorce: *20250914*, dane_20250914_*, actions_20250914*")
    print("   📁 Lokalizacje: logs/ai/, logs/human/, logs/game/ (nie analysis!)")
    
    print("\n💡 PRZYDATNE KOMENDY:")
    print("   # Bezpieczne czyszczenie z ochroną ML:")
    print("   python czyszczenie/czyszczenie_csv.py")
    print()
    print("   # Zobacz co zostanie wyczyszczone:")  
    print("   python tools/analiza_plikow_sesyjnych.py")
    print()
    print("   # Test aktualnego stanu czyszczenia:")
    print("   python tools/final_test_csv_update.py")

if __name__ == "__main__":
    practical_session_cleanup_guide()