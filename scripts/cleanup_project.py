#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt porzadkowania projektu Kampania 1939
Usuwa zbedne pliki i foldery przed refaktoryzacja
"""

import os
import shutil
import glob

def remove_directory(path):
    """Usuwa katalog jesli istnieje"""
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f"[OK] Usunieto katalog: {path}")
    else:
        print(f"[INFO] Katalog nie istnieje: {path}")

def remove_file(path):
    """Usuwa plik jesli istnieje"""
    if os.path.exists(path):
        os.remove(path)
        print(f"[OK] Usunieto plik: {path}")
    else:
        print(f"[INFO] Plik nie istnieje: {path}")

def remove_cache_directories():
    """Usuwa wszystkie katalogi __pycache__"""
    cache_dirs = glob.glob("**/__pycache__", recursive=True)
    for cache_dir in cache_dirs:
        remove_directory(cache_dir)

def main():
    print("ROZPOCZYNAM PORZADKOWANIE PROJEKTU")
    print("=" * 50)
    
    # 1. Usuniecie archiwum testow
    print("\nUsuwam archiwalne testy...")
    remove_directory("testy archiwum")
    
    # 2. Usuniecie pustych folderow UI
    print("\nUsuwam puste foldery UI...")
    remove_directory("ui")
    remove_directory("gui_disabled")
    
    # 3. Usuniecie cache'ow
    print("\nUsuwam cache...")
    remove_cache_directories()
    remove_directory(".pytest_cache")
    remove_file(".coverage")
    
    # 4. Usuniecie logow
    print("\nUsuwam logi...")
    remove_file("ekran_startowy.log")
    
    # 5. Sprawdzenie czy istnieja foldery net/store
    print("\nSprawdzam foldery net i store...")
    if os.path.exists("net"):
        remove_directory("net")
    if os.path.exists("store"):
        remove_directory("store")
    
    print("\n" + "=" * 50)
    print("[SUKCES] PORZADKOWANIE ZAKONCZONE!")
    print("\nSTRUKTURA PO CZYSZCZENIU:")
    print("engine/          - Silnik gry (glowny kod)")
    print("gui/             - Interface uzytkownika (glowny kod)")
    print("tests/           - Aktualne testy (czyste)")
    print("core/            - Systemy dodatkowe")
    print("ai/              - AI dowodcow (do rozbudowy)")
    print("accessibility/   - Dostepnosc")
    print("assets/          - Zasoby gry")
    print("data/            - Dane gry")
    print("edytory/         - Narzedzia deweloperskie")
    print("saves/           - Zapisy gry")
    print("tools/           - Narzedzia pomocnicze")

if __name__ == "__main__":
    main()
