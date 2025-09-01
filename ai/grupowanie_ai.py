"""Moduł grupowania i koordynacji (wydzielony z ai_commander).
Przeniesione implementacje: group_units_by_proximity, adaptive_grouping, assign_targets_with_coordination, dynamic_reassignment.
Uwaga: Funkcje przyjmują uproszczone argumenty aby pozostać kompatybilne z bieżącym wywołaniem w ai_commander.
"""
from __future__ import annotations
from typing import Any, List, Dict

__all__ = [
    'adaptive_grouping','assign_targets_with_coordination','dynamic_reassignment',
    'group_units_by_proximity'
]

def group_units_by_proximity(units, max_group_distance=8):
    if not units:
        return []
    clusters = []
    visited = set()
    for unit in units:
        uid = unit.get('id')
        if uid in visited:
            continue
        cluster = [unit]
        visited.add(uid)
        ux, uy = unit['q'], unit['r']
        for other in units:
            oid = other.get('id')
            if oid in visited:
                continue
            ox, oy = other['q'], other['r']
            dist = abs(ux-ox) + abs(uy-oy)
            if dist <= max_group_distance:
                cluster.append(other)
                visited.add(oid)
        clusters.append(cluster)
    return clusters


def adaptive_grouping(my_units, game_engine):
    key_points_state = getattr(game_engine, 'key_points_state', {})
    total_value = sum(kp.get('current_value', 0) for kp in key_points_state.values()) or 1
    target_group_count = max(1, min(5, total_value // 50 + 1))
    clusters = group_units_by_proximity(my_units, max_group_distance=4)
    if len(clusters) <= target_group_count:
        print(f"[GRUPOWANIE] Używam {len(clusters)} klastrów jako grup docelowych")
        return clusters
    clusters.sort(key=lambda c: len(c), reverse=True)
    final_groups = clusters[:target_group_count]
    leftovers = clusters[target_group_count:]
    for small_cluster in leftovers:
        target_group = min(final_groups, key=lambda g: len(g))
        target_group.extend(small_cluster)
    print(f"[GRUPOWANIE] Powstało {len(final_groups)} grup po adaptacyjnym scaleniu")
    return final_groups


def assign_targets_with_coordination(groups, prioritized_targets, game_engine):
    board = getattr(game_engine, 'board', None)
    if not board:
        return []
    assignments = []
    reserved = set()
    for group in groups:
        if not group:
            continue
        leader = group[0]
        leader_pos = (leader['q'], leader['r'])
        best_target = None
        best_score = -1
        for target in prioritized_targets:
            if isinstance(target, dict):
                t_pos = target.get('position') or target.get('pos') or target.get('target')
                t_val = target.get('value', target.get('current_value', 0))
            else:
                t_pos = target
                t_val = 1
            if not t_pos:
                continue
            t_key = f"{t_pos[0]},{t_pos[1]}"
            if t_key in reserved:
                continue
            path = board.find_path(leader_pos, t_pos, max_mp=leader.get('mp',1), max_fuel=leader.get('fuel',1))
            if not path or len(path) < 2:
                continue
            distance = len(path) - 1
            score = t_val / (distance + 1)
            if score > best_score:
                best_score = score
                best_target = t_pos
        if best_target:
            reserved.add(f"{best_target[0]},{best_target[1]}")
            assignments.append({'group': group, 'target': best_target})
            print(f"[KOORDYNACJA] Grupa lider {leader.get('id')} -> cel {best_target} (score {best_score:.2f})")
        else:
            assignments.append({'group': group, 'target': None})
            print(f"[KOORDYNACJA] Grupa lider {leader.get('id')} brak celu")
    return assignments


def dynamic_reassignment(group_assignments, game_engine):
    board = getattr(game_engine, 'board', None)
    key_points_state = getattr(game_engine, 'key_points_state', {})
    if not board:
        return group_assignments
    active_assignments = []
    for assign in group_assignments:
        grp = assign.get('group')
        tgt = assign.get('target')
        if not grp:
            continue
        leader = grp[0]
        if tgt:
            active_assignments.append(assign)
            continue
        available_kps = []
        for hex_id, kp in key_points_state.items():
            if kp.get('current_value', 0) <= 0:
                continue
            try:
                if ',' in hex_id:
                    q, r = map(int, hex_id.split(','))
                else:
                    q, r = map(int, hex_id.split('_'))
                available_kps.append(((q, r), kp.get('current_value', 0)))
            except (ValueError, IndexError):
                continue
        available_kps.sort(key=lambda x: x[1], reverse=True)
        leader_pos = (leader['q'], leader['r'])
        best_candidate = None
        best_score = -1
        for (kp_pos, val) in available_kps:
            path = board.find_path(leader_pos, kp_pos, max_mp=leader.get('mp',1), max_fuel=leader.get('fuel',1))
            if not path or len(path) < 2:
                continue
            distance = len(path) - 1
            score = val / (distance + 1)
            if score > best_score:
                best_candidate = kp_pos
                best_score = score
        if best_candidate:
            print(f"[REASIGN] Grupa {leader.get('id')} -> nowy cel {best_candidate} (score {best_score:.2f})")
            active_assignments.append({'group': grp, 'target': best_candidate})
        else:
            active_assignments.append(assign)
    return active_assignments
