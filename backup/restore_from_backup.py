#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Przywracanie projektu z wybranego commita/backupa.

Funkcje:
- Pokazuje listę ostatnich commitów z opisami i datami
- Pozwala wybrać numer commita do przywrócenia
- Bezpiecznie przywraca wybrany stan (z opcją backup bieżącego stanu)
- Obsługuje różne gałęzie
- Waliduje czy nie ma niecommitowanych zmian

Przykłady:
    python backup/restore_from_backup.py                    # Lista 10 ostatnich commitów
    python backup/restore_from_backup.py --count 20         # Lista 20 ostatnich
    python backup/restore_from_backup.py --branch main      # Lista z gałęzi main
    python backup/restore_from_backup.py --no-backup        # Bez backup przed przywróceniem
"""
import subprocess, sys, datetime, os, argparse, shlex
from pathlib import Path

def sh(cmd: str, check=True, capture=True):
    return subprocess.run(cmd, shell=True, text=True,
                          capture_output=capture, check=False)

def run_or_die(cmd: str):
    r = sh(cmd)
    if r.returncode != 0:
        print(f"❌ {cmd}\n{r.stderr.strip()}")
        sys.exit(1)
    return (r.stdout or '').strip()

def parse_args():
    ap = argparse.ArgumentParser(description="Przywracanie projektu z wybranego commita")
    ap.add_argument('-c', '--count', type=int, default=10, 
                    help='Liczba ostatnich commitów do pokazania (default: 10)')
    ap.add_argument('-b', '--branch', help='Gałąź do sprawdzenia (domyślnie aktualna)')
    ap.add_argument('--no-backup', action='store_true', 
                    help='Nie rób backup bieżącego stanu przed przywróceniem')
    ap.add_argument('--force', action='store_true',
                    help='Wymuś przywrócenie nawet z niecommitowanymi zmianami')
    return ap.parse_args()

def check_working_tree_clean():
    """Sprawdza czy working tree jest czysty"""
    r = sh('git status --porcelain')
    if r.returncode != 0:
        return False, "Błąd sprawdzania statusu git"
    
    if r.stdout.strip():
        return False, "Masz niecommitowane zmiany"
    return True, "OK"

def get_current_branch():
    """Pobiera nazwę aktualnej gałęzi"""
    r = sh('git rev-parse --abbrev-ref HEAD')
    if r.returncode == 0:
        return (r.stdout or '').strip()
    return 'main'

def get_commit_list(branch=None, count=10):
    """Pobiera listę commitów z opisami i datami"""
    branch = branch or get_current_branch()
    cmd = f'git log {branch} --oneline --format="%h|%ci|%an|%s" -n {count}'
    r = sh(cmd)
    
    if r.returncode != 0:
        print(f"❌ Błąd pobierania commitów z gałęzi '{branch}': {r.stderr}")
        return []
    
    commits = []
    for line in (r.stdout or '').strip().split('\n'):
        if '|' in line:
            parts = line.split('|', 3)
            if len(parts) == 4:
                hash_short, date_str, author, message = parts
                # Formatuj datę
                try:
                    date_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_formatted = date_obj.strftime('%d.%m.%Y %H:%M')
                except:
                    date_formatted = date_str[:16]
                
                commits.append({
                    'hash': hash_short,
                    'date': date_formatted,
                    'author': author,
                    'message': message,
                    'full_line': line
                })
    return commits

def display_commits(commits):
    """Wyświetla listę commitów do wyboru"""
    print("\n📋 OSTATNIE COMMITY:")
    print("=" * 80)
    for i, commit in enumerate(commits, 1):
        print(f"{i:2d}. [{commit['hash']}] {commit['date']} - {commit['author']}")
        print(f"    📝 {commit['message']}")
        print()

def create_backup_branch():
    """Tworzy backup branch z aktualnym stanem"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_branch = f"backup_before_restore_{timestamp}"
    
    current_branch = get_current_branch()
    run_or_die(f'git checkout -b {backup_branch}')
    print(f"✅ Utworzono backup branch: {backup_branch}")
    
    # Wróć na oryginalną gałąź
    run_or_die(f'git checkout {current_branch}')
    return backup_branch

def restore_to_commit(commit_hash, create_backup=True):
    """Przywraca projekt do wybranego commita"""
    if create_backup:
        backup_branch = create_backup_branch()
        print(f"💾 Backup utworzony: {backup_branch}")
    
    print(f"🔄 Przywracam do commita: {commit_hash}")
    
    # Hard reset do wybranego commita
    run_or_die(f'git reset --hard {commit_hash}')
    
    print("✅ Przywrócenie zakończone!")
    print(f"📍 Aktualny commit: {commit_hash}")
    
    if create_backup:
        print(f"💡 Aby wrócić do poprzedniego stanu: git checkout {backup_branch}")

def main():
    args = parse_args()
    
    # Sprawdź czy jesteśmy w repo git
    repo_root = Path(__file__).parent.parent.resolve()
    os.chdir(repo_root)
    if not (repo_root / '.git').exists():
        print('❌ Brak repo .git – przerwano.')
        return 1
    
    # Sprawdź czystość working tree
    clean, message = check_working_tree_clean()
    if not clean and not args.force:
        print(f"❌ {message}")
        print("💡 Użyj --force aby wymusić lub commituj zmiany przed przywróceniem")
        return 1
    elif not clean:
        print(f"⚠️ {message} - kontynuuję z --force")
    
    # Pobierz listę commitów
    commits = get_commit_list(args.branch, args.count)
    if not commits:
        print("❌ Nie znaleziono commitów")
        return 1
    
    # Wyświetl commity
    display_commits(commits)
    
    # Wybór użytkownika
    print("🎯 WYBÓR COMMITA:")
    print("=" * 40)
    try:
        choice = input(f"Wybierz numer commita (1-{len(commits)}) lub 'q' aby wyjść: ").strip()
        
        if choice.lower() == 'q':
            print("👋 Anulowano")
            return 0
        
        choice_num = int(choice)
        if choice_num < 1 or choice_num > len(commits):
            print("❌ Nieprawidłowy numer")
            return 1
            
    except ValueError:
        print("❌ Nieprawidłowy wybór")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Anulowano przez użytkownika")
        return 0
    
    # Wybany commit
    selected_commit = commits[choice_num - 1]
    print(f"\n🎯 Wybrałeś: [{selected_commit['hash']}] {selected_commit['message']}")
    
    # Potwierdzenie
    confirm = input("❓ Czy na pewno przywrócić ten commit? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes', 'tak', 't']:
        print("👋 Anulowano")
        return 0
    
    # Przywrócenie
    try:
        restore_to_commit(selected_commit['hash'], not args.no_backup)
        print("\n🎉 Projekt został pomyślnie przywrócony!")
        
    except Exception as e:
        print(f"❌ Błąd podczas przywracania: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
