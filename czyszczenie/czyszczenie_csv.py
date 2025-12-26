#!/usr/bin/env python3
"""
CZYSZCZENIE CSV - Czyści wszystkie pliki CSV z folderu logs
Autor: AI Assistant for Commander
Wersja: 4.0 - STRUKTURA logs/sesja_aktualna/ + KOMPATYBILNOŚĆ
Data: 15.09.2025

NOWY WORKFLOW (v4.0) - POLSKIE NAZWY:
====================================
🗑️ ZAWSZE CZYŚCI:
- logs/sesja_aktualna/**/*.csv - Pliki sesyjne AI (NOWE POLSKIE NAZWY)
- logs/current_session/**/*.csv - Pliki sesyjne AI (KOMPATYBILNOŚĆ)
- logs/sesja_aktualna/**/*.log - Logi sesji (NOWE)
- logs/sesja_aktualna/**/*.txt - Teksty sesji (NOWE)
- logs/current_session/**/*.log - Logi sesji (KOMPATYBILNOŚĆ)
- logs/current_session/**/*.txt - Teksty sesji (KOMPATYBILNOŚĆ)

🛡️ ZAWSZE CHRONI:
- logs/analysis/**/* - Dane uczenia maszynowego i archiwa
- logs/analysis/ml_ready/* - Datasets gotowe do ML
- logs/analysis/raporty/* - Raporty długoterminowe

⚙️ TRYB ZALEŻNY:
- Inne pliki w logs/ - bezpieczny z ochroną, agresywny bez ochrony

STRUKTURA:
==========
logs/
├── sesja_aktualna/           ← CZYŚCIĆ CO SESJĘ (NOWE POLSKIE NAZWY)
│   ├── ai_commander/         ← Logi AI Commander 
│   ├── ai_general/           ← Logi AI General
│   ├── specialized/          ← Logi specjalistyczne
│   └── vp_intelligence/      ← VP Intelligence sesji
├── current_session/          ← CZYŚCIĆ CO SESJĘ (KOMPATYBILNOŚĆ)
├── archiwum_sesji/           ← CHRONIĆ ZAWSZE (archiwa sesji)
├── analysis/                 ← CHRONIĆ ZAWSZE
│   ├── ml_ready/            ← Dane ML
│   ├── raporty/             ← Raporty
│   └── statystyki/          ← Stats długoterminowe
├── dane_ml/                  ← CHRONIĆ ZAWSZE (dane uczenia)
└── vp_intelligence/          ← Mieszane (zależne od trybu)
    └── archives/            ← Chronione archiwa
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
    """Czyści TYLKO pliki z logs/sesja_aktualna/ - BEZPIECZNIE chroni pozostałe!"""
    return _clean_logs_files(aggressive=False)

def clean_csv_files_aggressive():
    """AGRESYWNE czyszczenie - czyści CSV + JSON po wpisaniu kodu zabezpieczenia"""
    return _clean_logs_files(aggressive=True)

def _clean_logs_files(aggressive: bool = False):
    """Czyści pliki z folderu logs z OCHRONĄ lub bez (tryb agresywny)
    
    NOWA LOGIKA v4.0 - POLSKIE NAZWY + KOMPATYBILNOŚĆ:
    - logs/sesja_aktualna/ - ZAWSZE czyści (pliki sesyjne, NOWE POLSKIE NAZWY)
    - logs/sesja_aktualna/ - ZAWSZE czyści (pliki sesyjne, NOWY SYSTEM)  
    - logs/current_session/ - TAKŻE czyści (pliki sesyjne, KOMPATYBILNOŚĆ)  
    - logs/analysis/ - ZAWSZE chroni (dane ML i długoterminowe)
    - Inne foldery - zależne od trybu (aggressive/safe)
    """
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    
    # Obsługuj zarówno nowy jak i stary folder sesji
    sesja_aktualna_dir = logs_dir / "sesja_aktualna"
    current_session_dir = logs_dir / "current_session"
    
    mode_text = "AGRESYWNE (CSV + JSON)" if aggressive else "BEZPIECZNE (z ochroną ML)"
    print(f"🧹 CZYSZCZENIE LOGS v4.0 - START ({mode_text})")
    print(f"📁 Katalog logs: {logs_dir}")
    print(f"🎯 NOWY WORKFLOW: logs/sesja_aktualna/ zawsze czyśczona w trybie bezpiecznym!")
    print("-" * 50)
    
    if not logs_dir.exists():
        print("❌ Katalog logs nie istnieje!")
        return False
    
    deleted_count = 0
    protected_count = 0
    total_size = 0
    
    # NOWA OCHRONA DANYCH - bardziej precyzyjna
    protected_patterns = [
        "analysis/ml_ready",      # Dane uczenia maszynowego
        "analysis/raporty",       # Raporty sesji
        "analysis/statystyki",    # Statystyki długoterminowe  
        "vp_intelligence/archives" # Archiwa VP Intelligence
    ]
    
    # PRIORYTETY CZYSZCZENIA:
    # 1. logs/sesja_aktualna/ + logs/current_session/ - ZAWSZE czyść (pliki sesyjne)
    # 2. logs/analysis/ - ZAWSZE chroń (dane ML)
    # 3. Inne - zależne od trybu
    
    # ROZSZERZONE CZYSZCZENIE - zależne od trybu
    if aggressive:
        extensions_to_clean = [
            "*.csv",      # CSV files (BEZ ochrony w trybie agresywnym)
            "*.json",     # JSON files (BEZ ochrony w trybie agresywnym)
            "*.log",      # Log files  
            "*.txt"       # Text logs
        ]
        print("🔥 TRYB AGRESYWNY: USUWA WSZYSTKO! (także ML i JSON!)")
    else:
        extensions_to_clean = [
            "*.csv",      # CSV files (z ochroną)
            "*.log",      # Log files  
            "*.txt"       # Text logs (JSON chronione)
        ]
        print("🛡️ TRYB BEZPIECZNY: Czyści TYLKO sesja_aktualna/, chroni resztę!")
    
    print("🔍 Szukam plików do przeanalizowania...")
    print(f"🎯 Rozszerzenia: {', '.join(extensions_to_clean)}")
    print(f"🛡️ Chronię: {', '.join(protected_patterns)}")
    print(f"🗑️ CZYŚCIĆ: logs/sesja_aktualna/ (pliki sesyjne)")
    if not aggressive:
        print(f"🛡️ CHRONIĆ: logs/ - wszystko poza sesja_aktualna/ (tryb bezpieczny)")
    else:
        print(f"💀 KASOWAĆ: logs/ - WSZYSTKIE pliki, także ML! (tryb agresywny)")
    
    all_files = []
    
    # Znajdź wszystkie pliki do przeanalizowania
    for extension in extensions_to_clean:
        files = list(logs_dir.rglob(extension))
        all_files.extend(files)
    
    # Usuń duplikaty
    all_files = list(set(all_files))
    
    print(f"📄 Przeanalizowano {len(all_files)} plików:")
    
    # Przeanalizuj każdy plik z NOWĄ LOGIKĄ
    files_to_delete = []
    files_to_protect = []
    
    for file_path in all_files:
        try:
            # NOWA LOGIKA OCHRONY:
            # 1. sesja_aktualna/ - ZAWSZE USUŃ (pliki sesyjne)
            # 2. analysis/ - ZAWSZE CHROŃ (dane ML)
            # 3. Inne - zależne od trybu i wzorców
            
            relative_path = file_path.relative_to(logs_dir)
            relative_unix = str(relative_path).replace("\\", "/")
            
            # CASE 1: logs/sesja_aktualna/ lub logs/current_session/ - zawsze czyść
            if relative_unix.startswith("sesja_aktualna/") or relative_unix.startswith("current_session/"):
                files_to_delete.append(file_path)
                size = file_path.stat().st_size
                print(f"🗑️ SESYJNY: {relative_path} ({size:,} B)")
                continue
                
            # CASE 2: logs/analysis/ - chroń TYLKO w trybie bezpiecznym
            if relative_unix.startswith("analysis/") and not aggressive:
                files_to_protect.append(file_path)
                size = file_path.stat().st_size
                print(f"🛡️ ARCHIWUM: {relative_path} ({size:,} B)")
                protected_count += 1
                continue
            elif relative_unix.startswith("analysis/") and aggressive:
                # W trybie agresywnym także usuń analysis/
                files_to_delete.append(file_path)
                size = file_path.stat().st_size
                print(f"💀 KASUJE ML: {relative_path} ({size:,} B)")
                continue
                
            # CASE 3: Inne pliki - sprawdź wzorce i tryb
            should_protect = False
            if not aggressive:
                # W trybie bezpiecznym CHROŃ pliki które nie są w sesja_aktualna/
                # USUŃ tylko gdy spełnia warunki specjalne lub jest w sesja_aktualna/
                should_protect = True  # DOMYŚLNIE CHROŃ w trybie bezpiecznym
                
                # Wyjątki - te pliki można usunąć nawet w trybie bezpiecznym:
                exceptions_to_clean = [
                    "temp/",           # Pliki tymczasowe
                    "cache/",          # Cache
                    "debug/",          # Debug logi (nie ML)
                ]
                
                # Sprawdź czy plik jest w wyjątkach (można usunąć)
                if any(exc in relative_unix for exc in exceptions_to_clean):
                    should_protect = False
            else:
                # W trybie agresywnym NIE chroń niczego - usuń WSZYSTKO!
                should_protect = False  # AGRESYWNY = ZERO OCHRONY
            
            if should_protect:
                files_to_protect.append(file_path)
                size = file_path.stat().st_size
                print(f"🛡️ CHRONIĘ: {relative_path} ({size:,} B)")
                protected_count += 1
            else:
                files_to_delete.append(file_path)
                size = file_path.stat().st_size
                symbol = "💀" if aggressive else "🗑️"
                print(f"{symbol} USUJĘ: {relative_path} ({size:,} B)")
        except Exception:
            print(f"⚠️ Nie mogę przeanalizować: {file_path.name}")
    
    if files_to_delete:
        print("-" * 30)
        print(f"📊 PODSUMOWANIE:")
        print(f"🗑️ Do usunięcia: {len(files_to_delete)} plików")
        print(f"🛡️ Chronionych: {len(files_to_protect)} plików")
        print()
        
        confirm = input(f"🗑️ Usunąć {len(files_to_delete)} plików sesyjnych? (tak/nie): ").lower().strip()
        
        if confirm not in ['tak', 't', 'yes', 'y']:
            print("❌ Operacja anulowana")
            return False
        
        print("🗑️ Usuwanie plików sesyjnych...")
        
        for file_path in files_to_delete:
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
    else:
        print("ℹ️ Brak plików sesyjnych do usunięcia")
    
    # DODATKOWO: Usuń puste katalogi sesyjne (ale nie chronione)
    empty_dirs_removed = 0
    for root, dirs, files in os.walk(logs_dir, topdown=False):
        try:
            # Nie usuwaj głównych katalogów analysis/, vp_intelligence/archives/
            relative_dir = Path(root).relative_to(logs_dir)
            relative_unix_dir = str(relative_dir).replace("\\", "/")
            
            if any(pattern in relative_unix_dir for pattern in protected_patterns):
                continue
            
            # NOWE: Czyść katalogi sesyjne nawet jeśli zawierają .session_lock
            if relative_unix_dir.startswith("sesja_aktualna/") or relative_unix_dir.startswith("current_session/"):
                try:
                    # Usuń wszystkie pliki w katalogu sesyjnym (włączając .session_lock)
                    for file_in_dir in Path(root).iterdir():
                        if file_in_dir.is_file():
                            file_in_dir.unlink()
                            print(f"🗑️ SESYJNY PLIK: {file_in_dir.relative_to(logs_dir)}")
                    
                    # Usuń katalog jeśli jest pusty
                    if not os.listdir(root):
                        os.rmdir(root)
                        print(f"📁 Usunięto pusty katalog sesyjny: {relative_dir}")
                        empty_dirs_removed += 1
                except Exception as e:
                    print(f"⚠️ Nie można wyczyścić katalogu sesyjnego {relative_dir}: {e}")
                continue
                
            # Standardowe usuwanie pustych katalogów
            if not os.listdir(root):  # Pusty katalog
                os.rmdir(root)
                print(f"📁 Usunięto pusty katalog: {relative_dir}")
                empty_dirs_removed += 1
        except Exception:
            pass
    
    # FINALNE PODSUMOWANIE
    print("-" * 50)
    print(f"✅ CZYSZCZENIE ZAKOŃCZONE:")
    print(f"🗑️ Usunięto plików: {deleted_count}")
    print(f"🛡️ Chronionych plików: {protected_count}")
    print(f"📁 Usunięto pustych katalogów: {empty_dirs_removed}")
    print(f"💾 Zwolniono miejsca: {total_size:,} bajtów ({total_size/1024/1024:.1f} MB)")
    
    if current_session_dir.exists():
        print(f"🎯 UWAGA: Foldery logs/sesja_aktualna/ i logs/current_session/ zostają wyczyszczone!")
    
    return deleted_count > 0


def verify_security_code():
    """Weryfikuje kod zabezpieczenia dla trybu agresywnego"""
    print("🚨 OSTRZEŻENIE: AGRESYWNY TRYB KASOWANIA!")
    print("💀 To usunie WSZYSTKIE pliki, także dane uczenia maszynowego!")
    print("🛡️ Aby kontynuować, wpisz kod: ZNISZCZ_ML")
    
    code = input("🔐 Kod zabezpieczenia: ").strip()
    
    if code == "ZNISZCZ_ML":
        print("✅ Kod poprawny - aktywuję tryb agresywny")
        return True
    else:
        print("❌ Błędny kod - operacja anulowana")
        return False


if __name__ == "__main__":
    print("🧹 CZYSZCZENIE LOGS v4.1 - Nowa struktura logs/sesja_aktualna/")
    print("=" * 60)
    print("1. BEZPIECZNE czyszczenie (chroni dane ML)")
    print("2. AGRESYWNE czyszczenie (kasuje WSZYSTKO po kodzie)")
    print("3. Wyjście")
    
    try:
        choice = input("\nWybór (1-3): ").strip()
        
        if choice == "1":
            clean_csv_files()
        elif choice == "2":
            if verify_security_code():
                clean_csv_files_aggressive()
        elif choice == "3":
            print("👋 Do widzenia!")
        else:
            print("❌ Nieprawidłowy wybór")
    except KeyboardInterrupt:
        print("\n❌ Operacja przerwana przez użytkownika")
    except Exception as e:
        print(f"❌ Błąd: {e}")