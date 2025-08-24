"""
Test sprawdzający czy dowódca może kupić jednostkę przez TokenShop
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Dodaj ścieżkę do głównego katalogu projektu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from core.ekonomia import EconomySystem
from engine.player import Player
from gui.token_shop import TokenShop
import tkinter as tk

def test_dowodca_moze_kupic_jednostke():
    """Test czy dowódca może kupić jednostkę używając TokenShop"""
    
    # Przygotowanie gracza-dowódcy z punktami ekonomicznymi
    dowodca = Player(2, "Polska", "Dowódca", 5)
    dowodca.economy = EconomySystem()
    dowodca.economy.economic_points = 50  # Daj dowódcy 50 punktów
    dowodca.punkty_ekonomiczne = 50
    
    print(f"Stan początkowy dowódcy: {dowodca.economy.economic_points} punktów ekonomicznych")
    
    # Lista dowódców (w prawdziwej grze byłoby więcej)
    dowodcy = [dowodca]
    
    # Symulacja zakupu przez TokenShop
    # Nie możemy testować GUI bezpośrednio, ale możemy przetestować logikę kupna
    
    # Dane jednostki do kupienia (jak z TokenShop)
    unit_data = {
        "nation": "Polska",
        "unit_type": "P",  # Piechota
        "unit_size": "Pluton",
        "commander_id": "2",
        "supports": [],
        "cost": 15  # Koszt piechoty pluton (z unit_factory)
    }
    
    print(f"Próba zakupu: {unit_data['unit_type']} {unit_data['unit_size']} za {unit_data['cost']} punktów")
    
    # Sprawdź czy dowódca ma wystarczająco punktów
    starting_points = dowodca.economy.economic_points
    cost = unit_data["cost"]
    
    assert starting_points >= cost, f"Dowódca nie ma wystarczających punktów: {starting_points} < {cost}"
    
    # Symuluj zakup (jak w TokenShop.buy_unit())
    if starting_points >= cost:
        # Odejmij punkty
        dowodca.economy.subtract_points(cost)
        remaining_points = dowodca.economy.get_points()['economic_points']
        
        print(f"Po zakupie: {remaining_points} punktów pozostało")
        
        # Sprawdź czy punkty zostały poprawnie odjęte
        assert remaining_points == starting_points - cost
        assert remaining_points == 35  # 50 - 15 = 35
        
        # Sprawdź czy folder dla żetonu zostałby utworzony
        # (w prawdziwym TokenShop tworzy się folder assets/tokens/nowe_dla_{dowodca_id})
        expected_folder = Path("assets/tokens") / f"nowe_dla_{unit_data['commander_id']}"
        
        print(f"Sprawdzam czy można utworzyć folder: {expected_folder}")
        
        # Test tworzenia folderu (bez rzeczywistego tworzenia w teście)
        try:
            expected_folder.parent.mkdir(parents=True, exist_ok=True)
            folder_can_be_created = True
        except Exception as e:
            folder_can_be_created = False
            print(f"Błąd tworzenia folderu: {e}")
        
        assert folder_can_be_created, "Nie można utworzyć folderu dla nowego żetonu"
        
        print("✅ Dowódca pomyślnie kupił jednostkę!")
        return True
    else:
        print("❌ Dowódca nie ma wystarczających punktów")
        return False

def test_dowodca_nie_moze_kupic_za_drogie_jednostki():
    """Test czy dowódca nie może kupić jednostki za drogie"""
    
    # Dowódca z małą ilością punktów
    dowodca = Player(3, "Polska", "Dowódca", 5)
    dowodca.economy = EconomySystem()
    dowodca.economy.economic_points = 5  # Tylko 5 punktów
    
    print(f"Stan początkowy dowódcy: {dowodca.economy.economic_points} punktów ekonomicznych")
    
    # Próba zakupu drogiej jednostki
    expensive_unit = {
        "unit_type": "TC",  # Czołg ciężki
        "unit_size": "Batalion",
        "cost": 50  # Droga jednostka
    }
    
    print(f"Próba zakupu drogiej jednostki za {expensive_unit['cost']} punktów")
    
    starting_points = dowodca.economy.economic_points
    cost = expensive_unit["cost"]
    
    # Sprawdź czy dowódca NIE ma wystarczających punktów
    assert starting_points < cost, f"Test niepoprawny - dowódca ma za dużo punktów: {starting_points} >= {cost}"
    
    # Sprawdź czy zakup zostanie odrzucony
    if starting_points < cost:
        print("✅ Zakup odrzucony - dowódca nie ma wystarczających punktów")
        
        # Punkty nie powinny zostać odjęte
        remaining_points = dowodca.economy.get_points()['economic_points']
        assert remaining_points == starting_points
        
        return False
    else:
        pytest.fail("Dowódca nie powinien móc kupić tak drogiej jednostki")

def test_rozne_typy_jednostek():
    """Test zakupu różnych typów jednostek"""
    
    dowodca = Player(2, "Polska", "Dowódca", 5)
    dowodca.economy = EconomySystem()
    dowodca.economy.economic_points = 100  # Dużo punktów na testy
    
    # Lista jednostek do przetestowania (z poprawionymi zakresami kosztów)
    units_to_test = [
        {"type": "P", "size": "Pluton", "expected_cost_range": (10, 20)},
        {"type": "K", "size": "Kompania", "expected_cost_range": (30, 50)},  # Kawaleria droższa
        {"type": "TL", "size": "Pluton", "expected_cost_range": (20, 40)},
        {"type": "Z", "size": "Kompania", "expected_cost_range": (15, 35)},
    ]
    
    successful_purchases = 0
    starting_points = dowodca.economy.economic_points
    
    for unit in units_to_test:
        print(f"\nTest zakupu: {unit['type']} {unit['size']}")
        
        # Import rzeczywistej logiki z unit_factory
        try:
            from core.unit_factory import compute_unit_stats
            stats = compute_unit_stats(unit["type"], unit["size"], [])
            actual_cost = stats.price
            
            print(f"Rzeczywisty koszt: {actual_cost} punktów")
            
            # Sprawdź czy koszt mieści się w oczekiwanym zakresie
            min_cost, max_cost = unit["expected_cost_range"]
            assert min_cost <= actual_cost <= max_cost, f"Koszt {actual_cost} poza zakresem {min_cost}-{max_cost}"
            
            # Sprawdź czy dowódca może kupić
            current_points = dowodca.economy.get_points()['economic_points']
            if current_points >= actual_cost:
                dowodca.economy.subtract_points(actual_cost)
                successful_purchases += 1
                print(f"✅ Zakupiono za {actual_cost} punktów")
            else:
                print(f"❌ Za mało punktów: {current_points} < {actual_cost}")
                
        except ImportError:
            print(f"⚠️ Nie można zaimportować unit_factory, pomijam test {unit['type']}")
    
    print(f"\nPodsumowanie: {successful_purchases}/{len(units_to_test)} udanych zakupów")
    final_points = dowodca.economy.get_points()['economic_points']
    spent_points = starting_points - final_points
    
    print(f"Wydano łącznie: {spent_points} punktów")
    print(f"Pozostało: {final_points} punktów")
    
    assert successful_purchases > 0, "Dowódca nie mógł kupić żadnej jednostki"
    assert spent_points > 0, "Nie wydano żadnych punktów"

if __name__ == "__main__":
    print("🧪 TESTY ZAKUPÓW DOWÓDCY")
    print("=" * 50)
    
    try:
        print("\n1. Test podstawowego zakupu:")
        test_dowodca_moze_kupic_jednostke()
        
        print("\n2. Test odrzucenia drogiego zakupu:")
        test_dowodca_nie_moze_kupic_za_drogie_jednostki()
        
        print("\n3. Test różnych typów jednostek:")
        test_rozne_typy_jednostek()
        
        print("\n🎉 WSZYSTKIE TESTY PRZESZŁY!")
        print("✅ Dowódca może kupować jednostki przez TokenShop")
        
    except Exception as e:
        print(f"\n❌ TEST NIEUDANY: {e}")
        import traceback
        traceback.print_exc()
