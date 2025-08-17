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
                # Formatuj datę - pełna data i czas
                try:
                    date_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_formatted = date_obj.strftime('%d.%m.%Y %H:%M:%S')
                    date_short = date_obj.strftime('%d.%m %H:%M')  # Skrócona wersja dla listy
                    
                    # Względny czas (np. "2 godziny temu")
                    now = datetime.datetime.now(date_obj.tzinfo)
                    diff = now - date_obj
                    if diff.days > 0:
                        relative_time = f"{diff.days} dni temu"
                    elif diff.seconds > 3600:
                        hours = diff.seconds // 3600
                        relative_time = f"{hours}h temu"
                    elif diff.seconds > 60:
                        minutes = diff.seconds // 60
                        relative_time = f"{minutes}min temu"
                    else:
                        relative_time = "przed chwilą"
                        
                except:
                    date_formatted = date_str[:19]
                    date_short = date_str[:16]
                    relative_time = ""
                
                # Generuj przyjazną nazwę
                friendly_name = generate_friendly_name(message, date_formatted)
                
                commits.append({
                    'hash': hash_short,
                    'date': date_formatted,
                    'date_short': date_short,
                    'relative_time': relative_time,
                    'author': author,
                    'message': message,
                    'friendly_name': friendly_name,
                    'full_line': line
                })
    return commits

def generate_friendly_name(message, date):
    """Generuje przyjazną nazwę dla commita"""
    # Słowa kluczowe do rozpoznawania typu commita
    if any(word in message.lower() for word in ['backup', 'porządkowanie', 'reorganizacja', 'czyszczenie']):
        return "🧹 Porządkowanie projektu"
    elif any(word in message.lower() for word in ['fix', 'naprawa', 'popraw']):
        return "🔧 Naprawy i poprawki"
    elif any(word in message.lower() for word in ['feat', 'dodanie', 'nowe', 'add']):
        return "✨ Nowe funkcje"
    elif any(word in message.lower() for word in ['ui', 'gui', 'panel', 'interfejs']):
        return "🎨 Zmiany interfejsu"
    elif any(word in message.lower() for word in ['engine', 'silnik', 'core']):
        return "⚙️ Zmiany silnika"
    elif any(word in message.lower() for word in ['test', 'debug']):
        return "🧪 Testy i debugowanie"
    elif any(word in message.lower() for word in ['doc', 'dokumentacja']):
        return "📝 Dokumentacja"
    elif any(word in message.lower() for word in ['merge', 'scalenie']):
        return "🔀 Scalenie gałęzi"
    else:
        # Użyj pierwszych słów komunikatu
        words = message.split()[:3]
        short_msg = ' '.join(words)
        if len(message) > 30:
            short_msg += "..."
        return f"📄 {short_msg}"

def display_commits(commits):
    """Wyświetla listę commitów do wyboru"""
    print("\n📋 OSTATNIE COMMITY:")
    print("=" * 100)
    for i, commit in enumerate(commits, 1):
        # Status aktualności
        if i == 1:
            status = "🟢 NAJNOWSZY"
        elif i == 2:
            status = "🟡 POPRZEDNI"
        else:
            status = f"🔵 #{i}"
            
        print(f"{i:2d}. {status} {commit['friendly_name']}")
        print(f"    📅 {commit['date']} ({commit['relative_time']}) | 👤 {commit['author']} | 🔗 {commit['hash']}")
        print(f"    📝 {commit['message']}")
        print()

def display_commit_aliases(commits):
    """Wyświetla aliasy commitów dla szybkiego wyboru"""
    print("🎯 SZYBKI WYBÓR:")
    print("-" * 50)
    
    # Znajdź specjalne commity
    backup_commits = [i for i, c in enumerate(commits, 1) if '🧹' in c['friendly_name']]
    fix_commits = [i for i, c in enumerate(commits, 1) if '🔧' in c['friendly_name']]
    feature_commits = [i for i, c in enumerate(commits, 1) if '✨' in c['friendly_name']]
    
    if backup_commits:
        backup_commit = commits[backup_commits[0]-1]
        print(f"  backup    → #{backup_commits[0]} ({backup_commit['date_short']}) ostatnie porządkowanie")
    if fix_commits:
        fix_commit = commits[fix_commits[0]-1]
        print(f"  fix       → #{fix_commits[0]} ({fix_commit['date_short']}) ostatnie poprawki")
    if feature_commits:
        feature_commit = commits[feature_commits[0]-1]
        print(f"  feature   → #{feature_commits[0]} ({feature_commit['date_short']}) ostatnie funkcje")
    
    print(f"  latest    → #1 ({commits[0]['date_short']}) najnowszy")
    if len(commits) >= 2:
        print(f"  previous  → #2 ({commits[1]['date_short']}) poprzedni")
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
    display_commit_aliases(commits)
    
    # Wybór użytkownika
    print("🎯 WYBÓR COMMITA:")
    print("=" * 40)
    try:
        choice = input(f"Wybierz numer (1-{len(commits)}), alias (backup/fix/feature/latest/previous) lub 'q': ").strip()
        
        if choice.lower() == 'q':
            print("👋 Anulowano")
            return 0
        
        # Obsługa aliasów
        choice_num = None
        if choice.lower() == 'latest':
            choice_num = 1
        elif choice.lower() == 'previous':
            choice_num = 2 if len(commits) >= 2 else 1
        elif choice.lower() == 'backup':
            backup_commits = [i for i, c in enumerate(commits, 1) if '🧹' in c['friendly_name']]
            choice_num = backup_commits[0] if backup_commits else None
        elif choice.lower() == 'fix':
            fix_commits = [i for i, c in enumerate(commits, 1) if '🔧' in c['friendly_name']]
            choice_num = fix_commits[0] if fix_commits else None
        elif choice.lower() == 'feature':
            feature_commits = [i for i, c in enumerate(commits, 1) if '✨' in c['friendly_name']]
            choice_num = feature_commits[0] if feature_commits else None
        else:
            choice_num = int(choice)
        
        if choice_num is None:
            print(f"❌ Nie znaleziono commita dla aliasu '{choice}'")
            return 1
            
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
    print(f"\n🎯 Wybrałeś: {selected_commit['friendly_name']}")
    print(f"    📅 {selected_commit['date']} ({selected_commit['relative_time']})")
    print(f"    👤 {selected_commit['author']} | 🔗 {selected_commit['hash']}")
    print(f"    📝 {selected_commit['message']}")
    
    # Potwierdzenie
    confirm = input("\n❓ Czy na pewno przywrócić ten commit? (y/N): ").strip().lower()
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
