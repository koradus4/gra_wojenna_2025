"""
PROSTY TEST DIALOGU - sprawdź czy GUI działa
"""

import tkinter as tk
from tkinter import messagebox

def test_dialog():
    """Test prostego dialogu"""
    print("🧪 Testuję dialog...")
    
    # Utwórz główne okno
    root = tk.Tk()
    root.title("Test Dialog")
    root.geometry("300x200")
    
    # Dodaj etykietę
    label = tk.Label(root, text="Dialog działa!", font=("Arial", 16))
    label.pack(pady=50)
    
    # Dodaj przycisk
    button = tk.Button(root, text="OK", command=root.destroy, font=("Arial", 12))
    button.pack(pady=10)
    
    print("✅ Dialog utworzony - powinien się pojawić")
    root.mainloop()
    print("✅ Dialog zamknięty")

if __name__ == "__main__":
    test_dialog()
