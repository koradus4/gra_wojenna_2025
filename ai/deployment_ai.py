"""Moduł wdrażania zakupionych jednostek (deployment) wydzielony z ai_commander.
Zawiera funkcje: deploy_purchased_units, find_deployment_position, create_and_deploy_token.
"""
from __future__ import annotations
from typing import Any, Optional, Tuple
from pathlib import Path
import json, os, glob
from ai.logowanie_ai import log_commander_action
from ai.ruch_jednostek import move_towards  # potencjalnie przydatne przyszłościowo

__all__ = [
    'deploy_purchased_units','find_deployment_position','create_and_deploy_token'
]

def deploy_purchased_units(game_engine, player_id):
    try:
        current_player = getattr(game_engine,'current_player_obj',None)
        if not current_player:
            return 0
        nation = getattr(current_player,'nation','Unknown')
        assets_path = Path('assets/tokens')
        commander_folder = assets_path / f"nowe_dla_{player_id}"
        if not commander_folder.exists():
            return 0
        # znajdź wszystkie token.json w podfolderach
        token_files = list(commander_folder.glob('*/token.json'))
        if not token_files:
            return 0
        deployed = 0
        for tf in token_files[:50]:  # safety limit
            try:
                with open(tf,'r',encoding='utf-8') as f:
                    data = json.load(f)
                # sprawdź czy już wdrożony (np. marker file)
                deployed_marker = tf.parent / '.deployed'
                if deployed_marker.exists():
                    continue
                pos = find_deployment_position(game_engine, player_id)
                if not pos:
                    continue
                created = create_and_deploy_token(game_engine, player_id, data, pos)
                if created:
                    deployed += 1
                    deployed_marker.touch()
            except Exception:
                continue
        if deployed>0:
            print(f"[DEPLOY] Wdrożono {deployed} nowych jednostek dla gracza {player_id}")
        return deployed
    except Exception as e:
        print(f"❌ [DEPLOY] Błąd: {e}")
        return 0

def find_deployment_position(game_engine, player_id) -> Optional[Tuple[int,int]]:
    try:
        board = getattr(game_engine,'board',None)
        if not board:
            return None
        # heurystyka: znajdź pierwszy mój token i spróbuj w jego sąsiedztwie
        my_tokens = [t for t in getattr(game_engine,'tokens',[]) if str(getattr(t,'owner','')).startswith(str(player_id))]
        if not my_tokens:
            return None
        base = my_tokens[0]
        base_pos = (getattr(base,'q',0), getattr(base,'r',0))
        # sprawdź sąsiadów z ograniczeniem 12 hexów
        for dq in range(-2,3):
            for dr in range(-2,3):
                q = base_pos[0]+dq
                r = base_pos[1]+dr
                if board.is_occupied(q,r):
                    continue
                return (q,r)
    except Exception:
        return None
    return None

def create_and_deploy_token(game_engine, player_id, token_data:dict, position:Tuple[int,int]):
    try:
        TokenClass = None
        try:
            from engine.token import Token as TokenClass
        except Exception:
            pass
        if not TokenClass:
            return False
        q,r = position
        new_token = TokenClass(
            id=token_data.get('id', f"AI_NEW_{player_id}"),
            owner=f"{player_id} ({getattr(getattr(game_engine,'current_player_obj',None),'nation','AI')})",
            q=q,r=r,
            type=token_data.get('type','unit'),
            stats=token_data.get('stats',{}),
        )
        game_engine.tokens.append(new_token)
        try:
            log_commander_action(
                unit_id=getattr(new_token,'id','?'),
                action_type='deploy_new',
                from_pos=None,
                to_pos=(q,r),
                reason='deployment_ai',
                player_nation=getattr(getattr(game_engine,'current_player_obj',None),'nation','AI'),
                extra={'phase':'deployment'}
            )
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"❌ [DEPLOY] Błąd tworzenia tokenu: {e}")
        return False
