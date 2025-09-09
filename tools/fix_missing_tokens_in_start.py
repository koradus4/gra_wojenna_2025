#!/usr/bin/env python3
"""
Naprawia problem brakujących zetonów w start_tokens.json
Znajduje zetony w assets/tokens/aktualne/ które nie są w start_tokens.json
i dodaje je używając inteligentnego systemu pozycjonowania.
"""
import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

def load_existing_start_tokens():
    """Wczytaj istniejące zetony z start_tokens.json"""
    start_tokens_path = Path("assets/start_tokens.json")
    if start_tokens_path.exists():
        with open(start_tokens_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def get_aktualne_tokens():
    """Pobierz listę wszystkich zetonów z folderu aktualne/"""
    aktualne_dir = Path("assets/tokens/aktualne")
    tokens = {}
    
    for json_file in aktualne_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
                token_id = token_data.get("id")
                if token_id:
                    tokens[token_id] = {
                        "data": token_data,
                        "file": json_file
                    }
        except Exception as e:
            print(f"⚠️ Błąd wczytywania {json_file}: {e}")
    
    return tokens

def get_nation_from_token(token_data):
    """Wyciągnij nację z danych tokena"""
    # Sprawdź pole nation w stats lub bezpośrednio
    nation = token_data.get("nation")
    if nation:
        return nation
        
    stats = token_data.get("stats", {})
    nation = stats.get("nation")
    if nation:
        return nation
    
    # Fallback - zgadnij z ID tokena
    token_id = token_data.get("id", "")
    if "Polska" in token_id or token_id.startswith("P_"):
        return "Polska"
    elif "Niemcy" in token_id or token_id.startswith("N_") or token_id.startswith("G_"):
        return "Niemcy"
    elif "Sowiecka" in token_id or "ZSRR" in token_id or token_id.startswith("S_"):
        return "Sowiecka"
    elif "Francj" in token_id or token_id.startswith("F_"):
        return "Francja"
    elif "Wielka" in token_id or "Brytani" in token_id or token_id.startswith("B_"):
        return "Wielka Brytania"
    
    print(f"⚠️ Nie można określić nacji dla tokena {token_id}")
    return None

def find_optimal_spawn_for_nation(nation, occupied_positions):
    """Znajdź optymalną pozycję spawn dla nacji używając inteligentnego systemu"""
    try:
        # Import inteligentnego systemu
        from ai.smart_deployment import find_optimal_spawn_position
        
        # Utwórz dane tokena dla systemu
        token_data = {
            "nation": nation,
            "type": "unknown"  # Może być rozwinięte w przyszłości
        }
        
        # Wywołaj inteligentny system
        position = find_optimal_spawn_position(None, None, token_data, nation)
        
        if position and position not in occupied_positions:
            return position
            
    except Exception as e:
        print(f"⚠️ Błąd inteligentnego pozycjonowania: {e}")
    
    # Fallback do prostego systemu spawn points
    return find_simple_spawn_for_nation(nation, occupied_positions)

def find_simple_spawn_for_nation(nation, occupied_positions):
    """Prosty fallback system spawn points"""
    try:
        # Wczytaj spawn points z map_data.json
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
                
        print(f"❌ Wszystkie spawn points zajęte dla {nation}")
        return None
        
    except Exception as e:
        print(f"❌ Błąd wczytywania spawn points: {e}")
        return None

def fix_missing_tokens():
    """Główna funkcja naprawcza"""
    print("🔧 Naprawiam brakujące zetony w start_tokens.json...")
    
    # 1. Wczytaj istniejące
    start_tokens = load_existing_start_tokens()
    existing_ids = {token["id"] for token in start_tokens}
    occupied_positions = {(token["q"], token["r"]) for token in start_tokens}
    
    print(f"📊 Istniejące zetony w start_tokens.json: {len(existing_ids)}")
    
    # 2. Wczytaj zetony z aktualne/
    aktualne_tokens = get_aktualne_tokens()
    print(f"📊 Zetony w folderze aktualne/: {len(aktualne_tokens)}")
    
    # 3. Znajdź brakujące
    missing_tokens = []
    for token_id, token_info in aktualne_tokens.items():
        if token_id not in existing_ids:
            missing_tokens.append((token_id, token_info))
    
    print(f"🔍 Znalezione brakujące zetony: {len(missing_tokens)}")
    
    if not missing_tokens:
        print("✅ Wszystkie zetony są już w start_tokens.json")
        return
    
    # 4. Dodaj brakujące zetony z pozycjami
    added_count = 0
    for token_id, token_info in missing_tokens:
        print(f"\n🔧 Przetwarzanie: {token_id}")
        
        # Określ nację
        nation = get_nation_from_token(token_info["data"])
        if not nation:
            print(f"❌ Pomijam - nie można określić nacji")
            continue
            
        # Znajdź pozycję
        position = find_optimal_spawn_for_nation(nation, occupied_positions)
        if not position:
            print(f"❌ Pomijam - nie można znaleźć pozycji dla {nation}")
            continue
            
        # Dodaj do start_tokens
        new_entry = {
            "id": token_id,
            "q": position[0],
            "r": position[1]
        }
        start_tokens.append(new_entry)
        occupied_positions.add(position)
        added_count += 1
        
        print(f"✅ Dodano {token_id} na pozycji {position} (nacja: {nation})")
    
    # 5. Zapisz zaktualizowany start_tokens.json
    if added_count > 0:
        start_tokens_path = Path("assets/start_tokens.json")
        with open(start_tokens_path, 'w', encoding='utf-8') as f:
            json.dump(start_tokens, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Dodano {added_count} zetonów do start_tokens.json")
        print("🎯 Teraz wszystkie zetony powinny być widoczne na mapie!")
    else:
        print("\n❌ Nie udało się dodać żadnych zetonów")

if __name__ == "__main__":
    fix_missing_tokens()
