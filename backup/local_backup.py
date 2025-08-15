#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOKALNY BACKUP PROJEKTU
======================

Tworzy kopię całego projektu na dysku lokalnym z datą i godziną.

Autor: Backup System
Data: 27 lipca 2025
"""

import os
import shutil
import datetime
from pathlib import Path
import sys

def create_local_backup():
    """Tworzy kopię zapasową projektu na dysku lokalnym."""
    
    # Ścieżka do głównego katalogu projektu (parent od backup/)
    project_root = Path(__file__).parent.parent
    project_name = project_root.name
    
    # Generuj znacznik czasu
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Nazwa folderu kopii: gra_wojenna_YYYYMMDD_HHMMSS
    backup_folder_name = f"gra_wojenna_{timestamp}"
    
    # Domyślna ścieżka backup (można zmienić)
    default_backup_path = Path.home() / "Desktop" / "backups_gra_wojenna"
    
    # Zapytaj użytkownika o lokalizację (opcjonalnie)
    print(f"🎯 LOKALNY BACKUP PROJEKTU")
    print(f"=" * 50)
    print(f"📁 Projekt: {project_name}")
    print(f"📅 Data i czas: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Domyślna lokalizacja: {default_backup_path}")
    print()
    
    # Zapytaj czy użyć domyślnej lokalizacji
    use_default = input("Użyć domyślnej lokalizacji? (T/n): ").strip().lower()
    
    if use_default in ['n', 'nie', 'no']:
        custom_path = input("Podaj ścieżkę do folderu backup: ").strip()
        if custom_path:
            backup_base_path = Path(custom_path)
        else:
            backup_base_path = default_backup_path
    else:
        backup_base_path = default_backup_path
    
    # Pełna ścieżka do kopii
    backup_path = backup_base_path / backup_folder_name
    
    # Utwórz katalog backup jeśli nie istnieje
    try:
        backup_base_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Katalog backup utworzony: {backup_base_path}")
    except Exception as e:
        print(f"❌ Błąd tworzenia katalogu backup: {e}")
        return False
    
    # Lista wykluczeń (pliki/foldery do pominięcia)
    exclude_patterns = {
        '__pycache__',
        '.git',
        '.vscode',
        'node_modules',
        '*.pyc',
        '*.pyo',
        '*.log',
        '.DS_Store',
        'Thumbs.db',
        '*.tmp',
        '*.temp'
    }
    
    def should_exclude(path_name):
        """Sprawdza czy plik/folder powinien być wykluczony."""
        for pattern in exclude_patterns:
            if pattern.startswith('*') and path_name.endswith(pattern[1:]):
                return True
            elif path_name == pattern:
                return True
        return False
    
    # Kopiuj projekt
    print(f"🔄 Rozpoczynam kopiowanie...")
    print(f"📂 Źródło: {project_root}")
    print(f"📂 Cel: {backup_path}")
    print()
    
    try:
        # Utwórz główny folder kopii
        backup_path.mkdir(exist_ok=True)
        
        # Liczniki dla statystyk
        files_copied = 0
        files_skipped = 0
        folders_created = 0
        
        # Kopiuj wszystkie pliki i foldery
        for root, dirs, files in os.walk(project_root):
            # Wykluczy foldery w dirs (modyfikacja in-place)
            dirs[:] = [d for d in dirs if not should_exclude(d)]
            
            # Oblicz relatywną ścieżkę
            rel_root = Path(root).relative_to(project_root)
            target_dir = backup_path / rel_root
            
            # Utwórz katalog docelowy
            if rel_root != Path('.'):  # Nie twórz głównego katalogu ponownie
                target_dir.mkdir(parents=True, exist_ok=True)
                folders_created += 1
                
            # Kopiuj pliki
            for file in files:
                if should_exclude(file):
                    files_skipped += 1
                    continue
                    
                source_file = Path(root) / file
                target_file = target_dir / file
                
                try:
                    shutil.copy2(source_file, target_file)
                    files_copied += 1
                    
                    # Progress indicator co 50 plików
                    if files_copied % 50 == 0:
                        print(f"📄 Skopiowano: {files_copied} plików...")
                        
                except Exception as e:
                    print(f"⚠️ Błąd kopiowania {source_file}: {e}")
                    files_skipped += 1
        
        # Utwórz plik informacyjny o backup
        info_file = backup_path / "BACKUP_INFO.txt"
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"KOPIA ZAPASOWA PROJEKTU GRA WOJENNA\n")
            f.write(f"=" * 40 + "\n\n")
            f.write(f"Data utworzenia: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Projekt źródłowy: {project_root}\n")
            f.write(f"Lokalizacja kopii: {backup_path}\n")
            f.write(f"Wersja: {timestamp}\n\n")
            f.write(f"STATYSTYKI:\n")
            f.write(f"- Plików skopiowanych: {files_copied}\n")
            f.write(f"- Plików pominiętych: {files_skipped}\n")
            f.write(f"- Folderów utworzonych: {folders_created}\n\n")
            f.write(f"WYKLUCZONE WZORCE:\n")
            for pattern in sorted(exclude_patterns):
                f.write(f"- {pattern}\n")
        
        # Oblicz rozmiar kopii
        total_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        print(f"\n🎉 BACKUP ZAKOŃCZONY POMYŚLNIE!")
        print(f"=" * 50)
        print(f"📂 Lokalizacja: {backup_path}")
        print(f"📊 Statystyki:")
        print(f"   - Plików skopiowanych: {files_copied}")
        print(f"   - Plików pominiętych: {files_skipped}")
        print(f"   - Folderów utworzonych: {folders_created}")
        print(f"   - Rozmiar kopii: {size_mb:.1f} MB")
        print(f"⏰ Czas wykonania: {timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ BŁĄD podczas tworzenia kopii: {e}")
        # Usuń częściową kopię w przypadku błędu
        if backup_path.exists():
            try:
                shutil.rmtree(backup_path)
                print(f"🧹 Wyczyszczono częściową kopię.")
            except:
                pass
        return False

def main():
    """Główna funkcja programu."""
    print("🚀 LOKALNY BACKUP PROJEKTU GRA WOJENNA")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("Użycie:")
        print("  python local_backup.py          # Interaktywny backup")
        print("  python local_backup.py -h       # Pomoc")
        print()
        print("Skrypt tworzy kopię całego projektu z datą i godziną.")
        print("Domyślna lokalizacja: ~/Desktop/backups_gra_wojenna/")
        return
    
    success = create_local_backup()
    
    if success:
        print("\n✅ Backup zakończony sukcesem!")
        input("\nNaciśnij Enter aby zakończyć...")
    else:
        print("\n❌ Backup zakończony błędem!")
        input("\nNaciśnij Enter aby zakończyć...")
        sys.exit(1)

if __name__ == "__main__":
    main()

# Deprecated. Use backup_local_min.py
