"""Moduł rozpoznania (reconnaissance) wydzielony z ai_commander.
Zawiera: gather_reconnaissance, _analyze_enemy_clusters, _calculate_cluster_center, _assess_keypoint_threats.
"""
from __future__ import annotations
from typing import Any, List, Dict, Tuple
from ai.obrona_ai import calculate_hex_distance

# Import dla logowania wywiadu
try:
    from utils.session_manager import SessionManager
    from utils.ai_commander_logger_zaawansowany import ZaawansowanyLoggerAI
    ADVANCED_LOGGING_AVAILABLE = True
except ImportError:
    ADVANCED_LOGGING_AVAILABLE = False

__all__ = [
    'gather_reconnaissance','analyze_enemy_clusters','assess_keypoint_threats', 'log_intelligence_analysis'
]

def log_intelligence_analysis(commander, analysis_type: str, intelligence_data: Dict[str, Any]):
    """Loguje analizę wywiadowczą AI"""
    if not ADVANCED_LOGGING_AVAILABLE:
        return
    
    try:
        session_manager = SessionManager()
        katalog_sesji = session_manager.get_current_session_dir()
        logger = ZaawansowanyLoggerAI(katalog_sesji)
        
        # Przygotowanie danych wywiadu
        intelligence_log_data = {
            'intelligence_type': analysis_type,
            'information_type': analysis_type,
            'nation': getattr(commander.player, 'nation', 'Unknown'),
            'source_reliability': intelligence_data.get('source_reliability', 0.8),
            'information_freshness': intelligence_data.get('information_freshness', 'CURRENT'),
            'enemy_units_spotted': intelligence_data.get('enemy_units_spotted', 0),
            'predicted_enemy_moves': intelligence_data.get('predicted_enemy_moves', 'UNKNOWN'),
            'threat_assessment_change': intelligence_data.get('threat_assessment_change', 'NO_CHANGE'),
            'counter_intelligence_detected': intelligence_data.get('counter_intelligence_detected', False),
            'surprise_probability': intelligence_data.get('surprise_probability', 0.1),
            'information_gaps': intelligence_data.get('information_gaps', 'MINIMAL'),
            'intelligence_confidence': intelligence_data.get('intelligence_confidence', 0.7),
            'actionable_intelligence': intelligence_data.get('actionable_intelligence', True),
            'intelligence_sharing': intelligence_data.get('intelligence_sharing', 'INTERNAL_ONLY'),
            'historical_prediction_accuracy': intelligence_data.get('historical_prediction_accuracy', 0.75),
            'enemy_pattern_recognition': intelligence_data.get('enemy_pattern_recognition', 'PARTIAL'),
            'deception_probability': intelligence_data.get('deception_probability', 0.05)
        }
        
        logger.loguj_analize_wywiadu(intelligence_log_data)
    except Exception as e:
        print(f"[LOG] Błąd logowania analizy wywiadu: {e}")

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
                    # POPRAWKA: Użyj prawdziwych statystyk bojowych zamiast tylko HP
                    attack_val = token.stats.get('attack', {}).get('value', 0)
                    defense_val = token.stats.get('defense_value', 0)
                    combat_value = getattr(token,'combat_value',0)  # HP - nadal potrzebne do sprawdzenia czy żyje
                    detection_level = 1.0
                    if hasattr(current_player,'visible_token_data'):
                        token_data = current_player.visible_token_data.get(token.id,{})
                        detection_level = token_data.get('detection_level',1.0)
                    
                    # Oblicz rzeczywistą siłę bojową jako kombinację ataku i obrony
                    combat_strength = max(1, (attack_val + defense_val) // 2)  # Średnia sił bojowych
                    
                    visible_enemies.append({
                        'id': getattr(token,'id','unknown'),
                        'position': enemy_pos,
                        'combat_value': combat_value,  # HP - do sprawdzenia stanu
                        'combat_strength': combat_strength,  # Prawdziwa siła bojowa
                        'attack_value': attack_val,
                        'defense_value': defense_val,
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
        
        # LOGOWANIE ANALIZY ROZPOZNANIA
        avg_detection_level = sum(e.get('detection_level', 1.0) for e in visible_enemies) / len(visible_enemies) if visible_enemies else 0
        total_enemy_strength = sum(e.get('combat_strength', 0) for e in visible_enemies)
        
        log_intelligence_analysis(commander, 'RECONNAISSANCE_SCAN', {
            'source_reliability': avg_detection_level,
            'information_freshness': 'CURRENT',
            'enemy_units_spotted': len(visible_enemies),
            'predicted_enemy_moves': f"Clusters: {len(enemy_clusters)}",
            'threat_assessment_change': 'UPDATED' if keypoint_threats else 'NO_CHANGE',
            'counter_intelligence_detected': avg_detection_level < 0.8,  # Niska wykrywalność = możliwy kontrwywiad
            'surprise_probability': 0.3 if len(enemy_clusters) > 2 else 0.1,
            'information_gaps': 'SIGNIFICANT' if len(visible_enemies) < 3 else 'MINIMAL',
            'intelligence_confidence': avg_detection_level,
            'actionable_intelligence': len(keypoint_threats) > 0 or len(enemy_clusters) > 0,
            'intelligence_sharing': 'INTERNAL_ONLY',
            'historical_prediction_accuracy': 0.75,  # Default - można poprawić z historii
            'enemy_pattern_recognition': 'PARTIAL' if enemy_clusters else 'NONE',
            'deception_probability': 0.05 if avg_detection_level > 0.9 else 0.15
        })
        
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
            'threat_level': sum(e.get('combat_strength', 1) for e in cluster)  # Użyj combat_strength zamiast combat_value
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
                    'threat_score': enemy.get('combat_strength', 1)/max(1,distance)  # Użyj combat_strength
                })
        if nearby_enemies:
            total_threat = sum(e['threat_score'] for e in nearby_enemies)
            threats[hex_id] = {
                'position': kp_pos,
                'threat_level': total_threat,
                'enemy_count': len(nearby_enemies),
                'closest_enemy_distance': min(e['distance'] for e in nearby_enemies)
            }
    
    # LOGOWANIE ANALIZY ZAGROŻEŃ PUNKTÓW KLUCZOWYCH
    if threats:
        max_threat = max(t['threat_level'] for t in threats.values())
        avg_threat = sum(t['threat_level'] for t in threats.values()) / len(threats)
        
        log_intelligence_analysis(commander, 'KEYPOINT_THREAT_ANALYSIS', {
            'source_reliability': 0.9,  # Bezpośrednia obserwacja = wysoka wiarygodność
            'information_freshness': 'CURRENT',
            'enemy_units_spotted': sum(t['enemy_count'] for t in threats.values()),
            'predicted_enemy_moves': 'KEYPOINT_ASSAULT',
            'threat_assessment_change': 'HEIGHTENED' if max_threat > 5 else 'MODERATE',
            'counter_intelligence_detected': False,
            'surprise_probability': min(0.8, max_threat / 10),  # Wyższa szansa na atak przy większym zagrożeniu
            'information_gaps': 'MINIMAL',
            'intelligence_confidence': 0.85,
            'actionable_intelligence': True,
            'intelligence_sharing': 'HIGH_PRIORITY',
            'historical_prediction_accuracy': 0.8,
            'enemy_pattern_recognition': 'KEYPOINT_FOCUS',
            'deception_probability': 0.1
        })
    
    return threats
