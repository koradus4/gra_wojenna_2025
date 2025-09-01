"""Moduł rozpoznania (reconnaissance) wydzielony z ai_commander.
Zawiera: gather_reconnaissance, _analyze_enemy_clusters, _calculate_cluster_center, _assess_keypoint_threats.
"""
from __future__ import annotations
from typing import Any, List, Dict, Tuple
from ai.obrona_ai import calculate_hex_distance

__all__ = [
    'gather_reconnaissance','analyze_enemy_clusters','assess_keypoint_threats'
]

def gather_reconnaissance(commander, game_engine: Any):
    try:
        current_player = getattr(game_engine,'current_player_obj',None)
        if not current_player:
            return {}
        visible_enemies = []
        if hasattr(current_player,'visible_tokens'):
            for token in current_player.visible_tokens:
                token_owner = getattr(token,'owner','')
                my_owner = f"{commander.player.id} ({commander.player.nation})"
                if token_owner != my_owner and token_owner:
                    enemy_pos = (getattr(token,'q',0), getattr(token,'r',0))
                    combat_value = getattr(token,'combat_value',0)
                    detection_level = 1.0
                    if hasattr(current_player,'visible_token_data'):
                        token_data = current_player.visible_token_data.get(token.id,{})
                        detection_level = token_data.get('detection_level',1.0)
                    visible_enemies.append({
                        'id': getattr(token,'id','unknown'),
                        'position': enemy_pos,
                        'combat_value': combat_value,
                        'detection_level': detection_level,
                        'owner': token_owner
                    })
        enemy_clusters = analyze_enemy_clusters(visible_enemies)
        keypoint_threats = assess_keypoint_threats(commander, visible_enemies, game_engine)
        commander.reconnaissance_data = {
            'visible_enemies': visible_enemies,
            'enemy_count': len(visible_enemies),
            'enemy_clusters': enemy_clusters,
            'keypoint_threats': keypoint_threats,
            'last_update': getattr(game_engine,'turn_number',1)
        }
        print(f"🔍 [RECON] Wykryto {len(visible_enemies)} wrogów w {len(enemy_clusters)} klastrach")
        if keypoint_threats:
            print(f"🚨 [RECON] {len(keypoint_threats)} punktów kluczowych zagrożonych")
        return commander.reconnaissance_data
    except Exception as e:
        print(f"❌ [RECON] Błąd rozpoznania: {e}")
        return {}

def analyze_enemy_clusters(enemies: List[Dict]):
    if not enemies:
        return []
    clusters = []
    processed = set()
    for i, enemy in enumerate(enemies):
        if i in processed:
            continue
        cluster = [enemy]
        processed.add(i)
        for j, other_enemy in enumerate(enemies):
            if j in processed:
                continue
            distance = calculate_hex_distance(enemy['position'], other_enemy['position'])
            if distance <= 4:
                cluster.append(other_enemy)
                processed.add(j)
        clusters.append({
            'size': len(cluster),
            'enemies': cluster,
            'center': _calculate_cluster_center(cluster),
            'threat_level': sum(e['combat_value'] for e in cluster)
        })
    return clusters

def _calculate_cluster_center(cluster: List[Dict]) -> Tuple[int,int]:
    if not cluster:
        return (0,0)
    avg_q = sum(e['position'][0] for e in cluster)//len(cluster)
    avg_r = sum(e['position'][1] for e in cluster)//len(cluster)
    return (avg_q, avg_r)

def assess_keypoint_threats(commander, enemies: List[Dict], game_engine: Any):
    key_points = getattr(game_engine,'key_points_state',{})
    threats = {}
    for hex_id, kp_data in key_points.items():
        if kp_data.get('current_value',0) <=0:
            continue
        try:
            q,r = map(int, hex_id.split(','))
            kp_pos = (q,r)
        except Exception:
            continue
        nearby_enemies = []
        for enemy in enemies:
            distance = calculate_hex_distance(kp_pos, enemy['position'])
            if distance <= 6:
                nearby_enemies.append({
                    'enemy': enemy,
                    'distance': distance,
                    'threat_score': enemy['combat_value']/max(1,distance)
                })
        if nearby_enemies:
            total_threat = sum(e['threat_score'] for e in nearby_enemies)
            threats[hex_id] = {
                'position': kp_pos,
                'threat_level': total_threat,
                'enemy_count': len(nearby_enemies),
                'closest_enemy_distance': min(e['distance'] for e in nearby_enemies)
            }
    return threats
