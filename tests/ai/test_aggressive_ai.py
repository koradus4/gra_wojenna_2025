#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 TEST AGGRESSIVE AI - sprawdza czy agresywny profil rzeczywiście atakuje

Ustawia profil AGGRESSIVE (ratio 0.72) i testuje czy AI w końcu atakuje!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ai.ai_config import set_ai_profile, get_param, AIProfile

def setup_aggressive_profile():
    """Ustawia profil aggressive i pokazuje parametry"""
    print("🔥 USTAWIAM PROFIL AGGRESSIVE")
    print("="*40)
    
    set_ai_profile(AIProfile.AGGRESSIVE)
    
    ratio = get_param('COMBAT.MINIMUM_ATTACK_RATIO', 1.2)
    threat = get_param('COMBAT.THREAT_RETREAT_THRESHOLD', 5)
    counter = get_param('COMBAT.COUNTER_ATTACK_MAX_PENALTY', 0.6)
    
    print(f"⚔️ MINIMUM_ATTACK_RATIO: {ratio} (zamiast 1.2)")
    print(f"🏃 THREAT_RETREAT_THRESHOLD: {threat}")  
    print(f"🛡️ COUNTER_ATTACK_MAX_PENALTY: {counter}")
    print()
    print("✅ AI powinno teraz atakować przy ratio 0.72 zamiast 1.2!")
    print("   To oznacza że atak przy 72% przewagi jest OK!")
    print()

def main():
    setup_aggressive_profile()
    
    print("🎮 Teraz uruchom szybki test żeby zobaczyć czy AI atakuje:")
    print("   python szybki_test_gry.py --scenario quick_aggressive")
    print()
    print("🔍 W logach szukaj:")
    print("   🎯 [COMBAT] {unit} atakuje {enemy}")
    print("   ⚔️ [COMBAT DEBUG] Próg ataku = 0.72")
    print("   🎲 [COMBAT DEBUG] ratio = {wartość >= 0.72}")

if __name__ == "__main__":
    main()