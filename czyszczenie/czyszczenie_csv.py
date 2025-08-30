#!/usr/bin/env python3
"""
CZYSZCZENIE CSV - Czyści pliki CSV z folderu logs
Autor: AI Assistant
Data: 31.08.2025

Usuwa:
- actions_*.csv
- ai_actions_*.csv  
- ai_purchases_*.csv
- Pliki CSV z podfolderów (ai_general/, ai_commander/, ai_flow/)
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
    """Czyści wszystkie pliki CSV z folderu logs"""
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    
    print("🧹 CZYSZCZENIE CSV - START")
    print(f"📁 Katalog logs: {logs_dir}")
    print("-" * 50)
    
    if not logs_dir.exists():
        print("❌ Katalog logs nie istnieje!")
        return False
    
    deleted_count = 0
    total_size = 0
    
    # Wzorce plików CSV do usunięcia
    csv_patterns = [
        "actions_*.csv",
        "ai_actions_*.csv", 
        "ai_purchases_*.csv",
        "ai_general/*.csv",
        "ai_commander/*.csv",
        "ai_flow/*.csv"
    ]
    
    for pattern in csv_patterns:
        pattern_path = logs_dir / pattern
        files = glob.glob(str(pattern_path))
        
        for file_path in files:
            file_obj = Path(file_path)
            if file_obj.exists():
                try:
                    # Sprawdź rozmiar przed usunięciem
                    size = file_obj.stat().st_size
                    total_size += size
                    
                    # Usuń plik
                    file_obj.unlink()
                    deleted_count += 1
                    
                    # Krótka nazwa dla wyświetlenia
                    relative_path = file_obj.relative_to(logs_dir)
                    print(f"🗑️  {relative_path} ({size} B)")
                    
                except Exception as e:
                    print(f"❌ Błąd usuwania {file_obj.name}: {e}")
    
    print("-" * 50)
    print(f"✅ PODSUMOWANIE:")
    print(f"   📄 Usuniętych plików: {deleted_count}")
    print(f"   💾 Zwolnione miejsce: {total_size / 1024:.1f} KB")
    
    if deleted_count == 0:
        print("ℹ️  Brak plików CSV do usunięcia")
    
    return True

def clean_csv_interactive():
    """Interaktywne czyszczenie z potwierdzeniem"""
    print("🧹 CZYSZCZENIE PLIKÓW CSV Z LOGS")
    print("=" * 40)
    print("Usuwa:")
    print("• actions_*.csv")
    print("• ai_actions_*.csv")
    print("• ai_purchases_*.csv") 
    print("• CSV z podfolderów ai_general/, ai_commander/, ai_flow/")
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
