import tkinter as tk
from engine.detection_filter import apply_detection_filter

class TooltipTokenInfo(tk.Toplevel):
    """
    Tooltip wyświetlający informacje o żetonie po najechaniu myszą.
    Automatycznie znika po 5 sekundach lub gdy mysz opuści obszar.
    """
    
    def __init__(self, parent, token, player=None, x=0, y=0):
        super().__init__(parent)
        
        # Konfiguracja okna tooltip
        self.overrideredirect(True)  # Usuń ramkę okna
        self.wm_attributes("-topmost", True)  # Zawsze na wierzchu
        self.config(bg="lightyellow", relief="solid", borderwidth=1)
        
        self.token = token
        self.player = player
        self.timer_id = None
        
        # Szerszy panel - miejsce na wszystkie dane (zmniejszona wysokość)
        self.config(width=450, height=200)
        
        # Główna ramka z padding
        main_frame = tk.Frame(self, bg="lightyellow", padx=10, pady=8)
        main_frame.pack(fill="both", expand=True)
        
        # Nagłówek z nazwą jednostki
        header_frame = tk.Frame(main_frame, bg="lightyellow")
        header_frame.pack(fill="x", pady=(0, 5))
        
        unit_name = token.stats.get('unit_full_name') or token.stats.get('label', token.id)
        header_label = tk.Label(header_frame, text=unit_name, 
                              font=("Arial", 12, "bold"), bg="lightyellow", fg="darkblue")
        header_label.pack()
        
        # Separator
        separator = tk.Frame(main_frame, height=1, bg="gray")
        separator.pack(fill="x", pady=(0, 5))
        
        # Ramka na dane - 2 kolumny
        data_frame = tk.Frame(main_frame, bg="lightyellow")
        data_frame.pack(fill="both", expand=True)
        
        # Lewa kolumna
        left_frame = tk.Frame(data_frame, bg="lightyellow")
        left_frame.grid(row=0, column=0, sticky="nw", padx=(0, 20))
        
        # Prawa kolumna  
        right_frame = tk.Frame(data_frame, bg="lightyellow")
        right_frame.grid(row=0, column=1, sticky="nw")
        
        # Tworzenie etykiet
        self.labels = {}
        self._create_labels(left_frame, right_frame)
        
        # Wypełnij dane
        self._populate_data()
        
        # Pozycjonowanie - przesunięte w lewo od kursora żeby nie zasłaniać
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Oblicz pozycję (w lewo od kursora, żeby nie zasłaniać) - zmniejszona wysokość
        tooltip_x = max(0, min(x - 460, screen_width - 460))  # 460px szerokości + margines
        tooltip_y = max(0, min(y - 50, screen_height - 220))   # 220px wysokości + margines
        
        self.geometry(f"450x200+{tooltip_x}+{tooltip_y}")
        
        # USUNIETO: Timer - panel widoczny tylko gdy mysz na żetonie
        
        # Event do ręcznego zamykania (opcjonalne)
        self.bind("<Button-1>", lambda e: self.destroy())
        
    def _create_labels(self, left_frame, right_frame):
        """Tworzy etykiety w dwóch kolumnach"""
        font = ("Arial", 9)
        bold_font = ("Arial", 9, "bold")
        
        # Lewa kolumna - podstawowe info
        left_labels = [
            ("nacja", "Nacja:"),
            ("jednostka", "Jednostka:"),  
            ("punkty_ruchu", "Punkty ruchu:"),
            ("wartość_obrony", "Wartość obrony:"),
            ("tryb_ruchu", "Tryb ruchu:"),
            ("paliwo", "Paliwo:")
        ]
        
        # Prawa kolumna - combat info
        right_labels = [
            ("zasięg_widzenia", "Zasięg widzenia:"),
            ("wartość_bojowa", "Zasoby bojowe:"),
            ("zasięg_ataku", "Zasięg ataku:"), 
            ("siła_ataku", "Siła ataku:"),
            ("price", "Wartość VP:")
        ]
        
        # Twórz etykiety w lewej kolumnie
        for i, (key, text) in enumerate(left_labels):
            label = tk.Label(left_frame, text=f"{text} -", font=font, 
                           anchor="w", bg="lightyellow", justify="left", 
                           wraplength=200)  # Zawijanie długich tekstów
            label.grid(row=i, column=0, sticky="w", pady=1)
            self.labels[key] = label
            
        # Twórz etykiety w prawej kolumnie  
        for i, (key, text) in enumerate(right_labels):
            label = tk.Label(right_frame, text=f"{text} -", font=font,
                           anchor="w", bg="lightyellow", justify="left",
                           wraplength=200)  # Zawijanie długich tekstów
            label.grid(row=i, column=0, sticky="w", pady=1)
            self.labels[key] = label
    
    def _populate_data(self):
        """Wypełnia dane - logika z TokenInfoPanel"""
        if self.token is None:
            return
            
        # Sprawdź czy to token wroga i jakim poziomem detekcji go widzimy
        detection_level = 1.0  # Domyślnie pełne informacje dla własnych tokenów
        is_enemy = False
        
        if self.player and hasattr(self.token, 'owner'):
            # Sprawdź czy to token wroga
            player_nation = getattr(self.player, 'nation', '')
            token_nation = self.token.stats.get('nation', '')
            
            if player_nation and token_nation and player_nation != token_nation:
                is_enemy = True
                # Pobierz detection_level z player.temp_visible_token_data
                if hasattr(self.player, 'temp_visible_token_data'):
                    token_data = self.player.temp_visible_token_data.get(self.token.id, {})
                    detection_level = token_data.get('detection_level', 0.0)
                else:
                    detection_level = 0.0
        
        # Jeśli to wróg, zastosuj filtr detekcji
        if is_enemy and detection_level < 1.0:
            filtered_info = apply_detection_filter(self.token, detection_level)
            self._show_filtered_token(filtered_info, detection_level)
        else:
            # Pokaż pełne informacje dla własnych tokenów lub pełnej detekcji
            self._show_full_token()
    
    def _show_full_token(self):
        """Wyświetl pełne informacje o tokenie - logika z TokenInfoPanel"""
        token = self.token
        nation = token.stats.get('nation', '-')
        
        # Dodaj informację o właścicielu/dowódcy
        owner_info = ''
        dowodca_id = None
        if hasattr(token, 'commander_id') and token.commander_id:
            dowodca_id = token.commander_id
        elif hasattr(token, 'owner') and token.owner:
            import re
            m = re.match(r"(\d+)", str(token.owner))
            if m:
                dowodca_id = m.group(1)
        if dowodca_id:
            owner_info = f" / Dowódca {dowodca_id}"
        nation_label = f"{nation}{owner_info}"
        
        # Pozostałe dane
        unit_name = token.stats.get('unit_full_name') or token.stats.get('label', token.id)
        move = getattr(token, 'currentMovePoints', token.stats.get('move', '-'))
        base_move = getattr(token, 'base_move', token.stats.get('move', '-'))
        defense = getattr(token, 'defense_value', token.stats.get('defense_value', '-'))
        base_defense = getattr(token, 'base_defense', token.stats.get('defense_value', '-'))
        sight = token.stats.get('sight', '-')
        current_fuel = getattr(token, 'currentFuel', token.stats.get('maintenance', '-'))
        max_fuel = getattr(token, 'maxFuel', token.stats.get('maintenance', '-'))
        combat_value = getattr(token, 'combat_value', token.stats.get('combat_value', '-'))
        base_combat_value = token.stats.get('combat_value', '-')
        movement_mode = getattr(token, 'movement_mode', 'combat')
        mode_label = {'combat': 'Bojowy', 'march': 'Marsz', 'recon': 'Zwiad'}.get(movement_mode, movement_mode)
        
        attack = token.stats.get('attack', '-')
        if isinstance(attack, dict):
            attack_range = attack.get('range', '-')
            attack_value = attack.get('value', '-')
        elif isinstance(attack, int):
            attack_range = '-'
            attack_value = attack
        else:
            attack_range = '-'
            attack_value = '-'
            
        price = token.stats.get('price', '-')
        
        # Aktualizuj etykiety
        self.labels["nacja"].config(text=f"Nacja: {nation_label}")
        self.labels["jednostka"].config(text=f"Jednostka: {unit_name}")
        self.labels["punkty_ruchu"].config(text=f"Punkty ruchu: {move} (bazowo: {base_move})")
        self.labels["wartość_obrony"].config(text=f"Wartość obrony: {defense} (bazowo: {base_defense})")
        self.labels["tryb_ruchu"].config(text=f"Tryb ruchu: {mode_label}")
        self.labels["paliwo"].config(text=f"Paliwo: {current_fuel}/{max_fuel}")
        self.labels["zasięg_widzenia"].config(text=f"Zasięg widzenia: {sight}")
        self.labels["wartość_bojowa"].config(text=f"Zasoby bojowe: {combat_value} (bazowo: {base_combat_value})")
        self.labels["zasięg_ataku"].config(text=f"Zasięg ataku: {attack_range}")
        self.labels["siła_ataku"].config(text=f"Siła ataku: {attack_value}")
        self.labels["price"].config(text=f"Wartość VP: {price}")
    
    def _show_filtered_token(self, filtered_info, detection_level):
        """Wyświetl przefiltrowane informacje o wrogu"""
        info_quality = filtered_info.get('info_quality', 'MINIMAL')
        
        token_id = filtered_info.get('id', 'UNKNOWN')
        nation = filtered_info.get('nation', '???')
        unit_type = filtered_info.get('type', 'KONTAKT')
        combat_value = filtered_info.get('combat_value', '???')
        
        certainty = f"(Pewność: {detection_level:.0%})"
        nation_label = f"{nation} {certainty}"
        
        quality_prefix = {
            'FULL': 'Zidentyfikowany:',
            'PARTIAL': 'Prawdopodobnie:',
            'MINIMAL': 'Nieznany kontakt:'
        }.get(info_quality, '')
        
        unit_label = f"{quality_prefix} {unit_type}"
        
        # Aktualizuj etykiety - ukryj szczegóły dla wrogów
        self.labels["nacja"].config(text=f"Nacja: {nation_label}")
        self.labels["jednostka"].config(text=f"Jednostka: {unit_label}")
        self.labels["punkty_ruchu"].config(text="Punkty ruchu: ???")
        self.labels["wartość_obrony"].config(text="Wartość obrony: ???")
        self.labels["tryb_ruchu"].config(text="Tryb ruchu: ???")
        self.labels["paliwo"].config(text="Paliwo: ???")
        self.labels["zasięg_widzenia"].config(text="Zasięg widzenia: ???")
        self.labels["wartość_bojowa"].config(text=f"Zasoby bojowe: {combat_value}")
        self.labels["zasięg_ataku"].config(text="Zasięg ataku: ???")
        self.labels["siła_ataku"].config(text="Siła ataku: ???")
        self.labels["price"].config(text="Wartość VP: ???")
    
    def destroy(self):
        """Zniszcz tooltip"""
        super().destroy()
