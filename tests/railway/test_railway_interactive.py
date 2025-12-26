"""Test interaktywnego generowania torów - symulacja użytkownika."""

from pathlib import Path
import sys

# Dodaj katalog edytory do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent / "edytory"))

from generate_railway_hex_tile import RailwayOptions, generate_railway

def test_basic_railway_generation():
    """Test podstawowego generowania torów - prosty odcinek."""
    print("=" * 60)
    print("TEST 1: Prosty tor (top → bottom)")
    print("=" * 60)
    
    output_dir = Path(__file__).parent.parent / "assets" / "terrain" / "railways" / "test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "test_straight.png"
    
    options = RailwayOptions(
        grid_size=64,
        background=None,
        entry_side="top",
        exit_side="bottom",
        railway_type="jednotorowy",
        seed=42,
        junctions=[],
        junction_double_track=False
    )
    
    try:
        result = generate_railway(options, output_path)
        print(f"✅ Wygenerowano: {result.image_path}")
        print(f"📋 Metadane: {result.metadata}")
        
        # Sprawdź czy plik istnieje
        assert result.image_path.exists(), "Plik obrazu nie istnieje!"
        assert result.metadata_path.exists(), "Plik metadanych nie istnieje!"
        assert result.metadata["entry_side"] == "top"
        assert result.metadata["exit_side"] == "bottom"
        
        print("✅ TEST PASSED: Prosty tor działa!")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_curved_railway():
    """Test zakrętu - jak w interaktywnym trybie."""
    print("\n" + "=" * 60)
    print("TEST 2: Zakręt (top_left → bottom_right)")
    print("=" * 60)
    
    output_dir = Path(__file__).parent.parent / "assets" / "terrain" / "railways" / "test"
    output_path = output_dir / "test_curved.png"
    
    options = RailwayOptions(
        grid_size=64,
        background=None,
        entry_side="top_left",
        exit_side="bottom_right",
        railway_type="dwutorowy",
        seed=123,
        junctions=[],
        junction_double_track=False
    )
    
    try:
        result = generate_railway(options, output_path)
        print(f"✅ Wygenerowano: {result.image_path}")
        print(f"📋 Metadane: {result.metadata}")
        
        assert result.image_path.exists()
        assert result.metadata["entry_side"] == "top_left"
        assert result.metadata["exit_side"] == "bottom_right"
        
        print("✅ TEST PASSED: Zakręt działa!")
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_railway_path_simulation():
    """Symulacja trasy z 3 heksów - jak użytkownik by klikał."""
    print("\n" + "=" * 60)
    print("TEST 3: Symulacja trasy 3 heksów (A→B→C)")
    print("=" * 60)
    
    # Symulacja: Użytkownik kliknął heksy (5,3) → (6,3) → (7,3)
    # To jest pozioma linia w prawo
    
    railway_path = ["5,3", "6,3", "7,3"]
    output_dir = Path(__file__).parent.parent / "assets" / "terrain" / "railways" / "test"
    
    print(f"Trasa: {' → '.join(railway_path)}")
    
    # Słownik kierunków między heksami (axial)
    AXIAL_DIRECTION_TO_SIDE = {
        (1, 0): "bottom_right",
        (1, -1): "top_right",
        (0, -1): "top",
        (-1, 0): "top_left",
        (-1, 1): "bottom_left",
        (0, 1): "bottom",
    }
    
    SIDE_OPPOSITE = {
        "top": "bottom",
        "top_right": "bottom_left",
        "bottom_right": "top_left",
        "bottom": "top",
        "bottom_left": "top_right",
        "top_left": "bottom_right",
    }
    
    def get_hex_delta(from_hex, to_hex):
        q1, r1 = map(int, from_hex.split(","))
        q2, r2 = map(int, to_hex.split(","))
        return (q2 - q1, r2 - r1)
    
    def get_side_between(from_hex, to_hex):
        delta = get_hex_delta(from_hex, to_hex)
        return AXIAL_DIRECTION_TO_SIDE.get(delta)
    
    all_passed = True
    
    for i, hex_id in enumerate(railway_path):
        print(f"\n--- Heks {i+1}/3: {hex_id} ---")
        
        if i == 0:
            # Pierwszy heks - exit=kierunek do następnego, entry=opposite
            exit_direction = get_side_between(hex_id, railway_path[i + 1])
            exit_side = exit_direction
            entry_side = SIDE_OPPOSITE.get(exit_side) if exit_side else "top"
        elif i == len(railway_path) - 1:
            # Ostatni heks - entry=bok z poprzedniego, exit=opposite
            entry_direction = get_side_between(railway_path[i - 1], hex_id)
            entry_side = SIDE_OPPOSITE.get(entry_direction) if entry_direction else "bottom"
            exit_side = SIDE_OPPOSITE.get(entry_side) if entry_side else "top"
        else:
            # Środkowy heks - entry z poprzedniego, exit do następnego
            entry_direction = get_side_between(railway_path[i - 1], hex_id)
            entry_side = SIDE_OPPOSITE.get(entry_direction) if entry_direction else "top"
            exit_direction = get_side_between(hex_id, railway_path[i + 1])
            exit_side = exit_direction if exit_direction else "bottom"
        
        print(f"Entry: {entry_side}, Exit: {exit_side}")
        
        # Sprawdź czy entry != exit (chyba że jeden jest None)
        if entry_side and exit_side and entry_side == exit_side:
            print(f"❌ BŁĄD: Entry i Exit są takie same! ({entry_side})")
            all_passed = False
            continue
        
        output_path = output_dir / f"test_path_{hex_id.replace(',', '_')}.png"
        
        options = RailwayOptions(
            grid_size=64,
            background=None,
            entry_side=entry_side,
            exit_side=exit_side,
            railway_type="jednotorowy",
            seed=42 + i,
            junctions=[],
            junction_double_track=False
        )
        
        try:
            result = generate_railway(options, output_path)
            print(f"✅ Wygenerowano: {result.image_path.name}")
            
            # Sprawdź metadane
            meta = result.metadata
            if meta["entry_side"] != entry_side:
                print(f"⚠️  Entry mismatch: expected={entry_side}, got={meta['entry_side']}")
            if meta["exit_side"] != exit_side:
                print(f"⚠️  Exit mismatch: expected={exit_side}, got={meta['exit_side']}")
                
        except Exception as e:
            print(f"❌ Generowanie FAILED: {e}")
            all_passed = False
    
    if all_passed:
        print("\n✅ TEST PASSED: Cała trasa wygenerowana poprawnie!")
    else:
        print("\n❌ TEST FAILED: Były błędy w trasie!")
    
    return all_passed


def main():
    print("🚂 TEST GENERATORA TORÓW KOLEJOWYCH")
    print("=" * 60)
    
    results = []
    
    # Test 1: Prosty tor
    results.append(("Prosty tor", test_basic_railway_generation()))
    
    # Test 2: Zakręt
    results.append(("Zakręt", test_curved_railway()))
    
    # Test 3: Symulacja trasy
    results.append(("Trasa 3 heksy", test_railway_path_simulation()))
    
    # Podsumowanie
    print("\n" + "=" * 60)
    print("PODSUMOWANIE TESTÓW")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 WSZYSTKIE TESTY PRZESZŁY!")
        return 0
    else:
        print("\n⚠️  NIEKTÓRE TESTY NIE PRZESZŁY!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
