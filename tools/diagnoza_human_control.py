#!/usr/bin/env python3
"""
DIAGNOZA PROBLEMU: Dlaczego gracz human nie może grać?
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.player import Player
from engine.engine import GameEngine

def diagnozuj_problem_human_control():
    """Diagnoza dlaczego gracz nie może kontrolować jednostek"""
    print("🔍 DIAGNOZA: Problem kontroli jednostek przez gracza human")
    print("=" * 60)
    
    # 1. Sprawdź konfigurację domyślną
    print("\n1️⃣ SPRAWDZENIE KONFIGURACJI DOMYŚLNEJ:")
    
    # Importuj GameLauncher
    from main import GameLauncher
    launcher = GameLauncher()
    
    print(f"🏴󠁧󠁢󠁰󠁬󠁳󠁿 Polski Generał AI: {launcher.ai_polish_general.get()}")
    print(f"🇩🇪 Niemiecki Generał AI: {launcher.ai_german_general.get()}")
    print(f"🏴󠁧󠁢󠁰󠁬󠁳󠁿 Polski Dowódca 1 AI: {launcher.ai_polish_commander_1.get()}")
    print(f"🏴󠁧󠁢󠁰󠁬󠁳󠁿 Polski Dowódca 2 AI: {launcher.ai_polish_commander_2.get()}")
    print(f"🇩🇪 Niemiecki Dowódca 1 AI: {launcher.ai_german_commander_1.get()}")
    print(f"🇩🇪 Niemiecki Dowódca 2 AI: {launcher.ai_german_commander_2.get()}")
    
    # 2. Sprawdź które jednostki są przypisane do którego gracza
    print("\n2️⃣ SPRAWDZENIE PRZYPISANIA JEDNOSTEK:")
    
    try:
        engine = GameEngine(
            map_path="data/map_data.json", 
            tokens_index_path="assets/tokens/index.json",
            tokens_start_path="assets/start_tokens.json"
        )
        
        # Zlicz jednostki na gracza
        jednostki_gracza = {}
        
        for token in engine.tokens:
            owner = getattr(token, 'owner', 'UNKNOWN')
            if owner not in jednostki_gracza:
                jednostki_gracza[owner] = []
            jednostki_gracza[owner].append(token.id)
        
        print("📊 JEDNOSTKI PRZYPISANE DO GRACZY:")
        for owner, tokens in jednostki_gracza.items():
            print(f"   {owner}: {len(tokens)} jednostek")
            for token_id in tokens[:3]:  # Pokaż pierwsze 3
                print(f"      - {token_id}")
            if len(tokens) > 3:
                print(f"      ... i {len(tokens) - 3} więcej")
    
    except Exception as e:
        print(f"❌ Błąd ładowania silnika: {e}")
    
    # 3. Sprawdź ustawienia AI w logach
    print("\n3️⃣ SPRAWDZENIE LOGÓW AI:")
    try:
        with open("logs/ai_commander/actions_20250914.csv", "r", encoding="utf-8") as f:
            lines = f.readlines()
            ai_units = set()
            for line in lines[1:11]:  # Pierwszych 10 linii po nagłówku
                parts = line.strip().split(',')
                if len(parts) > 0:
                    ai_units.add(parts[0])
            
            print(f"📋 AI kontroluje jednostki: {', '.join(list(ai_units)[:5])}...")
    except Exception as e:
        print(f"⚠️ Nie można odczytać logów AI: {e}")
    
    # 4. DIAGNOZA PROBLEMU
    print("\n4️⃣ DIAGNOZA PROBLEMU:")
    
    wszystkie_ai = (
        launcher.ai_polish_general.get() and
        launcher.ai_german_general.get() and
        launcher.ai_polish_commander_1.get() and
        launcher.ai_polish_commander_2.get() and
        launcher.ai_german_commander_1.get() and
        launcher.ai_german_commander_2.get()
    )
    
    if wszystkie_ai:
        print("❌ PROBLEM: Wszyscy gracze mają włączone AI!")
        print("   💡 ROZWIĄZANIE: Wyłącz AI dla wybranego gracza w launcherze")
        print("   📱 INSTRUKCJA: Uruchom main.py → Odznacz checkboxy AI")
    else:
        print("✅ Konfiguracja AI nie jest problemem")
    
    print("\n5️⃣ INSTRUKCJE NAPRAWY:")
    print("1. Uruchom: python main.py")
    print("2. W sekcji 'Konfiguracja AI' odznacz checkboxy dla gracza którego chcesz kontrolować")
    print("3. Na przykład: odznacz 'Polski Dowódca 1 (id=2) - AI' dla kontroli dowódcy 2")
    print("4. Kliknij 'Uruchom Grę'")
    print("5. Gdy przyjdzie tura tego gracza, zostanie otwarty panel GUI")
    
    return not wszystkie_ai

if __name__ == "__main__":
    sukces = diagnozuj_problem_human_control()
    if sukces:
        print("\n🎉 System skonfigurowany prawidłowo!")
    else:
        print("\n⚠️ System wymaga konfiguracji!")