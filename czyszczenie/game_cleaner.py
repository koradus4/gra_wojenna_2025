"""Narzędzia czyszczenia projektu.

Tryby CLI (python -m utils.game_cleaner --mode <tryb>):
    quick          – szybkie: strategic_orders + purchased tokens (foldery nowe_dla_*)
    new_game       – pełne: jak quick + logi AI + logi akcji
    tokens_soft    – usuń TYLKO rozmieszczone żetony: assets/start_tokens.json -> [] oraz pola token w data/map_data.json (mapa / spawn / key_points zostają)
    tokens_hard    – jak tokens_soft + PURGE assets/tokens/* (z backupem jeśli nie podasz --no-backup)

Opcje:
    --no-backup    – pomija tworzenie katalogu backup/...
    --confirm      – wymaga dla trybu tokens_hard (bez tego odrzuci)

Przykłady (PowerShell):
    python utils/game_cleaner.py --mode quick
    python utils/game_cleaner.py --mode tokens_soft
    python utils/game_cleaner.py --mode tokens_hard --confirm
    python utils/game_cleaner.py --mode tokens_hard --confirm --no-backup
"""
from __future__ import annotations
import os
import shutil
import json
import argparse
from datetime import datetime
from pathlib import Path


def clean_strategic_orders():
    """Usuń stare rozkazy strategiczne"""
    try:
        orders_file = Path("data/strategic_orders.json")
        if orders_file.exists():
            orders_file.unlink()
            print("✅ Usunięto stare rozkazy strategiczne")
        else:
            print("ℹ️ Brak starych rozkazów strategicznych")
    except Exception as e:
        print(f"⚠️ Błąd usuwania rozkazów: {e}")


def clean_purchased_tokens():
    """Usuń wszystkie zakupione żetony z poprzedniej gry"""
    try:
        tokens_dir = Path("assets/tokens")
        deleted_count = 0
        
        # Usuń foldery nowe_dla_X
        for folder in tokens_dir.glob("nowe_dla_*"):
            if folder.is_dir():
                shutil.rmtree(folder)
                deleted_count += 1
                print(f"✅ Usunięto folder: {folder.name}")
        
        # NOWE: Usuń zakupione zetony z folderu aktualne/
        aktualne_dir = tokens_dir / "aktualne"
        if aktualne_dir.exists():
            deleted_files = 0
            # Usuń pliki nowy_* z folderu aktualne/
            for file_path in aktualne_dir.glob("nowy_*.json"):
                try:
                    # Usuń odpowiadający plik PNG
                    png_path = file_path.with_suffix('.png')
                    if png_path.exists():
                        png_path.unlink()
                        deleted_files += 1
                    
                    # Usuń plik JSON
                    file_path.unlink()
                    deleted_files += 1
                    print(f"✅ Usunięto zakupiony zeton: {file_path.stem}")
                except Exception as e:
                    print(f"⚠️ Błąd usuwania {file_path.name}: {e}")
            
            if deleted_files > 0:
                print(f"✅ Usunięto {deleted_files} plików zakupionych zetonów z aktualne/")
        
        if deleted_count > 0:
            print(f"✅ Usunięto {deleted_count} folderów z zakupionymi żetonami")
        else:
            print("ℹ️ Brak zakupionych żetonów do usunięcia")
            
    except Exception as e:
        print(f"⚠️ Błąd usuwania żetonów: {e}")


def clean_purchased_tokens_from_index():
    """Usuń zakupione zetony z assets/tokens/index.json"""
    try:
        index_path = Path("assets/tokens/index.json")
        if not index_path.exists():
            print("ℹ️ Brak pliku index.json - pomijam czyszczenie")
            return
            
        # Wczytaj index.json
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        # Filtruj zetony - usuń te z id zaczynającym się od "nowy_"
        original_count = len(index_data)
        cleaned_data = [token for token in index_data if not token.get("id", "").startswith("nowy_")]
        removed_count = original_count - len(cleaned_data)
        
        if removed_count > 0:
            # Zapisz wyczyszczony index.json
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Usunięto {removed_count} zakupionych zetonów z index.json")
        else:
            print("ℹ️ Brak zakupionych zetonów w index.json")
            
    except Exception as e:
        print(f"⚠️ Błąd czyszczenia index.json: {e}")


