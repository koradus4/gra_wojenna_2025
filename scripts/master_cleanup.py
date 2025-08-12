#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MASTER SCRIPT - Kompletne porzadkowanie projektu Kampania 1939
Wykonuje wszystkie operacje porzadkowania w odpowiedniej kolejnosci
"""

import subprocess
import sys
import os

def run_script(script_name, description):
    """Uruchamia skrypt i wyswietla postep"""
    print(f"\n[PROCES] {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"[SUKCES] {description} - ZAKONCZONE POMYSLNIE")
        else:
            print(f"[BLAD] BLAD w {script_name}:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"[BLAD] BLAD wykonania {script_name}: {e}")
        return False
    
    return True

def check_git_status():
    """Sprawdza czy projekt jest w git i czy sa niezapisane zmiany"""
    if os.path.exists(".git"):
        print("[GIT] Projekt jest w Git - sprawdzam status...")
        try:
            result = subprocess.run(["git", "status", "--porcelain"], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                print("[UWAGA] Sa niezapisane zmiany w Git!")
                print("Czy chcesz kontynuowac? (y/n): ", end="")
                if input().lower() != 'y':
                    return False
        except:
            print("[UWAGA] Nie mozna sprawdzic statusu Git")
    return True

def main():
    print("MASTER SCRIPT - PORZADKOWANIE KAMPANIA 1939")
    print("=" * 60)
    print("Ten skrypt wykona kompletne porzadkowanie projektu:")
    print("1. Usunie zbedne pliki i foldery")
    print("2. Zreorganizuje strukture projektu") 
    print("3. Przygotuje do refaktoryzacji i AI")
    print("=" * 60)
      # Sprawdzenie Git
    if not check_git_status():
        print("[STOP] Przerwano na zyczenie uzytkownika")
        return
    
    print("\nCzy chcesz kontynuowac? (y/n): ", end="")
    if input().lower() != 'y':
        print("[STOP] Przerwano na zyczenie uzytkownika")
        return
    
    scripts = [
        ("cleanup_project.py", "CZYSZCZENIE ZBEDNYCH PLIKOW"),
        ("reorganize_project.py", "REORGANIZACJA STRUKTURY"),
        ("prepare_refactor.py", "PRZYGOTOWANIE DO REFAKTORYZACJI")
    ]
    
    success_count = 0
    
    for script, description in scripts:
        if run_script(script, description):
            success_count += 1
        else:
            print(f"\n[BLAD] Nie udalo sie wykonac {script}")
            print("Czy chcesz kontynuowac? (y/n): ", end="")
            if input().lower() != 'y':
                break
    
    print("\n" + "=" * 60)
    print("PODSUMOWANIE PORZADKOWANIA")
    print("=" * 60)
    
    if success_count == len(scripts):
        print("[SUKCES] WSZYSTKIE OPERACJE ZAKONCZONE POMYSLNIE!")
        print("\nPROJEKT JEST GOTOWY DO:")
        print("- Refaktoryzacji engine/action.py")
        print("- Implementacji AI dowodcow")
        print("- Rozbudowy testow")
        print("- Dalszego rozwoju")
        
        print("\nNOWA STRUKTURA:")
        print("engine/          - Silnik gry")
        print("gui/             - Interface")
        print("ai/              - AI dowodcow (przygotowane)")
        print("tests/           - Testy (oczyszczone)")
        print("docs/            - Dokumentacja")
        print("scripts/         - Skrypty")
        print("... inne foldery")
        
        print("\nNASTEPNE KROKI:")
        print("1. Sprawdz docs/REFACTOR_AND_AI_PLAN.md")
        print("2. Rozpocznij refaktoryzacje engine/action.py")
        print("3. Implementuj pierwszego AI dowodce")
        
    else:
        print(f"[UWAGA] WYKONANO {success_count}/{len(scripts)} operacji")
        print("Sprawdz bledy powyzej i uruchom ponownie")
    
    print("\nMILEGO KODOWANIA!")

if __name__ == "__main__":
    main()
