#!/usr/bin/env python3
"""
SZCZEGÓŁOWA ANALIZA PLIKÓW LOGÓW SESYJNYCH
==========================================
Identyfikuje które pliki są tworzone tylko na potrzeby bieżącej sesji gry
vs te które mają wartość długoterminową i powinny być archiwizowane.
"""

import os
from pathlib import Path
from datetime import datetime

def analyze_session_logs():
    """Pełna analiza plików sesyjnych vs archiwalnych"""
    
    print("📊 SZCZEGÓŁOWA ANALIZA LOGÓW SESYJNYCH")
    print("=" * 60)
    
    # Struktura plików logów zgodnie z kodem źródłowym
    session_file_patterns = {
        "🎮 GŁÓWNE LOGI SESYJNE": {
            "description": "Pliki tworzone podczas pojedynczej sesji gry",
            "patterns": [
                "logs/actions_YYYYMMDD_HHMMSS.csv",           # utils/action_logger.py
                "logs/ai_commander/actions_YYYYMMDD.csv",     # ai/logowanie_ai.py  
                "logs/ai_commander/turns_YYYYMMDD.csv",       # ai/logowanie_ai.py (podsumowania tur)
                "logs/ai_purchases_YYYYMMDD.csv",             # ai/ekonomia_ai.py
                "logs/ai_actions_YYYYMMDD.csv",               # legacy - stare logi AI
                "logs/movement_test.log",                     # ai/ruch_jednostek.py
            ],
            "created_by": [
                "action_logger.py - główne akcje gry",
                "logowanie_ai.py - szczegółowe akcje AI Commander", 
                "ekonomia_ai.py - zakupy AI General",
                "ruch_jednostek.py - debugowanie ruchów"
            ],
            "cleanup": "✅ MOŻNA BEZPIECZNIE CZYŚCIĆ po sesji"
        },
        
        "🧠 NOWY SYSTEM LOGOWANIA": {
            "description": "Rozbudowane logi kategoryzowane (nowy system)",
            "patterns": [
                "logs/ai/dowodca/dane_YYYYMMDD_HHMMSS.json",       # AI Commander decyzje
                "logs/ai/general/dane_YYYYMMDD_HHMMSS.json",       # AI General decyzje  
                "logs/ai/strategia/dane_YYYYMMDD_HHMMSS.json",     # Strategia AI
                "logs/ai/walka/dane_YYYYMMDD_HHMMSS.json",         # Walka AI
                "logs/ai/ruch/dane_YYYYMMDD_HHMMSS.json",          # Ruch AI
                "logs/ai/zaopatrzenie/dane_YYYYMMDD_HHMMSS.json",  # Zaopatrzenie AI
                "logs/ai/ekonomia/dane_YYYYMMDD_HHMMSS.json",      # Ekonomia AI
                "logs/human/akcje/dane_YYYYMMDD_HHMMSS.json",      # Akcje gracza ludzkiego
                "logs/human/decyzje/dane_YYYYMMDD_HHMMSS.json",    # Decyzje gracza ludzkiego  
                "logs/human/interfejs/dane_YYYYMMDD_HHMMSS.json",  # Interfejs gracza
                "logs/game/mechanika/dane_YYYYMMDD_HHMMSS.json",   # Mechanika gry
                "logs/game/stan/dane_YYYYMMDD_HHMMSS.json",        # Stan gry
                "logs/game/bledy/dane_YYYYMMDD_HHMMSS.json",       # Błędy gry
            ],
            "created_by": [
                "Nowy system logowania kategoryzowanego",
                "Każda kategoria ma osobny logger JSON",
                "Tworzony przez różne moduły AI i game"
            ],
            "cleanup": "✅ MOŻNA BEZPIECZNIE CZYŚCIĆ po sesji (ale sprawdź datę!)"
        },
        
        "📞 PHASE 4 - ADVANCED LOGISTICS": {
            "description": "Rozbudowane logi komunikacji AI Commander <-> AI General",
            "patterns": [
                "logs/ai_commander/force_analysis.csv",           # communication_ai.py
                "logs/ai_commander/reinforcement_requests.csv",   # communication_ai.py
                "logs/ai_general/communication_log.csv",          # communication_ai.py  
                "logs/ai_general/request_collection.csv",         # ekonomia_ai.py
                "logs/ai_general/purchase_priorities.csv",        # ekonomia_ai.py
                "logs/ai_general/adaptive_purchases.csv",         # ekonomia_ai.py
                "logs/garrison_issues/garrison_problems_YYYYMMDD.csv", # wsparcie_garnizonu.py
            ],
            "created_by": [
                "communication_ai.py - komunikacja między AI", 
                "ekonomia_ai.py - inteligentne zakupy",
                "wsparcie_garnizonu.py - problemy garnizonów"
            ],
            "cleanup": "🤔 CZĘŚCIOWO SESYJNE - sprawdź daty i zawartość"
        },

        "🛡️ DANE ARCHIWALNE (CHRONIONE)": {
            "description": "Wartościowe dane do długoterminowej analizy",
            "patterns": [
                "logs/analysis/ml_ready/ai_decyzje_*_meta.json",      # Metadane ML
                "logs/analysis/ml_ready/ekonomia_ai_*_meta.json",     # Metadane ekonomii ML
                "logs/analysis/ml_ready/*.csv",                       # Datasety ML  
                "logs/analysis/raporty/sesja_YYYYMMDD_HHMMSS.json",   # Raporty sesji
                "logs/analysis/statystyki/*.json",                    # Statystyki długoterminowe
                "logs/vp_intelligence/archives/*.csv",                # Archiwa VP Intelligence
            ],
            "created_by": [
                "System analizy ML - przetwarza logi na datasety",
                "Generator raportów sesji", 
                "VP Intelligence - śledzenie punktów zwycięstwa",
                "Statystyki długoterminowe"
            ],
            "cleanup": "🚫 NIGDY NIE CZYŚCIĆ! Bezcenne dane analityczne"
        },

        "🗂️ PLIKI KONFIGURACYJNE SESJI": {
            "description": "Pliki konfiguracji i stanu sesji",
            "patterns": [
                "data/strategic_orders.json",                    # Rozkazy strategiczne gracza
                "assets/tokens/nowe_dla_*/",                     # Zakupione żetony dla graczy
                "assets/tokens/aktualne/nowy_*.json",            # Nowe żetony w grze
                "data/map_data.json (sekcja 'token')",           # Rozmieszczone żetony na mapie
            ],
            "created_by": [
                "System rozkazów strategicznych",
                "System zakupów żetonów", 
                "Rozmieszczenie żetonów na mapie"
            ],
            "cleanup": "✅ CZYŚCIĆ po sesji (resetować do stanu początkowego)"
        }
    }
    
    # Wyświetl analizę
    for category, info in session_file_patterns.items():
        print(f"\n{category}")
        print("=" * (len(category) - 2))  # -2 bo emoji zajmuje 2 znaki w terminalu
        print(f"📝 {info['description']}")
        print()
        
        print("📁 WZORCE PLIKÓW:")
        for pattern in info['patterns']:
            print(f"   • {pattern}")
        
        print(f"\n🔧 TWORZONE PRZEZ:")
        for creator in info['created_by']:
            print(f"   • {creator}")
        
        print(f"\n🧹 CZYSZCZENIE:")
        print(f"   {info['cleanup']}")
    
    print(f"\n🎯 PODSUMOWANIE REKOMENDACJI:")
    print("=" * 40)
    
    print(f"\n✅ PLIKI SESYJNE (można czyścić po grze):")
    print(f"   • Wszystkie z datą dzisiejszą w nazwie")  
    print(f"   • logs/actions_*.csv")
    print(f"   • logs/ai_commander/actions_*.csv") 
    print(f"   • logs/ai_commander/turns_*.csv")
    print(f"   • logs/ai/*/dane_*.json (sprawdź daty!)")
    print(f"   • logs/human/*/dane_*.json")
    print(f"   • logs/game/*/dane_*.json")
    print(f"   • data/strategic_orders.json")
    print(f"   • assets/tokens/nowe_dla_*/")
    
    print(f"\n🛡️ PLIKI ARCHIWALNE (NIGDY nie czyścić!):")
    print(f"   • logs/analysis/ml_ready/* (BEZCENNE!)")
    print(f"   • logs/analysis/raporty/* (raporty sesji)")
    print(f"   • logs/analysis/statystyki/* (długoterminowe)")
    print(f"   • logs/vp_intelligence/archives/*")
    
    print(f"\n🤔 PLIKI MIESZANE (sprawdzać przed czyszczeniem):")
    print(f"   • logs/ai_commander/force_analysis.csv")
    print(f"   • logs/ai_general/*.csv")
    print(f"   • logs/garrison_issues/* (sprawdź daty)")
    
    print(f"\n⚠️ OBECNY STAN CZYSZCZENIA:")
    print(f"   🔧 Stary system: clean_csv_logs() NISZCZY dane ML")
    print(f"   ✅ Nowy system: czyszczenie_csv.py MA ochronę ML")  
    print(f"   💡 Rekomendacja: Używaj tylko nowego systemu czyszczenia")
    
    print(f"\n📋 WZORCE NAZW DO ROZPOZNAWANIA:")
    print(f"   SESYJNE: *YYYYMMDD*, dane_YYYYMMDD_HHMMSS.*, actions_*")
    print(f"   ARCHIWALNE: analysis/ml_ready/*, analysis/raporty/*, vp_intelligence/archives/*")
    print(f"   KONFIGURACYJNE: strategic_orders.json, nowe_dla_*, nowy_*.json")

if __name__ == "__main__":
    analyze_session_logs()