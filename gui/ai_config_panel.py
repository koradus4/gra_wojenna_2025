"""
AI Configuration Panel - Suwaki dla ekranu startowego
Wizualny interface do dostrajania parametrów AI Commander
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable
import math

from ai.ai_config import get_ai_config, AIProfile, get_param, set_ai_profile


class AIConfigPanel:
    """Panel konfiguracji AI z suwakami i presetami"""
    
    def __init__(self, parent_frame: ttk.Frame, compact_mode=False):
        self.parent = parent_frame
        self.compact_mode = compact_mode
        self.config_manager = get_ai_config()
        self.sliders: Dict[str, ttk.Scale] = {}
        self.labels: Dict[str, ttk.Label] = {}
        self.on_change_callbacks: list[Callable] = []
        
        # Słownik opisów parametrów dla polskich użytkowników (laików)
        self.parameter_descriptions = {
            "ECONOMY.MIN_BUY": "Minimalna ilość PE potrzebna do rozpoczęcia zakupów jednostek.\nJeśli AI ma mniej PE, nie będzie kupować nowych jednostek i będzie oszczędzać na później.",
            "ECONOMY.MIN_ALLOCATE": "Minimalna ilość PE potrzebna do alokacji zasobów dla dowódców.\nAI nie będzie przydzielać PE dowódcom jeśli ma mniej niż ta wartość.",
            "ECONOMY.ALLOC_RATIO": "Jaka część dostępnych PE zostanie przeznaczona na zakupy w tej turze.\n50% oznacza że AI wydaje połowę PE, resztę zostawia w rezerwie na następne tury.",
            "LOGISTICS.LOW_FUEL_UNITS_RATIO_TRIGGER": "Próg kryzysu paliwowego - gdy mało jednostek ma paliwo.\nPoniżej tego progu AI zacznie oszczędzać paliwo i ograniczać ruchy.",
            "COMBAT.THREAT_RETREAT_THRESHOLD": "Poziom zagrożenia przy którym AI wykonuje odwrót ze walki.\nIm wyższa wartość, tym AI jest bardziej odważne i rzadziej ucieka przed przeciwnikiem.",
            "COMBAT.COUNTER_ATTACK_MAX_PENALTY": "Maksymalna kara za przeprowadzanie kontrataków.\nWyższa wartość oznacza że AI będzie rzadziej kontratakować (większa ostrożność).",
            "COMBAT.KEYPOINT_DEFENSE_RANGE": "Zasięg w jakim AI broni zajętych punktów kluczowych.\nJednostki będą bronić miast i fabryk w tym promieniu.",
            "COMBAT.PROXIMITY_THREAT_RANGE": "Zasięg wykrywania zagrożeń ze strony wroga.\nAI planuje obronę i manewry uwzględniając wrogów w tym zasięgu.",
            "COMBAT.MIN_COUNTERATTACK_RANGE": "Minimalny zasięg potrzebny do przeprowadzania kontrataków.\nAI nie będzie atakować celów które są bliżej niż ta wartość (bezpieczeństwo).",
            "COMBAT.MAX_ATTACK_RANGE": "Maksymalny zasięg ataków które AI będzie przeprowadzać.\nJednostki nie będą atakować celów dalszych niż ta odległość (oszczędność ruchu).",
            "STRATEGY.VP_WINNING_THRESHOLD": "Próg punktów VP przy którym AI zmienia strategię na zwycięską.\nPo osiągnięciu tego progu AI skupia się na ochronie przewagi i dobiciu przeciwnika.",
            "DEPLOYMENT.DEFAULT_VP_WEIGHT": "Jak ważne są punkty zwycięstwa (VP) przy wyborze celów do zajęcia.\nWyższa wartość = AI bardziej skupia się na punktach VP zamiast ekonomii.",
            "DEPLOYMENT.DEFAULT_ECON_WEIGHT": "Jak ważne są punkty ekonomiczne przy wyborze celów.\nWyższa wartość = AI bardziej preferuje zajmować miasta i fabryki zamiast punktów VP.",
            "PURCHASES.FORCE_RATIO_THRESHOLDS.DEFENSIVE": "Próg siły przy którym AI przechodzi w tryb defensywny.\nIm niższa wartość, tym szybciej AI przestaje atakować i zaczyna się bronić.",
            "LOGISTICS.MAX_UNITS_PER_TURN": "Maksymalna liczba jednostek które AI może kupić w jednej turze.\nOgranicza tempo rozbudowy armii - wyższa wartość = szybszy rozwój wojska.",
            "MOVEMENT.MIN_GROUP_SIZE": "Minimalny rozmiar grupy jednostek poruszających się razem.\nAI będzie grupować jednostki w większe formacje zamiast wysyłać je pojedynczo.",
            "DEPLOYMENT.GARRISON_LIMITS.default": "Domyślna liczba jednostek pozostawianych jako garnizon w zajętych punktach.\nWięcej = lepsza obrona miast, ale mniej jednostek dostępnych do ataku.",
            "LOGISTICS.RESUPPLY_RATIOS.WOJNA": "Jaka część zasobów jest przeznaczana na zaopatrzenie podczas wojny.\nWyższa wartość = lepsze zaopatrzenie jednostek, ale mniej zasobów na nowe zakupy."
        }
        
        # Aktualny profil - pobierz z konfiguracji
        try:
            current_profile_name = getattr(self.config_manager, 'current_profile', 'balanced')
            if hasattr(current_profile_name, 'value'):  # Enum
                current_profile_name = current_profile_name.value
        except:
            current_profile_name = "balanced"
            
        print(f"🎯 Początkowy profil: {current_profile_name}")
        self.current_profile = tk.StringVar(value=current_profile_name)
        
        # Flaga do wyłączania callbacków podczas ładowania
        self.loading_values = False
        
        self._create_ui()
        self._load_current_values()
        
    def add_change_callback(self, callback: Callable):
        """Dodaje callback wywoływany przy zmianie parametrów"""
        self.on_change_callbacks.append(callback)
        
    def _create_ui(self):
        """Tworzy interfejs użytkownika"""
        
        # Główny kontener - bez scrolling, wszystko się mieści
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill="both", expand=True)
        
        # === NAGŁÓWEK ===
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ttk.Label(header_frame, text="🎛️ Konfiguracja AI Commander", 
                 font=("Arial", 12, "bold")).pack(side="left")
                 
        # Info button
        ttk.Button(header_frame, text="ℹ️", width=3,
                  command=self._show_help).pack(side="right")
        
        # === PROFILE PRESETS ===
        self._create_profile_section()
        
        # === MAIN TABS ===
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill="both", expand=True, padx=(10, 35), pady=5)  # Jeszcze więcej padding po prawej
        
        # Tworzenie zakładek
        self._create_economy_tab(notebook)
        self._create_combat_tab(notebook) 
        self._create_strategy_tab(notebook)
        self._create_advanced_tab(notebook)
        
        # === STATUS BAR ===
        self._create_status_bar()
        
    def _create_profile_section(self):
        """Tworzy sekcję z presetami profili"""
        profile_frame = ttk.LabelFrame(self.main_frame, text="Profile AI", padding="10")
        profile_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Przyciski profili - zwykłe buttony z haczykami
        buttons_frame = ttk.Frame(profile_frame)
        buttons_frame.pack(fill="x")
        
        profiles = [
            ("balanced", "🎯 Zbalansowany", "Uniwersalny profil, adaptacyjny"),
            ("aggressive", "🔥 Agresywny", "Maksymalny atak, wysokie ryzyko"),
            ("defensive", "🛡️ Defensywny", "Ochrona pozycji, ekonomia"),
            ("custom", "⚙️ Niestandardowy", "Ręcznie dostrojone parametry")
        ]
        
        # Zapisz reference do buttonów
        self.profile_buttons = {}
        
        for i, (profile_id, name, desc) in enumerate(profiles):
            # Utwórz funkcję callback dla tego konkretnego profilu
            def make_callback(pid):
                def callback():
                    print(f"🖱️ Kliknięto przycisk profilu: {pid}")
                    self._load_profile(pid)
                return callback
            
            btn = ttk.Button(
                buttons_frame,
                text=f"   {name}",  # Początek bez haczyka
                command=make_callback(profile_id),
                width=20  # Zwiększona szerokość
            )
            btn.pack(side="left", padx=(0, 8))
            
            # Zapisz referencję
            self.profile_buttons[profile_id] = btn
            
            # Tooltip z opisem
            self._create_tooltip(btn, desc)
            
        # Ustaw początkowy profil z haczkiem
        self._update_profile_buttons()
            
        # Custom indicator
        self.custom_indicator = ttk.Label(profile_frame, text="", 
                                        font=("Arial", 9), foreground="orange")
        self.custom_indicator.pack(anchor="w", pady=(5, 0))
    
    def _update_profile_buttons(self):
        """Aktualizuje haczyki na przyciskach profili"""
        current = self.current_profile.get()
        # print(f"🔄 Aktualizuję przyciski dla profilu: {current}")  # DEBUG OFF
        
        profile_names = {
            "balanced": "🎯 Zbalansowany",
            "aggressive": "🔥 Agresywny", 
            "defensive": "🛡️ Defensywny",
            "custom": "⚙️ Niestandardowy"
        }
        
        for profile_id, btn in self.profile_buttons.items():
            name = profile_names[profile_id]
            if profile_id == current:
                btn.config(text=f"✅ {name}")  # Z haczykiem
                # print(f"✅ Haczyk przy: {name}")  # DEBUG OFF
            else:
                btn.config(text=f"    {name}")  # Bez haczyka (4 spacje dla wyrównania)
    
    def _create_economy_tab(self, notebook: ttk.Notebook):
        """Zakładka ekonomii"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="💰 Ekonomia")
        
        # Główne parametry ekonomiczne
        params = [
            ("ECONOMY.MIN_BUY", "Minimum PE do zakupów", 15, 50, "PE"),
            ("ECONOMY.MIN_ALLOCATE", "Minimum PE do alokacji", 40, 100, "PE"), 
            ("ECONOMY.ALLOC_RATIO", "% PE dla dowódców", 0.3, 0.8, "%"),
            ("LOGISTICS.LOW_FUEL_UNITS_RATIO_TRIGGER", "Próg kryzysu paliwa", 0.1, 0.5, "%")
        ]
        
        for i, (param_path, label, min_val, max_val, unit) in enumerate(params):
            self._create_slider_row(tab, param_path, label, min_val, max_val, unit, i)
            
        # Wyjaśnienie praktyczne
        self._add_tab_explanation(tab, len(params), "ekonomia")
    
    def _create_combat_tab(self, notebook: ttk.Notebook):
        """Zakładka walki"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="⚔️ Walka")
        
        params = [
            ("COMBAT.THREAT_RETREAT_THRESHOLD", "Próg odwrotu", 1, 40, "poziom"),
            ("COMBAT.COUNTER_ATTACK_MAX_PENALTY", "Kara za kontratak", 0.1, 1.0, "%"),
            ("COMBAT.KEYPOINT_DEFENSE_RANGE", "Zasięg obrony punktów", 1, 5, "hex"),
            ("COMBAT.PROXIMITY_THREAT_RANGE", "Zasięg detekcji zagrożeń", 3, 8, "hex")
        ]
        
        for i, (param_path, label, min_val, max_val, unit) in enumerate(params):
            self._create_slider_row(tab, param_path, label, min_val, max_val, unit, i)
        
        # Wyjaśnienie praktyczne
        self._add_tab_explanation(tab, len(params), "walka")
    
    def _create_strategy_tab(self, notebook: ttk.Notebook):
        """Zakładka strategii"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="🎯 Strategia") 
        
        params = [
            ("STRATEGY.VP_WINNING_THRESHOLD", "Próg wygranej VP", 5, 20, "VP"),
            ("DEPLOYMENT.DEFAULT_VP_WEIGHT", "Waga punktów VP", 0.1, 2.0, "x"),
            ("DEPLOYMENT.DEFAULT_ECON_WEIGHT", "Waga punktów ekonomicznych", 0.1, 2.0, "x"),
            ("PURCHASES.FORCE_RATIO_THRESHOLDS.DEFENSIVE", "Próg trybu defensywnego", 0.3, 1.0, "ratio")
        ]
        
        for i, (param_path, label, min_val, max_val, unit) in enumerate(params):
            self._create_slider_row(tab, param_path, label, min_val, max_val, unit, i)
        
        # Wyjaśnienie praktyczne
        self._add_tab_explanation(tab, len(params), "strategia")
    
    def _create_advanced_tab(self, notebook: ttk.Notebook):
        """Zakładka zaawansowane"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="🔧 Zaawansowane")
        
        params = [
            ("LOGISTICS.MAX_UNITS_PER_TURN", "Max jednostek na turę", 1, 5, "szt"),
            ("MOVEMENT.MIN_GROUP_SIZE", "Min. rozmiar grupy", 2, 6, "szt"),
            ("DEPLOYMENT.GARRISON_LIMITS.default", "Domyślny limit garnizonu", 1, 5, "szt"),
            ("LOGISTICS.RESUPPLY_RATIOS.WOJNA", "Ratio resupply w wojnie", 0.5, 1.0, "%")
        ]
        
        for i, (param_path, label, min_val, max_val, unit) in enumerate(params):
            self._create_slider_row(tab, param_path, label, min_val, max_val, unit, i)
            
        # Wyjaśnienie praktyczne
        self._add_tab_explanation(tab, len(params), "zaawansowane")
            
        # Reset do domyślnych - przesunięte niżej
        reset_frame = ttk.Frame(tab)
        reset_frame.grid(row=len(params)+2, column=0, columnspan=3, pady=10)
        
        ttk.Button(reset_frame, text="🔄 Reset do domyślnych", 
                  command=self._reset_to_defaults).pack(side="left", padx=(0, 10))
        ttk.Button(reset_frame, text="💾 Zapisz konfigurację", 
                  command=self._save_config).pack(side="left")
    
    def _create_slider_row(self, parent, param_path: str, label: str, 
                          min_val: float, max_val: float, unit: str, row: int):
        """Tworzy rząd z suwakiem dla parametru"""
        
        # Label z ikoną informacyjną
        label_frame = ttk.Frame(parent)
        label_frame.grid(row=row, column=0, sticky="w", padx=(10, 10), pady=5)
        
        label_widget = ttk.Label(label_frame, text=f"{label}:")
        label_widget.pack(side="left")
        
        # Ikonka informacyjna z tooltipem
        info_label = ttk.Label(label_frame, text=" ℹ️", foreground="blue", cursor="hand2")
        info_label.pack(side="left")
        
        # Dodaj tooltip z opisem parametru
        if param_path in self.parameter_descriptions:
            description = self.parameter_descriptions[param_path]
            self._create_tooltip(info_label, description)
            self._create_tooltip(label_widget, description)  # Tooltip także na głównym labelu
        
        # Slider - przywracamy normalną długość
        slider = ttk.Scale(parent, from_=min_val, to=max_val, orient="horizontal",
                          length=180, command=lambda v, p=param_path: self._on_slider_change(p, v))
        slider.grid(row=row, column=1, padx=(5, 40), pady=5, sticky="w")  # Więcej padding po prawej
        
        # Dodaj tooltip także na slider
        if param_path in self.parameter_descriptions:
            self._create_tooltip(slider, self.parameter_descriptions[param_path])
        
        # Value label
        value_label = ttk.Label(parent, text=f"{min_val:.1f} {unit}")
        value_label.grid(row=row, column=2, sticky="w", padx=(0, 20), pady=5)  # Więcej padding po prawej
        
        # Konfiguruj grid column weights - więcej miejsca dla suwaków  
        parent.columnconfigure(0, weight=0, minsize=140)  # Label kolumna  
        parent.columnconfigure(1, weight=0, minsize=200)  # Slider kolumna - więcej miejsca
        parent.columnconfigure(2, weight=0, minsize=80)   # Value kolumna
        
        # Zapisz referencje
        self.sliders[param_path] = slider
        self.labels[param_path] = value_label
    
    def _add_tab_explanation(self, parent, start_row: int, tab_type: str):
        """Dodaje sekcję z wyjaśnieniami na dole zakładki"""
        # Separator
        separator = ttk.Separator(parent, orient='horizontal')
        separator.grid(row=start_row, column=0, columnspan=3, sticky="ew", pady=(15, 10))
        
        # Ramka z wyjaśnieniami
        info_frame = ttk.LabelFrame(parent, text="📋 Praktyczne wyjaśnienie", padding="10")
        info_frame.grid(row=start_row+1, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))
        
        # Tekst wyjaśniający zależny od typu zakładki
        explanations = {
            "ekonomia": """💡 Jak to działa w praktyce:
