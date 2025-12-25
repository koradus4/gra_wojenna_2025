"""
GENERATOR BUDYNKÓW MIEJSKICH
Narzędzie do generowania wariantów budynków z obrazów referencyjnych
Wykorzystuje Gemini Vision API + proceduralne transformacje pixel-art

Autor: AI Assistant
Data: 23 grudnia 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageEnhance
from pathlib import Path
import json
import random
import google.generativeai as genai
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import colorsys

# ============================================================================
# KONFIGURACJA
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTLEMENT_ASSETS_DIR = PROJECT_ROOT / "assets" / "terrain" / "presets" / "user_assets" / "settlement"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "terrain" / "presets" / "user_assets" / "settlement" / "ai_generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Klucze API
GEMINI_API_KEY = "AIzaSyAuXWOk-wnT2hGxK7LpXFIs9VuydjG6Eis"  # Gemini Vision (analiza)
VERTEX_AI_KEY = "AQ.Ab8RN6KLXtialOQsxh-zMBt94kILPeaXpKTgERDITKJhUVwDPA"  # Vertex AI (Imagen 3)
VERTEX_PROJECT_ID = "gen-lang-client-0986780723"
VERTEX_LOCATION = "us-central1"

# Typy budynków - PEŁNA BAZA
BUILDING_TYPES = {
    "kamienica": {"name": "Kamienica", "base_height": (24, 32), "base_width": (28, 40)},
    "dom": {"name": "Dom mieszkalny", "base_height": (18, 26), "base_width": (20, 32)},
    "ratusz": {"name": "Ratusz", "base_height": (28, 38), "base_width": (32, 48)},
    "shop": {"name": "Sklep/warsztat", "base_height": (16, 24), "base_width": (18, 28)},
    "kościół": {"name": "Kościół", "base_height": (32, 42), "base_width": (28, 40)},
    "dworzec": {"name": "Dworzec kolejowy", "base_height": (20, 28), "base_width": (36, 52)},
    "szkoła": {"name": "Szkoła", "base_height": (22, 30), "base_width": (32, 44)},
    "szpital": {"name": "Szpital", "base_height": (24, 32), "base_width": (36, 48)},
    "restauracja": {"name": "Restauracja/kawiarnia", "base_height": (18, 24), "base_width": (24, 32)},
    "bank": {"name": "Bank", "base_height": (24, 32), "base_width": (28, 40)},
    "teatr": {"name": "Teatr/kino", "base_height": (26, 34), "base_width": (32, 48)},
    "fabryka": {"name": "Fabryka/zakład", "base_height": (20, 28), "base_width": (36, 56)},
    "magazyn": {"name": "Magazyn", "base_height": (18, 24), "base_width": (32, 48)},
    "hotel": {"name": "Hotel", "base_height": (28, 36), "base_width": (32, 44)},
    "poczta": {"name": "Poczta", "base_height": (20, 26), "base_width": (24, 36)},
    "straż": {"name": "Straż pożarna", "base_height": (22, 28), "base_width": (28, 40)},
    "koszary": {"name": "Koszary wojskowe", "base_height": (20, 26), "base_width": (36, 52)},
    "muzeum": {"name": "Muzeum", "base_height": (24, 32), "base_width": (32, 44)},
}

# Warianty stylistyczne
STYLE_VARIANTS = {
    "cegła": {"name": "Ceglany", "hue_shift": (-10, 10), "sat_mult": (0.9, 1.1)},
    "tynk": {"name": "Tynkowany", "hue_shift": (0, 20), "sat_mult": (0.7, 0.9)},
    "kamień": {"name": "Kamienny", "hue_shift": (-20, 0), "sat_mult": (0.5, 0.8)},
    "drewno": {"name": "Drewniany", "hue_shift": (15, 35), "sat_mult": (0.8, 1.0)},
}

# Prompty dla Vertex AI Imagen 3 - PIXEL ART FOCUSED
BUILDING_PROMPTS = {
    "kamienica": "Isometric pixel art apartment building for retro game. 3-4 floors, beige walls, orange tile roof, small square windows in rows, simple pixel-art style, 16-color palette, visible pixels, clean outlines, game asset, no anti-aliasing",
    "dom": "Isometric pixel art small house for retro game. 1-2 floors, wooden or brick texture, pitched roof, chimney, simple windows, pixel-art style, 12-color palette, visible individual pixels, game asset",
    "ratusz": "Isometric pixel art town hall for retro game. Clock tower with visible clock face, ornate facade, arched entrance, Polish flag, orange tile roof, pixel-art style, 16-color palette, clean pixel edges, game asset",
    "shop": "Isometric pixel art shop building for retro game. Ground floor storefront, awning, display window, living quarters above, pixel-art style, 12-color palette, visible pixels, game asset",
    "kościół": "Isometric pixel art church for retro game. Bell tower with cross on top, arched Gothic windows, stone walls, orange roof, pixel-art style, 16-color palette, clean outlines, game asset",
    "dworzec": "Isometric pixel art railway station for retro game. Long rectangular building, platform, clock on facade, brick walls, industrial style, pixel-art, 16-color palette, visible pixels, game asset",
    "szkoła": "Isometric pixel art school building for retro game. 2-3 floors, many uniform windows, brick walls, institutional look, pixel-art style, 12-color palette, clean edges, game asset",
    "szpital": "Isometric pixel art hospital for retro game. Multi-wing building, red cross symbol, many windows, clean white walls, pixel-art style, 16-color palette, visible pixels, game asset",
    "restauracja": "Isometric pixel art restaurant for retro game. Decorative facade, large windows, outdoor tables, welcoming entrance, pixel-art style, 12-color palette, game asset",
    "bank": "Isometric pixel art bank building for retro game. Solid architecture, columns at entrance, vault-like appearance, stone facade, pixel-art style, 16-color palette, clean outlines, game asset",
    "teatr": "Isometric pixel art theater for retro game. Grand facade, marquee sign, decorative entrance, Art Deco style, pixel-art, 16-color palette, visible pixels, game asset",
    "fabryka": "Isometric pixel art factory for retro game. Large rectangular building, brick smokestack, small windows, industrial design, pixel-art style, 12-color palette, game asset",
    "magazyn": "Isometric pixel art warehouse for retro game. Simple rectangular structure, large cargo doors, minimal windows, brick/wood construction, pixel-art style, 12-color palette, game asset",
    "hotel": "Isometric pixel art hotel for retro game. 3-4 floors, many windows, balconies, welcoming entrance, traditional architecture, pixel-art style, 16-color palette, visible pixels, game asset",
    "poczta": "Isometric pixel art post office for retro game. Civic building, service windows, postal insignia, brick construction, pixel-art style, 12-color palette, clean edges, game asset",
    "straż": "Isometric pixel art fire station for retro game. Tower for hoses, large garage doors, bell on top, brick walls, pixel-art style, 16-color palette, visible pixels, game asset",
    "koszary": "Isometric pixel art military barracks for retro game. Long rectangular building, uniform windows, parade ground, austere design, pixel-art style, 12-color palette, game asset",
    "muzeum": "Isometric pixel art museum for retro game. Neo-Classical facade, columns, symmetrical design, stone walls, grand entrance, pixel-art style, 16-color palette, visible pixels, game asset",
}

# ============================================================================
# FUNKCJE POMOCNICZE - ANALIZA OBRAZU
# ============================================================================

def analyze_building_with_gemini(image_path: Path, api_key: str) -> Dict:
    """Analizuje budynek przez Gemini Vision"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        img = Image.open(image_path)
        
        prompt = """
        Przeanalizuj ten pixel-art budynek dla gry wojennej 1939.
        
        ZADANIE:
        1. Określ typ budynku (kamienica, dom, ratusz, sklep, kościół, dworzec)
        2. Opisz styl architektoniczny (cegła, tynk, kamień, drewno)
        3. Wypisz główne kolory (RGB)
        4. Opisz charakterystyczne elementy (okna, dach, drzwi, ozdoby)
        5. Wymiary (wysokość, szerokość w pikselach)
        
        Zwróć JSON:
        {
            "building_type": "typ",
            "style": "styl",
            "primary_colors": ["#RRGGBB", "#RRGGBB"],
            "features": ["okna prostokątne", "dach dwuspadowy", ...],
            "dimensions": {"width": 38, "height": 28},
            "roof_type": "dwuspadowy/płaski/mansardowy",
            "window_count": 8,
            "floors": 3,
            "description": "krótki opis"
        }
        """
        
        response = model.generate_content([prompt, img])
        
        # Parsowanie JSON z odpowiedzi
        text = response.text
        # Usuń markdown formatting jeśli jest
        text = text.replace("```json", "").replace("```", "").strip()
        
        return json.loads(text)
        
    except Exception as e:
        print(f"Błąd analizy Gemini: {e}")
        return {
            "building_type": "unknown",
            "style": "unknown",
            "primary_colors": ["#8B7355", "#6B5345"],
            "features": [],
            "dimensions": {"width": 32, "height": 24},
            "description": f"Analiza niedostępna: {str(e)}"
        }

