import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk, colorchooser
import json
import math
import os
import shutil
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk, ImageFont

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
SOLID_BACKGROUND_COLOR = (48, 64, 40)
HEX_TEXTURE_GRID_SIZE = 64
HEX_TEXTURE_EXPORT_SIZE = 512
NEIGHBOR_PREVIEW_SCALE = 1.0
CONTEXT_CANVAS_SCALE = 1.8
EDGE_BAND_CELLS = 3

HEX_TEXTURE_DIR = ASSET_ROOT / "terrain" / "hex_painted"
HEX_TEXTURE_DIR.mkdir(parents=True, exist_ok=True)

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

# Kolory poglądowe dla podglądu sąsiednich heksów, używane gdy brak dedykowanej tekstury.
TERRAIN_PREVIEW_COLORS = {
    "teren_płaski": "#91a86b",
    "mała rzeka": "#3fa5d6",
    "duża rzeka": "#2b7aa6",
    "las": "#3f6d3a",
    "bagno": "#62795c",
    "mała miejscowość": "#b88b5a",
    "miasto": "#8a7c74",
    "most": "#d1b27c",
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
        if self.map_image_path:
            self.background_info = {
                "type": "image",
                "path": to_rel(str(self.map_image_path))
            }
        else:
            self.background_info = {
                "type": "solid",
                "color": list(SOLID_BACKGROUND_COLOR)
            }

        # --- Ustawienia heksów ---
        self.hex_size = self.config.get("hex_size", 30)
        self.hex_defaults = {"defense_mod": 0, "move_mod": 0}
        self.current_working_file = DATA_FILENAME_WORKING
        self.size_hard_limits = {"cols": (10, 160), "rows": (10, 120), "hex_size": (16, 64)}
        self.size_soft_limits = {"cols": 120, "rows": 90, "hex_size": 48}

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
        self.hex_texture_cache: dict[tuple[str, int], ImageTk.PhotoImage] = {}

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
            buttons_frame, text="Zapisz dane mapy", command=self.save_map_and_data,
            bg="saddlebrown", fg="white", activebackground="saddlebrown", activeforeground="white"
        )
        self.save_map_and_data_button.pack(padx=5, pady=2, fill=tk.X)

        # === CHECKBOX AUTO-SAVE ===
        self.auto_save_var = tk.BooleanVar(value=True)
        auto_save_cb = tk.Checkbutton(buttons_frame, text="🔄 Auto-save", variable=self.auto_save_var,
                                     bg="darkolivegreen", fg="white", selectcolor="darkolivegreen",
                                     command=self.toggle_auto_save)
        auto_save_cb.pack(padx=5, pady=2, anchor="w")

        # Przycisk konfiguracji mapy
        self.configure_map_button = tk.Button(
            buttons_frame,
            text="Konfiguracja mapy…",
            command=self.open_map_configuration_dialog,
            bg="saddlebrown",
            fg="white",
            activebackground="saddlebrown",
            activeforeground="white"
        )
        self.configure_map_button.pack(padx=5, pady=2, fill=tk.X)

        # === UTWORZENIE PANED WINDOW DLA LEPSZEGO ZARZĄDZANIA PRZESTRZENIĄ ===
        # Paned window dzieli pozostałą przestrzeń na paletę żetonów i panel informacyjny
        self.main_paned = tk.PanedWindow(self.panel_frame, orient=tk.VERTICAL, bg="darkolivegreen")
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # === GÓRNA CZĘŚĆ: Paleta żetonów i inne sekcje ===
        self.upper_container = tk.Frame(self.main_paned, bg="darkolivegreen")
        # Górny panel ma przejmować całą dodatkową przestrzeń na scrollowane sekcje
        self.main_paned.add(self.upper_container, minsize=200, stretch="always")
        self.upper_canvas = tk.Canvas(self.upper_container, bg="darkolivegreen", highlightthickness=0)
        self.upper_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.upper_scrollbar = tk.Scrollbar(self.upper_container, orient=tk.VERTICAL, command=self.upper_canvas.yview)
        self.upper_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.upper_canvas.configure(yscrollcommand=self.upper_scrollbar.set)
        self.upper_frame = tk.Frame(self.upper_canvas, bg="darkolivegreen")
        self.upper_frame_window = self.upper_canvas.create_window((0, 0), window=self.upper_frame, anchor="nw")
        self.upper_frame.bind("<Configure>", lambda _e: self.upper_canvas.configure(scrollregion=self.upper_canvas.bbox("all")))
        self.upper_canvas.bind("<Configure>", lambda e: self.upper_canvas.itemconfigure(self.upper_frame_window, width=e.width))
        self.upper_canvas.bind("<MouseWheel>", self._scroll_upper_panel)
        self.upper_frame.bind("<MouseWheel>", self._scroll_upper_panel)
        self.upper_canvas.bind("<Button-4>", self._scroll_upper_panel)
        self.upper_canvas.bind("<Button-5>", self._scroll_upper_panel)
        self.upper_frame.bind("<Button-4>", self._scroll_upper_panel)
        self.upper_frame.bind("<Button-5>", self._scroll_upper_panel)

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

        # === EKSPORT ŻETONÓW ===
        self.export_tokens_button = tk.Button(
            self.upper_frame,
            text="Eksportuj rozmieszczenie żetonów",
            command=self.export_start_tokens,
            bg="saddlebrown", fg="white", activebackground="saddlebrown", activeforeground="white"
        )
        self.export_tokens_button.pack(padx=5, pady=2, fill=tk.X)

        # === DOLNA CZĘŚĆ: Panel informacyjny ===
        self.lower_frame = tk.Frame(self.main_paned, bg="darkolivegreen")
        # Dolny panel pokazuje tylko informacje o aktywnym heksie, więc trzymamy go kompaktowo
        self.main_paned.add(self.lower_frame, minsize=160, stretch="never")

        # === PANEL INFORMACYJNY ===
        self.build_info_panel_in_frame(self.lower_frame)
        self.root.update_idletasks()
        try:
            self.main_paned.paneconfigure(self.lower_frame, height=200)
        except Exception:
            pass

        # === CANVAS MAPY ===
        self.build_map_canvas()

    def open_map_configuration_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Konfiguracja mapy")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="darkolivegreen")
        dialog.resizable(False, False)

        current_cols = self.config.get("grid_cols", 56)
        current_rows = self.config.get("grid_rows", 40)
        current_hex = self.hex_size

        cols_var = tk.IntVar(value=current_cols)
        rows_var = tk.IntVar(value=current_rows)
        hex_var = tk.IntVar(value=current_hex)
        export_var = tk.BooleanVar(value=True)
        backup_var = tk.BooleanVar(value=True)

        main_frame = tk.Frame(dialog, bg="darkolivegreen", padx=12, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        fields = tk.Frame(main_frame, bg="darkolivegreen")
        fields.pack(fill=tk.X)

        def build_spinbox(parent, label_text, var, limits):
            row = tk.Frame(parent, bg="darkolivegreen")
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label_text, bg="darkolivegreen", fg="white", width=20, anchor="w").pack(side=tk.LEFT)
            spin = tk.Spinbox(
                row,
                from_=limits[0],
                to=limits[1],
                textvariable=var,
                width=6,
                justify="right"
            )
            spin.pack(side=tk.LEFT)
            return spin

        build_spinbox(fields, "Szerokość (kolumny)", cols_var, self.size_hard_limits["cols"])
        build_spinbox(fields, "Wysokość (wiersze)", rows_var, self.size_hard_limits["rows"])
        build_spinbox(fields, "Rozmiar heksa", hex_var, self.size_hard_limits["hex_size"])

        preset_frame = tk.Frame(main_frame, bg="darkolivegreen")
        preset_frame.pack(fill=tk.X, pady=(6, 0))

        def apply_preset(cols, rows, size):
            cols_var.set(cols)
            rows_var.set(rows)
            hex_var.set(size)

        tk.Label(preset_frame, text="Presety:", bg="darkolivegreen", fg="yellow").pack(side=tk.LEFT)
        tk.Button(preset_frame, text="Potyczka", command=lambda: apply_preset(30, 20, 28)).pack(side=tk.LEFT, padx=2)
        tk.Button(preset_frame, text="Standard", command=lambda: apply_preset(56, 40, 30)).pack(side=tk.LEFT, padx=2)
        tk.Button(preset_frame, text="Kampania", command=lambda: apply_preset(120, 80, 32)).pack(side=tk.LEFT, padx=2)

        flags_frame = tk.Frame(main_frame, bg="darkolivegreen")
        flags_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Checkbutton(flags_frame, text="Eksportuj startowe żetony", variable=export_var, bg="darkolivegreen", fg="white", selectcolor="darkolivegreen").pack(anchor="w")
        tk.Checkbutton(flags_frame, text="Zrób kopię mapy przed zmianą", variable=backup_var, bg="darkolivegreen", fg="white", selectcolor="darkolivegreen").pack(anchor="w")

        info_var = tk.StringVar(value="")
        warning_var = tk.StringVar(value="")

        info_label = tk.Label(main_frame, textvariable=info_var, bg="darkolivegreen", fg="white", justify="left", wraplength=340)
        info_label.pack(fill=tk.X, pady=(10, 4))
        warning_label = tk.Label(main_frame, textvariable=warning_var, bg="darkolivegreen", fg="orange", justify="left", wraplength=340)
        warning_label.pack(fill=tk.X)

        buttons = tk.Frame(main_frame, bg="darkolivegreen")
        buttons.pack(fill=tk.X, pady=(12, 0))
        tk.Button(buttons, text="Anuluj", command=dialog.destroy, bg="saddlebrown", fg="white", width=10).pack(side=tk.RIGHT, padx=4)

        def update_preview():
            try:
                new_cols = int(cols_var.get())
                new_rows = int(rows_var.get())
                new_hex = int(hex_var.get())
            except (tk.TclError, ValueError):
                info_var.set("Nieprawidłowe wartości.")
                warning_var.set("")
                return

            preview = self._calculate_config_change_effects(new_cols, new_rows, new_hex)
            if preview["errors"]:
                info_var.set("Błędy: " + "; ".join(preview["errors"]))
                warning_var.set("")
                return
            info_var.set(preview["summary"])
            warning_var.set(preview["warning"])  # może być pusty

        def apply_changes():
            try:
                new_cols = int(cols_var.get())
                new_rows = int(rows_var.get())
                new_hex = int(hex_var.get())
            except (tk.TclError, ValueError):
                messagebox.showerror("Błąd", "Podano nieprawidłowe wartości.")
                return
            result = self._apply_map_configuration(
                new_cols,
                new_rows,
                new_hex,
                export_tokens=export_var.get(),
                make_backup=backup_var.get()
            )
            if result:
                messagebox.showinfo("Konfiguracja mapy", result)
                dialog.destroy()

        tk.Button(buttons, text="Zastosuj", command=apply_changes, bg="forestgreen", fg="white", width=10).pack(side=tk.RIGHT)

        cols_var.trace_add("write", lambda *_: update_preview())
        rows_var.trace_add("write", lambda *_: update_preview())
        hex_var.trace_add("write", lambda *_: update_preview())

        update_preview()

    def _calculate_config_change_effects(self, cols: int, rows: int, hex_size: int) -> dict:
        errors = []
        warnings = []

        min_cols, max_cols = self.size_hard_limits["cols"]
        min_rows, max_rows = self.size_hard_limits["rows"]
        min_hex, max_hex = self.size_hard_limits["hex_size"]

        if not (min_cols <= cols <= max_cols):
            errors.append(f"Kolumny poza zakresem ({min_cols}-{max_cols}).")
        if not (min_rows <= rows <= max_rows):
            errors.append(f"Wiersze poza zakresem ({min_rows}-{max_rows}).")
        if not (min_hex <= hex_size <= max_hex):
            errors.append(f"Rozmiar heksa poza zakresem ({min_hex}-{max_hex}).")

        soft_cols = self.size_soft_limits["cols"]
        soft_rows = self.size_soft_limits["rows"]
        soft_hex = self.size_soft_limits["hex_size"]

        if cols > soft_cols or rows > soft_rows:
            warnings.append("Duża siatka może wydłużyć ładowanie i ruch AI.")
        if hex_size > soft_hex:
            warnings.append("Duże heksy mogą nie zmieścić się na ekranie.")

        allowed_hexes = self._build_allowed_hex_ids(cols, rows)
        current_hexes = set(self.hex_data.keys())
        removed_hexes = current_hexes - allowed_hexes

        tokens_removed = sum(1 for hid in removed_hexes if self.hex_data.get(hid, {}).get("token"))
        key_points_removed = sum(1 for hid in self.key_points if hid not in allowed_hexes)
        spawn_removed = 0
        for nation, hex_list in self.spawn_points.items():
            spawn_removed += sum(1 for hid in hex_list if hid not in allowed_hexes)

        min_move_mod = min(value.get("move_mod", 0) for value in TERRAIN_TYPES.values())
        estimated_range = max(6, int(12 / max(1, 1 + min_move_mod)))

        required_width, required_height = self._estimate_canvas_size(cols, rows, hex_size)
        current_width = getattr(self, "world_width", required_width)
        current_height = getattr(self, "world_height", required_height)
        if required_width > current_width or required_height > current_height:
            warnings.append("Aktualne tło jest za małe – zostanie zastąpione jednolitym tłem.")

        total_hexes = len(allowed_hexes)
        summary_lines = [
            f"Nowa siatka: {cols} × {rows} ({total_hexes} heksów).",
            f"Szacowany zasięg kawalerii przy płaskim terenie: ok. {estimated_range} heksów.",
        ]
        if removed_hexes:
            summary_lines.append(
                f"Do wyzerowania: {len(removed_hexes)} heksów (żetony: {tokens_removed}, spawn: {spawn_removed}, key pointy: {key_points_removed})."
            )
        else:
            summary_lines.append("Brak utraty obecnych danych.")
        if cols == self.config.get("grid_cols") and rows == self.config.get("grid_rows") and hex_size == self.hex_size:
            summary_lines.append("Parametry bez zmian.")

        return {
            "summary": "\n".join(summary_lines),
            "warning": "\n".join(warnings),
            "errors": errors,
            "removed": {
                "hexes": len(removed_hexes),
                "tokens": tokens_removed,
                "spawn": spawn_removed,
                "key_points": key_points_removed,
            },
            "allowed_hexes": allowed_hexes,
            "canvas_size": (required_width, required_height),
        }

    def _estimate_canvas_size(self, cols: int, rows: int, hex_size: int) -> tuple[int, int]:
        horizontal_spacing = 1.5 * hex_size
        width = int(hex_size * 2 + max(0, cols - 1) * horizontal_spacing + hex_size)
        hex_height = math.sqrt(3) * hex_size
        height = int((math.sqrt(3) / 2) * hex_size + rows * hex_height + hex_size)
        return max(200, width), max(200, height)

    def _build_allowed_hex_ids(self, cols: int, rows: int) -> set[str]:
        allowed = set()
        for col in range(max(0, cols)):
            for row in range(max(0, rows)):
                q = col
                r = row - (col // 2)
                allowed.add(f"{q},{r}")
        return allowed

    def _apply_background_metadata(self, meta: dict | None) -> None:
        if not meta:
            if self.map_image_path:
                self.background_info = {
                    "type": "image",
                    "path": to_rel(str(self.map_image_path))
                }
            else:
                self.background_info = {
                    "type": "solid",
                    "color": list(SOLID_BACKGROUND_COLOR)
                }
            return

        bg_type = meta.get("type")
        if bg_type == "image":
            raw_path = meta.get("path")
            resolved: Path | str | None
            if raw_path:
                if os.path.isabs(raw_path):
                    resolved = Path(raw_path)
                else:
                    resolved = ASSET_ROOT / raw_path
            else:
                resolved = None
            if resolved and Path(resolved).exists():
                abs_path = str(Path(resolved))
                self.map_image_path = abs_path
                self.config["map_image_path"] = abs_path
                self.background_info = {
                    "type": "image",
                    "path": to_rel(str(resolved))
                }
            else:
                self.map_image_path = None
                self.config["map_image_path"] = None
                self.background_info = {
                    "type": "solid",
                    "color": list(SOLID_BACKGROUND_COLOR)
                }
        elif bg_type == "solid":
            color = meta.get("color", list(SOLID_BACKGROUND_COLOR))
            if isinstance(color, tuple):
                color = list(color)
            self.background_info = {
                "type": "solid",
                "color": color
            }
            self.map_image_path = None
            self.config["map_image_path"] = None
        else:
            if self.map_image_path:
                self.background_info = {
                    "type": "image",
                    "path": to_rel(str(self.map_image_path))
                }
            else:
                self.background_info = {
                    "type": "solid",
                    "color": list(SOLID_BACKGROUND_COLOR)
                }

        width = meta.get("width") or meta.get("canvas_width")
        height = meta.get("height") or meta.get("canvas_height")
        if width and height:
            self.world_width, self.world_height = int(width), int(height)

    def _serialize_background_info(self) -> dict:
        info = dict(getattr(self, "background_info", {}))
        if not info:
            return {}
        if info.get("type") == "image":
            path_to_store = None
            if self.map_image_path:
                path_to_store = to_rel(str(self.map_image_path))
            elif info.get("path"):
                path_to_store = info["path"]
            if path_to_store:
                info["path"] = path_to_store
            else:
                info.pop("path", None)
        if info.get("type") == "solid":
            color = info.get("color", list(SOLID_BACKGROUND_COLOR))
            if isinstance(color, tuple):
                color = list(color)
            info["color"] = color
        width = getattr(self, "world_width", None)
        height = getattr(self, "world_height", None)
        if width:
            info["width"] = int(width)
        if height:
            info["height"] = int(height)
        return info

    def _apply_map_configuration(self, cols: int, rows: int, hex_size: int, *, export_tokens: bool, make_backup: bool) -> str | None:
        preview = self._calculate_config_change_effects(cols, rows, hex_size)
        if preview["errors"]:
            messagebox.showerror("Błąd konfiguracji", "\n".join(preview["errors"]))
            return None

        if cols == self.config.get("grid_cols") and rows == self.config.get("grid_rows") and hex_size == self.hex_size:
            return "Parametry mapy pozostają bez zmian."

        removed = preview["removed"]
        if any(removed.values()):
            if not messagebox.askyesno(
                "Potwierdzenie",
                (
                    "Zmiana rozmiaru zresetuje dane mapy.\n"
                    f"Wyzerowane zostaną wpisy dla {removed['hexes']} heksów, {removed['tokens']} żetonów, "
                    f"{removed['spawn']} punktów spawn i {removed['key_points']} punktów kluczowych. Kontynuować?"
                ),
            ):
                return None

        backup_path = None
        if make_backup:
            backup_path = self._create_map_backup()

        previous_auto_save = self.auto_save_enabled
        self.auto_save_enabled = False

        try:
            self.config["grid_cols"] = cols
            self.config["grid_rows"] = rows
            self.hex_size = hex_size

            self.hex_data = {}
            self.key_points = {}
            self.spawn_points = {}
            self.hex_tokens.clear()
            self.selected_hex = None

            required_width, required_height = preview["canvas_size"]
            self.bg_image = Image.new("RGB", (required_width, required_height), SOLID_BACKGROUND_COLOR)
            self.photo_bg = ImageTk.PhotoImage(self.bg_image)
            self.world_width, self.world_height = self.bg_image.size
            self.map_image_path = None
            self.canvas.config(scrollregion=(0, 0, self.world_width, self.world_height))
            self.config["map_image_path"] = None
            self.background_info = {
                "type": "solid",
                "color": list(SOLID_BACKGROUND_COLOR),
                "width": self.world_width,
                "height": self.world_height
            }

            if hasattr(self, "hex_info_label"):
                self.hex_info_label.config(text="Heks: brak")
            if hasattr(self, "terrain_info_label"):
                self.terrain_info_label.config(text="Teren: brak")
            if hasattr(self, "token_info_label"):
                self.token_info_label.config(text="Żeton: brak")
            if hasattr(self, "key_point_info_label"):
                self.key_point_info_label.config(text="")
            if hasattr(self, "spawn_point_info_label"):
                self.spawn_point_info_label.config(text="")
            self.canvas.delete("hover_zoom")

            self.draw_grid()
            self.save_data()
            if export_tokens:
                self.export_start_tokens(show_message=False)
            self.force_refresh_palette()
        finally:
            self.auto_save_enabled = previous_auto_save

        result_lines = [f"Zastosowano: {cols} × {rows}, hex {hex_size}."]
        if backup_path:
            result_lines.append(f"Backup zapisany jako: {backup_path.name}")
        result_lines.append("Mapa została zresetowana do domyślnej siatki.")
        return "\n".join(result_lines)

    def _create_map_backup(self) -> Path | None:
        source = Path(self.current_working_file)
        if not source.exists():
            return None
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = DATA_ROOT / f"map_data.json.bak-{timestamp}"
        try:
            shutil.copy2(source, backup_path)
        except Exception as exc:
            messagebox.showwarning("Backup", f"Nie udało się utworzyć kopii zapasowej: {exc}")
            return None
        self._trim_old_backups()
        return backup_path

    def _trim_old_backups(self, keep: int = 5) -> None:
        backups = sorted(DATA_ROOT.glob("map_data.json.bak-*"), reverse=True)
        for obsolete in backups[keep:]:
            try:
                obsolete.unlink()
            except OSError:
                pass

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
        self.control_panel_frame = tk.Frame(parent_frame, bg="darkolivegreen", relief=tk.RIDGE, bd=3, height=160)
        # Panel z informacjami siedzi na dole i nie rozciąga się w pionie
        self.control_panel_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False, padx=2, pady=2)
        
        tk.Label(self.control_panel_frame, text="Informacje o heksie", 
                 bg="darkolivegreen", fg="white", font=("Arial", 10, "bold")).pack(pady=2)
        
        # Kontener na informacje podstawowe
        basic_info_frame = tk.Frame(self.control_panel_frame, bg="darkolivegreen")
        basic_info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        self.hex_info_label = tk.Label(basic_info_frame, text="Heks: brak", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.hex_info_label.pack(anchor="w", pady=1)
        
        self.terrain_info_label = tk.Label(basic_info_frame, text="Teren: brak", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.terrain_info_label.pack(anchor="w", pady=1)
        
        self.token_info_label = tk.Label(basic_info_frame, text="Żeton: brak", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.token_info_label.pack(anchor="w", pady=1)

        self.texture_info_label = tk.Label(basic_info_frame, text="Tekstura: domyślna", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.texture_info_label.pack(anchor="w", pady=1)

        tools_frame = tk.Frame(self.control_panel_frame, bg="darkolivegreen")
        tools_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(6, 2))

        self.edit_texture_button = tk.Button(
            tools_frame,
            text="🎨 Edytuj wygląd heksa",
            command=self.open_selected_hex_texture_editor,
            bg="saddlebrown",
            fg="white",
            activebackground="saddlebrown",
            activeforeground="white"
        )
        self.edit_texture_button.pack(fill=tk.X)
        self.edit_texture_button.config(state=tk.DISABLED)

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

    def _scroll_upper_panel(self, event):
        if not hasattr(self, "upper_canvas"):
            return
        widget = getattr(event, "widget", None)
        if widget is getattr(self, "tokens_canvas", None) or widget is getattr(self, "token_palette_frame", None):
            return
        step = 0
        if hasattr(event, "delta") and event.delta:
            step = -1 if event.delta > 0 else 1
        elif getattr(event, "num", None) in (4, 5):
            step = -1 if event.num == 4 else 1
        if step:
            self.upper_canvas.yview_scroll(step, "units")
            return "break"

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
            self.background_info = {
                "type": "image",
                "path": to_rel(str(file_path))
            }
            self.load_map_image()
            messagebox.showinfo("Sukces", "Wybrano nową domyślną mapę.")
        else:
            messagebox.showinfo("Anulowano", "Nie wybrano nowej mapy.")

    def load_map_image(self):
        'Wczytuje obraz mapy jako tło i ustawia rozmiary.'
        bg_meta = getattr(self, "background_info", {})
        bg_type = bg_meta.get("type")

        if bg_type == "solid":
            color = tuple(bg_meta.get("color", list(SOLID_BACKGROUND_COLOR)))
            width = bg_meta.get("width") or getattr(self, "world_width", None)
            height = bg_meta.get("height") or getattr(self, "world_height", None)
            if not width or not height:
                width, height = self._estimate_canvas_size(
                    self.config.get("grid_cols"),
                    self.config.get("grid_rows"),
                    self.hex_size
                )
            self.world_width, self.world_height = int(width), int(height)
            self.bg_image = Image.new("RGB", (self.world_width, self.world_height), color)
            self.photo_bg = ImageTk.PhotoImage(self.bg_image)
            self.canvas.config(scrollregion=(0, 0, self.world_width, self.world_height))
            self.background_info = {
                "type": "solid",
                "color": list(color),
                "width": self.world_width,
                "height": self.world_height
            }
            self.draw_grid()
            return

        path_to_load = self.map_image_path
        if not path_to_load:
            raw_path = bg_meta.get("path")
            if raw_path:
                path_to_load = raw_path if os.path.isabs(raw_path) else ASSET_ROOT / raw_path

        try:
            if not path_to_load:
                raise FileNotFoundError("Brak ścieżki tła mapy")
            self.bg_image = Image.open(path_to_load).convert("RGB")
            self.map_image_path = str(path_to_load)
        except Exception as e:
            print(f"⚠️  Nie udało się załadować tła mapy: {e}")
            width, height = self._estimate_canvas_size(
                self.config.get("grid_cols"),
                self.config.get("grid_rows"),
                self.hex_size
            )
            self.world_width, self.world_height = width, height
            self.bg_image = Image.new("RGB", (width, height), SOLID_BACKGROUND_COLOR)
            self.photo_bg = ImageTk.PhotoImage(self.bg_image)
            self.canvas.config(scrollregion=(0, 0, width, height))
            self.background_info = {
                "type": "solid",
                "color": list(SOLID_BACKGROUND_COLOR),
                "width": width,
                "height": height
            }
            self.map_image_path = None
            self.config["map_image_path"] = None
            self.draw_grid()
            return

        self.world_width, self.world_height = self.bg_image.size
        self.photo_bg = ImageTk.PhotoImage(self.bg_image)
        # Ustaw obszar przewijania
        self.canvas.config(scrollregion=(0, 0, self.world_width, self.world_height))
        self.config["map_image_path"] = self.map_image_path
        self.background_info = {
            "type": "image",
            "path": to_rel(str(self.map_image_path)),
            "width": self.world_width,
            "height": self.world_height
        }
        # Rysuj ponownie siatkę
        self.draw_grid()

    def draw_grid(self):
        """Rysuje siatkę heksów i aktualizuje wyświetlane żetony."""
        self.canvas.delete("all")
        if getattr(self, "world_width", None) and getattr(self, "world_height", None):
            self.canvas.config(scrollregion=(0, 0, self.world_width, self.world_height))
        if not hasattr(self, 'photo_bg'):
            self.photo_bg = ImageTk.PhotoImage(Image.new("RGB", (1, 1), (255, 255, 255)))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_bg)
        self.hex_centers = {}
        s = self.hex_size
        hex_height = math.sqrt(3) * s
        horizontal_spacing = 1.5 * s
        grid_cols = self.config.get("grid_cols")
        grid_rows = self.config.get("grid_rows")
        self.canvas.image_store = []

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
                texture_rel = terrain.get("texture")
                if texture_rel:
                    texture_image = self._get_hex_texture_image(texture_rel)
                    if texture_image:
                        self.canvas.create_image(center_x, center_y, image=texture_image)
                        self.canvas.image_store.append(texture_image)
                self.draw_hex(hex_id, center_x, center_y, s, terrain)

    # Rysowanie żetonów na mapie
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

    def draw_hex(self, hex_id, center_x, center_y, s, terrain=None):
        'Rysuje pojedynczy heksagon na canvasie wraz z tekstem modyfikatorów.'
        points = get_hex_vertices(center_x, center_y, s)
        self.canvas.create_polygon(points, outline="red", fill="", width=2, tags=hex_id)        # usuwamy poprzedni tekst
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
                tags=f"tekst_{hex_id}"
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
            outline=outline, width=3, tags=f"spawn_{nation}_{hex_id}"
        )
        self.canvas.create_text(
            cx, cy + self.hex_size * 0.60,
            text=letter,
            fill=outline,
            font=("Arial", 10, "bold"),
            tags=f"spawn_{nation}_{hex_id}"
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
            tags=f"key_point_{key_type}_{hex_id}"
        )
        
        # Rysuj skrót typu
        self.canvas.create_text(
            cx, cy,
            text=letter,
            fill="black",
            font=("Arial", 9, "bold"),
            tags=f"key_point_{key_type}_{hex_id}"
        )
        
        # Rysuj wartość pod kółkiem
        self.canvas.create_text(
            cx, cy + self.hex_size * 0.65,
            text=str(value),
            fill=outline,
            font=("Arial", 8, "bold"),
            tags=f"key_point_{key_type}_{hex_id}"
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
            self.edit_texture_button.config(state=tk.DISABLED)
            self.texture_info_label.config(text="Tekstura: domyślna")

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

    def open_selected_hex_texture_editor(self):
        if not getattr(self, "selected_hex", None):
            messagebox.showinfo("Brak wyboru", "Najpierw wybierz heks na mapie.")
            return
        self.open_hex_texture_editor(self.selected_hex)

    def open_hex_texture_editor(self, hex_id: str):
        # Zamknij poprzednie okno jeśli jeszcze istnieje
        if hasattr(self, "_texture_editor_window") and self._texture_editor_window:
            try:
                self._texture_editor_window.destroy()
            except tk.TclError:
                pass

        terrain = self.hex_data.setdefault(hex_id, {
            "terrain_key": "teren_płaski",
            "move_mod": 0,
            "defense_mod": 0,
        })

        pixels = self._load_hex_texture_pixels(terrain.get("texture"))

        editor = tk.Toplevel(self.root)
        editor.title(f"Edytor tekstury heksa {hex_id}")
        editor.configure(bg="darkolivegreen")
        editor.transient(self.root)
        editor.grab_set()
        editor.geometry("820x520")
        try:
            editor.state("zoomed")
        except Exception:
            try:
                editor.attributes("-zoomed", True)
            except Exception:
                pass

        editor.grid_rowconfigure(0, weight=0)
        editor.grid_rowconfigure(1, weight=1)
        editor.grid_columnconfigure(0, weight=1)
        editor.grid_columnconfigure(1, weight=0, minsize=360)

        self._texture_editor_window = editor

        grid_size = HEX_TEXTURE_GRID_SIZE
        canvas_target_size = 480
        cell_size = max(14, min(28, canvas_target_size // grid_size))
        if cell_size <= 0:
            cell_size = 14
        canvas_size = grid_size * cell_size
        if CONTEXT_CANVAS_SCALE <= 1.0:
            extra_cells_per_side = 0
        else:
            extra_cells_per_side = max(1, int(math.ceil(((CONTEXT_CANVAS_SCALE - 1.0) * grid_size) / 2.0)))
        context_grid_size = grid_size + extra_cells_per_side * 2
        context_canvas_size = context_grid_size * cell_size
        grid_offset = extra_cells_per_side * cell_size

        preview_wrapper = tk.Frame(editor, bg="#111111")
        preview_wrapper.grid(row=0, column=0, rowspan=2, padx=12, pady=12, sticky="nsew")
        preview_wrapper.grid_rowconfigure(0, weight=1)
        preview_wrapper.grid_columnconfigure(0, weight=1)

        preview_canvas = tk.Canvas(
            preview_wrapper,
            width=context_canvas_size,
            height=context_canvas_size,
            bg="#111111",
            highlightthickness=0
        )
        preview_canvas.place(relx=0.5, rely=0.5, anchor="center")

        hex_mask = self._precompute_hex_mask()
        center = grid_size / 2.0
        mask_vertices = getattr(self, "_hex_texture_vertices", {}).get(grid_size)
        if not mask_vertices:
            radius = grid_size / 2.0 - 0.5
            mask_vertices = get_hex_vertices(center, center, radius)

        mask_radius_units = grid_size / 2.0 - 0.5
        mask_radius_px = mask_radius_units * cell_size
        q, r = map(int, hex_id.split(","))
        neighbor_dirs = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        centers = getattr(self, "hex_centers", {})
        main_center = centers.get(hex_id)
        units_scale = (mask_radius_units / self.hex_size) if (main_center and self.hex_size) else None

        edge_definitions = [
            {"key": "E", "label": "Prawa krawędź", "direction": (1, 0)},
            {"key": "NE", "label": "Prawa górna krawędź", "direction": (1, -1)},
            {"key": "NW", "label": "Lewa górna krawędź", "direction": (0, -1)},
            {"key": "W", "label": "Lewa krawędź", "direction": (-1, 0)},
            {"key": "SW", "label": "Lewa dolna krawędź", "direction": (-1, 1)},
            {"key": "SE", "label": "Prawa dolna krawędź", "direction": (0, 1)},
        ]

        def canvas_offset_for_hex(target_hex_id: str, dq: int, dr: int) -> tuple[float, float]:
            if units_scale and target_hex_id in centers and main_center:
                target_center = centers[target_hex_id]
                dx_units = (target_center[0] - main_center[0]) * units_scale
                dy_units = (target_center[1] - main_center[1]) * units_scale
            else:
                dx_units = (3.0 / 2.0) * dq * mask_radius_units
                dy_units = (math.sqrt(3) * (dr + dq / 2.0)) * mask_radius_units
            dx_cells = int(round(dx_units))
            dy_cells = int(round(dy_units))
            return dx_cells * cell_size, dy_cells * cell_size

        def dilate_mask(base_mask: list[list[bool]], iterations: int) -> list[list[bool]]:
            current = [row[:] for row in base_mask]
            if iterations <= 0:
                return current
            for _ in range(iterations):
                expanded = [row[:] for row in current]
                for row in range(grid_size):
                    for col in range(grid_size):
                        if expanded[row][col] or not hex_mask[row][col]:
                            continue
                        for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            n_row = row + d_row
                            n_col = col + d_col
                            if 0 <= n_row < grid_size and 0 <= n_col < grid_size and current[n_row][n_col]:
                                expanded[row][col] = True
                                break
                current = expanded
            return current

        def build_edge_mode_data() -> dict[str, dict]:
            data: dict[str, dict] = {}
            for entry in edge_definitions:
                dq, dr = entry["direction"]
                neighbor_id = f"{q + dq},{r + dr}"
                enabled = neighbor_id in centers
                edge_data = {
                    "key": entry["key"],
                    "label": entry["label"],
                    "direction": (dq, dr),
                    "neighbor_id": neighbor_id,
                    "enabled": enabled,
                    "dx_cells": 0,
                    "dy_cells": 0,
                    "band_mask": [[False for _ in range(grid_size)] for _ in range(grid_size)],
                    "neighbor_pixels": None,
                    "neighbor_texture_rel": None,
                    "neighbor_mask": hex_mask,
                    "dirty": False,
                }
                if not enabled:
                    data[entry["key"]] = edge_data
                    continue
                dx_canvas, dy_canvas = canvas_offset_for_hex(neighbor_id, dq, dr)
                dx_cells = int(round(dx_canvas / cell_size))
                dy_cells = int(round(dy_canvas / cell_size))
                edge_data["dx_cells"] = dx_cells
                edge_data["dy_cells"] = dy_cells
                base_band = [[False for _ in range(grid_size)] for _ in range(grid_size)]
                for row in range(grid_size):
                    if not any(hex_mask[row]):
                        continue
                    for col in range(grid_size):
                        if not hex_mask[row][col]:
                            continue
                        n_row = row - dy_cells
                        n_col = col - dx_cells
                        if 0 <= n_row < grid_size and 0 <= n_col < grid_size and hex_mask[n_row][n_col]:
                            base_band[row][col] = True
                iterations = max(0, EDGE_BAND_CELLS - 1)
                edge_data["band_mask"] = dilate_mask(base_band, iterations)
                neighbor_terrain = self.hex_data.get(neighbor_id)
                neighbor_pixels = self._load_hex_texture_pixels(neighbor_terrain.get("texture") if neighbor_terrain else None)
                edge_data["neighbor_pixels"] = neighbor_pixels
                edge_data["neighbor_texture_rel"] = neighbor_terrain.get("texture") if neighbor_terrain else None
                has_band = any(any(row) for row in edge_data["band_mask"])
                edge_data["enabled"] = enabled and has_band
                data[entry["key"]] = edge_data
            return data

        edge_mode_data = build_edge_mode_data()

        def pixels_to_image(pixel_grid: list[list[str | None]]) -> Image.Image:
            img = Image.new("RGBA", (grid_size, grid_size), (0, 0, 0, 0))
            for row in range(grid_size):
                for col in range(grid_size):
                    color = pixel_grid[row][col]
                    if color:
                        r_c = int(color[1:3], 16)
                        g_c = int(color[3:5], 16)
                        b_c = int(color[5:7], 16)
                        img.putpixel((col, row), (r_c, g_c, b_c, 255))
            return img

        def blank_pixel_grid() -> list[list[str | None]]:
            return [[None for _ in range(grid_size)] for _ in range(grid_size)]

        def hex_to_rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
            return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), alpha

        def create_stamp_overlay_image(pixel_grid: list[list[str | None]], alpha: int = 180) -> Image.Image:
            base = pixels_to_image(pixel_grid).resize((canvas_size, canvas_size), Image.NEAREST)
            if alpha >= 255:
                return base
            overlay = base.copy()
            overlay_data = []
            for r, g, b, a in overlay.getdata():
                if a == 0:
                    overlay_data.append((r, g, b, 0))
                else:
                    overlay_data.append((r, g, b, alpha))
            overlay.putdata(overlay_data)
            return overlay

        def build_preset_preview_photo(pixel_grid: list[list[str | None]]) -> ImageTk.PhotoImage:
            mini = pixels_to_image(pixel_grid)
            preview_bg = Image.new("RGBA", mini.size, (36, 48, 32, 255))
            preview_bg.alpha_composite(mini)
            preview = preview_bg.resize((96, 96), Image.NEAREST)
            return ImageTk.PhotoImage(preview)

        def set_pixel(grid: list[list[str | None]], row: int, col: int, color: str) -> None:
            if 0 <= row < grid_size and 0 <= col < grid_size and hex_mask[row][col]:
                grid[row][col] = color

        def set_pixel_if_empty(grid: list[list[str | None]], row: int, col: int, color: str) -> None:
            if 0 <= row < grid_size and 0 <= col < grid_size and hex_mask[row][col] and grid[row][col] is None:
                grid[row][col] = color

        def paint_disc(grid: list[list[str | None]], center_row: int, center_col: int, radius: int,
                       palette: list[str]) -> None:
            if radius <= 0:
                return
            palette_len = len(palette)
            for row in range(center_row - radius, center_row + radius + 1):
                if row < 0 or row >= grid_size:
                    continue
                for col in range(center_col - radius, center_col + radius + 1):
                    if col < 0 or col >= grid_size or not hex_mask[row][col]:
                        continue
                    dy = row - center_row
                    dx = col - center_col
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= radius + 0.35:
                        t = dist / max(1.0, radius)
                        idx = min(palette_len - 1, int(t * (palette_len - 1)))
                        set_pixel(grid, row, col, palette[idx])

        def paint_soft_patch(grid: list[list[str | None]], center_row: int, center_col: int,
                             radius_row: int, radius_col: int, palette: list[str]) -> None:
            palette_len = len(palette)
            for row in range(center_row - radius_row, center_row + radius_row + 1):
                if row < 0 or row >= grid_size:
                    continue
                for col in range(center_col - radius_col, center_col + radius_col + 1):
                    if col < 0 or col >= grid_size or not hex_mask[row][col]:
                        continue
                    dy = (row - center_row) / max(1.0, radius_row)
                    dx = (col - center_col) / max(1.0, radius_col)
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= 1.0:
                        idx = min(palette_len - 1, int(dist * (palette_len - 1)))
                        set_pixel_if_empty(grid, row, col, palette[idx])

        def draw_polyline(grid: list[list[str | None]], points: list[tuple[int, int]], width: int,
                          palette: list[str], overwrite: bool = True) -> None:
            if len(points) < 2:
                return
            palette_len = len(palette)
            for idx in range(len(points) - 1):
                r0, c0 = points[idx]
                r1, c1 = points[idx + 1]
                steps = max(abs(r1 - r0), abs(c1 - c0)) * 4
                if steps <= 0:
                    steps = 1
                for step in range(steps + 1):
                    t = step / steps
                    row = int(round(r0 + (r1 - r0) * t))
                    col = int(round(c0 + (c1 - c0) * t))
                    for dy in range(-width, width + 1):
                        target_row = row + dy
                        if target_row < 0 or target_row >= grid_size:
                            continue
                        for dx in range(-width, width + 1):
                            target_col = col + dx
                            if target_col < 0 or target_col >= grid_size or not hex_mask[target_row][target_col]:
                                continue
                            dist = math.sqrt(dx * dx + dy * dy)
                            if dist <= width + 0.35:
                                shade = dist / max(1.0, width)
                                color_idx = min(palette_len - 1, int(shade * (palette_len - 1)))
                                if overwrite or grid[target_row][target_col] is None:
                                    set_pixel(grid, target_row, target_col, palette[color_idx])

        def draw_dashed_line(grid: list[list[str | None]], points: list[tuple[int, int]], spacing: float,
                             color: str) -> None:
            if len(points) < 2:
                return
            distance_acc = 0.0
            last_row, last_col = points[0]
            for idx in range(len(points) - 1):
                r0, c0 = points[idx]
                r1, c1 = points[idx + 1]
                steps = max(abs(r1 - r0), abs(c1 - c0)) * 4
                if steps <= 0:
                    steps = 1
                for step in range(steps + 1):
                    t = step / steps
                    row = int(round(r0 + (r1 - r0) * t))
                    col = int(round(c0 + (c1 - c0) * t))
                    segment = math.sqrt((row - last_row) ** 2 + (col - last_col) ** 2)
                    distance_acc += segment
                    last_row, last_col = row, col
                    if int(distance_acc / spacing) % 2 == 0:
                        set_pixel(grid, row, col, color)

        def fill_rect(grid: list[list[str | None]], top: int, left: int, height: int, width_rect: int,
                      palette: list[str]) -> None:
            if height <= 0 or width_rect <= 0:
                return
            palette_len = len(palette)
            for row in range(top, top + height):
                if row < 0 or row >= grid_size:
                    continue
                for col in range(left, left + width_rect):
                    if col < 0 or col >= grid_size or not hex_mask[row][col]:
                        continue
                    rel_row = (row - top) / max(1, height - 1)
                    rel_col = (col - left) / max(1, width_rect - 1)
                    weight = max(0.0, min(0.999, rel_row * 0.6 + rel_col * 0.4))
                    idx = min(palette_len - 1, int(weight * (palette_len - 1)))
                    set_pixel(grid, row, col, palette[idx])

        def sprinkle_windows(grid: list[list[str | None]], top: int, left: int, height: int, width_rect: int,
                              color: str, stride: int) -> None:
            for row in range(top, top + height):
                if row < 0 or row >= grid_size:
                    continue
                for col in range(left, left + width_rect):
                    if col < 0 or col >= grid_size or not hex_mask[row][col]:
                        continue
                    if (row + col) % stride == 0:
                        set_pixel(grid, row, col, color)

        def build_forest_presets() -> list[dict]:
            canopy_palette = ["#173220", "#1f4a2f", "#2e663f", "#3f8454", "#58a86c"]
            highlight_palette = ["#6ec57f", "#8bdc99"]
            ground_palette = ["#1f2d22", "#273a2c", "#304736"]
            center_row = grid_size // 2
            center_col = grid_size // 2
            specs = [
                {
                    "id": "forest_grove_small",
                    "label": "Las • zagajnik",
                    "ground": {"offset": (2, 0), "radius_row": 18, "radius_col": 20},
                    "trees": [(-8, -6, 4), (-6, 6, 3), (0, -2, 4), (7, 5, 3)],
                },
                {
                    "id": "forest_dense_cluster",
                    "label": "Las • gęsty klaster",
                    "ground": {"offset": (0, 0), "radius_row": 22, "radius_col": 22},
                    "trees": [(-10, -4, 5), (-2, -8, 4), (-4, 6, 5), (6, -1, 4), (8, 7, 3)],
                },
                {
                    "id": "forest_edge",
                    "label": "Las • skraj",
                    "ground": {"offset": (4, -2), "radius_row": 20, "radius_col": 24},
                    "trees": [(-12, -2, 4), (-6, 5, 4), (2, 8, 4), (10, 2, 3), (4, -6, 3)],
                },
            ]
            presets: list[dict] = []
            for spec in specs:
                grid = blank_pixel_grid()
                ground = spec.get("ground")
                if ground:
                    paint_soft_patch(
                        grid,
                        center_row + ground["offset"][0],
                        center_col + ground["offset"][1],
                        ground["radius_row"],
                        ground["radius_col"],
                        ground_palette,
                    )
                for offset_row, offset_col, radius in spec["trees"]:
                    tree_center_row = center_row + offset_row
                    tree_center_col = center_col + offset_col
                    paint_disc(grid, tree_center_row, tree_center_col, radius, canopy_palette)
                    paint_disc(grid, tree_center_row - 1, tree_center_col - 1, max(1, radius - 2), highlight_palette)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            return presets

        def build_river_presets() -> list[dict]:
            water_palette = ["#17384f", "#20506c", "#2e6d8c", "#3f8fb5", "#55abd4"]
            shoreline_palette = ["#243b32", "#2c4a3b", "#335744", "#3e664f"]
            center_row = grid_size // 2
            center_col = grid_size // 2
            specs = [
                {
                    "id": "river_meander",
                    "label": "Rzeka • meandry",
                    "branches": [
                        [(-26, -18), (-16, -8), (-4, 0), (10, 10), (24, 18)],
                    ],
                    "width": 3,
                },
                {
                    "id": "river_diagonal",
                    "label": "Rzeka • ukośna",
                    "branches": [
                        [(-24, 16), (-10, 6), (6, -4), (24, -14)],
                    ],
                    "width": 3,
                },
                {
                    "id": "river_fork",
                    "label": "Rzeka • rozwidlenie",
                    "branches": [
                        [(-26, -6), (-12, -2), (4, 4), (20, 10)],
                        [(4, 4), (14, -8), (26, -16)],
                    ],
                    "width": 3,
                },
            ]
            presets: list[dict] = []
            for spec in specs:
                grid = blank_pixel_grid()
                for branch in spec["branches"]:
                    absolute_points = [(center_row + r, center_col + c) for r, c in branch]
                    draw_polyline(grid, absolute_points, spec["width"], water_palette, overwrite=True)
                    draw_polyline(grid, absolute_points, spec["width"] + 1, shoreline_palette, overwrite=False)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            return presets

        def build_city_presets() -> list[dict]:
            wall_palette = ["#8f8780", "#a69f98", "#c1bbb5", "#dedad5"]
            roof_palette = ["#b95f40", "#d17d55", "#e69b6f"]
            window_color = "#f2e6c9"
            plaza_palette = ["#5d564d", "#6c655b", "#7a7366"]
            center_row = grid_size // 2
            center_col = grid_size // 2
            specs = [
                {
                    "id": "city_quarters",
                    "label": "Miasto • kwartały",
                    "blocks": [
                        {"top": -10, "left": -14, "height": 12, "width": 10},
                        {"top": -8, "left": 2, "height": 13, "width": 11},
                        {"top": 4, "left": -6, "height": 9, "width": 12},
                    ],
                    "plaza": {"top": -2, "left": -4, "height": 6, "width": 8},
                },
                {
                    "id": "city_riverside",
                    "label": "Miasto • nad rzeką",
                    "blocks": [
                        {"top": -14, "left": -6, "height": 10, "width": 12},
                        {"top": -2, "left": -12, "height": 12, "width": 9},
                        {"top": 6, "left": 0, "height": 10, "width": 11},
                    ],
                    "plaza": {"top": 0, "left": -3, "height": 5, "width": 7},
                },
                {
                    "id": "city_fortified",
                    "label": "Miasto • rynek",
                    "blocks": [
                        {"top": -8, "left": -10, "height": 14, "width": 8},
                        {"top": -8, "left": 2, "height": 14, "width": 8},
                        {"top": -3, "left": -3, "height": 6, "width": 6},
                    ],
                    "plaza": {"top": -4, "left": -2, "height": 8, "width": 4},
                },
            ]
            presets: list[dict] = []
            for spec in specs:
                grid = blank_pixel_grid()
                plaza = spec.get("plaza")
                if plaza:
                    fill_rect(
                        grid,
                        center_row + plaza["top"],
                        center_col + plaza["left"],
                        plaza["height"],
                        plaza["width"],
                        plaza_palette,
                    )
                for block in spec["blocks"]:
                    top = center_row + block["top"]
                    left = center_col + block["left"]
                    fill_rect(grid, top, left, block["height"], block["width"], wall_palette)
                    sprinkle_windows(grid, top + 1, left + 1, max(1, block["height"] - 2), max(1, block["width"] - 2), window_color, 5)
                    roof_height = max(1, block["height"] // 3)
                    fill_rect(grid, top, left, roof_height, block["width"], roof_palette)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            return presets

        def build_bridge_presets() -> list[dict]:
            water_palette = ["#123249", "#1a4f70", "#256e96", "#3c8db9"]
            deck_palette = ["#654d33", "#7a6040", "#937757", "#b3956f"]
            railing_palette = ["#c9c0a9", "#e3d8bd"]
            center_row = grid_size // 2
            center_col = grid_size // 2
            specs = [
                {
                    "id": "bridge_horizontal",
                    "label": "Most • poziomy",
                    "water_patch": {"radius_row": 24, "radius_col": 26, "offset": (0, 0)},
                    "deck": [(-2, -26), (-1, 26)],
                    "railing": [(-4, -26), (-3, 26)],
                    "railing_offset": 4,
                },
            {
                    "id": "bridge_diagonal",
                    "label": "Most • ukośny",
                    "water_patch": {"radius_row": 26, "radius_col": 24, "offset": (2, 0)},
                    "deck": [(-24, -20), (-12, -8), (8, 6), (24, 18)],
                    "railing": [(-24, -20), (-12, -8), (8, 6), (24, 18)],
                    "railing_offset": 3,
                },
            ]
            presets: list[dict] = []
            for spec in specs:
                grid = blank_pixel_grid()
                patch = spec["water_patch"]
                paint_soft_patch(
                    grid,
                    center_row + patch["offset"][0],
                    center_col + patch["offset"][1],
                    patch["radius_row"],
                    patch["radius_col"],
                    water_palette,
                )
                deck_points = [(center_row + r, center_col + c) for r, c in spec["deck"]]
                draw_polyline(grid, deck_points, 2, deck_palette, overwrite=True)
                railing_points = [(center_row + r, center_col + c) for r, c in spec["railing"]]
                draw_polyline(grid, railing_points, spec["railing_offset"], railing_palette, overwrite=False)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            return presets

        def build_road_presets() -> list[dict]:
            asphalt_palette = ["#1f1c18", "#2a2723", "#37322d", "#4a453f"]
            shoulder_palette = ["#514a41", "#6a6257", "#7d7467"]
            center_line_color = "#d9c86a"
            center_row = grid_size // 2
            center_col = grid_size // 2
            specs = [
                {
                    "id": "road_s_curve",
                    "label": "Droga • łuk",
                    "path": [(-26, -12), (-12, -6), (0, 0), (12, 6), (26, 12)],
                    "width": 2,
                },
                {
                    "id": "road_diagonal",
                    "label": "Droga • ukośna",
                    "path": [(-24, 14), (-8, 6), (8, -4), (24, -12)],
                    "width": 2,
                },
                {
                    "id": "road_crossing",
                    "label": "Droga • skrzyżowanie",
                    "path": [(-26, 0), (-14, 0), (0, 0), (16, 0), (26, 0)],
                    "width": 2,
                },
            ]
            presets: list[dict] = []
            for spec in specs:
                grid = blank_pixel_grid()
                path_points = [(center_row + r, center_col + c) for r, c in spec["path"]]
                draw_polyline(grid, path_points, spec["width"], asphalt_palette, overwrite=True)
                draw_polyline(grid, path_points, spec["width"] + 1, shoulder_palette, overwrite=False)
                draw_dashed_line(grid, path_points, spacing=3.5, color=center_line_color)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            return presets

        def build_rail_presets() -> list[dict]:
            rail_palette = ["#3f454d", "#59616a", "#7b858f"]
            sleeper_color = "#6a5139"
            center_row = grid_size // 2
            center_col = grid_size // 2
            specs = [
                {
                    "id": "rail_vertical",
                    "label": "Kolej • pionowa",
                    "rails": [
                        [(-26, -4), (-12, -3), (0, -2), (14, -1), (26, 0)],
                        [(-26, 4), (-12, 3), (0, 2), (14, 1), (26, 0)],
                    ],
                    "ties": {"orientation": "horizontal", "start": -24, "end": 24, "step": 4, "half_width": 5},
                },
                {
                    "id": "rail_diagonal",
                    "label": "Kolej • ukośna",
                    "rails": [
                        [(-24, -18), (-10, -8), (8, 6), (24, 16)],
                        [(-24, -12), (-10, -2), (8, 10), (24, 18)],
                    ],
                    "ties": {"orientation": "diagonal", "start": -18, "end": 18, "step": 5, "length": 6},
                },
            ]
            presets: list[dict] = []
            for spec in specs:
                grid = blank_pixel_grid()
                rail_paths = []
                for rail in spec["rails"]:
                    points = [(center_row + r, center_col + c) for r, c in rail]
                    rail_paths.append(points)
                    draw_polyline(grid, points, 1, rail_palette, overwrite=True)
                ties = spec["ties"]
                if ties["orientation"] == "horizontal":
                    for r_offset in range(ties["start"], ties["end"] + 1, ties["step"]):
                        row = center_row + r_offset
                        for col in range(center_col - ties["half_width"], center_col + ties["half_width"] + 1):
                            set_pixel_if_empty(grid, row, col, sleeper_color)
                else:
                    length = ties.get("length", 6)
                    for diag in range(ties["start"], ties["end"] + 1, ties["step"]):
                        row = center_row + diag
                        col = center_col + diag
                        for offset in range(-length // 2, length // 2 + 1):
                            set_pixel_if_empty(grid, row - offset, col + offset, sleeper_color)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            return presets

        preset_categories = [
            {
                "key": "forest",
                "label": "Lasy",
                "icon": "🌲",
                "builder": build_forest_presets,
            },
            {
                "key": "rivers",
                "label": "Rzeki",
                "icon": "🌊",
                "builder": build_river_presets,
            },
            {
                "key": "cities",
                "label": "Miasta",
                "icon": "🏙️",
                "builder": build_city_presets,
            },
            {
                "key": "bridges",
                "label": "Mosty",
                "icon": "🌉",
                "builder": build_bridge_presets,
            },
            {
                "key": "roads",
                "label": "Drogi",
                "icon": "🛣️",
                "builder": build_road_presets,
            },
            {
                "key": "rail",
                "label": "Kolej",
                "icon": "🚆",
                "builder": build_rail_presets,
            },
        ]

        neighbor_outline_points: list[list[float]] = []
        for dq, dr in neighbor_dirs:
            dx_canvas, dy_canvas = canvas_offset_for_hex(f"{q + dq},{r + dr}", dq, dr)
            poly_points: list[float] = []
            for vx, vy in mask_vertices:
                poly_points.extend((vx * cell_size + grid_offset + dx_canvas,
                                    vy * cell_size + grid_offset + dy_canvas))
            neighbor_outline_points.append(poly_points)

        preview_color_cache: dict[str, list[list[str | None]]] = {}

        def solid_color_pixels(color: str) -> list[list[str | None]]:
            cached = preview_color_cache.get(color)
            if cached is not None:
                return cached
            grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
            for row in range(grid_size):
                for col in range(grid_size):
                    if hex_mask[row][col]:
                        grid[row][col] = color
            preview_color_cache[color] = grid
            return grid

        def get_context_pixels(target_hex_id: str) -> list[list[str | None]] | None:
            if target_hex_id == hex_id:
                return None
            terrain_data = self.hex_data.get(target_hex_id)
            if not terrain_data:
                return None
            texture_rel = terrain_data.get("texture")
            if texture_rel:
                return self._load_hex_texture_pixels(texture_rel)
            terrain_key = terrain_data.get("terrain_key")
            if terrain_key:
                preview_color = TERRAIN_PREVIEW_COLORS.get(terrain_key)
                if preview_color:
                    return solid_color_pixels(preview_color)
            return None

        def build_texture_context() -> Image.Image | None:
            context_img = Image.new("RGBA", (context_canvas_size, context_canvas_size), (0, 0, 0, 0))
            has_any = False
            for dq, dr in neighbor_dirs:
                neighbor_id = f"{q + dq},{r + dr}"
                neighbor_pixels = get_context_pixels(neighbor_id)
                if not neighbor_pixels:
                    continue
                neighbor_img = pixels_to_image(neighbor_pixels)
                if neighbor_img.getbbox() is None:
                    continue
                neighbor_size = max(canvas_size, int(round(canvas_size * NEIGHBOR_PREVIEW_SCALE)))
                neighbor_size = min(context_canvas_size, neighbor_size)
                neighbor_img = neighbor_img.resize((neighbor_size, neighbor_size), Image.NEAREST)
                offset_x, offset_y = canvas_offset_for_hex(neighbor_id, dq, dr)
                center_px = context_canvas_size / 2.0
                paste_x = int(round(center_px + offset_x - neighbor_size / 2.0))
                paste_y = int(round(center_px + offset_y - neighbor_size / 2.0))
                context_img.paste(neighbor_img, (paste_x, paste_y), neighbor_img)
                has_any = True
            return context_img if has_any else None

        context_background = build_texture_context()
        background_photo = ImageTk.PhotoImage(context_background) if context_background else None
        outline_points: list[float] = []
        for vx, vy in mask_vertices:
            outline_points.extend((vx * cell_size + grid_offset, vy * cell_size + grid_offset))

        state = {
            "pixels": pixels,
            "current_color": "#ffffff",
            "eraser": False,
            "mask": hex_mask,
            "background_photo": background_photo,
            "stamp_pixels": None,
            "stamp_overlay_photo": None,
            "stamp_preview_id": None,
            "stamp_offset": (0, 0),
            "preset_preview_refs": [],
            "preset_category_window": None,
            "preset_detail_window": None,
            "preset_categories": preset_categories,
            "edge_mode_active": False,
            "edge_current_key": None,
            "edge_neighbors": edge_mode_data,
            "undo_stack": [],
            "redo_stack": [],
            "history_action_active": False,
            "history_edit_dirty": False,
            "stamp_scale_percent": 100.0,
            "stamp_base_pixels": None,
            "stamp_label": None,
        }

        stamp_status_label = None
        selected_edge_var = tk.StringVar(value="")
        edge_status_label = None
        undo_btn = None
        redo_btn = None
        stamp_scale_label = None
        stamp_scale_widget = None
        stamp_scale_var = tk.DoubleVar(master=editor, value=100.0)

        HISTORY_LIMIT = 40

        def clone_pixels(source: list[list[str | None]]) -> list[list[str | None]]:
            return [row[:] for row in source]

        def capture_snapshot() -> dict:
            neighbors_state: dict[str, dict] = {}
            for key, entry in state["edge_neighbors"].items():
                neighbor_pixels = entry.get("neighbor_pixels")
                neighbors_state[key] = {
                    "pixels": clone_pixels(neighbor_pixels) if neighbor_pixels is not None else None,
                    "dirty": entry.get("dirty", False),
                }
            return {
                "pixels": clone_pixels(state["pixels"]),
                "neighbors": neighbors_state,
            }

        def restore_snapshot(snapshot: dict) -> None:
            state["pixels"] = clone_pixels(snapshot["pixels"])
            for key, neighbor_state in snapshot.get("neighbors", {}).items():
                entry = state["edge_neighbors"].get(key)
                if not entry:
                    continue
                entry["dirty"] = neighbor_state.get("dirty", False)
                pixels_snapshot = neighbor_state.get("pixels")
                entry["neighbor_pixels"] = clone_pixels(pixels_snapshot) if pixels_snapshot is not None else None
            state["history_edit_dirty"] = False

        def update_history_buttons() -> None:
            if undo_btn is not None:
                undo_btn.config(state=tk.NORMAL if state["undo_stack"] else tk.DISABLED)
            if redo_btn is not None:
                redo_btn.config(state=tk.NORMAL if state["redo_stack"] else tk.DISABLED)

        def begin_edit_action() -> None:
            if state["history_action_active"]:
                return
            state["undo_stack"].append(capture_snapshot())
            if len(state["undo_stack"]) > HISTORY_LIMIT:
                state["undo_stack"].pop(0)
            state["redo_stack"].clear()
            state["history_action_active"] = True
            state["history_edit_dirty"] = False
            update_history_buttons()

        def finish_edit_action(event=None) -> None:
            if not state["history_action_active"]:
                return
            if not state["history_edit_dirty"] and state["undo_stack"]:
                state["undo_stack"].pop()
            state["history_action_active"] = False
            state["history_edit_dirty"] = False
            update_history_buttons()

        def undo_action(event=None):
            if state["history_action_active"]:
                finish_edit_action()
            if not state["undo_stack"]:
                return "break"
            snapshot = state["undo_stack"].pop()
            state["redo_stack"].append(capture_snapshot())
            if len(state["redo_stack"]) > HISTORY_LIMIT:
                state["redo_stack"].pop(0)
            restore_snapshot(snapshot)
            draw_grid()
            update_history_buttons()
            return "break"

        def redo_action(event=None):
            if state["history_action_active"]:
                finish_edit_action()
            if not state["redo_stack"]:
                return "break"
            snapshot = state["redo_stack"].pop()
            state["undo_stack"].append(capture_snapshot())
            if len(state["undo_stack"]) > HISTORY_LIMIT:
                state["undo_stack"].pop(0)
            restore_snapshot(snapshot)
            draw_grid()
            update_history_buttons()
            return "break"

        def scale_pixels(source_pixels: list[list[str | None]], percent: float) -> list[list[str | None]]:
            percent = max(10.0, min(100.0, percent))
            target = max(1, min(grid_size, int(round(grid_size * percent / 100.0))))
            if target == grid_size:
                return clone_pixels(source_pixels)
            img = pixels_to_image(source_pixels)
            resized = img.resize((target, target), Image.NEAREST)
            result = blank_pixel_grid()
            offset_row = (grid_size - target) // 2
            offset_col = (grid_size - target) // 2
            for row in range(target):
                for col in range(target):
                    r, g, b, a = resized.getpixel((col, row))
                    if a == 0:
                        continue
                    dst_row = row + offset_row
                    dst_col = col + offset_col
                    if 0 <= dst_row < grid_size and 0 <= dst_col < grid_size and hex_mask[dst_row][dst_col]:
                        result[dst_row][dst_col] = f"#{r:02x}{g:02x}{b:02x}"
            return result

        def refresh_stamp_from_scale() -> None:
            if state.get("stamp_base_pixels") is None:
                return
            percent = state.get("stamp_scale_percent", 100.0)
            scaled = scale_pixels(state["stamp_base_pixels"], percent)
            state["stamp_pixels"] = scaled
            state["stamp_overlay_photo"] = ImageTk.PhotoImage(create_stamp_overlay_image(scaled))
            if state.get("stamp_preview_id") is not None:
                preview_canvas.itemconfig(state["stamp_preview_id"], image=state["stamp_overlay_photo"])
            update_stamp_overlay_position(*state.get("stamp_offset", (0, 0)))

        def on_scale_change(value: str) -> None:
            try:
                percent = float(value)
            except (TypeError, ValueError):
                percent = 100.0
            percent = max(10.0, min(100.0, percent))
            state["stamp_scale_percent"] = percent
            if stamp_scale_label is not None:
                stamp_scale_label.config(text=f"Skala: {int(round(percent))}%")
            refresh_stamp_from_scale()
            if stamp_status_label is not None:
                if state.get("stamp_label"):
                    stamp_status_label.config(text=f"Preset: {state['stamp_label']} — kliknij, aby wstawić (skala {int(round(percent))}%)")
                elif state.get("stamp_pixels") is None:
                    stamp_status_label.config(text="Preset: brak")

        def apply_color_to_neighbor(edge_entry: dict, row: int, col: int, new_val: str | None) -> bool:
            if not edge_entry or not edge_entry.get("enabled"):
                return False
            nr = row - edge_entry["dy_cells"]
            nc = col - edge_entry["dx_cells"]
            if not (0 <= nr < grid_size and 0 <= nc < grid_size):
                return False
            neighbor_mask = edge_entry.get("neighbor_mask", hex_mask)
            if not neighbor_mask[nr][nc]:
                return False
            neighbor_pixels = edge_entry.get("neighbor_pixels")
            if neighbor_pixels is None:
                return False
            if neighbor_pixels[nr][nc] == new_val:
                return False
            neighbor_pixels[nr][nc] = new_val
            edge_entry["dirty"] = True
            return True

        def update_stamp_overlay_position(delta_row: int | None = None, delta_col: int | None = None) -> None:
            if state.get("stamp_pixels") is None or state.get("stamp_overlay_photo") is None:
                if state.get("stamp_preview_id") is not None:
                    preview_canvas.delete(state["stamp_preview_id"])
                    state["stamp_preview_id"] = None
                return
            if delta_row is None or delta_col is None:
                delta_row, delta_col = state.get("stamp_offset", (0, 0))
            else:
                state["stamp_offset"] = (delta_row, delta_col)
            x = grid_offset + delta_col * cell_size
            y = grid_offset + delta_row * cell_size
            if state.get("stamp_preview_id") is None:
                state["stamp_preview_id"] = preview_canvas.create_image(
                    x,
                    y,
                    anchor="nw",
                    image=state["stamp_overlay_photo"],
                    tags="stamp_preview"
                )
            else:
                preview_canvas.coords(state["stamp_preview_id"], x, y)
            preview_canvas.tag_lower("stamp_preview", "outline")

        def clear_stamp_mode(update_label: bool = True) -> None:
            state["stamp_pixels"] = None
            state["stamp_overlay_photo"] = None
            state["stamp_offset"] = (0, 0)
            state["stamp_base_pixels"] = None
            state["stamp_label"] = None
            if state.get("stamp_preview_id") is not None:
                preview_canvas.delete(state["stamp_preview_id"])
                state["stamp_preview_id"] = None
            preview_canvas.config(cursor="")
            if update_label and stamp_status_label is not None:
                stamp_status_label.config(text="Preset: brak")

        def enter_stamp_mode(preset: dict) -> None:
            clear_stamp_mode(update_label=False)
            state["stamp_base_pixels"] = preset["pixels"]
            state["stamp_label"] = preset["name"]
            state["stamp_offset"] = (0, 0)
            state["stamp_scale_percent"] = float(stamp_scale_var.get())
            refresh_stamp_from_scale()
            preview_canvas.config(cursor="hand2")
            update_stamp_overlay_position(0, 0)
            if stamp_status_label is not None:
                stamp_status_label.config(text=f"Preset: {preset['name']} — kliknij, aby wstawić (skala {int(round(state['stamp_scale_percent']))}%)")

        def apply_stamp_at(row: int, col: int) -> None:
            if state.get("stamp_pixels") is None:
                return
            delta_row = row - grid_size // 2
            delta_col = col - grid_size // 2
            state["stamp_offset"] = (delta_row, delta_col)
            update_stamp_overlay_position(delta_row, delta_col)
            changed = False
            stamp_pixels = state["stamp_pixels"]
            neighbor_entry = None
            if state.get("edge_mode_active") and state.get("edge_current_key"):
                neighbor_entry = state["edge_neighbors"].get(state["edge_current_key"])
                if neighbor_entry and not neighbor_entry.get("enabled"):
                    neighbor_entry = None
            for src_row in range(grid_size):
                target_row = src_row + delta_row
                if not (0 <= target_row < grid_size):
                    continue
                for src_col in range(grid_size):
                    target_col = src_col + delta_col
                    if not (0 <= target_col < grid_size) or not state["mask"][target_row][target_col]:
                        continue
                    color = stamp_pixels[src_row][src_col]
                    if color is None:
                        continue
                    if state["pixels"][target_row][target_col] != color:
                        state["pixels"][target_row][target_col] = color
                        changed = True
                    if neighbor_entry and color is not None:
                        if apply_color_to_neighbor(neighbor_entry, target_row, target_col, color):
                            changed = True
            if changed:
                state["history_edit_dirty"] = True
                draw_grid()

        def canvas_motion(event):
            if state.get("stamp_pixels") is None:
                return
            col = int((event.x - grid_offset) // cell_size)
            row = int((event.y - grid_offset) // cell_size)
            if 0 <= row < grid_size and 0 <= col < grid_size:
                update_stamp_overlay_position(row - grid_size // 2, col - grid_size // 2)


        def draw_grid():
            preview_canvas.delete("background")
            if state.get("background_photo"):
                preview_canvas.create_image(0, 0, anchor="nw", image=state["background_photo"], tags="background")
                preview_canvas._background_photo = state["background_photo"]
            preview_canvas.delete("cell")
            preview_canvas.delete("outline")
            preview_canvas.delete("neighbor_outline")
            preview_canvas.delete("stamp_preview")
            preview_canvas.delete("edge_band")
            for row in range(grid_size):
                for col in range(grid_size):
                    if not state["mask"][row][col]:
                        continue
                    x0 = col * cell_size + grid_offset
                    y0 = row * cell_size + grid_offset
                    fill = state["pixels"][row][col] or ""
                    preview_canvas.create_rectangle(
                        x0,
                        y0,
                        x0 + cell_size,
                        y0 + cell_size,
                        fill=fill if fill else "",
                        outline="#333333",
                        width=1,
                        tags=("cell", f"cell_{row}_{col}")
                    )
            for poly_points in neighbor_outline_points:
                preview_canvas.create_polygon(
                    *poly_points,
                    outline="#555555",
                    fill="",
                    width=1,
                    tags="neighbor_outline",
                    smooth=False
                )
            preview_canvas.create_polygon(
                *outline_points,
                outline="#bbbbbb",
                fill="",
                width=2,
                tags="outline",
                smooth=False
            )
            if state.get("edge_mode_active") and state.get("edge_current_key"):
                edge_entry = state["edge_neighbors"].get(state["edge_current_key"])
                if edge_entry and edge_entry.get("enabled"):
                    for row in range(grid_size):
                        band_row = edge_entry["band_mask"][row]
                        if not any(band_row):
                            continue
                        for col in range(grid_size):
                            if not band_row[col]:
                                continue
                            x0 = col * cell_size + grid_offset
                            y0 = row * cell_size + grid_offset
                            preview_canvas.create_rectangle(
                                x0,
                                y0,
                                x0 + cell_size,
                                y0 + cell_size,
                                outline="#ffd966",
                                width=1,
                                tags="edge_band"
                            )
                    preview_canvas.tag_lower("edge_band", "outline")
            update_stamp_overlay_position()

        def enter_edge_mode(edge_key: str) -> None:
            entry = state["edge_neighbors"].get(edge_key)
            if not entry or not entry.get("enabled"):
                return
            if state.get("stamp_pixels") is not None:
                clear_stamp_mode()
            state["edge_mode_active"] = True
            state["edge_current_key"] = edge_key
            selected_edge_var.set(edge_key)
            if edge_status_label is not None:
                edge_status_label.config(text=f"Aktywny: {entry['label']} (sąsiad {entry['neighbor_id']})")
            draw_grid()

        def exit_edge_mode() -> None:
            state["edge_mode_active"] = False
            state["edge_current_key"] = None
            selected_edge_var.set("")
            if edge_status_label is not None:
                edge_status_label.config(text="Aktywny: brak")
            draw_grid()

        def close_preset_window(ref_key: str) -> None:
            window = state.get(ref_key)
            if window and window.winfo_exists():
                try:
                    window.destroy()
                except tk.TclError:
                    pass
            state[ref_key] = None

        def open_presets_for_category(category: dict) -> None:
            existing = state.get("preset_detail_window")
            if existing and existing.winfo_exists():
                existing.destroy()
            win = tk.Toplevel(editor)
            win.title(f"Presety — {category['label']}")
            win.configure(bg="darkolivegreen")
            win.transient(editor)
            win.geometry("420x420")
            state["preset_detail_window"] = win

            def on_close_detail() -> None:
                close_preset_window("preset_detail_window")

            win.protocol("WM_DELETE_WINDOW", on_close_detail)

            header = tk.Label(win, text=category["label"], bg="darkolivegreen", fg="white", font=("Arial", 12, "bold"))
            header.pack(fill=tk.X, pady=(10, 6))

            content = tk.Frame(win, bg="darkolivegreen")
            content.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

            presets = category["builder"]()
            state["preset_preview_refs"] = [preset["preview_photo"] for preset in presets]

            if not presets:
                tk.Label(
                    content,
                    text="Brak presetów w tej kategorii",
                    bg="darkolivegreen",
                    fg="#f2d7d5",
                    font=("Arial", 10)
                ).pack(pady=12)
                return

            grid = tk.Frame(content, bg="darkolivegreen")
            grid.pack(fill=tk.BOTH, expand=True)
            columns = 2
            for idx, preset in enumerate(presets):
                grid.grid_columnconfigure(idx % columns, weight=1)
                btn = tk.Button(
                    grid,
                    image=preset["preview_photo"],
                    text=preset["name"],
                    compound="top",
                    bg="darkolivegreen",
                    fg="white",
                    activebackground="darkolivegreen",
                    activeforeground="white",
                    bd=1,
                    relief=tk.RIDGE,
                    wraplength=150,
                    justify="center",
                    command=lambda p=preset: (
                        enter_stamp_mode(p),
                        close_preset_window("preset_detail_window")
                    )
                )
                btn.grid(row=idx // columns, column=idx % columns, padx=6, pady=6, sticky="nsew")

        def open_preset_library() -> None:
            existing = state.get("preset_category_window")
            if existing and existing.winfo_exists():
                existing.deiconify()
                existing.lift()
                return
            win = tk.Toplevel(editor)
            win.title("Biblioteka presetów")
            win.configure(bg="darkolivegreen")
            win.transient(editor)
            win.geometry("340x360")
            win.resizable(False, False)
            state["preset_category_window"] = win

            def on_close() -> None:
                close_preset_window("preset_category_window")

            win.protocol("WM_DELETE_WINDOW", on_close)

            tk.Label(
                win,
                text="Wybierz kategorię",
                bg="darkolivegreen",
                fg="white",
                font=("Arial", 12, "bold")
            ).pack(fill=tk.X, pady=(12, 6))

            container = tk.Frame(win, bg="darkolivegreen")
            container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

            for category in preset_categories:
                btn = tk.Button(
                    container,
                    text=f"{category['icon']}  {category['label']}",
                    anchor="w",
                    command=lambda c=category: open_presets_for_category(c),
                    bg="saddlebrown",
                    fg="white",
                    activebackground="saddlebrown",
                    activeforeground="white"
                )
                btn.pack(fill=tk.X, pady=4)

        def set_current_color(color: str | None):
            if state.get("stamp_pixels") is not None:
                clear_stamp_mode()
            state["current_color"] = color
            state["eraser"] = False
            if color:
                current_color_preview.config(bg=color, text="", fg="white")
            else:
                current_color_preview.config(bg="#222222", text="Przezroczysty", fg="white")

        def pick_color_dialog():
            color_code = colorchooser.askcolor(title="Wybierz kolor", parent=editor)
            if color_code and color_code[1]:
                set_current_color(color_code[1])

        def toggle_eraser():
            if state.get("stamp_pixels") is not None:
                clear_stamp_mode()
            state["eraser"] = not state["eraser"]
            eraser_btn.config(relief="sunken" if state["eraser"] else "raised")

        def apply_color_to_cell(row: int, col: int):
            if not (0 <= row < grid_size and 0 <= col < grid_size):
                return
            if not state["mask"][row][col]:
                return
            edge_entry = None
            if state.get("edge_mode_active"):
                edge_key = state.get("edge_current_key")
                if not edge_key:
                    return
                edge_entry = state["edge_neighbors"].get(edge_key)
                if not edge_entry or not edge_entry.get("enabled"):
                    return
                if not edge_entry["band_mask"][row][col]:
                    return
            new_val = None if state["eraser"] else state["current_color"]
            pixel_changed = False
            if state["pixels"][row][col] != new_val:
                state["pixels"][row][col] = new_val
                fill = new_val if new_val else ""
                preview_canvas.itemconfig(f"cell_{row}_{col}", fill=fill)
                pixel_changed = True
            neighbor_changed = False
            if edge_entry:
                neighbor_changed = apply_color_to_neighbor(edge_entry, row, col, new_val)
            if pixel_changed or neighbor_changed:
                state["history_edit_dirty"] = True

        def canvas_paint(event):
            col = int((event.x - grid_offset) // cell_size)
            row = int((event.y - grid_offset) // cell_size)
            if state.get("stamp_pixels") is not None:
                if 0 <= row < grid_size and 0 <= col < grid_size:
                    apply_stamp_at(row, col)
                return
            apply_color_to_cell(row, col)

        def canvas_pick_color(event):
            col = int((event.x - grid_offset) // cell_size)
            row = int((event.y - grid_offset) // cell_size)
            if not (0 <= row < grid_size and 0 <= col < grid_size):
                return
            if not state["mask"][row][col]:
                return
            if state.get("edge_mode_active"):
                edge_key = state.get("edge_current_key")
                if not edge_key:
                    return
                edge_entry = state["edge_neighbors"].get(edge_key)
                if not edge_entry or not edge_entry.get("enabled") or not edge_entry["band_mask"][row][col]:
                    return
            color = state["pixels"][row][col]
            if color:
                if state.get("stamp_pixels") is not None:
                    clear_stamp_mode()
                set_current_color(color)

        def handle_left_press(event):
            begin_edit_action()
            canvas_paint(event)

        preview_canvas.bind("<ButtonPress-1>", handle_left_press)
        preview_canvas.bind("<B1-Motion>", canvas_paint)
        preview_canvas.bind("<ButtonRelease-1>", finish_edit_action)
        preview_canvas.bind("<Button-3>", canvas_pick_color)
        preview_canvas.bind("<Motion>", canvas_motion)

        toolbar = tk.Frame(editor, bg="darkolivegreen", width=360)
        toolbar.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(12, 4))

        tools = tk.Frame(editor, bg="darkolivegreen", width=360)
        tools.grid(row=1, column=1, sticky="nsew", padx=(0, 12), pady=(0, 12))

        tk.Label(tools, text="Aktualny kolor", bg="darkolivegreen", fg="white", font=("Arial", 10, "bold")).pack(anchor="w")
        current_color_preview = tk.Label(tools, bg=state["current_color"], width=10, height=2, relief=tk.SUNKEN, bd=2)
        current_color_preview.pack(pady=(2, 8), fill=tk.X)

        tk.Button(tools, text="Wybierz kolor…", command=pick_color_dialog, bg="saddlebrown", fg="white").pack(fill=tk.X, pady=2)

        palette_frame = tk.LabelFrame(tools, text="Paleta", bg="darkolivegreen", fg="white")
        palette_frame.pack(fill=tk.X, pady=(8, 4))

        default_palette = [
            "#2f4f4f", "#556b2f", "#8b4513", "#b8860b",
            "#deb887", "#d2691e", "#6b8e23", "#87ceeb",
            "#4682b4", "#c0c0c0", "#ffffff", "#000000",
        ]
        for idx, pal_color in enumerate(default_palette):
            btn = tk.Button(
                palette_frame,
                bg=pal_color,
                width=3,
                command=lambda c=pal_color: set_current_color(c)
            )
            btn.grid(row=idx // 4, column=idx % 4, padx=2, pady=2, sticky="nsew")

        transparent_row = (len(default_palette) + 3) // 4
        transparent_btn = tk.Button(
            palette_frame,
            text="Przezroczysty",
            command=lambda: set_current_color(None),
            bg="#222222",
            fg="white"
        )
        transparent_btn.grid(row=transparent_row, column=0, columnspan=4, padx=2, pady=(4, 2), sticky="nsew")

        eraser_btn = tk.Button(tools, text="Gumka", command=toggle_eraser, bg="#444", fg="white")
        eraser_btn.pack(fill=tk.X, pady=(8, 2))

        tk.Label(tools, text="Lewy przycisk: maluj", bg="darkolivegreen", fg="white").pack(anchor="w", pady=(4, 0))
        tk.Label(tools, text="Prawy przycisk: pipeta", bg="darkolivegreen", fg="white").pack(anchor="w")

        tk.Button(
            tools,
            text="Biblioteka presetów…",
            command=open_preset_library,
            bg="saddlebrown",
            fg="white"
        ).pack(fill=tk.X, pady=(10, 4))

        tk.Button(
            tools,
            text="Wyłącz preset",
            command=clear_stamp_mode,
            bg="#555555",
            fg="white"
        ).pack(fill=tk.X, pady=(0, 4))

        stamp_status_label = tk.Label(tools, text="Preset: brak", bg="darkolivegreen", fg="#d4f2bf", anchor="w", wraplength=220, justify="left")
        stamp_status_label.pack(fill=tk.X, padx=2, pady=(0, 6))

        scale_frame = tk.LabelFrame(tools, text="Skala presetów", bg="darkolivegreen", fg="white")
        scale_frame.pack(fill=tk.X, pady=(0, 8))
        stamp_scale_label = tk.Label(scale_frame, text="Skala: 100%", bg="darkolivegreen", fg="#d4f2bf", anchor="w")
        stamp_scale_label.pack(fill=tk.X, padx=4, pady=(4, 0))
        stamp_scale_widget = tk.Scale(
            scale_frame,
            from_=10,
            to=100,
            resolution=5,
            orient=tk.HORIZONTAL,
            variable=stamp_scale_var,
            command=on_scale_change,
            length=220,
            bg="darkolivegreen",
            highlightthickness=0,
            troughcolor="#555555"
        )
        stamp_scale_widget.pack(fill=tk.X, padx=4, pady=(2, 4))
        on_scale_change(str(stamp_scale_var.get()))

        edge_frame = tk.LabelFrame(tools, text="Pas styku", bg="darkolivegreen", fg="white")
        edge_frame.pack(fill=tk.X, pady=(12, 6))
        tk.Label(
            edge_frame,
            text="Wybierz krawędź, aby malować styki dwóch heksów jednocześnie.",
            bg="darkolivegreen",
            fg="#d4f2bf",
            wraplength=180,
            justify="left"
        ).pack(fill=tk.X, padx=4, pady=(2, 4))
        for edge_entry in edge_definitions:
            edge_info = edge_mode_data[edge_entry["key"]]
            label_text = f"{edge_entry['label']} → {edge_info['neighbor_id']}"
            btn = tk.Radiobutton(
                edge_frame,
                text=label_text,
                variable=selected_edge_var,
                value=edge_entry["key"],
                command=lambda key=edge_entry["key"]: enter_edge_mode(key),
                bg="darkolivegreen",
                fg="white",
                selectcolor="darkolivegreen",
                anchor="w"
            )
            if not edge_info.get("enabled"):
                btn.config(state=tk.DISABLED, fg="#555555")
            btn.pack(fill=tk.X, padx=4, pady=1)
        tk.Button(
            edge_frame,
            text="Wyłącz pas styku",
            command=exit_edge_mode,
            bg="#555555",
            fg="white"
        ).pack(fill=tk.X, padx=4, pady=(6, 2))
        edge_status_label = tk.Label(edge_frame, text="Aktywny: brak", bg="darkolivegreen", fg="#d4f2bf", anchor="w", wraplength=180, justify="left")
        edge_status_label.pack(fill=tk.X, padx=4, pady=(0, 2))

        def save_and_close():
            clear_stamp_mode(update_label=False)
            close_preset_window("preset_detail_window")
            close_preset_window("preset_category_window")
            texture_rel = self._save_hex_texture(hex_id, state["pixels"])
            self.hex_data.setdefault(hex_id, {}).update({"texture": texture_rel})
            textures_to_drop = {texture_rel}
            neighbor_updates: list[str] = []
            for edge_entry in state["edge_neighbors"].values():
                if not edge_entry.get("enabled") or not edge_entry.get("dirty"):
                    continue
                neighbor_pixels = edge_entry.get("neighbor_pixels")
                if neighbor_pixels is None:
                    continue
                neighbor_id = edge_entry["neighbor_id"]
                neighbor_texture_rel = self._save_hex_texture(neighbor_id, neighbor_pixels)
                neighbor_record = self.hex_data.get(neighbor_id)
                if neighbor_record is None:
                    neighbor_record = {
                        "terrain_key": "teren_płaski",
                        "move_mod": 0,
                        "defense_mod": 0,
                    }
                    self.hex_data[neighbor_id] = neighbor_record
                neighbor_record["texture"] = neighbor_texture_rel
                edge_entry["neighbor_texture_rel"] = neighbor_texture_rel
                edge_entry["dirty"] = False
                textures_to_drop.add(neighbor_texture_rel)
                neighbor_updates.append(neighbor_id)
                if getattr(self, "selected_hex", None) == neighbor_id:
                    self.update_hex_info_display(neighbor_id)
            if textures_to_drop:
                self.hex_texture_cache = {k: v for k, v in self.hex_texture_cache.items() if k[0] not in textures_to_drop}
            if neighbor_updates:
                print(f"Zapisano pas styku dla sąsiadów: {', '.join(neighbor_updates)}")
            editor.grab_release()
            editor.destroy()
            self._texture_editor_window = None
            self.update_hex_info_display(hex_id)
            self.draw_grid()
            self.auto_save_and_export("zapisano teksturę heksa")

        def close_editor():
            clear_stamp_mode(update_label=False)
            close_preset_window("preset_detail_window")
            close_preset_window("preset_category_window")
            editor.grab_release()
            editor.destroy()
            self._texture_editor_window = None

        undo_btn = tk.Button(toolbar, text="Cofnij (Ctrl+Z)", command=undo_action, bg="saddlebrown", fg="white", width=14, state=tk.DISABLED)
        undo_btn.pack(side=tk.LEFT, padx=4)
        redo_btn = tk.Button(toolbar, text="Ponów (Ctrl+Y)", command=redo_action, bg="saddlebrown", fg="white", width=14, state=tk.DISABLED)
        redo_btn.pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Zapisz", command=save_and_close, bg="forestgreen", fg="white", width=12).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Anuluj", command=close_editor, bg="saddlebrown", fg="white", width=12).pack(side=tk.LEFT, padx=4)
        update_history_buttons()

        editor.bind("<Control-z>", undo_action)
        editor.bind("<Control-Z>", undo_action)
        editor.bind("<Control-y>", redo_action)
        editor.bind("<Control-Y>", redo_action)

        draw_grid()

        texture_rel = terrain.get("texture")
        if texture_rel:
            try:
                img_path = fix_image_path(texture_rel)
                if img_path.exists():
                    tk.Label(tools, text=f"Plik: {to_rel(str(img_path))}", bg="darkolivegreen", fg="white", wraplength=180, justify="left").pack(fill=tk.X, pady=(10, 0))
            except Exception:
                pass

        editor.protocol("WM_DELETE_WINDOW", close_editor)

    def _load_hex_texture_pixels(self, texture_rel: str | None) -> list[list[str | None]]:
        grid_size = HEX_TEXTURE_GRID_SIZE
        mask = self._precompute_hex_mask()
        pixels: list[list[str | None]] = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        if not texture_rel:
            return pixels
        img_path = fix_image_path(texture_rel)
        if not img_path.exists():
            return pixels
        try:
            img = Image.open(img_path).convert("RGBA")
            if img.width != grid_size or img.height != grid_size:
                img = img.resize((grid_size, grid_size), Image.NEAREST)
            for row in range(grid_size):
                for col in range(grid_size):
                    if not mask[row][col]:
                        continue
                    r, g, b, a = img.getpixel((col, row))
                    if a == 0:
                        pixels[row][col] = None
                    else:
                        pixels[row][col] = f"#{r:02x}{g:02x}{b:02x}"
        except Exception as exc:
            print(f"Nie udało się wczytać tekstury heksa: {exc}")
        return pixels

    def _save_hex_texture(self, hex_id: str, pixels: list[list[str | None]]) -> str:
        grid_size = HEX_TEXTURE_GRID_SIZE
        mask = self._precompute_hex_mask()
        base_img = Image.new("RGBA", (grid_size, grid_size), (0, 0, 0, 0))
        for row in range(grid_size):
            for col in range(grid_size):
                if not mask[row][col]:
                    continue
                color = pixels[row][col]
                if color:
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    base_img.putpixel((col, row), (r, g, b, 255))
        export_img = base_img.resize((HEX_TEXTURE_EXPORT_SIZE, HEX_TEXTURE_EXPORT_SIZE), Image.NEAREST)
        filename = f"hex_{hex_id.replace(',', '_')}.png"
        output_path = HEX_TEXTURE_DIR / filename
        export_img.save(output_path)
        rel_path = to_rel(str(output_path))
        print(f"Zapisano teksturę heksa do {output_path}")
        return rel_path

    def _get_hex_texture_image(self, texture_rel: str) -> ImageTk.PhotoImage | None:
        cache_key = (texture_rel, self.hex_size)
        if cache_key in self.hex_texture_cache:
            return self.hex_texture_cache[cache_key]
        img_path = fix_image_path(texture_rel)
        if not img_path.exists():
            return None
        try:
            img = Image.open(img_path).convert("RGBA")
            target_size = (int(self.hex_size * 2), int(self.hex_size * 2))
            img = img.resize(target_size, Image.NEAREST)
            photo = ImageTk.PhotoImage(img)
            self.hex_texture_cache[cache_key] = photo
            return photo
        except Exception as exc:
            print(f"Nie udało się wczytać obrazu tekstury: {exc}")
            return None

    def _precompute_hex_mask(self) -> list[list[bool]]:
        grid_size = HEX_TEXTURE_GRID_SIZE
        cache = getattr(self, "_hex_texture_masks", None)
        if cache and grid_size in cache:
            return cache[grid_size]

        center = grid_size / 2.0
        radius = grid_size / 2.0 - 0.5
        vertices = get_hex_vertices(center, center, radius)

        mask = [[False for _ in range(grid_size)] for _ in range(grid_size)]
        for row in range(grid_size):
            for col in range(grid_size):
                sample_points = [
                    (col + 0.5, row + 0.5),
                    (col, row),
                    (col + 1.0, row),
                    (col, row + 1.0),
                    (col + 1.0, row + 1.0),
                ]
                if any(point_in_polygon(px, py, vertices) for px, py in sample_points):
                    mask[row][col] = True
                    continue
                for vx, vy in vertices:
                    if col <= vx <= col + 1 and row <= vy <= row + 1:
                        mask[row][col] = True
                        break

        if cache is None:
            self._hex_texture_masks = {}
        if not hasattr(self, "_hex_texture_vertices"):
            self._hex_texture_vertices = {}
        self._hex_texture_masks[grid_size] = mask
        self._hex_texture_vertices[grid_size] = vertices
        return mask

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

        texture_rel = terrain.get("texture")
        if texture_rel:
            self.texture_info_label.config(text=f"Tekstura: {texture_rel}")
        else:
            self.texture_info_label.config(text="Tekstura: domyślna")
        self.edit_texture_button.config(state=tk.NORMAL)
        
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
                "orientation": "pointy",
                "background": self._serialize_background_info()
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
            meta = loaded_data.get("meta", {})
            if meta:
                self.hex_size = meta.get("hex_size", self.hex_size)
                self.config["grid_cols"] = meta.get("cols", self.config.get("grid_cols"))
                self.config["grid_rows"] = meta.get("rows", self.config.get("grid_rows"))
                self._apply_background_metadata(meta.get("background"))
            else:
                self._apply_background_metadata(None)
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

            # i dopiero potem rysuj grid
            self.draw_grid()
            
            # Odśwież paletę żetonów
            self.update_filtered_tokens()
            
            # Nie pokazuj popup przy starcie - tylko loguj do konsoli
            print(f"✅ Wczytano dane mapy z: {self.current_working_file}")
            print(f"📍 Kluczowe punkty: {len(self.key_points)}")
            print(f"🚀 Punkty wystawienia: {sum(len(v) for v in self.spawn_points.values())}")
        else:
            self._apply_background_metadata(None)
            self.load_map_image()
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
