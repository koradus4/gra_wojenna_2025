import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import os
from pathlib import Path
from PIL import ImageFont
from edytory.token_editor_prototyp import create_flag_background

"""TokenShop – zmodernizowany do korzystania z centralnego         unit_type_name = {
            "P": "Piechota",
            "K": "Kawaleria",
            "TC": "Czołg ciężki",
            "TŚ": "Czołg średni",
            "TL": "Czołg lekki",
            "TS": "Sam. pancerny",
            "AC": "Artyleria ciężka",
            "AL": "Artyleria lekka",
            "AP": "Artyleria plot",
            "R": "Zwiad",
            "Z": "Zaopatrzenie ⭐ PE",
            "D": "Dowództwo",
            "G": "Generał"
        }.get(unit_type, unit_type)ce.model).

Usuwa zależność od legacy core.unit_factory (pozostawione tylko minimalne fallbacki w razie braku modułu balansu)."""
from balance.model import (
    compute_token,
    build_unit_names,
    ALLOWED_SUPPORT,
    UPGRADES as SUPPORT_UPGRADES,
)

# Transporty – w nowym systemie wykrywane przez dodatni movement_delta > 0 i nazwy znane
TRANSPORT_TYPES = [
    "przodek dwukonny",
    "sam. ciezarowy Fiat 621",
    "sam.ciezarowy Praga Rv",
    "ciagnik altyleryjski",
]
import traceback

