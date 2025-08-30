import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
import json
import math
import os
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageFont

# Folder „assets” obok map_editor_prototyp.py
ASSET_ROOT = Path(__file__).parent.parent / "assets"

def fix_image_path(relative_path):
    """Naprawia ścieżki obrazów, usuwając podwójne assets/"""
    if isinstance(relative_path, str):
        # Usuń assets/ z początku, jeśli występuje
        if relative_path.startswith("assets/"):
            relative_path = relative_path[7:]  # usuń "assets/"
        elif relative_path.startswith("assets\\"):
            relative_path = relative_path[8:]  # usuń "assets\"
    
    # Tworzymy pełną ścieżkę
    full_path = ASSET_ROOT / relative_path
    return full_path
ASSET_ROOT.mkdir(exist_ok=True)

# Dodajemy folder data na potrzeby silnika i testów
DATA_ROOT = Path(__file__).parent.parent / "data"
DATA_ROOT.mkdir(exist_ok=True)

DEFAULT_MAP_FILE = str(ASSET_ROOT / "mapa_globalna.jpg")
DEFAULT_MAP_DIR = ASSET_ROOT
# Zmieniamy domyślną ścieżkę zapisu danych mapy na data/map_data.json
DATA_FILENAME_WORKING = DATA_ROOT / "map_data.json"

def to_rel(path: str) -> str:
    """Zwraca ścieżkę assets/... względem katalogu projektu."""
    try:
        return str(Path(path).relative_to(ASSET_ROOT))
    except ValueError:
        return str(path)   # gdy ktoś wybierze plik spoza assets/

# ----------------------------
# Konfiguracja rodzajów terenu
# ----------------------------
TERRAIN_TYPES = {
    "teren_płaski": {"move_mod": 0, "defense_mod": 0},
    "mała rzeka": {"move_mod": 2, "defense_mod": 1},
    "duża rzeka": {"move_mod": 5, "defense_mod": -1},  # przekraczalna, koszt ruchu 6
    "las": {"move_mod": 2, "defense_mod": 2},
    "bagno": {"move_mod": 3, "defense_mod": 1},
    "mała miejscowość": {"move_mod": 1, "defense_mod": 2},
    "miasto": {"move_mod": 2, "defense_mod": 2},
    "most": {"move_mod": 0, "defense_mod": -1}
}

# mapowanie państw → kolor mgiełki
SPAWN_OVERLAY = {
    "Polska": "#ffcccc;#ffffff",   # białe od góry, czerwone na dole
    "Niemcy": "#ccccff"    # jasnoniebieska
}

def zapisz_dane_hex(hex_data, filename=DATA_FILENAME_WORKING):
    'Zapisuje dane terenu do pliku JSON (roboczy plik).'
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            print(f"Nie można utworzyć katalogu {directory}: {e}")
            # Jeśli nie można utworzyć katalogu, zapisz w katalogu skryptu
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(filename))
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(hex_data, f, indent=2, ensure_ascii=False)

def wczytaj_dane_hex(filename=DATA_FILENAME_WORKING):
    'Wczytuje dane terenu z pliku JSON.'
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# ----------------------------
# Konfiguracja mapy
# ----------------------------
CONFIG = {
    'map_settings': {
        'map_image_path': r"C:\\ścieżka\\do\\tła\\mapa.jpg",  # Pełna ścieżka do obrazu tła mapy
        'hex_size': 30,
        'grid_cols': 56,   # liczba kolumn heksów
        'grid_rows': 40    # liczba wierszy heksów
    }
}

def point_in_polygon(x, y, poly):
    'Sprawdza, czy punkt (x,y) leży wewnątrz wielokąta poly.'
    num = len(poly)
    j = num - 1
    c = False
    for i in range(num):
        if ((poly[i][1] > y) != (poly[j][1] > y)) and \
           (x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / (poly[j][1] - poly[i][1] + 1e-10) + poly[i][0]):
            c = not c
        j = i
    return c

def get_hex_vertices(center_x, center_y, s):
    # Zwraca wierzchołki heksu (POINTY‑TOP) w układzie axial.
    return [
        (center_x - s, center_y),
        (center_x - s/2, center_y - (math.sqrt(3)/2)*s),
        (center_x + s/2, center_y - (math.sqrt(3)/2)*s),
        (center_x + s, center_y),
        (center_x + s/2, center_y + (math.sqrt(3)/2)*s),
        (center_x - s/2, center_y + (math.sqrt(3)/2)*s)
    ]

