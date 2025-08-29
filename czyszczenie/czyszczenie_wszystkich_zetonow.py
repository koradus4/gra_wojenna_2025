#!/usr/bin/env python3
"""
Prosty skrypt czyszczący żetony z gry.
Usuwa wszystkie żetony z mapy, katalog tokens i plik start_tokens.json.
"""

import json
import os
import shutil
import sys

def clear_tokens_directory():
    """Czyści katalog assets/tokens"""
    tokens_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "tokens")
    
    if os.path.exists(tokens_dir):
        print(f"Czyszczenie katalogu: {tokens_dir}")
        # Usuń zawartość katalogu, ale zostaw sam katalog
        for item in os.listdir(tokens_dir):
            item_path = os.path.join(tokens_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"  Usunięto katalog: {item}")
            else:
                os.remove(item_path)
                print(f"  Usunięto plik: {item}")
    else:
        print(f"Katalog {tokens_dir} nie istnieje")

def clear_start_tokens_file():
    """Czyści/usuwa plik start_tokens.json"""
    start_tokens_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "start_tokens.json")
    
    if os.path.exists(start_tokens_file):
        print(f"Usuwanie pliku: {start_tokens_file}")
        os.remove(start_tokens_file)
        print("  Plik start_tokens.json usunięty")
    else:
        print(f"Plik {start_tokens_file} nie istnieje")

def clear_tokens_from_map():
    """Usuwa wszystkie wpisy 'token' z map_data.json"""
    map_data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "map_data.json")
    
    if not os.path.exists(map_data_file):
        print(f"Plik {map_data_file} nie istnieje")
        return
    
    print(f"Czyszczenie żetonów z mapy: {map_data_file}")
    
    try:
        with open(map_data_file, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
        
        removed_count = 0
        if 'terrain' in map_data:
            for hex_coords, hex_data in map_data['terrain'].items():
                if 'token' in hex_data:
                    del hex_data['token']
                    removed_count += 1
        
        with open(map_data_file, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, indent=2, ensure_ascii=False)
        
        print(f"  Usunięto {removed_count} żetonów z mapy")
        
    except Exception as e:
        print(f"Błąd podczas czyszczenia map_data.json: {e}")

def confirm_operation():
    """Potwierdzenie operacji czyszczenia"""
    print("⚠️  UWAGA! ⚠️")
    print("To działanie NIEODWRACALNIE usunie:")
    print("- Wszystkie żetony z katalogu assets/tokens/")
    print("- Plik assets/start_tokens.json") 
    print("- Wszystkie żetony z mapy (data/map_data.json)")
    print()
    print("❌ WSZYSTKIE ŻETONY ZOSTANĄ USUNIĘTE! ❌")
    print()
    
    while True:
        response = input("Czy na pewno chcesz kontynuować? Wpisz 'TAK' aby potwierdzić lub 'NIE' aby anulować: ").strip().upper()
        
        if response == "TAK":
            print("✅ Potwierdzono - rozpoczynam czyszczenie...")
            return True
        elif response == "NIE":
            print("❌ Anulowano - żetony pozostają bez zmian")
            return False
        else:
            print("❓ Proszę wpisać 'TAK' lub 'NIE'")

def main():
    """Główna funkcja czyszcząca"""
    print("=== CZYSZCZENIE ŻETONÓW Z GRY ===")
    print()
    
    # Sprawdź czy użytkownik potwierdza operację
    if not confirm_operation():
        sys.exit(0)
    
    print()
    print("🔄 Rozpoczynam czyszczenie...")
    print()
    
    # 1. Wyczyść katalog tokens
    clear_tokens_directory()
    print()
    
    # 2. Usuń plik start_tokens.json
    clear_start_tokens_file()
    print()
    
    # 3. Usuń żetony z map_data.json
    clear_tokens_from_map()
    print()
    
    print("=== CZYSZCZENIE ZAKOŃCZONE ===")

if __name__ == "__main__":
    main()
