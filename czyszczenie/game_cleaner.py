"""
Główne narzędzie czyszczenia gry - działa z nową strukturą timestampingu sesji

FUNKCJE CZYSZCZENIA:
===================
- Obsługa logs/sesja_aktualna/ z timestampami (NOWE POLSKIE NAZWY)
- Obsługa logs/current_session/ dla kompatybilności wstecznej
- Inteligentna ochrona danych ML i archiwów
- Kompatybilność z main.py i całym systemem sesji

TRYBY CZYSZCZENIA:
==================
- quick: Szybkie czyszczenie strategic_orders, purchased_tokens
- new_game: Pełne czyszczenie przygotowujące do nowej gry
- csv: Czyszczenie tylko plików CSV z logs/
- tokens_soft: Usuwa rozmieszczone żetony (z backup)
- tokens_hard: Pełne usunięcie żetonów + purge assets/tokens/

BEZPIECZEŃSTWO:
===============
- Zawsze chroni dane ML w logs/analysis/
- Backup przed ryzykownymi operacjami
- Potwierdzenie dla operacji tokens_hard
- Obsługa błędów z informacyjnymi komunikatami
"""

import shutil
from pathlib import Path
from datetime import datetime
import argparse
import json


def clean_strategic_orders():
    """Usuń pliki strategicznych rozkazów"""
    try:
        files_to_clean = [
            "strategic_orders.json",
            "data/strategic_orders.json"
        ]
        
        deleted_count = 0
        for file_path in files_to_clean:
            p = Path(file_path)
            if p.exists():
                p.unlink()
                deleted_count += 1
                print(f"✅ Usunięto: {file_path}")
        
        if deleted_count == 0:
            print("ℹ️ Brak plików strategic_orders do usunięcia")
        else:
            print(f"✅ Usunięto {deleted_count} plików strategic_orders")
            
    except Exception as e:
        print(f"⚠️ Błąd usuwania strategic_orders: {e}")


def clean_purchased_tokens():
    """Usuń zakupione żetony"""
    try:
        purchased_dir = Path("purchased_tokens")
        if not purchased_dir.exists():
            print("ℹ️ Brak katalogu purchased_tokens – pomijam")
            return
            
        deleted_files = 0
        deleted_dirs = 0
        
        for item in purchased_dir.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    deleted_files += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    deleted_dirs += 1
            except Exception as e:
                print(f"⚠️ Nie mogę usunąć {item}: {e}")
        
        if deleted_files or deleted_dirs:
            print(f"✅ Usunięto zakupione żetony: pliki={deleted_files}, katalogi={deleted_dirs}")
        else:
            print("ℹ️ Brak zakupionych żetonów do usunięcia")
            
    except Exception as e:
        print(f"⚠️ Błąd usuwania zakupionych żetonów: {e}")


def clean_purchased_tokens_from_index():
    """Usuń zakupione żetony z index.json"""
    try:
        index_file = Path("index.json")
        if not index_file.exists():
            print("ℹ️ Brak index.json – pomijam czyszczenie")
            return
            
        try:
            data = json.loads(index_file.read_text(encoding='utf-8'))
            if 'purchased_tokens' in data:
                del data['purchased_tokens']
                index_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
                print("✅ Usunięto purchased_tokens z index.json")
            else:
                print("ℹ️ Brak purchased_tokens w index.json")
        except json.JSONDecodeError:
            print("⚠️ Błędny format JSON w index.json")
            
    except Exception as e:
        print(f"⚠️ Błąd czyszczenia index.json: {e}")


def clean_purchased_tokens_from_start():
    """NIE CZYŚĆ start_tokens.json - zostaw rozmieszczone żetony na mapie!"""
    print("ℹ️ start_tokens.json - CHRONIONY (rozmieszczenie żetonów)")