# ============================================================================
# FUNKCJE POMOCNICZE - TRANSFORMACJE PIXEL-ART
# ============================================================================

def get_dominant_colors(img: Image.Image, num_colors: int = 5) -> List[Tuple[int, int, int]]:
    """Wyodrębnia dominujące kolory z obrazu"""
    # Zmniejsz obraz dla szybkości
    img_small = img.copy()
    img_small.thumbnail((100, 100))
    
    # Konwersja do RGB
    if img_small.mode != 'RGB':
        img_small = img_small.convert('RGB')
    
    # Zlicz kolory
    colors = img_small.getcolors(10000)
    if not colors:
        return [(139, 115, 85)] * num_colors
    
    # Sortuj po częstości
    sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
    
    # Zwróć top N (pomijając przezroczyste/białe)
    result = []
    for count, color in sorted_colors:
        # Pomijaj bardzo jasne (tło) i bardzo ciemne (kontury)
        if len(color) == 3:
            r, g, b = color
            brightness = (r + g + b) / 3
            if 30 < brightness < 230:
                result.append(color)
                if len(result) >= num_colors:
                    break
    
    return result or [(139, 115, 85)] * num_colors


def shift_hue(color: Tuple[int, int, int], shift: float) -> Tuple[int, int, int]:
    """Przesuwa odcień koloru (HSV)"""
    r, g, b = [x / 255.0 for x in color]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    # Przesuń odcień
    h = (h + shift / 360.0) % 1.0
    
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def adjust_saturation(color: Tuple[int, int, int], multiplier: float) -> Tuple[int, int, int]:
    """Zmienia nasycenie koloru"""
    r, g, b = [x / 255.0 for x in color]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    s = max(0.0, min(1.0, s * multiplier))
    
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def create_color_map(original_colors: List[Tuple], target_style: str) -> Dict:
    """Tworzy mapowanie kolorów dla danego stylu"""
    style_config = STYLE_VARIANTS.get(target_style, STYLE_VARIANTS["cegła"])
    
    hue_shift = random.uniform(*style_config["hue_shift"])
    sat_mult = random.uniform(*style_config["sat_mult"])
    
    color_map = {}
    for orig_color in original_colors:
        new_color = shift_hue(orig_color, hue_shift)
        new_color = adjust_saturation(new_color, sat_mult)
        color_map[orig_color] = new_color
    
    return color_map


