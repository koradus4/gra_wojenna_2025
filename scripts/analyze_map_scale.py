#!/usr/bin/env python3
"""
Skrypt do analizy skali mapy referencyjnej.
Pozwala kliknąć na miasta i obliczyć skalę px/km.
Wyniki wyświetlane są w terminalu.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import math

ASSET_ROOT = Path(__file__).parent.parent / "assets"
MAP_FILE = ASSET_ROOT / "mapa_globalna.jpg"

# Rzeczywiste odległości między miastami (km, linia prosta)
REAL_DISTANCES = {
    ("Warszawa", "Łódź"): 120,
    ("Warszawa", "Płock"): 100,
    ("Warszawa", "Włocławek"): 140,
    ("Łódź", "Płock"): 85,
    ("Łódź", "Włocławek"): 115,
    ("Płock", "Włocławek"): 55,
}


def log(msg: str):
    """Wypisz do terminala i zwróć tekst."""
    print(msg)
    return msg + "\n"


class MapScaleAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Analiza skali mapy - kliknij na miasta")
        
        # Punkty oznaczone przez użytkownika
        self.points = {}  # nazwa -> (x, y)
        self.current_city = None
        
        # Wczytaj obraz
        self.original_img = Image.open(MAP_FILE)
        self.img_width, self.img_height = self.original_img.size
        
        print("\n" + "="*60)
        print("ANALIZA SKALI MAPY REFERENCYJNEJ")
        print("="*60)
        print(f"Plik: {MAP_FILE}")
        print(f"Rozmiar obrazu: {self.img_width} × {self.img_height} px")
        print("="*60 + "\n")
        
        # Skalowanie do wyświetlenia - mniejsze okno
        self.display_scale = min(1100 / self.img_width, 700 / self.img_height, 0.85)
        display_w = int(self.img_width * self.display_scale)
        display_h = int(self.img_height * self.display_scale)
        
        self.display_img = self.original_img.resize((display_w, display_h), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.display_img)
        
        # UI - górny pasek
        top_frame = ttk.Frame(root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(top_frame, text="Miasto:").pack(side=tk.LEFT)
        self.city_var = tk.StringVar(value="Warszawa")
        cities = ["Warszawa", "Łódź", "Płock", "Włocławek", "Łowicz"]
        self.city_combo = ttk.Combobox(top_frame, textvariable=self.city_var, values=cities, width=12)
        self.city_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="📊 Oblicz skalę", command=self.calculate_scale).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="⬡ Oblicz siatkę", command=self.calculate_hex_grid).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="🔄 Reset", command=self.reset_points).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value=f"Obraz: {self.img_width}×{self.img_height} px | Kliknij na miasta")
        ttk.Label(top_frame, textvariable=self.status_var).pack(side=tk.RIGHT)
        
        # Canvas z obrazem
        self.canvas = tk.Canvas(root, width=display_w, height=display_h, bg="black")
        self.canvas.pack(padx=5, pady=5)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.bind("<Button-1>", self.on_click)
        
        # Dolny pasek z oznaczonymi miastami
        bottom_frame = ttk.Frame(root)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(bottom_frame, text="Oznaczone:").pack(side=tk.LEFT)
        self.marked_var = tk.StringVar(value="(brak)")
        ttk.Label(bottom_frame, textvariable=self.marked_var, foreground="green").pack(side=tk.LEFT, padx=5)
        
        print("INSTRUKCJA:")
        print("1. Wybierz miasto z listy")
        print("2. Kliknij na jego lokalizację na mapie")
        print("3. Powtórz dla min. 2 miast (Warszawa, Łódź, Płock, Włocławek)")
        print("4. Kliknij 'Oblicz skalę'")
        print("5. Kliknij 'Oblicz siatkę'\n")
    
    def reset_points(self):
        self.points = {}
        self.marked_var.set("(brak)")
        # Odśwież canvas
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        print("\n[RESET] Punkty wyczyszczone\n")
    
    def on_click(self, event):
        # Przelicz na rzeczywiste współrzędne obrazu
        real_x = int(event.x / self.display_scale)
        real_y = int(event.y / self.display_scale)
        
        city = self.city_var.get()
        self.points[city] = (real_x, real_y)
        
        # Narysuj marker
        r = 6
        self.canvas.create_oval(
            event.x - r, event.y - r, event.x + r, event.y + r,
            fill="red", outline="yellow", width=2
        )
        self.canvas.create_text(
            event.x, event.y - 12, text=city, fill="yellow", font=("Arial", 9, "bold")
        )
        
        # Aktualizuj status
        marked = ", ".join(self.points.keys())
        self.marked_var.set(marked)
        self.status_var.set(f"Oznaczono {len(self.points)} miast")
        
        print(f"✓ {city}: ({real_x}, {real_y}) px")
    
    def calculate_scale(self):
        if len(self.points) < 2:
            messagebox.showwarning("Za mało punktów", "Oznacz co najmniej 2 miasta!")
            return
        
        print("\n" + "="*60)
        print("ANALIZA SKALI")
        print("="*60)
        
        scales = []
        for (city1, city2), km in REAL_DISTANCES.items():
            if city1 in self.points and city2 in self.points:
                x1, y1 = self.points[city1]
                x2, y2 = self.points[city2]
                px_dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                scale = px_dist / km
                scales.append(scale)
                print(f"\n{city1} → {city2}:")
                print(f"  Piksele: {px_dist:.1f} px")
                print(f"  Rzeczywiste: {km} km")
                print(f"  Skala: {scale:.2f} px/km")
        
        if scales:
            avg_scale = sum(scales) / len(scales)
            
            print("\n" + "="*60)
            print(f">>> ŚREDNIA SKALA: {avg_scale:.2f} px/km <<<")
            print("="*60)
            
            # Oblicz pokrycie mapy w km
            map_width_km = self.img_width / avg_scale
            map_height_km = self.img_height / avg_scale
            print(f"\nWymiary mapy w rzeczywistości:")
            print(f"  Szerokość: {map_width_km:.1f} km")
            print(f"  Wysokość: {map_height_km:.1f} km")
            print(f"  Powierzchnia: ~{map_width_km * map_height_km:.0f} km²")
            
            self.avg_scale = avg_scale
            self.status_var.set(f"Skala: {avg_scale:.2f} px/km | Mapa: {map_width_km:.0f}×{map_height_km:.0f} km")
    
    def calculate_hex_grid(self):
        if not hasattr(self, 'avg_scale'):
            messagebox.showwarning("Brak skali", "Najpierw oblicz skalę!")
            return
        
        print("\n" + "="*60)
        print("OBLICZENIE SIATKI HEKSÓW")
        print("="*60)
        print(f"Skala bazowa: {self.avg_scale:.2f} px/km")
        print(f"Rozmiar obrazu: {self.img_width} × {self.img_height} px\n")
        
        results = []
        
        # Oblicz dla różnych rozmiarów heksa (3-5 km)
        for km_per_hex in [3, 4, 5]:
            print(f"{'─'*40}")
            print(f"  1 HEKS = {km_per_hex} km")
            print(f"{'─'*40}")
            
            # Piksele na heks (szerokość heksa)
            px_per_hex = km_per_hex * self.avg_scale
            
            # Dla heksów pointy-top:
            # szerokość heksa = 2 * size (od wierzchołka do wierzchołka poziomo)
            # wysokość heksa = sqrt(3) * size
            # odstęp poziomy między środkami = 1.5 * size
            # odstęp pionowy między środkami = sqrt(3) * size
            
            hex_size = px_per_hex / 2
            horiz_spacing = 1.5 * hex_size
            vert_spacing = math.sqrt(3) * hex_size
            
            cols = int(self.img_width / horiz_spacing) + 1
            rows = int(self.img_height / vert_spacing) + 1
            total = cols * rows
            
            print(f"  Szerokość heksa: {px_per_hex:.1f} px")
            print(f"  hex_size (promień): {hex_size:.1f} px")
            print(f"  Odstęp poziomy: {horiz_spacing:.1f} px")
            print(f"  Odstęp pionowy: {vert_spacing:.1f} px")
            print(f"  ")
            print(f"  >>> KOLUMNY: {cols}")
            print(f"  >>> WIERSZE: {rows}")
            print(f"  >>> RAZEM HEKSÓW: {total}")
            print()
            
            results.append({
                "km": km_per_hex,
                "cols": cols,
                "rows": rows,
                "hex_size": hex_size,
                "total": total
            })
        
        # Podsumowanie
        print("="*60)
        print("PODSUMOWANIE - parametry do map_editor:")
        print("="*60)
        for r in results:
            print(f"\n  [1 heks = {r['km']} km]")
            print(f"    grid_cols = {r['cols']}")
            print(f"    grid_rows = {r['rows']}")
            print(f"    hex_size = {r['hex_size']:.1f}")
        
        print("\n" + "="*60)
        print("Wybierz wariant i użyj tych wartości w CONFIG map_editora")
        print("="*60 + "\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = MapScaleAnalyzer(root)
    root.mainloop()