def clean_ai_logs():
    """Usuń logi AI z obsługą nowej struktury timestampingu"""
    try:
        logs_dir = Path("logs")
        if not logs_dir.exists():
            print("ℹ️ Brak katalogu logs – pomijam logi AI")
            return
            
        deleted_files = 0
        deleted_dirs = 0
        protected_files = 0
        
        print("🧹 Czyszczenie logów AI z ochroną danych ML...")
        
        # Wzorce chronionych katalogów
        protected_patterns = [
            "analysis/ml_ready",
            "analysis/raporty", 
            "analysis/statystyki",
            "vp_intelligence/archives"
        ]
        
        # AKTUALIZACJA v4.0: Sprawdź strukturę sesji z polskimi nazwami + kompatybilność
        # Obsługuj zarówno stary current_session jak i nowy sesja_aktualna dla kompatybilności
        for session_folder_name in ["current_session", "sesja_aktualna"]:
            session_folder = logs_dir / session_folder_name
            if session_folder.exists():
                print(f"🎯 Czyszczenie: {session_folder_name}/")
                # Usuń wszystkie foldery timestampów (bezpieczne)
                for timestamp_folder in session_folder.iterdir():
                    if timestamp_folder.is_dir():
                        try:
                            shutil.rmtree(timestamp_folder)
                            deleted_dirs += 1
                            print(f"✅ Usunięto folder sesji: {session_folder_name}/{timestamp_folder.name}")
                        except Exception as e:
                            print(f"⚠️ Nie mogę usunąć {session_folder_name}/{timestamp_folder.name}: {e}")
                            
                print(f"🧹 Wyczyszczono: {session_folder_name}/")
            else:
                print(f"ℹ️ Brak katalogu: {session_folder_name}/")
        
        # Usuń pliki ai_*.csv (stare logi spoza current_session)
        for ai_file in logs_dir.rglob("ai_*.csv"):
            try:
                # Sprawdź czy plik jest w chronionym obszarze
                should_protect = any(pattern in str(ai_file) for pattern in protected_patterns)
                
                if should_protect:
                    print(f"💾 Chronię: {ai_file.relative_to(logs_dir)}")
                    protected_files += 1
                    continue
                
                ai_file.unlink()
                deleted_files += 1
                print(f"✅ Usunięto: {ai_file.relative_to(logs_dir)}")
                
            except Exception as e:
                print(f"⚠️ Nie mogę usunąć {ai_file}: {e}")
        
        # Usuń katalogi ai_* (stare logi)
        for ai_dir in logs_dir.glob("ai_*"):
            if ai_dir.is_dir():
                try:
                    # Sprawdź czy katalog jest chroniony
                    should_protect = any(pattern in str(ai_dir) for pattern in protected_patterns)
                    
                    if should_protect:
                        print(f"💾 Chronię katalog: {ai_dir.relative_to(logs_dir)}")
                        protected_files += 1
                        continue
                    
                    shutil.rmtree(ai_dir)
                    deleted_dirs += 1
                    print(f"✅ Usunięto katalog: {ai_dir.name}")
                    
                except Exception as e:
                    print(f"⚠️ Nie mogę usunąć katalogu {ai_dir}: {e}")
        
        if deleted_files or deleted_dirs or protected_files:
            print(f"✅ Czyszczenie AI zakończone: {deleted_files} plików + {deleted_dirs} katalogów")
            print(f"💾 Chronionych plików ML: {protected_files}")
        else:
            print("ℹ️ Brak logów AI do usunięcia")
            
    except Exception as e:
        print(f"❌ Błąd czyszczenia logów AI: {e}")


