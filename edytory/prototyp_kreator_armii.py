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
from collections import Counter
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
        self.excluded_unit_types = {"AP", "D", "G"}
        self.unit_templates = {
            "P": {"name": "Piechota", "base_cost": 25, "weight": 0.30, "category": "INFANTRY"},
            "K": {"name": "Kawaleria", "base_cost": 30, "weight": 0.08, "category": "CAVALRY_RECON"},
            "R": {"name": "Zwiad", "base_cost": 28, "weight": 0.07, "category": "CAVALRY_RECON"},
            "TL": {"name": "Czołg Lekki", "base_cost": 35, "weight": 0.10, "category": "TANKS"},
            "TŚ": {"name": "Czołg Średni", "base_cost": 45, "weight": 0.07, "category": "TANKS"},
            "TC": {"name": "Czołg Ciężki", "base_cost": 60, "weight": 0.04, "category": "TANKS"},
            "TS": {"name": "Sam. Pancerny", "base_cost": 35, "weight": 0.04, "category": "TANKS"},
            "AL": {"name": "Artyleria Lekka", "base_cost": 35, "weight": 0.09, "category": "ARTILLERY"},
            "AC": {"name": "Artyleria Ciężka", "base_cost": 55, "weight": 0.06, "category": "ARTILLERY"},
            "Z": {"name": "Zaopatrzenie", "base_cost": 20, "weight": 0.15, "category": "SUPPLY"}
        }

        self.category_generation_order = [
            "SUPPLY",
            "TANKS",
            "INFANTRY",
            "ARTILLERY",
            "CAVALRY_RECON"
        ]

        self.unit_sizes = ["Pluton", "Kompania", "Batalion"]
        self.size_multipliers = {"Pluton": 1.0, "Kompania": 1.5, "Batalion": 2.2}
        self.tank_infantry_offset = 1  # o ile piechota może przewyższyć liczbę czołgów
          # Zmienne GUI
        self.selected_nation = tk.StringVar(value="Polska")
        self.selected_commander = tk.StringVar(value="2 (Polska)")
        self.army_size = tk.IntVar(value=10)
        self.army_budget = tk.IntVar(value=500)
        self.creating_army = False
        
        # Lista utworzonych jednostek
        self.created_units = []
        self._cached_tokens_by_nation = None
        
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
            "R": ["obserwator"],
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
            "Z": ["drużyna granatników", "sekcja km.ppanc", "sekcja ckm", "obserwator"],
        }

        for unit_type in list(self.allowed_support.keys()):
            if unit_type in self.excluded_unit_types:
                self.allowed_support.pop(unit_type, None)

        for unit_type in list(self.unit_templates.keys()):
            if unit_type in self.excluded_unit_types:
                self.unit_templates.pop(unit_type, None)
        
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
        
        ttk.Button(
            action_frame,
            text="🎮 Armie z gotowych żetonów",
            command=self.generate_existing_token_armies,
            style='Military.TButton'
        ).pack(fill=tk.X, pady=1)
        
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
    
    def _build_category_map(self):
        categories = {}
        for unit_type, template in self.unit_templates.items():
            category = template.get("category", unit_type)
            category_entry = categories.setdefault(category, {"weight": 0.0, "unit_types": []})
            category_entry["unit_types"].append(unit_type)
            category_entry["weight"] += max(template.get("weight", 0.0), 0.0)

        # Jeśli waga kategorii wynosi 0, rozdziel po równo między jej typy
        for category, data in categories.items():
            if data["weight"] <= 0:
                data["weight"] = float(len(data["unit_types"]))

        return categories

    def _allocate_category_counts(self, size, categories):
        if size <= 0 or not categories:
            return {}

        total_weight = sum(data["weight"] for data in categories.values())
        if total_weight <= 0:
            total_weight = float(len(categories))

        counts = {}
        fractional = []

        for category, data in categories.items():
            weight = data["weight"] if data["weight"] > 0 else total_weight / len(categories)
            exact = (weight / total_weight) * size
            base_count = int(exact)
            counts[category] = base_count
            fractional.append((exact - base_count, category))

        assigned = sum(counts.values())
        fractional.sort(key=lambda item: item[0], reverse=True)

        # Rozdziel pozostałe sloty według największych ułamków
        while assigned < size and fractional:
            for _, category in fractional:
                if assigned >= size:
                    break
                counts[category] += 1
                assigned += 1

        supply_min = min(2, size) if "SUPPLY" in categories else 0
        if supply_min and counts.get("SUPPLY", 0) < supply_min:
            diff = supply_min - counts.get("SUPPLY", 0)
            counts["SUPPLY"] = supply_min
            assigned += diff

        counts = self._rebalance_tanks_vs_infantry(counts, size, supply_min)
        assigned = sum(counts.values())

        # Jeśli przekroczyliśmy liczbę slotów, odejmij od największych kategorii poza SUPPLY
        if assigned > size:
            adjustable = [cat for cat in self.category_generation_order if cat != "SUPPLY" and counts.get(cat, 0) > 0]
            idx = 0
            while assigned > size and adjustable:
                cat = adjustable[idx % len(adjustable)]
                if counts.get(cat, 0) > 0:
                    counts[cat] -= 1
                    assigned -= 1
                if counts.get(cat, 0) == 0 and cat in adjustable:
                    adjustable.remove(cat)
                idx += 1

        # Jeśli nadal mamy wolne sloty (np. brak kategorii poza SUPPLY), rozdziel według kolejności
        if assigned < size:
            for category in self.category_generation_order:
                if assigned >= size:
                    break
                if category in counts:
                    counts[category] += 1
                    assigned += 1

        counts = self._rebalance_tanks_vs_infantry(counts, size, supply_min)
        assigned = sum(counts.values())

        if assigned > size:
            adjustable = [cat for cat in self.category_generation_order if counts.get(cat, 0) > 0]
            idx = 0
            while assigned > size and adjustable:
                cat = adjustable[idx % len(adjustable)]
                idx += 1
                if cat == "SUPPLY" and counts.get(cat, 0) <= supply_min:
                    continue
                if counts.get(cat, 0) > 0:
                    counts[cat] -= 1
                    assigned -= 1

        elif assigned < size:
            for category in ["TANKS", "INFANTRY", "ARTILLERY", "CAVALRY_RECON", "SUPPLY"]:
                if assigned >= size:
                    break
                counts[category] = counts.get(category, 0) + 1
                assigned += 1

        return counts

    def _select_unit_type_for_category(self, category, categories):
        data = categories.get(category)
        if not data:
            return None

        candidates = data["unit_types"]
        weights = [self.unit_templates[unit_type].get("weight", 0.0) for unit_type in candidates]
        total_weight = sum(weights)

        if total_weight <= 0:
            return random.choice(candidates)

        pick = random.uniform(0, total_weight)
        cumulative = 0.0
        for unit_type, weight in zip(candidates, weights):
            cumulative += weight
            if pick <= cumulative:
                return unit_type

        return candidates[-1]

    def _rebalance_tanks_vs_infantry(self, counts, size, supply_min):
        if size <= 2:
            return counts

        tanks = counts.get("TANKS", 0)
        infantry = counts.get("INFANTRY", 0)

        if infantry <= 0:
            return counts

        def desired_tanks(current_counts):
            current_infantry = current_counts.get("INFANTRY", 0)
            if current_infantry <= 0:
                return 0
            return max(1, current_infantry - self.tank_infantry_offset)

        target = desired_tanks(counts)
        assigned = sum(counts.values())

        # Jeśli mamy wolne sloty, dołóż czołgi do targetu
        while counts.get("TANKS", 0) < target and assigned < size:
            counts["TANKS"] = counts.get("TANKS", 0) + 1
            assigned += 1

        if counts.get("TANKS", 0) >= target:
            if counts.get("TANKS", 0) > counts.get("INFANTRY", 0):
                counts["TANKS"] = counts.get("INFANTRY", 0)
            return counts

        donors = [
            cat for cat in self.category_generation_order
            if cat not in {"SUPPLY", "TANKS"} and counts.get(cat, 0) > 0
        ]

        attempts = 0
        max_attempts = size * max(1, len(donors))

        while counts.get("TANKS", 0) < desired_tanks(counts) and attempts < max_attempts:
            attempts += 1
            if not donors:
                break
            donor = donors[attempts % len(donors)]
            donor_min = 0
            if donor == "INFANTRY":
                donor_min = max(desired_tanks(counts), 1)
            if counts.get(donor, 0) <= donor_min:
                continue
            counts[donor] -= 1
            counts["TANKS"] = counts.get("TANKS", 0) + 1

        if counts.get("TANKS", 0) > counts.get("INFANTRY", 0):
            counts["TANKS"] = counts.get("INFANTRY", 0)

        return counts

    def _create_preview_unit(self, unit_type, remaining_budget, force_basic=False):
        template = self.unit_templates.get(unit_type)
        if not template:
            return None

        if force_basic:
            unit_size = "Pluton"
        else:
            if unit_type == "Z":
                size_pool = ["Pluton", "Pluton", "Pluton", "Kompania", "Kompania", "Batalion"]
            elif self.unit_templates.get(unit_type, {}).get("category") == "TANKS":
                size_pool = ["Pluton", "Pluton", "Kompania", "Pluton", "Kompania", "Batalion"]
            else:
                size_pool = self.unit_sizes
            unit_size = random.choice(size_pool)
        size_multiplier = self.size_multipliers.get(unit_size, 1.0)
        base_cost = int(template["base_cost"] * size_multiplier)

        variation = 1.0 if force_basic else random.uniform(0.8, 1.2)
        unit_cost = max(1, int(base_cost * variation))

        selected_upgrades = []
        if not force_basic:
            selected_upgrades = self.auto_select_upgrades(unit_type, unit_size, unit_cost)

        upgrade_cost = sum(self.support_upgrades.get(upgrade, {}).get("purchase", 0) for upgrade in selected_upgrades)
        total_cost = unit_cost + upgrade_cost

        if total_cost > remaining_budget:
            return None

        return {
            'type': template['name'],
            'size': unit_size,
            'cost': total_cost,
            'base_cost': unit_cost,
            'upgrade_cost': upgrade_cost,
            'unit_type': unit_type,
            'upgrades': selected_upgrades
        }

    def generate_balanced_army_preview(self, size, budget):
        """Generuje armię, losując najpierw kategorię (P, T, K+R, A, Z), a dopiero potem konkretny typ."""
        army = []
        if size <= 0 or budget <= 0:
            return army

        categories = self._build_category_map()
        category_counts = self._allocate_category_counts(size, categories)

        remaining_budget = budget
        remaining_slots = size
        added_per_category = {category: 0 for category in category_counts.keys()}

        generation_order = [
            category for category in self.category_generation_order if category in category_counts
        ]
        for category in category_counts.keys():
            if category not in generation_order:
                generation_order.append(category)

        for category in generation_order:
            target = category_counts.get(category, 0)
            if target <= 0:
                continue

            attempts = 0
            max_attempts = max(5, target * 3)

            while (
                added_per_category.get(category, 0) < target
                and remaining_slots > 0
                and remaining_budget > 0
                and attempts < max_attempts
            ):
                attempts += 1
                unit_type = self._select_unit_type_for_category(category, categories)
                if not unit_type:
                    break

                unit_entry = self._create_preview_unit(unit_type, remaining_budget)
                if unit_entry is None:
                    unit_entry = self._create_preview_unit(unit_type, remaining_budget, force_basic=True)

                if unit_entry is None:
                    cheap_types = sorted(
                        categories[category]["unit_types"],
                        key=lambda t: self.unit_templates[t]["base_cost"]
                    )
                    for fallback_type in cheap_types:
                        unit_entry = self._create_preview_unit(fallback_type, remaining_budget, force_basic=True)
                        if unit_entry is not None:
                            unit_type = fallback_type
                            break

                if unit_entry is None:
                    break

                army.append(unit_entry)
                remaining_budget -= unit_entry['cost']
                remaining_slots -= 1
                added_per_category[category] = added_per_category.get(category, 0) + 1

        fallback_types = ['TL', 'P', 'R', 'Z']
        fallback_idx = 0
        guard = 0
        while remaining_slots > 0 and remaining_budget > 0 and guard < size * 4:
            guard += 1
            unit_type = fallback_types[fallback_idx % len(fallback_types)]
            fallback_idx += 1
            unit_entry = self._create_preview_unit(unit_type, remaining_budget, force_basic=True)
            if unit_entry is None:
                continue
            army.append(unit_entry)
            remaining_budget -= unit_entry['cost']
            remaining_slots -= 1

        if len(army) > size:
            army = army[:size]

        return army
    
    def generate_existing_token_armies(self):
        """Buduje dwie armie (Polska i Niemcy) korzystając z już utworzonych żetonów."""
        tokens_by_nation = self.load_existing_tokens()
        polish_tokens = tokens_by_nation.get("Polska", [])
        german_tokens = tokens_by_nation.get("Niemcy", [])

        messages = []
        if not polish_tokens:
            messages.append("Brak dostępnych żetonów dla 🇵🇱 Polski.")
        if not german_tokens:
            messages.append("Brak dostępnych żetonów dla 🇩🇪 Niemiec.")

        if messages:
            self.units_text.delete(1.0, tk.END)
            self.units_text.insert(tk.END, "\n".join(messages) + "\n")
            self.info_label.config(text=" | ".join(messages))
            self.status_label.config(text="⚠️ Brakuje żetonów do zbudowania obu armii")
            return

        size = self.army_size.get()
        budget = self.army_budget.get()

        planned_polish = self.generate_balanced_army_preview(size, budget)
        planned_german = self.generate_balanced_army_preview(size, budget)

        polish_result = self._map_preview_to_existing_tokens(planned_polish, polish_tokens, budget)
        german_result = self._map_preview_to_existing_tokens(planned_german, german_tokens, budget)

        self._render_existing_armies(polish_result, german_result)

        info_summary = (
            f"🇵🇱 {polish_result.get('actual_count', 0)}/{polish_result.get('desired_count', 0)} żetonów "
            f"({polish_result.get('total_cost', 0)} VP) | "
            f"🇩🇪 {german_result.get('actual_count', 0)}/{german_result.get('desired_count', 0)} żetonów "
            f"({german_result.get('total_cost', 0)} VP)"
        )
        self.info_label.config(text=info_summary)
        self.status_label.config(text="🎮 Armie z gotowych żetonów przygotowane")

    def load_existing_tokens(self, force=False):
        """Ładuje listę dostępnych żetonów dla każdej nacji, z prostym cache."""
        if not force and self._cached_tokens_by_nation is not None:
            return self._cached_tokens_by_nation

        tokens_by_nation = self._load_tokens_from_filesystem()
        total_found = sum(len(items) for items in tokens_by_nation.values())

        if total_found == 0:
            tokens_by_nation = self._load_tokens_from_save()

        self._cached_tokens_by_nation = tokens_by_nation
        return tokens_by_nation

    def _load_tokens_from_filesystem(self):
        """Przeszukuje folder assets/tokens i próbuje wczytać token.json dla każdej jednostki."""
        base_dir = Path("assets/tokens")
        tokens_by_nation = {"Polska": [], "Niemcy": []}

        if not base_dir.exists():
            return tokens_by_nation

        for nation in tokens_by_nation.keys():
            nation_dir = base_dir / nation
            if not nation_dir.exists():
                continue

            for token_dir in nation_dir.iterdir():
                if not token_dir.is_dir():
                    continue

                json_path = token_dir / "token.json"
                if not json_path.exists():
                    continue

                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        raw_data = json.load(f)
                except Exception as exc:
                    print(f"⚠️ Błąd odczytu {json_path}: {exc}")
                    continue

                record = self._extract_token_record(raw_data, default_nation=nation)
                if record:
                    tokens_by_nation[record["nation"]].append(record)

        for nation_tokens in tokens_by_nation.values():
            nation_tokens.sort(key=lambda t: (t.get("unit_type"), t.get("unit_size"), t.get("price", 0)))

        return tokens_by_nation

    def _load_tokens_from_save(self):
        """Fallback: pobiera żetony z zapisu saves/after_deployment.json."""
        tokens_by_nation = {"Polska": [], "Niemcy": []}
        save_path = Path("saves/after_deployment.json")

        if not save_path.exists():
            return tokens_by_nation

        try:
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            print(f"⚠️ Błąd odczytu {save_path}: {exc}")
            return tokens_by_nation

        for entry in data.get("tokens", []):
            stats = entry.get("stats", {})
            raw_record = {
                "id": entry.get("id"),
                "stats": stats,
                "support": entry.get("support"),
                "nation": stats.get("nation"),
            }
            record = self._extract_token_record(raw_record, default_nation=stats.get("nation"))
            if record:
                tokens_by_nation[record["nation"]].append(record)

        for nation_tokens in tokens_by_nation.values():
            nation_tokens.sort(key=lambda t: (t.get("unit_type"), t.get("unit_size"), t.get("price", 0)))

        return tokens_by_nation

    def _extract_token_record(self, raw_data, default_nation=None):
        """Normalizuje strukturę danych żetonu, zwraca None jeśli brakuje kluczowych pól."""
        stats = raw_data.get("stats", raw_data)
        nation = stats.get("nation") or raw_data.get("nation") or default_nation
        if nation not in {"Polska", "Niemcy"}:
            return None

        unit_type = stats.get("unit_type") or stats.get("unitType") or raw_data.get("unit_type")
        if not unit_type or unit_type in self.excluded_unit_types:
            return None

        unit_size = stats.get("unit_size") or stats.get("unitSize") or raw_data.get("unit_size") or "Pluton"
        price_value = (
            stats.get("price")
            or stats.get("purchase_value")
            or raw_data.get("purchase_value")
            or raw_data.get("price")
        )
        price = self._to_int(price_value, 0)

        name = (
            stats.get("label")
            or stats.get("unit_full_name")
            or raw_data.get("name")
            or raw_data.get("id")
            or f"{unit_type} {unit_size}"
        )
        token_id = raw_data.get("id") or stats.get("label") or name

        support = stats.get("support") or raw_data.get("support")
        if isinstance(support, list):
            support = ", ".join(str(item) for item in support)
        elif not isinstance(support, str):
            support = ""

        image = stats.get("image") or raw_data.get("image")

        return {
            "id": token_id,
            "name": name,
            "unit_type": unit_type,
            "unit_size": unit_size,
            "price": price,
            "nation": nation,
            "support": support,
            "image": image,
        }

    def _map_preview_to_existing_tokens(self, planned_units, tokens, budget):
        """Próbuje przypisać planowane jednostki do istniejących żetonów."""
        available = [dict(token) for token in tokens]
        random.shuffle(available)

        def pop_first(predicate):
            for idx, token in enumerate(available):
                if predicate(token):
                    return available.pop(idx)
            return None

        selected = []
        total_cost = 0

        for planned in planned_units:
            match = pop_first(
                lambda token: token.get("unit_type") == planned["unit_type"]
                and token.get("unit_size") == planned["size"]
            )
            if match is None:
                match = pop_first(lambda token: token.get("unit_type") == planned["unit_type"])
            if match is None and available:
                match = pop_first(lambda token: True)

            if match:
                match = dict(match)
                match["planned"] = planned
                price = self._to_int(match.get("price"), 0)
                total_cost += price
                selected.append(match)

        desired_count = len(planned_units)

        if len(selected) < desired_count and available:
            available.sort(key=lambda token: self._to_int(token.get("price"), 0))
            while available and len(selected) < desired_count:
                fallback = dict(available.pop(0))
                fallback["planned"] = None
                price = self._to_int(fallback.get("price"), 0)
                total_cost += price
                selected.append(fallback)

        z_count = sum(1 for token in selected if token.get("unit_type") == "Z")

        return {
            "units": selected,
            "total_cost": total_cost,
            "budget": budget,
            "desired_count": desired_count,
            "actual_count": len(selected),
            "z_count": z_count,
        }

    def _render_existing_armies(self, polish_result, german_result):
        self.units_text.delete(1.0, tk.END)
        self.units_text.insert(tk.END, "🎮 ARMIE Z GOTOWYCH ŻETONÓW\n\n")
        self._render_single_existing_army("Polska", polish_result)
        self._render_single_existing_army("Niemcy", german_result)

    def _render_single_existing_army(self, nation, result):
        flag = "🇵🇱" if nation == "Polska" else "🇩🇪" if nation == "Niemcy" else ""
        units = result.get("units", [])
        desired = result.get("desired_count", len(units))
        total_cost = result.get("total_cost", 0)
        budget = result.get("budget", 0)
        diff = budget - total_cost

        header = f"{flag} {nation} ({len(units)}/{desired} jednostek)\n"
        self.units_text.insert(tk.END, header)

        for idx, token in enumerate(units, start=1):
            name = token.get("name") or token.get("id")
            unit_type = token.get("unit_type", "?")
            unit_size = token.get("unit_size", "?")
            price = self._to_int(token.get("price"), 0)
            planned = token.get("planned")
            plan_info = ""
            if planned:
                plan_info = f" | plan: {planned['unit_type']} {planned['size']}"
            self.units_text.insert(
                tk.END,
                f"{idx:2}. {name} [{unit_type} {unit_size}] - {price} VP{plan_info}\n",
            )

        self.units_text.insert(
            tk.END,
            f"SUMA: {total_cost} VP | BUDŻET: {budget} VP | RÓŻNICA: {diff:+} VP\n",
        )

        missing = desired - result.get("actual_count", len(units))
        if missing > 0:
            self.units_text.insert(tk.END, f"⚠️ Brakuje {missing} jednostek do pełnej armii.\n")

        if desired >= 2 and result.get("z_count", 0) < 2:
            self.units_text.insert(tk.END, "⚠️ Mniej niż 2 jednostki zaopatrzenia dostępne.\n")

        self.units_text.insert(tk.END, "\n")

    def _to_int(self, value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    
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
            
        elif unit_type in ["AC", "AL"]:  # Artyleria - obserwator + transport
            priorities = ["obserwator", "ciagnik altyleryjski", "sam. ciezarowy Fiat 621"]
            max_upgrades = min(2, int(upgrade_chance * 2.5))
            
        elif unit_type == "K":  # Kawaleria - tylko ckm
            priorities = ["sekcja ckm"]
            max_upgrades = 1 if random.random() < upgrade_chance else 0
        elif unit_type == "R":  # Zwiad - opcjonalny obserwator
            priorities = ["obserwator"]
            max_upgrades = 1 if random.random() < upgrade_chance else 0
            
        else:  # Pozostałe (np. Z)
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
            
        # Policz typy jednostek oraz rozkład kategorii
        type_counts = {}
        category_counts = Counter()
        total_cost = sum(unit['cost'] for unit in army)

        for unit in army:
            unit_type = unit['unit_type']
            type_counts[unit_type] = type_counts.get(unit_type, 0) + 1
            category = self.unit_templates.get(unit_type, {}).get('category', 'INNE')
            category_counts[category] += 1
        
        # Wyświetl analizę
        self.units_text.insert(tk.END, f"\n📊 ANALIZA BALANSU:\n")
        
        z_count = type_counts.get('Z', 0)
        infantry_count = category_counts.get('INFANTRY', 0)
        tank_count = category_counts.get('TANKS', 0)
        cav_recon_count = category_counts.get('CAVALRY_RECON', 0)
        artillery_count = category_counts.get('ARTILLERY', 0)
        supply_count = category_counts.get('SUPPLY', 0)

        self.units_text.insert(
            tk.END,
            f"  ⚔️ Kategorie: P={infantry_count} | T={tank_count} | K+R={cav_recon_count} | A={artillery_count} | Z={supply_count}\n"
        )

        if infantry_count > 0:
            ratio = tank_count / infantry_count
            self.units_text.insert(
                tk.END,
                f"  📐 Relacja czołgi/piechota: {tank_count}/{infantry_count} (~{ratio:.2f}x)\n"
            )
        else:
            self.units_text.insert(tk.END, "  📐 Relacja czołgi/piechota: brak piechoty w składzie\n")

        self.units_text.insert(
            tk.END,
            f"  🔄 K+R vs A vs Z: {cav_recon_count}/{artillery_count}/{supply_count}\n"
        )
        
        tank_expectation = max(1, infantry_count - self.tank_infantry_offset) if infantry_count > 0 else 0
        if infantry_count > 0 and tank_count == 0:
            self.units_text.insert(tk.END, "  ❌ Brak czołgów względem piechoty – rozważ ponowne losowanie.\n")
        elif tank_count < tank_expectation:
            self.units_text.insert(tk.END, f"  ⚠️ Czołgi odstają od piechoty (oczekiwano ≥{tank_expectation}).\n")
        
        for unit_type, count in sorted(type_counts.items()):
            template = self.unit_templates.get(unit_type, {})
            type_name = template.get('name', unit_type)
            percentage = (count / len(army)) * 100
            
            # Oznacz jednostki Z jako PE collectors
            if unit_type == 'Z':
                self.units_text.insert(tk.END, f"  💰 {type_name}: {count} ({percentage:.0f}%) - PE COLLECTORS\n")
            else:
                self.units_text.insert(tk.END, f"  {type_name}: {count} ({percentage:.0f}%)\n")
        
        # Krótka ocena PE
        if z_count >= 2:
            self.units_text.insert(tk.END, f"✅ Ekonomia PE: zabezpieczona ({z_count} jednostek Z)\n")
        elif z_count == 1:
            self.units_text.insert(tk.END, f"⚠️ Ekonomia PE: ryzykowna (tylko {z_count} jednostka Z)\n")
        else:
            self.units_text.insert(tk.END, f"❌ Ekonomia PE: brak zabezpieczenia!\n")
    
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
        
        # Pobierz nazwę jednostki (może być 'unit_full_name' lub 'type')
        unit_display_name = unit.get('unit_full_name', unit.get('type', 'Jednostka'))
        
        # Aktualizuj progress
        self.update_creation_progress(progress, f"Tworzenie: {unit_display_name}")
        
        # Utwórz żeton
        success = self.create_single_token(unit)
        
        if success:
            print(f"✅ Utworzono: {unit_display_name}")
        else:
            print(f"❌ Błąd: {unit_display_name}")
        
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
                "R": [f"{commander_num}. Oddział Rozpoznawczy", f"{commander_num}. Kompania Zwiadowcza", f"{commander_num}. Batalion Rozpoznawczy"],
                "Z": [f"{commander_num}. Oddział Zaopatrzeniowy", f"{commander_num}. Kompania Zaopatrzeniowa", f"{commander_num}. Batalion Wsparcia"]
            }
        else:  # Niemcy
            unit_names = {
                "P": [f"{commander_num}. Infanterie Regiment", f"{commander_num}. Grenadier Bataillon", f"{commander_num}. Schützen Kompanie"],
                "TL": [f"{commander_num}. Panzer Zug", f"{commander_num}. Panzer Kompanie", f"{commander_num}. Panzer Abteilung"],
                "TŚ": [f"{commander_num}. schwere Panzer", f"{commander_num}. Panzer Regiment", f"{commander_num}. Panzer Brigade"],
                "AL": [f"{commander_num}. Artillerie Batterie", f"{commander_num}. Artillerie Abteilung", f"{commander_num}. Artillerie Regiment"],
                "AC": [f"{commander_num}. schwere Artillerie", f"{commander_num}. Haubitze Abteilung", f"{commander_num}. schwere Artillerie Regiment"],
                "R": [f"{commander_num}. Aufklärungs Zug", f"{commander_num}. Aufklärungs Kompanie", f"{commander_num}. Aufklärungs Bataillon"],
                "Z": [f"{commander_num}. Versorgungs Zug", f"{commander_num}. Versorgungs Kompanie", f"{commander_num}. Unterstützungs Bataillon"]
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
            "unit_full_name": unit_name,
            "unit_type": unit_type,
            "unit_size": preview_unit['size'],
            "nation": nation,
            "movement": str(movement),
            "attack_range": str(attack_range),
            "attack_value": str(attack_value),
            "combat_value": str(combat_value),
            "defense_value": str(defense_value),
            "unit_maintenance": str(maintenance),
            "purchase_value": str(total_cost),
            "sight_range": str(computed.sight if compute_token else final_stats.get('sight', 2)),
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
        # Bezpieczne pobranie nazwy jednostki dla logów
        unit_name = unit.get('name', unit.get('unit_full_name', unit.get('type', 'Jednostka')))
        
        try:
            # Sprawdź czy Token Editor nadal istnieje
            if not self.token_editor or not hasattr(self.token_editor, 'nation'):
                print(f"Token Editor uszkodzony, pomijam {unit_name}")
                return False
            
            # Ustaw podstawowe parametry
            commander = self.selected_commander.get()
            
            try:
                # Bezpieczne ustawienie parametrów
                self.token_editor.nation.set(unit.get("nation", "Polska"))
                self.token_editor.unit_type.set(unit.get("unit_type", "infantry")) 
                self.token_editor.unit_size.set(unit.get("unit_size", "battalion"))
                
                if hasattr(self.token_editor, 'selected_commander'):
                    self.token_editor.selected_commander.set(commander)
                
                # Ustaw statystyki
                self.token_editor.movement_points.set(unit.get("movement_points", 3))
                self.token_editor.attack_range.set(unit.get("attack_range", 1))
                self.token_editor.attack_value.set(unit.get("attack_value", 5))
                self.token_editor.combat_value.set(unit.get("combat_value", 5))
                self.token_editor.defense_value.set(unit.get("defense_value", 5))
                self.token_editor.unit_maintenance.set(unit.get("unit_maintenance", 1))
                self.token_editor.purchase_value.set(unit.get("purchase_value", 10))
                self.token_editor.sight_range.set(unit.get("sight_range", 2))
                
            except tk.TclError as e:
                print(f"Błąd GUI Token Editor dla {unit_name}: {e}")
                return False
            
            # Zastosuj upgrady bezpiecznie
            support = unit.get("support", "")
            if support and hasattr(self.token_editor, 'selected_supports'):
                try:
                    # Wyczyść poprzednie upgrady
                    self.token_editor.selected_supports.clear()
                    if hasattr(self.token_editor, 'selected_transport'):
                        self.token_editor.selected_transport.set("")
                    
                    # Zastosuj nowe upgrady
                    upgrades = [u.strip() for u in support.split(",") if u.strip()]
                    for upgrade in upgrades:
                        if upgrade in self.token_editor.transport_types:
                            self.token_editor.selected_transport.set(upgrade)
                        else:
                            self.token_editor.selected_supports.add(upgrade)
                            
                except Exception as e:
                    print(f"Błąd ustawiania upgradów dla {unit_name}: {e}")
                    # Kontynuuj bez upgradów
            
            # Aktualizuj pola liczbowe
            try:
                if hasattr(self.token_editor, 'update_numeric_fields'):
                    self.token_editor.update_numeric_fields()
            except Exception as e:
                print(f"Błąd aktualizacji pól dla {unit_name}: {e}")
            
            # Zapisz żeton
            try:
                self.token_editor.save_token(auto_mode=True, auto_name=unit_name)
                return True
            except Exception as e:
                print(f"Błąd zapisu żetonu {unit_name}: {e}")
                return False
                
        except Exception as e:
            print(f"Ogólny błąd tworzenia żetonu {unit_name}: {e}")
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
        self._cached_tokens_by_nation = None
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
