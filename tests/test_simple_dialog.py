"""
SUPER PROSTY DIALOG - bez zbędnych komplikacji
"""

import tkinter as tk
from tkinter import messagebox

class SimpleNationDialog:
    def __init__(self):
        self.result = None
        
        # Główne okno
        self.root = tk.Tk()
        self.root.title("Wybór nacji - AI vs Człowiek")
        self.root.geometry("400x350")
        
        # Tytuł
        title = tk.Label(self.root, text="🎮 WYBIERZ NACJE", font=("Arial", 16, "bold"))
        title.pack(pady=20)
        
        # Twoja nacja
        tk.Label(self.root, text="👤 TY GRASZ:", font=("Arial", 12, "bold")).pack(pady=5)
        self.player_nation = tk.StringVar(value="Polska")
        tk.Radiobutton(self.root, text="🇵🇱 Polska", variable=self.player_nation, 
                      value="Polska", font=("Arial", 11)).pack(pady=2)
        tk.Radiobutton(self.root, text="🇩🇪 Niemcy", variable=self.player_nation, 
                      value="Niemcy", font=("Arial", 11)).pack(pady=2)
        
        tk.Label(self.root, text="").pack(pady=10)  # Odstęp
        
        # AI trudność
        tk.Label(self.root, text="🤖 AI GRA:", font=("Arial", 12, "bold")).pack(pady=5)
        self.ai_difficulty = tk.StringVar(value="medium")
        tk.Radiobutton(self.root, text="🟢 Łatwy", variable=self.ai_difficulty, 
                      value="easy", font=("Arial", 11)).pack(pady=2)
        tk.Radiobutton(self.root, text="🟡 Średni", variable=self.ai_difficulty, 
                      value="medium", font=("Arial", 11)).pack(pady=2)
        tk.Radiobutton(self.root, text="🔴 Trudny", variable=self.ai_difficulty, 
                      value="hard", font=("Arial", 11)).pack(pady=2)
        
        tk.Label(self.root, text="").pack(pady=10)  # Odstęp
        
        # Info
        tk.Label(self.root, text="⏱️ Gra: 10 tur\n🧠 AI uczy się z każdej partii", 
                font=("Arial", 10), fg="gray").pack(pady=10)
        
        # Przyciski
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="🎮 GRAJ!", command=self._start_game,
                 font=("Arial", 14, "bold"), bg="lightgreen", width=10, height=2).pack(side='left', padx=10)
        tk.Button(button_frame, text="❌ Anuluj", command=self._cancel,
                 font=("Arial", 12), width=8, height=2).pack(side='right', padx=10)
    
    def _start_game(self):
        player_choice = self.player_nation.get()
        ai_choice = "Niemcy" if player_choice == "Polska" else "Polska"
        
        self.result = {
            'player_nation': player_choice,
            'ai_nation': ai_choice,
            'ai_difficulty': self.ai_difficulty.get()
        }
        print(f"🎮 Wybrano: {self.result}")
        self.root.destroy()
    
    def _cancel(self):
        self.result = None
        self.root.destroy()
    
    def show(self):
        self.root.mainloop()
        return self.result

def test_simple_dialog():
    dialog = SimpleNationDialog()
    result = dialog.show()
    
    if result:
        print(f"✅ Wynik: {result}")
    else:
        print("❌ Anulowano")

if __name__ == "__main__":
    test_simple_dialog()
