# -*- coding: utf-8 -*-
"""
Szybki raport diagnostyczny AI Commander:
- skłonność do ataku (z decision/combat + walka_ai)
- zachowanie garnizonów KP (próby vs blokady, powody)
- przerwane ruchy (kody błędów, powody)

Raport czyta najnowszą sesję z SessionManager i dzisiejsze pliki CSV.
Skrypt jest odporny na brak plików i brak kolumn (drukuje ostrzeżenia).
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path
import argparse
from collections import Counter, defaultdict
from datetime import datetime

# Zapewnij import modułów z katalogu projektu
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from utils.session_manager import SessionManager
except Exception:
    SessionManager = None  # type: ignore


def _find_header(name: str, headers: list[str]) -> str | None:
    # Pomocniczo: dopasuj dokładnie lub po obniżeniu i bez diakrytyki podstawowej
    candidates = [h for h in headers if h == name]
    if candidates:
        return candidates[0]
    low = name.lower()
    for h in headers:
        if h.lower() == low:
            return h
    return None


def _read_csv_rows(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def _resolve_session_dir(args: argparse.Namespace) -> Path | None:
    """
    Ustala katalog sesji na podstawie argumentów CLI bez wymuszania utworzenia nowej sesji.
    Priorytet:
      1) --session-dir (bezpośrednia ścieżka)
      2) --session-name (szukaj w logs/sesja_aktualna oraz logs/archiwum_sesji)
      3) --use-latest-existing (ostatnia istniejąca sesja w powyższych katalogach)
      4) fallback: SessionManager.get_current_session_dir()
    """
    base_logs = Path('logs')
    aktualna_root = base_logs / 'sesja_aktualna'
    arch_root = base_logs / 'archiwum_sesji'

    # 1) Bezpośrednia ścieżka
    if getattr(args, 'session_dir', None):
        p = Path(args.session_dir)
        return p if p.exists() else None

    # 2) Nazwa katalogu sesji
    if getattr(args, 'session_name', None):
        name = args.session_name
        cand1 = aktualna_root / name
        cand2 = arch_root / name
        if cand1.exists():
            return cand1
        if cand2.exists():
            return cand2
        return None

    # 3) Ostatnia istniejąca sesja
    if getattr(args, 'use_latest_existing', False):
        candidates: list[Path] = []
        if aktualna_root.exists():
            candidates += [p for p in aktualna_root.iterdir() if p.is_dir()]
        if arch_root.exists():
            candidates += [p for p in arch_root.iterdir() if p.is_dir()]
        if candidates:
            # sortuj po mtime malejąco
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return candidates[0]
        return None

    # 4) Fallback – użyj aktywnej sesji (może utworzyć nową)
    if SessionManager is not None:
        sm = SessionManager()
        return sm.get_current_session_dir()
    return None


def main() -> int:
    print("\n=== Raport diagnostyczny AI Commander ===")
    parser = argparse.ArgumentParser(description='Raport diagnostyczny AI Commander')
    parser.add_argument('--session-dir', type=str, help='Pełna ścieżka do katalogu sesji do analizy')
    parser.add_argument('--session-name', type=str, help='Nazwa katalogu sesji (np. 2025-09-18_21-48) w logs/sesja_aktualna lub logs/archiwum_sesji')
    parser.add_argument('--use-latest-existing', action='store_true', help='Użyj najnowszej istniejącej sesji bez tworzenia nowej')
    args = parser.parse_args()

    session_dir = _resolve_session_dir(args)
    if session_dir is None:
        print("⚠️ Nie udało się ustalić katalogu sesji. Podaj --session-dir lub --session-name, albo uruchom grę, aby utworzyć sesję.")
        return 1

    print(f"📁 [SESSION] Analizuję: {session_dir}")
    dzisiaj = datetime.now().strftime('%Y%m%d')

    taktyczne = session_dir / 'ai_commander_zaawansowany' / 'akcje_taktyczne' / f'akcje_taktyczne_{dzisiaj}.csv'
    walka = session_dir / 'ai_commander_zaawansowany' / 'walka_ai' / f'walka_ai_{dzisiaj}.csv'

    rows_t = _read_csv_rows(taktyczne)
    rows_w = _read_csv_rows(walka)

    if not rows_t and not rows_w:
        print("ℹ️ Brak dzisiejszych plików CSV (akcje_taktyczne, walka_ai) – uruchom scenariusz gry lub smoketesty.")
        return 0

    # Ustal nagłówki dynamicznie
    t_headers = list(rows_t[0].keys()) if rows_t else []
    w_headers = list(rows_w[0].keys()) if rows_w else []

    # Mapy nagłówków PL (z możliwością fallback na ang)
    H = {
        'action_type': _find_header('typ_akcji', t_headers) or _find_header('action_type', t_headers),
        'decision': _find_header('decyzja', t_headers) or _find_header('decision', t_headers),
        'reason': _find_header('powod', t_headers) or _find_header('reason', t_headers),
        'kod_bledu': _find_header('kod_bledu', t_headers) or _find_header('error_code', t_headers),
        'status': _find_header('status_walidacji', t_headers) or _find_header('validate_status', t_headers),
        'turn': _find_header('tura', t_headers) or _find_header('turn', t_headers),
        'correlation_id': _find_header('korelacja_id', t_headers) or _find_header('correlation_id', t_headers),
        'obstacle_hint': _find_header('podpowiedz_przeszkody', t_headers) or _find_header('obstacle_hint', t_headers),
        'nearest_dist': _find_header('najblizszy_osiagalny_dystans', t_headers) or _find_header('nearest_reachable_dist', t_headers),
    }

    HW = {
        'attacker': _find_header('atakujacy_id', w_headers) or _find_header('attacker_id', w_headers),
        'defender': _find_header('broniacy_id', w_headers) or _find_header('defender_id', w_headers),
        'outcome': _find_header('wynik_walki', w_headers) or _find_header('outcome', w_headers),
        'attacker_nation': _find_header('atakujaca_nacja', w_headers) or _find_header('attacker_nation', w_headers),
        'defender_nation': _find_header('broniaca_nacja', w_headers) or _find_header('defender_nation', w_headers),
    }

    # 1) Skłonność do ataku
    combat_decisions = [r for r in rows_t if H['action_type'] and r.get(H['action_type']) == 'combat_decision']
    attacks = [r for r in combat_decisions if H['decision'] and r.get(H['decision']) == 'attack']
    skipped = [r for r in combat_decisions if H['decision'] and r.get(H['decision']) != 'attack']
    print("\n-- Skłonność do ataku --")
    if combat_decisions:
        p = 100.0 * len(attacks) / max(1, len(combat_decisions))
        print(f"Decyzje bojowe: {len(combat_decisions)} | atak: {len(attacks)} ({p:.1f}%) | pominięte: {len(skipped)}")
    else:
        print("Brak wpisów combat_decision w akcje_taktyczne.")
    if rows_w:
        print(f"Wykonane walki (walka_ai): {len(rows_w)}")

    # 2) Garnizony KP
    vac_attempt = Counter()
    vac_blocked = Counter()
    reasons_attempt = Counter()
    reasons_blocked = Counter()
    for r in rows_t:
        at = r.get(H['action_type']) if H['action_type'] else None
        if at == 'kp_vacate_attempt':
            reasons_attempt[r.get(H['reason'], 'N/A')] += 1
            vac_attempt['total'] += 1
        elif at == 'kp_vacate_blocked':
            reasons_blocked[r.get(H['reason'], 'N/A')] += 1
            vac_blocked['total'] += 1
    print("\n-- Garnizony KP --")
    print(f"Próby zwolnienia: {vac_attempt.get('total',0)} | Zablokowane: {vac_blocked.get('total',0)}")
    if reasons_attempt:
        top_a = reasons_attempt.most_common(3)
        print("Top powody prób:", ", ".join([f"{k}={v}" for k,v in top_a]))
    if reasons_blocked:
        top_b = reasons_blocked.most_common(3)
        print("Top powody blokad:", ", ".join([f"{k}={v}" for k,v in top_b]))

    # 3) Przerwane ruchy
    aborted = [r for r in rows_t if H['action_type'] and r.get(H['action_type']) == 'move_aborted']
    by_code = Counter([r.get(H['kod_bledu'], 'N/A') for r in aborted]) if H['kod_bledu'] else Counter()
    by_status = Counter([r.get(H['status'], 'N/A') for r in aborted]) if H['status'] else Counter()
    print("\n-- Przerwane ruchy --")
    print(f"Łącznie: {len(aborted)}")
    if by_status:
        print("Statusy:", ", ".join([f"{k}={v}" for k,v in by_status.most_common()]))
    if by_code:
        print("Kody błędów:", ", ".join([f"{k}={v}" for k,v in by_code.most_common(5)]))

    # Per-turn breakdown (przerwane ruchy + ataki)
    if H['turn']:
        turns = sorted(set([r.get(H['turn']) for r in rows_t if r.get(H['turn'])]))
        print("\n-- Per-turn breakdown --")
        for t in turns:
            t_rows = [r for r in rows_t if r.get(H['turn']) == t]
            t_aborted = [r for r in t_rows if r.get(H['action_type']) == 'move_aborted']
            t_codes = Counter([r.get(H['kod_bledu'], 'N/A') for r in t_aborted]) if H['kod_bledu'] else Counter()
            t_combat = [r for r in t_rows if r.get(H['action_type']) == 'combat_decision']
            t_attacks = [r for r in t_combat if r.get(H['decision']) == 'attack'] if H['decision'] else []
            print(f"Tura {t}: move_aborted={len(t_aborted)}, NO_PATH={t_codes.get('NO_PATH',0)} NO_FUEL={t_codes.get('NO_FUEL',0)} NO_MP={t_codes.get('NO_MP',0)} | attacks={len(t_attacks)}")

    # Top NO_PATH offenders i obstacle hints
    if H['kod_bledu']:
        no_path_rows = [r for r in aborted if r.get(H['kod_bledu']) == 'NO_PATH']
        offenders = Counter([r.get('unit_id','?') for r in no_path_rows])
        hints = Counter([r.get(H['obstacle_hint'], 'N/A') for r in no_path_rows if H['obstacle_hint']])
        print("\nTop NO_PATH (unit_id):", ", ".join([f"{k}={v}" for k,v in offenders.most_common(5)]))
        if hints:
            print("Obstacle hints:", ", ".join([f"{k}={v}" for k,v in hints.most_common(5)]))

    # Korelacja łańcuchów: policz ile korelacji ma pełny łańcuch scan->precheck->decision
    if H['correlation_id'] and H['action_type']:
        chains = defaultdict(set)
        for r in rows_t:
            cid = r.get(H['correlation_id'])
            if not cid:
                continue
            chains[cid].add(r.get(H['action_type']))
        full = sum(1 for s in chains.values() if {'attack_opportunity_scan','combat_precheck','combat_decision'}.issubset(s))
        print(f"\nKorelacje z pełnym łańcuchem scan→precheck→decision: {full}")

    # Friendly-fire / cross-commander checks: ta sama nacja attacker vs defender
    if rows_w and HW['attacker_nation'] and HW['defender_nation']:
        same_nation = [r for r in rows_w if r.get(HW['attacker_nation']) and r.get(HW['attacker_nation']) == r.get(HW['defender_nation'])]
        if same_nation:
            print(f"\n⚠️ Wykryto walki tej samej nacji (cross-commander?): {len(same_nation)}")
        else:
            print("\nBrak walk tej samej nacji (OK)")

    print("\n=== Koniec raportu ===\n")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