• Minimum PE do zakupów: Jeśli masz 25 PE a próg to 30 - AI poczeka na więcej PE
• Ratio alokacji: Przy 50% AI wyda połowę PE tej tury, resztę zostawi na następne
• Próg kryzysu paliwa: AI zacznie oszczędzać paliwo gdy zostanie mało jednostek sprawnych

🎯 Przykład: PE=40, próg=30, ratio=60% → AI kupi za 24 PE, zostawi 16 PE na później""",
            
            "walka": """💡 Jak to działa w praktyce:  
• Próg odwrotu: Przy zagrożeniu 3 i progu 4 - AI walczy, przy 5 - ucieka
• Kara za kontratak: Wyższa wartość = AI rzadziej kontratakuje (ostrożność)
• Zasięg obrony: AI broni punktów w tym promieniu od zajętych miast
• Zasięg detekcji: AI widzi zagrożenia i planuje obronę w tym zasięgu

🎯 Przykład: Wróg w odległości 3, próg odwrotu=4, zasięg obrony=2 → AI broni""",
            
            "strategia": """💡 Jak to działa w praktyce:
• Waga VP: Przy 1.5x AI preferuje punkty zwycięstwa nad ekonomią  
• Waga ekonomii: Przy 2.0x AI woli zajmować miasta niż punkty VP
• Próg defensywy: Przy 0.4 AI szybko przechodzi w obronę gdy ma słabe siły
• Próg wygranej: AI zmienia strategię gdy zbliża się do tej liczby punktów VP