def clean_csv_logs():
    """Usuń wszystkie pliki CSV z folderu logs (ZACHOWUJE dane ML i archiwa!)"""
    try:
        logs_dir = Path("logs")
        if not logs_dir.exists():
            print("ℹ️ Brak katalogu logs – pomijam czyszczenie CSV")
            return

        deleted_count = 0
        protected_count = 0
        total_size = 0
        
        print("🧹 Czyszczenie CSV z ochroną danych ML...")
        
        # ROZSZERZONA OCHRONA - wzorce ścieżek do zachowania
        protected_patterns = [
            "analysis/ml_ready",      # Dane ML
            "analysis/raporty",       # Raporty sesji
            "analysis/statystyki",    # Statystyki długoterminowe
            "vp_intelligence/archives" # Archiwa VP Intelligence
        ]
        
        # Usuń WSZYSTKIE pliki CSV rekurencyjnie z logs/ - ALE CHROŃ ważne dane!
        processed_files = set()
        
        for csv_file in logs_dir.rglob("*.csv"):
            if csv_file not in processed_files:
                try:
                    # SPRAWDŹ OCHRONĘ: Czy plik jest w chronionym katalogu?
                    should_protect = any(pattern in str(csv_file) for pattern in protected_patterns)
                    
                    if should_protect:
                        print(f"💾 Chronię: {csv_file.relative_to(logs_dir)}")
                        protected_count += 1
                        continue
                    
                    # USUŃ plik CSV
                    size = csv_file.stat().st_size
                    csv_file.unlink()
                    deleted_count += 1
                    total_size += size
                    processed_files.add(csv_file)
                    print(f"✅ Usunięto: {csv_file.relative_to(logs_dir)}")
                    
                except Exception as e:
                    print(f"⚠️ Nie mogę usunąć {csv_file}: {e}")

        # DODATKOWO: Usuń inne pliki logów (ale nie JSON z protected areas)
        for pattern in ["*.log", "*.txt"]:
            for log_file in logs_dir.rglob(pattern):
                try:
                    # SPRAWDŹ OCHRONĘ
                    should_protect = any(protected_pattern in str(log_file) for protected_pattern in protected_patterns)
                    
                    if should_protect:
                        protected_count += 1
                        continue
                    
                    size = log_file.stat().st_size
                    log_file.unlink()
                    deleted_count += 1
                    total_size += size
                    print(f"✅ Usunięto: {log_file.relative_to(logs_dir)}")
                    
                except Exception as e:
                    print(f"⚠️ Nie mogę usunąć {log_file}: {e}")

        # PODSUMOWANIE
        if deleted_count > 0 or protected_count > 0:
            print(f"✅ Usunięto {deleted_count} plików ({total_size/1024:.1f} KB)")
            print(f"💾 Zachowano {protected_count} plików ML/raportów/archiwów!")
        else:
            print("ℹ️ Brak plików CSV do usunięcia")
            
    except Exception as e:
        print(f"⚠️ Błąd usuwania plików CSV: {e}")


def clean_game_logs():
    """Usuń logi akcji gracza z poprzedniej gry"""
    try:
        logs_dir = Path("logs")
        deleted_files = 0
        deleted_dirs = 0

        if not logs_dir.exists():
            print("ℹ️ Brak katalogu logs – pomijam logi akcji")
            return

        # Rekurencyjne usuwanie plików actions_*.csv
        for f in logs_dir.rglob("actions_*.csv"):
            try:
                f.unlink()
                deleted_files += 1
            except Exception as e:
                print(f"⚠️ Nie mogę usunąć {f}: {e}")

        # Usuń dodatkowy folder game_actions jeśli istnieje
        ga = logs_dir / "game_actions"
        if ga.exists() and ga.is_dir():
            try:
                shutil.rmtree(ga)
                deleted_dirs += 1
            except Exception as e:
                print(f"⚠️ Nie mogę usunąć katalogu {ga}: {e}")

        if deleted_files or deleted_dirs:
            print(f"✅ Usunięto logi akcji: pliki={deleted_files}, katalogi={deleted_dirs}")
        else:
            print("ℹ️ Brak logów akcji do usunięcia (actions_*.csv / game_actions)")
            
    except Exception as e:
        print(f"⚠️ Błąd usuwania logów akcji: {e}")


def clean_all_for_new_game():
    """Kompletne czyszczenie dla nowej gry"""
    print("🧹 CZYSZCZENIE DANYCH Z POPRZEDNIEJ GRY...")
    print("=" * 50)
    
    clean_strategic_orders()
    clean_purchased_tokens()
    clean_purchased_tokens_from_index()
    clean_purchased_tokens_from_start()
    clean_ai_logs()
    clean_game_logs()
    
    print("=" * 50)
    print("✅ CZYSZCZENIE ZAKOŃCZONE - GOTOWY NA NOWĄ GRĘ!")
    print("")


def quick_clean():
    """Szybkie czyszczenie tylko najważniejszych rzeczy"""
    print("🧹 SZYBKIE CZYSZCZENIE...")
    print("-" * 30)
    
    clean_strategic_orders()
    clean_purchased_tokens()
    clean_purchased_tokens_from_index()
    clean_purchased_tokens_from_start()
    
    print("-" * 30)
    print("✅ SZYBKIE CZYSZCZENIE ZAKOŃCZONE!")
    print("")


def csv_only_clean():
    """Czyszczenie TYLKO plików CSV z logs"""
    print("🧹 CZYSZCZENIE CSV...")
    print("-" * 30)
    
    clean_csv_logs()
    
    print("-" * 30)
    print("✅ CZYSZCZENIE CSV ZAKOŃCZONE!")
    print("")


# ==================== NOWE FUNKCJE TOKENS ====================

def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _backup_dir(label: str) -> Path:
    b = Path("backup") / f"{label}_{_ts()}"
    b.mkdir(parents=True, exist_ok=True)
    return b


