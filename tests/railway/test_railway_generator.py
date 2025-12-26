"""Testy generatora torów kolejowych.

Sprawdza poprawność działania generate_railway_hex_tile.py przed integracją z map_editor.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Dodaj katalog edytory do ścieżki
sys.path.insert(0, str(Path(__file__).parent))

from generate_railway_hex_tile import (
    EXPORT_SIZE_BY_GRID,
    HEX_SIDES,
    JUNCTION_MIN_ANGLE_DEG,
    RAILWAY_DIMENSIONS,
    RailwayOptions,
    SIDE_ANGLES,
    SIDE_OPPOSITE,
    _angle_between_sides,
    _bezier_cubic,
    _bezier_quadratic,
    _build_hex_mask,
    _generate_curved_path,
    _generate_junction_curve,
    _generate_straight_path,
    _hex_center,
    _hex_vertices,
    _is_valid_junction,
    _point_in_polygon,
    _side_to_edge_center,
    generate_railway,
)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL niedostępne - testy generowania obrazów zostaną pominięte")


# ============================================================================
# TESTY GEOMETRII HEKSA
# ============================================================================

def test_hex_geometry():
    """Test funkcji geometrycznych heksa."""
    print("\n" + "="*70)
    print("TEST 1: Geometria heksa")
    print("="*70)
    
    grid = 64
    
    # Test 1.1: Środek heksa
    print("\n[1.1] Środek heksa")
    center = _hex_center(grid)
    expected = (32.0, 32.0)
    assert center == expected, f"Oczekiwano {expected}, otrzymano {center}"
    print(f"✓ Środek dla grid={grid}: {center}")
    
    # Test 1.2: Wierzchołki heksa
    print("\n[1.2] Wierzchołki heksa (pointy-top)")
    vertices = _hex_vertices(grid)
    assert len(vertices) == 6, f"Heks powinien mieć 6 wierzchołków, ma {len(vertices)}"
    print(f"✓ Liczba wierzchołków: {len(vertices)}")
    
    # Sprawdź symetrię
    cx, cy = center
    for i, (vx, vy) in enumerate(vertices):
        dist = math.sqrt((vx - cx)**2 + (vy - cy)**2)
        print(f"  Wierzchołek {i}: ({vx:.2f}, {vy:.2f}), odległość od centrum: {dist:.2f}")
    
    # Test 1.3: Środki krawędzi
    print("\n[1.3] Środki krawędzi dla wszystkich boków")
    for side in HEX_SIDES:
        edge_center = _side_to_edge_center(side, grid)
        print(f"  {side:15} -> ({edge_center[0]:.2f}, {edge_center[1]:.2f})")
        
        # Sprawdź czy punkt jest w rozsądnej odległości od centrum
        # (dla pointy-top, środki boków mają różne odległości od centrum)
        dist = math.sqrt((edge_center[0] - cx)**2 + (edge_center[1] - cy)**2)
        radius = grid / 2.0 - 0.5
        # Dla pointy-top: top/bottom są bliżej (sqrt3/2 * r), left/right dalej (r)
        assert dist < grid, f"Punkt krawędzi {side} poza obszarem"
    
    print("✓ Wszystkie środki krawędzi w rozsądnych pozycjach")
    
    # Test 1.4: Przeciwne boki
    print("\n[1.4] Mapowanie przeciwnych boków")
    for side, opposite in SIDE_OPPOSITE.items():
        reverse = SIDE_OPPOSITE.get(opposite)
        assert reverse == side, f"Niezgodność: {side} -> {opposite} -> {reverse}"
        print(f"  {side:15} <-> {opposite}")
    print("✓ Mapowanie przeciwnych boków spójne")
    
    return True


def test_angle_calculations():
    """Test obliczeń kątów między bokami."""
    print("\n" + "="*70)
    print("TEST 2: Obliczenia kątów")
    print("="*70)
    
    # Test 2.1: Kąty między sąsiednimi bokami
    print("\n[2.1] Kąty między sąsiednimi bokami (powinny być 60°)")
    for i, side1 in enumerate(HEX_SIDES):
        side2 = HEX_SIDES[(i + 1) % 6]
        angle = _angle_between_sides(side1, side2)
        print(f"  {side1:15} -> {side2:15}: {angle:.1f}°")
        assert abs(angle - 60.0) < 1.0, f"Kąt między sąsiednimi bokami powinien być ~60°"
    print("✓ Wszystkie kąty sąsiednie poprawne")
    
    # Test 2.2: Kąty między przeciwnymi bokami
    print("\n[2.2] Kąty między przeciwnymi bokami (powinny być 180°)")
    for side, opposite in SIDE_OPPOSITE.items():
        angle = _angle_between_sides(side, opposite)
        print(f"  {side:15} <-> {opposite:15}: {angle:.1f}°")
        assert abs(angle - 180.0) < 1.0, f"Kąt między przeciwnymi bokami powinien być ~180°"
    print("✓ Wszystkie kąty przeciwne poprawne")
    
    # Test 2.3: Tabelka wszystkich kątów
    print("\n[2.3] Macierz wszystkich kątów między bokami")
    print(f"{'':15}", end="")
    for side2 in HEX_SIDES:
        print(f"{side2:12}", end="")
    print()
    
    for side1 in HEX_SIDES:
        print(f"{side1:15}", end="")
        for side2 in HEX_SIDES:
            angle = _angle_between_sides(side1, side2)
            print(f"{angle:10.0f}°", end=" ")
        print()
    
    return True


def test_junction_validation():
    """Test walidacji dozwolonych dojazdów."""
    print("\n" + "="*70)
    print("TEST 3: Walidacja dojazdów (rozjazdów)")
    print("="*70)
    
    print(f"\nMinimalny kąt dozwolony: {JUNCTION_MIN_ANGLE_DEG}°")
    
    # Test 3.1: Wszystkie możliwe kombinacje
    print("\n[3.1] Sprawdzanie wszystkich możliwych dojazdów")
    
    test_cases = [
        ("top", "bottom", ["top_left", "top_right", "bottom_left", "bottom_right"]),
        ("top", "bottom_right", ["bottom", "bottom_left", "top_left"]),
        ("top_right", "bottom_left", ["top", "bottom", "bottom_right", "top_left"]),
    ]
    
    for entry, exit_side, expected_valid in test_cases:
        print(f"\n  Główny tor: {entry} -> {exit_side}")
        valid_junctions = []
        invalid_junctions = []
        
        for junction_side in HEX_SIDES:
            if junction_side in (entry, exit_side):
                continue
            
            is_valid = _is_valid_junction(entry, exit_side, junction_side)
            if is_valid:
                valid_junctions.append(junction_side)
            else:
                invalid_junctions.append(junction_side)
        
        print(f"    Dozwolone dojazdy: {', '.join(valid_junctions) if valid_junctions else 'brak'}")
        print(f"    Wykluczone: {', '.join(invalid_junctions) if invalid_junctions else 'brak'}")
        
        # Weryfikacja zgodności z oczekiwaniami
        for side in expected_valid:
            if side in valid_junctions:
                print(f"      ✓ {side} - poprawnie dozwolony")
            else:
                print(f"      ✗ {side} - BŁĄD: powinien być dozwolony!")
    
    print("\n✓ Walidacja dojazdów zakończona")
    return True


def test_bezier_curves():
    """Test krzywych Béziera."""
    print("\n" + "="*70)
    print("TEST 4: Krzywe Béziera")
    print("="*70)
    
    # Test 4.1: Kwadratowa krzywa Béziera
    print("\n[4.1] Krzywa kwadratowa Béziera")
    p0 = (0.0, 0.0)
    p1 = (32.0, 32.0)
    p2 = (64.0, 0.0)
    
    # Sprawdź punkty końcowe
    start = _bezier_quadratic(p0, p1, p2, 0.0)
    end = _bezier_quadratic(p0, p1, p2, 1.0)
    middle = _bezier_quadratic(p0, p1, p2, 0.5)
    
    assert abs(start[0] - p0[0]) < 0.01 and abs(start[1] - p0[1]) < 0.01
    assert abs(end[0] - p2[0]) < 0.01 and abs(end[1] - p2[1]) < 0.01
    
    print(f"  t=0.0: {start} (powinno być {p0})")
    print(f"  t=0.5: {middle}")
    print(f"  t=1.0: {end} (powinno być {p2})")
    print("  ✓ Punkty końcowe zgodne")
    
    # Test 4.2: Sześcienna krzywa Béziera
    print("\n[4.2] Krzywa sześcienna Béziera")
    p0 = (0.0, 0.0)
    p1 = (20.0, 40.0)
    p2 = (44.0, 40.0)
    p3 = (64.0, 0.0)
    
    start = _bezier_cubic(p0, p1, p2, p3, 0.0)
    end = _bezier_cubic(p0, p1, p2, p3, 1.0)
    
    assert abs(start[0] - p0[0]) < 0.01 and abs(start[1] - p0[1]) < 0.01
    assert abs(end[0] - p3[0]) < 0.01 and abs(end[1] - p3[1]) < 0.01
    
    print(f"  t=0.0: {start} (powinno być {p0})")
    print(f"  t=1.0: {end} (powinno być {p3})")
    print("  ✓ Punkty końcowe zgodne")
    
    return True


def test_path_generation():
    """Test generowania ścieżek torów."""
    print("\n" + "="*70)
    print("TEST 5: Generowanie ścieżek")
    print("="*70)
    
    grid = 64
    
    # Test 5.1: Ścieżka prosta
    print("\n[5.1] Ścieżka prosta (top -> bottom)")
    entry = _side_to_edge_center("top", grid)
    exit_pt = _side_to_edge_center("bottom", grid)
    
    straight_path = _generate_straight_path(entry, exit_pt, num_points=20)
    assert len(straight_path) == 20
    assert abs(straight_path[0][0] - entry[0]) < 0.01
    assert abs(straight_path[0][1] - entry[1]) < 0.01
    assert abs(straight_path[-1][0] - exit_pt[0]) < 0.01
    assert abs(straight_path[-1][1] - exit_pt[1]) < 0.01
    
    print(f"  Liczba punktów: {len(straight_path)}")
    print(f"  Start: {straight_path[0]} (oczekiwano {entry})")
    print(f"  Koniec: {straight_path[-1]} (oczekiwano {exit_pt})")
    print("  ✓ Ścieżka prosta poprawna")
    
    # Test 5.2: Ścieżka zakrzywiona
    print("\n[5.2] Ścieżka zakrzywiona (top -> bottom_right)")
    entry = _side_to_edge_center("top", grid)
    exit_pt = _side_to_edge_center("bottom_right", grid)
    center = _hex_center(grid)
    
    curved_path = _generate_curved_path(entry, exit_pt, center, num_points=24)
    assert len(curved_path) == 24
    assert abs(curved_path[0][0] - entry[0]) < 0.01
    assert abs(curved_path[-1][0] - exit_pt[0]) < 0.01
    
    print(f"  Liczba punktów: {len(curved_path)}")
    print(f"  Start: {curved_path[0]}")
    print(f"  Koniec: {curved_path[-1]}")
    print("  ✓ Ścieżka zakrzywiona poprawna")
    
    # Test 5.3: Krzywa rozjazdu
    print("\n[5.3] Krzywa rozjazdu (junction)")
    junction_entry = _side_to_edge_center("top_left", grid)
    merge_point = straight_path[len(straight_path) // 2]
    main_direction = (exit_pt[0] - entry[0], exit_pt[1] - entry[1])
    
    junction_path = _generate_junction_curve(
        junction_entry, merge_point, main_direction, "top_left", num_points=40
    )
    assert len(junction_path) == 40
    
    print(f"  Liczba punktów: {len(junction_path)}")
    print(f"  Start (krawędź): {junction_path[0]}")
    print(f"  Koniec (merge): {junction_path[-1]}")
    print("  ✓ Krzywa rozjazdu poprawna")
    
    return True


def test_hex_mask():
    """Test maski heksa."""
    print("\n" + "="*70)
    print("TEST 6: Maska heksa")
    print("="*70)
    
    grid = 64
    mask = _build_hex_mask(grid)
    
    # Test 6.1: Rozmiar maski
    print(f"\n[6.1] Rozmiar maski: {len(mask)}x{len(mask[0])}")
    assert len(mask) == grid
    assert len(mask[0]) == grid
    print("  ✓ Wymiary poprawne")
    
    # Test 6.2: Środek heksa powinien być w masce
    print("\n[6.2] Sprawdzanie punktów charakterystycznych")
    center = _hex_center(grid)
    cx, cy = int(center[0]), int(center[1])
    assert mask[cy][cx], "Środek heksa powinien być w masce"
    print(f"  ✓ Środek ({cx}, {cy}) w masce")
    
    # Test 6.3: Narożniki obrazu powinny być poza maską
    corners_outside = all([
        not mask[0][0],
        not mask[0][grid-1],
        not mask[grid-1][0],
        not mask[grid-1][grid-1],
    ])
    assert corners_outside, "Narożniki obrazu powinny być poza heksem"
    print("  ✓ Narożniki poza maską")
    
    # Test 6.4: Policz procent pikseli w masce
    total_pixels = grid * grid
    hex_pixels = sum(sum(row) for row in mask)
    coverage = 100.0 * hex_pixels / total_pixels
    
    # Generator używa radius = grid/2 - 0.5, więc pokrycie jest mniejsze
    # Oczekujemy 50-70% dla bezpiecznego marginesu
    min_coverage = 50.0
    max_coverage = 70.0
    
    print(f"\n[6.4] Pokrycie maski")
    print(f"  Piksele w heksie: {hex_pixels}/{total_pixels}")
    print(f"  Pokrycie: {coverage:.1f}%")
    print(f"  Dopuszczalny zakres: {min_coverage:.1f}% - {max_coverage:.1f}%")
    assert min_coverage <= coverage <= max_coverage, \
        f"Pokrycie {coverage:.1f}% poza zakresem {min_coverage}-{max_coverage}%"
    print("  ✓ Pokrycie w oczekiwanym zakresie")
    
    return True


# ============================================================================
# TESTY GENEROWANIA OBRAZÓW
# ============================================================================

def test_image_generation():
    """Test generowania obrazów torów."""
    if not PIL_AVAILABLE:
        print("\n⚠️ PIL niedostępne - pomijam testy generowania obrazów")
        return True
    
    print("\n" + "="*70)
    print("TEST 7: Generowanie obrazów")
    print("="*70)
    
    output_dir = Path(__file__).parent / "test_output_railway"
    output_dir.mkdir(exist_ok=True)
    
    test_cases = [
        {
            "name": "Tor prosty jednotorowy",
            "file": "straight_single.png",
            "options": {
                "grid_size": 64,
                "background": None,
                "entry_side": "top",
                "exit_side": "bottom",
                "railway_type": "jednotorowy",
                "seed": 42,
            }
        },
        {
            "name": "Tor prosty dwutorowy",
            "file": "straight_double.png",
            "options": {
                "grid_size": 64,
                "background": None,
                "entry_side": "top",
                "exit_side": "bottom",
                "railway_type": "dwutorowy",
                "seed": 42,
            }
        },
        {
            "name": "Tor zakrzywiony",
            "file": "curved_single.png",
            "options": {
                "grid_size": 64,
                "background": None,
                "entry_side": "top",
                "exit_side": "bottom_right",
                "railway_type": "jednotorowy",
                "seed": 42,
            }
        },
        {
            "name": "Rozjazd jednostronny",
            "file": "junction_single.png",
            "options": {
                "grid_size": 64,
                "background": None,
                "entry_side": "top",
                "exit_side": "bottom",
                "railway_type": "jednotorowy",
                "junctions": ["top_left"],
                "seed": 42,
            }
        },
        {
            "name": "Rozjazd dwustronny",
            "file": "junction_double.png",
            "options": {
                "grid_size": 64,
                "background": None,
                "entry_side": "top",
                "exit_side": "bottom",
                "railway_type": "jednotorowy",
                "junctions": ["top_left", "top_right"],
                "seed": 42,
            }
        },
        {
            "name": "Tor dwutorowy z rozjazdem dwutorowym",
            "file": "double_junction_double.png",
            "options": {
                "grid_size": 64,
                "background": None,
                "entry_side": "top_left",
                "exit_side": "bottom_right",
                "railway_type": "dwutorowy",
                "junctions": ["bottom"],
                "junction_double_track": True,
                "seed": 42,
            }
        },
    ]
    
    generated_files = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[7.{i}] {test_case['name']}")
        
        output_path = output_dir / test_case['file']
        options = RailwayOptions(**test_case['options'])
        
        try:
            result = generate_railway(options, output_path)
            
            # Sprawdź czy plik został utworzony
            assert result.image_path.exists(), f"Plik obrazu nie został utworzony: {result.image_path}"
            assert result.metadata_path.exists(), f"Plik metadanych nie został utworzony: {result.metadata_path}"
            
            # Sprawdź rozmiar obrazu
            img = Image.open(result.image_path)
            expected_size = EXPORT_SIZE_BY_GRID.get(options.grid_size, 512)
            assert img.size == (expected_size, expected_size), \
                f"Niepoprawny rozmiar: {img.size}, oczekiwano ({expected_size}, {expected_size})"
            
            # Sprawdź metadane
            with open(result.metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            assert metadata['entry_side'] == options.entry_side
            assert metadata['exit_side'] == options.exit_side
            assert metadata['railway_type'] == options.railway_type
            
            print(f"  ✓ Wygenerowano: {output_path.name}")
            print(f"     Rozmiar: {img.size}")
            print(f"     Prosty: {metadata.get('is_straight', 'N/A')}")
            if 'junctions' in metadata and metadata['junctions']:
                print(f"     Dojazdy: {', '.join(metadata['junctions'])}")
            
            generated_files.append(output_path)
            
        except Exception as e:
            print(f"  ✗ BŁĄD: {e}")
            return False
    
    print(f"\n✓ Wygenerowano {len(generated_files)} plików testowych w: {output_dir}")
    return True


def test_railway_dimensions():
    """Test wymiarów torów."""
    print("\n" + "="*70)
    print("TEST 8: Wymiary torów")
    print("="*70)
    
    print("\n[8.1] Wymiary jednotorowe")
    single = RAILWAY_DIMENSIONS["jednotorowy"]
    for key, value in single.items():
        print(f"  {key:20} = {value}")
    
    print("\n[8.2] Wymiary dwutorowe")
    double = RAILWAY_DIMENSIONS["dwutorowy"]
    for key, value in double.items():
        print(f"  {key:20} = {value}")
    
    # Sprawdź logiczne wartości
    assert single["track_gauge"] > 0, "Rozstaw szyn musi być > 0"
    assert single["rail_width"] > 0, "Szerokość szyny musi być > 0"
    assert single["sleeper_width"] > single["track_gauge"], \
        "Podkład musi być szerszy niż rozstaw szyn"
    assert single["ballast_width"] > single["sleeper_width"], \
        "Podsypka musi być szersza niż podkład"
    
    assert double["track_separation"] > double["track_gauge"], \
        "Odległość między torami musi być większa niż rozstaw szyn"
    
    print("\n✓ Wszystkie wymiary logiczne")
    return True


# ============================================================================
# GŁÓWNA FUNKCJA TESTOWA
# ============================================================================

def run_all_tests():
    """Uruchamia wszystkie testy."""
    print("\n" + "="*70)
    print("TESTY GENERATORA TORÓW KOLEJOWYCH")
    print("="*70)
    print(f"Lokalizacja: {Path(__file__).parent / 'generate_railway_hex_tile.py'}")
    
    tests = [
        ("Geometria heksa", test_hex_geometry),
        ("Obliczenia kątów", test_angle_calculations),
        ("Walidacja dojazdów", test_junction_validation),
        ("Krzywe Béziera", test_bezier_curves),
        ("Generowanie ścieżek", test_path_generation),
        ("Maska heksa", test_hex_mask),
        ("Wymiary torów", test_railway_dimensions),
        ("Generowanie obrazów", test_image_generation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success, None))
        except Exception as e:
            print(f"\n✗ BŁĄD w teście '{test_name}': {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False, str(e)))
    
    # Podsumowanie
    print("\n" + "="*70)
    print("PODSUMOWANIE TESTÓW")
    print("="*70)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, error in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:10} {test_name}")
        if error:
            print(f"           Błąd: {error}")
    
    print(f"\nWynik: {passed}/{total} testów zaliczonych ({100*passed/total:.0f}%)")
    
    if passed == total:
        print("\n🎉 WSZYSTKIE TESTY ZALICZONE - generator gotowy do integracji!")
        return True
    else:
        print(f"\n⚠️ {total - passed} testów nie powiodło się - wymagane poprawki!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
