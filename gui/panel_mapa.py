import tkinter as tk
from tkinter import ttk, simpledialog
from engine.hex_utils import get_hex_vertices
from PIL import Image, ImageTk
import os
import math
from pathlib import Path

ASSETS_ROOT = Path(__file__).resolve().parent.parent / "assets"

class PanelMapa(tk.Frame):
    def __init__(self, parent, game_engine, bg_path: str, player_nation: str, width=800, height=600, token_info_panel=None, panel_dowodcy=None):
        super().__init__(parent)
        self.game_engine = game_engine
        self.map_model = self.game_engine.board
        self.player_nation = player_nation
        self.tokens = self.game_engine.tokens
        self.token_info_panel = token_info_panel
        self.panel_dowodcy = panel_dowodcy  # <--- dodane
          # Przechowywanie informacji o aktywnym dowódcy dla przezroczystości
        self.active_commander_id = None
        
        # Inicjalizacja ścieżki ruchu (zapobiega błędowi AttributeError)
        self.current_path = None

        # Canvas + Scrollbary
        self.canvas = tk.Canvas(self, width=width, height=height)
        hbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        vbar = tk.Scrollbar(self, orient="vertical",   command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        hbar.grid(row=1, column=0, sticky="ew")
        vbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Nakładka przyciemnienia zależna od pory dnia (inicjalizacja w __init__)
        self._daylight_overlay_id = None
        self._current_phase_for_overlay = None

        # Cache na tekstury terenu (musi istnieć zanim narysujemy siatkę)
        self._terrain_texture_cache: dict[tuple[str, int], ImageTk.PhotoImage] = {}

    # tło mapy - preferuj meta z pliku mapy, w przeciwnym razie zachowuj się jak wcześniej
        self._bg = None
        resolved_background = self._resolve_background(bg_path, width, height)
        if resolved_background is not None:
            self._bg = ImageTk.PhotoImage(resolved_background["image"])
            self.canvas.create_image(0, 0, anchor="nw", image=self._bg)
            self.canvas.config(scrollregion=(0, 0, resolved_background["width"], resolved_background["height"]))
            self._bg_width = resolved_background["width"]
            self._bg_height = resolved_background["height"]
        else:
            self._bg_width = width
            self._bg_height = height
            self.canvas.config(scrollregion=(0, 0, width, height))

        # rysuj siatkę i etykiety
        self._draw_hex_grid()

        # kliknięcia
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-3>", self._on_right_click_token)

        # żetony
        self.token_images = {}
        # mapowanie token_id -> canvas item id (dla markerów statusu ruchu)
        self._token_canvas_items = {}
        # markery statusu ruchu (token_id -> marker canvas id)
        self._move_status_markers = {}
        # tooltip token info
        self.active_tooltip = None
        self._draw_tokens_on_map()
        # Aktywuj podgląd hover dla generała i dowódców jeśli dostępny player w silniku
        try:
            if hasattr(self.game_engine, 'current_player_obj') and getattr(self.game_engine.current_player_obj, 'role', None) in ('Generał', 'Dowódca'):
                self.player = self.game_engine.current_player_obj
                # Przekaż player do token_info_panel dla detection_level
                if self.token_info_panel and hasattr(self.token_info_panel, 'set_player'):
                    self.token_info_panel.set_player(self.player)
                self._setup_hover_binding()
        except Exception:
            pass

    def _ensure_daylight_overlay_top(self):
        """Utrzymuje nakładkę przyciemnienia nad innymi elementami Canvas."""
        if self._daylight_overlay_id is not None:
            try:
                self.canvas.tag_raise(self._daylight_overlay_id)
            except Exception:
                pass

    def update_daylight_overlay(self, phase: str | None):
        """Aktualizuje nakładkę przyciemniającą mapę zależnie od pory dnia.

        phase: 'rano' | 'dzień' | 'wieczór' | 'noc' (inne wartości wyłączają przyciemnienie)
        """
        try:
            # Jeśli nic się nie zmieniło – tylko upewnij się, że nakładka jest na wierzchu
            if phase == self._current_phase_for_overlay and self._daylight_overlay_id is not None:
                self._ensure_daylight_overlay_top()
                return

            # Usuń poprzednią nakładkę
            if self._daylight_overlay_id is not None:
                try:
                    self.canvas.delete(self._daylight_overlay_id)
                except Exception:
                    pass
                self._daylight_overlay_id = None

            self._current_phase_for_overlay = phase

            # Mapowanie pory dnia na stopień przyciemnienia (stipple)
            # Uwaga: Canvas nie wspiera alfa dla figur – używamy wzorków (stipple)
            stipple = None
            fill_color = "#000000"
            if phase in ("rano", "dzień"):
                stipple = None  # brak nakładki
            elif phase == "wieczór":
                stipple = "gray25"   # delikatne przyciemnienie
            elif phase == "noc":
                stipple = "gray50"   # wyraźniejsze przyciemnienie
            else:
                stipple = None

            if stipple is None:
                # Bez nakładki
                return

            # Wymiary płótna odpowiadające całej mapie (scrollregion)
            w = getattr(self, "_bg_width", self.canvas.winfo_width() or 800)
            h = getattr(self, "_bg_height", self.canvas.winfo_height() or 600)

            self._daylight_overlay_id = self.canvas.create_rectangle(
                0, 0, w, h,
                fill=fill_color,
                outline="",
                stipple=stipple,
                tags=("daylight_overlay",)
            )
            self._ensure_daylight_overlay_top()
        except Exception:
            # Bezpieczny fallback – brak przyciemnienia
            pass

    def set_active_commander(self, commander_id):
        """Ustawia aktywnego dowódcę dla efektu przezroczystości żetonów"""
        self.active_commander_id = commander_id
        self._draw_tokens_on_map()  # Odśwież wyświetlanie żetonów

    def _get_token_commander_id(self, token):
        """Pobiera ID dowódcy z ownera żetonu (format: 'ID (Nation)')"""
        if hasattr(token, 'owner') and token.owner:
            # Format ownera: "2 (Polska)" -> zwraca "2"
            return token.owner.split(' ')[0]
        return None

    def center_on_player_tokens(self):
        """Centruje mapę na środku wszystkich jednostek aktualnego gracza"""
        if not hasattr(self, 'player') or not self.player:
            return
        
        # Znajdź wszystkie jednostki gracza
        player_tokens = []
        expected_owner = f"{self.player.id} ({self.player.nation})"
        
        for token in self.tokens:
            if hasattr(token, 'owner') and token.owner == expected_owner:
                if token.q is not None and token.r is not None:
                    player_tokens.append(token)
        
        if not player_tokens:
            return  # Brak jednostek do wycentrowania
        
        # Oblicz środek wszystkich jednostek
        avg_q = sum(token.q for token in player_tokens) / len(player_tokens)
        avg_r = sum(token.r for token in player_tokens) / len(player_tokens)
        
        # Przelicz na współrzędne pikseli
        center_x, center_y = self.map_model.hex_to_pixel(avg_q, avg_r)
        
        # Pobierz rozmiary canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return  # Canvas nie jest jeszcze gotowy
        
        # Oblicz pozycję scroll aby wycentrować
        scroll_x = (center_x - canvas_width / 2) / self._bg_width
        scroll_y = (center_y - canvas_height / 2) / self._bg_height
        
        # Ogranicz do zakresu 0.0 - 1.0
        scroll_x = max(0.0, min(1.0, scroll_x))
        scroll_y = max(0.0, min(1.0, scroll_y))
        
        # Przewiń mapę
        self.canvas.xview_moveto(scroll_x)
        self.canvas.yview_moveto(scroll_y)

    def center_on_nation_tokens(self, nation: str):
        """Centruje mapę na geometrycznym środku WSZYSTKICH jednostek danej nacji (nie tylko aktualnego gracza).

        Używane dla generała aby objąć żetony wszystkich jego dowódców.
        """
        if not nation:
            return
        nation_tokens = []
        # Szukamy po owner (format: "<id> (Nacja)") oraz po stats['nation'] jako fallback
        marker = f"({nation})"
        for token in self.tokens:
            if token.q is None or token.r is None:
                continue
            try:
                owner_ok = (hasattr(token, 'owner') and token.owner.endswith(marker))
            except Exception:
                owner_ok = False
            nation_ok = False
            try:
                nation_ok = (token.stats.get('nation') == nation)
            except Exception:
                pass
            if owner_ok or nation_ok:
                nation_tokens.append(token)
        if not nation_tokens:
            return
        avg_q = sum(t.q for t in nation_tokens) / len(nation_tokens)
        avg_r = sum(t.r for t in nation_tokens) / len(nation_tokens)
        center_x, center_y = self.map_model.hex_to_pixel(avg_q, avg_r)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return
        scroll_x = (center_x - canvas_width / 2) / self._bg_width
        scroll_y = (center_y - canvas_height / 2) / self._bg_height
        scroll_x = max(0.0, min(1.0, scroll_x))
        scroll_y = max(0.0, min(1.0, scroll_y))
        self.canvas.xview_moveto(scroll_x)
        self.canvas.yview_moveto(scroll_y)

    def center_on_commander_token(self, commander_id: str, nation: str):
        """Centruje mapę na środku wszystkich jednostek przypisanych do konkretnego dowódcy (po prefiksie ownera)."""
        if not commander_id:
            return
        commander_tokens = []
        marker_suffix = f"({nation})" if nation else ''
        prefix = f"{commander_id} "  # owner zwykle: '2 (Polska)'
        for token in self.tokens:
            if token.q is None or token.r is None:
                continue
            if hasattr(token, 'owner') and token.owner.startswith(prefix):
                if marker_suffix and not token.owner.endswith(marker_suffix):
                    continue
                commander_tokens.append(token)
        if not commander_tokens:
            return
        avg_q = sum(t.q for t in commander_tokens) / len(commander_tokens)
        avg_r = sum(t.r for t in commander_tokens) / len(commander_tokens)
        center_x, center_y = self.map_model.hex_to_pixel(avg_q, avg_r)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return
        scroll_x = (center_x - canvas_width / 2) / self._bg_width
        scroll_y = (center_y - canvas_height / 2) / self._bg_height
        scroll_x = max(0.0, min(1.0, scroll_x))
        scroll_y = max(0.0, min(1.0, scroll_y))
        self.canvas.xview_moveto(scroll_x)
        self.canvas.yview_moveto(scroll_y)

    def _sync_player_from_engine(self):
        """Synchronizuje self.player z aktualnym obiektem gracza z silnika gry."""
        if hasattr(self.game_engine, 'current_player_obj'):
            self.player = self.game_engine.current_player_obj
            # Przekaż player do token_info_panel dla detection_level
            if self.token_info_panel and hasattr(self.token_info_panel, 'set_player'):
                self.token_info_panel.set_player(self.player)

    def _draw_hex_grid(self):
        self._sync_player_from_engine()
        self.canvas.delete("hex")
        self.canvas.delete("fog")
        self.canvas.delete("spawn_overlay")  # Usuwamy stare nakładki spawnów
        self.canvas.delete("terrain_texture")
        s = self.map_model.hex_size
        visible_hexes = set()
        if hasattr(self, 'player') and hasattr(self.player, 'visible_hexes'):
            visible_hexes = set((int(q), int(r)) for q, r in self.player.visible_hexes)
        # Dodaj tymczasową widoczność (odkryte w tej turze)
        if hasattr(self.player, 'temp_visible_hexes'):
            visible_hexes |= set((int(q), int(r)) for q, r in self.player.temp_visible_hexes)
        fogged = []
        for key, tile in self.map_model.terrain.items():
            if isinstance(key, tuple) and len(key) == 2:
                q, r = key
            else:
                q, r = map(int, str(key).split(','))
            cx, cy = self.map_model.hex_to_pixel(q, r)
            if 0 <= cx <= self._bg_width and 0 <= cy <= self._bg_height:
                if (int(q), int(r)) not in visible_hexes:
                    fogged.append((int(q), int(r)))
        # --- PODŚWIETLANIE SPAWNÓW ---
        spawn_colors = {
            'Polska': '#ff5555',   # półprzezroczysty czerwony
            'Niemcy': '#5555ff',   # półprzezroczysty niebieski
        }
        spawn_points = getattr(self.map_model, 'spawn_points', {})
        for nation, hex_list in spawn_points.items():
            color = spawn_colors.get(nation, '#cccccc')
            for hex_id in hex_list:
                if ',' in hex_id:
                    try:
                        q, r = map(int, hex_id.split(','))
                    except Exception:
                        continue
                else:
                    continue
                cx, cy = self.map_model.hex_to_pixel(q, r)
                verts = get_hex_vertices(cx, cy, s)
                flat = [coord for p in verts for coord in p]
                self.canvas.create_polygon(
                    flat,
                    fill=color,
                    outline='',
                    stipple='gray25',
                    tags='spawn_overlay'
                )
        for key, tile in self.map_model.terrain.items():
            # Obsługa kluczy tuple (q, r) lub string "q,r"
            if isinstance(key, tuple) and len(key) == 2:
                q, r = int(key[0]), int(key[1])
            else:
                q, r = map(int, str(key).split(','))
            cx, cy = self.map_model.hex_to_pixel(q, r)
            if 0 <= cx <= self._bg_width and 0 <= cy <= self._bg_height:
                texture_photo = self._get_terrain_texture_photo(getattr(tile, "texture", None))
                if texture_photo:
                    self.canvas.create_image(
                        cx,
                        cy,
                        image=texture_photo,
                        anchor="center",
                        tags=("terrain_texture",)
                    )
                verts = get_hex_vertices(cx, cy, s)
                flat = [coord for p in verts for coord in p]
                self.canvas.create_polygon(
                    flat,
                    outline="red",
                    fill="",
                    width=1,
                    tags="hex"
                )
                # Rysuj mgiełkę tylko jeśli (q, r) nie jest w visible_hexes (upewnij się, że tuple intów)
                if (q, r) not in visible_hexes:
                    self.canvas.create_polygon(
                        flat,
                        fill="#222222",
                        stipple="gray50",
                        outline="",
                        tags="fog"
                    )
        # --- PODŚWIETLANIE PUNKTÓW SPECJALNYCH (mosty, miasta, fortyfikacje, węzły) ---
        key_points = getattr(self.map_model, 'key_points', {})
        special_types = {'most', 'miasto', 'fortyfikacja', 'węzeł komunikacyjny'}
        for hex_id, point_type in key_points.items():
            # point_type to dict, np. {'type': 'miasto', 'value': 100}
            type_str = point_type.get('type', '').lower() if isinstance(point_type, dict) else str(point_type).lower()
            if type_str in special_types:
                if isinstance(hex_id, tuple) and len(hex_id) == 2:
                    q, r = int(hex_id[0]), int(hex_id[1])
                else:
                    q, r = map(int, str(hex_id).split(','))
                cx, cy = self.map_model.hex_to_pixel(q, r)
                if 0 <= cx <= self._bg_width and 0 <= cy <= self._bg_height:
                    verts = get_hex_vertices(cx, cy, s)
                    flat = [coord for p in verts for coord in p]
                    # Bardzo delikatna zielona mgiełka (jasna, półprzezroczysta, lekki wzorek)
                    self.canvas.create_polygon(
                        flat,
                        fill='#b6ffb6',  # bardzo jasna zieleń
                        outline='',
                        stipple='gray25',  # bardzo delikatna mgiełka
                        tags='special_point_overlay'
                    )
        # Po narysowaniu siatki upewnij się, że nakładka dnia/nocy jest na wierzchu
        self._ensure_daylight_overlay_top()

    def _resolve_background(self, fallback_path: str, fallback_width: int, fallback_height: int):
        """Zwraca słownik z kluczami image/width/height na podstawie metadanych mapy."""
        meta = getattr(self.map_model, "background_meta", {})
        assets_root = Path(__file__).resolve().parent.parent / "assets"

        def build_solid(color_rgb, w, h):
            image = Image.new("RGB", (w, h), tuple(color_rgb))
            return {"image": image, "width": w, "height": h}

        def estimate_size(cols, rows, hex_size):
            horizontal_spacing = 1.5 * hex_size
            width = int(hex_size * 2 + max(0, cols - 1) * horizontal_spacing + hex_size)
            hex_height = math.sqrt(3) * hex_size
            height = int((math.sqrt(3) / 2) * hex_size + rows * hex_height + hex_size)
            return max(200, width), max(200, height)

        if isinstance(meta, dict) and meta:
            bg_type = meta.get("type")
            if bg_type == "image":
                raw_path = meta.get("path")
                if raw_path:
                    candidate = Path(raw_path)
                    if not candidate.is_absolute():
                        candidate = assets_root / raw_path
                    if candidate.exists():
                        img = Image.open(candidate)
                        return {"image": img, "width": img.width, "height": img.height}
            elif bg_type == "solid":
                color = meta.get("color", [48, 64, 40])
                width = meta.get("width")
                height = meta.get("height")
                if not width or not height:
                    width, height = estimate_size(self.map_model.cols, self.map_model.rows, self.map_model.hex_size)
                return build_solid(color, int(width), int(height))

        # fallback: użyj przekazanego bg_path jeśli istnieje
        if fallback_path and os.path.exists(fallback_path):
            img = Image.open(fallback_path)
            return {"image": img, "width": img.width, "height": img.height}

        # ostatecznie: solid default w oparciu o rozmiar mapy
        width, height = estimate_size(self.map_model.cols, self.map_model.rows, self.map_model.hex_size)
        return build_solid([48, 64, 40], width, height)

    def _get_terrain_texture_photo(self, texture_rel: str | None):
        if not texture_rel:
            return None
        normalized = texture_rel.replace("\\", "/")
        cache_key = (normalized, self.map_model.hex_size)
        if cache_key in self._terrain_texture_cache:
            return self._terrain_texture_cache[cache_key]
        texture_path = ASSETS_ROOT / normalized
        if not texture_path.exists():
            return None
        try:
            img = Image.open(texture_path).convert("RGBA")
            target_size = int(self.map_model.hex_size * 2)
            if target_size <= 0:
                return None
            img = img.resize((target_size, target_size), Image.NEAREST)
            photo = ImageTk.PhotoImage(img)
            self._terrain_texture_cache[cache_key] = photo
            return photo
        except Exception:
            return None

    def _draw_tokens_on_map(self):
        self._sync_player_from_engine()
        self.tokens = self.game_engine.tokens  # Zawsze aktualizuj listę żetonów
        self.canvas.delete("token")
        self.canvas.delete("token_sel")  # Usuwamy stare obwódki        # Filtrowanie widoczności żetonów przez fog of war (uwzględnij temp_visible_tokens)
        # Usuń stare markery statusu
        try:
            for mid in self._move_status_markers.values():
                self.canvas.delete(mid)
        except Exception:
            pass
        self._move_status_markers = {}
        self._token_canvas_items = {}
        tokens = self.tokens
        if hasattr(self, 'player') and hasattr(self.player, 'visible_tokens') and hasattr(self.player, 'temp_visible_tokens'):
            tokens = [t for t in self.tokens if t.id in (self.player.visible_tokens | self.player.temp_visible_tokens)]
        elif hasattr(self, 'player') and hasattr(self.player, 'visible_tokens'):
            tokens = [t for t in self.tokens if t.id in self.player.visible_tokens]
        for token in tokens:
            # USUNIĘTO DEBUGI
            if token.q is not None and token.r is not None:
                # Określ ścieżkę do obrazu na podstawie detection_level dla wrogów
                img_path = self._get_token_image_path(token)
                if not img_path:
                    continue
                try:
                    img = Image.open(img_path)
                    # SKALOWANIE ŻETONÓW: bazowo 40x40; lekkie powiększenie o ~10% (wcześniej 30%).
                    # Aby zmienić globalnie: dostosuj TOKEN_SIZE_FACTOR albo BASE_TOKEN_SIZE poniżej.
                    BASE_TOKEN_SIZE = 40
                    TOKEN_SIZE_FACTOR = 1.1  # 10% większe (BYŁO 1.3)
                    hex_size = int(round(BASE_TOKEN_SIZE * TOKEN_SIZE_FACTOR))
                    img = img.resize((hex_size, hex_size), Image.LANCZOS)
                    
                    # Zastosuj przezroczystość dla nieaktywnych żetonów
                    if self.active_commander_id is not None:
                        token_commander_id = self._get_token_commander_id(token)
                        if token_commander_id != self.active_commander_id:
                            # Żeton nieaktywnego dowódcy - zmniejsz przezroczystość
                            img = img.convert("RGBA")
                            alpha = img.split()[-1]  # Pobierz kanał alfa
                            alpha = alpha.point(lambda p: int(p * 0.4))  # 40% przezroczystości
                            img.putalpha(alpha)
                    
                    # Zastosuj przezroczystość na podstawie detection_level dla tokenów wroga
                    if hasattr(self, 'player') and hasattr(token, 'owner'):
                        player_nation = getattr(self.player, 'nation', '')
                        token_nation = token.stats.get('nation', '')
                        
                        if player_nation and token_nation and player_nation != token_nation:
                            # To jest token wroga - sprawdź detection_level
                            detection_level = 1.0  # Domyślnie pełna widoczność
                            
                            if hasattr(self.player, 'temp_visible_token_data'):
                                token_data = self.player.temp_visible_token_data.get(token.id, {})
                                detection_level = token_data.get('detection_level', 0.0)
                            
                            # Zastosuj przezroczystość na podstawie detection_level
                            if detection_level < 1.0:
                                img = img.convert("RGBA")
                                alpha = img.split()[-1]  # Pobierz kanał alfa
                                # Przezroczystość: 0.4-1.0 na podstawie detection_level
                                opacity = 0.4 + (detection_level * 0.6)
                                alpha = alpha.point(lambda p: int(p * opacity))
                                img.putalpha(alpha)
                    
                    tk_img = ImageTk.PhotoImage(img)
                    x, y = self.map_model.hex_to_pixel(token.q, token.r)
                    img_item = self.canvas.create_image(x, y, image=tk_img, anchor="center", tags=("token", f"token_{token.id}"))
                    self.token_images[token.id] = tk_img
                    self._token_canvas_items[token.id] = img_item
                    # --- USUNIĘTO: wyświetlanie parametrów tekstowych na żetonie ---
                    # Obwódka zależna od trybu ruchu
                    border_color = "yellow"  # domyślnie bojowy
                    if hasattr(token, 'movement_mode'):
                        if token.movement_mode == 'combat':
                            border_color = "yellow"  # bojowy
                        elif token.movement_mode == 'march':
                            border_color = "limegreen"  # marsz
                        elif token.movement_mode == 'recon':
                            border_color = "red"  # zwiad
                    if hasattr(self, 'selected_token_id') and token.id == self.selected_token_id:
                        verts = get_hex_vertices(x, y, hex_size)
                        flat = [coord for p in verts for coord in p]
                        self.canvas.create_polygon(
                            flat,
                            outline=border_color,
                            width=2,
                            fill="",
                            tags="token_sel"
                        )
                except Exception as e:
                    pass  # USUNIĘTO DEBUGI
        # Kod spełnia wymagania: synchronizacja żetonów, tagowanie, poprawna mgiełka i widoczność.
        # Po narysowaniu żetonów zaktualizuj markery statusu ruchu
        self._refresh_move_status_markers()
        # Upewnij się, że nakładka dnia/nocy pozostaje na wierzchu
        self._ensure_daylight_overlay_top()

    def _get_token_image_path(self, token):
        """Zwraca ścieżkę do obrazu tokena z uwzględnieniem detection_level dla wrogów"""
        # Sprawdź czy to token wroga
        if hasattr(self, 'player') and hasattr(token, 'owner'):
            player_nation = getattr(self.player, 'nation', '')
            token_nation = token.stats.get('nation', '')
            
            if player_nation and token_nation and player_nation != token_nation:
                # To jest token wroga - sprawdź detection_level
                detection_level = 1.0
                
                if hasattr(self.player, 'temp_visible_token_data'):
                    token_data = self.player.temp_visible_token_data.get(token.id, {})
                    detection_level = token_data.get('detection_level', 0.0)
                
                # Wybierz odpowiednią ikonę na podstawie detection_level
                if detection_level >= 0.8:
                    # Pełna identyfikacja - standardowa ikona
                    pass  # Użyj standardowej logiki poniżej
                elif detection_level >= 0.5:
                    # Częściowa identyfikacja - generyczna ikona kategorii
                    unit_type = token.stats.get('type', 'unknown')
                    if 'tank' in unit_type.lower():
                        generic_path = "assets/tokens/generic/tank_contact.png"
                    elif 'infantry' in unit_type.lower():
                        generic_path = "assets/tokens/generic/infantry_contact.png"
                    elif 'artillery' in unit_type.lower():
                        generic_path = "assets/tokens/generic/artillery_contact.png"
                    else:
                        generic_path = "assets/tokens/generic/unknown_contact.png"
                    
                    if os.path.exists(generic_path):
                        return generic_path
                else:
                    # Minimalna informacja - ikona nieznany kontakt
                    unknown_path = "assets/tokens/generic/unknown_contact.png"
                    if os.path.exists(unknown_path):
                        return unknown_path
        
        # Standardowa logika dla własnych tokenów lub pełnej detekcji
        img_path = token.stats.get("image")
        if not img_path:
            nation = token.stats.get('nation', '')
            img_path = f"assets/tokens/{nation}/{token.id}/token.png"
        if not os.path.exists(img_path):
            img_path = "assets/tokens/default/token.png" if os.path.exists("assets/tokens/default/token.png") else None
        
        return img_path

    def _refresh_move_status_markers(self):
        """WYŁĄCZONE: nie rysuj kropek statusu ruchu. Czyść tylko ewentualne stare markery."""
        try:
            # Usuń markery z canvasu po tagu i wyczyść mapę id->marker
            self.canvas.delete('move_status')
        except Exception:
            pass
        try:
            self.canvas.delete('move_tip')
        except Exception:
            pass
        self._move_status_markers = {}
        # No-op: marker drawing disabled

    def _draw_path_on_map(self):
        if self.current_path:
            coords = []
            for q, r in self.current_path:
                x, y = self.map_model.hex_to_pixel(q, r)
                coords.append((x, y))
            if len(coords) > 1:
                for i in range(len(coords)-1):
                    self.canvas.create_line(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1], fill='blue', width=4, tags='path')

    def refresh(self):
        self.canvas.delete('path')
        self._sync_player_from_engine()
        self._draw_hex_grid()
        self._draw_tokens_on_map()
        self._draw_path_on_map()
        # Po odświeżeniu aktualizujemy ewentualny podgląd hover
        if getattr(self, 'last_hover_token_id', None) and self.token_info_panel:
            tok = next((t for t in self.tokens if t.id == self.last_hover_token_id), None)
            if tok:
                try:
                    self.token_info_panel.show_token(tok)
                except Exception:
                    pass

    def _setup_hover_binding(self):
        # Jednorazowe podłączenie zdarzenia ruchu myszy
        if not hasattr(self, '_hover_bound'):
            self.canvas.bind('<Motion>', self._on_mouse_move)
            self._hover_bound = True

    def _on_mouse_move(self, event):
        # Podgląd tylko dla ról kontrolujących (Generał lub Dowódca)
        if not (hasattr(self, 'player') and getattr(self.player, 'role', None) in ('Generał', 'Dowódca')):
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # znajdź żeton pod kursorem (widoczny dla gracza zgodnie z widocznością)
        hovered = None
        for token in self.tokens:
            if token.q is None or token.r is None:
                continue
            # Zachowujemy regułę widocznych tokenów jeśli zdefiniowane
            visible_ids = set()
            if hasattr(self.player, 'visible_tokens') and hasattr(self.player, 'temp_visible_tokens'):
                visible_ids = self.player.visible_tokens | self.player.temp_visible_tokens
            elif hasattr(self.player, 'visible_tokens'):
                visible_ids = self.player.visible_tokens
            if visible_ids and token.id not in visible_ids:
                continue
            tx, ty = self.map_model.hex_to_pixel(token.q, token.r)
            if abs(x - tx) < self.map_model.hex_size // 2 and abs(y - ty) < self.map_model.hex_size // 2:
                hovered = token
                break
        
        # Nowy system tooltip - pokazuj tooltip tylko gdy mysz jest na żetonie
        if hovered and hovered.id != getattr(self, 'last_hover_token_id', None):
            self.last_hover_token_id = hovered.id
            
            # Zniszcz poprzedni tooltip jeśli istnieje
            if hasattr(self, 'active_tooltip') and self.active_tooltip:
                try:
                    self.active_tooltip.destroy()
                except:
                    pass
            
            # Utwórz nowy tooltip - pozycja względem ekranu
            screen_x = event.x_root
            screen_y = event.y_root
            
            try:
                from gui.tooltip_token_info import TooltipTokenInfo
                self.active_tooltip = TooltipTokenInfo(
                    parent=self.winfo_toplevel(),
                    token=hovered,
                    player=self.player,
                    x=screen_x,
                    y=screen_y
                )
            except Exception as e:
                print(f"Błąd tworzenia tooltip: {e}")
                
        elif hovered is None and getattr(self, 'last_hover_token_id', None) is not None:
            # Opuściliśmy żeton - natychmiast zniszcz tooltip
            self.last_hover_token_id = None
            if hasattr(self, 'active_tooltip') and self.active_tooltip:
                try:
                    self.active_tooltip.destroy()
                    self.active_tooltip = None
                except:
                    pass

    def clear_token_info_panel(self):
        parent = self.master
        while parent is not None:
            if hasattr(parent, 'token_info_panel'):
                parent.token_info_panel.clear()
                break
            parent = getattr(parent, 'master', None)

    def _on_click(self, event):
        # NAJPIERW: Ukryj tooltip żeby nie konfliktował z klikiem
        if hasattr(self, 'active_tooltip') and self.active_tooltip:
            try:
                self.active_tooltip.destroy()
                self.active_tooltip = None
            except:
                pass
        self.last_hover_token_id = None
        
        # Blokada akcji dla generała (podgląd, brak ruchu)
        if hasattr(self, 'player') and hasattr(self.player, 'role') and self.player.role == 'Generał':
            # Zachowujemy blokadę czynności, ale usuwamy komunikat popup proszony przez użytkownika
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        hr = self.map_model.coords_to_hex(x, y)
        # --- DODANE: obsługa wystawiania żetonu z poczekalni ---
        if self.panel_dowodcy is not None and hasattr(self.panel_dowodcy, 'deploy_window'):
            deploy = self.panel_dowodcy.deploy_window
            if deploy is not None and getattr(deploy, 'selected_token_path', None):
                import os, json, shutil
                from engine.token import Token
                from tkinter import messagebox
                token_folder = deploy.selected_token_path
                # print(f"[DEBUG] Wybrano folder żetonu: {token_folder}")
                token_json = os.path.join(token_folder, "token.json")
                if os.path.exists(token_json):
                    # SPRAWDŹ SPAWN NATION
                    if hr is None:
                        try:
                            from utils.action_logger import log_action
                            log_action(self.game_engine, getattr(self, 'player', None), getattr(self.game_engine, 'turn', None), 'deploy_error', details={}, result_msg='no_hex_clicked')
                        except Exception:
                            pass
                        messagebox.showerror("Błąd", "Kliknij na pole mapy, aby wystawić żeton.")
                        return
                    tile = self.game_engine.board.get_tile(hr[0], hr[1])
                    nation = str(self.player.nation).strip().lower()
                    if not tile or not tile.spawn_nation or str(tile.spawn_nation).strip().lower() != nation:
                        try:
                            from utils.action_logger import log_action
                            log_action(self.game_engine, getattr(self, 'player', None), getattr(self.game_engine, 'turn', None), 'deploy_error', details={'to_q': hr[0], 'to_r': hr[1]}, result_msg='invalid_spawn_hex')
                        except Exception:
                            pass
                        messagebox.showerror("Błąd wystawiania", f"Możesz wystawiać nowe żetony tylko na polach spawnu swojej nacji!")
                        return
                    # print(f"[DEBUG] Plik token.json istnieje: {token_json}")
                    with open(token_json, encoding="utf-8") as f:
                        token_data = json.load(f)
                    # Ustaw owner na aktualnego gracza
                    token_owner = f"{self.player.id} ({self.player.nation})"
                    # print(f"[DEBUG] Ustawiam ownera: {token_owner}")
                    token_data["owner"] = token_owner
                    # Utwórz obiekt Token
                    new_token = Token.from_json(token_data)
                    new_token.set_position(hr[0], hr[1])
                    new_token.owner = token_owner
                    # Resetuj punkty ruchu i paliwa po wystawieniu
                    new_token.apply_movement_mode(reset_mp=True)
                    new_token.currentFuel = new_token.maxFuel
                    # Skopiuj PNG do katalogu docelowego jeśli wymagane (np. assets/tokens/aktualne/)
                    png_src = os.path.join(token_folder, "token.png")
                    json_src = os.path.join(token_folder, "token.json")
                    if os.path.exists(png_src):
                        dest_dir = os.path.join("assets", "tokens", "aktualne")
                        os.makedirs(dest_dir, exist_ok=True)
                        base_name = os.path.basename(token_folder)
                        png_dst = os.path.join(dest_dir, base_name + ".png")
                        shutil.copy2(png_src, png_dst)
                        # print(f"[DEBUG] Skopiowano PNG do: {png_dst}")
                        # Ustaw nową ścieżkę do obrazka w stats['image']
                        new_token.stats['image'] = png_dst.replace('\\', '/')
                    # Skopiuj również token.json do katalogu aktualne
                    if os.path.exists(json_src):
                        json_dst = os.path.join(dest_dir, base_name + ".json")
                        shutil.copy2(json_src, json_dst)
                        # print(f"[DEBUG] Skopiowano JSON do: {json_dst}")
                    # print(f"[DEBUG] Utworzono Token: id={new_token.id}, q={new_token.q}, r={new_token.r}, owner={new_token.owner}")
                    self.game_engine.tokens.append(new_token)
                    # print(f"[DEBUG] Liczba żetonów po dodaniu: {len(self.game_engine.tokens)}")
                    self.game_engine.board.set_tokens(self.game_engine.tokens)
                    # LOG: deploy
                    try:
                        from utils.action_logger import log_action
                        log_action(
                            self.game_engine,
                            getattr(self, 'player', None),
                            getattr(self.game_engine, 'turn', None),
                            'deploy',
                            details={
                                'token_id': new_token.id,
                                'to_q': new_token.q, 'to_r': new_token.r,
                            },
                            result_msg='deployed'
                        )
                    except Exception:
                        pass
                    # Dodaj: aktualizacja widoczności po dodaniu żetonu
                    from engine.engine import update_all_players_visibility
                    update_all_players_visibility(self.game_engine.players, self.game_engine.tokens, self.game_engine.board)
                    # Wymuś ustawienie current_player_obj na gracza, który wystawił żeton
                    self.game_engine.current_player_obj = self.player
                    # Odśwież panel mapy po synchronizacji widoczności
                    self.refresh()
                    # print(f"[DEBUG] Odświeżono mapę po dodaniu żetonu.")                    # Usuń folder z poczekalni
                    shutil.rmtree(token_folder)
                    # print(f"[DEBUG] Usunięto folder: {token_folder}")
                    # Zamknij okno deploy
                    deploy.destroy()
                    self.panel_dowodcy.deploy_window = None
                    # Aktualizuj stan przycisku deploy - usuń miganie jeśli nie ma już żetonów
                    self.panel_dowodcy.update_deploy_button_state()
                    # print(f"[DEBUG] Zamknięto okno deploy.")
                    return
        # ...existing code...
        if not hasattr(self, 'selected_token_id'):
            self.selected_token_id = None
        # Sprawdź, czy kliknięto na żeton
        clicked_token = None
        for token in self.tokens:
            if token.q is not None and token.r is not None:
                visible_ids = set()
                if hasattr(self.player, 'visible_tokens') and hasattr(self.player, 'temp_visible_tokens'):
                    visible_ids = self.player.visible_tokens | self.player.temp_visible_tokens
                elif hasattr(self.player, 'visible_tokens'):
                    visible_ids = self.player.visible_tokens
                if token.id not in visible_ids:
                    continue
                tx, ty = self.map_model.hex_to_pixel(token.q, token.r)
                hex_size = self.map_model.hex_size
                if abs(x - tx) < hex_size // 2 and abs(y - ty) < hex_size // 2:
                    clicked_token = token
                    break
        if clicked_token:
            expected_owner = f"{getattr(self.player, 'id', '?')} ({getattr(self.player, 'nation', '?')})"
            if getattr(clicked_token, 'owner', None) != expected_owner:
                self.selected_token_id = None
                self.current_path = None
                if self.token_info_panel is not None:
                    self.token_info_panel.clear()
                self.refresh()
                return
            # Najpierw pokaż info panel z aktualnym stanem żetonu
            self.selected_token_id = clicked_token.id
            if self.panel_dowodcy is not None:
                self.panel_dowodcy.wybrany_token = clicked_token
            if self.token_info_panel is not None:
                self.token_info_panel.show_token(clicked_token)
            # Jeśli tryb nie jest zablokowany, pokaż okno wyboru trybu ruchu
            if not getattr(clicked_token, 'movement_mode_locked', False):
                class ModeDialog(simpledialog.Dialog):
                    def body(self, master):
                        tk.Label(master, text="Wybierz tryb ruchu:").pack()
                        self.combo = ttk.Combobox(master, values=["Bojowy", "Marsz", "Zwiad"], state="readonly")
                        mode_map = {'combat': 0, 'marsz': 1, 'recon': 2}
                        curr_mode = getattr(clicked_token, 'movement_mode', 'combat')
                        idx = mode_map.get(curr_mode, 0)
                        self.combo.current(idx)
                        self.combo.pack()
                        return self.combo
                    def apply(self):
                        self.result = self.combo.get()
                dialog = ModeDialog(self)
                mode = getattr(dialog, 'result', None)
                # Sprawdź czy dialog został potwierdzony (nie anulowany)
                if mode is not None and mode in ["Bojowy", "Marsz", "Zwiad"]:
                    if mode == "Bojowy":
                        clicked_token.movement_mode = "combat"
                    elif mode == "Marsz":
                        clicked_token.movement_mode = "march"
                    elif mode == "Zwiad":
                        clicked_token.movement_mode = "recon"
                    clicked_token.apply_movement_mode(reset_mp=False)
                    clicked_token.movement_mode_locked = True  # Blokada zmiany trybu do końca tury
                    self.selected_token_id = clicked_token.id
                    if self.panel_dowodcy is not None:
                        self.panel_dowodcy.wybrany_token = clicked_token
                    if self.token_info_panel is not None:
                        self.token_info_panel.show_token(clicked_token)  # Odśwież info panel po zmianie trybu
                # Jeśli dialog anulowano - nie blokujemy trybu, można ponownie wybrać
            self.current_path = None
            self.refresh()
            return
        elif hr and self.selected_token_id:
            token = next((t for t in self.tokens if t.id == self.selected_token_id), None)
            if token:
                # Spróbuj znaleźć ścieżkę do celu, a jeśli się nie uda, znajdź maksymalnie osiągalną ścieżkę
                path = self.game_engine.board.find_path((token.q, token.r), hr, max_mp=token.currentMovePoints, max_fuel=getattr(token, 'currentFuel', 9999))
                if path:
                    # POLICZ RZECZYWISTY KOSZT RUCHU
                    real_cost = 0
                    for step in path[1:]:  # pomijamy start
                        tile = self.game_engine.board.get_tile(*step)
                        move_mod = getattr(tile, 'move_mod', 0)
                        move_cost = 1 + move_mod
                        real_cost += move_cost
                    # Pokaż niebieską ścieżkę przez 0.5s, potem wykonaj ruch automatycznie
                    self.current_path = path
                    self.refresh()
                    # Etykieta: w zasięgu
                    try:
                        self.canvas.delete('path_label')
                    except Exception:
                        pass
                    try:
                        dx, dy = self.map_model.hex_to_pixel(hr[0], hr[1])
                        self.canvas.create_text(dx, dy - 18, text='w zasięgu', fill='#1e90ff', font=('Arial', 10, 'bold'), tags='path_label')
                        self.canvas.after(500, lambda: self.canvas.delete('path_label'))
                    except Exception:
                        pass
                    def _do_move_to_target():
                        from engine.action_refactored_clean import MoveAction
                        action = MoveAction(token.id, hr[0], hr[1])
                        result = self.game_engine.execute_action(action, player=getattr(self, 'player', None))
                        success, msg = result.success, result.message
                        self.tokens = self.game_engine.tokens
                        # LOG: move
                        try:
                            from utils.action_logger import log_action
                            log_action(
                                self.game_engine,
                                getattr(self, 'player', None),
                                getattr(self.game_engine, 'turn', None),
                                'move',
                                details={
                                    'token_id': token.id,
                                    'from_q': path[0][0], 'from_r': path[0][1],
                                    'to_q': hr[0], 'to_r': hr[1],
                                },
                                result_msg=msg
                            )
                        except Exception:
                            pass
                        if success:
                            from engine.engine import update_all_players_visibility
                            if hasattr(self.game_engine, 'players'):
                                update_all_players_visibility(self.game_engine.players, self.game_engine.tokens, self.game_engine.board)
                            # --- AUTOMATYCZNA REAKCJA WROGÓW ---
                            moved_token = token  # żeton, który się ruszał
                            # print(f"[DEBUG] Sprawdzam reakcję wrogów na ruch żetonu {moved_token.id} ({moved_token.owner}) na ({moved_token.q},{moved_token.r})")
                            for enemy in self.game_engine.tokens:
                                if enemy.id == moved_token.id or enemy.owner == moved_token.owner:
                                    continue
                                # Blokada: nie atakuje własnych żetonów
                                nation_enemy = enemy.owner.split('(')[-1].replace(')','').strip()
                                nation_moved = moved_token.owner.split('(')[-1].replace(')','').strip()
                                if nation_enemy == nation_moved:
                                    # print(f"[DEBUG] Blokada: {enemy.id} ({enemy.owner}) nie atakuje własnego żetonu {moved_token.id} ({moved_token.owner})!")
                                    continue
                                sight = enemy.stats.get('sight', 0)
                                dist = self.game_engine.board.hex_distance((enemy.q, enemy.r), (moved_token.q, moved_token.r))
                                in_sight = dist <= sight
                                attack_range = enemy.stats.get('attack', {}).get('range', 1)
                                in_range = dist <= attack_range
                                # print(f"[DEBUG] Wróg {enemy.id} ({enemy.owner}) na ({enemy.q},{enemy.r}): dystans={dist}, sight={sight}, attack_range={attack_range}, in_sight={in_sight}, in_range={in_range}")
                                if in_sight and in_range:
                                    # print(f"[REAKCJA WROGA] {enemy.id} ({enemy.owner}) atakuje {moved_token.id} ({moved_token.owner})!")
                                    setattr(moved_token, 'wykryty_do_konca_tury', True)
                                    from engine.action_refactored_clean import CombatAction
                                    action = CombatAction(enemy.id, moved_token.id, is_reaction=True)
                                    result = self.game_engine.execute_action(action)
                                    success2, msg2 = result.success, result.message
                                    # LOG: reaction attack
                                    try:
                                        from utils.action_logger import log_action
                                        # Preferuj numer tury z TurnManager jeśli jest dostępny
                                        current_turn = None
                                        try:
                                            current_turn = getattr(getattr(self.game_engine, 'turn_manager', None), 'current_turn', None)
                                        except Exception:
                                            current_turn = None
                                        if current_turn is None:
                                            current_turn = getattr(self.game_engine, 'turn', None)
                                        log_action(
                                            self.game_engine,
                                            enemy.owner,
                                            current_turn,
                                            'reaction_attack',
                                            details={
                                                'token_id': enemy.id,
                                                'target_token_id': moved_token.id,
                                                'from_q': enemy.q, 'from_r': enemy.r,
                                                'to_q': moved_token.q, 'to_r': moved_token.r,
                                            },
                                            result_msg=msg2
                                        )
                                    except Exception:
                                        pass
                                    # print(f"[WYNIK REAKCJI] {enemy.id} -> {moved_token.id}: {msg2}")
                                    self._visualize_combat(enemy, moved_token, msg2)
                                    # Komunikat zwrotny także dla ataku reakcyjnego
                                    from tkinter import messagebox
                                    messagebox.showinfo("Wynik walki", msg2)
                            # --- DODANE: wymuszone odświeżenie mapy po wszystkich reakcjach wrogów ---
                            self.refresh()
                        # Zaktualizuj panel informacji o żetonie natychmiast po ruchu
                        try:
                            if self.token_info_panel is not None:
                                moved = next((t for t in self.tokens if t.id == token.id), None)
                                if moved is not None:
                                    self.token_info_panel.show_token(moved)
                        except Exception:
                            pass
                        if not success:
                            from tkinter import messagebox
                            messagebox.showerror("Błąd ruchu", msg)
                        if success:
                            self.selected_token_id = None
                        self.current_path = None
                        self.refresh()
                    # Odczekaj 0.5 sekundy zanim wykonasz ruch (by ścieżka była widoczna)
                    self.canvas.after(500, _do_move_to_target)
                else:
                    # Ustal ścieżkę do najdalszego osiągalnego pola (fallback)
                    fallback_path = self.game_engine.board.find_path((token.q, token.r), hr, max_mp=token.currentMovePoints, max_fuel=getattr(token, 'currentFuel', 9999), fallback_to_closest=True)
                    if fallback_path and len(fallback_path) > 1:
                        # Narysuj ścieżkę, odczekaj 0.5s i automatycznie wykonaj ruch do ostatniego heksu z fallbacku
                        self.current_path = fallback_path
                        self.refresh()
                        dest = fallback_path[-1]
                        # Etykieta: poza zasięgiem
                        try:
                            self.canvas.delete('path_label')
                        except Exception:
                            pass
                        try:
                            dx, dy = self.map_model.hex_to_pixel(dest[0], dest[1])
                            self.canvas.create_text(dx, dy - 18, text='poza zasięgiem', fill='#ff8c00', font=('Arial', 10, 'bold'), tags='path_label')
                            self.canvas.after(500, lambda: self.canvas.delete('path_label'))
                        except Exception:
                            pass
                        def _do_move_to_fallback():
                            from engine.action_refactored_clean import MoveAction
                            action = MoveAction(token.id, dest[0], dest[1])
                            result = self.game_engine.execute_action(action, player=getattr(self, 'player', None))
                            success, msg = result.success, result.message
                        self.tokens = self.game_engine.tokens
                        # LOG: move (fallback)
                        try:
                            from utils.action_logger import log_action
                            log_action(
                                self.game_engine,
                                getattr(self, 'player', None),
                                getattr(self.game_engine, 'turn', None),
                                'move',
                                details={
                                    'token_id': token.id,
                                    'from_q': fallback_path[0][0], 'from_r': fallback_path[0][1],
                                    'to_q': dest[0], 'to_r': dest[1],
                                    'fallback': True
                                },
                                result_msg=None
                            )
                        except Exception:
                            pass
                        def _after_fallback_move():
                            # Po wykonaniu ruchu powtórz logikę post-move jak w głównym ruchu
                            success = True  # zakładamy, że log powyżej zapisany; wynik ruchu sprawdzimy wewnątrz funkcji
                            try:
                                from engine.engine import update_all_players_visibility
                                if hasattr(self.game_engine, 'players'):
                                    update_all_players_visibility(self.game_engine.players, self.game_engine.tokens, self.game_engine.board)
                                moved_token = token
                                for enemy in self.game_engine.tokens:
                                    if enemy.id == moved_token.id or enemy.owner == moved_token.owner:
                                        continue
                                    nation_enemy = enemy.owner.split('(')[-1].replace(')','').strip()
                                    nation_moved = moved_token.owner.split('(')[-1].replace(')','').strip()
                                    if nation_enemy == nation_moved:
                                        continue
                                    sight = enemy.stats.get('sight', 0)
                                    dist = self.game_engine.board.hex_distance((enemy.q, enemy.r), (moved_token.q, moved_token.r))
                                    in_sight = dist <= sight
                                    attack_range = enemy.stats.get('attack', {}).get('range', 1)
                                    in_range = dist <= attack_range
                                    if in_sight and in_range:
                                        setattr(moved_token, 'wykryty_do_konca_tury', True)
                                        from engine.action_refactored_clean import CombatAction
                                        action2 = CombatAction(enemy.id, moved_token.id, is_reaction=True)
                                        result = self.game_engine.execute_action(action2)
                                        success2, msg2 = result.success, result.message
                                        try:
                                            from utils.action_logger import log_action
                                            current_turn = getattr(getattr(self.game_engine, 'turn_manager', None), 'current_turn', getattr(self.game_engine, 'turn', None))
                                            log_action(
                                                self.game_engine,
                                                enemy.owner,
                                                current_turn,
                                                'reaction_attack',
                                                details={
                                                    'token_id': enemy.id,
                                                    'target_token_id': moved_token.id,
                                                    'from_q': enemy.q, 'from_r': enemy.r,
                                                    'to_q': moved_token.q, 'to_r': moved_token.r,
                                                },
                                                result_msg=msg2
                                            )
                                        except Exception:
                                            pass
                                        self._visualize_combat(enemy, moved_token, msg2)
                                        from tkinter import messagebox
                                        messagebox.showinfo("Wynik walki", msg2)
                                self.refresh()
                            except Exception:
                                pass
                            # Zaktualizuj panel informacji o żetonie natychmiast po ruchu (fallback)
                            try:
                                if self.token_info_panel is not None:
                                    moved = next((t for t in self.tokens if t.id == token.id), None)
                                    if moved is not None:
                                        self.token_info_panel.show_token(moved)
                            except Exception:
                                pass
                            self.selected_token_id = None
                            self.current_path = None
                            self.refresh()
                        # Odczekaj 0.5 sekundy zanim wykonasz ruch fallback
                        self.canvas.after(500, lambda: (_do_move_to_fallback(), _after_fallback_move()))
                    else:
                        # Brak jakiegokolwiek ruchu możliwego — NIC nie rób i nie pokazuj błędu
                        try:
                            from utils.action_logger import log_action
                            log_action(self.game_engine, getattr(self, 'player', None), getattr(self.game_engine, 'turn', None), 'move_error', details={'token_id': token.id}, result_msg='no_reachable_hex')
                        except Exception:
                            pass
        else:
            self.selected_token_id = None
            self.current_path = None
        if clicked_token is None:
            self.clear_token_info_panel()
        self.refresh()

    def _on_right_click_token(self, event):
        # NAJPIERW: Ukryj tooltip żeby nie konfliktował z prawym klikiem
        if hasattr(self, 'active_tooltip') and self.active_tooltip:
            try:
                self.active_tooltip.destroy()
                self.active_tooltip = None
            except:
                pass
        self.last_hover_token_id = None
        
        # Obsługa ataku na żeton przeciwnika
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        clicked_token = None
        for token in self.tokens:
            if token.q is not None and token.r is not None:
                visible_ids = set()
                if hasattr(self.player, 'visible_tokens') and hasattr(self.player, 'temp_visible_tokens'):
                    visible_ids = self.player.visible_tokens | self.player.temp_visible_tokens
                elif hasattr(self.player, 'visible_tokens'):
                    visible_ids = self.player.visible_tokens
                if token.id not in visible_ids:
                    continue
                tx, ty = self.map_model.hex_to_pixel(token.q, token.r)
                hex_size = self.map_model.hex_size
                if abs(x - tx) < hex_size // 2 and abs(y - ty) < hex_size // 2:
                    clicked_token = token
                    break
        # Jeśli generał – użyj prawego kliknięcia tylko do podglądu info, bez selekcji/ataku (dowódca zachowuje atak)
        if hasattr(self, 'player') and getattr(self.player, 'role', None) == 'Generał':
            if clicked_token and self.token_info_panel is not None:
                try:
                    self.token_info_panel.show_token(clicked_token)
                except Exception:
                    pass
            return
        # Sprawdź, czy kliknięto w żeton przeciwnika (nie swój, nie sojusznika)
        if clicked_token and self.selected_token_id:
            attacker = next((t for t in self.tokens if t.id == self.selected_token_id), None)
            if not attacker:
                return
            # Sprawdź, czy to przeciwnik
            nation1 = str(attacker.stats.get('nation', ''))
            nation2 = str(clicked_token.stats.get('nation', ''))
            if nation1 == nation2:
                return  # Nie atakuj sojusznika
            from tkinter import messagebox
            answer = messagebox.askyesno("Potwierdź atak", f"Czy chcesz zaatakować żeton {clicked_token.id}?\n({clicked_token.stats.get('unit','')})")
            if not answer:
                try:
                    from utils.action_logger import log_action
                    log_action(
                        self.game_engine,
                        getattr(self, 'player', None),
                        getattr(self.game_engine, 'turn', None),
                        'attack_cancel',
                        details={'token_id': attacker.id, 'target_token_id': clicked_token.id},
                        result_msg='user_no'
                    )
                except Exception:
                    pass
                return
            # Wywołaj CombatAction
            from engine.action_refactored_clean import CombatAction
            action = CombatAction(attacker.id, clicked_token.id)
            result = self.game_engine.execute_action(action, player=getattr(self, 'player', None))
            success, msg = result.success, result.message
            self.tokens = self.game_engine.tokens
            # LOG: attack
            try:
                from utils.action_logger import log_action
                log_action(
                    self.game_engine,
                    getattr(self, 'player', None),
                    getattr(self.game_engine, 'turn', None),
                    'attack',
                    details={
                        'token_id': attacker.id,
                        'target_token_id': clicked_token.id,
                        'from_q': attacker.q, 'from_r': attacker.r,
                        'to_q': clicked_token.q, 'to_r': clicked_token.r,
                    },
                    result_msg=msg
                )
            except Exception:
                pass
            # Efekty wizualne (szkielet): podświetlenie pól, miganie, usuwanie, cofania
            self._visualize_combat(attacker, clicked_token, msg)
            # Komunikat zwrotny
            if not success:
                messagebox.showerror("Błąd ataku", msg)
            else:
                messagebox.showinfo("Wynik walki", msg)
            # Odśwież mapę i panele
            self.selected_token_id = None
            self.refresh()

    def _visualize_combat(self, attacker, defender, msg):
        # 1. Podświetlenie pól atakującego i broniącego (mgiełka)
        ax, ay = self.map_model.hex_to_pixel(attacker.q, attacker.r)
        dx, dy = self.map_model.hex_to_pixel(defender.q, defender.r)
        hex_size = self.map_model.hex_size
        verts_a = get_hex_vertices(ax, ay, hex_size)
        verts_d = get_hex_vertices(dx, dy, hex_size)
        # Poprawione kolory: jasnozielony i jasnoczerwony (bez przezroczystości)
        self.canvas.create_polygon([c for p in verts_a for c in p], fill='#90ee90', outline='', tags='combat_fx')
        self.canvas.create_polygon([c for p in verts_d for c in p], fill='#ff7f7f', outline='', tags='combat_fx')
        self.canvas.after(400, lambda: self.canvas.delete('combat_fx'))

        # 2. Miganie żetonów, usuwanie, cofania (na podstawie msg)
        def blink_token(token_id, color, times=4, delay=120, on_end=None):
            tag = f"token_{token_id}"
            def blink(i):
                if i % 2 == 0:
                    self.canvas.itemconfig(tag, state='hidden')
                else:
                    self.canvas.itemconfig(tag, state='normal')
                if i < times * 2:
                    self.canvas.after(delay, lambda: blink(i + 1))
                elif on_end:
                    on_end()
            blink(0)

        def animate_remove(token_id):
            self.canvas.after(350, self.refresh)

        def animate_retreat(token, old_q, old_r, new_q, new_r):
            steps = 6
            x0, y0 = self.map_model.hex_to_pixel(old_q, old_r)
            x1, y1 = self.map_model.hex_to_pixel(new_q, new_r)
            dx = (x1 - x0) / steps
            dy = (y1 - y0) / steps
            tag = f"token_{token.id}"
            def move_step(i):
                if i > steps:
                    self.refresh()
                    return
                self.canvas.move(tag, dx, dy)
                self.canvas.after(40, lambda: move_step(i + 1))
            move_step(1)

        # Rozpoznanie efektu na podstawie komunikatu msg
        msg_l = msg.lower()
        # Eliminacja obrońcy
        if 'obrońca został zniszczony' in msg_l or 'obrońca nie mógł się cofnąć' in msg_l:
            blink_token(defender.id, color='red', times=4, delay=100, on_end=lambda: animate_remove(defender.id))
            # Aktualizacja VP po eliminacji
            if hasattr(self, 'panel_dowodcy') and hasattr(self.panel_dowodcy, 'panel_gracza'):
                from gui.panel_gracza import PanelGracza
                PanelGracza.update_all_vp()
        # Eliminacja atakującego
        elif 'atakujący został zniszczony' in msg_l:
            blink_token(attacker.id, color='red', times=4, delay=100, on_end=lambda: animate_remove(attacker.id))
            # Aktualizacja VP po eliminacji
            if hasattr(self, 'panel_dowodcy') and hasattr(self.panel_dowodcy, 'panel_gracza'):
                from gui.panel_gracza import PanelGracza
                PanelGracza.update_all_vp()
        # Cofanie obrońcy
        elif 'cofnął się na' in msg_l:
            import re
            m = re.search(r'cofnął się na \(([-\d]+),([\-\d]+)\)', msg)
            if m:
                new_q, new_r = int(m.group(1)), int(m.group(2))
                old_q, old_r = defender.q, defender.r
                animate_retreat(defender, old_q, old_r, new_q, new_r)
                blink_token(defender.id, color='red', times=2, delay=120, on_end=self.refresh)
        # Domyślnie: krótkie miganie obu żetonów
        else:
            def after_blink():
                self.refresh()
            blink_token(attacker.id, color='orange', times=2, delay=100, on_end=None)
            blink_token(defender.id, color='orange', times=2, delay=100, on_end=after_blink)
        # Po animacjach, po odświeżeniu mapy, wypisz wartości po walce
        def print_after_refresh():
            att = next((t for t in self.tokens if t.id == attacker.id), None)
            defn = next((t for t in self.tokens if t.id == defender.id), None)
            # Usunięto printy debugujące
        self.canvas.after(600, print_after_refresh)

    # Dodane: metoda do ładowania stanu gry (przykładowa implementacja)
    def load_game_state(self, state):
        # Przykładowa struktura state:
        # {
        #     'tokens': [ { 'id': 1, 'q': 2, 'r': 3, ... }, { 'id': 2, 'q': 4, 'r': 5, ... }, ... ],
        #     'current_player': 1,
        #     'turn': 5,
        #     ...
        # }
        try:
            # Przywróć żetony
            token_map = {t.id: t for t in self.tokens}
            for token_data in state.get('tokens', []):
                token_id = token_data.get('id')
                token = token_map.get(token_id)
                if token:
                    # Aktualizuj tylko istniejące tokeny
                    for key, value in token_data.items():
                        setattr(token, key, value)
            # Przywróć inne istotne dane ze stanu gry
            self.game_engine.current_player_id = state.get('current_player', self.game_engine.current_player_id)
            self.game_engine.turn = state.get('turn', self.game_engine.turn)
            # Odśwież widok
            self.refresh()
            # Usunięto printy debugujące
        except Exception as e:
            print(f"[ERROR] Ładowanie stanu gry nie powiodło się: {e}")

    # Dodane: metoda do zapisywania stanu gry (przykładowa implementacja)
    def save_game_state(self):
        try:
            state = {
                'tokens': [ { 'id': t.id, 'q': t.q, 'r': t.r, 'owner': t.owner, 'movement_mode': t.movement_mode, 'currentMovePoints': t.currentMovePoints, 'stats': t.stats } for t in self.tokens ],
                'current_player': self.game_engine.current_player_id,
                'turn': self.game_engine.turn,
            }
            # Zapisz stan do pliku lub innego medium
            with open('save_game.json', 'w') as f:
                import json
                json.dump(state, f, ensure_ascii=False, indent=4)
            # Usunięto printy debugujące
        except Exception as e:
            print(f"[ERROR] Zapisywanie stanu gry nie powiodło się: {e}")

    # Dodane: debug metoda do wypisywania aktualnego stanu gry w konsoli
    def debug_print_game_state(self):
        # Usunięto wszystkie printy debugujące
        pass