🎯 Przykład: VP=80pkt×1.5=120, Econ=60pkt×2.0=120 → AI wybiera cel bliższy""",
            
            "zaawansowane": """💡 Jak to działa w praktyce:
• Max jednostek na turę: Ogranicza tempo rozbudowy armii (1=powoli, 5=szybko)
• Min rozmiar grupy: AI grupuje jednostki (2=pary, 6=duże formacje)
• Limit garnizonu: Ile jednostek zostawi w każdym zajętym punkcie jako ochrona
• Ratio resupply: Jaka część zasobów idzie na zaopatrzenie vs nowe zakupy

🎯 Przykład: Grupa=4, garnizon=2 → AI porusza 4 jednostkami razem, 2 zostają w bazie"""
        }
        
        explanation_text = explanations.get(tab_type, "Parametry tej sekcji wpływają na zachowanie AI.")
        
        # Label z wieloliniowym tekstem
        text_widget = tk.Text(info_frame, wrap="word", height=5, width=70,
                             font=("Arial", 9), bg="#f8f9fa", relief="flat",
                             state="normal")
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("1.0", explanation_text)
        text_widget.config(state="disabled")  # Tylko do odczytu
        
    def _create_status_bar(self):
        """Tworzy pasek statusu"""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.status_label = ttk.Label(status_frame, text="✅ Gotowy do gry", 
                                    font=("Arial", 9), foreground="green")
        self.status_label.pack(side="left")
        
        # Podgląd aktualnych wartości
        preview_btn = ttk.Button(status_frame, text="👁️ Podgląd AI", 
                               command=self._preview_ai_behavior)
        preview_btn.pack(side="right")
    
    def _load_profile(self, profile_id: str):
        """Ładuje profil i aktualizuje suwaki"""
        print(f"🔄 Ładowanie profilu: {profile_id}")
        
        # Aktualizuj current_profile
        self.current_profile.set(profile_id)
        
        # Aktualizuj haczyki na przyciskach
        self._update_profile_buttons()
        
        # Jeśli to custom, nie rób nic więcej - to oznacza ręczne ustawienia
        if profile_id == "custom":
            self.status_label.config(text="⚙️ Profil niestandardowy - ręczne ustawienia", 
                                   foreground="orange")
            return
            
        try:
            # Zmień profil w konfiguracji
            profile_enum = AIProfile(profile_id)
            set_ai_profile(profile_enum)
            
            # Aktualizuj suwaki - resetuj do wartości profilu
            self._load_current_values()
            
            # Pokaż status
            profile_info = self.config_manager.get_profile_info()
            self.status_label.config(text=f"✅ Załadowano: {profile_info['name']}", 
                                   foreground="green")
            
            # Wyczyść custom indicator
            self.custom_indicator.config(text="")
            
            # Powiadom callbacki
            self._notify_change()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można załadować profilu: {e}")
    
    def _load_current_values(self):
        """Ładuje aktualne wartości do suwaków"""
        self.loading_values = True  # Wyłącz callbacki
        
        for param_path, slider in self.sliders.items():
            try:
                current_value = get_param(param_path, 0)
                slider.set(current_value)
                self._update_value_label(param_path, current_value)
            except Exception as e:
                print(f"Błąd ładowania {param_path}: {e}")
                
        self.loading_values = False  # Włącz callbacki
    
    def _on_slider_change(self, param_path: str, value_str: str):
        """Callback zmiany suwaka"""
        # Ignoruj podczas ładowania wartości
        if self.loading_values:
            return
            
        try:
            value = float(value_str)
            
            # Aktualizuj w konfiguracji
            self.config_manager.set_parameter(param_path, value)
            
            # Aktualizuj label
            self._update_value_label(param_path, value)
            
            # Pokaż że to custom config
            self.custom_indicator.config(text="⚙️ Konfiguracja niestandardowa")
            self.current_profile.set("custom")
            
            # Aktualizuj haczyki na przyciskach
            self._update_profile_buttons()
            
            # Status
            self.status_label.config(text=f"⚡ Zmieniono: {param_path}", 
                                   foreground="orange")
            
            # Powiadom callbacki  
            self._notify_change()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zmienić parametru: {e}")
    
    def _update_value_label(self, param_path: str, value: float):
        """Aktualizuje label z wartością"""
        if param_path in self.labels:
            # Formatowanie w zależności od typu
            if "RATIO" in param_path or "WEIGHT" in param_path or "PENALTY" in param_path:
                if value <= 1.0:
                    display_value = f"{value:.0%}"
                else:
                    display_value = f"{value:.1f}x"
            elif isinstance(value, float) and value < 10:
                display_value = f"{value:.1f}"
            else:
                display_value = f"{value:.0f}"
                
            # Określ jednostkę na podstawie ścieżki
            if "MIN_BUY" in param_path or "MIN_ALLOCATE" in param_path:
                unit = "PE"
            elif "THRESHOLD" in param_path and "VP" in param_path:
                unit = "VP" 
            elif "RANGE" in param_path:
                unit = "hex"
            elif "TURN" in param_path:
                unit = "szt"
            elif "RATIO" in param_path or "WEIGHT" in param_path or "PENALTY" in param_path:
                unit = ""  # Already included in display_value
            else:
                unit = ""
                
            self.labels[param_path].config(text=f"{display_value} {unit}".strip())
    
    def _notify_change(self):
        """Powiadamia o zmianie konfiguracji"""
        for callback in self.on_change_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Błąd callback: {e}")
    
    def _reset_to_defaults(self):
        """Resetuje do wartości domyślnych"""
        result = messagebox.askyesno("Reset", 
                                   "Czy na pewno chcesz zresetować wszystkie parametry do wartości domyślnych?")
        if result:
            try:
                # Załaduj profil zbalansowany
                self._load_profile("balanced")
                messagebox.showinfo("Sukces", "Parametry zresetowane do domyślnych")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zresetować: {e}")
    
    def _save_config(self):
        """Zapisuje konfigurację do pliku"""
        try:
            self.config_manager.save_config()
            messagebox.showinfo("Sukces", "Konfiguracja zapisana pomyślnie")
            self.status_label.config(text="✅ Konfiguracja zapisana", foreground="green")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać konfiguracji: {e}")
    
    def _preview_ai_behavior(self):
        """Pokazuje podgląd zachowania AI z aktualnymi parametrami"""
        
        # Przykładowa sytuacja
        current_pe = 50
        threat_level = 3
        vp_target = 80
        econ_target = 60
        
        # Oblicz decyzje AI
        min_buy = get_param('ECONOMY.MIN_BUY', 30)
        can_buy = current_pe >= min_buy
        
        vp_weight = get_param('DEPLOYMENT.DEFAULT_VP_WEIGHT', 0.5)
        econ_weight = get_param('DEPLOYMENT.DEFAULT_ECON_WEIGHT', 1.0)
        
        vp_score = vp_target * vp_weight
        econ_score = econ_target * econ_weight
        prefers_vp = vp_score > econ_score
        
        threat_threshold = get_param('COMBAT.THREAT_RETREAT_THRESHOLD', 5)
        should_retreat = threat_level >= threat_threshold
        
        # Pokaż wyniki
        result_text = f"""🎯 Podgląd zachowania AI
        