def clean_purchased_tokens_from_start():
    """Usuń zakupione zetony z assets/start_tokens.json"""
    try:
        start_path = Path("assets/start_tokens.json")
        if not start_path.exists():
            print("ℹ️ Brak pliku start_tokens.json - pomijam czyszczenie")
            return
            
        # Wczytaj start_tokens.json
        with open(start_path, 'r', encoding='utf-8') as f:
            start_data = json.load(f)
        
        # Filtruj pozycje - usuń te z id zaczynającym się od "nowy_"
        original_count = len(start_data)
        cleaned_data = [pos for pos in start_data if not pos.get("id", "").startswith("nowy_")]
        removed_count = original_count - len(cleaned_data)
        
        if removed_count > 0:
            # Zapisz wyczyszczony start_tokens.json
            with open(start_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Usunięto {removed_count} zakupionych zetonów z start_tokens.json")
        else:
            print("ℹ️ Brak zakupionych zetonów w start_tokens.json")
            
    except Exception as e:
        print(f"⚠️ Błąd czyszczenia start_tokens.json: {e}")


def clean_ai_logs():
    """Usuń logi AI z poprzedniej gry (ZACHOWUJE dane ML!)"""
    try:
        logs_dir = Path("logs")
        deleted_files = 0
        deleted_dirs = 0

        if not logs_dir.exists():
            print("ℹ️ Brak katalogu logs – pomijam logi AI")
            return

        # Rekurencyjne usuwanie plików ai_*.csv w całym drzewie logs
        # UWAGA: CHRONIMY dane ML!
        for f in logs_dir.rglob("ai_*.csv"):
            try:
                # OCHRONA: Pomiń pliki ML w analysis/ml_ready
                if 'analysis' in f.parts and 'ml_ready' in f.parts:
                    print(f"💾 Chronię dane ML: {f.relative_to(logs_dir)}")
                    continue
                
                f.unlink()
                deleted_files += 1
                print(f"✅ Usunięto: {f.relative_to(logs_dir)}")
            except Exception as e:
                print(f"⚠️ Nie mogę usunąć {f}: {e}")

        # Usuń katalogi z logami AI (całe drzewa) - ale NIE analysis!
        for ai_folder in ["ai_commander", "ai_general"]:
            ai_path = logs_dir / ai_folder
            if ai_path.exists() and ai_path.is_dir():
                try:
                    shutil.rmtree(ai_path)
                    deleted_dirs += 1
                    print(f"✅ Usunięto katalog: {ai_folder}")
                except Exception as e:
                    print(f"⚠️ Nie mogę usunąć katalogu {ai_path}: {e}")

        if deleted_files or deleted_dirs:
            print(f"✅ Usunięto logi AI: pliki={deleted_files}, katalogi={deleted_dirs}")
            print("💾 UWAGA: Dane ML zostały ZACHOWANE!")
        else:
            print("ℹ️ Brak logów AI do usunięcia (ai_*.csv i katalogi ai_*)")
            
    except Exception as e:
        print(f"⚠️ Błąd usuwania logów AI: {e}")


def clean_csv_logs():
    """Usuń wszystkie pliki CSV z folderu logs (ZACHOWUJE dane ML!)"""
    try:
        logs_dir = Path("logs")
        if not logs_dir.exists():
            print("ℹ️ Brak katalogu logs – pomijam czyszczenie CSV")
            return

        deleted_count = 0
        protected_count = 0
        total_size = 0
        
        # Wzorce plików CSV do usunięcia
        csv_patterns = [
            "actions_*.csv",
            "ai_actions_*.csv", 
            "ai_purchases_*.csv",
            "garrison_*.csv",
            "ai_*.csv",           # Wszystkie inne pliki AI CSV
            "*_problems_*.csv",   # Pliki problemów (garrison_problems itp.)
            "*_issues_*.csv"      # Pliki issues
        ]
        
        # Usuń pliki CSV z głównego katalogu
        for pattern in csv_patterns:
            for csv_file in logs_dir.glob(pattern):
                try:
                    size = csv_file.stat().st_size
                    csv_file.unlink()
                    deleted_count += 1
                    total_size += size
                except Exception as e:
                    print(f"⚠️ Nie mogę usunąć {csv_file.name}: {e}")
        
        # Usuń WSZYSTKIE pliki CSV rekurencyjnie z logs/ - ALE CHROŃ ML!
        processed_files = set()
        for csv_file in logs_dir.rglob("*.csv"):
            if csv_file not in processed_files:
                try:
                    # OCHRONA: Pomiń pliki ML i raporty
                    if 'analysis' in csv_file.parts:
                        if 'ml_ready' in csv_file.parts:
                            print(f"💾 Chronię dane ML: {csv_file.relative_to(logs_dir)}")
                            protected_count += 1
                            continue
                        elif 'raporty' in csv_file.parts or 'statystyki' in csv_file.parts:
                            print(f"💾 Chronię raporty: {csv_file.relative_to(logs_dir)}")
                            protected_count += 1
                            continue
                    
                    size = csv_file.stat().st_size
                    csv_file.unlink()
                    deleted_count += 1
                    total_size += size
                    processed_files.add(csv_file)
                    print(f"✅ Usunięto: {csv_file.relative_to(logs_dir)}")
                except Exception as e:
                    print(f"⚠️ Nie mogę usunąć {csv_file}: {e}")

        if deleted_count > 0 or protected_count > 0:
            print(f"✅ Usunięto {deleted_count} plików CSV ({total_size/1024:.1f} KB)")
            print(f"💾 Zachowano {protected_count} plików ML i raportów!")
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
    """Usuń rozmieszczone żetony (start_tokens.json + token fields) – bez ruszania katalogu assets/tokens."""
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
    """Pełne wyczyszczenie żetonów: tokens_soft + PURGE assets/tokens/*"""
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
