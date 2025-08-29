"""
KREATOR ARMII - Profesjonalna aplikacja do tworzenia armii
Pełna automatyzacja, GUI, kontrola parametrów, inteligentne balansowanie
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import sys
import json
import random
import threading
import time
try:
    from balance.model import compute_token
except ImportError:
    compute_token = None  # fallback jeśli brak modułu

# Deterministyczny seed dla powtarzalnych podglądów
random.seed(42)

# Dodaj ścieżkę do edytorów (z głównego folderu projektu)
project_root = Path(__file__).parent
sys.path.append(str(project_root / "edytory"))

class ArmyCreatorStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("🎖️ Kreator Armii - Kampania 1939")
        self.root.geometry("800x700")
        self.root.configure(bg="#556B2F")  # Dark olive green jak w grze
        self.root.resizable(True, True)
        
        # Ikona i style
        self.setup_styles()
          # Dane aplikacji (POPRAWIONE - po 2 dowódców na nację)
        self.nations = ["Polska", "Niemcy"]
        self.commanders = {
            "Polska": ["2 (Polska)", "3 (Polska)"],
            "Niemcy": ["5 (Niemcy)", "6 (Niemcy)"]
        }
        
        # Typy jednostek z bazowymi kosztami i statystykami
        self.unit_templates = {
            "P": {"name": "Piechota", "base_cost": 25, "weight": 0.4},
            "K": {"name": "Kawaleria", "base_cost": 30, "weight": 0.1},
            "TL": {"name": "Czołg Lekki", "base_cost": 35, "weight": 0.15},
            "TŚ": {"name": "Czołg Średni", "base_cost": 45, "weight": 0.1},
            "TC": {"name": "Czołg Ciężki", "base_cost": 60, "weight": 0.05},
            "TS": {"name": "Sam. Pancerny", "base_cost": 35, "weight": 0.1},
            "AL": {"name": "Artyleria Lekka", "base_cost": 35, "weight": 0.15},
            "AC": {"name": "Artyleria Ciężka", "base_cost": 55, "weight": 0.1},
            "AP": {"name": "Art. Przeciwlotnicza", "base_cost": 30, "weight": 0.05},
            "Z": {"name": "Zaopatrzenie/Rozpoznanie", "base_cost": 20, "weight": 0.1},
            "D": {"name": "Dowództwo", "base_cost": 40, "weight": 0.05}
        }
        
        self.unit_sizes = ["Pluton", "Kompania", "Batalion"]
          # Zmienne GUI
        self.selected_nation = tk.StringVar(value="Polska")
        self.selected_commander = tk.StringVar(value="2 (Polska)")
        self.army_size = tk.IntVar(value=10)
        self.army_budget = tk.IntVar(value=500)
        self.creating_army = False
        
        # Lista utworzonych jednostek
        self.created_units = []
        
        # Token Editor (zainicjalizowany później)
        self.token_editor = None
        
        # System upgradów automatycznych z Token Editora
        self.support_upgrades = {
            "drużyna granatników": {
                "movement": -1, "range": 1, "attack": 2, "combat": 0,
                "unit_maintenance": 1, "purchase": 10, "defense": 1
            },
            "sekcja km.ppanc": {
                "movement": -1, "range": 1, "attack": 2, "combat": 0,
                "unit_maintenance": 2, "purchase": 10, "defense": 2
            },
            "sekcja ckm": {
                "movement": -1, "range": 1, "attack": 2, "combat": 0,
                "unit_maintenance": 2, "purchase": 10, "defense": 2
            },
            "przodek dwukonny": {
                "movement": 2, "range": 0, "attack": 0, "combat": 0,
                "unit_maintenance": 1, "purchase": 5, "defense": 0
            },
            "sam. ciezarowy Fiat 621": {
                "movement": 5, "range": 0, "attack": 0, "combat": 0,
                "unit_maintenance": 3, "purchase": 8, "defense": 0
            },
            "sam.ciezarowy Praga Rv": {
                "movement": 5, "range": 0, "attack": 0, "combat": 0,
                "unit_maintenance": 3, "purchase": 8, "defense": 0
            },
            "ciagnik altyleryjski": {
                "movement": 3, "range": 0, "attack": 0, "combat": 0,
                "unit_maintenance": 4, "purchase": 12, "defense": 0
            },
            "obserwator": {
                "movement": 0, "range": 0, "attack": 0, "combat": 0,
                "unit_maintenance": 1, "purchase": 5, "defense": 0
            }
        }
        
        # Dozwolone upgrady dla każdego typu jednostki
        self.allowed_support = {
            "P": ["drużyna granatników", "sekcja km.ppanc", "sekcja ckm", 
                 "przodek dwukonny", "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv"],
            "K": ["sekcja ckm"],
            "TC": ["obserwator"],
            "TŚ": ["obserwator"],
            "TL": ["obserwator"],
            "TS": ["obserwator"],
            "AC": ["drużyna granatników", "sekcja ckm", "sekcja km.ppanc",
                  "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv", 
                  "ciagnik altyleryjski", "obserwator"],
            "AL": ["drużyna granatników", "sekcja ckm", "sekcja km.ppanc",
                  "przodek dwukonny", "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv",
                  "ciagnik altyleryjski", "obserwator"],
            "AP": ["drużyna granatników", "sekcja ckm", "sekcja km.ppanc",
                  "przodek dwukonny", "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv",
                  "ciagnik altyleryjski", "obserwator"],
            "Z": ["drużyna granatników", "sekcja km.ppanc", "sekcja ckm", "obserwator"],
            "D": ["drużyna granatników", "sekcja km.ppanc", "sekcja ckm", 
                 "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv", "obserwator"],
            "G": ["drużyna granatników", "sekcja km.ppanc", "sekcja ckm", 
                 "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv", "obserwator"]
        }
        
        # Typy transportu (tylko jeden na jednostkę)
        self.transport_types = ["przodek dwukonny", "sam. ciezarowy Fiat 621", 
                              "sam.ciezarowy Praga Rv", "ciagnik altyleryjski"]
        
        # Poziom wyposażenia armii (0-100%)
        self.equipment_level = tk.IntVar(value=50)
        
        self.create_gui()
        self.update_commander_options()
    
    def setup_styles(self):
        """Konfiguracja stylów TTK."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Kolory motywu wojskowego (jak w grze)
        style.configure('Title.TLabel', 
                       foreground='white', 
                       background='#556B2F',  # Dark olive green
                       font=('Arial', 20, 'bold'))
        
        style.configure('Header.TLabel',
                       foreground='white',
                       background='#556B2F',  # Dark olive green
                       font=('Arial', 12, 'bold'))
        
        style.configure('Military.TButton',
                       font=('Arial', 11, 'bold'),
                       foreground='#556B2F')
        
        style.configure('Success.TButton',
                       font=('Arial', 12, 'bold'),
                       foreground='#6B8E23')  # Olive green jak w grze
        
        style.configure('Danger.TButton',
                       font=('Arial', 12, 'bold'),
                       foreground='#8B0000')
    
    def create_gui(self):
        """Tworzy główny interfejs aplikacji."""
        
        # Nagłówek
        header_frame = tk.Frame(self.root, bg="#6B8E23", height=80)  # Olive green jak w grze
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        title_label = ttk.Label(header_frame, 
                               text="🎖️ KREATOR ARMII", 
                               style='Title.TLabel')
        title_label.pack(expand=True)
        
        subtitle_label = ttk.Label(header_frame,
                                  text="Profesjonalne tworzenie armii dla Kampanii 1939",
                                  style='Header.TLabel')
        subtitle_label.pack()
        
        # Główny kontener
        main_frame = tk.Frame(self.root, bg="#556B2F")  # Dark olive green
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Lewa kolumna - Parametry z scrollowaniem
        left_frame = tk.Frame(main_frame, bg="#6B8E23", width=350)  # Olive green jak w grze
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        # Canvas i scrollbar dla scrollowania
        self.left_canvas = tk.Canvas(left_frame, bg="#6B8E23", highlightthickness=0)
        self.left_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=self.left_canvas.yview)
        self.scrollable_left_frame = tk.Frame(self.left_canvas, bg="#6B8E23")
        
        self.scrollable_left_frame.bind(
            "<Configure>",
            lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
        )
        
        self.left_canvas.create_window((0, 0), window=self.scrollable_left_frame, anchor="nw")
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        
        self.left_canvas.pack(side="left", fill="both", expand=True)
        self.left_scrollbar.pack(side="right", fill="y")
        
        # Bind scroll events - ulepszone
        def _on_mousewheel(event):
            self.left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            self.left_canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        def _unbind_from_mousewheel(event):
            self.left_canvas.unbind_all("<MouseWheel>")
            
        self.left_canvas.bind('<Enter>', _bind_to_mousewheel)
        self.left_canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Dodatkowe usprawnienie - aktualizuj scrollregion po załadowaniu wszystkich elementów
        def update_scroll_region():
            self.root.update_idletasks()
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
            # Przewiń na dół, żeby pokazać dolne przyciski
            self.left_canvas.yview_moveto(1.0)
        
        # Uruchom po stworzeniu interfejsu
        self.root.after(100, update_scroll_region)
        
        self.create_parameters_panel(self.scrollable_left_frame)
        
        # Prawa kolumna - Podgląd i kontrola
        right_frame = tk.Frame(main_frame, bg="#6B8E23")  # Olive green jak w grze
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.create_preview_panel(right_frame)
        
        # Status bar na dole
        self.create_status_bar()
    
    def create_parameters_panel(self, parent):
        """Tworzy panel parametrów armii."""
        
        # Tytuł sekcji
        ttk.Label(parent, text="⚙️ PARAMETRY ARMII", style='Header.TLabel').pack(pady=5)
        
        # Nacja
        nation_frame = tk.Frame(parent, bg="#6B8E23")  # Olive green
        nation_frame.pack(fill=tk.X, padx=20, pady=3)
        
        ttk.Label(nation_frame, text="🏴 Nacja:", style='Header.TLabel').pack(anchor='w')
        nation_combo = ttk.Combobox(nation_frame, textvariable=self.selected_nation,
                                   values=self.nations, state='readonly', width=25)
        nation_combo.pack(fill=tk.X, pady=1)
        nation_combo.bind('<<ComboboxSelected>>', self.on_nation_change)
        
        # Dowódca
        commander_frame = tk.Frame(parent, bg="#6B8E23")  # Olive green
        commander_frame.pack(fill=tk.X, padx=20, pady=3)
        
        ttk.Label(commander_frame, text="👨‍✈️ Dowódca:", style='Header.TLabel').pack(anchor='w')
        self.commander_combo = ttk.Combobox(commander_frame, textvariable=self.selected_commander,
                                           state='readonly', width=25)
        self.commander_combo.pack(fill=tk.X, pady=1)
        
        # Separator
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=20, pady=8)
        
        # Rozmiar armii
        size_frame = tk.Frame(parent, bg="#6B8E23")  # Olive green
        size_frame.pack(fill=tk.X, padx=20, pady=3)
        
        ttk.Label(size_frame, text="📊 Ilość żetonów:", style='Header.TLabel').pack(anchor='w')
        self.size_scale = tk.Scale(size_frame, from_=5, to=25, orient=tk.HORIZONTAL,
                                  variable=self.army_size, bg="#6B8E23", fg="white",
                                  highlightbackground="#6B8E23", command=self.update_preview)
        self.size_scale.pack(fill=tk.X, pady=1)
        
        # Budżet VP
        budget_frame = tk.Frame(parent, bg="#6B8E23")  # Olive green
        budget_frame.pack(fill=tk.X, padx=20, pady=3)
        
        ttk.Label(budget_frame, text="💰 Budżet VP:", style='Header.TLabel').pack(anchor='w')
        self.budget_scale = tk.Scale(budget_frame, from_=250, to=1000, orient=tk.HORIZONTAL,
                                    variable=self.army_budget, bg="#6B8E23", fg="white",
                                    highlightbackground="#6B8E23", command=self.update_preview)
        self.budget_scale.pack(fill=tk.X, pady=1)
          # Poziom wyposażenia armii
        equipment_frame = tk.Frame(parent, bg="#6B8E23")  # Olive green
        equipment_frame.pack(fill=tk.X, padx=20, pady=3)
        
        ttk.Label(equipment_frame, text="🔧 Poziom wyposażenia:", style='Header.TLabel').pack(anchor='w')
        self.equipment_scale = tk.Scale(equipment_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                      variable=self.equipment_level, bg="#6B8E23", fg="white",
                                      highlightbackground="#6B8E23", command=self.update_preview)
        self.equipment_scale.pack(fill=tk.X, pady=1)
        
        # Informacja o poziomie wyposażenia
        equipment_info = tk.Label(equipment_frame, 
                                text="0% = brak upgradów, 50% = standardowe, 100% = pełne wyposażenie",
                                bg="#6B8E23", fg="white", font=("Arial", 7))
        equipment_info.pack(pady=1)
        
        # Separator
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=20, pady=8)
        
        # Przyciski akcji
        action_frame = tk.Frame(parent, bg="#6B8E23")  # Olive green
        action_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Button(action_frame, text="🎲 Losowa Armia", 
                  command=self.generate_random_army,
                  style='Military.TButton').pack(fill=tk.X, pady=1)
        
        ttk.Button(action_frame, text="⚖️ Zbalansuj Auto",
                  command=self.auto_balance_army,
                  style='Military.TButton').pack(fill=tk.X, pady=1)
        
        ttk.Button(action_frame, text="🗑️ Wyczyść",
                  command=self.clear_army,
                  style='Danger.TButton').pack(fill=tk.X, pady=1)
        
        # Główny przycisk tworzenia - kompaktowy
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=20, pady=5)
        
        self.create_button = ttk.Button(action_frame, text="💾 UTWÓRZ ARMIĘ",
                                       command=self.create_army_thread,
                                       style='Success.TButton')
        self.create_button.pack(fill=tk.X, pady=5)
        
        # Panel zarządzania folderami - ultra kompaktowy
        ttk.Separator(parent, orient='horizontal').pack(fill=tk.X, padx=20, pady=3)
        
        management_frame = tk.Frame(parent, bg="#6B8E23")  # Olive green
        management_frame.pack(fill=tk.X, padx=20, pady=2)
        
        ttk.Label(management_frame, text="🗂️ ZARZĄDZANIE FOLDERAMI", 
                 style='Header.TLabel', font=("Arial", 10, "bold")).pack(pady=2)
        
        # Statystyki żetonów - ultra kompaktowe
        self.stats_frame = tk.Frame(management_frame, bg="#556B2F", relief=tk.RIDGE, bd=1)
        self.stats_frame.pack(fill=tk.X, pady=2)
        
        self.stats_label = tk.Label(self.stats_frame, 
                                   text="📊 Sprawdzanie folderów...", 
                                   bg="#556B2F", fg="white", 
                                   font=("Arial", 8), 
                                   wraplength=300,
                                   justify=tk.LEFT)
        self.stats_label.pack(pady=1, padx=3)
        
        # Przyciski czyszczenia - ultra kompaktowe (2x2 układ)
        clean_frame = tk.Frame(management_frame, bg="#6B8E23")
        clean_frame.pack(fill=tk.X, pady=2)
        
        # Górny rząd przycisków
        top_buttons_frame = tk.Frame(clean_frame, bg="#6B8E23")
        top_buttons_frame.pack(fill=tk.X, pady=0)
        
        ttk.Button(top_buttons_frame, text="🗑️ Polskie",
                  command=self.clean_polish_tokens,
                  style='Danger.TButton').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,1))
        
        ttk.Button(top_buttons_frame, text="🗑️ Niemieckie",
                  command=self.clean_german_tokens,
                  style='Danger.TButton').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(1,0))
        
        # Dolny rząd przycisków
        bottom_buttons_frame = tk.Frame(clean_frame, bg="#6B8E23")
        bottom_buttons_frame.pack(fill=tk.X, pady=(1,0))
        
        ttk.Button(bottom_buttons_frame, text="🗑️ WSZYSTKIE",
                  command=self.clean_all_tokens,
                  style='Danger.TButton').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,1))
        
        ttk.Button(bottom_buttons_frame, text="📊 Odśwież",
                  command=self.refresh_token_stats,
                  style='Military.TButton').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(1,0))
        
        # Załaduj początkowe statystyki
        self.refresh_token_stats()
    
    def create_preview_panel(self, parent):
        """Tworzy panel podglądu armii."""
        
        # Tytuł sekcji
        ttk.Label(parent, text="👁️ PODGLĄD ARMII", style='Header.TLabel').pack(pady=10)
        
        # Informacje o armii
        info_frame = tk.Frame(parent, bg="#6B8E23")  # Olive green
        info_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.info_label = ttk.Label(info_frame, text="Wybierz parametry aby zobaczyć podgląd",
                                   style='Header.TLabel')
        self.info_label.pack()
        
        # Lista jednostek
        list_frame = tk.Frame(parent, bg="#6B8E23")  # Olive green
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ttk.Label(list_frame, text="📋 Skład armii:", style='Header.TLabel').pack(anchor='w')
        
        # Scrolled text dla listy jednostek
        self.units_text = scrolledtext.ScrolledText(list_frame, height=15, width=40,
                                                   bg="white", fg="#556B2F",  # Tekst w kolorze dark olive
                                                   font=('Consolas', 10))
        self.units_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Progress bar
        self.progress_frame = tk.Frame(parent, bg="#6B8E23")  # Olive green
        self.progress_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(self.progress_frame, text="Postęp tworzenia:", style='Header.TLabel').pack(anchor='w')
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=2)
        
        self.progress_label = ttk.Label(self.progress_frame, text="Gotowy do pracy",
                                       style='Header.TLabel')
        self.progress_label.pack()
    
    def create_status_bar(self):
        """Tworzy pasek statusu."""
        status_frame = tk.Frame(self.root, bg="#556B2F", height=30)  # Dark olive green
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = ttk.Label(status_frame, 
                                     text="⚡ Kreator Armii - Gotowy",
                                     style='Header.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Informacja o autorze
        author_label = ttk.Label(status_frame,
                                text="Kampania 1939 © 2025",
                                style='Header.TLabel')
        author_label.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def on_nation_change(self, event=None):
        """Obsługuje zmianę nacji."""
        self.update_commander_options()
        self.update_preview()
    
    def update_commander_options(self):
        """Aktualizuje opcje dowódców dla wybranej nacji."""
        nation = self.selected_nation.get()
        commanders = self.commanders.get(nation, [])
        
        self.commander_combo['values'] = commanders
        if commanders:
            self.selected_commander.set(commanders[0])
    
    def update_preview(self, event=None):
        """Aktualizuje podgląd armii."""
        if self.creating_army:
            return
            
        size = self.army_size.get()
        budget = self.army_budget.get()
        nation = self.selected_nation.get()
        
        # Aktualizuj informacje
        avg_cost = budget // size if size > 0 else 0
        equipment_percent = self.equipment_level.get()
        self.info_label.config(text=f"📊 {size} żetonów | 💰 {budget} VP | ⚖️ ~{avg_cost} VP/żeton | 🔧 {equipment_percent}% wyposażenia")
        
        # Wygeneruj przykładową armię do podglądu
        preview_army = self.generate_balanced_army_preview(size, budget)
        
        # Wyświetl w text widget
        self.units_text.delete(1.0, tk.END)
        total_cost = 0
        
        for i, unit in enumerate(preview_army, 1):
            # Dodaj informację o upgradach
            upgrades_info = f" +{len(unit.get('upgrades', []))}🔧" if unit.get('upgrades') else ""
            unit_text = f"{i:2}. {unit['type']} {unit['size']} - {unit['cost']} VP{upgrades_info}\n"
            self.units_text.insert(tk.END, unit_text)
            total_cost += unit['cost']
        
        # Podsumowanie
        self.units_text.insert(tk.END, f"\n{'='*30}\n")
        self.units_text.insert(tk.END, f"SUMA: {total_cost} VP\n")
        self.units_text.insert(tk.END, f"BUDŻET: {budget} VP\n")
        self.units_text.insert(tk.END, f"POZOSTAŁO: {budget - total_cost} VP\n")
        
        # Analiza balansu
        self.analyze_army_balance(preview_army)
    
    def generate_balanced_army_preview(self, size, budget):
        """Generuje zbalansowaną armię do podglądu."""
        army = []
        remaining_budget = budget
        remaining_slots = size
        
        # Sortuj typy według wagi (od najważniejszych)
        sorted_types = sorted(self.unit_templates.items(), 
                             key=lambda x: x[1]['weight'], reverse=True)
        
        for unit_type, template in sorted_types:
            if remaining_slots <= 0 or remaining_budget <= 0:
                break
                
            # Oblicz ile jednostek tego typu chcemy
            desired_count = int(size * template['weight'])
            
            # Dla bardzo małych armii (≤3) nie wymuszaj minimum 1 dla każdego typu
            if size <= 3 and desired_count == 0:
                # Małe szanse dla rzadkich typów w mini-armiach
                if random.random() < template['weight'] * 2:
                    desired_count = 1
            elif desired_count == 0:
                # Dla większych armii daj małą szansę na rzadkie typy
                if random.random() < template['weight']:
                    desired_count = 1
            
            actual_count = min(desired_count, remaining_slots, 
                             remaining_budget // template['base_cost'] if template['base_cost'] > 0 else 0)
            
            for _ in range(actual_count):
                if remaining_slots <= 0 or remaining_budget < template['base_cost']:
                    break
                    
                # Wybierz losowy rozmiar jednostki
                unit_size = random.choice(self.unit_sizes)
                
                # Dostosuj koszt w zależności od rozmiaru
                size_multiplier = {"Pluton": 1.0, "Kompania": 1.5, "Batalion": 2.2}
                unit_cost = int(template['base_cost'] * size_multiplier.get(unit_size, 1.0))
                
                # Dodaj losową wariację ±20%
                variation = random.uniform(0.8, 1.2)
                unit_cost = int(unit_cost * variation)
                
                # Automatycznie wybierz upgrady na podstawie poziomu wyposażenia
                selected_upgrades = self.auto_select_upgrades(unit_type, unit_size, unit_cost)
                
                # Dodaj koszt upgradów
                upgrade_cost = sum(self.support_upgrades.get(upgrade, {}).get("purchase", 0) 
                                 for upgrade in selected_upgrades)
                total_unit_cost = unit_cost + upgrade_cost
                
                if total_unit_cost <= remaining_budget:
                    army.append({
                        'type': template['name'],
                        'size': unit_size,
                        'cost': total_unit_cost,
                        'base_cost': unit_cost,
                        'upgrade_cost': upgrade_cost,
                        'unit_type': unit_type,
                        'upgrades': selected_upgrades
                    })
                    remaining_budget -= total_unit_cost
                    remaining_slots -= 1
        
        # Wypełnij pozostałe sloty tanimi jednostkami
        while remaining_slots > 0 and remaining_budget >= 15:
            cheap_types = [('Z', 'Rozpoznanie'), ('P', 'Piechota')]
            unit_type, type_name = random.choice(cheap_types)
            unit_size = 'Pluton'
            unit_cost = min(remaining_budget, random.randint(15, 25))
            
            army.append({
                'type': type_name,
                'size': unit_size, 
                'cost': unit_cost,
                'base_cost': unit_cost,
                'upgrade_cost': 0,
                'unit_type': unit_type,
                'upgrades': []
            })
            remaining_budget -= unit_cost
            remaining_slots -= 1
        
        # ZABEZPIECZENIE: Upewnij się, że nie przekraczamy limitu jednostek
        if len(army) > size:
            print(f"⚠️ UWAGA: Armia ma {len(army)} jednostek, ale limit to {size}. Obcinam do limitu.")
            army = army[:size]
        
        return army
    
    def auto_select_upgrades(self, unit_type, unit_size, base_cost):
        """Automatycznie wybiera upgrady na podstawie typu jednostki i poziomu wyposażenia."""
        equipment_level = self.equipment_level.get()
        
        # Szansa na upgrade zależy od poziomu wyposażenia
        upgrade_chance = equipment_level / 100.0
        
        # Dostępne upgrady dla tego typu jednostki
        available_upgrades = self.allowed_support.get(unit_type, [])
        if not available_upgrades:
            return []
        
        selected_upgrades = []
        
        # Strategia wyboru upgradów według typu jednostki
        if unit_type == "P":  # Piechota - może mieć wiele upgradów
            # Priorytet: granatniki > ckm > transport
            priorities = ["drużyna granatników", "sekcja ckm", "przodek dwukonny", "sam. ciezarowy Fiat 621"]
            max_upgrades = min(3, int(upgrade_chance * 4))  # 0-3 upgrady
            
        elif unit_type in ["TC", "TŚ", "TL", "TS"]:  # Czołgi - tylko obserwator
            priorities = ["obserwator"]
            max_upgrades = 1 if random.random() < upgrade_chance else 0
            
        elif unit_type in ["AC", "AL", "AP"]:  # Artyleria - obserwator + transport
            priorities = ["obserwator", "ciagnik altyleryjski", "sam. ciezarowy Fiat 621"]
            max_upgrades = min(2, int(upgrade_chance * 2.5))
            
        elif unit_type == "K":  # Kawaleria - tylko ckm
            priorities = ["sekcja ckm"]
            max_upgrades = 1 if random.random() < upgrade_chance else 0
            
        else:  # Pozostałe (Z, D, G)
            priorities = ["sam. ciezarowy Fiat 621", "sekcja ckm"]
            max_upgrades = 1 if random.random() < upgrade_chance else 0
        
        # Wybierz upgrady według priorytetów
        transport_selected = False
        for priority_upgrade in priorities:
            if len(selected_upgrades) >= max_upgrades:
                break
            
            if priority_upgrade in available_upgrades:
                # Dodatkowa szansa bazująca na priorytecie
                priority_chance = upgrade_chance * random.uniform(0.7, 1.0)
                
                if random.random() < priority_chance:
                    # Sprawdź czy to transport (tylko jeden na jednostkę)
                    if priority_upgrade in self.transport_types:
                        if not transport_selected:
                            selected_upgrades.append(priority_upgrade)
                            transport_selected = True
                    else:
                        selected_upgrades.append(priority_upgrade)
        
        # Dodaj losowe upgrady jeśli poziom wyposażenia > 70%
        if equipment_level > 70 and len(selected_upgrades) < max_upgrades:
            remaining_upgrades = [u for u in available_upgrades 
                                if u not in selected_upgrades 
                                and (u not in self.transport_types or not transport_selected)]
            
            if remaining_upgrades:
                extra_upgrade = random.choice(remaining_upgrades)
                selected_upgrades.append(extra_upgrade)
        
        return selected_upgrades
    
    def analyze_army_balance(self, army):
        """Analizuje balans armii i wyświetla statystyki."""
        if not army:
            return
            
        # Policz typy jednostek
        type_counts = {}
        total_cost = sum(unit['cost'] for unit in army)
        
        for unit in army:
            unit_type = unit['unit_type']
            type_counts[unit_type] = type_counts.get(unit_type, 0) + 1
        
        # Wyświetl analizę
        self.units_text.insert(tk.END, f"\n📊 ANALIZA BALANSU:\n")
        
        for unit_type, count in sorted(type_counts.items()):
            template = self.unit_templates.get(unit_type, {})
            type_name = template.get('name', unit_type)
            percentage = (count / len(army)) * 100
            self.units_text.insert(tk.END, f"  {type_name}: {count} ({percentage:.0f}%)\n")
    
    def generate_random_army(self):
        """Generuje losową armię."""
        size = random.randint(8, 20)
        budget = random.randint(300, 800)
        
        self.army_size.set(size)
        self.army_budget.set(budget)
        self.update_preview()
        
        self.status_label.config(text="🎲 Wygenerowano losową armię")
    
    def auto_balance_army(self):
        """Automatycznie balansuje armię według optymalnych proporcji."""
        size = self.army_size.get()
        budget = self.army_budget.get()
        
        # Optymalne proporcje dla różnych rozmiarów armii
        if size <= 8:
            # Mała armia - skupiona
            optimal_budget = min(budget, size * 45)
        elif size <= 15:
            # Średnia armia - zbalansowana
            optimal_budget = min(budget, size * 35)
        else:
            # Duża armia - tańsze jednostki
            optimal_budget = min(budget, size * 30)
        
        self.army_budget.set(optimal_budget)
        self.update_preview()
        
        self.status_label.config(text="⚖️ Armia została automatycznie zbalansowana")
    
    def clear_army(self):
        """Czyści podgląd armii."""
        self.units_text.delete(1.0, tk.END)
        self.units_text.insert(tk.END, "Armia została wyczyszczona.\n\nWybierz parametry aby zobaczyć nowy podgląd.")
        self.status_label.config(text="🗑️ Armia wyczyszczona")
    
    def create_army_thread(self):
        """Uruchamia tworzenie armii w głównym wątku GUI (nieblokujące)."""
        if self.creating_army:
            return
        
        # Walidacja parametrów
        if self.army_size.get() < 5 or self.army_size.get() > 25:
            messagebox.showerror("❌ Błąd", "Rozmiar armii musi być między 5 a 25 żetonów!")
            return
            
        if self.army_budget.get() < 250 or self.army_budget.get() > 1000:
            messagebox.showerror("❌ Błąd", "Budżet musi być między 250 a 1000 VP!")
            return
            
        self.creating_army = True
        
        try:
            # Aktualizuj GUI
            self.create_button.config(state='disabled', text="⏳ TWORZENIE...")
            self.status_label.config(text="🏭 Tworzenie armii w toku...")
            
            # Wygeneruj finalną armię
            size = self.army_size.get()
            budget = self.army_budget.get()
            self.final_army = self.generate_final_army(size, budget)
            
            # Inicjalizuj Token Editor
            self.progress_label.config(text="Inicjalizacja Token Editor...")
            if not self.initialize_token_editor():
                return
            
            # Rozpocznij sekwencyjne tworzenie żetonów
            self.current_unit_index = 0
            self.total_units = len(self.final_army)
            self.root.after(100, self.create_next_token)
            
        except Exception as e:
            self.creation_failed(str(e))
    
    def create_next_token(self):
        """Tworzy kolejny żeton w sekwencji z lepszą obsługą błędów."""
        if self.current_unit_index >= self.total_units:
            # Wszystkie żetony utworzone
            self.creation_completed(self.current_unit_index)  # Użyj rzeczywistej liczby
            return
            
        unit = self.final_army[self.current_unit_index]
        progress = ((self.current_unit_index + 1) / self.total_units) * 100
        
        # Aktualizuj progress
        self.update_creation_progress(progress, f"Tworzenie: {unit['name']}")
        
        # Utwórz żeton
        success = self.create_single_token(unit)
        
        if success:
            print(f"✅ Utworzono: {unit['name']}")
        else:
            print(f"❌ Błąd: {unit['name']}")
        
        self.current_unit_index += 1
        
        # Zaplanuj następny żeton z dłuższą przerwą dla stabilności
        self.root.after(800, self.create_next_token)
    
    def generate_final_army(self, size, budget):
        """Generuje finalną armię z dokładnymi nazwami jednostek."""
        nation = self.selected_nation.get()
        commander_full = self.selected_commander.get()
        commander_num = commander_full.split()[0]
        
        # Bazowa armia
        base_army = self.generate_balanced_army_preview(size, budget)
        
        # Konwertuj na finalne jednostki z nazwami
        final_army = []
        for i, unit in enumerate(base_army, 1):
            unit_data = self.convert_to_final_unit(unit, nation, commander_num, i)
            final_army.append(unit_data)
        
        return final_army
    
    def convert_to_final_unit(self, preview_unit, nation, commander_num, index):
        """Konwertuje jednostkę podglądu na finalną jednostkę z pełnymi danymi."""
        
        # Słowniki nazw dla różnych nacji
        if nation == "Polska":
            unit_names = {
                "P": [f"{commander_num}. Pułk Piechoty", f"{commander_num}. Batalion Strzelców", f"{commander_num}. Kompania Grenadierów"],
                "K": [f"{commander_num}. Pułk Ułanów", f"{commander_num}. Szwadron Kawalerii", f"{commander_num}. Oddział Jazdy"],
                "TL": [f"{commander_num}. Pluton Tankietek", f"{commander_num}. Kompania Czołgów Lekkich", f"{commander_num}. Batalion Pancerny"],
                "TŚ": [f"{commander_num}. Pluton Czołgów", f"{commander_num}. Kompania Pancerna", f"{commander_num}. Batalion Czołgów"],
                "AL": [f"{commander_num}. Bateria Artylerii", f"{commander_num}. Dywizjon Artylerii", f"{commander_num}. Pułk Artylerii"],
                "AC": [f"{commander_num}. Bateria Ciężka", f"{commander_num}. Dywizjon Ciężki", f"{commander_num}. Pułk Artylerii Ciężkiej"],
                "Z": [f"{commander_num}. Oddział Rozpoznawczy", f"{commander_num}. Kompania Zaopatrzeniowa", f"{commander_num}. Batalion Wsparcia"]
            }
        else:  # Niemcy
            unit_names = {
                "P": [f"{commander_num}. Infanterie Regiment", f"{commander_num}. Grenadier Bataillon", f"{commander_num}. Schützen Kompanie"],
                "TL": [f"{commander_num}. Panzer Zug", f"{commander_num}. Panzer Kompanie", f"{commander_num}. Panzer Abteilung"],
                "TŚ": [f"{commander_num}. schwere Panzer", f"{commander_num}. Panzer Regiment", f"{commander_num}. Panzer Brigade"],
                "AL": [f"{commander_num}. Artillerie Batterie", f"{commander_num}. Artillerie Abteilung", f"{commander_num}. Artillerie Regiment"],
                "AC": [f"{commander_num}. schwere Artillerie", f"{commander_num}. Haubitze Abteilung", f"{commander_num}. schwere Artillerie Regiment"],
                "Z": [f"{commander_num}. Aufklärungs Zug", f"{commander_num}. Versorgungs Kompanie", f"{commander_num}. Unterstützungs Bataillon"]
            }
        
        unit_type = preview_unit['unit_type']
        names_list = unit_names.get(unit_type, [f"{commander_num}. {preview_unit['type']} Einheit"])
        unit_name = random.choice(names_list)
        
        # Nowy zunifikowany system balansu
        upgrades_list = preview_unit.get('upgrades', [])
        quality = 'standard'  # miejsce na przyszłe quality per unit
        if compute_token:
            computed = compute_token(unit_type, preview_unit['size'], nation, upgrades_list, quality=quality)
            movement = computed.movement
            attack_range = computed.attack_range
            attack_value = computed.attack_value
            combat_value = computed.combat_value
            defense_value = computed.defense_value
            maintenance = computed.maintenance
            total_cost = computed.total_cost
        else:
            # fallback stary mechanizm
            cost = preview_unit.get('base_cost', preview_unit['cost'])
            base_stats = self.generate_unit_stats(unit_type, preview_unit['size'], cost)
            final_stats = self.apply_upgrade_modifiers(base_stats, upgrades_list)
            movement = final_stats['movement']
            attack_range = final_stats['attack_range']
            attack_value = final_stats['attack_value']
            combat_value = final_stats['combat_value']
            defense_value = final_stats['defense_value']
            maintenance = final_stats['maintenance']
            total_cost = preview_unit['cost']
        
        return {
            "name": unit_name,
            "nation": nation,
            "unit_type": unit_type,
            "unit_size": preview_unit['size'],
            "movement_points": str(movement),
            "attack_range": str(attack_range),
            "attack_value": str(attack_value),
            "combat_value": str(combat_value),
            "defense_value": str(defense_value),
            "unit_maintenance": str(maintenance),
            "purchase_value": str(total_cost),
            "sight_range": str(computed.sight if compute_token else final_stats['sight']),
            "support": ", ".join(upgrades_list)
        }
    
    def generate_unit_stats(self, unit_type, unit_size, cost):
        """Stub – zachowany dla kompatybilności, gdy brak balance.model."""
        return {"movement": 0, "attack_range": 0, "attack_value": 0, "combat_value": 0, "defense_value": 0, "sight": 0, "maintenance": 0}

    def apply_upgrade_modifiers(self, base_stats, upgrades):
        """Stub – bez modyfikacji."""
        return base_stats  # stub
    
    def initialize_token_editor(self):
        """Inicjalizuje Token Editor w głównym oknie (bez dodatkowego okna)."""
        if self.token_editor is None:
            try:
                from token_editor_prototyp import TokenEditor
                
                # NIE twórz nowego okna - użyj istniejącego root
                # Ale ukryj Token Editor wizualnie
                self.root.withdraw()  # Ukryj główne okno na czas inicjalizacji
                
                # Utwórz proste okno dla Token Editor
                token_window = tk.Toplevel()
                token_window.title("Token Editor - Tryb Automatyczny")
                token_window.geometry("200x100")
                token_window.configure(bg="darkolivegreen")
                
                # Umieść poza ekranem
                token_window.geometry("+5000+5000")
                
                self.token_editor = TokenEditor(token_window)
                
                # Pokaż z powrotem główne okno
                self.root.deiconify()
                
                return True
                
            except ImportError as e:
                self.root.deiconify()  # Przywróć okno nawet przy błędzie
                self.creation_failed(f"Nie można załadować Token Editor: {e}")
                return False
        return True
    
    def create_single_token(self, unit):
        """Tworzy pojedynczy żeton używając Token Editor z lepszą obsługą błędów."""
        try:
            # Sprawdź czy Token Editor nadal istnieje
            if not self.token_editor or not hasattr(self.token_editor, 'nation'):
                print(f"Token Editor uszkodzony, pomijam {unit['name']}")
                return False
            
            # Ustaw podstawowe parametry
            commander = self.selected_commander.get()
            
            try:
                # Bezpieczne ustawienie parametrów
                self.token_editor.nation.set(unit["nation"])
                self.token_editor.unit_type.set(unit["unit_type"]) 
                self.token_editor.unit_size.set(unit["unit_size"])
                
                if hasattr(self.token_editor, 'selected_commander'):
                    self.token_editor.selected_commander.set(commander)
                
                # Ustaw statystyki
                self.token_editor.movement_points.set(unit["movement_points"])
                self.token_editor.attack_range.set(unit["attack_range"])
                self.token_editor.attack_value.set(unit["attack_value"])
                self.token_editor.combat_value.set(unit["combat_value"])
                self.token_editor.defense_value.set(unit["defense_value"])
                self.token_editor.unit_maintenance.set(unit["unit_maintenance"])
                self.token_editor.purchase_value.set(unit["purchase_value"])
                self.token_editor.sight_range.set(unit["sight_range"])
                
            except tk.TclError as e:
                print(f"Błąd GUI Token Editor dla {unit['name']}: {e}")
                return False
            
            # Zastosuj upgrady bezpiecznie
            if unit["support"] and hasattr(self.token_editor, 'selected_supports'):
                try:
                    # Wyczyść poprzednie upgrady
                    self.token_editor.selected_supports.clear()
                    if hasattr(self.token_editor, 'selected_transport'):
                        self.token_editor.selected_transport.set("")
                    
                    # Zastosuj nowe upgrady
                    upgrades = [u.strip() for u in unit["support"].split(",") if u.strip()]
                    for upgrade in upgrades:
                        if upgrade in self.token_editor.transport_types:
                            self.token_editor.selected_transport.set(upgrade)
                        else:
                            self.token_editor.selected_supports.add(upgrade)
                            
                except Exception as e:
                    print(f"Błąd ustawiania upgradów dla {unit['name']}: {e}")
                    # Kontynuuj bez upgradów
            
            # Aktualizuj pola liczbowe
            try:
                if hasattr(self.token_editor, 'update_numeric_fields'):
                    self.token_editor.update_numeric_fields()
            except Exception as e:
                print(f"Błąd aktualizacji pól dla {unit['name']}: {e}")
            
            # Zapisz żeton
            try:
                self.token_editor.save_token(auto_mode=True, auto_name=unit['name'])
                return True
            except Exception as e:
                print(f"Błąd zapisu żetonu {unit['name']}: {e}")
                return False
                
        except Exception as e:
            print(f"Ogólny błąd tworzenia żetonu {unit['name']}: {e}")
            return False
    
    def update_creation_progress(self, progress, message):
        """Aktualizuje progress bar i wiadomość."""
        self.progress_bar['value'] = progress
        self.progress_label.config(text=message)
        self.status_label.config(text=f"🏭 {message}")
    
    def creation_completed(self, units_created):
        """Obsługuje zakończenie tworzenia armii z czyszczeniem."""
        self.creating_army = False
        
        # Zamknij Token Editor jeśli istnieje
        if self.token_editor and hasattr(self.token_editor, 'root'):
            try:
                self.token_editor.root.destroy()
            except:
                pass
            self.token_editor = None
        
        self.progress_bar['value'] = 100
        self.progress_label.config(text=f"✅ Ukończono! Próbowano utworzyć {units_created} żetonów")
        self.status_label.config(text=f"🎉 Armia ukończona! Próbowano utworzyć {units_created} żetonów")
        
        self.create_button.config(state='normal', text="💾 UTWÓRZ ARMIĘ")
        
        # Sprawdź ile rzeczywiście zostało utworzonych
        actual_count = self.count_actual_created_tokens()
        
        # Wyświetl podsumowanie
        messagebox.showinfo("🎉 Ukończono!", 
                           f"Proces tworzenia armii zakończony!\n\n"
                           f"📊 Próbowano utworzyć: {units_created} żetonów\n"
                           f"✅ Rzeczywiście utworzono: {actual_count} żetonów\n"
                           f"🎖️ Dowódca: {self.selected_commander.get()}\n"
                           f"🏴 Nacja: {self.selected_nation.get()}\n"
                           f"💰 Budżet: {self.army_budget.get()} VP\n\n" +
                           f"Żetony zapisane w: assets/tokens/{self.selected_nation.get()}/")
        
        # Odśwież statystyki
        self.refresh_token_stats()
    
    def count_actual_created_tokens(self):
        """Zlicza rzeczywiście utworzone żetony dla aktualnej nacji."""
        try:
            nation = self.selected_nation.get()
            count, _ = self.count_nation_tokens(nation)
            return count
        except:
            return 0
    
    def creation_failed(self, error_message):
        """Obsługuje błąd podczas tworzenia armii."""
        self.creating_army = False
        self.progress_label.config(text="❌ Błąd tworzenia armii")
        self.status_label.config(text="❌ Błąd podczas tworzenia armii")
        
        self.create_button.config(state='normal', text="💾 UTWÓRZ ARMIĘ")
        
        messagebox.showerror("❌ Błąd", 
                            f"Wystąpił błąd podczas tworzenia armii:\n\n{error_message}")
    
    # === FUNKCJE ZARZĄDZANIA FOLDERAMI ===
    
    def refresh_token_stats(self):
        """Odświeża statystyki żetonów w folderach."""
        try:
            tokens_dir = Path("assets/tokens")
            if not tokens_dir.exists():
                self.stats_label.config(text="📂 Folder assets/tokens nie istnieje")
                return
            
            # Sprawdź foldery nacji
            polish_count, polish_vp = self.count_nation_tokens("Polska")
            german_count, german_vp = self.count_nation_tokens("Niemcy")
            
            stats_text = f"📊 STATYSTYKI ŻETONÓW:\n"
            stats_text += f"🇵🇱 Polska: {polish_count} żetonów ({polish_vp} VP)\n"
            stats_text += f"🇩🇪 Niemcy: {german_count} żetonów ({german_vp} VP)"
            
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            self.stats_label.config(text=f"❌ Błąd: {str(e)}")
    
    def count_nation_tokens(self, nation):
        """Zlicza żetony i VP dla danej nacji."""
        tokens_dir = Path(f"assets/tokens/{nation}")
        if not tokens_dir.exists():
            return 0, 0
        
        count = 0
        total_vp = 0
        
        for token_folder in tokens_dir.iterdir():
            if token_folder.is_dir():
                json_file = token_folder / "token.json"
                if json_file.exists():
                    count += 1
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            total_vp += int(data.get('purchase_value', 0))
                    except:
                        pass  # Ignoruj błędy odczytu
        
        return count, total_vp
    
    def clean_polish_tokens(self):
        """Czyści polskie żetony z potwierdzeniem."""
        self.clean_nation_tokens("Polska", "🇵🇱")
    
    def clean_german_tokens(self):
        """Czyści niemieckie żetony z potwierdzeniem."""
        self.clean_nation_tokens("Niemcy", "🇩🇪")
    
    def clean_all_tokens(self):
        """Czyści wszystkie żetony z potwierdzeniem."""
        if messagebox.askyesno("⚠️ UWAGA!", 
                              "Czy na pewno chcesz usunąć WSZYSTKIE żetony?\n\n"
                              "Ta operacja nie może być cofnięta!\n\n"
                              "🗑️ Zostaną usunięte:\n"
                              "• Wszystkie polskie żetony\n"
                              "• Wszystkie niemieckie żetony\n"
                              "• Plik index.json"):
            
            try:
                import shutil
                tokens_dir = Path("assets/tokens")
                
                if tokens_dir.exists():
                    # Usuń foldery nacji
                    for nation_dir in tokens_dir.iterdir():
                        if nation_dir.is_dir() and nation_dir.name in ["Polska", "Niemcy"]:
                            shutil.rmtree(nation_dir)
                    
                    # Usuń index.json
                    index_file = tokens_dir / "index.json"
                    if index_file.exists():
                        index_file.unlink()
                
                self.refresh_token_stats()
                messagebox.showinfo("✅ Sukces!", "Wszystkie żetony zostały usunięte.")
                
            except Exception as e:
                messagebox.showerror("❌ Błąd", f"Błąd podczas usuwania:\n{str(e)}")
    
    def clean_nation_tokens(self, nation, flag):
        """Czyści żetony wybranej nacji z potwierdzeniem."""
        # Sprawdź ile żetonów do usunięcia
        count, vp = self.count_nation_tokens(nation)
        
        if count == 0:
            messagebox.showinfo("ℹ️ Info", f"Brak żetonów {flag} {nation} do usunięcia.")
            return
        
        if messagebox.askyesno("⚠️ POTWIERDŹ USUNIĘCIE", 
                              f"Czy na pewno chcesz usunąć żetony {flag} {nation}?\n\n"
                              f"🗑️ Do usunięcia:\n"
                              f"• {count} żetonów\n"
                              f"• {vp} VP łącznie\n\n"
                              f"Ta operacja nie może być cofnięta!"):
            
            try:
                import shutil
                nation_dir = Path(f"assets/tokens/{nation}")
                
                if nation_dir.exists():
                    shutil.rmtree(nation_dir)
                
                # Aktualizuj index.json
                self.update_index_after_deletion(nation)
                
                self.refresh_token_stats()
                messagebox.showinfo("✅ Sukces!", 
                                   f"Usunięto {count} żetonów {flag} {nation} ({vp} VP).")
                
            except Exception as e:
                messagebox.showerror("❌ Błąd", f"Błąd podczas usuwania:\n{str(e)}")
    
    def update_index_after_deletion(self, deleted_nation):
        """Aktualizuje index.json po usunięciu żetonów nacji."""
        try:
            index_file = Path("assets/tokens/index.json")
            if not index_file.exists():
                return
            
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # Usuń żetony usuniętej nacji z indeksu
            if deleted_nation in index_data:
                del index_data[deleted_nation]
            
            # Zapisz zaktualizowany indeks
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Błąd aktualizacji index.json: {e}")

def main():
    """Główna funkcja aplikacji."""
    root = tk.Tk()
    app = ArmyCreatorStudio(root)
    
    # Wyśrodkuj okno na ekranie
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
