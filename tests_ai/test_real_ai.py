#!/usr/bin/env python3
"""
Test rzeczywistego AI w głównej grze - sprawdzenie alokacji w prawdziwym środowisku
"""

import sys
import os
sys.path.append('.')

def test_real_ai_in_game():
    print("🔧 Testing Real AI in Game Environment")
    
    # Uruchom główną grę i sprawdź logi
    print("🎯 Sprawdzamy logi AI z rzeczywistej gry...")
    
    # Sprawdź ostatnie logi AI General
    logs_dir = "logs/ai_general"
    if os.path.exists(logs_dir):
        economy_files = [f for f in os.listdir(logs_dir) if f.startswith('ai_economy_polska_')]
        if economy_files:
            latest_economy = sorted(economy_files)[-1]
            economy_path = os.path.join(logs_dir, latest_economy)
            
            print(f"📊 Reading latest economy log: {latest_economy}")
            
            with open(economy_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            if len(lines) > 1:  # Ma więcej niż header
                print("📋 Ostatnie wpisy ekonomii AI General:")
                for line in lines[-5:]:  # Ostatnie 5 linii
                    print(f"   {line.strip()}")
            else:
                print("❌ Brak wpisów w logu ekonomii")
        else:
            print("❌ Brak logów ekonomii AI General")
    else:
        print("❌ Brak katalogu logów AI General")
    
    # Sprawdź ostatnie logi AI Commander
    commander_logs_dir = "logs/ai_commander"
    if os.path.exists(commander_logs_dir):
        for cmd_id in [2, 3]:  # Sprawdź dowódców polskich
            cmd_dir = os.path.join(commander_logs_dir, f"commander_{cmd_id}")
            if os.path.exists(cmd_dir):
                resupply_files = [f for f in os.listdir(cmd_dir) if f.startswith('ai_resupply_')]
                if resupply_files:
                    latest_resupply = sorted(resupply_files)[-1]
                    resupply_path = os.path.join(cmd_dir, latest_resupply)
                    
                    print(f"🔧 Reading Commander {cmd_id} resupply log: {latest_resupply}")
                    
                    with open(resupply_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    if len(lines) > 1:
                        print(f"📋 Commander {cmd_id} ostatnie resupply:")
                        for line in lines[-3:]:  # Ostatnie 3 linie
                            print(f"   {line.strip()}")
                    else:
                        print(f"❌ Brak wpisów resupply dla Commander {cmd_id}")
    
    print("\n🎯 === URUCHOM RZECZYWISTĄ GRĘ ===")
    print("Aby przetestować pełny łańcuch AI:")
    print("1. Uruchom: python main.py")
    print("2. Wybierz gracza AI (Polska)")
    print("3. Wykonaj turę AI")
    print("4. Sprawdź logi w logs/ai_general/ i logs/ai_commander/")
    
    # Dodatkowo - sprawdź czy AI jest aktywne w main.py
    print("\n🔍 Sprawdzanie konfiguracji AI w main.py...")
    
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        if 'make_ai_turn' in main_content:
            print("✅ main.py zawiera obsługę AI turn")
        else:
            print("❌ main.py nie zawiera make_ai_turn")
            
        if 'AIGeneral' in main_content:
            print("✅ main.py importuje AIGeneral")
        else:
            print("❌ main.py nie importuje AIGeneral")
            
        if 'AICommander' in main_content:
            print("✅ main.py importuje AICommander") 
        else:
            print("❌ main.py nie importuje AICommander")
            
    except Exception as e:
        print(f"❌ Błąd czytania main.py: {e}")

if __name__ == "__main__":
    test_real_ai_in_game()
