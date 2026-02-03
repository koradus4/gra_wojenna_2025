#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demonstracja naprawy błędu pyimage1
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time

def demo_pyimage_fix():
    """Demo pokazujące naprawę błędu pyimage1"""
    
    print("Uruchamiam demo naprawy błędu pyimage1...")
    
    # Symuluj launcher
    root1 = tk.Tk()
    root1.title("LAUNCHER (będzie zamknięty)")
    root1.geometry("300x200")
    
    label1 = tk.Label(root1, text="To jest launcher\n(stary sposób powodował błąd pyimage1)", 
                     wraplength=250, justify="center")
    label1.pack(expand=True)
    
    def start_game_old_way():
        """Stary sposób (powodował błąd)"""
        try:
            # Próba ukrycia i utworzenia nowego okna w tym samym procesie
            root1.withdraw()
            
            # To mogło powodować błąd pyimage1
            root2 = tk.Toplevel(root1)
            root2.title("GRA (stary sposób - problematyczny)")
            root2.geometry("400x300")
            
            tk.Label(root2, text="To mogło powodować błąd pyimage1\n(konflikt między instancjami Tkinter)", 
                    wraplength=350, justify="center").pack(expand=True)
            
            tk.Button(root2, text="Zamknij", command=lambda: [root2.destroy(), root1.deiconify()]).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd (symulowany): {e}")
            root1.deiconify()
    
    def start_game_new_way():
        """Nowy sposób (naprawa)"""
        try:
            # Zapisz konfigurację (w prawdziwej aplikacji)
            print("✓ Zapisuję konfigurację gry...")
            
            # Zamknij launcher całkowicie
            root1.destroy()
            
            # Po krótkiej przerwie utwórz całkiem nową instancję
            def create_new_game():
                time.sleep(0.5)  # Krótka przerwa
                
                # Nowy, niezależny root window
                game_root = tk.Tk()
                game_root.title("GRA (nowy sposób - naprawiony)")
                game_root.geometry("400x300")
                
                tk.Label(game_root, text="✓ To jest naprawa błędu pyimage1!\n\n" +
                        "• Launcher został całkowicie zamknięty\n" +
                        "• Gra działa w nowej instancji Tkinter\n" +
                        "• Brak konfliktów obrazów/zasobów", 
                        wraplength=350, justify="left").pack(expand=True, padx=20)
                
                tk.Button(game_root, text="Zamknij grę", 
                         command=game_root.destroy, bg="#4CAF50", fg="white").pack(pady=10)
                
                game_root.mainloop()
            
            # Uruchom w osobnym wątku aby symulować nowy proces
            thread = threading.Thread(target=create_new_game)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd: {e}")
    
    # Przyciski w launcherze
    frame = tk.Frame(root1)
    frame.pack(side=tk.BOTTOM, pady=10)
    
    tk.Button(frame, text="Stary sposób\n(problematyczny)", 
             command=start_game_old_way, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
    
    tk.Button(frame, text="Nowy sposób\n(naprawiony)", 
             command=start_game_new_way, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
    
    root1.mainloop()

if __name__ == "__main__":
    print("=" * 50)
    print("DEMO NAPRAWY BŁĘDU PYIMAGE1")
    print("=" * 50)
    print("Uruchamiam demonstrację...")
    
    demo_pyimage_fix()
    
    print("Demo zakończone.")
