#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Przygotowanie do refaktoryzacji engine/action.py i implementacji AI
Tworzy backup i przygotowuje strukture
"""

import os
import shutil
import datetime

def create_backup():
    """Tworzy backup przed refaktoryzacja"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_pre_refactor_{timestamp}"
    
    print(f"[BACKUP] Tworze backup: {backup_dir}")
    
    # Backup kluczowych plikow przed refaktoryzacja
    important_files = [
        "engine/action.py",
        "engine/engine.py", 
        "engine/player.py",
        "gui/panel_dowodcy.py"
    ]
    
    os.makedirs(backup_dir, exist_ok=True)
    
    for file_path in important_files:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, file_path)
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(file_path, backup_path)
            print(f"[OK] Backup: {file_path}")

def prepare_ai_structure():
    """Przygotowuje strukture dla AI dowodcow"""
    print("\nPrzygotowuje strukture AI...")    
    # Tworzenie plikow startowych dla AI
    ai_files = {
        "ai/__init__.py": "# AI package for Kampania 1939\n",
        "ai/commanders/__init__.py": "# AI commanders implementations\n",
        "ai/commanders/base_commander.py": '''"""
Bazowa klasa dla AI dowodcow
"""

class BaseCommander:
    """Bazowa klasa dla wszystkich AI dowodcow"""
    
    def __init__(self, player_id, difficulty="medium"):
        self.player_id = player_id
        self.difficulty = difficulty
        self.name = "Base Commander"
    
    def make_decision(self, game_state):
        """Podejmuje decyzje na podstawie stanu gry"""
        raise NotImplementedError("Subclasses must implement make_decision")
    
    def evaluate_position(self, game_state):
        """Ocenia aktualna pozycje na planszy"""
        raise NotImplementedError("Subclasses must implement evaluate_position")
''',
        "ai/decision_trees/__init__.py": "# Decision trees for AI\n",
        "ai/strategies/__init__.py": "# AI strategies\n"
    }
    
    for file_path, content in ai_files.items():
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[CREATE] Utworzono: {file_path}")

def create_refactor_plan():
    """Tworzy szczegolowy plan refaktoryzacji"""
    plan = """# PLAN REFAKTORYZACJI ENGINE/ACTION.PY

## CELE
1. Uproszczenie struktury akcji
2. Lepsze type hints
3. Podzial na mniejsze, testowalne funkcje
4. Przygotowanie dla integracji z AI

## ETAPY

### ETAP 1: Analiza obecnej struktury
- [ ] Identyfikacja wszystkich typow akcji
- [ ] Mapowanie zaleznosci miedzy akcjami
- [ ] Wylistowanie funkcji do podzialu

### ETAP 2: Refaktoryzacja
- [ ] Podzial execute_action na mniejsze funkcje
- [ ] Stworzenie oddzielnych klas dla typow akcji
- [ ] Dodanie type hints
- [ ] Dokumentacja wszystkich funkcji

### ETAP 3: Testy
- [ ] Aktualizacja istniejacych testow
- [ ] Dodanie testow jednostkowych dla nowych klas
- [ ] Testy integracyjne

### ETAP 4: Integracja z AI
- [ ] Interface dla AI do podejmowania decyzji
- [ ] Funkcje pomocnicze dla oceny stanu gry
- [ ] Integracja z systemem dowodcow

## PRZYGOTOWANIE DLA AI DOWODCOW

### Struktura AI:
```
ai/
├── commanders/
│   ├── base_commander.py       - Bazowa klasa
│   ├── aggressive_commander.py - Agresywny styl
│   ├── defensive_commander.py  - Defensywny styl
│   └── balanced_commander.py   - Zbalansowany styl
├── decision_trees/
│   ├── combat_decisions.py     - Decyzje bojowe
│   ├── movement_decisions.py   - Decyzje ruchu
│   └── economic_decisions.py   - Decyzje ekonomiczne
└── strategies/
    ├── early_game.py          - Strategia wczesnej gry
    ├── mid_game.py            - Strategia srodkowej gry
    └── late_game.py           - Strategia poznej gry
```

### Interface AI-Engine:
- `GameState` - snapshot stanu gry dla AI
- `ActionEvaluator` - ocena akcji przez AI
- `DecisionMaker` - podejmowanie decyzji przez AI
"""
    
    with open("docs/REFACTOR_AND_AI_PLAN.md", 'w', encoding='utf-8') as f:
        f.write(plan)
    print("[PLAN] Utworzono szczegolowy plan refaktoryzacji")

def main():
    print("PRZYGOTOWANIE DO REFAKTORYZACJI I AI")
    print("=" * 50)
    
    # 1. Backup przed refaktoryzacją
    create_backup()
    
    # 2. Struktura AI
    prepare_ai_structure()
      # 3. Utworzenie docs jesli nie istnieje
    os.makedirs("docs", exist_ok=True)
    
    # 4. Plan refaktoryzacji
    create_refactor_plan()
    
    print("\n" + "=" * 50)
    print("[SUKCES] PRZYGOTOWANIE ZAKONCZONE!")
    print("\nKOLEJNE KROKI:")
    print("1. Uruchom cleanup_project.py")
    print("2. Uruchom reorganize_project.py") 
    print("3. Rozpocznij refaktoryzacje engine/action.py")
    print("4. Implementuj AI dowodcow")
    print("\nSprawdz: docs/REFACTOR_AND_AI_PLAN.md")

if __name__ == "__main__":
    main()