📊 Sytuacja testowa:
• PE: {current_pe}, Zagrożenie: {threat_level}
• Cel VP: {vp_target} pkt, Cel Econ: {econ_target} pkt

🤖 Decyzje AI:
• Ekonomia: {'KUPUJ' if can_buy else 'CZEKAJ'} (próg: {min_buy:.0f} PE)
• Cel: {'VP' if prefers_vp else 'EKONOMIA'} ({vp_score:.0f} vs {econ_score:.0f})  
• Walka: {'ODWRÓT' if should_retreat else 'WALCZ'} (próg: {threat_threshold:.0f})

⚙️ Kluczowe parametry:
• Waga VP: {vp_weight:.1f}x
• Waga Ekonomii: {econ_weight:.1f}x  
• Próg odwrotu: {threat_threshold:.0f}
• Próg zakupów: {min_buy:.0f} PE"""
        
        # Pokaż w oknie dialogowym
        dialog = tk.Toplevel(self.main_frame)
        dialog.title("👁️ Podgląd AI")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        
        text_widget = tk.Text(dialog, wrap="word", padx=10, pady=10, 
                            font=("Consolas", 10))
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("1.0", result_text)
        text_widget.config(state="disabled")
        
        ttk.Button(dialog, text="OK", command=dialog.destroy).pack(pady=10)
    
    def _show_help(self):
        """Pokazuje pomoc o konfiguracji AI"""
        help_text = """🎛️ Konfiguracja AI Commander - Pomoc

