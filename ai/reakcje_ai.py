"""Ataki reakcyjne AI wyodrębnione z ai_commander."""
from __future__ import annotations
from typing import Any

__all__ = ["check_ai_reaction_attacks"]

def check_ai_reaction_attacks(moved_token, game_engine: Any, ai_player_nation: str = "Unknown") -> None:
    from ai.logowanie_ai import log_commander_action
    try:
        if not moved_token or not game_engine:
            return
        moved_owner = getattr(moved_token, 'owner', '')
        for enemy in getattr(game_engine, 'tokens', []):
            if enemy.id == moved_token.id or enemy.owner == moved_token.owner:
                continue
            nation_enemy = enemy.owner.split('(')[-1].replace(')', '').strip()
            nation_moved = moved_owner.split('(')[-1].replace(')', '').strip()
            if nation_enemy == nation_moved:
                continue
            board = getattr(game_engine, 'board', None)
            if not board:
                continue
            sight = enemy.stats.get('sight', 0)
            dist = board.hex_distance((enemy.q, enemy.r), (moved_token.q, moved_token.r))
            if dist > sight:
                continue
            attack_range = enemy.stats.get('attack', {}).get('range', 1)
            if dist > attack_range:
                continue
            print(f"🎯 [AI_REACTION] {enemy.id} ({enemy.owner}) atakuje {moved_token.id} ({moved_owner})!")
            setattr(moved_token, 'wykryty_do_konca_tury', True)
            from engine.action_refactored_clean import CombatAction
            action = CombatAction(enemy.id, moved_token.id, is_reaction=True)
            result = game_engine.execute_action(action)
            if getattr(result, 'success', False):
                print(f"⚔️ [AI_REACTION] Sukces: {getattr(result,'message','OK')}")
            else:
                print(f"❌ [AI_REACTION] Błąd: {getattr(result,'message','brak')}")
            try:
                log_commander_action(
                    unit_id=enemy.id,
                    action_type="reaction_combat",
                    from_pos=(enemy.q, enemy.r),
                    to_pos=(moved_token.q, moved_token.r),
                    reason=f"Reaction attack on {moved_token.id}",
                    player_nation=nation_enemy
                )
            except Exception:
                pass
    except Exception as e:
        print(f"❌ [AI_REACTION] Błąd sprawdzania reakcji: {e}")