def apply_color_transform(img: Image.Image, color_map: Dict) -> Image.Image:
    """Aplikuje transformację kolorów do obrazu"""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    pixels = img.load()
    width, height = img.size
    
    # Stwórz nowy obraz
    result = Image.new('RGBA', (width, height))
    result_pixels = result.load()
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            
            if a == 0:  # Przezroczysty
                result_pixels[x, y] = (r, g, b, a)
                continue
            
            # Znajdź najbliższy kolor w mapie
            orig_color = (r, g, b)
            closest_orig = min(color_map.keys(), 
                             key=lambda c: sum((c[i] - orig_color[i])**2 for i in range(3)))
            
            new_color = color_map[closest_orig]
            result_pixels[x, y] = (*new_color, a)
    
    return result


def flip_horizontal(img: Image.Image) -> Image.Image:
    """Odbicie lustrzane"""
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def add_weathering(img: Image.Image, intensity: float = 0.3) -> Image.Image:
    """Dodaje efekt starzenia/zniszczenia"""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Lekkie przyciemnienie losowych pikseli
    pixels = img.load()
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a > 0 and random.random() < intensity * 0.1:
                darken = random.uniform(0.7, 0.95)
                pixels[x, y] = (int(r * darken), int(g * darken), int(b * darken), a)
    
    return img


def generate_building_variant(
    reference_img: Image.Image,
    variant_config: Dict
) -> Image.Image:
    """
    Generuje wariant budynku z referencji
    
    variant_config:
        - style: nazwa stylu z STYLE_VARIANTS
        - flip: bool - odbicie lustrzane
        - weathering: float 0-1 - stopień zniszczenia
        - color_shift: float - dodatkowe przesunięcie koloru
    """
    img = reference_img.copy()
    
    # 1. Transformacja kolorów
    if variant_config.get("style"):
        dominant_colors = get_dominant_colors(img)
        color_map = create_color_map(dominant_colors, variant_config["style"])
        img = apply_color_transform(img, color_map)
    
    # 2. Odbicie lustrzane
    if variant_config.get("flip", False):
        img = flip_horizontal(img)
    
    # 3. Starzenie
    weathering = variant_config.get("weathering", 0.0)
    if weathering > 0:
        img = add_weathering(img, weathering)
    
    return img


# ============================================================================
# GENERATOR Z VERTEX AI IMAGEN 3
# ============================================================================

def generate_with_imagen3(
    building_type: str,
    style: str,
    reference_path: Optional[Path] = None,
    prompt_override: Optional[str] = None,
    use_reference: bool = True
) -> Optional[Image.Image]:
    """
    Generuje NOWY budynek przez Vertex AI Imagen 3
    
    Args:
        building_type: Typ budynku z BUILDING_TYPES
        style: Styl architektoniczny z STYLE_VARIANTS
        reference_path: Opcjonalny obraz referencyjny (style guide)
        prompt_override: Niestandardowy prompt (opcjonalnie)
        use_reference: Czy użyć obrazu referencyjnego
    
    Returns:
        PIL Image lub None jeśli błąd
    """
    try:
        # Import Vertex AI
        try:
            from google.cloud import aiplatform
            import vertexai
            from vertexai.preview.vision_models import ImageGenerationModel
        except ImportError:
            print("⚠️  Brak biblioteki Vertex AI. Zainstaluj:")
            print("   pip install google-cloud-aiplatform")
            return None
        
        # Inicjalizacja Vertex AI
        vertexai.init(
            project=VERTEX_PROJECT_ID,
            location=VERTEX_LOCATION
        )
        
        # Załaduj model Imagen 3
        model = ImageGenerationModel.from_pretrained("imagegeneration@006")
        
        # Przygotuj prompt
        if prompt_override:
            prompt = prompt_override
        else:
            # Użyj szczegółowego promptu z bazy
            building_desc = BUILDING_PROMPTS.get(
                building_type, 
                f"Historical building from 1939 Poland: {building_type}"
            )
            
            # Mapowanie stylów
            style_descriptions = {
                "cegła": "Red brick construction, earthy brown-red tones",
                "tynk": "Plastered walls, light beige or cream colors, smooth facade",
                "kamień": "Stone construction, grey granite tones, solid appearance",
                "drewno": "Wooden construction, natural brown tones, timber details",
            }
            
            style_desc = style_descriptions.get(style, "Traditional construction style")
            
            prompt = f"""
PIXEL ART BUILDING FOR RETRO STRATEGY GAME

TYPE: {building_desc}
STYLE: {style_desc}

CRITICAL PIXEL ART RULES:
✓ Isometric view (like Age of Empires, SimCity 2000)
✓ VISIBLE PIXELS - each pixel clearly defined, NO blur, NO anti-aliasing
✓ 12-16 color palette MAXIMUM
✓ Simple geometric shapes - triangles, rectangles, squares
✓ Clean black outlines around building
✓ Flat color fills with simple 2-tone shading only
✓ Orange/red tile roof (classic pixel-art style)
✓ Dark simple windows (black/dark blue rectangles)
✓ Transparent background

FORBIDDEN:
✗ NO realistic textures or gradients
✗ NO photo-realistic rendering
✗ NO smooth anti-aliasing
✗ NO complex details
✗ NO modern architecture

EXACTLY LIKE: 16-bit strategy game building sprite (1990s style)
            """.strip()
        
        print(f"📝 Prompt: {prompt[:150]}...")
        
        # Dodaj dodatkowe szczegóły stylistyczne do promptu jeśli jest referencja
        if use_reference and reference_path and reference_path.exists():
            print(f"🖼️  Referencja stylistyczna: {reference_path.name}")
            # Wzbogać prompt o więcej szczegółów pixel-art
            prompt += "\n\nSTYLE: Clean pixel art with defined edges, isometric view, limited color palette (8-16 colors), visible individual pixels, no anti-aliasing, sharp outlines."
        
        # Parametry generowania
        generation_params = {
            "prompt": prompt,
            "number_of_images": 1,
            "aspect_ratio": "1:1",
            "safety_filter_level": "block_few",
            "person_generation": "dont_allow",
        }
        
        # GENERUJ!
        print("🎨 Generuję przez Imagen 3...")
        response = model.generate_images(**generation_params)
        
        # Pobierz wygenerowany obraz
        if response.images:
            generated = response.images[0]
            
            # Konwersja do PIL Image
            try:
                pil_img = generated._pil_image
            except AttributeError:
                # Alternatywna metoda - zapis i wczytanie
                temp_output = OUTPUT_DIR / "_temp_imagen_output.png"
                generated.save(str(temp_output))
                pil_img = Image.open(temp_output)
                temp_output.unlink()
            
            # POST-PROCESSING: Dopasuj do projektu
            pil_img = post_process_generated_image(pil_img)
            
            print("✅ Wygenerowano przez Imagen 3!")
            return pil_img
        else:
            print("❌ Imagen 3 nie zwrócił obrazu")
            return None
            
    except Exception as e:
        print(f"❌ Błąd Imagen 3: {e}")
        import traceback
        traceback.print_exc()
        return None