def offset_to_axial(col: int, row: int) -> tuple[int, int]:
    # Pointy-top even-q offset: q = col, r = row - (col // 2)
    q = col
    r = row - (col // 2)
    return q, r

class MapEditor:
    def __init__(self, root, config):
        # --- Podstawy ---
        self.root = root
        self.root.configure(bg="darkolivegreen")
        self.config = config["map_settings"]
        self.map_image_path = self.get_last_modified_map()  # Automatyczne otwieranie ostatniej mapy

        # --- Ustawienia heksów ---
        self.hex_size = self.config.get("hex_size", 30)
        self.hex_defaults = {"defense_mod": 0, "move_mod": 0}
        self.current_working_file = DATA_FILENAME_WORKING

        # --- Dane mapy ---
        self.hex_data: dict[str, dict] = {}
        self.key_points: dict[str, dict] = {}
        self.spawn_points: dict[str, list[str]] = {}

        # --- Selekcja ---
        self.selected_hex: str | None = None

        # --- Typy punktów kluczowych ---
        self.available_key_point_types = {
            "most": 50,
            "miasto": 100,
            "węzeł komunikacyjny": 75,
            "fortyfikacja": 150
        }

        # --- Nacje / żetony ---
        self.available_nations = ["Polska", "Niemcy"]
        self.hex_tokens: dict[str, str] = {}
        self.token_images: dict[str, ImageTk.PhotoImage] = {}

        # --- Nowy system palety żetonów ---
        self.token_index: list[dict] = []  # Lista wszystkich żetonów z index.json
        self.filtered_tokens: list[dict] = []  # Przefiltrowana lista żetonów
        self.selected_token = None  # Aktualnie wybrany żeton do wstawiania
        self.selected_token_button = None  # Przycisk zaznaczonego żetonu
        self.uniqueness_mode = True  # Tryb unikalności żetonów
        self.multi_placement_mode = False  # Tryb wielokrotnego wstawiania (Shift)
        
        # Filtry - tylko konkretny dowódca
        self.filter_commander = tk.StringVar(value="Wszystkie")
        self.commander_var = tk.StringVar(value="Wszyscy dowódcy")  # dla dropdown
        self.commander_filter = None  # aktualny filtr dowódcy
        
        # Auto-save debounce
        self._auto_save_after = None
        self.auto_save_enabled = True  # domyślnie włączony auto-save

        # --- Cache dla ghost (półprzezroczyste obrazy) ---
        self._ghost_cache: dict[tuple[Path, int], ImageTk.PhotoImage] = {}

        # --- Inicjalizacja GUI i danych ---
        self.load_token_index()
        self.build_gui()
        self.load_map_image()
        self.load_data()
        
        # Wymuś odświeżenie palety po inicjalizacji
        self.root.after(100, self.force_refresh_palette)

    def load_token_index(self):
        """Ładuje index żetonów z assets/tokens/index.json"""
        index_path = ASSET_ROOT / "tokens" / "index.json"
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                self.token_index = json.load(f)
            # Konwertuj ścieżki obrazów na względne jeśli są absolutne
            for token in self.token_index:
                if "image" in token:
                    token["image"] = token["image"].replace("\\", "/")
                    if token["image"].startswith("assets/"):
                        # Już względna ścieżka
                        pass
                    else:
                        # Konwertuj do względnej
                        token["image"] = to_rel(token["image"])
            print(f"Załadowano {len(self.token_index)} żetonów z indeksu")
        except Exception as e:
            print(f"Błąd ładowania indeksu żetonów: {e}")
            self.token_index = []
        self.update_filtered_tokens()

    def update_filtered_tokens(self):
        """Aktualizuje listę przefiltrowanych żetonów według aktualnych filtrów"""
        self.filtered_tokens = []
        
        # Debug info
        print(f"🔍 Filtrowanie żetonów: total={len(self.token_index)}")
        
        # Pobierz używane żetony jeśli unikalność włączona
        used_tokens = set()
        if self.uniqueness_mode:
            for terrain in self.hex_data.values():
                token = terrain.get("token")
                if token and "unit" in token:
                    used_tokens.add(token["unit"])
            print(f"🔒 Użyte żetony (unikalność ON): {len(used_tokens)}")
        
        for token in self.token_index:
            # Filtr unikalności
            if self.uniqueness_mode and token["id"] in used_tokens:
                continue
                
            # Filtr dowódcy - obsługa formatu dropdown "Dow. X (Nacja)"
            commander_filter = self.filter_commander.get()
            if commander_filter != "Wszystkie":
                # Wyciągnij numer dowódcy z "Dow. 2 (Polska)" -> "2"
                if commander_filter.startswith("Dow. "):
                    commander_num = commander_filter.split()[1]
                    token_owner = token.get("owner", "")
                    # Sprawdź czy owner zaczyna się od numeru dowódcy
                    if not token_owner.startswith(commander_num + " "):
                        continue
                    
            self.filtered_tokens.append(token)
        
        print(f"✅ Przefiltrowane żetony: {len(self.filtered_tokens)}")
        
        # Odśwież paletę żetonów
        if hasattr(self, 'token_palette_frame'):
            self.refresh_token_palette()

    def force_refresh_palette(self):
        """Wymusza odświeżenie palety żetonów po inicjalizacji"""
        print("🔄 Wymuszenie odświeżenia palety...")
        print(f"📊 Stan: {len(self.token_index)} żetonów w indeksie")
        print(f"🔒 Unikalność: {self.uniqueness_mode}")
        print(f"�️  Filtr dowódcy: {self.filter_commander.get()}")
        
        # Wymuś reset filtra na domyślny
        self.filter_commander.set("Wszystkie")
        
        # Wymuś aktualizację
        self.update_filtered_tokens()
        
        # Dodatkowo odśwież canvas
        if hasattr(self, 'tokens_canvas'):
            self.tokens_canvas.update_idletasks()

    def get_last_modified_map(self):
        # zawsze używamy predefiniowanej mapy
        if os.path.exists(DEFAULT_MAP_FILE):
            return DEFAULT_MAP_FILE
        # jeśli nie ma pliku, pozwalamy wybrać ręcznie
        print("⚠️  Nie znaleziono pliku domyślnej mapy. Użytkownik może wybrać ręcznie.")
        return filedialog.askopenfilename(
            title="Wybierz mapę",
            initialdir=os.path.dirname(DEFAULT_MAP_FILE),
            filetypes=[("Obrazy", "*.jpg *.png *.bmp"), ("Wszystkie pliki", "*.*")]
        )

    def build_gui(self):
        'Tworzy interfejs użytkownika.'
        # Panel boczny z przyciskami i paletą żetonów
        self.panel_frame = tk.Frame(self.root, bg="darkolivegreen", relief=tk.RIDGE, bd=5)
        self.panel_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # === SEKCJA OPERACJI (na górze) ===
        buttons_frame = tk.Frame(self.panel_frame, bg="darkolivegreen")
        buttons_frame.pack(side=tk.TOP, fill=tk.X)

        # Przycisk "Otwórz Mapę + Dane"
        self.open_map_and_data_button = tk.Button(
            buttons_frame, text="Otwórz Mapę + Dane", command=self.open_map_and_data,
            bg="saddlebrown", fg="white", activebackground="saddlebrown", activeforeground="white"
        )
        self.open_map_and_data_button.pack(padx=5, pady=2, fill=tk.X)

        # Przycisk "Zapisz dane mapy"
        self.save_map_and_data_button = tk.Button(
            buttons_frame, text="Zapisz mapę + eksport żetonów", command=self.save_map_and_data,
            bg="saddlebrown", fg="white", activebackground="saddlebrown", activeforeground="white"
        )
        self.save_map_and_data_button.pack(padx=5, pady=2, fill=tk.X)

        # === PRZYCISK ZMIANY ROZMIARU MAPY ===
        self.resize_map_button = tk.Button(
            buttons_frame, text="Zmień rozmiar mapy", command=self.resize_map_dialog,
            bg="saddlebrown", fg="white", activebackground="saddlebrown", activeforeground="white"
        )
        self.resize_map_button.pack(padx=5, pady=2, fill=tk.X)

        # === CHECKBOX AUTO-SAVE ===
        self.auto_save_var = tk.BooleanVar(value=True)
        auto_save_cb = tk.Checkbutton(buttons_frame, text="🔄 Auto-save", variable=self.auto_save_var,
                                     bg="darkolivegreen", fg="white", selectcolor="darkolivegreen",
                                     command=self.toggle_auto_save)
        auto_save_cb.pack(padx=5, pady=2, anchor="w")

        # === UTWORZENIE PANED WINDOW DLA LEPSZEGO ZARZĄDZANIA PRZESTRZENIĄ ===
        # Paned window dzieli pozostałą przestrzeń na paletę żetonów i panel informacyjny
        self.main_paned = tk.PanedWindow(self.panel_frame, orient=tk.VERTICAL, bg="darkolivegreen")
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # === GÓRNA CZĘŚĆ: Paleta żetonów i inne sekcje ===
        self.upper_frame = tk.Frame(self.main_paned, bg="darkolivegreen")
        self.main_paned.add(self.upper_frame, minsize=200)
        
        # === PALETA ŻETONÓW ===
        self.build_token_palette_in_frame(self.upper_frame)

        # === SEKCJA TERENU ===
        terrain_frame = tk.LabelFrame(self.upper_frame, text="Rodzaje terenu", bg="darkolivegreen", fg="white",
                                      font=("Arial", 9, "bold"))
        terrain_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.current_brush = None
        self.terrain_buttons = {}

        for terrain_key in TERRAIN_TYPES.keys():
            btn = tk.Button(
                terrain_frame,
                text=terrain_key.replace("_", " ").title(),
                width=16,
                bg="saddlebrown",
                fg="white",
                activebackground="saddlebrown",
                activeforeground="white",
                command=lambda k=terrain_key: self.toggle_brush(k)
            )
            btn.pack(padx=2, pady=1, fill=tk.X)
            self.terrain_buttons[terrain_key] = btn

        # === SEKCJA PUNKTÓW KLUCZOWYCH ===
        key_points_frame = tk.LabelFrame(self.upper_frame, text="Punkty kluczowe", bg="darkolivegreen", fg="white",
                                         font=("Arial", 9, "bold"))
        key_points_frame.pack(fill=tk.X, padx=5, pady=2)
        self.add_key_point_button = tk.Button(key_points_frame, text="Dodaj kluczowy punkt", command=self.add_key_point_dialog,
                                              bg="saddlebrown", fg="white", activebackground="saddlebrown", activeforeground="white")
        self.add_key_point_button.pack(padx=5, pady=2, fill=tk.X)

        # === SEKCJA PUNKTÓW ZRZUTU ===
        spawn_points_frame = tk.LabelFrame(self.upper_frame, text="Punkty zrzutu", bg="darkolivegreen", fg="white",
                                           font=("Arial", 9, "bold"))
        spawn_points_frame.pack(fill=tk.X, padx=5, pady=2)
        self.add_spawn_point_button = tk.Button(spawn_points_frame, text="Dodaj punkt wystawienia", command=self.add_spawn_point_dialog,
                                                bg="saddlebrown", fg="white", activebackground="saddlebrown", activeforeground="white")
        self.add_spawn_point_button.pack(padx=5, pady=2, fill=tk.X)
        
        # === RESET HEKSU ===
        reset_hex_frame = tk.LabelFrame(self.upper_frame, text="Reset wybranego heksu", bg="darkolivegreen", fg="white",
                                        font=("Arial", 9, "bold"))
        reset_hex_frame.pack(fill=tk.X, padx=5, pady=2)
        self.reset_hex_button = tk.Button(reset_hex_frame, text="Resetuj wybrany heks", command=self.reset_selected_hex,
                                          bg="saddlebrown", fg="white", activebackground="saddlebrown", activeforeground="white")
        self.reset_hex_button.pack(padx=5, pady=2, fill=tk.X)

        # === DOLNA CZĘŚĆ: Panel informacyjny ===
        self.lower_frame = tk.Frame(self.main_paned, bg="darkolivegreen")
        self.main_paned.add(self.lower_frame, minsize=150)
        
        # === PANEL INFORMACYJNY ===
        self.build_info_panel_in_frame(self.lower_frame)
        
        # === CANVAS MAPY ===
        self.build_map_canvas()

    def build_token_palette_in_frame(self, parent_frame):
        """Buduje paletę żetonów z filtrami w podanym frame"""
        palette_frame = tk.LabelFrame(parent_frame, text="Paleta żetonów", bg="darkolivegreen", fg="white",
                                     font=("Arial", 10, "bold"))
        # Kompaktowa paleta - nie zajmuje całej przestrzeni
        palette_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # === FILTRY ===
        filters_frame = tk.Frame(palette_frame, bg="darkolivegreen")
        filters_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # Checkbox unikalności
        self.uniqueness_var = tk.BooleanVar(value=True)
        uniqueness_cb = tk.Checkbutton(filters_frame, text="Unikalność", variable=self.uniqueness_var,
                                      bg="darkolivegreen", fg="white", selectcolor="darkolivegreen",
                                      command=self.toggle_uniqueness)
        uniqueness_cb.pack(side=tk.LEFT)
        
        # Filtry dowódcy (dropdown) - skalowalne rozwiązanie
        commanders_container = tk.Frame(palette_frame, bg="darkolivegreen", relief="sunken", bd=2)
        commanders_container.pack(fill=tk.X, padx=2, pady=3)
        
        tk.Label(commanders_container, text="🎖️ WYBÓR DOWÓDCY:", bg="darkolivegreen", fg="yellow", 
                font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(5,10))
        
        # Pobierz wszystkich dowódców z indeksu dynamicznie
        commanders_list = ["Wszystkie"]
        if self.token_index:
            unique_commanders = set()
            for token in self.token_index:
                owner = token.get("owner", "")
                if owner:
                    # Wyciągnij numer dowódcy z formatu "5 (Niemcy)" -> "5"
                    commander_num = owner.split()[0] if owner else ""
                    if commander_num.isdigit():
                        unique_commanders.add(commander_num)
            
            # Sortuj dowódców i dodaj z opisem nacji
            for commander_num in sorted(unique_commanders):
                # Znajdź nację dla tego dowódcy
                nation = ""
                for token in self.token_index:
                    if token.get("owner", "").startswith(commander_num + " "):
                        nation = token.get("nation", "")
                        break
                commanders_list.append(f"Dow. {commander_num} ({nation})")
        
        # Dropdown dowódców
        self.commander_dropdown = ttk.Combobox(commanders_container, 
                                             textvariable=self.filter_commander, 
                                             values=commanders_list, 
                                             state="readonly", 
                                             width=20)
        self.commander_dropdown.pack(side=tk.LEFT, padx=5)
        self.commander_dropdown.bind("<<ComboboxSelected>>", self.on_commander_selected)
        
        # Ustaw domyślny wybór
        self.filter_commander.set("Wszystkie")
        
        # === LISTA ŻETONÓW ===
        # Kontener z przewijaniem - KOMPAKTOWA WYSOKOŚĆ
        tokens_container = tk.Frame(palette_frame, bg="darkolivegreen")
        tokens_container.pack(fill=tk.X, padx=2, pady=2)
        
        # Ustaw mniejszą wysokość dla kontenera żetonów (około 200px)
        self.tokens_canvas = tk.Canvas(tokens_container, bg="darkolivegreen", highlightthickness=0, height=200)
        tokens_scrollbar = tk.Scrollbar(tokens_container, orient="vertical", command=self.tokens_canvas.yview)
        self.token_palette_frame = tk.Frame(self.tokens_canvas, bg="darkolivegreen")
        
        self.tokens_canvas.create_window((0, 0), window=self.token_palette_frame, anchor="nw")
        self.tokens_canvas.configure(yscrollcommand=tokens_scrollbar.set)
        
        self.tokens_canvas.pack(side="left", fill="x")
        tokens_scrollbar.pack(side="right", fill="y")
        
        # Bind scroll
        self.token_palette_frame.bind('<Configure>', lambda e: self.tokens_canvas.configure(scrollregion=self.tokens_canvas.bbox("all")))
        
        # Mouse wheel scrolling dla palety żetonów
        def on_mouse_wheel(event):
            self.tokens_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.tokens_canvas.bind("<MouseWheel>", on_mouse_wheel)
        self.token_palette_frame.bind("<MouseWheel>", on_mouse_wheel)
        
        # Wypełnij paletę
        self.refresh_token_palette()

    def build_info_panel_in_frame(self, parent_frame):
        """Buduje panel informacyjny o wybranym heksie w podanym frame"""
        self.control_panel_frame = tk.Frame(parent_frame, bg="darkolivegreen", relief=tk.RIDGE, bd=3)
        # Panel informacyjny zajmuje całą dostępną przestrzeń w dolnej części
        self.control_panel_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        tk.Label(self.control_panel_frame, text="Informacje o heksie", 
                 bg="darkolivegreen", fg="white", font=("Arial", 10, "bold")).pack(pady=2)
        
        # Kontener na informacje podstawowe
        basic_info_frame = tk.Frame(self.control_panel_frame, bg="darkolivegreen")
        basic_info_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Informacja o rozmiarze mapy
        self.map_size_label = tk.Label(basic_info_frame, text="Mapa: 56×40 (2240 heksów)", bg="darkolivegreen", fg="lightgreen", font=("Arial", 9, "bold"))
        self.map_size_label.pack(anchor="w", pady=1)
        
        self.hex_info_label = tk.Label(basic_info_frame, text="Heks: brak", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.hex_info_label.pack(anchor="w", pady=1)
        
        self.terrain_info_label = tk.Label(basic_info_frame, text="Teren: brak", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.terrain_info_label.pack(anchor="w", pady=1)
        
        self.token_info_label = tk.Label(basic_info_frame, text="Żeton: brak", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.token_info_label.pack(anchor="w", pady=1)
        
        # Dodatkowa informacja o stanie mapy
        self.map_status_label = tk.Label(basic_info_frame, text="", bg="darkolivegreen", fg="lightblue", font=("Arial", 8))
        self.map_status_label.pack(anchor="w", pady=1)

    def build_map_canvas(self):
        """Buduje canvas mapy z przewijaniem"""
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", cursor="cross")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Dodanie suwaka pionowego
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Przeniesienie poziomego suwaka do root
        self.h_scrollbar = tk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)

        # Bindowanie eventów
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # PPM - usuń żeton
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)  # Przeciąganie żetonów
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)  # Koniec przeciągania
        self.canvas.bind("<B2-Motion>", self.do_pan)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<Motion>", self.on_canvas_hover)
        
        # Bind klawiatury
        self.root.bind("<Delete>", self.delete_token_from_selected_hex)
        self.root.bind("<KeyPress-Shift_L>", self.enable_multi_placement)
        self.root.bind("<KeyRelease-Shift_L>", self.disable_multi_placement)
        self.root.focus_set()  # Aby klawiatura działała
        
        # Zmienne dla drag & drop
        self.drag_start_hex = None
        self.drag_token_data = None

    def refresh_token_palette(self):
        """Odświeża paletę żetonów według aktualnych filtrów"""
        print(f"🎨 Odświeżanie palety żetonów: {len(self.filtered_tokens)} do wyświetlenia")
        
        # Wyczyść poprzednie przyciski
        for widget in self.token_palette_frame.winfo_children():
            widget.destroy()
            
        if not self.filtered_tokens:
            # Pokaż komunikat jeśli brak żetonów
            no_tokens_label = tk.Label(self.token_palette_frame, 
                                     text="Brak żetonów\ndo wyświetlenia", 
                                     bg="darkolivegreen", fg="yellow", 
                                     font=("Arial", 10, "bold"))
            no_tokens_label.pack(pady=20)
            print("⚠️  Brak żetonów do wyświetlenia - dodano komunikat")
        else:
            # Utwórz przyciski dla przefiltrowanych żetonów
            created_buttons = 0
            for i, token in enumerate(self.filtered_tokens):
                try:
                    btn_frame = tk.Frame(self.token_palette_frame, bg="darkolivegreen")
                    btn_frame.pack(fill=tk.X, padx=2, pady=1)
                    
                    # Miniatura żetonu - napraw podwójną ścieżkę assets
                    img_path = fix_image_path(token["image"])
                    
                    if img_path.exists():
                        try:
                            img = Image.open(img_path).resize((32, 32))
                            img_tk = ImageTk.PhotoImage(img)
                            
                            # Skróć tekst przycisku
                            btn_text = token.get("label", token["id"])
                            if len(btn_text) > 20:
                                btn_text = btn_text[:17] + "..."
                            
                            btn = tk.Button(btn_frame, image=img_tk, text=btn_text,
                                           compound="left", anchor="w", 
                                           bg="saddlebrown", fg="white", relief="raised",
                                           command=lambda t=token: self.select_token_for_placement(t))
                            btn.image = img_tk  # Zachowaj referencję
                            btn.pack(fill=tk.X)
                            
                            # Dodaj tooltip z pełnymi informacjami
                            tooltip_text = f"ID: {token['id']}\nNacja: {token.get('nation', 'N/A')}\nTyp: {token.get('unitType', 'N/A')}\nRozmiar: {token.get('unitSize', 'N/A')}"
                            if 'combat_value' in token:
                                tooltip_text += f"\nWalka: {token['combat_value']}"
                            if 'price' in token:
                                tooltip_text += f"\nCena: {token['price']}"
                            
                            self.create_tooltip(btn, tooltip_text)
                            
                            # Zapamiętaj przycisk w tokenie dla późniejszego podświetlenia
                            token['_button'] = btn
                            created_buttons += 1
                            
                        except Exception as e:
                            print(f"❌ Błąd obrazu dla {token['id']}: {e}")
                            # Fallback dla uszkodzonych obrazów
                            btn = tk.Button(btn_frame, text=token.get("label", token["id"])[:20],
                                           bg="saddlebrown", fg="white", relief="raised",
                                           command=lambda t=token: self.select_token_for_placement(t))
                            btn.pack(fill=tk.X)
                            token['_button'] = btn
                            created_buttons += 1
                    else:
                        print(f"❌ Brak obrazu: {img_path}")
                        # Fallback dla brakujących obrazów
                        btn = tk.Button(btn_frame, text=f"❌ {token.get('label', token['id'])[:15]}",
                                       bg="red", fg="white", relief="raised",
                                       command=lambda t=token: self.select_token_for_placement(t))
                        btn.pack(fill=tk.X)
                        token['_button'] = btn
                        created_buttons += 1
                        
                except Exception as e:
                    print(f"❌ Błąd tworzenia przycisku dla {token.get('id', 'UNKNOWN')}: {e}")
            
            print(f"✅ Utworzono {created_buttons} przycisków żetonów")
        
        # Aktualizuj scroll region
        self.token_palette_frame.update_idletasks()
        self.tokens_canvas.configure(scrollregion=self.tokens_canvas.bbox("all"))
        print("📐 Zaktualizowano scroll region")

    def create_tooltip(self, widget, text):
        """Tworzy tooltip dla widgetu"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                           relief="solid", borderwidth=1, font=("Arial", 8))
            label.pack()
            widget.tooltip = tooltip
            
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def select_token_for_placement(self, token):
        """Wybiera żeton do wstawiania"""
        # Wyczyść poprzedni wybór
        if self.selected_token and '_button' in self.selected_token:
            try:
                self.selected_token['_button'].config(relief="raised", bg="saddlebrown")
            except tk.TclError:
                # Przycisk został usunięty podczas odświeżania palety, ignoruj błąd
                pass
            
        # Ustaw nowy wybór
        self.selected_token = token
        if '_button' in token:
            try:
                token['_button'].config(relief="sunken", bg="orange")
            except tk.TclError:
                # Przycisk został usunięty podczas odświeżania palety, ignoruj błąd
                pass
            
        print(f"🎯 Wybrano żeton: {token['id']} ({token.get('nation', 'N/A')})")

    def toggle_uniqueness(self):
        """Przełącza tryb unikalności żetonów"""
        self.uniqueness_mode = self.uniqueness_var.get()
        self.update_filtered_tokens()
        print(f"🔒 Tryb unikalności: {'ON' if self.uniqueness_mode else 'OFF'}")

    def set_commander_filter(self, commander):
        """Ustawia filtr konkretnego dowódcy"""
        self.filter_commander.set(commander)
        self.update_filtered_tokens()
        
        # Zaktualizuj przyciski dowódców
        for commander_name, btn in self.commander_buttons.items():
            if commander_name == commander:
                btn.config(relief="sunken", bg="orange")
            else:
                btn.config(relief="raised", bg="saddlebrown")
        
        print(f"�️  Ustawiono filtr dowódcy: {commander}")

    def enable_multi_placement(self, event):
        """Włącza tryb wielokrotnego wstawiania (Shift)"""
        self.multi_placement_mode = True
        print("⚡ Tryb wielokrotnego wstawiania: ON (Shift)")

    def disable_multi_placement(self, event):
        """Wyłącza tryb wielokrotnego wstawiania"""
        self.multi_placement_mode = False
        print("⚡ Tryb wielokrotnego wstawiania: OFF")

    def delete_token_from_selected_hex(self, event):
        """Usuwa żeton z zaznaczonego heksu (klawisz Delete)"""
        if self.selected_hex and self.selected_hex in self.hex_data:
            terrain = self.hex_data[self.selected_hex]
            if "token" in terrain:
                del terrain["token"]
                self.draw_grid()
                self.auto_save_and_export("usunięto żeton")
                print(f"Usunięto żeton z heksu {self.selected_hex}")
                self.update_filtered_tokens()  # Odśwież listę dostępnych żetonów

    def select_default_map_path(self):
        'Pozwala użytkownikowi wybrać nowe tło mapy.'
        file_path = filedialog.askopenfilename(
            title="Wybierz domyślną mapę",
            filetypes=[("Obrazy", "*.jpg *.png *.bmp"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            self.map_image_path = file_path
            self.config["map_image_path"] = file_path
            messagebox.showinfo("Sukces", "Wybrano nową domyślną mapę.")
        else:
            messagebox.showinfo("Anulowano", "Nie wybrano nowej mapy.")

    def load_map_image(self):
        'Wczytuje obraz mapy jako tło i ustawia rozmiary.'
        try:
            self.bg_image = Image.open(self.map_image_path).convert("RGB")
        except Exception as e:
            # jeśli nie udało się wczytać domyślnej mapy, poproś użytkownika o wybranie pliku
            print(f"⚠️  Nie udało się załadować domyślnej mapy: {e}")
            file = filedialog.askopenfilename(
                title="Wybierz mapę",
                filetypes=[("Obrazy", "*.jpg *.png *.bmp"), ("Wszystkie pliki", "*.*")]
            )
            if file:
                self.map_image_path = file
                return self.load_map_image()
            else:
                return
        self.world_width, self.world_height = self.bg_image.size
        self.photo_bg = ImageTk.PhotoImage(self.bg_image)
        # Ustaw obszar przewijania
        self.canvas.config(scrollregion=(0, 0, self.world_width, self.world_height))
        # Rysuj ponownie siatkę
        self.draw_grid()

    def draw_grid(self):
        """Rysuje siatkę heksów i aktualizuje wyświetlane żetony."""
        # Usuń tylko elementy siatki, zachowaj tło
        self.canvas.delete("hex")
        self.canvas.delete("spawn")
        self.canvas.delete("key_point")
        self.canvas.delete("highlight")
        
        # Upewnij się że tło jest wyświetlone
        if hasattr(self, 'photo_bg') and self.photo_bg:
            # Usuń stare tło i narysuj nowe
            self.canvas.delete("background")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_bg, tags="background")
        
        self.hex_centers = {}
        s = self.hex_size
        hex_height = math.sqrt(3) * s
        horizontal_spacing = 1.5 * s
        grid_cols = self.config.get("grid_cols")
        grid_rows = self.config.get("grid_rows")

        # GENERUJEMY SIATKĘ W UKŁADZIE OFFSETOWYM EVEN-Q (prostokąt)
        for col in range(grid_cols):
            for row in range(grid_rows):
                # Konwersja offset -> axial (even-q)
                q = col
                r = row - (col // 2)
                center_x = s + col * horizontal_spacing
                center_y = (s * math.sqrt(3) / 2) + row * hex_height
                if col % 2 == 1:
                    center_y += hex_height / 2
                if center_x + s > self.world_width or center_y + (s * math.sqrt(3) / 2) > self.world_height:
                    continue
                hex_id = f"{q},{r}"
                self.hex_centers[hex_id] = (center_x, center_y)

                # Dodanie domyślnych danych terenu płaskiego, jeśli brak danych
                if hex_id not in self.hex_data:
                    self.hex_data[hex_id] = {
                        "terrain_key": "teren_płaski",
                        "move_mod": 0,
                        "defense_mod": 0
                    }

                terrain = self.hex_data.get(hex_id, self.hex_defaults)
                self.draw_hex(hex_id, center_x, center_y, s, terrain)

        # Rysowanie żetonów na mapie
        self.canvas.image_store = []  # lista na referencje do obrazków
        for hex_id, terrain in self.hex_data.items():
            token = terrain.get("token")
            if token and "image" in token and hex_id in self.hex_centers:
                # normalizuj slashy na wszelki wypadek
                token["image"] = token["image"].replace("\\", "/")
                img_path = fix_image_path(token["image"])
                
                if not img_path.exists():
                    print(f"[WARN] Missing token image: {img_path}")
                    continue          # pomijamy brakujący plik
                img = Image.open(img_path).resize((self.hex_size, self.hex_size))
                tk_img = ImageTk.PhotoImage(img)
                cx, cy = self.hex_centers[hex_id]
                self.canvas.create_image(cx, cy, image=tk_img)
                self.canvas.image_store.append(tk_img)

        # nakładka mgiełki dla punktów zrzutu
        for nation, hex_list in self.spawn_points.items():
            for hex_id in hex_list:
                self.draw_spawn_marker(nation, hex_id)

        # rysowanie znaczników kluczowych punktów
        for hex_id, kp in self.key_points.items():
            self.draw_key_point_marker(kp['type'], kp['value'], hex_id)

        # Podświetlenie wybranego heksu
        if self.selected_hex is not None:
            self.highlight_hex(self.selected_hex)
        
        # Aktualizacja stanu mapy
        self.update_map_status()

    def draw_hex(self, hex_id, center_x, center_y, s, terrain=None):
        'Rysuje pojedynczy heksagon na canvasie wraz z tekstem modyfikatorów.'
        points = get_hex_vertices(center_x, center_y, s)
        self.canvas.create_polygon(points, outline="red", fill="", width=2, tags=("hex", hex_id))
        
        # usuwamy poprzedni tekst
        self.canvas.delete(f"tekst_{hex_id}")
        # rysujemy modyfikatory tylko jeśli ten heks ma niestandardowe dane
        if hex_id in self.hex_data:
            move_mod = terrain.get('move_mod', 0)
            defense_mod = terrain.get('defense_mod', 0)
            tekst = f"M:{move_mod} D:{defense_mod}"
            self.canvas.create_text(
                center_x, center_y,
                text=tekst,
                fill="blue",
                font=("Arial", 10),
                anchor="center",
                tags=("hex", f"tekst_{hex_id}")
            )

    def draw_spawn_marker(self, nation, hex_id):
        """Rysuje prosty, wyraźny znacznik punktu wystawienia (kolorowa obwódka + litera nacji)."""
        if hex_id not in self.hex_centers:
            return
        cx, cy = self.hex_centers[hex_id]
        color_map = {"Polska": ("#ff5555", "P"), "Niemcy": ("#5555ff", "N")}
        outline, letter = color_map.get(nation, ("#ffffff", nation[:1].upper()))
        r_c = int(self.hex_size * 0.55)
        self.canvas.create_oval(
            cx - r_c, cy - r_c, cx + r_c, cy + r_c,
            outline=outline, width=3, tags=("spawn", f"spawn_{nation}_{hex_id}")
        )
        self.canvas.create_text(
            cx, cy + self.hex_size * 0.60,
            text=letter,
            fill=outline,
            font=("Arial", 10, "bold"),
            tags=("spawn", f"spawn_{nation}_{hex_id}")
        )

    def draw_key_point_marker(self, key_type, value, hex_id):
        """Rysuje kolorowy znacznik punktu kluczowego (kółko + skrót typu)."""
        if hex_id not in self.hex_centers:
            return
        cx, cy = self.hex_centers[hex_id]
        
        # Mapowanie typów na kolory i skróty (max 2 znaki)
        color_map = {
            "most": ("#FFD700", "Mo"),          # Złoty
            "miasto": ("#FF6B35", "Mi"),        # Pomarańczowy
            "węzeł komunikacyjny": ("#4ECDC4", "WK"),  # Turkusowy
            "fortyfikacja": ("#45B7D1", "Fo")   # Niebieski
        }
        
        outline, letter = color_map.get(key_type, ("#FFFF00", key_type[:2].upper()))
        
        # Rysuj kółko (mniejsze niż spawn points)
        r_c = int(self.hex_size * 0.45)
        self.canvas.create_oval(
            cx - r_c, cy - r_c, cx + r_c, cy + r_c,
            outline=outline, width=3, fill="",  # Bez wypełnienia, tylko obramowanie
            tags=("key_point", f"key_point_{key_type}_{hex_id}")
        )
        
        # Rysuj skrót typu
        self.canvas.create_text(
            cx, cy,
            text=letter,
            fill="black",
            font=("Arial", 9, "bold"),
            tags=("key_point", f"key_point_{key_type}_{hex_id}")
        )
        
        # Rysuj wartość pod kółkiem
        self.canvas.create_text(
            cx, cy + self.hex_size * 0.65,
            text=str(value),
            fill=outline,
            font=("Arial", 8, "bold"),
            tags=("key_point", f"key_point_{key_type}_{hex_id}")
        )

    def get_clicked_hex(self, x, y):
        for hex_id, (cx, cy) in self.hex_centers.items():
            vertices = get_hex_vertices(cx, cy, self.hex_size)
            if point_in_polygon(x, y, vertices):
                return hex_id  # Zwracaj hex_id jako string "q,r"
        return None

    def on_canvas_click(self, event):
        """Obsługuje LPM na canvasie - wstawia żeton lub wybiera heks"""
        # Wyczyść stan przeciągania na wszelki wypadek
        self.drag_start_hex = None
        self.drag_token_data = None
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        hex_id = self.get_clicked_hex(x, y)
        
        if hex_id:
            # Jeśli mamy wybrany żeton do wstawienia
            if self.selected_token:
                self.place_token_on_hex_new(self.selected_token, hex_id)
                
                # Jeśli nie jest tryb wielokrotnego wstawiania, wyczyść wybór
                if not self.multi_placement_mode:
                    self.clear_token_selection_new()
                return
                
            # Kompatybilność z starym systemem
            if hasattr(self, 'selected_token_for_deployment') and self.selected_token_for_deployment:
                self.place_token_on_hex(self.selected_token_for_deployment, hex_id)
                self.clear_token_selection()
                return
                
            # Jeśli jest aktywny pędzel terenu
            if self.current_brush:
                q, r = map(int, hex_id.split(","))
                self.paint_hex((q, r), self.current_brush)
                return
                
            # Standardowe zaznaczenie heksu
            self.selected_hex = hex_id
            self.highlight_hex(hex_id)
            self.update_hex_info_display(hex_id)
        else:
            # Kliknięcie w pustą przestrzeń - wyczyść wybór żetonu
            if self.selected_token:
                self.clear_token_selection_new()
            elif hasattr(self, 'selected_token_for_deployment') and self.selected_token_for_deployment:
                self.clear_token_selection()

    def on_canvas_right_click(self, event):
        """Obsługuje PPM na canvasie - usuwa żeton z heksu"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        hex_id = self.get_clicked_hex(x, y)
        
        if hex_id and hex_id in self.hex_data:
            terrain = self.hex_data[hex_id]
            if "token" in terrain:
                del terrain["token"]
                self.draw_grid()
                self.auto_save_and_export("usunięto żeton PPM")
                print(f"Usunięto żeton z heksu {hex_id}")
                self.update_filtered_tokens()  # Odśwież listę dostępnych żetonów

    def on_canvas_drag(self, event):
        """Obsługuje przeciąganie żetonów między heksami"""
        if not self.drag_start_hex:
            # Rozpocznij przeciąganie jeśli kliknięto na heks z żetonem
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            hex_id = self.get_clicked_hex(x, y)
            
            if hex_id and hex_id in self.hex_data:
                terrain = self.hex_data[hex_id]
                if "token" in terrain and not self.selected_token:  # Tylko jeśli nie ma wybranego żetonu do wstawienia
                    self.drag_start_hex = hex_id
                    self.drag_token_data = terrain["token"].copy()
                    print(f"Rozpoczęto przeciąganie żetonu z {hex_id}")

    def on_canvas_release(self, event):
        """Obsługuje zakończenie przeciągania żetonu"""
        if self.drag_start_hex and self.drag_token_data:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            target_hex = self.get_clicked_hex(x, y)
            
            if target_hex and target_hex != self.drag_start_hex:
                # Sprawdź czy docelowy heks jest pusty
                if target_hex not in self.hex_data or "token" not in self.hex_data[target_hex]:
                    # Przenieś żeton
                    if target_hex not in self.hex_data:
                        self.hex_data[target_hex] = {
                            "terrain_key": "teren_płaski",
                            "move_mod": 0,
                            "defense_mod": 0
                        }
                    
                    # Dodaj żeton do docelowego heksu
                    self.hex_data[target_hex]["token"] = self.drag_token_data
                    
                    # Usuń żeton ze źródłowego heksu
                    del self.hex_data[self.drag_start_hex]["token"]
                    
                    # Odśwież mapę
                    self.draw_grid()
                    self.auto_save_and_export("przeniesiono żeton")
                    print(f"Przeniesiono żeton z {self.drag_start_hex} do {target_hex}")
                else:
                    print(f"Docelowy heks {target_hex} już ma żeton")
            
        # Wyczyść stan przeciągania
        self.drag_start_hex = None
        self.drag_token_data = None

    def place_token_on_hex_new(self, token, hex_id):
        """Umieszcza żeton na heksie (nowa wersja)"""
        # Sprawdź czy heks już ma żeton
        if hex_id in self.hex_data and "token" in self.hex_data[hex_id]:
            print(f"Heks {hex_id} już ma żeton")
            return
            
        # Sprawdź unikalność
        if self.uniqueness_mode:
            for terrain in self.hex_data.values():
                existing_token = terrain.get("token")
                if existing_token and existing_token.get("unit") == token["id"]:
                    print(f"Żeton {token['id']} już jest na mapie (tryb unikalności)")
                    return
        
        # Jeśli brak wpisu dla heksu, utwórz domyślny
        if hex_id not in self.hex_data:
            self.hex_data[hex_id] = {
                "terrain_key": "teren_płaski",
                "move_mod": 0,
                "defense_mod": 0
            }
        
        # Dodaj żeton
        rel_path = token["image"].replace("\\", "/")
        self.hex_data[hex_id]["token"] = {
            "unit": token["id"],
            "image": rel_path
        }
        
        # Odśwież mapę i zapisz
        self.draw_grid()
        self.auto_save_and_export("wstawiono żeton")
        print(f"Wstawiono żeton {token['id']} na heks {hex_id}")
        
        # Odśwież listę dostępnych żetonów
        self.update_filtered_tokens()

    def clear_token_selection_new(self):
        """Czyści wybór żetonu (nowa wersja)"""
        if self.selected_token and '_button' in self.selected_token:
            try:
                # Sprawdź czy przycisk nadal istnieje w interfejsie
                self.selected_token['_button'].config(relief="raised", bg="saddlebrown")
            except tk.TclError:
                # Przycisk został usunięty podczas odświeżania palety, ignoruj błąd
                pass
        self.selected_token = None
        print("Wyczyszczono wybór żetonu")

    def update_hex_info_display(self, hex_id):
        """Aktualizuje wyświetlane informacje o heksie"""
        terrain = self.hex_data.get(hex_id, self.hex_defaults)
        
        # Podstawowe info
        self.hex_info_label.config(text=f"Heks: {hex_id}")
        
        # Teren
        terrain_key = terrain.get('terrain_key', 'teren_płaski')
        move_mod = terrain.get('move_mod', 0)
        defense_mod = terrain.get('defense_mod', 0)
        self.terrain_info_label.config(text=f"Teren: {terrain_key} (M:{move_mod} D:{defense_mod})")
        
        # Żeton
        token = terrain.get("token")
        if token:
            token_info = f"Żeton: {token.get('unit', 'nieznany')}"
        else:
            token_info = "Żeton: brak"
        self.token_info_label.config(text=token_info)
        
        # Sprawdź czy to Key Point
        key_point_info = ""
        if hex_id in self.key_points:
            key_data = self.key_points[hex_id]
            key_type = key_data.get('type', 'nieznany')
            key_value = key_data.get('value', 0)
            key_point_info = f"🔑 Key Point: {key_type} (wartość: {key_value})"
        
        # Sprawdź czy to Spawn Point
        spawn_point_info = ""
        for nation, spawn_list in self.spawn_points.items():
            if hex_id in spawn_list:
                spawn_point_info = f"🚀 Spawn Point: {nation}"
                break
        
        # Aktualizuj etykiety - dodaj nowe jeśli nie istnieją
        if not hasattr(self, 'key_point_info_label'):
            # Dodaj nowe etykiety do basic_info_frame
            basic_info_frame = self.hex_info_label.master
            self.key_point_info_label = tk.Label(basic_info_frame, text="", bg="darkolivegreen", fg="yellow", font=("Arial", 9))
            self.key_point_info_label.pack(anchor="w", pady=1)
            
            self.spawn_point_info_label = tk.Label(basic_info_frame, text="", bg="darkolivegreen", fg="lightblue", font=("Arial", 9))
            self.spawn_point_info_label.pack(anchor="w", pady=1)
        
        # Zaktualizuj informacje o key point i spawn point
        self.key_point_info_label.config(text=key_point_info)
        self.spawn_point_info_label.config(text=spawn_point_info)

    def auto_save_and_export(self, reason):
        """Automatyczny zapis danych mapy i eksport żetonów z debounce"""
        # Sprawdź czy auto-save jest włączony
        if not self.auto_save_enabled:
            return
            
        # Natychmiastowy zapis map_data.json
        try:
            self.save_data()
        except Exception as e:
            print(f"Błąd zapisu danych: {e}")
            
        # Debounce eksportu start_tokens.json
        if self._auto_save_after:
            self.root.after_cancel(self._auto_save_after)
        self._auto_save_after = self.root.after(500, self.export_start_tokens_delayed)
        
        print(f"Auto-save: {reason}")

    def export_start_tokens_delayed(self):
        """Opóźniony eksport start_tokens.json"""
        try:
            count = self.export_start_tokens(show_message=False)
            print(f"Auto-export start_tokens.json ({count} żetonów)")
        except Exception as e:
            print(f"Błąd eksportu żetonów: {e}")

    def highlight_hex(self, hex_id):
        'Oznacza wybrany heks żółtą obwódką.'
        self.canvas.delete("highlight")
        if hex_id in self.hex_centers:
            cx, cy = self.hex_centers[hex_id]
            s = self.hex_size
            self.canvas.create_oval(cx - s, cy - s, cx + s, cy + s,
                                    outline="yellow", width=3, tags="highlight")

    # --- STATUS / AUTO SAVE ---
    def set_status(self, msg: str):
        if hasattr(self, 'status_label'):
            self.status_label.config(text=msg)
        # opcjonalnie print
        # print('[STATUS]', msg)

    def auto_save(self, reason: str):
        if not getattr(self, 'auto_save_enabled', None):
            return
        if not self.auto_save_enabled.get():
            return
        # debounce
        if hasattr(self, '_auto_save_after') and self._auto_save_after:
            self.root.after_cancel(self._auto_save_after)
        self._auto_save_after = self.root.after(500, lambda: self._perform_auto_save(reason))

    def _perform_auto_save(self, reason: str):
        try:
            self.save_data()
            self.set_status(f'Auto-save: {reason}')
        except Exception as e:
            self.set_status(f'Auto-save błąd: {e}')

    def on_canvas_hover(self, event):
        """Obsługuje hover nad canvasem - ghost preview i zoom żetonów"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        hex_id = self.get_clicked_hex(x, y)
        self.canvas.delete("hover_zoom")
        
        if not hex_id:
            if hasattr(self, '_hover_zoom_images'):
                self._hover_zoom_images.clear()
            return
            
        terrain = self.hex_data.get(hex_id, self.hex_defaults)
        token_existing = terrain.get('token')
        
        # 1. Ghost preview dla nowego systemu żetonów
        if self.selected_token and not token_existing and hex_id in self.hex_centers:
            cx, cy = self.hex_centers[hex_id]
            s_zoom = int(self.hex_size * 1.2)
            
            # Sprawdź czy można postawić żeton (unikalność)
            can_place = True
            color = "#00ffaa"  # zielony
            
            if self.uniqueness_mode:
                for terrain_check in self.hex_data.values():
                    existing_token = terrain_check.get("token")
                    if existing_token and existing_token.get("unit") == self.selected_token["id"]:
                        can_place = False
                        color = "#ff0000"  # czerwony
                        break
            
            # Rysuj obwódkę
            points = get_hex_vertices(cx, cy, s_zoom)
            self.canvas.create_polygon(points, outline=color, width=2, dash=(4,2), fill="", tags="hover_zoom")
            
            # Rysuj ghost image
            img_path = fix_image_path(self.selected_token["image"])
            
            if img_path.exists():
                key_cache = (img_path, s_zoom)
                tk_img = self._ghost_cache.get(key_cache)
                if tk_img is None:
                    try:
                        base = Image.open(img_path).convert('RGBA').resize((s_zoom, s_zoom))
                        r,g,b,a = base.split()
                        # Przezroczystość w zależności od możliwości postawienia
                        alpha = 0.55 if can_place else 0.3
                        a = a.point(lambda v: int(v*alpha))
                        base = Image.merge('RGBA', (r,g,b,a))
                        tk_img = ImageTk.PhotoImage(base)
                        self._ghost_cache[key_cache] = tk_img
                    except Exception:
                        tk_img = None
                        
                if tk_img:
                    self.canvas.create_image(cx, cy, image=tk_img, tags='hover_zoom')
                    if not hasattr(self, '_hover_zoom_images'):
                        self._hover_zoom_images = []
                    self._hover_zoom_images.append(tk_img)
                    
            # Czerwony X jeśli nie można postawić
            if not can_place:
                self.canvas.create_text(cx, cy, text="✗", fill="red", font=("Arial", 20, "bold"), tags="hover_zoom")
            
            return
            
        # 2. Kompatybilność ze starym systemem
        if hasattr(self, 'selected_token_for_deployment') and self.selected_token_for_deployment and not token_existing and hex_id in self.hex_centers:
            cx, cy = self.hex_centers[hex_id]
            s_zoom = int(self.hex_size * 1.2)
            points = get_hex_vertices(cx, cy, s_zoom)
            self.canvas.create_polygon(points, outline="#00ffaa", width=2, dash=(4,2), fill="", tags="hover_zoom")
            img_path = None
            sel = self.selected_token_for_deployment
            if sel:
                if sel.get('image_path'):
                    img_path = Path(sel['image_path'])
                elif sel.get('image'):
                    img_path = fix_image_path(sel['image'])
            if img_path and img_path.exists():
                key_cache = (img_path, s_zoom)
                tk_img = self._ghost_cache.get(key_cache)
                if tk_img is None:
                    try:
                        base = Image.open(img_path).convert('RGBA').resize((s_zoom, s_zoom))
                        r,g,b,a = base.split()
                        a = a.point(lambda v: int(v*0.55))
                        base = Image.merge('RGBA', (r,g,b,a))
                        tk_img = ImageTk.PhotoImage(base)
                        self._ghost_cache[key_cache] = tk_img
                    except Exception:
                        tk_img = None
                if tk_img:
                    self.canvas.create_image(cx, cy, image=tk_img, tags='hover_zoom')
                    if not hasattr(self, '_hover_zoom_images'):
                        self._hover_zoom_images = []
                    self._hover_zoom_images.append(tk_img)
            return
            
        # 3. Powiększenie istniejącego żetonu
        if token_existing and 'image' in token_existing and hex_id in self.hex_centers:
            cx, cy = self.hex_centers[hex_id]
            move_mod = terrain.get('move_mod',0)
            defense_mod = terrain.get('defense_mod',0)
            s_zoom = int(self.hex_size * 1.5)
            points = get_hex_vertices(cx, cy, s_zoom)
            self.canvas.create_polygon(points, outline='orange', fill='#ffffcc', width=3, tags='hover_zoom')
            label = f"M:{move_mod} D:{defense_mod}"
            if token_existing.get('unit'):
                label += f"\n{token_existing['unit']}"
            self.canvas.create_text(cx, cy, text=label, fill='black', font=('Arial', 14, 'bold'), tags='hover_zoom')
            img_path = fix_image_path(token_existing['image'])
            
            if img_path.exists():
                try:
                    img = Image.open(img_path).resize((s_zoom, s_zoom))
                    tk_img = ImageTk.PhotoImage(img)
                    self.canvas.create_image(cx, cy, image=tk_img, tags='hover_zoom')
                    if not hasattr(self, '_hover_zoom_images'):
                        self._hover_zoom_images = []
                    self._hover_zoom_images.append(tk_img)
                except Exception:
                    pass

    def save_data(self):
        'Zapisuje aktualne dane (teren, kluczowe punkty, spawn_points) do pliku JSON.'
        # --- USUWANIE MARTWYCH ŻETONÓW ---
        for hex_id, terrain in list(self.hex_data.items()):
            token = terrain.get("token")
            if token and "image" in token:
                img_path = fix_image_path(token["image"])
                if not img_path.exists():
                    terrain.pop("token", None)
        # --- KONIEC USUWANIA ---
        # ZAPISZ CAŁĄ SIATKĘ HEKSÓW (nie tylko zmienione)
        map_data = {
            "meta": {
                "hex_size": self.hex_size,
                "cols": self.config.get("grid_cols"),
                "rows": self.config.get("grid_rows"),
                "coord_system": "axial",
                "orientation": "pointy"
            },
            "terrain": self.hex_data,
            "key_points": self.key_points,
            "spawn_points": self.spawn_points
        }
        self.current_working_file = self.get_working_data_path()
        print(f"Zapisywanie danych do: {self.current_working_file}")
        with open(self.current_working_file, "w", encoding="utf-8") as f:
            import json
            json.dump(map_data, f, indent=2, ensure_ascii=False)
        # messagebox.showinfo("Zapisano", f"Dane mapy zostały zapisane w:\n{self.current_working_file}\n"
        #                                 f"Liczba kluczowych punktów: {len(self.key_points)}\n"
        #                                 f"Liczba punktów wystawienia: {sum(len(v) for v in self.spawn_points.values())}")

    def load_data(self):
        'Wczytuje dane z pliku roboczego (teren, kluczowe i spawn).'
        self.current_working_file = self.get_working_data_path()
        print(f"Wczytywanie danych z: {self.current_working_file}")
        loaded_data = wczytaj_dane_hex(self.current_working_file)
        if loaded_data:
            orientation = loaded_data.get("meta", {}).get("orientation", "pointy")
            self.orientation = orientation  # przechowaj w obiekcie, przyda się GUI
            if "meta" not in loaded_data:          # plik starego formatu
                self.hex_data = loaded_data
                self.key_points = {}
                self.spawn_points = {}
            else:
                self.hex_data   = loaded_data.get("terrain", {})
                self.key_points = loaded_data.get("key_points", {})
                self.spawn_points = loaded_data.get("spawn_points", {})
            self.hex_tokens = {
                hex_id: terrain["image"]
                for hex_id, terrain in self.hex_data.items()
                if "image" in terrain and os.path.exists(terrain["image"])
            }
            # MIGRACJA starej struktury tokenów
            for hid, hinfo in list(self.hex_data.items()):
                # 1) absolutna ścieżka w korzeniu heksu -> token + rel
                if "image" in hinfo:
                    img = hinfo.pop("image")
                    hinfo["token"] = {"unit": Path(img).stem, "image": to_rel(img)}

                # 2) przenieś png_file do image, jeśli jeszcze nie przeniesione
                if "token" in hinfo and "png_file" in hinfo["token"]:
                    pf = hinfo["token"].pop("png_file")
                    if "image" not in hinfo["token"]:
                        hinfo["token"]["image"] = to_rel(pf)

                # 3) upewnij się, że image jest relatywne
                if "token" in hinfo and "image" in hinfo["token"]:
                    hinfo["token"]["image"] = to_rel(hinfo["token"]["image"])
            # zawsze upewnij się, że tło jest załadowane
            self.load_map_image()

            # Automatyczne skalowanie tła do aktualnego rozmiaru siatki
            current_cols = self.config.get("grid_cols", 56)
            current_rows = self.config.get("grid_rows", 40)
            self.scale_background_image_if_needed(current_cols, current_rows)

            # i dopiero potem rysuj grid
            self.draw_grid()
            
            # Odśwież paletę żetonów
            self.update_filtered_tokens()
            
            # Nie pokazuj popup przy starcie - tylko loguj do konsoli
            print(f"✅ Wczytano dane mapy z: {self.current_working_file}")
            print(f"📍 Kluczowe punkty: {len(self.key_points)}")
            print(f"🚀 Punkty wystawienia: {sum(len(v) for v in self.spawn_points.values())}")
        else:
            print("⚠️  Brak danych do wczytania lub plik nie istnieje")

    def clear_variables(self):
        'Kasuje wszystkie niestandardowe ustawienia mapy (reset do płaskiego terenu).'
        answer = messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz zresetować mapę do domyślnego terenu płaskiego?")
        if answer:
            self.hex_data = {}
            self.key_points = {}
            self.spawn_points = {}
            zapisz_dane_hex({"terrain": {}, "key_points": {}, "spawn_points": {}}, self.current_working_file)
            self.draw_grid()
            messagebox.showinfo("Zresetowano", "Mapa została zresetowana do domyślnego terenu płaskiego.")

    def save_map_and_data(self):
        """Zapisuje dane JSON mapy i eksportuje żetony."""
        try:
            self.save_data()  # Zapisuje dane JSON
            count = self.export_start_tokens(show_message=False)  # Eksportuje żetony
            messagebox.showinfo("Sukces", f"Dane mapy zostały zapisane pomyślnie.\nWyeksportowano {count} żetonów.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać danych mapy: {e}")

    def toggle_auto_save(self):
        """Zmienia stan auto-save"""
        self.auto_save_enabled = self.auto_save_var.get()
        status = "włączony" if self.auto_save_enabled else "wyłączony"
        print(f"Auto-save {status}")

    def _is_hex_in_bounds(self, hex_id, max_q, max_r):
        """Sprawdza czy heks jest w granicach mapy."""
        try:
            q, r = map(int, hex_id.split(","))
            return not (q < 0 or q > max_q or r < -(q//2) or r > max_r - (q//2))
        except ValueError:
            return False

    def clean_out_of_bounds_data(self):
        """Usuwa dane z heksów poza granicami mapy."""
        grid_cols = self.config.get("grid_cols")
        grid_rows = self.config.get("grid_rows")
        
        # Oblicz maksymalne dozwolone współrzędne axial
        max_q = grid_cols - 1
        max_r = grid_rows - 1
        
        removed_items = {"terrain": 0, "tokens": 0, "key_points": 0, "spawn_points": 0}
        
        # Usuń dane terenu i żetonów poza granicami
        for hex_id in list(self.hex_data.keys()):
            try:
                q, r = map(int, hex_id.split(","))
                # Sprawdź czy heks jest poza granicami
                if q < 0 or q > max_q or r < -(q//2) or r > max_r - (q//2):
                    if "token" in self.hex_data[hex_id]:
                        removed_items["tokens"] += 1
                    removed_items["terrain"] += 1
                    del self.hex_data[hex_id]
            except ValueError:
                pass
        
        # Usuń key points poza granicami
        for hex_id in list(self.key_points.keys()):
            try:
                q, r = map(int, hex_id.split(","))
                if q < 0 or q > max_q or r < -(q//2) or r > max_r - (q//2):
                    removed_items["key_points"] += 1
                    del self.key_points[hex_id]
            except ValueError:
                pass
        
        # Usuń spawn points poza granicami
        for nation in self.spawn_points:
            original_len = len(self.spawn_points[nation])
            self.spawn_points[nation] = [
                hex_id for hex_id in self.spawn_points[nation]
                if self._is_hex_in_bounds(hex_id, max_q, max_r)
            ]
            removed_items["spawn_points"] += original_len - len(self.spawn_points[nation])
        
        return removed_items

    def scale_background_image_if_needed(self, new_cols, new_rows):
        """Automatycznie skaluje obraz tła do rozmiaru siatki heksów (bez pytania)."""
        if not hasattr(self, 'bg_image') or self.bg_image is None:
            print("⚠️ Brak obrazu tła - skalowanie pominięte")
            return False
            
        s = self.hex_size
        # Oblicz wymagane wymiary dla nowej siatki
        required_width = s + new_cols * 1.5 * s + s * 2  # dodatkowy margines
        required_height = (s * math.sqrt(3) / 2) + new_rows * math.sqrt(3) * s + s * 2
        
        print(f"📐 Wymagane wymiary: {required_width:.0f}×{required_height:.0f}")
        print(f"📐 Aktualne wymiary tła: {self.world_width}×{self.world_height}")
        
        # Zawsze skaluj obraz do wymaganego rozmiaru (nawet jeśli zniekształci proporcje)
        try:
            print(f"🔄 Automatyczne skalowanie obrazu do {required_width:.0f}×{required_height:.0f}...")
            
            # Skaluj obraz używając wysokiej jakości filtra (dokładne wymiary bez zachowania proporcji)
            from PIL import Image
            self.bg_image = self.bg_image.resize((int(required_width), int(required_height)), Image.LANCZOS)
            self.world_width, self.world_height = self.bg_image.size
            
            # Zaktualizuj wyświetlany obraz
            self.photo_bg = ImageTk.PhotoImage(self.bg_image)
            self.canvas.delete("background")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_bg, tags="background")
            
            # Zaktualizuj obszar przewijania
            self.canvas.config(scrollregion=(0, 0, self.world_width, self.world_height))
            
            print(f"✅ Obraz przeskalowany do {self.world_width}×{self.world_height}")
            return True
            
        except Exception as e:
            print(f"❌ Błąd skalowania obrazu: {e}")
            messagebox.showerror("Błąd skalowania", f"Nie udało się przeskalować obrazu: {e}")
            return False

    def count_invisible_hexes(self):
        """Liczy heksy które są poza granicami obrazu tła."""
        if not hasattr(self, 'world_width') or not hasattr(self, 'world_height'):
            return 0
            
        invisible_count = 0
        grid_cols = self.config.get("grid_cols")
        grid_rows = self.config.get("grid_rows")
        s = self.hex_size
        
        for col in range(grid_cols):
            for row in range(grid_rows):
                q = col
                r = row - (col // 2)
                
                # Oblicz pozycję centrum heksa
                center_x = s + col * 1.5 * s
                center_y = (s * math.sqrt(3) / 2) + row * math.sqrt(3) * s
                
                # Sprawdź czy heks jest poza granicami obrazu
                if center_x + s > self.world_width or center_y + (s * math.sqrt(3) / 2) > self.world_height:
                    invisible_count += 1
                    
        return invisible_count

    def update_map_status(self):
        """Aktualizuje informację o stanie mapy."""
        try:
            grid_cols = self.config.get("grid_cols", 56)
            grid_rows = self.config.get("grid_rows", 40)
            total_hexes = grid_cols * grid_rows
            invisible_hexes = self.count_invisible_hexes()
            
            # Aktualizuj informację o rozmiarze mapy (zawsze widoczne)
            size_text = f"📐 Mapa: {grid_cols}×{grid_rows} ({total_hexes} heksów)"
            self.map_size_label.config(text=size_text, fg="lightgreen")
            
            # Aktualizuj status problemów (tylko jeśli są)
            if invisible_hexes > 0:
                status_text = f"⚠️ {invisible_hexes} heksów poza obszarem tła"
                self.map_status_label.config(text=status_text, fg="orange")
            else:
                self.map_status_label.config(text="✅ Wszystkie heksy widoczne", fg="lightgreen")
                
        except Exception as e:
            self.map_status_label.config(text=f"Błąd stanu mapy: {e}", fg="red")

    def resize_map_dialog(self):
        """Okno dialogowe do zmiany rozmiaru mapy."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Zmień rozmiar mapy")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        current_cols = self.config.get("grid_cols", 56)
        current_rows = self.config.get("grid_rows", 40)
        
        # Informacja o aktualnym rozmiarze
        tk.Label(dialog, text=f"Aktualny rozmiar: {current_cols}×{current_rows} heksów",
                 font=("Arial", 10, "bold")).pack(pady=10)
        
        # Predefiniowane rozmiary
        presets_frame = tk.Frame(dialog)
        presets_frame.pack(pady=10)
        
        tk.Label(presets_frame, text="Predefiniowane rozmiary:", font=("Arial", 9, "bold")).grid(row=0, column=0, columnspan=4, pady=5)
        
        cols_var = tk.StringVar(value=str(current_cols))
        rows_var = tk.StringVar(value=str(current_rows))
        
        def apply_preset(cols, rows):
            cols_var.set(str(cols))
            rows_var.set(str(rows))
        
        preset_configs = [
            ("Małe (20×15)", 20, 15),
            ("Średnie (40×30)", 40, 30),
            ("Standardowe (56×40)", 56, 40),
            ("Duże (80×60)", 80, 60),
        ]
        
        for i, (name, cols, rows) in enumerate(preset_configs):
            btn = tk.Button(presets_frame, text=name, 
                            command=lambda c=cols, r=rows: apply_preset(c, r),
                            bg="saddlebrown", fg="white", width=15, font=("Arial", 8))
            btn.grid(row=1+(i//2), column=i%2, padx=5, pady=2)
        
        # Ramka na pola wprowadzania
        input_frame = tk.Frame(dialog)
        input_frame.pack(pady=15)
        
        tk.Label(input_frame, text="Własne wymiary:", font=("Arial", 9, "bold")).grid(row=0, column=0, columnspan=2, pady=5)
        
        tk.Label(input_frame, text="Kolumny:").grid(row=1, column=0, padx=5, sticky="e")
        cols_entry = tk.Entry(input_frame, textvariable=cols_var, width=8)
        cols_entry.grid(row=1, column=1, padx=5, sticky="w")
        cols_entry.bind('<Return>', lambda e: apply_resize())
        
        tk.Label(input_frame, text="Wiersze:").grid(row=2, column=0, padx=5, sticky="e")
        rows_entry = tk.Entry(input_frame, textvariable=rows_var, width=8)
        rows_entry.grid(row=2, column=1, padx=5, sticky="w")
        rows_entry.bind('<Return>', lambda e: apply_resize())
        
        # Informacja o automatycznym skalowaniu
        warning_label = tk.Label(dialog, text="ℹ️ Uwaga: Obraz tła zostanie automatycznie przeskalowany\ndo rozmiaru wybranej siatki heksów.",
                              fg="blue", font=("Arial", 9))
        warning_label.pack(pady=10)
        
        # Przyciski akcji
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=15, padx=20)
        
        def apply_resize():
            try:
                new_cols = int(cols_var.get())
                new_rows = int(rows_var.get())
                
                if new_cols <= 0 or new_rows <= 0:
                    messagebox.showerror("Błąd", "Wymiary muszą być dodatnie!")
                    return
                
                if new_cols > 200 or new_rows > 200:
                    if not messagebox.askyesno("Ostrzeżenie wydajności", 
                                           f"Bardzo duży rozmiar ({new_cols}×{new_rows}) może wpływać na wydajność.\nKontynuować?"):
                        return
                    
                # Ostrzeżenie jeśli zmniejszamy mapę
                if new_cols < current_cols or new_rows < current_rows:
                    if not messagebox.askyesno("Ostrzeżenie", 
                                           "Zmniejszenie rozmiaru może spowodować utratę danych poza nowymi granicami.\nKontynuować?"):
                        return
                
                # Aktualizacja konfiguracji
                self.config["grid_cols"] = new_cols
                self.config["grid_rows"] = new_rows
                
                # Automatyczne skalowanie tła (zawsze)
                scaling_success = self.scale_background_image_if_needed(new_cols, new_rows)
                
                # Usuń dane poza granicami jeśli zmniejszamy mapę
                removed_summary = ""
                if new_cols < current_cols or new_rows < current_rows:
                    removed = self.clean_out_of_bounds_data()
                    if any(removed.values()):
                        removed_summary = f"\n\nUsunięto elementy poza granicami:"
                        if removed['terrain']: removed_summary += f"\n• Tereny: {removed['terrain']}"
                        if removed['tokens']: removed_summary += f"\n• Żetony: {removed['tokens']}"
                        if removed['key_points']: removed_summary += f"\n• Punkty kluczowe: {removed['key_points']}"
                        if removed['spawn_points']: removed_summary += f"\n• Punkty wystawienia: {removed['spawn_points']}"
                
                # Przerysowanie siatki
                self.draw_grid()
                
                # Automatyczny zapis nowej konfiguracji
                if self.auto_save_enabled:
                    self.auto_save_and_export("resize_map")
                
                # Przygotowanie komunikatu o wyniku
                success_msg = f"Rozmiar mapy zmieniony na {new_cols}×{new_rows}."
                if scaling_success:
                    success_msg += f"\n\n✅ Obraz tła został automatycznie przeskalowany."
                else:
                    success_msg += f"\n\n⚠️ Uwaga: Wystąpił problem z automatycznym skalowaniem tła."
                success_msg += removed_summary
                
                dialog.destroy()
                messagebox.showinfo("Sukces", success_msg)
                
            except ValueError:
                messagebox.showerror("Błąd", "Wymiary muszą być liczbami całkowitymi!")
                
        tk.Button(button_frame, text="Zastosuj", command=apply_resize, 
                  bg="green", fg="white", width=12).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Anuluj", command=dialog.destroy, 
                  bg="red", fg="white", width=12).pack(side=tk.RIGHT, padx=10)

    def open_map_and_data(self):
        """Otwiera mapę i wczytuje dane."""
        try:
            # Domyślna ścieżka do mapy
            map_path = filedialog.askopenfilename(
                initialdir=DEFAULT_MAP_DIR,
                title="Wybierz mapę",
                filetypes=[("Obrazy", "*.jpg *.png *.bmp"), ("Wszystkie pliki", "*.*")]
            )
            if map_path:
                self.map_image_path = map_path
                self.load_map_image()
                self.load_data()
                messagebox.showinfo("Sukces", "Mapa i dane zostały pomyślnie wczytane.")
            else:
                messagebox.showinfo("Anulowano", "Nie wybrano mapy.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się otworzyć mapy i danych: {e}")

    def add_key_point_dialog(self):
        'Okno dialogowe do dodawania kluczowego punktu na wybranym heksie.'
        if self.selected_hex is None:
            messagebox.showinfo("Informacja", "Najpierw wybierz heks klikając na niego.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Dodaj kluczowy punkt")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="Wybierz typ punktu:", font=("Arial", 10)).pack(pady=10)
        point_types = list(self.available_key_point_types.keys())
        selected_type = tk.StringVar(value=point_types[0])
        tk.OptionMenu(dialog, selected_type, *point_types).pack()
        def save_key_point():
            ptype = selected_type.get()
            value = self.available_key_point_types[ptype]
            self.key_points[self.selected_hex] = {"type": ptype, "value": value}
            self.save_data()
            self.draw_key_point(self.selected_hex, ptype, value)
            messagebox.showinfo("Sukces", f"Dodano kluczowy punkt '{ptype}' o wartości {value} na heksie {self.selected_hex}.")
            dialog.destroy()
        tk.Button(dialog, text="Zapisz", command=save_key_point, bg="green", fg="white").pack(pady=10)
        tk.Button(dialog, text="Anuluj", command=dialog.destroy, bg="red", fg="white").pack(pady=5)
        # po sukcesie dodania key point
        self.auto_save('key point')

    def add_spawn_point_dialog(self):
        'Okno dialogowe do dodawania punktu wystawienia dla nacji.'
        if self.selected_hex is None:
            messagebox.showinfo("Informacja", "Najpierw wybierz heks klikając na niego.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Dodaj punkt wystawienia")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="Wybierz nację:", font=("Arial", 10)).pack(pady=10)
        selected_nation = tk.StringVar(value=self.available_nations[0])
        tk.OptionMenu(dialog, selected_nation, *self.available_nations).pack()
        def save_spawn_point():
            nation = selected_nation.get()
            self.spawn_points.setdefault(nation, []).append(self.selected_hex)
            self.save_data()
            self.draw_grid()  # Odśwież rysunek mapy, aby zobaczyć mgiełkę
            messagebox.showinfo("Sukces", f"Dodano punkt wystawienia dla nacji '{nation}' na heksie {self.selected_hex}.")
            dialog.destroy()
        tk.Button(dialog, text="Zapisz", command=save_spawn_point, bg="green", fg="white").pack(pady=10)
        tk.Button(dialog, text="Anuluj", command=dialog.destroy, bg="red", fg="white").pack(pady=5)
        # po sukcesie dodania spawn
        self.auto_save('spawn point')

    def draw_key_point(self, hex_id, point_type, value):
        'Rysuje na canvasie etykietę kluczowego punktu.'
        if hex_id in self.hex_centers:
            cx, cy = self.hex_centers[hex_id]
            self.canvas.create_text(cx, cy, text=f"{point_type}\n({value})", fill="yellow",
                                    font=("Arial", 10, "bold"), tags=f"key_point_{hex_id}")

    def apply_terrain(self, terrain_key):
        'Przypisuje wybrany typ terenu do aktualnie zaznaczonego heksu.'
        if self.selected_hex is None:
            messagebox.showinfo("Informacja", "Najpierw wybierz heks klikając na niego.")
            return
        terrain = TERRAIN_TYPES.get(terrain_key)
        if terrain:
            # Sprawdź, czy teren jest domyślny
            if (terrain.get('move_mod', 0) == self.hex_defaults.get('move_mod', 0) and
                terrain.get('defense_mod', 0) == self.hex_defaults.get('defense_mod', 0)):
                # Jeśli teren jest domyślny, usuń wpis z hex_data
                if self.selected_hex in self.hex_data:
                    del self.hex_data[self.selected_hex]
            else:
                # W przeciwnym razie, dodaj/zaktualizuj wpis z kluczem terenu
                self.hex_data[self.selected_hex] = {
                    "terrain_key": terrain_key,
                    "move_mod": terrain["move_mod"],
                    "defense_mod": terrain["defense_mod"]
                }
            # Zapisz dane i odrysuj heks
            self.save_data()
            cx, cy = self.hex_centers[self.selected_hex]
            self.draw_hex(self.selected_hex, cx, cy, self.hex_size, terrain)
            messagebox.showinfo("Zapisano", f"Dla heksu {self.selected_hex} ustawiono teren: {terrain_key}")
        else:
            messagebox.showerror("Błąd", "Niepoprawny rodzaj terenu.")

    def clear_token_selection(self):
        """Czyści aktualnie wybrany żeton do wystawienia."""
        if self.selected_token_button:
            try:
                # Sprawdź czy przycisk nadal istnieje (dialog może być zamknięty)
                self.selected_token_button.config(relief="raised", bg="saddlebrown")
            except tk.TclError:
                # Przycisk został zniszczony (dialog zamknięty) - ignoruj błąd
                pass
        self.selected_token_for_deployment = None
        self.selected_token_button = None

    def reset_selected_hex(self):
        """Czyści wszystkie dane przypisane do wybranego heksu i aktualizuje plik start_tokens.json."""
        if self.selected_hex is None:
            messagebox.showinfo("Informacja", "Najpierw wybierz heks klikając na niego.")
            return

        # Usuwanie danych przypisanych do heksu
        self.hex_data.pop(self.selected_hex, None)
        self.key_points.pop(self.selected_hex, None)
        for nation, hexes in self.spawn_points.items():
            if self.selected_hex in hexes:
                hexes.remove(self.selected_hex)
        # Usuwanie żetonu z hex_tokens
        self.hex_tokens.pop(self.selected_hex, None)

        # --- USUWANIE MARTWYCH WPISÓW ŻETONÓW Z CAŁEJ MAPY ---
        for hex_id, terrain in list(self.hex_data.items()):
            token = terrain.get("token")
            if token and "image" in token:
                img_path = fix_image_path(token["image"])
                if not img_path.exists():
                    terrain.pop("token", None)

        # Zapisanie zmian i odświeżenie mapy
        self.save_data()
        self.draw_grid()
        # Automatyczna aktualizacja pliku start_tokens.json po usunięciu żetonu
        self.export_start_tokens()
        messagebox.showinfo("Sukces", f"Dane dla heksu {self.selected_hex} zostały zresetowane.")

    def do_pan(self, event):
        'Przesuwa mapę myszką.'
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def start_pan(self, event):
        'Rozpoczyna przesuwanie mapy myszką.'
        self.canvas.scan_mark(event.x, event.y)

    def on_close(self):
        'Obsługuje zamknięcie aplikacji - daje możliwość zapisu mapy.'
        answer = messagebox.askyesno("Zamykanie programu", "Czy chcesz zapisać dane mapy przed zamknięciem?")
        if answer:
            self.save_map_and_data()
        self.root.destroy()

    def print_extreme_hexes(self):
        'Wypisuje w konsoli współrzędne skrajnych heksów (debug).'
        if not self.hex_centers:
            print("Brak heksów do analizy.")
            return
        xs = [coord[0] for coord in self.hex_centers.values()]
        ys = [coord[1] for coord in self.hex_centers.values()]
        print("Skrajne heksy:")
        print("Lewy skrajny (x) =", min(xs))
        print("Prawy skrajny (x) =", max(xs))
        print("Górny skrajny (y) =", min(ys))
        print("Dolny skrajny (y) =", max(ys))

    def get_working_data_path(self):
        # Zawsze zwracaj ścieżkę do data/map_data.json
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / "map_data.json")

    def load_tokens_from_folders(self, folders):
        """Wczytuje listę żetonów z podanych folderów (zgodnie z nową strukturą: token.json + token.png)."""
        tokens = []
        for folder in folders:
            if os.path.exists(folder):
                for subfolder in os.listdir(folder):
                    token_folder = os.path.join(folder, subfolder)
                    if os.path.isdir(token_folder):
                        json_path = os.path.join(token_folder, "token.json")   # poprawka: nowa nazwa pliku
                        png_path = os.path.join(token_folder, "token.png")     # poprawka: nowa nazwa pliku
                        if os.path.exists(json_path) and os.path.exists(png_path):
                            tokens.append({
                                "name": subfolder,
                                "json_path": json_path,
                                "image_path": png_path
                            })
        return tokens

    def deploy_token_dialog(self):
        """PRZESTARZAŁA METODA - używa nowej palety żetonów"""
        print("Metoda deploy_token_dialog jest przestarzała. Używaj nowej palety żetonów.")
        # Stara implementacja została zastąpiona przez paletę żetonów w panelu bocznym
        """Wyświetla okno dialogowe z wszystkimi dostępnymi żetonami w folderze tokeny (unikalność: żeton znika po wystawieniu)."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Wybierz żeton")
        dialog.geometry("300x300")  # Ustawienie rozmiaru okna
        dialog.transient(self.root)
        dialog.grab_set()

        # Konfiguracja siatki w oknie dialogowym
        dialog.rowconfigure(0, weight=1)
        dialog.columnconfigure(0, weight=1)

        # Ramka przewijana dla żetonów
        frame_container = tk.Frame(dialog, bg="darkolivegreen")
        frame_container.grid(row=0, column=0, sticky="nsew")

        frame_container.rowconfigure(0, weight=1)
        frame_container.columnconfigure(0, weight=1)

        canvas = tk.Canvas(frame_container, bg="darkolivegreen")
        canvas.grid(row=0, column=0, sticky="nsew")

        scroll_y = tk.Scrollbar(frame_container, orient="vertical", command=canvas.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")

        scroll_x = tk.Scrollbar(frame_container, orient="horizontal", command=canvas.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame = tk.Frame(canvas, bg="darkolivegreen")

        # Konfiguracja przewijania
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        # Wczytaj żetony z folderów
        token_base = str(ASSET_ROOT / "tokens")
        token_folders = [os.path.join(token_base, d)
                         for d in os.listdir(token_base)
                         if os.path.isdir(os.path.join(token_base, d))]
        tokens = self.load_tokens_from_folders(token_folders)

        # Filtruj żetony, które już są na mapie (unikalność)
        used_token_ids = set()
        for terrain in self.hex_data.values():
            token = terrain.get("token")
            if token and "unit" in token:
                used_token_ids.add(token["unit"])
        available_tokens = [t for t in tokens if self._get_token_id_from_json(t["json_path"]) not in used_token_ids]
        
        # Wyświetlanie żetonów
        for token in available_tokens:
            if os.path.exists(token["image_path"]):
                img = Image.open(token["image_path"]).resize((50, 50))
                img = ImageTk.PhotoImage(img)
                btn = tk.Button(
                    frame, image=img, text=token["name"], compound="top",
                    bg="saddlebrown", fg="white", relief="raised",
                    command=lambda t=token, b=None, d=dialog: self.select_token_for_deployment(t, b, d)
                )
                btn.image = img  # Przechowuj referencję do obrazu
                btn.pack(pady=5, padx=5, side="left")
                  # Zaktualizuj lambda, aby przekazać referencję do przycisku i dialoga
                btn.config(command=lambda t=token, b=btn, d=dialog: self.select_token_for_deployment(t, b, d))

        # Ustawienie scrollregion po dodaniu widgetów
        frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def select_token_for_deployment(self, token, button, dialog=None):
        """Wybiera żeton do wystawienia (system click-and-click)."""
        # Wyczyść poprzedni wybór
        self.clear_token_selection()

        # Ustaw nowy wybór
        self.selected_token_for_deployment = token
        self.selected_token_button = button

        # Podświetl wybrany przycisk
        if button is not None:
            button.config(relief="sunken", bg="orange")

        # Zamknij dialog po wyborze żetonu
        if dialog is not None:
            try:
                dialog.destroy()
            except Exception:
                pass

        # Informuj użytkownika
        self.set_status(f"Wybrano żeton: {token['name']} (kliknij heks aby postawić)")

    def _get_token_id_from_json(self, json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                token_json = json.load(f)
            return token_json.get("id")
        except Exception:
            return None

    def place_token_on_hex(self, token, clicked_hex):
        """Umieszcza wybrany żeton na wskazanym heksie (string 'q,r')."""
        if not token or not clicked_hex:
            return

        try:
            q, r = map(int, clicked_hex.split(","))
        except ValueError:
            return
        hex_id = f"{q},{r}"

        # Jeśli brak wpisu – utwórz z domyślnym terenem
        if hex_id not in self.hex_data:
            self.hex_data[hex_id] = {
                "terrain_key": "płaski",
                "move_mod": 0,
                "defense_mod": 0
            }

        # Wczytaj prawdziwe ID żetonu z token.json
        try:
            with open(token["json_path"], "r", encoding="utf-8") as f:
                token_json = json.load(f)
            token_id = token_json.get("id", Path(token["json_path"]).stem)
        except Exception:
            token_id = Path(token.get("json_path", "UNKNOWN.json")).stem

        rel_path = to_rel(token["image_path"]).replace("\\", "/")
        self.hex_data[hex_id]["token"] = {"unit": token_id, "image": rel_path}

        # Odśwież mapę i zapisz
        self.draw_grid()
        self.set_status(f"Postawiono żeton '{token['name']}' na {hex_id}")
        self.auto_save('postawiono żeton')

    def toggle_brush(self, key):
        if self.current_brush == key:           # drugi klik → wyłącz
            self.terrain_buttons[key].config(relief="raised")
            self.current_brush = None
            return
        # przełącz pędzel
        for k,b in self.terrain_buttons.items():
            b.config(relief="raised")
        self.terrain_buttons[key].config(relief="sunken")
        self.current_brush = key

    def paint_hex(self, clicked_hex, terrain_key):
        'Maluje heks wybranym typem terenu.'
        q, r = clicked_hex
        hex_id = f"{q},{r}"
        terrain = TERRAIN_TYPES.get(terrain_key)
        if terrain:
            if (terrain.get('move_mod', 0) == self.hex_defaults.get('move_mod', 0) and
                terrain.get('defense_mod', 0) == self.hex_defaults.get('defense_mod', 0)):
                if hex_id in self.hex_data:
                    del self.hex_data[hex_id]
            else:
                self.hex_data[hex_id] = {
                    "terrain_key": terrain_key,
                    "move_mod": terrain["move_mod"],
                    "defense_mod": terrain["defense_mod"]
                }
            self.save_data()
            cx, cy = self.hex_centers[hex_id]
            self.draw_hex(hex_id, cx, cy, self.hex_size, terrain)
        else:
            messagebox.showerror("Błąd", "Niepoprawny rodzaj terenu.")
        self.auto_save('malowanie terenu')

    def export_start_tokens(self, path=None, show_message=True):
        """Eksportuje rozmieszczenie wszystkich żetonów na mapie do assets/start_tokens.json."""
        if path is None:
            path = str(ASSET_ROOT / "start_tokens.json")
        tokens = []
        for hex_id, terrain in self.hex_data.items():
            token = terrain.get("token")
            if token and "unit" in token:
                try:
                    q, r = map(int, hex_id.split(","))
                except Exception:
                    continue
                tokens.append({
                    "id": token["unit"],
                    "q": q,
                    "r": r
                })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        
        if show_message:
            messagebox.showinfo("Sukces", f"Wyeksportowano rozmieszczenie żetonów do:\n{path}")
        return len(tokens)

    def on_commander_selected(self, event):
        """Obsługuje wybór dowódcy z dropdown"""
        selected_commander = self.commander_var.get()
        print(f"⚔️  Wybrano dowódcę z dropdown: {selected_commander}")
        
        if selected_commander == "Wszyscy dowódcy":
            self.commander_filter = None
        else:
            self.commander_filter = selected_commander
        
        self.update_filtered_tokens()

if __name__ == '__main__':
    import sys
    try:
        cfg = CONFIG  # użyj lokalnej stałej CONFIG
        root = tk.Tk()
        root.title('Map Editor')
        app = MapEditor(root, cfg)
        root.mainloop()
    except Exception as e:
        print('Błąd startu:', e, file=sys.stderr)
        raise
