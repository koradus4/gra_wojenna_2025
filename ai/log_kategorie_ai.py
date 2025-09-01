"""Centralne kategorie / tagi logów AI.

Dodawaj nowe kategorie tylko jeśli realnie filtrujesz je osobno – unikamy inflacji tagów.
"""
TACTIC = "TACTIC"          # Ruchy taktyczne / misje
DEPLOY = "DEPLOY"          # Deployment nowych jednostek
ERROR = "ERROR"            # Błędy niekrytyczne / wyjątki
FUEL = "FUEL"              # Sprawy paliwa
PROGRESSIVE = "PROGRESSIVE"# Ruch postępowy
PRIORIZER = "PRIORIZER"    # Priorytetyzacja celów
WARN = "WARN"              # Ostrzeżenia
INFO = "INFO"              # Ogólne informacje
DEFENSE = "DEFENSE"        # Faza defensywna
RESUPPLY = "RESUPPLY"      # Uzupełnianie zasobów (HP / CV / ammo)
MOVE = "MOVE"              # Ruch jednostek (standard / advanced)
ADAPTIVE = "ADAPTIVE"      # System adaptacyjny
ASSIGN = "ASSIGN"          # Przydziały grup / liderów
SAVE = "SAVE"              # Zapisy stanu / plików

__all__ = [
    'TACTIC','DEPLOY','ERROR','FUEL','PROGRESSIVE','PRIORIZER','WARN','INFO',
    'DEFENSE','RESUPPLY','MOVE','ADAPTIVE','ASSIGN','SAVE'
]
