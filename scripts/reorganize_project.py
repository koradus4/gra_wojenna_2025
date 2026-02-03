#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reorganizacja struktury projektu Kampania 1939
Konsoliduje i reorganizuje pliki w logiczne grupy
"""

import os
import shutil

def move_file(src, dst):
    """Przenosi plik z src do dst"""
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        print(f"[MOVE] Przeniesiono: {src} -> {dst}")
    else:
        print(f"[INFO] Nie znaleziono: {src}")

def create_directory(path):
    """Tworzy katalog jesli nie istnieje"""
    os.makedirs(path, exist_ok=True)
    print(f"[DIR] Utworzono katalog: {path}")

def main():
    print("REORGANIZACJA STRUKTURY PROJEKTU")
    print("=" * 50)    
    # 1. Stworzenie struktury dla AI
    print("\nPrzygotowuje strukture dla AI dowodcow...")
    create_directory("ai/commanders")
    create_directory("ai/decision_trees")
    create_directory("ai/strategies")
    
    # 2. Konsolidacja planow rozwoju
    print("\nReorganizuje dokumentacje...")
    create_directory("docs/plans")
    
    plans = [
        "PLAN_PUNKTY_KLUCZOWE_I_EKONOMIA.md",
        "PLAN_REFAKTORYZACJI_ENGINE_ACTIONS.md", 
        "PLAN_REFAKTORYZACJI_SILNIKA.md",
        "PLAN_ROZWOJU.md",
        "PLAN_SYSTEMU_WALKI_I_AKCJI.md",
        "PLAN_ZAKUPU_I_WYSTAWIANIA_JEDNOSTEK.md"
    ]
    
    for plan in plans:
        if os.path.exists(plan):
            move_file(plan, f"docs/plans/{plan}")
    
    # 3. Przeniesienie README gameplay
    move_file("README_GAMEPLAY.md", "docs/README_GAMEPLAY.md")
      # 4. Organizacja skryptow
    print("\nOrganizuje skrypty...")
    create_directory("scripts")
    
    scripts = [
        "create_backup.bat",
        "export_to_github.bat"
    ]
    
    for script in scripts:
        if os.path.exists(script):
            move_file(script, f"scripts/{script}")
    
    print("\n" + "=" * 50)
    print("[SUKCES] REORGANIZACJA ZAKONCZONA!")
    
    print("\nNOWA STRUKTURA:")
    print("engine/              - Silnik gry")
    print("gui/                 - Interface")
    print("ai/                  - AI dowodcow")
    print("  commanders/        - Implementacje AI")
    print("  decision_trees/    - Drzewa decyzyjne")
    print("  strategies/        - Strategie AI")
    print("tests/               - Testy")
    print("docs/                - Dokumentacja")
    print("  plans/             - Plany rozwoju")
    print("  README_GAMEPLAY.md")
    print("scripts/             - Skrypty pomocnicze")
    print("core/                - Systemy dodatkowe")
    print("accessibility/       - Dostepnosc")
    print("assets/              - Zasoby")
    print("data/                - Dane")
    print("edytory/             - Edytory")
    print("saves/               - Zapisy")
    print("tools/               - Narzedzia")

if __name__ == "__main__":
    main()