def post_process_generated_image(img: Image.Image) -> Image.Image:
    """
    Post-processing wygenerowanego obrazu aby dopasować do projektu
    - Resize do 64x64
    - Konwersja do RGBA
    - Czyszczenie tła
    """
    # 1. Konwersja do RGBA
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # 2. Resize do 64x64 (jeśli potrzebne)
    if img.size != (64, 64):
        # Użyj NEAREST dla pixel-art (bez interpolacji)
        img = img.resize((64, 64), Image.NEAREST)
    
    # 3. Wyostrz kontury (opcjonalnie)
    # img = img.filter(ImageFilter.SHARPEN)
    
    return img


# ============================================================================
# GUI - GŁÓWNA APLIKACJA
# ============================================================================

class SettlementGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("🏛️ Generator Budynków Miejskich")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2F4F2F")
        
        # Dane
        self.reference_buildings = []
        self.current_reference: Optional[Path] = None
        self.current_analysis: Optional[Dict] = None
        self.generated_variants = []  # Lista: (img, label, building_type, style)
        self.variant_checkboxes = []  # Lista: (checkbox_var, img, label, building_type, style)
        self.current_building_type: Optional[str] = None
        
        # Załaduj referencje
        self.load_reference_buildings()
        
        # GUI
        self.build_gui()
        
    def load_reference_buildings(self):
        """Ładuje budynki referencyjne z folderu settlement"""
        for png_file in SETTLEMENT_ASSETS_DIR.glob("*.png"):
            # Pomijaj thumbnails
            if "_thumb" not in png_file.stem:
                self.reference_buildings.append(png_file)
        
        print(f"✅ Załadowano {len(self.reference_buildings)} budynków referencyjnych")
    
    def build_gui(self):
        """Buduje interfejs użytkownika"""
        
        # ===== GÓRNY PANEL - NAGŁÓWEK =====
        header = tk.Frame(self.root, bg="#556B2F", height=60, relief=tk.RIDGE, bd=3)
        header.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(
            header,
            text="🏛️ GENERATOR BUDYNKÓW MIEJSKICH",
            bg="#556B2F",
            fg="white",
            font=("Arial", 18, "bold")
        ).pack(side=tk.LEFT, padx=20, pady=10)
        
        tk.Label(
            header,
            text="Powered by Gemini Vision + Procedural Pixel-Art",
            bg="#556B2F",
            fg="#FFD700",
            font=("Arial", 10, "italic")
        ).pack(side=tk.LEFT, padx=10)
        
        # ===== GŁÓWNY KONTENER =====
        main_container = tk.Frame(self.root, bg="#2F4F2F")
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # LEWA STRONA - Referencje i analiza
        left_panel = tk.Frame(main_container, bg="#3D5A3D", relief=tk.SUNKEN, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # PRAWA STRONA - Generowanie i podgląd
        right_panel = tk.Frame(main_container, bg="#3D5A3D", relief=tk.SUNKEN, bd=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # ===== LEWA STRONA =====
        
        # TRYB PRACY
        mode_frame = tk.LabelFrame(
            left_panel,
            text="⚙️ Tryb generowania",
            bg="#3D5A3D",
            fg="white",
            font=("Arial", 12, "bold")
        )
        mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.generation_mode_var = tk.StringVar(value="new")
        
        tk.Radiobutton(
            mode_frame,
            text="🏗️ GENERUJ NOWE BUDYNKI (Imagen 3)",
            variable=self.generation_mode_var,
            value="new",
            command=self.on_mode_changed,
            bg="#3D5A3D",
            fg="white",
            selectcolor="#556B2F",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        tk.Radiobutton(
            mode_frame,
            text="🎨 Warianty z istniejących",
            variable=self.generation_mode_var,
            value="variants",
            command=self.on_mode_changed,
            bg="#3D5A3D",
            fg="white",
            selectcolor="#556B2F",
            font=("Arial", 10)
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # SEKCJA: WYBÓR TYPU BUDYNKU (dla trybu "new")
        self.building_type_frame = tk.LabelFrame(
            left_panel,
            text="1️⃣ Wybierz typ budynku do wygenerowania",
            bg="#3D5A3D",
            fg="white",
            font=("Arial", 12, "bold")
        )
        self.building_type_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Lista typów budynków
        type_list_frame = tk.Frame(self.building_type_frame, bg="#3D5A3D")
        type_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        type_scrollbar = tk.Scrollbar(type_list_frame)
        type_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.building_type_listbox = tk.Listbox(
            type_list_frame,
            bg="#2F4F2F",
            fg="#FFD700",
            font=("Arial", 11, "bold"),
            selectmode=tk.SINGLE,
            yscrollcommand=type_scrollbar.set,
            height=15
        )
        self.building_type_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        type_scrollbar.config(command=self.building_type_listbox.yview)
        
        # Wypełnij listę typów
        for key, data in BUILDING_TYPES.items():
            display = f"{data['name']} ({key})"
            self.building_type_listbox.insert(tk.END, display)
        
        self.building_type_listbox.bind("<<ListboxSelect>>", self.on_building_type_selected)
        
        # Opis wybranego typu
        self.type_description_label = tk.Label(
            self.building_type_frame,
            bg="#1C1C1C",
            fg="#00FF00",
            font=("Courier", 9),
            text="← Wybierz typ budynku",
            wraplength=300,
            justify=tk.LEFT,
            padx=10,
            pady=10
        )
        self.type_description_label.pack(pady=10, fill=tk.X, padx=10)
        
        # Sekcja: Wybór referencji (dla trybu "variants")
        self.ref_frame = tk.LabelFrame(
            left_panel,
            text="1️⃣ Wybierz budynek referencyjny",
            bg="#3D5A3D",
            fg="white",
            font=("Arial", 12, "bold")
        )
        # Nie pack() - będzie pokazywany warunkowo
        
        # Lista budynków
        ref_list_frame = tk.Frame(self.ref_frame, bg="#3D5A3D")
        ref_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(ref_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.ref_listbox = tk.Listbox(
            ref_list_frame,
            bg="#2F4F2F",
            fg="white",
            font=("Courier", 10),
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set
        )
        self.ref_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.ref_listbox.yview)
        
        # Wypełnij listę
        for building in self.reference_buildings:
            self.ref_listbox.insert(tk.END, building.stem)
        
        self.ref_listbox.bind("<<ListboxSelect>>", self.on_reference_selected)
        
        # Podgląd referencji
        self.ref_preview_label = tk.Label(self.ref_frame, bg="#2F4F2F", text="Podgląd referencji")
        self.ref_preview_label.pack(pady=10)
        
        # Przycisk analizy
        tk.Button(
            self.ref_frame,
            text="🔍 Analizuj przez Gemini Vision",
            command=self.analyze_reference,
            bg="#4169E1",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=10
        ).pack(pady=10)
        
        # Wynik analizy
        analysis_frame = tk.LabelFrame(
            left_panel,
            text="2️⃣ Analiza budynku",
            bg="#3D5A3D",
            fg="white",
            font=("Arial", 12, "bold")
        )
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.analysis_text = tk.Text(
            analysis_frame,
            bg="#1C1C1C",
            fg="#00FF00",
            font=("Courier", 9),
            height=12,
            wrap=tk.WORD
        )
        self.analysis_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ===== PRAWA STRONA =====
        
        # Sekcja: Konfiguracja generowania
        config_frame = tk.LabelFrame(
            right_panel,
            text="3️⃣ Konfiguracja wariantów",
            bg="#3D5A3D",
            fg="white",
            font=("Arial", 12, "bold")
        )
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Liczba wariantów
        tk.Label(
            config_frame,
            text="Liczba wariantów:",
            bg="#3D5A3D",
            fg="white",
            font=("Arial", 10)
        ).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.variant_count_var = tk.IntVar(value=4)
        tk.Spinbox(
            config_frame,
            from_=1,
            to=12,
            textvariable=self.variant_count_var,
            width=10,
            font=("Arial", 10)
        ).grid(row=0, column=1, padx=10, pady=5)
        
        # Styl architektoniczny
        tk.Label(
            config_frame,
            text="Style do wygenerowania:",
            bg="#3D5A3D",
            fg="white",
            font=("Arial", 10)
        ).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.style_vars = {}
        styles_subframe = tk.Frame(config_frame, bg="#3D5A3D")
        styles_subframe.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=10)
        
        for style_key, style_data in STYLE_VARIANTS.items():
            var = tk.BooleanVar(value=True)
            self.style_vars[style_key] = var
            tk.Checkbutton(
                styles_subframe,
                text=style_data["name"],
                variable=var,
                bg="#3D5A3D",
                fg="white",
                selectcolor="#556B2F",
                font=("Arial", 9)
            ).pack(anchor=tk.W)
        
        # Opcje dodatkowe
        tk.Label(
            config_frame,
            text="Opcje transformacji:",
            bg="#3D5A3D",
            fg="white",
            font=("Arial", 10)
        ).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        
        options_subframe = tk.Frame(config_frame, bg="#3D5A3D")
        options_subframe.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=10)
        
        self.flip_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_subframe,
            text="Odbicia lustrzane",
            variable=self.flip_var,
            bg="#3D5A3D",
            fg="white",
            selectcolor="#556B2F"
        ).pack(anchor=tk.W)
        
        self.weathering_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            options_subframe,
            text="Efekt starzenia",
            variable=self.weathering_var,
            bg="#3D5A3D",
            fg="white",
            selectcolor="#556B2F"
        ).pack(anchor=tk.W)
        
        # PRZYCISK GENEROWANIA
        tk.Button(
            config_frame,
            text="🎨 GENERUJ WARIANTY",
            command=self.generate_variants,
            bg="#228B22",
            fg="white",
            font=("Arial", 14, "bold"),
            padx=30,
            pady=15
        ).grid(row=3, column=0, columnspan=3, pady=20)
        
        # Sekcja: Podgląd wygenerowanych
        preview_frame = tk.LabelFrame(
            right_panel,
            text="4️⃣ Wygenerowane warianty",
            bg="#3D5A3D",
            fg="white",
            font=("Arial", 12, "bold")
        )
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas z przewijaniem
        canvas_container = tk.Frame(preview_frame, bg="#2F4F2F")
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        v_scrollbar = tk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.variants_canvas = tk.Canvas(
            canvas_container,
            bg="#2F4F2F",
            yscrollcommand=v_scrollbar.set
        )
        self.variants_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.config(command=self.variants_canvas.yview)
        
        self.variants_frame = tk.Frame(self.variants_canvas, bg="#2F4F2F")
        self.variants_canvas.create_window((0, 0), window=self.variants_frame, anchor=tk.NW)
        
        self.variants_frame.bind("<Configure>", 
            lambda e: self.variants_canvas.configure(scrollregion=self.variants_canvas.bbox("all")))
        
        # Przyciski akcji
        action_frame = tk.Frame(right_panel, bg="#3D5A3D")
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            action_frame,
            text="✅ EKSPORTUJ WYBRANE",
            command=self.export_selected_variants,
            bg="#228B22",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            action_frame,
            text="💾 Zapisz wszystkie",
            command=self.save_all_variants,
            bg="#4682B4",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            action_frame,
            text="🗑️ Wyczyść",
            command=self.clear_variants,
            bg="#DC143C",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Gotowy. Wybierz budynek referencyjny.",
            bg="#1C1C1C",
            fg="#00FF00",
            font=("Courier", 10),
            anchor=tk.W,
            padx=10
        )
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Ustaw domyślny tryb
        self.on_mode_changed()
    
    def on_mode_changed(self):
        """Handler zmiany trybu generowania"""
        mode = self.generation_mode_var.get()
        
        if mode == "new":
            # Pokaż wybór typu budynku, ukryj referencje
            self.building_type_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.ref_frame.pack_forget()
            self.status_label.config(text="🏗️ Tryb: Generowanie NOWYCH budynków przez Imagen 3")
        else:
            # Pokaż referencje, ukryj wybór typu
            self.ref_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.building_type_frame.pack_forget()
            self.status_label.config(text="🎨 Tryb: Warianty istniejących budynków")
    
    def on_building_type_selected(self, event):
        """Handler wyboru typu budynku"""
        selection = self.building_type_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        building_key = list(BUILDING_TYPES.keys())[idx]
        self.current_building_type = building_key
        
        # Pokaż prompt dla tego typu
        prompt = BUILDING_PROMPTS.get(building_key, "Brak opisu")
        self.type_description_label.config(text=f"📝 {prompt}")
        
        self.status_label.config(text=f"Wybrano typ: {BUILDING_TYPES[building_key]['name']}")
    
    def on_reference_selected(self, event):
        """Handler wyboru budynku referencyjnego"""
        selection = self.ref_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        self.current_reference = self.reference_buildings[idx]
        
        # Pokaż podgląd
        try:
            img = Image.open(self.current_reference)
            img.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(img)
            self.ref_preview_label.configure(image=photo, text="")
            self.ref_preview_label.image = photo
            
            self.status_label.config(text=f"Wybrano: {self.current_reference.name}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można załadować obrazu: {e}")
    
    def analyze_reference(self):
        """Analizuje wybrany budynek przez Gemini Vision"""
        if not self.current_reference:
            messagebox.showwarning("Uwaga", "Najpierw wybierz budynek referencyjny!")
            return
        
        self.status_label.config(text="🔍 Analizuję przez Gemini Vision...")
        self.root.update()
        
        try:
            # Wywołaj Gemini Vision API
            analysis = analyze_building_with_gemini(self.current_reference, GEMINI_API_KEY)
            self.current_analysis = analysis
            
            # Wyświetl wynik
            self.analysis_text.delete("1.0", tk.END)
            self.analysis_text.insert(tk.END, "═══ ANALIZA BUDYNKU ═══\n\n", "header")
            self.analysis_text.insert(tk.END, json.dumps(analysis, indent=2, ensure_ascii=False))
            
            self.status_label.config(text=f"✅ Analiza zakończona: {analysis.get('building_type', 'unknown')}")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd analizy: {e}")
            self.status_label.config(text=f"❌ Błąd analizy: {str(e)}")
    
    def generate_variants(self):
        """Generuje warianty budynku LUB nowe budynki (zależnie od trybu)"""
        mode = self.generation_mode_var.get()
        
        if mode == "new":
            # TRYB: Generowanie NOWYCH budynków
            self.generate_new_buildings()
        else:
            # TRYB: Warianty istniejących
            self.generate_building_variants()
    
    def generate_new_buildings(self):
        """Generuje NOWE budynki przez Imagen 3"""
        # Sprawdź wybór typu
        selection = self.building_type_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uwaga", "Najpierw wybierz typ budynku!")
            return
        
        idx = selection[0]
        building_key = list(BUILDING_TYPES.keys())[idx]
        building_name = BUILDING_TYPES[building_key]["name"]
        
        # Pobierz konfigurację
        num_variants = self.variant_count_var.get()
        selected_styles = [k for k, v in self.style_vars.items() if v.get()]
        
        if not selected_styles:
            messagebox.showwarning("Uwaga", "Wybierz przynajmniej jeden styl!")
            return
        
        # Wyczyść poprzednie
        self.clear_variants()
        
        self.status_label.config(text=f"🤖 Generuję {num_variants} budynków: {building_name}...")
        self.root.update()
        
        # Czy użyć obrazu referencyjnego (pierwszy na liście)?
        use_ref = len(self.reference_buildings) > 0 and self.variant_count_var.get() > 0
        reference_path = self.reference_buildings[0] if use_ref else None
        
        try:
            # Generuj budynki
            for i in range(num_variants):
                # Wybierz styl (rotacja przez wybrane)
                style = selected_styles[i % len(selected_styles)]
                
                self.status_label.config(text=f"🤖 Imagen 3: {building_name} [{style}] {i+1}/{num_variants}...")
                self.root.update()
                
                # Wywołaj Imagen 3
                variant_img = generate_with_imagen3(
                    building_type=building_key,
                    style=style,
                    reference_path=reference_path,
                    use_reference=use_ref
                )
                
                # Dodaj do podglądu
                if variant_img:
                    label = f"{building_key}_{style}_{i+1}"
                    self._add_variant_to_preview(variant_img, label, building_key, style)
                    self.generated_variants.append((variant_img, building_key, style, i+1))
                else:
                    print(f"⚠️  Nie udało się wygenerować wariantu {i+1}")
            
            self.status_label.config(text=f"✅ Wygenerowano {len(self.generated_variants)} budynków!")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd generowania: {e}")
            self.status_label.config(text=f"❌ Błąd: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def generate_building_variants(self):
        """Generuje WARIANTY istniejącego budynku (proceduralnie)"""
        if not self.current_reference:
            messagebox.showwarning("Uwaga", "Najpierw wybierz budynek referencyjny!")
            return
        
        # Pobierz konfigurację
        num_variants = self.variant_count_var.get()
        selected_styles = [k for k, v in self.style_vars.items() if v.get()]
        
        if not selected_styles:
            messagebox.showwarning("Uwaga", "Wybierz przynajmniej jeden styl!")
            return
        
        # Wyczyść poprzednie warianty
        self.clear_variants()
        
        self.status_label.config(text=f"🎨 Generuję {num_variants} wariantów...")
        self.root.update()
        
        try:
            reference_img = Image.open(self.current_reference)
            
            # Generuj warianty
            for i in range(num_variants):
                # Wybierz styl (rotacja przez wybrane)
                style = selected_styles[i % len(selected_styles)]
                
                self.status_label.config(text=f"🎨 Proceduralnie: Wariant {i+1}/{num_variants}...")
                self.root.update()
                
                variant_config = {
                    "style": style,
                    "flip": (i % 2 == 1) and self.flip_var.get(),
                    "weathering": 0.3 if self.weathering_var.get() else 0.0
                }
                variant_img = generate_building_variant(reference_img, variant_config)
                
                # Dodaj do podglądu
                if variant_img:
                    building_type = self.current_analysis.get('building_type', 'unknown') if self.current_analysis else 'unknown'
                    self._add_variant_to_preview(variant_img, f"{style}_{i+1}", building_type, style)
                    self.generated_variants.append((variant_img, style, i+1))
            
            self.status_label.config(text=f"✅ Wygenerowano {len(self.generated_variants)} wariantów")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd generowania: {e}")
            self.status_label.config(text=f"❌ Błąd: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _add_variant_to_preview(self, img: Image.Image, label: str, building_type: str = "unknown", style: str = "cegła"):
        """Dodaje wygenerowany wariant do podglądu z checkboxem"""
        # Kontener dla pojedynczego wariantu
        variant_container = tk.Frame(self.variants_frame, bg="#3D5A3D", relief=tk.RAISED, bd=2)
        variant_container.pack(fill=tk.X, padx=5, pady=5)
        
        # CHECKBOX DO WYBORU
        checkbox_var = tk.BooleanVar(value=False)
        checkbox = tk.Checkbutton(
            variant_container,
            text="",
            variable=checkbox_var,
            bg="#3D5A3D",
            selectcolor="#228B22",
            activebackground="#3D5A3D"
        )
        checkbox.pack(side=tk.LEFT, padx=5)
        
        # Zapisz checkbox do listy
        self.variant_checkboxes.append((checkbox_var, img, label, building_type, style))
        
        # Miniaturka
        thumbnail = img.copy()
        thumbnail.thumbnail((120, 120))
        photo = ImageTk.PhotoImage(thumbnail)
        
        img_label = tk.Label(variant_container, image=photo, bg="#2F4F2F")
        img_label.image = photo  # Zachowaj referencję
        img_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Info
        info_frame = tk.Frame(variant_container, bg="#3D5A3D")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(
            info_frame,
            text=f"🏗️ {BUILDING_TYPES.get(building_type, {}).get('name', building_type)} | {label}",
            bg="#3D5A3D",
            fg="white",
            font=("Arial", 11, "bold")
        ).pack(anchor=tk.W, pady=2)
        
        tk.Label(
            info_frame,
            text=f"Rozmiar: {img.size[0]}x{img.size[1]} px | Styl: {STYLE_VARIANTS.get(style, {}).get('name', style)}",
            bg="#3D5A3D",
            fg="#B0C4DE",
            font=("Arial", 9)
        ).pack(anchor=tk.W, pady=2)
    
    def generate_building_metadata(self, building_type: str, style: str, img: Image.Image) -> Dict:
        """Generuje JSON metadata dla budynku"""
        width, height = img.size
        
        # Collision box - zakładamy budynek zajmuje ~80% wymiarów
        collision_width = int(width * 0.8)
        collision_height = int(height * 0.8)
        
        metadata = {
            "type": "settlement_building",
            "building_type": building_type,
            "building_name": BUILDING_TYPES.get(building_type, {}).get("name", building_type),
            "style": style,
            "dimensions": {
                "width": width,
                "height": height
            },
            "collision_box": {
                "width": collision_width,
                "height": collision_height,
                "offset_x": (width - collision_width) // 2,
                "offset_y": (height - collision_height) // 2
            },
            "properties": {
                "passable": False,
                "blocks_vision": True,
                "destructible": True,
                "cover_value": 0.8 if building_type in ["koszary", "fabryka", "bank"] else 0.5
            },
            "generation": {
                "method": "vertex_ai_imagen3",
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "prompt_type": building_type
            }
        }
        
        return metadata
    
    def export_selected_variants(self):
        """Eksportuje wybrane warianty jako assety z JSON"""
        if not self.variant_checkboxes:
            messagebox.showwarning("Uwaga", "Brak wariantów do eksportu!")
            return
        
        # Zbierz zaznaczone
        selected = [
            (img, label, building_type, style) 
            for checkbox_var, img, label, building_type, style in self.variant_checkboxes 
            if checkbox_var.get()
        ]
        
        if not selected:
            messagebox.showwarning("Uwaga", "Nie zaznaczono żadnych wariantów!\n\nUżyj checkboxów aby wybrać które budynki eksportować.")
            return
        
        try:
            exported_count = 0
            
            for img, label, building_type, style in selected:
                # Generuj nazwę pliku
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename_base = f"{building_type}_{style}_{timestamp}_{exported_count}"
                
                # Zapisz PNG
                png_path = OUTPUT_DIR / f"{filename_base}.png"
                img.save(png_path)
                
                # Generuj i zapisz JSON
                metadata = self.generate_building_metadata(building_type, style, img)
                json_path = OUTPUT_DIR / f"{filename_base}.json"
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Eksportowano: {filename_base}")
                exported_count += 1
            
            messagebox.showinfo(
                "Sukces", 
                f"✅ Wyeksportowano {exported_count} budynków!\n\nLokalizacja:\n{OUTPUT_DIR}\n\nKażdy budynek ma:\n- .png (obraz 64x64)\n- .json (metadata)"
            )
            
            self.status_label.config(text=f"✅ Wyeksportowano {exported_count} budynków do {OUTPUT_DIR.name}/")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd eksportu: {e}")
            import traceback
            traceback.print_exc()
    
    def save_all_variants(self):
        """Zapisuje wszystkie wygenerowane warianty"""
        if not self.generated_variants:
            messagebox.showwarning("Uwaga", "Brak wariantów do zapisania!")
            return
        
        # Zapytaj o prefix nazwy
        prefix = self.current_reference.stem if self.current_reference else "building"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        saved_count = 0
        for i, variant_data in enumerate(self.generated_variants):
            # Obsługa obu formatów: (img, style, num) lub (img, building, style, num)
            if len(variant_data) == 3:
                img, style, variant_num = variant_data
                building_type = "variant"
            else:
                img, building_type, style, variant_num = variant_data
            
            filename = f"{prefix}_{building_type}_{style}_v{variant_num}_{timestamp}.png"
            output_path = OUTPUT_DIR / filename
            
            try:
                img.save(output_path)
                saved_count += 1
                print(f"✅ Zapisano: {filename}")
            except Exception as e:
                print(f"❌ Błąd zapisu {filename}: {e}")
        
        messagebox.showinfo(
            "Zapisano",
            f"Zapisano {saved_count}/{len(self.generated_variants)} budynków\n\n"
            f"Lokalizacja:\n{OUTPUT_DIR}"
        )
        self.status_label.config(text=f"💾 Zapisano {saved_count} budynków do {OUTPUT_DIR.name}/")
    
    def clear_variants(self):
        """Czyści wygenerowane warianty"""
        for widget in self.variants_frame.winfo_children():
            widget.destroy()
        self.generated_variants.clear()
        self.variant_checkboxes.clear()
        self.status_label.config(text="🗑️ Wyczyszczono warianty")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Uruchamia aplikację"""
    root = tk.Tk()
    app = SettlementGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
