#!/usr/bin/env python3
"""
PROJEKT STRUKTURY logs/current_session/
=====================================
Dedykowany folder dla plików kasowanych co sesję gry
"""

def design_session_structure():
    """Zaprojektuj strukturę logs/current_session/"""
    
    print("🏗️ PROJEKT: logs/current_session/ STRUCTURE")
    print("=" * 60)
    print("🎯 CEL: Oddzielić pliki sesyjne od archiwalnych")
    print("🧹 EFEKT: Łatwe czyszczenie i analiza tylko bieżących danych")
    
    structure = {
        "logs/current_session/": {
            "description": "📁 Główny folder plików sesyjnych (kasowane co grę)",
            "contents": {
                "actions_YYYYMMDD_HHMMSS.csv": "🎮 Główny log akcji (action_logger.py)",
                "README_SESSION.md": "📝 Informacje o bieżącej sesji",
                
                "ai_commander/": {
                    "description": "🤖 Logi AI Commander",
                    "contents": {
                        "actions_YYYYMMDD.csv": "Szczegółowe akcje AI Commander",
                        "turns_YYYYMMDD.csv": "Podsumowania tur AI Commander",
                        "force_analysis.csv": "Analiza sił AI Commander",
                        "reinforcement_requests.csv": "Żądania wzmocnień"
                    }
                },
                
                "ai_general/": {
                    "description": "🏭 Logi AI General", 
                    "contents": {
                        "ai_purchases_YYYYMMDD.csv": "Zakupy AI General",
                        "communication_log.csv": "Komunikacja AI General",
                        "request_collection.csv": "Zbieranie żądań",
                        "purchase_priorities.csv": "Priorytety zakupów",
                        "adaptive_purchases.csv": "Adaptacyjne zakupy"
                    }
                },
                
                "specialized/": {
                    "description": "🔧 Specjalizowane logi",
                    "contents": {
                        "garrison_problems_YYYYMMDD.csv": "Problemy garnizonów",
                        "victory_ai_phase1_YYYYMMDD.csv": "Victory AI faza 1", 
                        "movement_test.log": "Debug ruchów jednostek"
                    }
                },
                
                "json_logs/": {
                    "description": "📋 Nowy system logowania JSON",
                    "contents": {
                        "ai/": "Logi AI (dowodca, general, strategia, walka, etc.)",
                        "human/": "Logi gracza ludzkiego",
                        "game/": "Logi mechaniki gry"
                    }
                }
            }
        },
        
        "logs/analysis/": {
            "description": "🛡️ ZACHOWANE - Dane długoterminowe (NIE kasowane)",
            "contents": {
                "ml_ready/": "Datasety ML i metadane",
                "raporty/": "Raporty sesji", 
                "statystyki/": "Statystyki długoterminowe"
            }
        }
    }
    
    def print_structure(data, indent=0):
        """Rekursywnie wyświetl strukturę"""
        prefix = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                desc = value.get("description", "")
                print(f"{prefix}📁 {key} {desc}")
                
                if "contents" in value:
                    print_structure(value["contents"], indent + 1)
            else:
                print(f"{prefix}📄 {key} - {value}")
    
    print_structure(structure)
    
    print(f"\n🎯 KORZYŚCI:")
    print("=" * 30)
    print("✅ CZYTELNOŚĆ: Jeden folder = jedna sesja gry")
    print("✅ BEZPIECZEŃSTWO: Dane ML oddzielone od sesyjnych")
    print("✅ ANALIZA: Łatwe znalezienie plików z bieżącej sesji")
    print("✅ CZYSZCZENIE: Jeden folder do wyczyszczenia") 
    print("✅ DEBUGOWANIE: Jasne co jest tymczasowe vs archiwalne")
    
    print(f"\n🔧 ZMIANY W KODZIE:")
    print("=" * 30)
    
    changes = [
        "utils/action_logger.py: logs/actions_*.csv → logs/current_session/actions_*.csv",
        "ai/logowanie_ai.py: logs/ai_commander/ → logs/current_session/ai_commander/",
        "ai/communication_ai.py: logs/ai_commander/force_analysis.csv → logs/current_session/ai_commander/",
        "ai/general_phase4.py: logs/ai_general/ → logs/current_session/ai_general/",
        "ai/wsparcie_garnizonu.py: logs/garrison_issues/ → logs/current_session/specialized/",
        "ai/victory_ai.py: logs/victory_ai_phase1_*.csv → logs/current_session/specialized/",
        "Nowy system JSON: logs/ai/, logs/human/, logs/game/ → logs/current_session/json_logs/"
    ]
    
    for i, change in enumerate(changes, 1):
        print(f"{i}. {change}")
    
    print(f"\n🧹 CZYSZCZENIE:")
    print("=" * 20)
    print("🗑️ DO KASOWANIA: rm -rf logs/current_session/*")  
    print("🛡️ ZACHOWANE: logs/analysis/* (bez zmian)")
    print("📝 EFEKT: Jasne rozgraniczenie sesyjne vs archiwalne")

if __name__ == "__main__":
    design_session_structure()