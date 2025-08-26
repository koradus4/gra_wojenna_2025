#!/usr/bin/env python3
"""
Test integracji AI w prawdziwej grze - analiza dlaczego AI nie porusza wszystkich żetonów
"""

import sys
import os
sys.path.append('.')

def analyze_ai_logs():
    print("🔍 ANALIZA LOGÓW AI Z PRAWDZIWEJ GRY")
    
    # Sprawdź najnowsze logi AI General
    ai_general_dir = "logs/ai_general"
    if os.path.exists(ai_general_dir):
        files = [f for f in os.listdir(ai_general_dir) if f.endswith('.csv')]
        if files:
            latest_files = sorted(files)[-3:]  # 3 najnowsze pliki
            print(f"\n📊 Najnowsze logi AI General: {latest_files}")
            
            for file in latest_files:
                file_path = os.path.join(ai_general_dir, file)
                print(f"\n📁 {file}:")
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        print(f"   Header: {lines[0].strip()}")
                        for line in lines[1:]:
                            print(f"   Data: {line.strip()}")
                    else:
                        print("   ❌ Brak danych")
    
    # Sprawdź logi AI Commander
    ai_commander_dir = "logs/ai_commander"
    if os.path.exists(ai_commander_dir):
        print(f"\n🤖 AI Commander folders:")
        for folder in os.listdir(ai_commander_dir):
            folder_path = os.path.join(ai_commander_dir, folder)
            if os.path.isdir(folder_path):
                print(f"   📁 {folder}:")
                
                # Sprawdź resupply logi
                resupply_files = [f for f in os.listdir(folder_path) if f.startswith('ai_resupply_')]
                if resupply_files:
                    latest_resupply = sorted(resupply_files)[-1]
                    resupply_path = os.path.join(folder_path, latest_resupply)
                    print(f"      🔧 Latest resupply: {latest_resupply}")
                    
                    with open(resupply_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) > 1:
                            for line in lines[-3:]:  # Ostatnie 3 linie
                                print(f"         {line.strip()}")
                        else:
                            print("         ❌ Brak danych resupply")
                
                # Sprawdź action logi
                action_files = [f for f in os.listdir(folder_path) if f.startswith('ai_actions_')]
                if action_files:
                    latest_action = sorted(action_files)[-1]
                    action_path = os.path.join(folder_path, latest_action)
                    print(f"      🎯 Latest actions: {latest_action}")
                    
                    with open(action_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) > 1:
                            for line in lines[-5:]:  # Ostatnie 5 linii
                                print(f"         {line.strip()}")
                        else:
                            print("         ❌ Brak danych actions")
    
    # Sprawdź główne logi akcji
    print(f"\n📋 GŁÓWNE LOGI AKCJI:")
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        action_files = [f for f in os.listdir(logs_dir) if f.startswith('actions_') and f.endswith('.csv')]
        if action_files:
            latest_action = sorted(action_files)[-1]
            action_path = os.path.join(logs_dir, latest_action)
            print(f"   📁 {latest_action}:")
            
            with open(action_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    print(f"   Header: {lines[0].strip()}")
                    
                    # Policz akcje per gracz
                    player_actions = {}
                    for line in lines[1:]:
                        parts = line.strip().split(',')
                        if len(parts) > 1:
                            player_id = parts[1] if len(parts) > 1 else 'unknown'
                            player_actions[player_id] = player_actions.get(player_id, 0) + 1
                    
                    print(f"   📊 Akcje per gracz: {player_actions}")
                    
                    # Pokaż ostatnie akcje
                    print(f"   🔍 Ostatnie 5 akcji:")
                    for line in lines[-5:]:
                        print(f"      {line.strip()}")
                else:
                    print("   ❌ Brak danych actions")

if __name__ == "__main__":
    analyze_ai_logs()
    
    print("\n🎮 === INSTRUKCJE TESTOWANIA ===")
    print("1. Uruchom: python main_ai.py")
    print("2. Wybierz AI dla Polski (Generał + Dowódcy)")
    print("3. Wykonaj 3-4 tury AI")
    print("4. Sprawdź czy wszystkie żetony się poruszają")
    print("5. Sprawdź logi powyżej")
    
    print("\n🔍 PYTANIA DO SPRAWDZENIA:")
    print("- Czy AI Commander wykonuje resupply?")
    print("- Czy AI Commander wykonuje akcje ruchu?")
    print("- Czy żetony mają paliwo po resupply?")
    print("- Czy są błędy w logach AI?")
