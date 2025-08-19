#!/usr/bin/env python3
"""
Test sklepu jednostek - sprawdza czy można kupować wszystkie dostępne jednostki
"""

import tkinter as tk
from tkinter import messagebox
import sys
from pathlib import Path
import pytest

# Dodaj ścieżki do modułów
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "gui"))
sys.path.append(str(project_root / "core"))

try:
    from gui.token_shop import TokenShop
    from core.ekonomia import Ekonomia
    print("✓ Importy TokenShop i Ekonomia udane")
except ImportError as e:
    print(f"✗ Błąd importu: {e}")
    sys.exit(1)

# Mock klasa dla dowódców
class MockCommander:
    def __init__(self, commander_id, name):
        self.id = commander_id
        self.name = name

# Mock klasa dla ekonomii
class TestEkonomia:
    def __init__(self, initial_points=1000):
        self.points = initial_points
    
    def get_points(self):
        return {'economic_points': self.points}
    
    def subtract_points(self, amount):
        self.points -= amount
        print(f"📉 Odjęto {amount} punktów, pozostało: {self.points}")

@pytest.mark.skip(reason="GUI test pomijany w pakiecie headless – uruchom manualnie gdy dostępne środowisko graficzne.")
def test_sklep_jednostek():
    """Test główny - tworzy sklep i sprawdza dostępne jednostki"""
    print("🛒 ROZPOCZYNAM TEST SKLEPU JEDNOSTEK")
    print("=" * 50)
    
    # Tworzenie głównego okna
    root = tk.Tk()
    root.withdraw()  # Ukryj główne okno
    
    # Mock dane
    ekonomia = TestEkonomia(initial_points=2000)
    dowodcy = [
        MockCommander("2", "Dowódca Polski"),
        MockCommander("3", "Generał Polski"),
        MockCommander("5", "Dowódca Niemiecki"),
        MockCommander("6", "Generał Niemiecki")
    ]
    
    def callback_zakupu():
        print("🎉 Callback zakupu wywołany!")
    
    print(f"💰 Punkty początkowe: {ekonomia.get_points()['economic_points']}")
    print(f"👥 Liczba dowódców: {len(dowodcy)}")
    
    try:
        # Tworzenie sklepu
        print("\n🏪 Tworzę sklep jednostek...")
        sklep = TokenShop(
            parent=root,
            ekonomia=ekonomia,
            dowodcy=dowodcy,
            on_purchase_callback=callback_zakupu,
            nation="Polska"
        )
        
        print("✓ Sklep utworzony pomyślnie!")
        
        # Sprawdzenie dostępnych jednostek
        print("\n📋 DOSTĘPNE JEDNOSTKI W SKLEPIE:")
        print("-" * 40)
        
        dostepne_jednostki = []
        for name, code, active in sklep.unit_type_order:
            status = "✓ DOSTĘPNA" if active else "✗ NIEDOSTĘPNA"
            print(f"{code:3} | {name:25} | {status}")
            if active:
                dostepne_jednostki.append((name, code))
        
        print(f"\n📊 PODSUMOWANIE:")
        print(f"Wszystkich typów jednostek: {len(sklep.unit_type_order)}")
        print(f"Dostępnych w sklepie: {len(dostepne_jednostki)}")
        print(f"Procent dostępności: {len(dostepne_jednostki)/len(sklep.unit_type_order)*100:.1f}%")
        
        # Test statystyk dla każdej jednostki
        print(f"\n🔢 SPRAWDZANIE STATYSTYK JEDNOSTEK:")
        print("-" * 50)
        
        for name, code in dostepne_jednostki[:5]:  # Test pierwszych 5
            sklep.unit_type.set(code)
            sklep.unit_size.set("Pluton")
            sklep.update_stats()
            
            stats = sklep.current_stats
            print(f"{name} ({code}):")
            print(f"  Koszt: {stats['cena']} | Atak: {stats['atak']} | Obrona: {stats['obrona']} | Ruch: {stats['ruch']}")
        
        # Test wsparcia
        print(f"\n🛠️ SPRAWDZANIE SYSTEMU WSPARCIA:")
        print("-" * 40)
        
        print(f"Dostępne wsparcia: {len(sklep.support_upgrades)} typów")
        for sup_name, sup_stats in list(sklep.support_upgrades.items())[:3]:
            print(f"  {sup_name}: koszt +{sup_stats['purchase']}, atak +{sup_stats['attack']}")
        
        # Test czy wszystkie jednostki mają poprawne statystyki
        print(f"\n🧪 TEST KOMPLETNOŚCI STATYSTYK:")
        print("-" * 35)
        
        problemy = []
        for name, code in dostepne_jednostki:
            for size in ["Pluton", "Kompania", "Batalion"]:
                sklep.unit_type.set(code)
                sklep.unit_size.set(size)
                try:
                    sklep.update_stats()
                    if sklep.current_stats['cena'] <= 0:
                        problemy.append(f"{name} {size}: brak ceny")
                except Exception as e:
                    problemy.append(f"{name} {size}: błąd - {e}")
        
        if problemy:
            print("⚠️ ZNALEZIONE PROBLEMY:")
            for problem in problemy[:5]:  # Pokaż max 5
                print(f"  - {problem}")
        else:
            print("✓ Wszystkie jednostki mają poprawne statystyki!")
        
        print(f"\n🎯 WYNIK TESTU:")
        print("=" * 30)
        if len(dostepne_jednostki) == len(sklep.unit_type_order) and not problemy:
            print("🟢 SUKCES: Wszystkie jednostki dostępne i działają!")
        elif len(dostepne_jednostki) == len(sklep.unit_type_order):
            print("🟡 CZĘŚCIOWY SUKCES: Wszystkie dostępne, ale są problemy ze statystykami")
        else:
            print("🔴 PROBLEM: Nie wszystkie jednostki są dostępne")
        
        print(f"\n👀 Sklep jest otwarty - możesz go przetestować ręcznie!")
        print(f"💡 Zamknij okno sklepu aby zakończyć test.")
        
        # Pokaż sklep
        sklep.deiconify()  # Upewnij się że jest widoczny
        sklep.lift()       # Przenieś na wierzch
        sklep.focus_force() # Daj focus
        
        # Uruchom główną pętlę
        root.mainloop()
        
    except Exception as e:
        print(f"❌ BŁĄD PODCZAS TESTU: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 URUCHAMIAM TEST SKLEPU JEDNOSTEK...")
    print("📝 Test sprawdzi:")
    print("   - Czy wszystkie jednostki są dostępne")
    print("   - Czy mają poprawne statystyki") 
    print("   - Czy system wsparcia działa")
    print("   - Czy można otworzyć sklep")
    print()
    
    sukces = test_sklep_jednostek()
    
    if sukces:
        print("\n✅ TEST ZAKOŃCZONY")
    else:
        print("\n❌ TEST NIEUDANY")
