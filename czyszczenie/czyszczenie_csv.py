#!/usr/bin/env python3
"""
CZYSZCZENIE CSV - Czyści wszystkie pliki CSV z folderu logs
Autor: AI Assistant
Data: 7.09.2025

Usuwa REKURSYWNIE:
- WSZYSTKIE pliki *.csv z logs/ i wszystkich podkatalogów
- actions_*.csv
- ai_actions_*.csv  
- ai_purchases_*.csv
- ai_general/*.csv
- garrison_issues/*.csv
- ai_commander/*.csv
- ai_flow/*.csv
"""

import os
import glob
import sys
from pathlib import Path

def get_project_root():
    """Znajdź katalog główny projektu"""
    current = Path(__file__).parent
    while current.parent != current:
        if (current / 'main_ai.py').exists():
            return current
        current = current.parent
    return Path(__file__).parent.parent

def clean_csv_files():
    """Czyści wszystkie pliki CSV z folderu logs PLUS inne pliki logów"""
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    
    print("🧹 CZYSZCZENIE LOGS - START (ULEPSZONE)")
    print(f"📁 Katalog logs: {logs_dir}")
    print("-" * 50)
    
    if not logs_dir.exists():
        print("❌ Katalog logs nie istnieje!")
        return False
    
    deleted_count = 0
    total_size = 0
    
    # ROZSZERZONE CZYSZCZENIE - wszystkie pliki logów
    extensions_to_clean = [
        "*.csv",      # CSV files
        "*.log",      # Log files  
        "*.json",     # JSON reports
        "*.txt"       # Text logs
    ]
    
    print("🔍 Szukam wszystkich plików logów w logs/ i podkatalogach...")
    print(f"🎯 Rozszerzenia: {', '.join(extensions_to_clean)}")
    
    all_files = []
    
    # Znajdź wszystkie pliki do usunięcia
    for extension in extensions_to_clean:
        files = list(logs_dir.rglob(extension))
        all_files.extend(files)
    
    # Usuń duplikaty
    all_files = list(set(all_files))
    
    print(f"📄 Znaleziono {len(all_files)} plików do usunięcia:")
    
    # Wyświetl co będzie usunięte (preview)
    for file_path in all_files:
        try:
            size = file_path.stat().st_size
            relative_path = file_path.relative_to(logs_dir)
            print(f"📋 {relative_path} ({size:,} B)")
        except Exception:
            print(f"📋 {file_path.name} (rozmiar nieznany)")
    
    if all_files:
        print("-" * 30)
        confirm = input(f"🗑️  Usunąć {len(all_files)} plików? (tak/nie): ").lower().strip()
        
        if confirm not in ['tak', 't', 'yes', 'y']:
            print("❌ Operacja anulowana")
            return False
        
        print("🗑️  Usuwanie plików...")
        
        for file_path in all_files:
            try:
                # Sprawdź rozmiar przed usunięciem
                size = file_path.stat().st_size
                total_size += size
                
                # Relative path do wyświetlenia
                relative_path = file_path.relative_to(logs_dir)
                
                # Usuń plik
                file_path.unlink()
                deleted_count += 1
                
                print(f"✅ {relative_path}")
                
            except Exception as e:
                print(f"❌ Błąd usuwania {file_path.name}: {e}")
    
    # DODATKOWO: Usuń puste katalogi
    empty_dirs_removed = 0
    for root, dirs, files in os.walk(logs_dir, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):  # Jeśli katalog pusty
                    dir_path.rmdir()
                    empty_dirs_removed += 1
                    rel_dir = dir_path.relative_to(logs_dir)
                    print(f"📁 Usunięto pusty katalog: {rel_dir}")
            except Exception:
                pass
    
    print("-" * 50)
    print(f"✅ PODSUMOWANIE:")
    print(f"   📄 Usuniętych plików: {deleted_count}")
    print(f"   📁 Usuniętych pustych katalogów: {empty_dirs_removed}")
    print(f"   💾 Zwolnione miejsce: {total_size / 1024:.1f} KB ({total_size / 1024 / 1024:.2f} MB)")
    
    if deleted_count == 0:
        print("ℹ️  Brak plików do usunięcia")
    else:
        print("🎉 Katalog logs został wyczyszczony!")
    
    return True

def clean_csv_interactive():
    """Interaktywne czyszczenie z potwierdzeniem"""
    print("🧹 CZYSZCZENIE PLIKÓW CSV Z LOGS")
    print("=" * 40)
    print("Usuwa:")
    print("• WSZYSTKIE pliki *.csv z logs/")
    print("• WSZYSTKIE pliki *.csv z podkatalogów")
    print("• ai_general/*.csv")
    print("• garrison_issues/*.csv") 
    print("• ai_commander/*.csv")
    print("• ai_flow/*.csv")
    print("• actions_*.csv")
    print("• ai_actions_*.csv")
    print("• ai_purchases_*.csv")
    print()
    
    response = input("Czy kontynuować? (tak/nie): ").lower().strip()
    
    if response in ['tak', 't', 'yes', 'y']:
        return clean_csv_files()
    else:
        print("❌ Operacja anulowana")
        return False

def main():
    """Główna funkcja"""
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        # Tryb automatyczny bez pytań
        clean_csv_files()
    else:
        # Tryb interaktywny
        clean_csv_interactive()

if __name__ == "__main__":
    main()