class TokenShop(tk.Toplevel):
    def __init__(self, parent, ekonomia, dowodcy, on_purchase_callback=None, nation=None):
        super().__init__(parent)
        # --- INICJALIZACJA ZMIENNYCH STANU (musi być przed budową GUI!) ---
        if nation is not None:
            self.nation = tk.StringVar(value=nation)
        else:
            self.nation = tk.StringVar(value="Polska")
        self.unit_type = tk.StringVar(value="P")
        self.unit_size = tk.StringVar(value="Pluton")
        self.selected_supports = set()
        self.selected_transport = tk.StringVar(value="")
        # Jedno źródło prawdy – centralny balans
        self.transport_types = TRANSPORT_TYPES
        self.support_upgrades = SUPPORT_UPGRADES
        self.allowed_support = ALLOWED_SUPPORT
        # Lista typów jednostek
        self.unit_type_order = [
            ("Piechota (P)", "P", True),
            ("Kawaleria (K)", "K", True),
            ("Zwiad (R)", "R", True),
            ("Czołg ciężki (TC)", "TC", True),
            ("Czołg średni (TŚ)", "TŚ", True),
            ("Czołg lekki (TL)", "TL", True),
            ("Sam. pancerny (TS)", "TS", True),
            ("Artyleria ciężka (AC)", "AC", True),
            ("Artyleria lekka (AL)", "AL", True),
            ("Artyleria plot (AP)", "AP", True),
            ("Zaopatrzenie (Z) ⭐ JEDYNY ZBIERACZ PE", "Z", True),
            ("Dowództwo (D)", "D", True),
            ("Generał (G)", "G", True)
        ]
        self.unit_type_map = {v: k for k, v, _ in self.unit_type_order}
        self.unit_type_reverse_map = {k: v for v, k, _ in self.unit_type_order}
        self.unit_type_display = tk.StringVar(value=self.unit_type_reverse_map[self.unit_type.get()])
        self._last_valid_unit_type = self.unit_type_display.get()

        # --- USTAWIENIA OKNA ---
        self.title("Zakup nowych jednostek")
        self.geometry("800x600")
        self.configure(bg="darkolivegreen")
        self.ekonomia = ekonomia
        self.dowodcy = dowodcy
        self.on_purchase_callback = on_purchase_callback
        self.selected_commander = tk.StringVar()
        self.points_var = tk.IntVar(value=self.ekonomia.get_points()['economic_points'])

        # --- Nagłówek w ramce ---
        header_frame = tk.Frame(self, bg="olivedrab", bd=5, relief=tk.RIDGE)
        header_frame.pack(fill=tk.X)
        header_label = tk.Label(header_frame, text="SKLEP GENERAŁA – Zakup nowych jednostek", bg="olivedrab", fg="white", font=("Arial", 20, "bold"))
        header_label.pack(pady=10)

        # --- Główne kontenery ---
        main_container = tk.Frame(self, bg="darkolivegreen")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Lewy panel: formularz wyboru
        self.control_frame = tk.Frame(main_container, bg="darkolivegreen")
        self.control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Prawy panel: podgląd/statystyki
        self.preview_frame = tk.Frame(main_container, bd=2, relief=tk.RIDGE, bg="darkolivegreen")
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)        # --- Punkty ekonomiczne ---
        points_box = tk.Frame(self.control_frame, bg="olivedrab", bd=3, relief=tk.GROOVE)
        points_box.pack(fill=tk.X, pady=5)
        self.points_label = tk.Label(points_box, text=f"Dostępne punkty ekonomiczne: {self.points_var.get()}", font=("Arial", 13, "bold"), bg="olivedrab", fg="white")
        self.points_label.pack(pady=5)

        # Buduj GUI
        self.build_gui()

    def get_text_color_for_nation(self, nation):
        """Zwraca kolor tekstu na żetonie dla danej nacji, identyczny jak w Token Editor"""
        defaults = {
            "Polska": "black",
            "Niemcy": "blue",
            "Wielka Brytania": "black",
            "Japonia": "black",
            "Stany Zjednoczone": "black",
            "Francja": "black",
            "Związek Radziecki": "white"
        }
        return defaults.get(nation, "black")

    def build_gui(self):
        """Buduje interfejs graficzny sklepu"""
        commander_box = tk.Frame(self.control_frame, bg="darkolivegreen")
        commander_box.pack(fill=tk.X, pady=5)
        tk.Label(commander_box, text="Wybierz dowódcę:", bg="darkolivegreen", fg="white", font=("Arial", 12, "bold")).pack(anchor="w")
        dowodcy_ids = [str(d.id) for d in self.dowodcy]
        if dowodcy_ids:
            self.selected_commander.set(dowodcy_ids[0])
        tk.OptionMenu(commander_box, self.selected_commander, *dowodcy_ids).pack(anchor="w", pady=2)

        # --- Formularz wyboru jednostki ---
        form_box = tk.Frame(self.control_frame, bg="darkolivegreen", bd=2, relief=tk.GROOVE)
        form_box.pack(fill=tk.BOTH, expand=True, pady=5)
        # Nacja (tylko label, bez wyboru)
        tk.Label(form_box, text="Nacja:", bg="darkolivegreen", fg="white", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=2)
        tk.Label(form_box, textvariable=self.nation, bg="darkolivegreen", fg="white", font=("Arial", 11, "bold")).grid(row=0, column=1, sticky="w", pady=2)
        # Typ jednostki (pełna nazwa w OptionMenu) – tylko aktywne typy
        tk.Label(form_box, text="Typ jednostki:", bg="darkolivegreen", fg="white", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=2)
        # Lista tylko aktywnych typów
        active_unit_types = [name for name, _, active in self.unit_type_order if active]
        unit_type_menu = tk.OptionMenu(form_box, self.unit_type_display, *active_unit_types)
        unit_type_menu.grid(row=1, column=1, sticky="w", pady=2)
        # Synchronizacja wyboru pełnej nazwy z logiką (skrót)
        def on_unit_type_change(*_):
            val = self.unit_type_display.get()
            # Ustaw kod typu na podstawie pełnej nazwy
            for name, code, active in self.unit_type_order:
                if name == val:
                    self.unit_type.set(code)
                    self._last_valid_unit_type = val
                    self.update_stats()
                    break
        self.unit_type_display.trace_add('write', on_unit_type_change)
        # Wielkość
        tk.Label(form_box, text="Wielkość:", bg="darkolivegreen", fg="white", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=2)
        tk.OptionMenu(form_box, self.unit_size, "Pluton", "Kompania", "Batalion").grid(row=2, column=1, sticky="w", pady=2)
        # Nazwa (usunięcie pola edytowalnego, automatyczna generacja)
        tk.Label(form_box, text="Nazwa jednostki:", bg="darkolivegreen", fg="white", font=("Arial", 11)).grid(row=3, column=0, sticky="w", pady=2)
        self.unit_label_var = tk.StringVar()
        self.unit_full_name_var = tk.StringVar()
        tk.Label(form_box, textvariable=self.unit_label_var, bg="darkolivegreen", fg="yellow", font=("Arial", 11, "bold")).grid(row=3, column=1, sticky="w", pady=2)
        # --- Wsparcie (w tym transport jako radio, z walidacją allowed_support) ---
        tk.Label(form_box, text="Wsparcie:", bg="darkolivegreen", fg="white", font=("Arial", 11)).grid(row=4, column=0, sticky="nw", pady=2)
        self.support_vars = {}
        support_frame = tk.Frame(form_box, bg="darkolivegreen")
        support_frame.grid(row=4, column=1, sticky="w", pady=2)
        # Słownik allowed_support jak w TokenEditor
    # (allowed_support i transport_types już ustawione wcześniej z unit_factory)
        def update_support_state(*_):
            ut = self.unit_type.get()
            allowed = self.allowed_support.get(ut, [])
            # Resetuj niedozwolone wsparcia i transporty
            for sup, var in self.support_vars.items():
                if sup not in allowed:
                    var.set(0)
            # Jeśli wybrany transport nie jest już dozwolony, odznacz go
            for t in self.transport_types:
                if t not in allowed and self.support_vars[t].get():
                    self.support_vars[t].set(0)
            # Dezaktywuj niedozwolone wsparcia/transporty
            for i, sup in enumerate(self.support_upgrades.keys()):
                cb = self.support_checkbuttons[sup]
                if sup in allowed:
                    cb.config(state="normal")
                else:
                    cb.config(state="disabled")
        self.support_checkbuttons = {}
        for i, sup in enumerate(self.support_upgrades.keys()):
            var = tk.IntVar()
            def make_cmd(sup=sup, var=var):
                def cmd():
                    # Transporty jako radio
                    if sup in self.transport_types:
                        # Jeśli kliknięto już wybrany transport, odznacz
                        if var.get():
                            # Odznacz wszystkie inne transporty
                            for t in self.transport_types:
                                if t != sup and t in self.support_vars:
                                    self.support_vars[t].set(0)
                    self.update_stats()
                return cmd
            cb = tk.Checkbutton(support_frame, text=sup, variable=var, command=make_cmd(), bg="darkolivegreen", fg="white", selectcolor="olivedrab", font=("Arial", 10))
            cb.grid(row=i//2, column=i%2, sticky="w")
            self.support_vars[sup] = var
            self.support_checkbuttons[sup] = cb
        # Automatyczna walidacja wsparcia przy zmianie typu jednostki
        self.unit_type.trace_add('write', update_support_state)
        update_support_state()

        # --- Przycisk kupna ---
        self.buy_btn = tk.Button(self.control_frame, text="Kup jednostkę", command=self.buy_unit, font=("Arial", 13, "bold"), bg="#6B8E23", fg="white", bd=3, relief=tk.RAISED)
        self.buy_btn.pack(pady=10)
        self.info_label = tk.Label(self.control_frame, text="", fg="red", bg="darkolivegreen", font=("Arial", 11, "bold"))
        self.info_label.pack()

        # --- Prawy panel: podgląd flagi i statystyki ---
        preview_title = tk.Label(self.preview_frame, text="Podgląd i statystyki jednostki", bg="olivedrab", fg="white", font=("Arial", 15, "bold"))
        preview_title.pack(fill=tk.X, pady=5)
        # Podgląd flagi
        self.flag_canvas = tk.Canvas(self.preview_frame, width=120, height=120, bg="dimgray", bd=2, relief=tk.SUNKEN)
        self.flag_canvas.pack(pady=10)
        self.flag_img = None
        # Statystyki
        stats_box = tk.Frame(self.preview_frame, bg="darkolivegreen", bd=2, relief=tk.GROOVE)
        stats_box.pack(fill=tk.BOTH, expand=True, pady=5)
        self.stats_labels = {}
        stats_names = ["Ruch", "Zasięg ataku", "Siła ataku", "Wartość bojowa", "Obrona", "Utrzymanie", "Cena", "Zasięg widzenia"]
        for i, stat in enumerate(stats_names):
            tk.Label(stats_box, text=stat+":", bg="darkolivegreen", fg="white", font=("Arial", 12, "bold")).grid(row=i, column=0, sticky="e", pady=2, padx=5)
            lbl = tk.Label(stats_box, text="0", width=10, anchor="w", bg="darkolivegreen", fg="white", font=("Arial", 12))
            lbl.grid(row=i, column=1, sticky="w", pady=2)
            self.stats_labels[stat] = lbl

        # --- Automatyczna aktualizacja statystyk i flagi oraz nazw ---
        def update_all(*_):
            self.update_stats()
            self.update_token_preview()
            self.update_unit_names()
        self.nation.trace_add('write', update_all)
        self.unit_type.trace_add('write', update_all)
        self.unit_size.trace_add('write', update_all)
        self.selected_commander.trace_add('write', update_all)
        self.update_unit_names()
        self.update_stats()

    def update_unit_names(self):
        # Użyj wspólnej fabryki (uniknięcie duplikacji)
        data = build_unit_names(
            self.nation.get(),
            self.unit_type.get(),
            self.unit_size.get(),
        )
        self.unit_label_var.set(data["label"])  # unified
        self.unit_full_name_var.set(data["unit_full_name"])  # identyczne gdy UNIFIED_LABELS=True

    def update_stats(self):
        """Przelicza statystyki wg centralnego modelu i odświeża GUI."""
        ut = self.unit_type.get()
        size = self.unit_size.get()
        supports = [sup for sup, var in self.support_vars.items() if var.get()]
        comp = compute_token(ut, size, self.nation.get(), supports, quality='standard')
        ruch = comp.movement
        zasieg = comp.attack_range
        atak = comp.attack_value
        combat = comp.combat_value
        obrona = comp.defense_value
        maintenance = comp.maintenance
        cena = comp.total_cost
        sight = comp.sight
        self.stats_labels["Ruch"].config(text=str(ruch))
        self.stats_labels["Zasięg ataku"].config(text=str(zasieg))
        self.stats_labels["Siła ataku"].config(text=str(atak))
        self.stats_labels["Wartość bojowa"].config(text=str(combat))
        self.stats_labels["Obrona"].config(text=str(obrona))
        self.stats_labels["Utrzymanie"].config(text=str(maintenance))
        self.stats_labels["Cena"].config(text=str(cena))
        self.stats_labels["Zasięg widzenia"].config(text=str(sight))
        self.buy_btn.config(state="normal" if self.points_var.get() >= cena else "disabled")
        self.current_stats = dict(
            ruch=ruch, zasieg=zasieg, atak=atak, combat=combat, obrona=obrona,
            maintenance=maintenance, cena=cena, sight=sight, supports=supports
        )
        self.update_token_preview()

    def update_token_preview(self):
        # Generuje miniaturę żetonu identyczną jak w TokenEditor (wzorowane na create_token_image)
        width, height = 120, 120
        nation = self.nation.get()
        unit_type = self.unit_type.get()
        unit_size = self.unit_size.get()
        # Flaga
        base_bg = create_flag_background(nation, width, height)
        token_img = base_bg.copy()
        draw = ImageDraw.Draw(token_img)
        # Obramowanie prostokątne
        draw.rectangle([0, 0, width, height], outline="black", width=3)
        # Przygotowanie tekstów
        unit_type_full = {
            "P": "Piechota",
            "K": "Kawaleria",
            "R": "Zwiad",
            "TC": "Czołg ciężki",
            "TŚ": "Czołg średni",
            "TL": "Czołg lekki",
            "TS": "Sam. pancerny",
            "AC": "Artyleria ciężka",
            "AL": "Artyleria lekka",
            "AP": "Artyleria plot",
            "Z": "Zaopatrzenie",
            "D": "Dowództwo",
            "G": "Generał"
        }.get(unit_type, unit_type)
        unit_symbol = {"Pluton": "***", "Kompania": "I", "Batalion": "II"}.get(unit_size, "")
        # Czcionki
        try:
            font_type = ImageFont.truetype("arialbd.ttf", 19)
            font_size = ImageFont.truetype("arial.ttf", 11)
            font_symbol = ImageFont.truetype("arialbd.ttf", 18)
        except Exception:
            font_type = font_size = font_symbol = ImageFont.load_default()        # Wyśrodkowanie i rysowanie (identycznie jak w TokenEditor)
        margin = 6
        # Określenie koloru tekstu na podstawie nacji
        text_color = self.get_text_color_for_nation(nation)
        # Pełna nazwa rodzaju jednostki – DUŻA, centralna, z zawijaniem
        def wrap_text(text, font, max_width):
            words = text.split()
            lines = []
            line = ""
            for w in words:
                test = line + (" " if line else "") + w
                if draw.textlength(test, font=font) <= max_width:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = w
            if line:
                lines.append(line)
            return lines
        max_text_width = int(width * 0.9)
        type_lines = wrap_text(unit_type_full, font_type, max_text_width)
        total_type_height = sum(draw.textbbox((0,0), line, font=font_type)[3] - draw.textbbox((0,0), line, font=font_type)[1] for line in type_lines)
        total_type_height += (len(type_lines)-1) * 2  # odstęp między liniami
        bbox_size = draw.textbbox((0,0), unit_size, font=font_size)
        size_height = bbox_size[3] - bbox_size[1]
        bbox_symbol = draw.textbbox((0,0), unit_symbol, font=font_symbol)
        symbol_height = bbox_symbol[3] - bbox_symbol[1]
        gap_type_to_size = margin * 2
        gap_size_to_symbol = 2
        total_height = total_type_height + gap_type_to_size + size_height + gap_size_to_symbol + symbol_height
        y = (height - total_height) // 2
        # Nazwa typu (zawijanie)
        for line in type_lines:
            bbox = draw.textbbox((0, 0), line, font=font_type)
            x = (width - (bbox[2] - bbox[0])) / 2
            draw.text((x, y), line, fill=text_color, font=font_type)
            y += bbox[3] - bbox[1] + 2
        y += gap_type_to_size - 2
        # Wielkość
        bbox_size = draw.textbbox((0, 0), unit_size, font=font_size)
        x_size = (width - (bbox_size[2] - bbox_size[0])) / 2
        draw.text((x_size, y), unit_size, fill=text_color, font=font_size)
        y += bbox_size[3] - bbox_size[1] + gap_size_to_symbol
        # Symbol wielkości
        bbox_symbol = draw.textbbox((0, 0), unit_symbol, font=font_symbol)
        x_symbol = (width - (bbox_symbol[2] - bbox_symbol[0])) / 2
        draw.text((x_symbol, y), unit_symbol, fill=text_color, font=font_symbol)
        # Wyświetl na canvasie
        self.flag_img = ImageTk.PhotoImage(token_img)
        self.flag_canvas.delete("all")
        self.flag_canvas.create_image(width // 2, height // 2, image=self.flag_img)

    def buy_unit(self):
        label = self.unit_label_var.get()
        unit_full_name = self.unit_full_name_var.get()
        dowodca_id = self.selected_commander.get()
        cena = self.current_stats["cena"]
        if cena > self.points_var.get():
            self.info_label.config(text="Za mało punktów!")
            return
        # --- Generuj unikalny id ---
        import datetime
        import re
        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        # Oczyść label z niedozwolonych znaków Windows
        safe_label = re.sub(r'[<>:"/\\|?*]', '_', label)
        unit_id = f"nowy_{self.unit_type.get()}_{self.unit_size.get()}__{dowodca_id}_{safe_label}_{now}"
        folder = Path("assets/tokens") / f"nowe_dla_{dowodca_id}" / unit_id
        folder.mkdir(parents=True, exist_ok=True)
        # Zamiast: "image": "token.png",
        # Ustal ścieżkę względną do pliku PNG względem katalogu głównego projektu
        # np. assets/tokens/nowe_dla_{dowodca_id}/{unit_id}/token.png
        rel_img_path = str(folder / "token.png").replace("\\", "/")
        token_json = {
            "id": unit_id,
            "nation": self.nation.get(),
            "unitType": self.unit_type.get(),
            "unitSize": self.unit_size.get(),
            "shape": "prostokąt",
            "label": label,
            "unit_full_name": unit_full_name,
            "move": self.current_stats["ruch"],
            "attack": {"range": self.current_stats["zasieg"], "value": self.current_stats["atak"]},
            "combat_value": self.current_stats["combat"],
            "defense_value": self.current_stats["obrona"],
            "maintenance": self.current_stats["maintenance"],
            "price": cena,
            "sight": self.current_stats["sight"],
            "owner": f"{dowodca_id}",
            "support_upgrades": self.current_stats.get("supports", []),
            "image": rel_img_path,
            "w": 240,
            "h": 240
        }
        import json
        with open(folder / "token.json", "w", encoding="utf-8") as f:
            json.dump(token_json, f, indent=2, ensure_ascii=False)
        # --- Obrazek: żeton jak w podglądzie ---
        width, height = 240, 240
        nation = self.nation.get()
        unit_type = self.unit_type.get()
        unit_size = self.unit_size.get()
        base_bg = create_flag_background(nation, width, height)
        token_img = base_bg.copy()
        draw = ImageDraw.Draw(token_img)
        draw.rectangle([0, 0, width, height], outline="black", width=6)
        unit_type_full = {
            "P": "Piechota",
            "K": "Kawaleria",
            "R": "Zwiad",
            "TC": "Czołg ciężki",
            "TŚ": "Czołg średni",
            "TL": "Czołg lekki",
            "TS": "Sam. pancerny",
            "AC": "Artyleria ciężka",
            "AL": "Artyleria lekka",
            "AP": "Artyleria plot",
            "Z": "Zaopatrzenie ⭐ PE",
            "D": "Dowództwo",
            "G": "Generał"
        }.get(unit_type, unit_type)
        unit_symbol = {"Pluton": "***", "Kompania": "I", "Batalion": "II"}.get(unit_size, "")
        try:
            font_type = ImageFont.truetype("arialbd.ttf", 38)
            font_size = ImageFont.truetype("arial.ttf", 22)
            font_symbol = ImageFont.truetype("arialbd.ttf", 36)
        except Exception:
            font_type = font_size = font_symbol = ImageFont.load_default()
        margin = 12
        # Określenie koloru tekstu na podstawie nacji
        text_color = self.get_text_color_for_nation(nation)
        def wrap_text(text, font, max_width):
            words = text.split()
            lines = []
            line = ""
            for w in words:
                test = line + (" " if line else "") + w
                if draw.textlength(test, font=font) <= max_width:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = w
            if line:
                lines.append(line)
            return lines
        max_text_width = int(width * 0.9)
        type_lines = wrap_text(unit_type_full, font_type, max_text_width)
        total_type_height = sum(draw.textbbox((0,0), line, font=font_type)[3] - draw.textbbox((0,0), line, font=font_type)[1] for line in type_lines)
        total_type_height += (len(type_lines)-1) * 4
        bbox_size = draw.textbbox((0,0), unit_size, font=font_size)
        size_height = bbox_size[3] - bbox_size[1]
        bbox_symbol = draw.textbbox((0,0), unit_symbol, font=font_symbol)
        symbol_height = bbox_symbol[3] - bbox_symbol[1]
        gap_type_to_size = margin * 2
        gap_size_to_symbol = 4
        total_height = total_type_height + gap_type_to_size + size_height + gap_size_to_symbol + symbol_height
        y = (height - total_height) // 2
        for line in type_lines:
            bbox = draw.textbbox((0, 0), line, font=font_type)
            x = (width - (bbox[2] - bbox[0])) / 2
            draw.text((x, y), line, fill=text_color, font=font_type)
            y += bbox[3] - bbox[1] + 4
        y += gap_type_to_size - 4
        bbox_size = draw.textbbox((0, 0), unit_size, font=font_size)
        x_size = (width - (bbox_size[2] - bbox_size[0])) / 2
        draw.text((x_size, y), unit_size, fill=text_color, font=font_size)
        y += bbox_size[3] - bbox_size[1] + gap_size_to_symbol
        bbox_symbol = draw.textbbox((0, 0), unit_symbol, font=font_symbol)
        x_symbol = (width - (bbox_symbol[2] - bbox_symbol[0])) / 2
        draw.text((x_symbol, y), unit_symbol, fill=text_color, font=font_symbol)
        token_img.save(folder / "token.png")
        # Odejmij punkty
        self.points_var.set(self.points_var.get() - cena)
        self.points_label.config(text=f"Dostępne punkty ekonomiczne: {self.points_var.get()}")
        self.ekonomia.subtract_points(cena)
        self.info_label.config(text=f"Zakupiono: {unit_full_name} (koszt: {cena})", fg="green")
        if self.on_purchase_callback:
            self.on_purchase_callback()
