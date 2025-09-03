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
    print(f"🔧 [GROUPING START] Rozpoczynam adaptacyjne grupowanie {len(my_units)} jednostek")
    key_points_state = getattr(game_engine, 'key_points_state', {})
    total_value = sum(kp.get('current_value', 0) for kp in key_points_state.values()) or 1
    target_group_count = max(1, min(5, total_value // 50 + 1))
    print(f"📊 [GROUP CALC] Wartość celów: {total_value}, docelowa liczba grup: {target_group_count}")
    
    clusters = group_units_by_proximity(my_units, max_group_distance=4)
    print(f"🎯 [PROXIMITY] Utworzono {len(clusters)} klastrów na podstawie bliskości:")
    for i, cluster in enumerate(clusters):
        leader_pos = (cluster[0]['q'], cluster[0]['r']) if cluster else None
        print(f"   Klaster {i+1}: {len(cluster)} jednostek, lider na {leader_pos}")
    
    if len(clusters) <= target_group_count:
        print(f"✅ [GROUPING DONE] Używam {len(clusters)} klastrów jako grup docelowych")
        return clusters
    
    clusters.sort(key=lambda c: len(c), reverse=True)
    final_groups = clusters[:target_group_count]
    leftovers = clusters[target_group_count:]
    
    print(f"🔄 [MERGE] Scalanie {len(leftovers)} mniejszych klastrów...")
    for small_cluster in leftovers:
        target_group = min(final_groups, key=lambda g: len(g))
        target_group.extend(small_cluster)
        print(f"   Dołączono {len(small_cluster)} jednostek do grupy o {len(target_group)-len(small_cluster)} jednostkach")
    
    print(f"✅ [GROUPING FINAL] Powstało {len(final_groups)} grup po adaptacyjnym scaleniu:")
    for i, group in enumerate(final_groups):
        leader_pos = (group[0]['q'], group[0]['r']) if group else None
        print(f"   Grupa {i+1}: {len(group)} jednostek, lider na {leader_pos}")
    return final_groups


def assign_targets_with_coordination(groups, prioritized_targets, game_engine):
    print(f"🎯 [ASSIGNMENT START] Przypisywanie celów dla {len(groups)} grup do {len(prioritized_targets)} celów")
    board = getattr(game_engine, 'board', None)
    if not board:
        print("❌ [ASSIGNMENT ERROR] Brak dostępu do board, nie można przypisać celów")
        return []
    
    assignments = []
    reserved = set()
    
    for i, group in enumerate(groups):
        if not group:
            continue
        leader = group[0]
        leader_pos = (leader['q'], leader['r'])
        best_target = None
        best_score = -1
        print(f"🔍 [GROUP {i+1}] Grupa {len(group)} jednostek, lider na {leader_pos}, szuka celu...")
        
        for j, target in enumerate(prioritized_targets):
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
                print(f"   ⛔ Cel {j+1} {t_pos} już zarezerwowany")
                continue
            path = board.find_path(leader_pos, t_pos, max_mp=leader.get('mp',1), max_fuel=leader.get('fuel',1))
            if not path or len(path) < 2:
                print(f"   🚫 Cel {j+1} {t_pos} nieosiągalny")
                continue
            distance = len(path) - 1
            score = t_val / (distance + 1)
            print(f"   📏 Cel {j+1} {t_pos}: wartość {t_val}, dystans {distance}, score {score:.2f}")
            if score > best_score:
                best_score = score
                best_target = t_pos
        if best_target:
            reserved.add(f"{best_target[0]},{best_target[1]}")
            assignments.append({'group': group, 'target': best_target})
            print(f"✅ [ASSIGNMENT] Grupa {i+1} (lider {leader.get('id')}) -> cel {best_target} (score {best_score:.2f})")
        else:
            assignments.append({'group': group, 'target': None})
            print(f"❌ [NO TARGET] Grupa {i+1} (lider {leader.get('id')}) - brak dostępnego celu")
    
    print(f"🎯 [ASSIGNMENT SUMMARY] Przypisano {len([a for a in assignments if a['target']])} / {len(assignments)} grup do celów")
    
    # LOGOWANIE DIAGNOSTYCZNE DO CSV
    try:
        from ai.logowanie_ai import log_group_formation
        player_nation = getattr(getattr(game_engine, 'current_player_obj', None), 'nation', 'Unknown')
        
        for i, assignment in enumerate(assignments):
            if assignment.get('group') and assignment.get('target'):
                group = assignment['group']
                target = assignment['target']
                leader = group[0] if group else None
                if leader:
                    log_group_formation(
                        group_id=i+1,
                        group_size=len(group),
                        leader_pos=(leader['q'], leader['r']),
                        assignment_score=assignment.get('score', 0.0),
                        target_pos=target,
                        player_nation=player_nation,
                        extra={
                            'coordination_mode': 'advanced',
                            'target_is_free': assignment.get('target_is_free', False)
                        }
                    )
    except Exception as log_err:
        print(f"[LOG ERROR] Nie udało się zapisać group formation: {log_err}")
    
    return assignments


def dynamic_reassignment(group_assignments, game_engine):
    print(f"🔄 [REASSIGNMENT] Sprawdzanie {len(group_assignments)} przypisań grup pod kątem dynamicznej reasignacji")
    board = getattr(game_engine, 'board', None)
    key_points_state = getattr(game_engine, 'key_points_state', {})
    if not board:
        print("❌ [REASSIGNMENT ERROR] Brak dostępu do board")
        return group_assignments
    
    active_assignments = []
    reassigned_count = 0
    for assign in group_assignments:
        grp = assign.get('group')
        tgt = assign.get('target')
        if not grp:
            continue
        leader = grp[0]
        leader_id = leader.get('id', 'unknown')
        
        if tgt:
            print(f"✅ [KEEP TARGET] Grupa {leader_id} zachowuje cel {tgt}")
            active_assignments.append(assign)
            continue
        
        print(f"🔍 [SEARCH NEW] Grupa {leader_id} szuka nowego celu...")
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
        print(f"   📋 Znaleziono {len(available_kps)} dostępnych punktów kluczowych")
        
        leader_pos = (leader['q'], leader['r'])
        best_candidate = None
        best_score = -1
        
        for (kp_pos, val) in available_kps:
            path = board.find_path(leader_pos, kp_pos, max_mp=leader.get('mp',1), max_fuel=leader.get('fuel',1))
            if not path or len(path) < 2:
                continue
            distance = len(path) - 1
            score = val / (distance + 1)
            print(f"   🎯 Kandydat {kp_pos}: wartość {val}, dystans {distance}, score {score:.2f}")
            if score > best_score:
                best_candidate = kp_pos
                best_score = score
                
        if best_candidate:
            print(f"🔄 [REASSIGNED] Grupa {leader_id} -> nowy cel {best_candidate} (score {best_score:.2f})")
            active_assignments.append({'group': grp, 'target': best_candidate})
            reassigned_count += 1
        else:
            print(f"❌ [NO ALTERNATIVE] Grupa {leader_id} - brak dostępnych celów")
            active_assignments.append(assign)
    
    print(f"🔄 [REASSIGNMENT SUMMARY] Przypisano nowe cele dla {reassigned_count} grup")
    
    # LOGOWANIE DIAGNOSTYCZNE DO CSV
    try:
        from ai.logowanie_ai import log_strategic_decision
        player_nation = getattr(getattr(game_engine, 'current_player_obj', None), 'nation', 'Unknown')
        
        log_strategic_decision(
            strategic_state="REASSIGNMENT",
            aggression_level=0.5,  # domyślna wartość
            total_groups=len(group_assignments),
            reassignments=reassigned_count,
            player_nation=player_nation,
            extra={
                'tactical_mode': 'dynamic_reassignment',
                'coordination_mode': 'adaptive'
            }
        )
    except Exception as log_err:
        print(f"[LOG ERROR] Nie udało się zapisać reassignment decision: {log_err}")
    
    return active_assignments
