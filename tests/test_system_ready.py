#!/usr/bin/env python3
"""
Szybki test importów i inicjalizacji silnika gry
"""
import sys
import os

# Dodaj folder główny
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_game_engine():
    """Test silnika gry"""
    print("=== TEST SILNIKA GRY ===")
    
    try:
        from engine.engine import GameEngine
        print("✓ GameEngine zaimportowany")
        
        # Test inicjalizacji
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json",
            tokens_start_path="assets/start_tokens.json",
            seed=42,
            read_only=True
        )
        
        print("✓ GameEngine zainicjalizowany")
        print(f"  - Tokenów: {len(game_engine.tokens)}")
        print(f"  - Rozmiar mapy: {game_engine.board.size if hasattr(game_engine.board, 'size') else 'nieznany'}")
        
        # Test niektórych tokenów
        if game_engine.tokens:
            for i, token in enumerate(game_engine.tokens[:5]):  # Pokaż pierwsze 5
                name = getattr(token, 'name', token.id)  # Użyj ID jako nazwa jeśli brak name
                print(f"  - Token {i+1}: {name} (właściciel: {token.owner})")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def test_ai_imports():
    """Test importów AI"""
    print("\n=== TEST IMPORTÓW AI ===")
    
    try:
        from main_ai_vs_human import LearningAIGeneral, LearningAICommander, AIManager
        print("✓ Klasy AI zaimportowane")
        
        from main_ai_vs_human import NationSelectionDialog
        print("✓ Dialog wyboru nacji zaimportowany")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd importu AI: {e}")
        return False

def test_gui_imports():
    """Test importów GUI"""
    print("\n=== TEST IMPORTÓW GUI ===")
    
    try:
        import tkinter as tk
        print("✓ tkinter dostępny")
        
        from gui.panel_generala import PanelGenerala
        print("✓ PanelGenerala zaimportowany")
        
        from gui.panel_dowodcy import PanelDowodcy
        print("✓ PanelDowodcy zaimportowany")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd importu GUI: {e}")
        return False

if __name__ == "__main__":
    print("🎮 TEST GOTOWOŚCI SYSTEMU KAMPANIA 1939")
    print("=" * 50)
    
    success = True
    
    # Test 1: Silnik gry
    if not test_game_engine():
        success = False
    
    # Test 2: Importy AI
    if not test_ai_imports():
        success = False
    
    # Test 3: Importy GUI
    if not test_gui_imports():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
        print("🎮 Gra jest gotowa do uruchomienia")
        print("\nDostępne tryby:")
        print("1. python main.py - Tryb normalny")
        print("2. python main_alternative.py - Tryb alternatywny")
        print("3. python main_ai_vs_human.py - Tryb AI vs Człowiek")
    else:
        print("❌ NIEKTÓRE TESTY NIE POWIODŁY SIĘ!")
        print("Sprawdź błędy powyżej")
    
    print("=" * 50)
