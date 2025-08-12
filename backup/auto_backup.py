#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOMATYCZNY BACKUP NA GITHUB
=============================

Skrypt automatycznie tworzy kopię projektu i wysyła na GitHub z podaną nazwą.

Użycie:
    python auto_backup.py "nazwa_commita"
    
    LUB uruchom bez argumentów - skrypt zapyta o nazwę commita
    
Przykład:
    python auto_backup.py "Poprawki AI General - system zakupów"
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

def run_command(command, description):
    """Wykonuje komendę w terminalu z opisem"""
    print(f"🔄 {description}...")
    print(f"   Komenda: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Błąd: {e}")
        if e.stderr:
            print(f"   Stderr: {e.stderr.strip()}")
        return False

def main():
    """Główna funkcja backupu"""
    print("🚀 AUTOMATYCZNY BACKUP NA GITHUB")
    print("=" * 50)
    
    # Sprawdź czy podano nazwę commita
    if len(sys.argv) < 2:
        print("📝 Nie podano nazwy commita jako argument")
        print("Przykłady: python auto_backup.py \"Poprawki AI General\"")
        print()
        commit_name = input("💬 Podaj nazwę commita: ").strip()
        
        if not commit_name:
            print("❌ Błąd: Nie można wykonać backup bez nazwy commita!")
            return False
    else:
        commit_name = sys.argv[1]
    timestamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    print(f"📝 Nazwa commita: {commit_name}")
    print(f"⏰ Czas: {timestamp}")
    print()
    
    # Sprawdź czy jesteśmy w repo git
    if not Path(".git").exists():
        print("❌ Błąd: Nie jesteś w repozytorium git!")
        return False
    
    # 1. Sprawdź status
    print("1️⃣ SPRAWDZANIE STATUSU")
    if not run_command("git status --porcelain", "Sprawdzam zmiany"):
        return False
    
    # 2. Dodaj wszystkie pliki
    print("\n2️⃣ DODAWANIE PLIKÓW")
    if not run_command("git add -A", "Dodaję wszystkie pliki do staging"):
        return False
    
    # 3. Sprawdź co zostanie commitowane
    print("\n3️⃣ PODGLĄD ZMIAN")
    run_command("git status --short", "Sprawdzam pliki do commita")
    
    # 4. Potwierdź commit
    print(f"\n4️⃣ POTWIERDZENIE")
    response = input(f"Czy chcesz commitować zmiany jako '{commit_name}'? (tak/nie): ").lower().strip()
    
    if response not in ['tak', 't', 'yes', 'y']:
        print("❌ Anulowano backup")
        return False
    
    # 5. Utwórz commit
    print("\n5️⃣ TWORZENIE COMMITA")
    full_commit_message = f"{commit_name} - {timestamp}"
    if not run_command(f'git commit -m "{full_commit_message}"', "Tworzę commit"):
        print("⚠️ Możliwe że nie ma zmian do commitowania")
    
    # 6. Sprawdź aktualną gałąź
    print("\n6️⃣ SPRAWDZANIE GAŁĘZI")
    try:
        result = subprocess.run("git branch --show-current", shell=True, 
                              capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()
        print(f"   📍 Aktualna gałąź: {current_branch}")
    except:
        current_branch = "main"
        print(f"   📍 Domyślna gałąź: {current_branch}")
    
    # 7. Wypchnij na GitHub
    print("\n7️⃣ WYSYŁANIE NA GITHUB")
    if not run_command(f"git push origin {current_branch}", f"Wysyłam na GitHub (gałąź: {current_branch})"):
        return False
    
    # 8. Podsumowanie
    print("\n🎉 BACKUP ZAKOŃCZONY POMYŚLNIE!")
    print("=" * 50)
    print(f"✅ Commit: {full_commit_message}")
    print(f"✅ Gałąź: {current_branch}")
    print(f"✅ Wysłano na: https://github.com/koradus4/turowka_z_ai")
    print()
    
    return True

if __name__ == "__main__":
    os.chdir("c:/Users/klif/kampania1939_restored")
    success = main()
    
    if success:
        print("🎯 Backup wykonany poprawnie!")
    else:
        print("💥 Wystąpił błąd podczas backupu!")
    
    input("\nNaciśnij Enter aby zakończyć...")
