"""Demonstracja możliwości generatora torów kolejowych.

Generuje zestaw przykładów pokazujących wszystkie funkcje.
"""

from pathlib import Path
import sys

# Upewnij się, że możemy importować moduły z katalogu `edytory`
sys.path.insert(0, str(Path(__file__).parent.parent / "edytory"))

from generate_railway_hex_tile import (
    RailwayOptions,
    generate_railway,
    HEX_SIDES,
    SIDE_OPPOSITE,
)


def main():
    """Generuje kompletny zestaw demonstracyjny."""
    
    # Domyślne miejsce przechowywania przykładów: tests/resources/railway/railway_demo
    output_dir = Path(__file__).parent.parent / "tests" / "resources" / "railway" / "railway_demo"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("DEMONSTRACJA GENERATORA TORÓW KOLEJOWYCH")
    print("="*70)
    print(f"\nKatalog wyjściowy: {output_dir}")
    
    demos = []
    
    # === 1. PODSTAWOWE TORY PROSTE ===
    
    print("\n📍 KATEGORIA 1: Tory proste")
    
    demos.append({
        "category": "proste",
        "name": "01_prosty_jednotorowy_NS",
        "desc": "Tor prosty północ-południe, jednotorowy",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top",
            exit_side="bottom",
            railway_type="jednotorowy",
            seed=100,
        )
    })
    
    demos.append({
        "category": "proste",
        "name": "02_prosty_dwutorowy_NS",
        "desc": "Tor prosty północ-południe, dwutorowy",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top",
            exit_side="bottom",
            railway_type="dwutorowy",
            seed=100,
        )
    })
    
    demos.append({
        "category": "proste",
        "name": "03_prosty_jednotorowy_NWSE",
        "desc": "Tor prosty NW-SE, jednotorowy",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top_left",
            exit_side="bottom_right",
            railway_type="jednotorowy",
            seed=101,
        )
    })
    
    # === 2. TORY ZAKRZYWIONE ===
    
    print("\n🌙 KATEGORIA 2: Tory zakrzywione")
    
    demos.append({
        "category": "zakrzywione",
        "name": "04_zakret_60_jednotorowy",
        "desc": "Zakręt 60° (sąsiednie boki), jednotorowy",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top",
            exit_side="top_right",
            railway_type="jednotorowy",
            seed=200,
        )
    })
    
    demos.append({
        "category": "zakrzywione",
        "name": "05_zakret_120_jednotorowy",
        "desc": "Zakręt 120° (przez jeden bok), jednotorowy",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top",
            exit_side="bottom_right",
            railway_type="jednotorowy",
            seed=201,
        )
    })
    
    demos.append({
        "category": "zakrzywione",
        "name": "06_zakret_60_dwutorowy",
        "desc": "Zakręt 60°, dwutorowy",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top_left",
            exit_side="top",
            railway_type="dwutorowy",
            seed=202,
        )
    })
    
    # === 3. ROZJAZDY JEDNOSTRONNE ===
    
    print("\n🔀 KATEGORIA 3: Rozjazdy jednostronne")
    
    demos.append({
        "category": "rozjazdy_jednostronne",
        "name": "07_rozjazd_lewy_jednostronny",
        "desc": "Tor prosty z rozjazdem lewym, jednotorowy",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top",
            exit_side="bottom",
            railway_type="jednotorowy",
            junctions=["top_left"],
            seed=300,
        )
    })
    
    demos.append({
        "category": "rozjazdy_jednostronne",
        "name": "08_rozjazd_prawy_jednostronny",
        "desc": "Tor prosty z rozjazdem prawym, jednotorowy",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top",
            exit_side="bottom",
            railway_type="jednotorowy",
            junctions=["top_right"],
            seed=301,
        )
    })
    
    demos.append({
        "category": "rozjazdy_jednostronne",
        "name": "09_rozjazd_zakret_z_dojazdem",
        "desc": "Tor zakrzywiony z dojazdem bocznym",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top",
            exit_side="bottom_right",
            railway_type="jednotorowy",
            junctions=["bottom"],
            seed=302,
        )
    })
    
    # === 4. ROZJAZDY DWUSTRONNE (WIDELCE) ===
    
    print("\n⚡ KATEGORIA 4: Rozjazdy dwustronne")
    
    demos.append({
        "category": "rozjazdy_dwustronne",
        "name": "10_rozjazd_symetryczny_Y",
        "desc": "Rozjazd Y - symetryczne widelce",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top",
            exit_side="bottom",
            railway_type="jednotorowy",
            junctions=["top_left", "top_right"],
            seed=400,
        )
    })
    
    demos.append({
        "category": "rozjazdy_dwustronne",
        "name": "11_rozjazd_asymetryczny",
        "desc": "Rozjazd asymetryczny (boki różne)",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top",
            exit_side="bottom",
            railway_type="jednotorowy",
            junctions=["top_right", "bottom_left"],
            seed=401,
        )
    })
    
    # === 5. TORY DWUTOROWE Z ROZJAZDAMI ===
    
    print("\n🚄 KATEGORIA 5: Dwutorowe z rozjazdami")
    
    demos.append({
        "category": "dwutorowe_rozjazdy",
        "name": "12_dwutorowy_rozjazd_jednotorowy",
        "desc": "Tor dwutorowy z rozjazdem jednotorowym",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top",
            exit_side="bottom",
            railway_type="dwutorowy",
            junctions=["top_left"],
            junction_double_track=False,
            seed=500,
        )
    })
    
    demos.append({
        "category": "dwutorowe_rozjazdy",
        "name": "13_dwutorowy_rozjazd_dwutorowy",
        "desc": "Tor dwutorowy z rozjazdem dwutorowym",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top",
            exit_side="bottom",
            railway_type="dwutorowy",
            junctions=["top_right"],
            junction_double_track=True,
            seed=501,
        )
    })
    
    demos.append({
        "category": "dwutorowe_rozjazdy",
        "name": "14_dwutorowy_widelce_dwutorowe",
        "desc": "Tor dwutorowy z dwoma rozjazdami dwutorowymi",
        "options": RailwayOptions(
            grid_size=64,
            background=None,
            entry_side="top_left",
            exit_side="bottom_right",
            railway_type="dwutorowy",
            junctions=["top", "bottom"],
            junction_double_track=True,
            seed=502,
        )
    })
    
    # === GENEROWANIE ===
    
    print(f"\n🔧 Generuję {len(demos)} przykładów...")
    print()
    
    success_count = 0
    
    for i, demo in enumerate(demos, 1):
        category = demo["category"]
        name = demo["name"]
        desc = demo["desc"]
        options = demo["options"]
        
        category_dir = output_dir / category
        category_dir.mkdir(exist_ok=True)
        
        output_path = category_dir / f"{name}.png"
        
        try:
            result = generate_railway(options, output_path)
            
            print(f"[{i:2d}/{len(demos)}] ✓ {name}")
            print(f"        {desc}")
            print(f"        → {output_path.relative_to(output_dir)}")
            
            success_count += 1
            
        except Exception as e:
            print(f"[{i:2d}/{len(demos)}] ✗ {name}")
            print(f"        BŁĄD: {e}")
    
    # === PODSUMOWANIE ===
    
    print()
    print("="*70)
    print("PODSUMOWANIE")
    print("="*70)
    print(f"Wygenerowano: {success_count}/{len(demos)} przykładów")
    print(f"Lokalizacja: {output_dir.absolute()}")
    print()
    print("Kategorie:")
    
    categories = {}
    for demo in demos:
        cat = demo["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in categories.items():
        cat_dir = output_dir / cat
        print(f"  • {cat:25} - {count:2d} plików w {cat_dir.relative_to(output_dir)}")
    
    print()
    print("✅ Demonstracja zakończona!")
    
    if success_count == len(demos):
        print("🎉 Wszystkie przykłady wygenerowane pomyślnie!")
        return 0
    else:
        print(f"⚠️ {len(demos) - success_count} przykładów nie powiodło się")
        return 1


if __name__ == "__main__":
    sys.exit(main())