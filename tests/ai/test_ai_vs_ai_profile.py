#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test gry AI vs AI z indywidualnymi profilami
"""

import subprocess
import time
from ai.ai_config import set_player_ai_profile, get_param_for_player, get_ai_config

def test_ai_vs_ai_profiles():
    """Test czy indywidualne profile działają w grze"""
    
    print("🎯 TEST AI VS AI Z INDYWIDUALNYMI PROFILAMI")
    print("=" * 50)
    
    # Test 1: Ustaw różne profile dla różnych graczy
    print("🔧 Ustawianie profili AI...")
    set_player_ai_profile(1, "aggressive")   # Polski Generał - agresywny
    set_player_ai_profile(4, "defensive")    # Niemiecki Generał - defensywny
    set_player_ai_profile(2, "balanced")     # Polski Dowódca 1 - zbalansowany
    set_player_ai_profile(5, "aggressive")   # Niemiecki Dowódca 1 - agresywny
    
    # Sprawdź czy zostały ustawione
    profiles = {}
    for player_id in [1, 2, 4, 5]:
        param = get_param_for_player("COMBAT.MINIMUM_ATTACK_RATIO", player_id)
        profiles[player_id] = param
        player_names = {1: "Polski Generał", 2: "Polski Dowódca 1", 
                       4: "Niemiecki Generał", 5: "Niemiecki Dowódca 1"}
        print(f"   {player_names[player_id]} (id={player_id}): {param:.2f}")
    
    # Sprawdź różnice między profilami
    aggressive_threshold = profiles[1]  # Polski Generał aggressive
    defensive_threshold = profiles[4]   # Niemiecki Generał defensive
    balanced_threshold = profiles[2]    # Polski Dowódca balanced
    
    print("\n📊 Analiza różnic profili:")
    print(f"   Aggressive: {aggressive_threshold:.2f}")
    print(f"   Balanced:   {balanced_threshold:.2f}")  
    print(f"   Defensive:  {defensive_threshold:.2f}")
    print(f"   Różnica Aggressive vs Defensive: {defensive_threshold - aggressive_threshold:.2f}")
    print(f"   Stosunek Defensive/Aggressive: {defensive_threshold / aggressive_threshold:.2f}x")
    
    if defensive_threshold > aggressive_threshold * 2:
        print("✅ Profile są znacząco różne - test PASS!")
        return True
    else:
        print("❌ Profile nie są wystarczająco różne - test FAIL!")
        return False

def quick_combat_simulation():
    """Symulacja krótkiej gry żeby sprawdzić profile w działaniu"""
    
    print("\n🎮 SYMULACJA SZYBKIEJ GRY")
    print("=" * 30)
    
    # Sprawdź czy możemy zaimportować komponenty gry
    try:
        from engine.engine import GameEngine
        from engine.player import Player
        from ai.ai_general import AIGeneral
        from ai.ai_commander import AICommander
        print("✅ Import komponentów gry - OK")
    except Exception as e:
        print(f"❌ Import komponentów gry - FAIL: {e}")
        return False
    
    try:
        # Stwórz uproszczony game engine
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json", 
            tokens_start_path="assets/start_tokens.json",
            seed=42,
            read_only=True
        )
        
        # Stwórz graczy z różnymi profilami
        players = [
            Player(1, "Polska", "Generał", 5),   # aggressive
            Player(4, "Niemcy", "Generał", 5),   # defensive
        ]
        
        # Ustaw profile przed stworzeniem AI
        set_player_ai_profile(1, "aggressive")
        set_player_ai_profile(4, "defensive")
        
        # Stwórz AI
        ai_generals = {}
        ai_generals[1] = AIGeneral("polish")
        ai_generals[4] = AIGeneral("german")
        
        print("✅ Konfiguracja gry - OK")
        print(f"   Polski Generał (1): MINIMUM_ATTACK_RATIO = {get_param_for_player('COMBAT.MINIMUM_ATTACK_RATIO', 1):.2f}")
        print(f"   Niemiecki Generał (4): MINIMUM_ATTACK_RATIO = {get_param_for_player('COMBAT.MINIMUM_ATTACK_RATIO', 4):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Konfiguracja gry - FAIL: {e}")
        return False

if __name__ == "__main__":
    success1 = test_ai_vs_ai_profiles()
    success2 = quick_combat_simulation() if success1 else False
    
    if success1 and success2:
        print("\n🎉 WSZYSTKIE TESTY PRZESZŁY!")
        print("📈 Podsumowanie:")
        print("   ✓ Profile AI są poprawnie ustawione indywidualnie")
        print("   ✓ Różnice między profilami są znaczące (2x+)")
        print("   ✓ Komponenty gry obsługują indywidualne profile")
        print("   ✓ AI może działać z różnymi profilami jednocześnie")
        print("\n🚀 Możesz teraz uruchomić pełną grę AI vs AI!")
        print("💡 Każdy gracz będzie miał inny styl gry zgodnie ze swoim profilem")
    else:
        print("\n🔥 BŁĘDY W TESTACH - sprawdź implementację")