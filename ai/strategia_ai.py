"""Moduł strategii AI - wyodrębniony z AdaptiveAICommander.

Zawiera:
 - analyze_strategic_state
 - _adapt_strategy_to_state
 - prioritize_keypoints
 - _determine_purchase_priority
 - _get_available_purchase_options
 - _select_optimal_purchases

Cel: odchudzenie pliku ai_commander.py oraz separacja odpowiedzialności.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


# Lokalna implementacja dystansu axial (unikamy importu z ai_commander by nie tworzyć pętli)
def _hex_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return (abs(a[0]-b[0]) + abs(a[0]+a[1]-b[0]-b[1]) + abs(a[1]-b[1])) // 2


def analyze_strategic_state(ai, game_engine) -> str:
    """Ocena sytuacji VP i strategiczna adaptacja (przeniesione)."""
    try:
        all_players = getattr(game_engine, 'players', [])
        current_player_id = ai.player.id

        vp_data = {}
        for player in all_players:
            player_id = getattr(player, 'id', None)
            if player_id is not None:
                vp_points = getattr(player, 'victory_points', 0)
                vp_data[player_id] = vp_points

        my_vp = vp_data.get(current_player_id, 0)
        other_vps = [vp for pid, vp in vp_data.items() if pid != current_player_id]

        if not other_vps:
            ai.strategic_state = "TIED"
            return ai.strategic_state

        max_enemy_vp = max(other_vps)

        vp_difference = my_vp - max_enemy_vp

        if vp_difference >= 10:
            new_state = "WINNING"
        elif vp_difference <= -10:
            new_state = "LOSING"
            ai.consecutive_losing_turns += 1
        else:
            new_state = "TIED"
            ai.consecutive_losing_turns = 0

        if new_state != ai.strategic_state:
            print(f"🎯 [STRATEGIC] Zmiana stanu: {ai.strategic_state} -> {new_state} (VP: {my_vp} vs max {max_enemy_vp})")
            ai.strategic_state = new_state
            _adapt_strategy_to_state(ai)

        return ai.strategic_state

    except Exception as e:
        print(f"❌ [STRATEGIC] Błąd analizy: {e}")
        return "TIED"


def _adapt_strategy_to_state(ai) -> None:
    """Adaptuje strategię na podstawie aktualnego stanu gry (przeniesione)."""
    if ai.strategic_state == "WINNING":
        ai.aggression_level = 0.3
        ai.budget_allocation = {"allocate": 0.7, "purchase": 0.2, "reserve": 0.1}
        print("🛡️ [STRATEGY] WINNING MODE: Defensywnie, focus na utrzymanie pozycji")
    elif ai.strategic_state == "LOSING":
        ai.aggression_level = 0.9
        ai.budget_allocation = {"allocate": 0.4, "purchase": 0.5, "reserve": 0.1}
        print("⚔️ [STRATEGY] LOSING MODE: Agresywnie, focus na nowe jednostki")
    else:  # TIED
        ai.aggression_level = 0.6
        ai.budget_allocation = {"allocate": 0.5, "purchase": 0.4, "reserve": 0.1}
        print("⚖️ [STRATEGY] TIED MODE: Zbalansowany approach")


def prioritize_keypoints(ai, game_engine):
    """Inteligentne priorytetyzowanie celów (przeniesione)."""
    try:
        key_points = getattr(game_engine, 'key_points_state', {})

        # Lokalny sposób pobierania jednostek gracza (unikamy importu)
        my_units = []
        for token in getattr(game_engine, 'tokens', []):
            try:
                if getattr(token, 'owner', '').startswith(str(ai.player.id)):
                    my_units.append({'q': getattr(token, 'q', 0), 'r': getattr(token, 'r', 0)})
            except Exception:
                pass

        ai.keypoint_priorities = {}

        for hex_id, kp_data in key_points.items():
            if kp_data.get('current_value', 0) <= 0:
                continue
            try:
                q, r = map(int, hex_id.split(','))
                kp_pos = (q, r)
            except Exception:
                continue

            current_value = kp_data.get('current_value', 0)
            kp_type = kp_data.get('type', 'unknown')
            base_priority = current_value

            if ai.strategic_state == "LOSING":
                if kp_type == 'victory':
                    base_priority *= 2.0
                elif kp_type == 'economy':
                    base_priority *= 1.2
            elif ai.strategic_state == "WINNING":
                if kp_type == 'economy':
                    base_priority *= 1.5
                elif kp_type == 'victory':
                    base_priority *= 0.8
            else:  # TIED
                if kp_type == 'economy':
                    base_priority *= 1.3

            if my_units:
                min_distance = float('inf')
                for unit in my_units:
                    unit_pos = (unit['q'], unit['r'])
                    distance = _hex_distance(kp_pos, unit_pos)
                    if distance < min_distance:
                        min_distance = distance
                distance_modifier = 1.0 / max(1, min_distance * 0.1)
                base_priority *= distance_modifier

            board = getattr(game_engine, 'board', None)
            occupied_by_enemy = False
            if board and hasattr(board, 'is_occupied') and board.is_occupied(q, r):
                for token in getattr(game_engine, 'tokens', []):
                    if getattr(token, 'q', -1) == q and getattr(token, 'r', -1) == r:
                        token_owner = getattr(token, 'owner', '')
                        my_owner = f"{ai.player.id} ({ai.player.nation})"
                        if token_owner != my_owner:
                            occupied_by_enemy = True
                            base_priority *= 1.5
                        break

            ai.keypoint_priorities[hex_id] = {
                'position': kp_pos,
                'priority': base_priority,
                'value': current_value,
                'type': kp_type,
                'occupied_by_enemy': occupied_by_enemy,
                'strategic_modifier': ai.strategic_state
            }

        sorted_priorities = sorted(
            ai.keypoint_priorities.items(),
            key=lambda x: x[1]['priority'],
            reverse=True
        )

        print(f"🎯 [PRIORITIES] Top 3 cele dla {ai.strategic_state}:")
        for i, (hid, data) in enumerate(sorted_priorities[:3]):
            print(f"  {i+1}. {hid} ({data['type']}) - priorytet {data['priority']:.1f}, wartość {data['value']}")

        return sorted_priorities
    except Exception as e:
        print(f"❌ [PRIORITIES] Błąd priorytetyzacji: {e}")
        return []


def _determine_purchase_priority(ai) -> Dict[str, float]:
    if ai.strategic_state == "LOSING":
        return {
            'fast_attack': 0.4,
            'heavy_combat': 0.3,
            'support': 0.2,
            'economic': 0.1
        }
    elif ai.strategic_state == "WINNING":
        return {
            'heavy_combat': 0.4,
            'support': 0.3,
            'economic': 0.2,
            'fast_attack': 0.1
        }
    else:  # TIED
        return {
            'heavy_combat': 0.3,
            'fast_attack': 0.3,
            'support': 0.2,
            'economic': 0.2
        }


def _get_available_purchase_options(ai, game_engine) -> List[Dict[str, Any]]:
    # Symulacja – w przyszłości integracja z token shopem
    return [
        {'type': 'infantry', 'category': 'heavy_combat', 'cost': 15, 'combat_value': 8, 'mobility': 2},
        {'type': 'tank', 'category': 'heavy_combat', 'cost': 25, 'combat_value': 12, 'mobility': 3},
        {'type': 'recon', 'category': 'fast_attack', 'cost': 12, 'combat_value': 5, 'mobility': 4},
        {'type': 'artillery', 'category': 'support', 'cost': 20, 'combat_value': 10, 'mobility': 1},
        {'type': 'engineer', 'category': 'support', 'cost': 18, 'combat_value': 6, 'mobility': 2},
        {'type': 'supply', 'category': 'economic', 'cost': 10, 'combat_value': 2, 'mobility': 2}
    ]


def _select_optimal_purchases(ai, available_units, budget, priorities, current_army_size):
    selected: List[Dict[str, Any]] = []
    remaining_budget = budget

    weighted_units = []
    for unit in available_units:
        category = unit['category']
        priority_weight = priorities.get(category, 0.1)
        efficiency = unit['combat_value'] / max(1, unit['cost'])
        score = priority_weight * efficiency
        weighted_units.append((score, unit))

    weighted_units.sort(key=lambda x: x[0], reverse=True)

    for score, unit in weighted_units:
        if remaining_budget >= unit['cost'] and len(selected) < 5:
            selected.append(unit)
            remaining_budget -= unit['cost']
            print(f"  🎯 Wybrano {unit['type']} ({unit['category']}) za {unit['cost']}zł, score: {score:.2f}")

    return selected
