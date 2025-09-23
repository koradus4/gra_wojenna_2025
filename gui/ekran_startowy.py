import tkinter as tk
from tkinter import messagebox
import tkinter.simpledialog as simpledialog
from tkinter import ttk
import logging

# Import funkcji czyszczenia
try:
    from utils.game_cleaner import clean_all_for_new_game, quick_clean
except ImportError:
    def clean_all_for_new_game():
        print("⚠️ Funkcja czyszczenia niedostępna")
    def quick_clean():
        print("⚠️ Funkcja czyszczenia niedostępna")

# Konfiguracja loggera
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='ekran_startowy.log',
    filemode='w'
)

# Dodanie handlera do logowania w konsoli
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

class EkranStartowy:
    def __init__(self, root):
        logging.info("Inicjalizacja ekranu startowego.")
        self.root = root
        self.root.title("Ekran Startowy")
        self.root.geometry("600x750")  # Zwiększenie wysokości okna dla nowych opcji
        self.root.configure(bg="#d3d3d3")

        self.nacje = ["Polska", "Niemcy"]
        self.miejsca = [None] * 6  # Gracze 1-6
        self.stanowiska = ["Generał", "Dowódca 1", "Dowódca 2", "Generał", "Dowódca 1", "Dowódca 2"]
        
        # NOWE OPCJE GRY
        self.max_turns = tk.StringVar(value="10")
        self.victory_mode = tk.StringVar(value="turns")

        self.create_widgets()

    def create_widgets(self):
        logging.info("Tworzenie widżetów ekranu startowego.")
        tk.Label(self.root, text="Wybór nacji i miejsc w grze", bg="#d3d3d3", font=("Arial", 16)).pack(pady=10)

        self.comboboxes = []
        self.czas_comboboxes = []  # Dodanie listy do przechowywania wyborów czasu

        for i in range(6):  # Dodanie pól dla 6 graczy
            frame = tk.Frame(self.root, bg="#d3d3d3")
            frame.pack(pady=5)

            label = tk.Label(frame, text=f"Gracz {i + 1} - {self.stanowiska[i]}", bg="#d3d3d3", font=("Arial", 12))
            label.pack(side=tk.LEFT, padx=10)

            combobox = ttk.Combobox(frame, values=self.nacje, state="readonly")
            combobox.bind("<<ComboboxSelected>>", self.create_callback(i))
            combobox.pack(side=tk.LEFT)
            self.comboboxes.append(combobox)

            czas_combobox = ttk.Combobox(frame, values=list(range(1, 11)), state="readonly")
            czas_combobox.set(1)  # Domyślnie ustawione na 1 minutę
            czas_combobox.bind("<<ComboboxSelected>>", self.create_czas_callback(i))
            czas_combobox.pack(side=tk.LEFT, padx=10)
            self.czas_comboboxes.append(czas_combobox)

        # (Opcja AI wycofana)

        # --- SEKCJA CZYSZCZENIA ---
        clean_frame = tk.LabelFrame(
            self.root,
            text="Opcje czyszczenia",
            bg="#d3d3d3",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        clean_frame.pack(pady=(10, 5), padx=20, fill="x")
        
        # Opis
        clean_desc = tk.Label(
            clean_frame,
            text="Usuń dane z poprzednich gier dla czystego startu",
            bg="#d3d3d3",
            font=("Arial", 9),
            fg="gray"
        )
        clean_desc.pack()
        
        # Przyciski czyszczenia
        clean_buttons_frame = tk.Frame(clean_frame, bg="#d3d3d3")
        clean_buttons_frame.pack(pady=5)
        
        tk.Button(
            clean_buttons_frame,
            text="🧹 Szybkie czyszczenie",
            command=self.quick_clean_action,
            bg="#FF9800",
            fg="white",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(
            clean_buttons_frame,
            text="🗑️ Pełne czyszczenie",
            command=self.full_clean_action,
            bg="#F44336",
            fg="white",
            font=("Arial", 9)
        ).pack(side=tk.LEFT)
        
        # Info o czyszczeniu
        clean_info = tk.Label(
            clean_frame,
            text="Szybkie: rozkazy strategiczne + zakupione żetony | Pełne: wszystko + logi",
            bg="#d3d3d3",
            font=("Arial", 8),
            fg="gray"
        )
        clean_info.pack()

        # --- SEKCJA OPCJI GRY ---
        game_options_frame = tk.LabelFrame(
            self.root,
            text="Opcje gry",
            bg="#d3d3d3",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        game_options_frame.pack(pady=(10, 5), padx=20, fill="x")
        
        # Liczba tur
        turns_frame = tk.Frame(game_options_frame, bg="#d3d3d3")
        turns_frame.pack(fill="x", pady=5)
        
        tk.Label(turns_frame, text="Maksymalna liczba tur:", bg="#d3d3d3", font=("Arial", 10, "bold")).pack(anchor="w")
        
        turn_options_frame = tk.Frame(turns_frame, bg="#d3d3d3")
        turn_options_frame.pack(anchor="w", padx=20)
        
        tk.Radiobutton(turn_options_frame, text="10 tur (szybka gra)", variable=self.max_turns, 
                      value="10", bg="#d3d3d3", font=("Arial", 9)).pack(anchor="w")
        tk.Radiobutton(turn_options_frame, text="20 tur (standardowa)", variable=self.max_turns, 
                      value="20", bg="#d3d3d3", font=("Arial", 9)).pack(anchor="w")
        tk.Radiobutton(turn_options_frame, text="30 tur (długa kampania)", variable=self.max_turns, 
                      value="30", bg="#d3d3d3", font=("Arial", 9)).pack(anchor="w")
        
        # Separator
        separator = tk.Frame(game_options_frame, height=1, bg="gray")
        separator.pack(fill="x", pady=10)
        
        # Warunki zwycięstwa
        victory_frame = tk.Frame(game_options_frame, bg="#d3d3d3")
        victory_frame.pack(fill="x", pady=5)
        
        tk.Label(victory_frame, text="Warunki zwycięstwa:", bg="#d3d3d3", font=("Arial", 10, "bold")).pack(anchor="w")
        
        victory_options_frame = tk.Frame(victory_frame, bg="#d3d3d3")
        victory_options_frame.pack(anchor="w", padx=20)
        
        tk.Radiobutton(victory_options_frame, text="🏆 Victory Points (porównanie po turach)", 
                      variable=self.victory_mode, value="turns", bg="#d3d3d3", font=("Arial", 9)).pack(anchor="w")
        tk.Radiobutton(victory_options_frame, text="💀 Eliminacja wroga (koniec przed limitem)", 
                      variable=self.victory_mode, value="elimination", bg="#d3d3d3", font=("Arial", 9)).pack(anchor="w")
        
        # Opis warunków
        victory_desc = tk.Label(
            victory_frame,
            text="• VP: Gra do końca, zwycięzca na podstawie punktów\n• Eliminacja: Koniec gdy jeden naród zostanie",
            bg="#d3d3d3",
            font=("Arial", 8),
            fg="gray",
            justify="left"
        )
        victory_desc.pack(anchor="w", padx=20, pady=(5, 0))

        tk.Button(self.root, text="Rozpocznij grę", command=self.rozpocznij_gre, bg="#4CAF50", fg="white").pack(pady=20)

    def create_callback(self, idx):
        def callback(event):
            wybor = self.comboboxes[idx].get()
            self.wybierz_nacje(idx, wybor)
        return callback

    def create_czas_callback(self, idx):
        def callback(event):
            self.sprawdz_czas(idx)
        return callback

    def sprawdz_wszystkie_wybory(self):
        """Weryfikuje wszystkie wybory graczy po każdej zmianie."""
        # Sprawdzenie, czy drużyny mają spójne nacje
        if self.miejsca[0] and self.miejsca[3] and self.miejsca[0] == self.miejsca[3]:
            logging.error("Generałowie obu drużyn mają tę samą nację, co jest niezgodne z zasadami.")
            messagebox.showerror("Błąd", "Generałowie obu drużyn muszą mieć różne nacje!")
            return False

        for i in range(3):
            if self.miejsca[0] and self.miejsca[i] and self.miejsca[0] != self.miejsca[i]:
                logging.error(f"Gracz {i + 1} w Team 1 ma inną nację niż Generał Team 1.")
                messagebox.showerror("Błąd", "Wszyscy gracze w Team 1 muszą mieć tę samą nację!")
                return False

        for i in range(3, 6):
            if self.miejsca[3] and self.miejsca[i] and self.miejsca[3] != self.miejsca[i]:
                logging.error(f"Gracz {i + 1} w Team 2 ma inną nację niż Generał Team 2.")
                messagebox.showerror("Błąd", "Wszyscy gracze w Team 2 muszą mieć tę samą nację!")
                return False

        return True

    # Dodano logikę dynamicznego dostosowywania suwaków i przywracania domyślnych wartości
    def sprawdz_czas(self, idx):
        """Weryfikuje, czy suma czasu dla jednej nacji nie przekracza 15 minut i dostosowuje czas pozostałych graczy."""
        team_1_czas = sum(int(self.czas_comboboxes[i].get()) for i in range(3) if self.czas_comboboxes[i].get().isdigit())
        team_2_czas = sum(int(self.czas_comboboxes[i].get()) for i in range(3, 6) if self.czas_comboboxes[i].get().isdigit())

        # Przywracanie domyślnych wartości, jeśli suma przekracza 15 minut
        if team_1_czas > 15 or team_2_czas > 15:
            for i in range(6):
                self.czas_comboboxes[i].set(1)
            messagebox.showerror("Błąd", "Suma czasu w drużynie nie może przekraczać 15 minut! Przywrócono domyślne wartości.")
            return

        # Dostosowanie maksymalnych wartości dla graczy w drużynie 1
        if idx < 3:
            for i in range(3):
                if i != idx:
                    max_czas = 15 - team_1_czas + int(self.czas_comboboxes[i].get())
                    self.czas_comboboxes[i]["values"] = list(range(1, max_czas + 1))

        # Dostosowanie maksymalnych wartości dla graczy w drużynie 2
        if idx >= 3:
            for i in range(3, 6):
                if i != idx:
                    max_czas = 15 - team_2_czas + int(self.czas_comboboxes[i].get())
                    self.czas_comboboxes[i]["values"] = list(range(1, max_czas + 1))

    def wybierz_nacje(self, idx, wybor):
        logging.debug(f"Gracz {idx + 1} wybrał nację: {wybor}")

        # Sprawdzenie, czy wybór jest pusty lub nieprawidłowy
        if not wybor or wybor not in self.nacje:
            logging.error(f"Gracz {idx + 1} wybrał nieprawidłową nację: {wybor}")
            messagebox.showerror("Błąd", "Musisz wybrać poprawną nację!")
            self.comboboxes[idx].set("")
            return

        # Zapisanie wyboru
        self.miejsca[idx] = wybor
        logging.info(f"Gracz {idx + 1} pomyślnie wybrał nację: {wybor}")

        # Weryfikacja wszystkich wyborów po zmianie
        if not self.sprawdz_wszystkie_wybory():
            self.miejsca[idx] = None
            self.comboboxes[idx].set("")

    def get_czas_na_ture(self, idx):
        """Pobiera czas na podturę dla danego gracza."""
        czas = self.czas_comboboxes[idx].get()
        logging.debug(f"Czas na turę dla gracza {idx + 1}: {czas}")
        return int(czas) if czas.isdigit() else 5

    def quick_clean_action(self):
        """Akcja szybkiego czyszczenia"""
        try:
            result = messagebox.askyesno(
                "Potwierdzenie",
                "Czy na pewno chcesz wyczyścić rozkazy strategiczne i zakupione żetony?\n\n"
                "To usunie:\n"
                "• Rozkazy strategiczne\n"
                "• Zakupione żetony (nowe_dla_* + aktualne/)\n"
                "• Wpisy w index.json i start_tokens.json"
            )
            if result:
                quick_clean()
                messagebox.showinfo("Sukces", "Szybkie czyszczenie zakończone pomyślnie!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas szybkiego czyszczenia: {e}")

    def full_clean_action(self):
        """Akcja pełnego czyszczenia"""
        try:
            result = messagebox.askyesno(
                "Potwierdzenie",
                "Czy na pewno chcesz wyczyścić WSZYSTKIE dane gry?\n\n"
                "To usunie:\n"
                "• Rozkazy strategiczne\n"
                "• Zakupione żetony (nowe_dla_* + aktualne/)\n"
                "• Wpisy w index.json i start_tokens.json\n"
                "• Logi\n"
                "• Logi akcji gry\n\n"
                "UWAGA: Ta operacja jest nieodwracalna!"
            )
            if result:
                clean_all_for_new_game()
                messagebox.showinfo("Sukces", "Pełne czyszczenie zakończone pomyślnie!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas pełnego czyszczenia: {e}")

    # Dodano walidację przy rozpoczęciu gry, aby sprawdzić, czy suma punktów w drużynach wynosi dokładnie 15
    def rozpocznij_gre(self):
        logging.info("Próba rozpoczęcia gry.")

        # Sprawdzenie poprawności wyborów przed rozpoczęciem gry
        for idx, nacja in enumerate(self.miejsca):
            if nacja is None:
                logging.error(f"Gracz {idx + 1} nie wybrał nacji.")
                messagebox.showerror("Błąd", f"Gracz {idx + 1} musi wybrać nację!")
                return

        # Dodatkowa weryfikacja logiki wyborów
        if not self.sprawdz_wszystkie_wybory():
            return

        # Sprawdzenie sumy punktów w drużynach
        team_1_czas = sum(int(self.czas_comboboxes[i].get()) for i in range(3))
        team_2_czas = sum(int(self.czas_comboboxes[i].get()) for i in range(3, 6))

        if team_1_czas < 15:
            messagebox.showerror("Błąd", f"Drużyna 1 ma do rozdysponowania {15 - team_1_czas} punktów.")
            self.czas_comboboxes[2].focus_set()  # Podświetlenie ostatniego gracza w drużynie 1
            return

        if team_2_czas < 15:
            messagebox.showerror("Błąd", f"Drużyna 2 ma do rozdysponowania {15 - team_2_czas} punktów.")
            self.czas_comboboxes[5].focus_set()  # Podświetlenie ostatniego gracza w drużynie 2
            return

        # Zapisanie danych w atrybutach klasy przed zniszczeniem GUI
        self.game_data = {
            "miejsca": self.miejsca,
            "czasy": [self.get_czas_na_ture(i) for i in range(6)],
            # (AI usunięte – brak flagi)
            "max_turns": int(self.max_turns.get()),  # Nowe opcje gry
            "victory_mode": self.victory_mode.get()
        }

        logging.info("Gra się rozpoczyna.")
        messagebox.showinfo("Start", "Gra się rozpoczyna!")
        self.root.destroy()

    def get_game_data(self):
        """Zwraca zapisane dane gry."""
        return self.game_data

if __name__ == "__main__":
    root = tk.Tk()
    app = EkranStartowy(root)
    root.mainloop()