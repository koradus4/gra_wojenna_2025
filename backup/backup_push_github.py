#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimalny push backup do repo użytkownika + tryb automatycznego monitorowania.

Funkcje podstawowe:
- Wykrywa aktualną gałąź (lub pozwala wymusić --branch/-b)
- Pomija push jeśli brak zmian (czysty working tree i ostatni commit <=60s temu)
- Waliduje czy remote 'origin' wskazuje na docelowe repo (opcjonalny ENV EXPECT_REMOTE_SUBSTR)
- Czytelny log

NOWE (watch mode):
- Parametr --watch uruchamia pętlę cyklicznie sprawdzającą repo
- Parametr --interval (sekundy) odstęp między próbami (domyślnie 120)
- Parametr --min-gap minimalny odstęp czasowy między kolejnymi pushami (domyślnie 60)
- Debounce: jeżeli wykryto zmiany, ale proces edycji trwa (wykrywane kolejnymi różnymi hashami statusu) – czeka aż status się ustabilizuje przez jeden cykl
- Automatyczny inkrementalny commit message jeśli brak -m (Auto backup + timestamp)
- Retry push (3 próby) przy chwilowych błędach sieci (--retry / --retry-delay)

Przykłady:
    python backup/backup_push_github.py                      # jednorazowy push
    python backup/backup_push_github.py -m "Fix ruch"        # własny komunikat
    python backup/backup_push_github.py -b main              # wymuszenie gałęzi
    python backup/backup_push_github.py --watch              # ciągłe monitorowanie
    python backup/backup_push_github.py --watch --interval 30 --min-gap 90
"""
import subprocess, sys, datetime, os, time, argparse, shlex, hashlib, traceback
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
    ap.add_argument('--watch', action='store_true', help='Tryb ciągłego monitorowania i automatycznych pushy')
    ap.add_argument('--interval', type=int, default=120, help='Odstęp (s) między sprawdzeniami w trybie watch (default: 120)')
    ap.add_argument('--min-gap', type=int, default=60, help='Minimalny odstęp (s) między kolejnymi pushami (default: 60)')
    ap.add_argument('--retry', type=int, default=3, help='Liczba prób push przy błędach sieci (default: 3)')
    ap.add_argument('--retry-delay', type=int, default=5, help='Odstęp (s) między retry push (default: 5)')
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

def do_single_push(args, min_age_override=None):
    """Wykonuje pojedynczy cykl commit + push jeśli są zmiany lub ostatni commit stary.

    Zwraca:
      (pushed: bool, reason: str)
    """
    branch = args.branch or detect_branch()
    dirty = working_tree_dirty()
    age = last_commit_age_seconds()
    min_gap = args.min_gap if min_age_override is None else min_age_override
    if not dirty and age < min_gap:
        return False, f"Brak zmian i ostatni commit {age:.0f}s temu (<{min_gap}s)"

    auto_msg = f"Auto backup {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    commit_msg = args.message or auto_msg
    print(f"➡️ Gałąź: {branch}")
    if dirty:
        print("➡️ Dodaję zmiany (git add -A)...")
        run_or_die('git add -A')
        print(f"➡️ Tworzę commit: {commit_msg}")
        sh(f'git commit -m {shlex.quote(commit_msg)}')  # commit może być pusty jeśli ktoś w międzyczasie dodał commit
    else:
        print("ℹ️ Czysto – używam istniejącego commita do push (tylko push).")

    cmd_push = f'git push origin {branch}' + (' --force-with-lease' if args.force else '')
    print(f"➡️ Push: {cmd_push}")
    # Retry mechanizm
    for attempt in range(1, args.retry + 1):
        r = sh(cmd_push)
        if r.returncode == 0:
            print("✅ Push OK")
            return True, 'pushed'
        print(f"⚠️ Push nieudany (próba {attempt}/{args.retry}): {r.stderr.strip().splitlines()[-1] if r.stderr else 'brak stderr'}")
        if attempt < args.retry:
            time.sleep(args.retry_delay)
    print("❌ Nie udało się wypchnąć po wszystkich próbach")
    return False, 'push_failed'


def compute_status_hash():
    r = sh('git status --porcelain')
    return hashlib.sha256((r.stdout or '').encode('utf-8')).hexdigest()


def watch_loop(args):
    print(f"👀 Watch mode start (interval={args.interval}s, min-gap={args.min_gap}s). Ctrl+C aby zakończyć.")
    last_status_hash = compute_status_hash()
    last_push_time = time.time() - args.min_gap  # pozwala na push od razu jeśli zmiany są
    stable_cycles = 0
    try:
        while True:
            start = time.time()
            current_hash = compute_status_hash()
            dirty = working_tree_dirty()
            age = last_commit_age_seconds()
            if current_hash != last_status_hash:
                stable_cycles = 0
                print("📝 Wykryto zmiany – oczekiwanie na ustabilizowanie...")
                last_status_hash = current_hash
            else:
                if dirty:
                    stable_cycles += 1
                else:
                    stable_cycles = 0

            ready_time = (time.time() - last_push_time) >= args.min_gap
            if dirty and stable_cycles >= 1 and ready_time:
                print("🚀 Zmiany ustabilizowane – próbuję push...")
                pushed, reason = do_single_push(args)
                if pushed:
                    last_push_time = time.time()
                    last_status_hash = compute_status_hash()  # odśwież
                    stable_cycles = 0
                else:
                    print(f"⚠️ Push nie wykonany: {reason}")
            elif not dirty and ready_time and age >= args.min_gap:
                # Opcjonalnie: można wymusić push (np. jeżeli remote był odrzucony wcześniej)
                pass

            elapsed = time.time() - start
            sleep_for = max(1, args.interval - elapsed)
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        print("👋 Watch mode przerwany przez użytkownika.")
    except Exception as e:
        print("❌ Błąd w watch loop:", e)
        traceback.print_exc()
        return 1
    return 0


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

    if args.watch:
        return watch_loop(args)
    else:
        # Pojedyncze wywołanie: zawsze wykonaj push (nawet jeśli poprzedni commit był przed chwilą)
        pushed, reason = do_single_push(args, min_age_override=0)
        if pushed:
            print("✅ Backup push zakończony (tryb jednorazowy)")
        else:
            print(f"ℹ️ Nic do zrobienia: {reason}")
        return 0

if __name__ == '__main__':
    sys.exit(main())
