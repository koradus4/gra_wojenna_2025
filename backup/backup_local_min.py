#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimalny lokalny backup projektu.

Usprawnienia:
- Dynamiczny katalog docelowy (ENV BACKUP_LOCAL_DIR lub argument CLI, domyślnie: C:/Users/klif/gra_wojenna_backups)
- Każdy backup w osobnym folderze snapshot_YYYYMMDD_HHMMSS (brak nadpisywania)
- Liczenie plików, rozmiaru i pominięć.
- Wykluczenia: .git, __pycache__, .vscode, logs, *pyc/pyo/log/tmp.
- Pomija katalog docelowy jeśli leży wewnątrz projektu.
"""
import os, shutil, sys, time
from pathlib import Path
from datetime import datetime

EXCLUDE_DIRS = {'.git', '__pycache__', '.vscode', 'logs'}
EXCLUDE_SUFFIX = {'.pyc', '.pyo', '.log', '.tmp'}

def should_skip(path: Path, project_root: Path, target_root: Path) -> bool:
    name = path.name
    # Nigdy nie kopiuj katalogu docelowego (gdy znajduje się w obrębie repo)
    try:
        if target_root in path.resolve().parents:
            return True
    except Exception:
        pass
    if path.is_dir() and name in EXCLUDE_DIRS:
        return True
    if any(name.endswith(suf) for suf in EXCLUDE_SUFFIX):
        return True
    return False

def human_size(num: int) -> str:
    for unit in ['B','KB','MB','GB','TB']:
        if num < 1024:
            return f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}PB"

def parse_args():
    import argparse
    ap = argparse.ArgumentParser(description='Lokalny backup projektu')
    ap.add_argument('-o','--output', help='Katalog bazowy backup (domyślnie ENV BACKUP_LOCAL_DIR lub C:/Users/klif/gra_wojenna_backups)')
    return ap.parse_args()

def main():
    args = parse_args()
    project_root = Path(__file__).parent.parent.resolve()
    base_output = (
        Path(args.output).expanduser() if args.output else
        Path(os.environ.get('BACKUP_LOCAL_DIR', r'C:/Users/klif/gra_wojenna_backups'))
    )
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    target_root = base_output / f'snapshot_{timestamp}'
    target_root.mkdir(parents=True, exist_ok=True)
    print(f"➡️ Start backupu: {project_root} -> {target_root}")

    t0 = time.time()
    files_copied = 0
    files_skipped = 0
    errors = 0
    total_size = 0

    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        # Filtr katalogów in-place (nie schodź w wykluczone)
        dirs[:] = [d for d in dirs if not should_skip(root_path / d, project_root, target_root)]
        # Jeśli to katalog docelowy (gdy jest wewnątrz projektu) – omiń całkowicie
        if target_root == root_path:
            dirs[:] = []
            continue
        rel_root = root_path.relative_to(project_root)
        dest_dir = target_root / rel_root
        dest_dir.mkdir(parents=True, exist_ok=True)
        for fname in files:
            src = root_path / fname
            if should_skip(src, project_root, target_root):
                files_skipped += 1
                continue
            rel = src.relative_to(project_root)
            dest = target_root / rel
            try:
                shutil.copy2(src, dest)
                files_copied += 1
                try:
                    total_size += src.stat().st_size
                except OSError:
                    pass
                if files_copied % 200 == 0:
                    print(f"  • Skopiowano {files_copied} plików...")
            except Exception as e:
                errors += 1
                print(f"⚠️ Błąd kopiowania {rel}: {e}")

    dt = time.time() - t0
    summary = target_root / 'BACKUP_INFO.txt'
    with summary.open('w', encoding='utf-8') as f:
        f.write('BACKUP PROJEKTU\n')
        f.write('='*40+'\n')
        f.write(f'Źródło: {project_root}\n')
        f.write(f'Cel: {target_root}\n')
        f.write(f'Czas: {timestamp}\n')
        f.write(f'Plików skopiowanych: {files_copied}\n')
        f.write(f'Plików pominiętych: {files_skipped}\n')
        f.write(f'Błędów: {errors}\n')
        f.write(f'Łączny rozmiar: {human_size(total_size)}\n')
        f.write(f'Czas trwania: {dt:.2f}s\n')

    print("✅ Zakończono.")
    print(f"   Skopiowano: {files_copied}, pominięto: {files_skipped}, błędy: {errors}, rozmiar: {human_size(total_size)}, czas: {dt:.2f}s")
    print(f"   Informacje: {summary}")

if __name__ == '__main__':
    main()
