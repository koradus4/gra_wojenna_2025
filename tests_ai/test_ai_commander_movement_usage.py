#!/usr/bin/env python3
"""
TEST: Weryfikacja czy AI Commander REALNIE używa trybów ruchu (combat/march/recon)

Dowody:
 - Bez przeciwników i daleki cel -> oczekiwany 'march'
 - Wróg blisko (<=3) -> oczekiwany 'recon'
 - Wróg średnio daleko (4-6) -> oczekiwany 'combat'
 - move_towards faktycznie zmienia movement_mode żetonu i wywołuje apply_movement_mode

Test używa lekkich stubów Board i GameEngine aby uniknąć ciężkiego ładowania całej gry.
Generuje jasne wydruki dowodowe oraz asercje.
"""

import os
import sys
from types import SimpleNamespace

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from ai.ai_commander import choose_movement_mode, move_towards  # type: ignore
from engine.token import Token  # type: ignore


class DummyBoard:
    def __init__(self):
        self.occupied = set()

    def hex_distance(self, a, b):
        (q1, r1), (q2, r2) = a, b
        dq = q2 - q1
        dr = r2 - r1
        ds = (q2 + r2) - (q1 + r1)
        return max(abs(dq), abs(dr), abs(ds))

    def find_path(self, start, goal, max_mp=999, max_fuel=999, **kwargs):
        # Prosta ścieżka liniowa (nieoptymalny ale deterministyczny stub)
        path = [start]
        cq, cr = start
        gq, gr = goal
        steps = 0
        while (cq, cr) != (gq, gr) and steps < 50 and len(path) <= max_mp:
            if cq < gq:
                cq += 1
            elif cq > gq:
                cq -= 1
            if cr < gr:
                cr += 1
            elif cr > gr:
                cr -= 1
            path.append((cq, cr))
            steps += 1
        return path if path[-1] == goal else path

    def is_occupied(self, q, r):
        return (q, r) in self.occupied

    def neighbors(self, q, r):
        dirs = [(1,0),(0,1),(-1,1),(-1,0),(0,-1),(1,-1)]
        return [(q+dq, r+dr) for dq, dr in dirs]


class DummyResult:
    def __init__(self, success=True, message="OK"):
        self.success = success
        self.message = message


def build_game_env(player_id=1, nation="Polska"):
    board = DummyBoard()
    player = SimpleNamespace(id=player_id, nation=nation, visible_tokens=set())
    engine = SimpleNamespace(
        board=board,
        tokens=[],
        current_player_obj=player,
        key_points_state={},
        execute_action=lambda action, player=None: DummyResult(True, f"Action {getattr(action,'__class__',type(action)).__name__} ok"),
        turn_number=1
    )
    return engine, player, board


def make_token(id_, owner, q, r, move=10, combat=5, defense=4, maintenance=30):
    stats = {"move": move, "combat_value": combat, "defense_value": defense, "maintenance": maintenance}
    t = Token(id=id_, owner=owner, stats=stats, q=q, r=r, movement_mode='combat')
    t.apply_movement_mode(reset_mp=True)
    return t


def evidence_line(label, value):
    print(f"[EVIDENCE] {label}: {value}")


def test_mode_selection():
    engine, player, board = build_game_env()
    my_token = make_token("T1", "1 (Polska)", 0, 0, move=10)
    engine.tokens.append(my_token)
    unit_dict = {"id": my_token.id, "q": my_token.q, "r": my_token.r, "token": my_token, "mp": my_token.maxMovePoints, "fuel": my_token.currentFuel}

    # CASE 1: Daleki cel brak wrogów -> march
    far_target = (20, 0)
    mode_far = choose_movement_mode(unit_dict, far_target, engine)
    evidence_line("CASE1 target distance", board.hex_distance((my_token.q,my_token.r), far_target))
    evidence_line("CASE1 chosen_mode", mode_far)
    assert mode_far == 'march', "Oczekiwano 'march' dla dalekiego celu bez wrogów"

    # CASE 2: Wróg blisko (distance <=3) -> recon
    enemy_close = make_token("E1", "2 (Niemcy)", 1, 1, move=8)
    player.visible_tokens = {enemy_close}  # Wróg jest widoczny
    close_target = (2,2)
    mode_close = choose_movement_mode(unit_dict, close_target, engine)
    evidence_line("CASE2 enemy distance", board.hex_distance((my_token.q,my_token.r), (enemy_close.q, enemy_close.r)))
    evidence_line("CASE2 chosen_mode", mode_close)
    assert mode_close == 'recon', "Oczekiwano 'recon' przy bliskim wrogu"

    # CASE 3: Wróg średni dystans (4-6) -> combat
    enemy_mid = make_token("E2", "2 (Niemcy)", 5, 0, move=8)
    player.visible_tokens = {enemy_mid}
    mid_target = (6,0)
    mode_mid = choose_movement_mode(unit_dict, mid_target, engine)
    evidence_line("CASE3 enemy distance", board.hex_distance((my_token.q,my_token.r), (enemy_mid.q, enemy_mid.r)))
    evidence_line("CASE3 chosen_mode", mode_mid)
    assert mode_mid == 'combat', "Oczekiwano 'combat' przy średnim dystansie do wroga"

    print("[RESULT] test_mode_selection PASSED")


def test_move_towards_integration():
    engine, player, board = build_game_env()
    token = make_token("T_MAIN", "1 (Polska)", 0, 0, move=10)
    engine.tokens.append(token)
    player.visible_tokens = set()  # brak wrogów
    unit_dict = {"id": token.id, "q": token.q, "r": token.r, "token": token, "mp": token.maxMovePoints, "fuel": token.currentFuel}
    far_target = (18, 0)

    before_mode = token.movement_mode
    evidence_line("INTEGRATION before_mode", before_mode)
    moved = move_towards(unit_dict, far_target, engine)
    after_mode = token.movement_mode
    evidence_line("INTEGRATION after_mode", after_mode)
    evidence_line("INTEGRATION moved_result", moved)
    assert after_mode == 'march', "move_towards powinien ustawić tryb 'march' przy dalekim celu"
    assert moved is True or moved is False  # samo wywołanie nie crashuje
    print("[RESULT] test_move_towards_integration PASSED")


def run_all():
    print("===== START MOVEMENT MODE USAGE TESTS =====")
    test_mode_selection()
    test_move_towards_integration()
    print("===== ALL TESTS PASSED (movement modes in use) =====")


if __name__ == "__main__":
    run_all()
