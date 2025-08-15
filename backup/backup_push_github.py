#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimalny push do repo https://github.com/koradus4/turowka_z_ai (gałąź main).
Zakłada, że remote origin jest już ustawiony i masz uprawnienia.
"""
import subprocess, sys, datetime, os
from pathlib import Path

def run(cmd):
    r = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if r.returncode != 0:
        print(f"❌ {cmd}\n{r.stderr}")
        sys.exit(1)
    if r.stdout.strip():
        print(r.stdout.strip())

def main():
    repo_root = Path(__file__).parent.parent
    os.chdir(repo_root)
    # szybka weryfikacja
    if not (repo_root/'.git').exists():
        print('Brak repo .git w katalogu projektu. Przerwano.')
        return
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    msg = f"Auto backup {ts}"
    print("➡️ Dodaję zmiany...")
    run('git add -A')
    print("➡️ Tworzę commit...")
    subprocess.run(f'git commit -m "{msg}"', shell=True)  # commit może być pusty
    print("➡️ Push na origin main...")
    run('git push origin main')
    print("✅ Wysłano na GitHub turowka_z_ai:main")

if __name__ == '__main__':
    main()