def _safe_copy(src: Path, dst: Path):
    if src.exists():
        shutil.copy2(src, dst)
        print(f"💾 Backup {src} -> {dst}")
    else:
        print(f"ℹ️ Pomijam backup (brak): {src}")


def _load_map(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"⚠️ Nie mogę odczytać {path}: {e}")
        return None


def _remove_tokens_from_map(map_obj: dict) -> int:
    terrain = map_obj.get('terrain', {})
    removed = 0
    for h, info in terrain.items():
        if isinstance(info, dict) and 'token' in info:
            info.pop('token', None)
            removed += 1
    return removed


def tokens_soft(no_backup: bool = False):
    """UWAGA: Usuń rozmieszczone żetony (start_tokens.json + token fields) – TYLKO dla specjalnych przypadków!"""
    assets = Path('assets')
    data = Path('data')
    start_tokens = assets / 'start_tokens.json'
    map_data = data / 'map_data.json'

    if not no_backup:
        bdir = _backup_dir('tokens_soft')
        _safe_copy(start_tokens, bdir / 'start_tokens.json')
        _safe_copy(map_data, bdir / 'map_data.json')
    else:
        print('(bez backupu)')

    # start_tokens -> []
    start_tokens.parent.mkdir(parents=True, exist_ok=True)
    start_tokens.write_text('[]', encoding='utf-8')
    print('✅ Wyczyszczono assets/start_tokens.json')

    mobj = _load_map(map_data)
    if mobj is None:
        print('ℹ️ Brak map_data.json – pomijam')
    else:
        removed = _remove_tokens_from_map(mobj)
        map_data.write_text(json.dumps(mobj, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'✅ Usunięto {removed} żetonów z mapy (teren/key_points/spawn_points nienaruszone)')

    print('🏁 tokens_soft zakończone.')


def tokens_hard(no_backup: bool = False, confirm: bool = False):
    """UWAGA: Pełne wyczyszczenie żetonów: tokens_soft + PURGE assets/tokens/* - TYLKO dla resetów!"""
    if not confirm:
        print('❌ Odmowa: brak --confirm przy tokens_hard')
        return

    assets_tokens = Path('assets') / 'tokens'
    if not no_backup:
        bdir = _backup_dir('tokens_hard')
        # backup katalogu tokens jako archiwum zip (jeśli istnieje)
        if assets_tokens.exists():
            zip_path = shutil.make_archive(str(bdir / 'tokens_backup'), 'zip', root_dir=assets_tokens)
            print(f'💾 Backup katalogu tokens -> {zip_path}')
        # plus backup plików mapy / start
        _safe_copy(Path('assets') / 'start_tokens.json', bdir / 'start_tokens.json')
        _safe_copy(Path('data') / 'map_data.json', bdir / 'map_data.json')
    else:
        print('(bez backupu)')

    # Soft część
    tokens_soft(no_backup=True)

    # PURGE katalog tokens
    if assets_tokens.exists():
        removed_dirs = 0
        for item in assets_tokens.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
                removed_dirs += 1
            else:
                try:
                    item.unlink()
                except Exception:
                    pass
        print(f'✅ Usunięto {removed_dirs} katalogów w assets/tokens')
    else:
        print('ℹ️ Brak assets/tokens – pomijam purge')
    print('🏁 tokens_hard zakończone.')


# ==================== CLI ====================

def parse_args():
    p = argparse.ArgumentParser(description='Narzędzia czyszczenia projektu')
    p.add_argument('--mode', choices=['quick', 'new_game', 'csv', 'tokens_soft', 'tokens_hard'], default='quick')
    p.add_argument('--no-backup', action='store_true', help='Pomiń tworzenie backupu (tylko tryby tokens_*)')
    p.add_argument('--confirm', action='store_true', help='Wymagane do trybu tokens_hard')
    return p.parse_args()


def main_cli():
    args = parse_args()
    mode = args.mode
    if mode == 'quick':
        quick_clean()
    elif mode == 'new_game':
        clean_all_for_new_game()
    elif mode == 'csv':
        csv_only_clean()
    elif mode == 'tokens_soft':
        tokens_soft(no_backup=args.no_backup)
    elif mode == 'tokens_hard':
        tokens_hard(no_backup=args.no_backup, confirm=args.confirm)
    else:
        print(f'Nieznany tryb: {mode}')


if __name__ == '__main__':
    main_cli()