🎯 PROFILE:
• Zbalansowany - uniwersalny, adaptacyjny
• Agresywny - atak, ryzyko, VP > ekonomia  
• Defensywny - ochrona, ekonomia > VP

🎚️ SUWAKI:
• Ekonomia - progi zakupów, alokacji
• Walka - odwrót, kontratak, zasięgi
• Strategia - wagi celów, progi VP
• Zaawansowane - limity, grupy

💡 WSKAZÓWKI:
• Zmiana suwaków → profil "Custom"
• Przyciski profili resetują suwaki
• "Podgląd AI" pokazuje efekt zmian
• Zmiany działają natychmiast w grze"""
        
        messagebox.showinfo("Pomoc - Konfiguracja AI", help_text)
    
    def _create_tooltip(self, widget, text):
        """Tworzy tooltip dla widgetu"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True) 
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, justify='left',
                           background="lightyellow", relief='solid', borderwidth=1,
                           font=("Arial", 9))
            label.pack()
            
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    def get_current_config_summary(self) -> str:
        """Zwraca podsumowanie aktualnej konfiguracji"""
        profile_info = self.config_manager.get_profile_info()
        
        key_params = {
            'MIN_BUY': get_param('ECONOMY.MIN_BUY'),
            'VP_WEIGHT': get_param('DEPLOYMENT.DEFAULT_VP_WEIGHT'), 
            'THREAT_THRESHOLD': get_param('COMBAT.THREAT_RETREAT_THRESHOLD'),
            'ALLOC_RATIO': get_param('ECONOMY.ALLOC_RATIO')
        }
        
        return f"Profile: {profile_info['name']} | " + \
               " | ".join([f"{k}: {v:.1f}" for k, v in key_params.items()])
    
    def refresh_from_config(self):
        """Odśwież wartości sliderów z aktualnej konfiguracji"""
        try:
            # Pobierz aktualny profil z global config
            from ai.ai_config import get_ai_config
            config = get_ai_config()
            current_profile_name = getattr(config, 'current_profile', 'balanced')
            
            # Jeśli to Enum, pobierz wartość
            if hasattr(current_profile_name, 'value'):
                current_profile_name = current_profile_name.value
                
            # Zaktualizuj profil
            self.current_profile.set(current_profile_name)
            
            # Aktualizuj haczyki na przyciskach
            self._update_profile_buttons()
            
            # Przeładuj wszystkie wartości
            self._load_current_values()
            
            # Aktualizuj status
            if current_profile_name == "custom":
                self.status_label.config(text="⚙️ Profil niestandardowy", foreground="orange")
            else:
                profile_info = config.get_profile_info() if hasattr(config, 'get_profile_info') else {}
                name = profile_info.get('name', current_profile_name.title())
                self.status_label.config(text=f"✅ Profil: {name}", foreground="green")
                
        except Exception as e:
            print(f"Błąd podczas odświeżania AI panelu: {e}")

    def pack(self, **kwargs):
        """Proxy dla pack() - przekazuje do głównego frame'a"""
        self.main_frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Proxy dla grid() - przekazuje do głównego frame'a"""
        self.main_frame.grid(**kwargs)


if __name__ == "__main__":
    # Test standalone
    root = tk.Tk()
    root.title("Test AI Config Panel")
    root.geometry("600x500")
    
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True)
    
    # Stwórz panel AI
    ai_panel = AIConfigPanel(main_frame)
    
    # Callback test
    def on_ai_change():
        print("🔄 AI configuration changed!")
        
    ai_panel.add_change_callback(on_ai_change)
    
    root.mainloop()