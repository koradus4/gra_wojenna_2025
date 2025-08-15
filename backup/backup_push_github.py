#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimalny push backup do repo użytkownika.

Usprawnienia:
- Wykrywa aktualną gałąź (lub pozwala wymusić --branch/-b)
- Pomija push jeśli brak zmian (czysty working tree i ostatni commit <=60s temu)
- Waliduje czy remote 'origin' wskazuje na docelowe repo (opcjonalny ENV EXPECT_REMOTE_SUBSTR)
- Czytelny log.

Przykłady:
  python backup/backup_push_github.py                # auto branch
  python backup/backup_push_github.py -m "Fix ruch"  # własny komunikat
  python backup/backup_push_github.py -b main         # wymuszenie gałęzi
"""
import subprocess, sys, datetime, os, time, argparse, shlex
from pathlib import Path

def sh(cmd: str, check=True, capture=True):
    return subprocess.run(cmd, shell=True, text=True,
                          capture_output=capture, check=False)

def run_or_die(cmd: str):
    r = sh(cmd)
    if r.returncode != 0:
        print(f"❌ {cmd}\n{r.stderr.strip()}")
        sys.exit(1)
    out = (r.stdout or '').strip()
    if out:
        print(out)
    return out

def detect_branch():
    r = sh('git rev-parse --abbrev-ref HEAD')
    if r.returncode == 0:
        b = (r.stdout or '').strip()
        if b:
            return b
    return 'main'

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('-b','--branch', help='Gałąź do push (domyślnie aktualna)')
    ap.add_argument('-m','--message', help='Własny komunikat commita')
    ap.add_argument('--force', action='store_true', help='Wymuś push (git push --force-with-lease)')
    return ap.parse_args()

def working_tree_dirty():
    r = sh('git status --porcelain')
    if r.returncode != 0:
        return True
    return bool(r.stdout.strip())

def last_commit_age_seconds():
    r = sh('git log -1 --format=%ct')
    if r.returncode != 0 or not r.stdout.strip():
        return 9999
    try:
        ts = int(r.stdout.strip())
        return time.time() - ts
    except ValueError:
        return 9999

def main():
    args = parse_args()
    repo_root = Path(__file__).parent.parent.resolve()
    os.chdir(repo_root)
    if not (repo_root / '.git').exists():
        print('❌ Brak repo .git – przerwano.')
        return 1

    expected = os.environ.get('EXPECT_REMOTE_SUBSTR')  # np. 'gra_wojenna_2025'
    remotes = sh('git remote -v')
    if expected and expected not in (remotes.stdout or ''):
        print(f"⚠️ Ostrzeżenie: remote nie zawiera ciągu '{expected}'")

    branch = args.branch or detect_branch()
    dirty = working_tree_dirty()
    age = last_commit_age_seconds()
    auto_msg = f"Auto backup {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    commit_msg = args.message or auto_msg

    if not dirty and age < 60:
        print(f"ℹ️ Brak zmian i ostatni commit {age:.0f}s temu – pomijam push.")
        return 0

    print(f"➡️ Gałąź: {branch}")
    if dirty:
        print("➡️ Dodaję zmiany...")
        run_or_die('git add -A')
        print(f"➡️ Tworzę commit: {commit_msg}")
        sh(f'git commit -m {shlex.quote(commit_msg)}')  # commit może być pusty jeśli w międzyczasie brak zmian
    else:
        print("ℹ️ Czysto – używam istniejącego commita do push.")

    cmd_push = f'git push origin {branch}' + (' --force-with-lease' if args.force else '')
    print(f"➡️ Push: {cmd_push}")
    run_or_die(cmd_push)
    print("✅ Backup push zakończony")
    return 0

if __name__ == '__main__':
    sys.exit(main())
