import tkinter as tk
from tkinter import messagebox
import tkinter.simpledialog as simpledialog
from tkinter import ttk
import logging

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
        self.root.geometry("600x600")  # Zwiększenie wysokości okna
        self.root.configure(bg="#d3d3d3")

        self.nacje = ["Polska", "Niemcy"]
        self.miejsca = [None] * 6  # Gracze 1-6
        self.stanowiska = ["Generał", "Dowódca 1", "Dowódca 2", "Generał", "Dowódca 1", "Dowódca 2"]
        
        # AI GENERAL CONFIGURATION
        self.use_ai_general = tk.BooleanVar(value=False)  # Domyślnie wyłączone

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

        # AI GENERAL OPTION
        ai_frame = tk.Frame(self.root, bg="#d3d3d3")
        ai_frame.pack(pady=10)
        
        ai_checkbox = tk.Checkbutton(
            ai_frame, 
            text="🤖 Włącz AI Generałów (Polska i Niemcy)", 
            variable=self.use_ai_general,
            bg="#d3d3d3",
            font=("Arial", 12),
            fg="#1976D2"
        )
        ai_checkbox.pack()
        
        # Info label
        ai_info = tk.Label(
            ai_frame,
            text="AI przejmie kontrolę nad generałami obu stron",
            bg="#d3d3d3",
            font=("Arial", 9),
            fg="gray"
        )
        ai_info.pack()

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
            "use_ai_general": self.use_ai_general.get()  # Dodanie opcji AI
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