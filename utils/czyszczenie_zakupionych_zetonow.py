#!/usr/bin/env python3
"""
Narzędzie do czyszczenia folderów żetonów po testach zakupów
Usuwa żetony z folderów poczekalni i aktualnych
"""

import os
import shutil
from pathlib import Path
import argparse
from datetime import datetime

class TokenFolderCleaner:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent / "assets" / "tokens"
        self.folders_to_clean = [
            "aktualne",
            "nowe_dla_2", 
            "nowe_dla_3",
            "nowe_dla_4",  # Niemcy generał
            "nowe_dla_5",  # Niemcy dowódca 1
            "nowe_dla_6",  # Niemcy dowódca 2
            "ai_units_2",  # AI units (jeśli zostały)
            "ai_units_3",
            "ai_units_4", 
            "ai_units_5",
            "ai_units_6"
        ]
    
    def scan_folders(self):
        """Skanuje foldery i pokazuje co jest do wyczyszczenia"""
        print("🔍 SKANOWANIE FOLDERÓW ŻETONÓW...")
        print(f"📁 Ścieżka bazowa: {self.base_path}")
        print()
        
        total_items = 0
        folders_found = []
        
        for folder_name in self.folders_to_clean:
            folder_path = self.base_path / folder_name
            
            if folder_path.exists():
                items = list(folder_path.iterdir())
                if items:
                    folders_found.append((folder_name, folder_path, items))
                    total_items += len(items)
                    print(f"📂 {folder_name}/")
                    for item in items:
                        if item.is_dir():
                            json_file = item / "token.json"
                            png_file = item / "token.png"
                            status = "✅" if json_file.exists() and png_file.exists() else "⚠️"
                            print(f"  {status} {item.name}")
                        else:
                            print(f"  📄 {item.name}")
                    print()
                else:
                    print(f"📂 {folder_name}/ - pusty")
            else:
                print(f"📂 {folder_name}/ - nie istnieje")
        
        print(f"📊 PODSUMOWANIE: {len(folders_found)} folderów z zawartością, {total_items} elementów łącznie")
        return folders_found, total_items
    
    def clean_folders(self, force=False):
        """Czyści foldery żetonów"""
        folders_found, total_items = self.scan_folders()
        
        if total_items == 0:
            print("✅ Wszystkie foldery są już czyste!")
            return
        
        if not force:
            print("⚠️  UWAGA: Ta operacja usunie wszystkie żetony z folderów poczekalni!")
            print(f"   Zostaną usunięte {total_items} elementy z {len(folders_found)} folderów.")
            response = input("\n❓ Kontynuować? (tak/nie): ").strip().lower()
            if response not in ['tak', 't', 'yes', 'y']:
                print("❌ Operacja anulowana")
                return
        
        print("\n🧹 ROZPOCZYNAM CZYSZCZENIE...")
        
        cleaned_folders = 0
        cleaned_items = 0
        
        for folder_name, folder_path, items in folders_found:
            print(f"🗑️  Czyszczę {folder_name}/...")
            
            for item in items:
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                        print(f"   ✅ Usunięto folder: {item.name}")
                    else:
                        item.unlink()
                        print(f"   ✅ Usunięto plik: {item.name}")
                    cleaned_items += 1
                except Exception as e:
                    print(f"   ❌ Błąd usuwania {item.name}: {e}")
            
            cleaned_folders += 1
        
        print(f"\n✅ CZYSZCZENIE ZAKOŃCZONE!")
        print(f"   📂 Wyczyszczono folderów: {cleaned_folders}")
        print(f"   🗑️  Usunięto elementów: {cleaned_items}")
    
    def backup_before_clean(self):
        """Tworzy backup przed czyszczeniem"""
        backup_dir = self.base_path.parent / "backup_tokens" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"💾 Tworzę backup w: {backup_dir}")
        
        backed_up = 0
        for folder_name in self.folders_to_clean:
            folder_path = self.base_path / folder_name
            if folder_path.exists() and any(folder_path.iterdir()):
                backup_folder = backup_dir / folder_name
                shutil.copytree(folder_path, backup_folder)
                backed_up += 1
                print(f"   ✅ {folder_name}/ -> backup")
        
        if backed_up > 0:
            print(f"✅ Backup utworzony ({backed_up} folderów)")
        else:
            print("ℹ️  Nic do backupu")
        
        return backup_dir if backed_up > 0 else None

def main():
    parser = argparse.ArgumentParser(description="Narzędzie do czyszczenia folderów żetonów")
    parser.add_argument('--scan', action='store_true', help='Tylko zeskanuj foldery (nie czyść)')
    parser.add_argument('--force', action='store_true', help='Czyść bez pytania o potwierdzenie')
    parser.add_argument('--backup', action='store_true', help='Utwórz backup przed czyszczeniem')
    
    args = parser.parse_args()
    
    cleaner = TokenFolderCleaner()
    
    print("🧹 === CZYSZCZENIE FOLDERÓW ŻETONÓW ===")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if args.scan:
        cleaner.scan_folders()
        return
    
    if args.backup:
        backup_path = cleaner.backup_before_clean()
        if backup_path:
            print()
    
    cleaner.clean_folders(force=args.force)

if __name__ == "__main__":
    main()
