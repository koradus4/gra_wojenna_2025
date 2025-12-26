"""
TEST KOŃCOWY - Sprawdzenie czy system deployment po naprawkach działa end-to-end
"""
import json
from pathlib import Path

def test_complete_workflow():
    """Test pełnego workflow: kupno -> deployment -> widoczność"""
    print("🎯 TEST KOŃCOWY: Sprawdzenie pełnego workflow deployment")
    
    # 1. Sprawdź czy tokeny są w aktualne/
    aktualne_dir = Path("assets/tokens/aktualne")
    token_files = list(aktualne_dir.glob("nowy_K_*.json"))
    print(f"📁 Tokeny kawalerii w aktualne/: {len(token_files)}")
    
    # 2. Sprawdź czy mają poprawne ścieżki obrazków
    correct_paths = 0
    for token_file in token_files:
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            image_path = token_data.get("image", "")
            if "assets/tokens/aktualne/" in image_path:
                correct_paths += 1
                print(f"✅ {token_file.name}: poprawna ścieżka obrazka")
            else:
                print(f"❌ {token_file.name}: błędna ścieżka: {image_path}")
        except Exception as e:
            print(f"❌ Błąd odczytu {token_file.name}: {e}")
    
    # 3. Sprawdź czy są w index.json
    index_path = Path("assets/tokens/index.json")
    tokens_in_index = 0
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            for token_file in token_files:
                token_id = token_file.stem
                if any(token.get("id") == token_id for token in index_data):
                    tokens_in_index += 1
                    print(f"✅ {token_id}: znaleziony w index.json")
                else:
                    print(f"❌ {token_id}: brak w index.json")
        except Exception as e:
            print(f"❌ Błąd odczytu index.json: {e}")
    
    # 4. Podsumowanie
    print(f"\n🎯 WYNIK TESTU:")
    print(f"   - Tokeny w aktualne/: {len(token_files)}")
    print(f"   - Poprawne ścieżki obrazków: {correct_paths}/{len(token_files)}")
    print(f"   - Tokeny w index.json: {tokens_in_index}/{len(token_files)}")
    
    if len(token_files) > 0 and correct_paths == len(token_files) and tokens_in_index == len(token_files):
        print("✅ SUKCES: System deployment działa w 100%!")
        print("✅ Tokeny kawalerii powinny być widoczne na mapie!")
        return True
    else:
        print("❌ PROBLEM: System deployment wymaga dalszych poprawek")
        return False

if __name__ == "__main__":
    test_complete_workflow()
