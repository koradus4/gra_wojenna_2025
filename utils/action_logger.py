import csv
import os
from datetime import datetime

_log_file_path = None
_initialized = False


def _ensure_init():
    global _initialized, _log_file_path
    if _initialized:
        return
    
    # AKTUALIZACJA v4.0: Używa SessionManager dla jednej sesji na proces
    try:
        from utils.session_manager import SessionManager
        session_dir = SessionManager.get_current_session_dir()
        logs_dir = str(session_dir)  # SessionManager zwraca Path
        print(f"📝 [ACTION_LOGGER] Używa SessionManager: {logs_dir}")
    except ImportError:
        # FALLBACK: Stary system z current_session (kompatybilność)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        logs_dir = os.path.join(os.getcwd(), 'logs', 'current_session', timestamp)
        print(f"⚠️ [ACTION_LOGGER] Fallback na stary system: {logs_dir}")
    
    os.makedirs(logs_dir, exist_ok=True)
    
    _log_file_path = os.path.join(logs_dir, f'actions_main.csv')
    with open(_log_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([
            'timestamp', 'turn',
            'player_id', 'player_nation', 'player_role',
            'action',
            'token_id', 'target_token_id',
            'from_q', 'from_r', 'to_q', 'to_r',
            'result',
            'vp_pl', 'vp_de',
            'pe_pl', 'pe_de'
        ])
    _initialized = True


def _sum_by_nation(players, attr_name='victory_points'):
    pl = 0
    de = 0
    for p in players or []:
        val = getattr(p, attr_name, 0) or 0
        if str(getattr(p, 'nation', '')).lower().startswith('pol'):
            pl += val
        elif str(getattr(p, 'nation', '')).lower().startswith('niem'):
            de += val
    return pl, de


def _sum_economy_points(players):
    pl = 0
    de = 0
    for p in players or []:
        pts = 0
        if hasattr(p, 'economy') and p.economy is not None:
            try:
                pts = int(p.economy.get_points().get('economic_points', 0))
            except Exception:
                pts = int(getattr(p.economy, 'economic_points', 0) or 0)
        else:
            pts = int(getattr(p, 'punkty_ekonomiczne', 0) or 0)
        if str(getattr(p, 'nation', '')).lower().startswith('pol'):
            pl += pts
        elif str(getattr(p, 'nation', '')).lower().startswith('niem'):
            de += pts
    return pl, de


def _resolve_player_info(player_or_owner, players):
    """Return (id, nation, role) for a Player or owner string like '2 (Polska)'."""
    pid = None
    nation = None
    role = None
    if player_or_owner is None and players:
        return None, None, None
    # Player instance
    if hasattr(player_or_owner, 'id') and hasattr(player_or_owner, 'nation'):
        pid = getattr(player_or_owner, 'id', None)
        nation = getattr(player_or_owner, 'nation', None)
        role = getattr(player_or_owner, 'role', None)
        return pid, nation, role
    # Owner string like "2 (Polska)"
    owner_str = str(player_or_owner or '').strip()
    if owner_str:
        try:
            owner_id = owner_str.split('(')[0].strip()
            owner_id_int = int(owner_id)
        except Exception:
            owner_id_int = None
        if players and owner_id_int is not None:
            for p in players:
                if getattr(p, 'id', None) == owner_id_int:
                    return p.id, p.nation, p.role
    return pid, nation, role


def log_action(game_engine, player_or_owner, turn_number, action, details=None, result_msg=None):
    """
    Log one action into CSV.
    - game_engine: to read players and VP/PE.
    - player_or_owner: Player instance or owner string like '2 (Polska)'.
    - turn_number: int or None.
    - action: 'move' | 'attack' | 'deploy' | 'reaction_attack' | 'resupply' | 'other'.
    - details: dict with optional keys: token_id, target_token_id, from_q, from_r, to_q, to_r, cost, path, extras.
    - result_msg: optional text summary.
    """
    try:
        _ensure_init()
        players = getattr(game_engine, 'players', [])
        pid, nation, role = _resolve_player_info(player_or_owner, players)
        vp_pl, vp_de = _sum_by_nation(players, 'victory_points')
        pe_pl, pe_de = _sum_economy_points(players)
        d = details or {}
        row = [
            datetime.now().isoformat(timespec='seconds'),
            turn_number,
            pid, nation, role,
            action,
            d.get('token_id'), d.get('target_token_id'),
            d.get('from_q'), d.get('from_r'), d.get('to_q'), d.get('to_r'),
            result_msg if result_msg is not None else d.get('result'),
            vp_pl, vp_de,
            pe_pl, pe_de
        ]
        with open(_log_file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(row)
    except Exception as e:
        # Fail-safe: don't break the game on logging issues
        try:
            print(f"[ActionLogger] Error: {e}")
        except Exception:
            pass
