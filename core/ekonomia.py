"""
Moduł systemu ekonomii – zarządza punktami ekonomicznymi i specjalnymi oraz wydarzeniami ekonomicznymi.
"""
import random

class EconomySystem:
    def __init__(self):
        """Inicjalizuje system ekonomii z domyślnymi wartościami."""
        self.economic_points = 0
        self.special_points = 0
        self.assigned_points = 0  # Dodano pole do przechowywania przydzielonych punktów

    def generate_economic_points(self):
        """Generuje punkty ekonomiczne."""
        start_points = self.economic_points
        points = random.randint(1, 100)
        self.economic_points += points

    def add_special_points(self):
        """Dodaje 1 punkt specjalny."""
        self.special_points += 1

    def subtract_points(self, points):
        """Odejmuje punkty ekonomiczne z dostępnej puli z pełną ochroną przed ujemnymi PE."""
        if not hasattr(self, 'economic_points'):
            print(f"⚠️ [ECONOMY] Brak economic_points! Inicjalizuje na 0")
            self.economic_points = 0
            
        current_pe = self.economic_points
        
        if points <= 0:
            print(f"⚠️ [ECONOMY] Próba odejęcia {points} PE - ignoruje")
            return
            
        if current_pe < points:
            print(f"🚫 [ECONOMY BLOCK] BLOKADA! Próba odejęcia {points} PE, dostępne {current_pe} PE")
            print(f"🚫 [ECONOMY BLOCK] Odejmuję maksimum: {current_pe} PE")
            self.economic_points = 0
        else:
            self.economic_points = current_pe - points
            print(f"💰 [ECONOMY] PE: {current_pe} → {self.economic_points} (odejęto {points})")
        
        # Dodatkowa kontrola bezpieczeństwa
        if self.economic_points < 0:
            print(f"🚨 [ECONOMY EMERGENCY] WYKRYTO UJEMNE PE ({self.economic_points})! Przywracam do 0")
            self.economic_points = 0

    def get_points(self):
        """Zwraca aktualne punkty ekonomiczne i specjalne."""
        return {"economic_points": self.economic_points, "special_points": self.special_points}

    def get_assigned_points(self):
        """Zwraca liczbę punktów przydzielonych dowódcom."""
        return self.assigned_points

    def add_economic_points(self, points):
        """Dodaje punkty ekonomiczne (np. z punktów kluczowych)."""
        self.economic_points += points

if __name__ == "__main__":
    economy = EconomySystem()
