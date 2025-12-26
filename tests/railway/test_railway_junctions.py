"""Test funkcji rozjazdów."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "edytory"))

from generate_railway_hex_tile import RailwayOptions, generate_railway

def test_junction():
    """Test rozjazdu jednotorowego i dwutorowego."""
    print("=" * 60)
    print("TEST: Rozjazdy (jednotorowy vs dwutorowy)")
    print("=" * 60)
    
    output_dir = Path(__file__).parent.parent / "assets" / "terrain" / "railways" / "test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test 1: Rozjazd jednotorowy
    print("\n--- Rozjazd JEDNOTOROWY ---")
    output_path1 = output_dir / "test_junction_single.png"
    
    options1 = RailwayOptions(
        grid_size=64,
        background=None,
        entry_side="top",
        exit_side="bottom",
        railway_type="dwutorowy",
        seed=500,
        junctions=["top_left"],  # Rozjazd w górę-lewo
        junction_double_track=False  # JEDNOTOROWY rozjazd
    )
    
    try:
        result1 = generate_railway(options1, output_path1)
        print(f"✅ Wygenerowano: {result1.image_path.name}")
        print(f"   Główny tor: dwutorowy")
        print(f"   Rozjazd top_left: jednotorowy")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # Test 2: Rozjazd dwutorowy
    print("\n--- Rozjazd DWUTOROWY ---")
    output_path2 = output_dir / "test_junction_double.png"
    
    options2 = RailwayOptions(
        grid_size=64,
        background=None,
        entry_side="top",
        exit_side="bottom",
        railway_type="dwutorowy",
        seed=501,
        junctions=["top_left"],  # Rozjazd w górę-lewo
        junction_double_track=True  # DWUTOROWY rozjazd
    )
    
    try:
        result2 = generate_railway(options2, output_path2)
        print(f"✅ Wygenerowano: {result2.image_path.name}")
        print(f"   Główny tor: dwutorowy")
        print(f"   Rozjazd top_left: DWUTOROWY")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ TEST PASSED: Oba typy rozjazdów działają!")
    print("=" * 60)
    print(f"\nPorównaj pliki:")
    print(f"  Jednotorowy: {output_path1.name}")
    print(f"  Dwutorowy:   {output_path2.name}")
    
    return True

if __name__ == "__main__":
    success = test_junction()
    sys.exit(0 if success else 1)
