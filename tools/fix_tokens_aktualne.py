"""
Naprawa tokenów w folderze aktualne/ - poprawia ścieżki i dodaje do index.json
Uruchamiany ręcznie żeby naprawić istniejące tokeny
"""
import json
from pathlib import Path
import sys
import os

# Dodaj ścieżkę do głównego folderu projektu
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def add_to_start_tokens(token_data):
    """Dodaje token do start_tokens.json z pozycją spawn"""
    try:
        start_tokens_path = Path("assets/start_tokens.json")
        if start_tokens_path.exists():
            with open(start_tokens_path, 'r', encoding='utf-8') as f:
                start_data = json.load(f)
        else:
            start_data = []
            
        token_id = token_data.get("id", "")
        
        # Sprawdź czy token już nie ma pozycji
        if not any(existing["id"] == token_id for existing in start_data):
            # Znajdź wolny spawn point dla nacji tokena
            spawn_position = find_free_spawn_point(token_data.get("nation", ""))
            
            if spawn_position:
                # Dodaj token z pozycją
                start_entry = {
                    "id": token_id,
                    "q": spawn_position[0],
                    "r": spawn_position[1]
                }
                start_data.append(start_entry)
                
                # Zapisz zaktualizowany start_tokens.json
                with open(start_tokens_path, 'w', encoding='utf-8') as f:
                    json.dump(start_data, f, indent=2, ensure_ascii=False)
                    
                print(f"✅ Dodano {token_id} do start_tokens.json na pozycji {spawn_position}")
            else:
                print(f"⚠️ Brak wolnych spawn points dla nacji {token_data.get('nation', '')}")
        else:
            print(f"ℹ️ Token {token_id} już ma pozycję w start_tokens.json")
            
    except Exception as e:
        print(f"❌ Błąd dodawania do start_tokens.json: {e}")

def find_free_spawn_point(nation):
    """Znajdź wolny spawn point dla danej nacji"""
    try:
        # Wczytaj map_data.json dla spawn points
        map_data_path = Path("data/map_data.json")
        if not map_data_path.exists():
            print(f"❌ Brak pliku map_data.json")
            return None
            
        with open(map_data_path, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
            
        spawn_points = map_data.get("spawn_points", {}).get(nation, [])
        if not spawn_points:
            print(f"❌ Brak spawn points dla nacji {nation}")
            return None
            
        # Wczytaj zajęte pozycje z start_tokens.json
        start_tokens_path = Path("assets/start_tokens.json")
        occupied_positions = set()
        if start_tokens_path.exists():
            with open(start_tokens_path, 'r', encoding='utf-8') as f:
                start_data = json.load(f)
            occupied_positions = {(pos["q"], pos["r"]) for pos in start_data}
        
        # Znajdź pierwszy wolny spawn point
        for spawn_str in spawn_points:
            try:
                q, r = map(int, spawn_str.split(','))
                if (q, r) not in occupied_positions:
                    print(f"✅ Znaleziono wolny spawn point ({q},{r}) dla {nation}")
                    return (q, r)
            except ValueError:
                print(f"⚠️ Błędny format spawn point: {spawn_str}")
                continue
                
        print(f"⚠️ Wszystkie spawn points zajęte dla {nation}")
        # Zwróć pierwszy spawn point jako fallback
        try:
            q, r = map(int, spawn_points[0].split(','))
            return (q, r)
        except (ValueError, IndexError):
            return None
            
    except Exception as e:
        print(f"❌ Błąd wyszukiwania spawn point: {e}")
        return None

def fix_existing_tokens():
    """Naprawia wszystkie tokeny w folderze aktualne/"""
    try:
        aktualne_dir = Path("assets/tokens/aktualne")
        index_path = Path("assets/tokens/index.json")
        
        if not aktualne_dir.exists():
            print("❌ Folder aktualne/ nie istnieje")
            return
            
        # Wczytaj obecny index.json
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        else:
            index_data = []
            
        existing_ids = {token.get("id", "") for token in index_data}
        fixed_count = 0
        added_count = 0
        
        # Przetwórz wszystkie pliki JSON w aktualne/
        for json_file in aktualne_dir.glob("*.json"):
            try:
                # Wczytaj dane tokena
                with open(json_file, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
                
                token_id = token_data.get("id", "")
                token_name = json_file.stem  # nazwa pliku bez rozszerzenia
                
                # Popraw ścieżkę obrazka jeśli jest błędna
                current_image = token_data.get("image", "")
                correct_image = f"assets/tokens/aktualne/{token_name}.png"
                
                if current_image != correct_image:
                    token_data["image"] = correct_image
                    
                    # Zapisz poprawiony JSON
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(token_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Poprawiono ścieżkę obrazka dla: {token_id}")
                    fixed_count += 1
                
                # Dodaj do index.json jeśli nie istnieje
                if token_id not in existing_ids:
                    index_data.append(token_data)
                    existing_ids.add(token_id)
                    print(f"✅ Dodano do index.json: {token_id}")
                    added_count += 1
                    
                    # KLUCZOWE: Dodaj także do start_tokens.json z pozycją spawn
                    add_to_start_tokens(token_data)
                    
            except Exception as e:
                print(f"❌ Błąd przetwarzania {json_file}: {e}")
        
        # Zapisz zaktualizowany index.json
        if added_count > 0:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎯 PODSUMOWANIE:")
        print(f"   - Poprawiono ścieżki: {fixed_count} tokenów")
        print(f"   - Dodano do index.json: {added_count} tokenów")
        print(f"   - Tokeny powinny być teraz widoczne na mapie!")
        
    except Exception as e:
        print(f"❌ Błąd główny: {e}")

if __name__ == "__main__":
    print("🔧 Naprawiam tokeny w folderze aktualne/...")
    fix_existing_tokens()
