#!/usr/bin/env python3
"""
Debug systemu ról graczy
========================

Sprawdza problem z rolami graczy w systemie key_points.

Autor: Debug Team
Data: 3 lipca 2025
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def debug_roles():
    """Debug ról graczy"""
    print("🔍 DEBUG RÓL GRACZY")
    print("=" * 30)
    
    from engine.player import Player
    from core.ekonomia import EconomySystem
    
    # Test różnych wariantów roli
    test_roles = ["generał", "Generał", "GENERAŁ", "general", "General"]
    
    for role in test_roles:
        player = Player("1", "Test", "Polska", role)
        player.economy = EconomySystem()
        
        # Test warunku z kodu
        condition1 = getattr(player, 'role', '').lower() == 'generał'
        condition2 = getattr(player, 'role', '').lower() == 'general'
        
        print(f"Rola: '{role}'")
        print(f"   ├─ getattr(p, 'role', ''): '{getattr(player, 'role', '')}'")
        print(f"   ├─ .lower(): '{getattr(player, 'role', '').lower()}'")
        print(f"   ├─ == 'generał': {condition1}")
        print(f"   └─ == 'general': {condition2}")
    
    print("\n🔍 TEST Z PRAWIDŁOWĄ ROLĄ:")
    
    # Utwórz gracza z rolą która powinna działać
    player = Player("1", "Polski Generał", "Polska", "generał")
    player.economy = EconomySystem()
    
    print(f"Utworzony gracz:")
    print(f"   ├─ ID: {player.id}")
    print(f"   ├─ Nacja: {player.nation}")
    print(f"   ├─ Rola: '{player.role}'")
    print(f"   ├─ Rola lower: '{player.role.lower()}'")
    print(f"   └─ Ma economy: {hasattr(player, 'economy')}")
    
    # Test warunków
    players = [player]
    generals1 = {p.nation: p for p in players if getattr(p, 'role', '').lower() == 'generał'}
    generals2 = {p.nation: p for p in players if getattr(p, 'role', '').lower() == 'general'}
    
    print(f"\nFiltrowanie:")
    print(f"   ├─ Z 'generał': {len(generals1)} graczy")
    print(f"   └─ Z 'general': {len(generals2)} graczy")
    
    return True

if __name__ == '__main__':
    debug_roles()
