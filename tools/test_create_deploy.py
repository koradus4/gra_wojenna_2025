"""
Test tworzenia nowych tokenów kawalerii i ich deployment
"""
import sys
from pathlib import Path

# Dodaj ścieżkę do głównego folderu projektu
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ai.deployment_ai import deploy_purchased_units
from gui.token_shop import create_cavalry_for_player

def test_create_and_deploy():
    """Test kompletnego procesu: tworzenie -> deployment -> sprawdzenie"""
    print("🎯 TWORZĘ NOWE TOKENY KAWALERII I TESTUJĘ DEPLOYMENT")
    
    # 1. Utwórz tokeny dla graczy 2 i 3 (Polska)
    print("\n📝 FAZA 1: Tworzenie tokenów...")
    
    try:
        print("Tworzę kawalerię dla gracza 2...")
        create_cavalry_for_player(2, "Polska")
        print("✅ Token dla gracza 2 utworzony")
        
        print("Tworzę kawalerię dla gracza 3...")
        create_cavalry_for_player(3, "Polska") 
        print("✅ Token dla gracza 3 utworzony")
        
    except Exception as e:
        print(f"❌ Błąd tworzenia tokenów: {e}")
        return False
    
    # 2. Sprawdź foldery nowe_dla_X
    print("\n📁 FAZA 2: Sprawdzenie folderów nowe_dla_X...")
    
    nowe_folders = []
    for player_id in [2, 3]:
        nowe_dir = Path(f"assets/tokens/nowe_dla_{player_id}")
        if nowe_dir.exists():
            token_folders = [f for f in nowe_dir.iterdir() if f.is_dir()]
            if token_folders:
                print(f"✅ nowe_dla_{player_id}: {len(token_folders)} folderów")
                nowe_folders.extend(token_folders)
            else:
                print(f"⚠️ nowe_dla_{player_id}: folder pusty")
        else:
            print(f"❌ nowe_dla_{player_id}: folder nie istnieje")
    
    if not nowe_folders:
        print("❌ Brak tokenów do deployment")
        return False
    
    # 3. Deployment
    print("\n🚀 FAZA 3: Deployment tokenów...")
    
    try:
        result = deploy_purchased_units()
        print(f"Deployment result: {result}")
        
    except Exception as e:
        print(f"❌ Błąd deployment: {e}")
        return False
    
    # 4. Sprawdź rezultaty
    print("\n🔍 FAZA 4: Sprawdzenie rezultatów...")
    
    aktualne_dir = Path("assets/tokens/aktualne")
    if aktualne_dir.exists():
        token_files = list(aktualne_dir.glob("nowy_K_*.json"))
        print(f"📁 Tokeny w aktualne/: {len(token_files)}")
        
        for token_file in token_files:
            print(f"  - {token_file.name}")
            
        return len(token_files) > 0
    else:
        print("❌ Folder aktualne/ nie istnieje")
        return False

if __name__ == "__main__":
    success = test_create_and_deploy()
    print(f"\n🎯 WYNIK: {'✅ SUKCES' if success else '❌ NIEPOWODZENIE'}")
