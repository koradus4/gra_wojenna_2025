#!/usr/bin/env python3
"""
Narzędzie testowe do weryfikacji systemu czyszczenia.
Sprawdza czy wszystkie komponenty zostały poprawnie wyczyszczone z zakupionych zetonów.
"""
import json
from pathlib import Path

def test_cleaning_system():
    """Testuje kompletność systemu czyszczenia"""
    print("🔍 TESTOWANIE SYSTEMU CZYSZCZENIA...")
    print("=" * 50)
    
    # Test 1: Folder nowe_dla_*
    tokens_dir = Path("assets/tokens")
    nowe_folders = list(tokens_dir.glob("nowe_dla_*"))
    print(f"📂 Foldery nowe_dla_*: {len(nowe_folders)}")
    for folder in nowe_folders:
        items = list(folder.iterdir()) if folder.exists() else []
        print(f"   {folder.name}: {len(items)} elementów")
    
    # Test 2: Folder aktualne/ - pliki nowy_*
    aktualne_dir = tokens_dir / "aktualne"
    if aktualne_dir.exists():
        nowy_json = list(aktualne_dir.glob("nowy_*.json"))
        nowy_png = list(aktualne_dir.glob("nowy_*.png"))
        print(f"📂 aktualne/ - nowy_*.json: {len(nowy_json)}")
        print(f"📂 aktualne/ - nowy_*.png: {len(nowy_png)}")
        
        if nowy_json:
            print("   ❌ POZOSTAŁE PLIKI JSON:")
            for f in nowy_json[:5]:  # Pokaż max 5
                print(f"      {f.name}")
        
        if nowy_png:
            print("   ❌ POZOSTAŁE PLIKI PNG:")
            for f in nowy_png[:5]:  # Pokaż max 5
                print(f"      {f.name}")
    else:
        print("📂 aktualne/ - folder nie istnieje")
    
    # Test 3: index.json - zetony nowy_*
    index_path = Path("assets/tokens/index.json")
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        total_tokens = len(index_data)
        nowy_tokens = [t for t in index_data if t.get("id", "").startswith("nowy_")]
        
        print(f"📄 index.json - łącznie zetonów: {total_tokens}")
        print(f"📄 index.json - zetony nowy_*: {len(nowy_tokens)}")
        
        if nowy_tokens:
            print("   ❌ POZOSTAŁE ZETONY NOWY_*:")
            for token in nowy_tokens[:5]:  # Pokaż max 5
                print(f"      {token.get('id', 'NO_ID')}")
    else:
        print("📄 index.json - plik nie istnieje")
    
    # Test 4: start_tokens.json - pozycje nowy_*
    start_path = Path("assets/start_tokens.json")
    if start_path.exists():
        with open(start_path, 'r', encoding='utf-8') as f:
            start_data = json.load(f)
        
        total_positions = len(start_data)
        nowy_positions = [p for p in start_data if p.get("id", "").startswith("nowy_")]
        
        print(f"📄 start_tokens.json - łącznie pozycji: {total_positions}")
        print(f"📄 start_tokens.json - pozycje nowy_*: {len(nowy_positions)}")
        
        if nowy_positions:
            print("   ❌ POZOSTAŁE POZYCJE NOWY_*:")
            for pos in nowy_positions[:5]:  # Pokaż max 5
                print(f"      {pos.get('id', 'NO_ID')} -> ({pos.get('q')}, {pos.get('r')})")
    else:
        print("📄 start_tokens.json - plik nie istnieje")
    
    # Podsumowanie
    print("\n" + "=" * 50)
    
    issues_found = False
    if nowe_folders and any(list(f.iterdir()) if f.exists() else [] for f in nowe_folders):
        print("❌ Problem: Niepuste foldery nowe_dla_*")
        issues_found = True
        
    if aktualne_dir.exists() and (list(aktualne_dir.glob("nowy_*.json")) or list(aktualne_dir.glob("nowy_*.png"))):
        print("❌ Problem: Pliki nowy_* w folderze aktualne/")
        issues_found = True
        
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        if any(t.get("id", "").startswith("nowy_") for t in index_data):
            print("❌ Problem: Zetony nowy_* w index.json")
            issues_found = True
            
    if start_path.exists():
        with open(start_path, 'r', encoding='utf-8') as f:
            start_data = json.load(f)
        if any(p.get("id", "").startswith("nowy_") for p in start_data):
            print("❌ Problem: Pozycje nowy_* w start_tokens.json")
            issues_found = True
    
    if not issues_found:
        print("✅ SYSTEM CZYSZCZENIA DZIAŁA POPRAWNIE!")
        print("✅ Wszystkie zakupione zetony zostały wyczyszczone.")
    else:
        print("⚠️ ZNALEZIONO PROBLEMY W SYSTEMIE CZYSZCZENIA")
        print("⚠️ Niektóre zakupione zetony nie zostały wyczyszczone.")
    
    print("=" * 50)

if __name__ == "__main__":
    test_cleaning_system()
