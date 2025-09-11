#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🏆 PHASE 5: VICTORY POINTS OPTIMIZATION SYSTEM
Module 1: VP Intelligence System

Zaawansowany system analizy i predykcji Victory Points
Integruje się z Phase 1-4 dla complete strategic mastery
"""

import csv
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Tuple, Optional

class VPIntelligenceSystem:
    """
    🧠 VP Intelligence System - Core Phase 5 Module
    
    Capabilities:
    - Real-time VP trend analysis
    - Predictive VP modeling (next 3-5 turns) 
    - VP opportunity identification
    - Enemy VP threat assessment
    """
    
    def __init__(self, game_engine=None, nation="Unknown"):
        self.game_engine = game_engine
        self.nation = nation
        self.vp_history = []
        self.threat_assessments = []
        self.opportunities = []
        self.predictions = {}
        
        # CSV logging setup
        self.logs_dir = Path("logs/vp_intelligence")
        self.logs_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.vp_trends_log = self.logs_dir / f"vp_trends_{nation}_{timestamp}.csv"
        self.vp_predictions_log = self.logs_dir / f"vp_predictions_{nation}_{timestamp}.csv"
        self.vp_opportunities_log = self.logs_dir / f"vp_opportunities_{nation}_{timestamp}.csv"
        
        self._init_csv_logs()
        print(f"🧠 [VP INTELLIGENCE] Initialized for {nation}")
    
    def _init_csv_logs(self):
        """Initialize CSV logging files"""
        # VP Trends Log
        with open(self.vp_trends_log, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'turn', 'nation', 'vp_current', 'vp_enemy', 'vp_gap', 
                'vp_trend', 'vp_velocity', 'threat_level', 'opportunity_count'
            ])
        
        # VP Predictions Log
        with open(self.vp_predictions_log, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'turn', 'nation', 'prediction_horizon', 'predicted_vp_own',
                'predicted_vp_enemy', 'confidence_level', 'key_factors', 'recommendations'
            ])
        
        # VP Opportunities Log  
        with open(self.vp_opportunities_log, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'turn', 'nation', 'opportunity_type', 'target_units',
                'estimated_vp_gain', 'risk_level', 'resources_required', 'priority_score'
            ])
    
    def analyze_vp_situation(self, current_turn: int) -> Dict:
        """
        🔍 Comprehensive VP situation analysis
        
        Returns:
            Dict with VP trends, threats, opportunities, and predictions
        """
        print(f"🔍 [VP INTEL] Analyzing VP situation for turn {current_turn}")
        
        # Get current VP status
        vp_status = self._get_current_vp_status()
        
        # Analyze trends
        vp_trends = self._analyze_vp_trends(vp_status, current_turn)
        
        # Assess threats
        threat_assessment = self._assess_vp_threats(vp_status)
        
        # Identify opportunities
        opportunities = self._identify_vp_opportunities(vp_status)
        
        # Generate predictions
        predictions = self._generate_vp_predictions(vp_status, current_turn)
        
        # Compile comprehensive analysis
        analysis = {
            'current_status': vp_status,
            'trends': vp_trends,
            'threats': threat_assessment,
            'opportunities': opportunities,
            'predictions': predictions,
            'strategic_recommendation': self._generate_strategic_recommendation(
                vp_status, vp_trends, threat_assessment, opportunities
            )
        }
        
        # Log analysis
        self._log_vp_analysis(analysis, current_turn)
        
        print(f"📊 [VP INTEL] Analysis complete - {len(opportunities)} opportunities identified")
        return analysis
    
    def _get_current_vp_status(self) -> Dict:
        """Get current VP status from game engine"""
        try:
            # Get VP status from game engine
            if hasattr(self.game_engine, 'get_victory_points'):
                vp_data = self.game_engine.get_victory_points()
            else:
                # Fallback - estimate from visible units
                vp_data = self._estimate_vp_from_units()
            
            return {
                'vp_own': vp_data.get('own', 0),
                'vp_enemy': vp_data.get('enemy', 0),
                'vp_gap': vp_data.get('own', 0) - vp_data.get('enemy', 0),
                'turn': vp_data.get('turn', 0),
                'max_turns': vp_data.get('max_turns', 30)
            }
        except Exception as e:
            print(f"⚠️ [VP INTEL] Error getting VP status: {e}")
            return {
                'vp_own': 0, 'vp_enemy': 0, 'vp_gap': 0,
                'turn': 1, 'max_turns': 30
            }
    
    def _estimate_vp_from_units(self) -> Dict:
        """Estimate VP from visible destroyed units (fallback method)"""
        # This is a simplified estimation - in real implementation
        # we would track destroyed enemy units for VP calculation
        return {
            'own': 0,  # Would track our VP from destroyed enemies
            'enemy': 0,  # Would estimate enemy VP from our losses
            'turn': getattr(self.game_engine, 'current_turn', 1),
            'max_turns': 30
        }
    
    def _analyze_vp_trends(self, vp_status: Dict, current_turn: int) -> Dict:
        """
        📈 Analyze VP trends and velocity
        """
        # Add current status to history
        self.vp_history.append({
            'turn': current_turn,
            'vp_own': vp_status['vp_own'],
            'vp_enemy': vp_status['vp_enemy'],
            'vp_gap': vp_status['vp_gap']
        })
        
        # Keep only recent history (last 10 turns)
        if len(self.vp_history) > 10:
            self.vp_history = self.vp_history[-10:]
        
        # Calculate trends
        if len(self.vp_history) >= 2:
            recent = self.vp_history[-2:]
            vp_velocity = recent[-1]['vp_gap'] - recent[-2]['vp_gap']
            
            # Determine trend direction
            if vp_velocity > 0:
                trend_direction = "IMPROVING"
            elif vp_velocity < 0:
                trend_direction = "DECLINING"  
            else:
                trend_direction = "STABLE"
        else:
            vp_velocity = 0
            trend_direction = "UNKNOWN"
        
        return {
            'direction': trend_direction,
            'velocity': vp_velocity,
            'history_length': len(self.vp_history),
            'avg_vp_per_turn': self._calculate_avg_vp_gain()
        }
    
    def _calculate_avg_vp_gain(self) -> float:
        """Calculate average VP gain per turn"""
        if len(self.vp_history) < 2:
            return 0.0
            
        total_gain = self.vp_history[-1]['vp_own'] - self.vp_history[0]['vp_own']
        turns = len(self.vp_history) - 1
        return total_gain / turns if turns > 0 else 0.0
    
    def _assess_vp_threats(self, vp_status: Dict) -> Dict:
        """
        ⚠️ Assess VP threats from enemy
        """
        try:
            # Analyze enemy units for VP threat potential
            enemy_units = self._get_visible_enemy_units()
            
            # Calculate threat levels based on combat_strength not HP
            high_value_targets = len([u for u in enemy_units if u.get('combat_strength', u.get('attack_val', 0) + u.get('defense_val', 0)) >= 10])
            medium_value_targets = len([u for u in enemy_units if 5 <= u.get('combat_strength', u.get('attack_val', 0) + u.get('defense_val', 0)) < 10])
            
            # Assess overall threat level
            if vp_status['vp_gap'] < -10:
                threat_level = "CRITICAL"
            elif vp_status['vp_gap'] < 0:
                threat_level = "HIGH"
            elif vp_status['vp_gap'] < 5:
                threat_level = "MEDIUM"
            else:
                threat_level = "LOW"
            
            return {
                'overall_threat': threat_level,
                'vp_deficit': max(0, -vp_status['vp_gap']),
                'enemy_units_visible': len(enemy_units),
                'high_value_targets': high_value_targets,
                'medium_value_targets': medium_value_targets,
                'threat_factors': self._identify_threat_factors(enemy_units, vp_status)
            }
            
        except Exception as e:
            print(f"⚠️ [VP INTEL] Error assessing threats: {e}")
            return {'overall_threat': 'UNKNOWN', 'error': str(e)}
    
    def _get_visible_enemy_units(self) -> List[Dict]:
        """Get all visible enemy units"""
        try:
            if hasattr(self.game_engine, 'board') and hasattr(self.game_engine.board, 'tokens'):
                enemy_units = []
                for token in self.game_engine.board.tokens.values():
                    # Check if it's an enemy token (different owner)
                    if hasattr(token, 'owner') and token.owner != getattr(self.game_engine, 'current_player_id', None):
                        enemy_units.append({
                            'id': getattr(token, 'id', 'unknown'),
                            'combat_value': getattr(token, 'combat_value', 0),
                            'position': (getattr(token, 'q', 0), getattr(token, 'r', 0)),
                            'type': getattr(token, 'unit_type', 'Unknown')
                        })
                return enemy_units
        except Exception as e:
            print(f"⚠️ [VP INTEL] Error getting enemy units: {e}")
        
        return []
    
    def _identify_threat_factors(self, enemy_units: List[Dict], vp_status: Dict) -> List[str]:
        """Identify specific threat factors"""
        factors = []
        
        if vp_status['vp_gap'] < -5:
            factors.append("VP_DEFICIT")
        
        if len(enemy_units) > 15:
            factors.append("LARGE_ENEMY_FORCE")
            
        high_combat_units = [u for u in enemy_units if u.get('combat_strength', u.get('attack_val', 0) + u.get('defense_val', 0)) >= 12]
        if len(high_combat_units) > 3:
            factors.append("ELITE_ENEMY_UNITS")
        
        return factors
    
    def _identify_vp_opportunities(self, vp_status: Dict) -> List[Dict]:
        """
        🎯 Identify VP acquisition opportunities
        """
        opportunities = []
        
        try:
            enemy_units = self._get_visible_enemy_units()
            
            for unit in enemy_units:
                # Calculate VP opportunity score based on combat strength, not HP
                combat_strength = unit.get('combat_strength', 
                                         unit.get('attack_val', 0) + unit.get('defense_val', 0))
                combat_value = unit.get('combat_value', 0)  # HP dla statusu jednostki
                
                if combat_strength >= 10:
                    # High-value target based on combat strength
                    opportunity = {
                        'type': 'HIGH_VALUE_ELIMINATION',
                        'target_id': unit['id'],
                        'target_type': unit.get('type', 'Unknown'),
                        'estimated_vp': self._estimate_vp_value(combat_strength),
                        'risk_level': 'MEDIUM',
                        'priority_score': combat_strength * 2,
                        'resources_required': 'MAJOR_ATTACK'
                    }
                    opportunities.append(opportunity)
                
                elif combat_strength >= 5:
                    # Medium-value target based on combat strength
                    opportunity = {
                        'type': 'MEDIUM_VALUE_ELIMINATION', 
                        'target_id': unit['id'],
                        'target_type': unit.get('type', 'Unknown'),
                        'estimated_vp': self._estimate_vp_value(combat_strength),
                        'risk_level': 'LOW',
                        'priority_score': combat_strength,
                        'resources_required': 'TACTICAL_STRIKE'
                    }
                    opportunities.append(opportunity)
            
            # Sort by priority score
            opportunities.sort(key=lambda x: x['priority_score'], reverse=True)
            
            # Keep top 10 opportunities
            self.opportunities = opportunities[:10]
            
        except Exception as e:
            print(f"⚠️ [VP INTEL] Error identifying opportunities: {e}")
            
        return self.opportunities
    
    def _estimate_vp_value(self, combat_strength: int) -> int:
        """Estimate VP value of destroying unit with given combat value"""
        # Simplified VP estimation based on combat strength - adjust based on game rules
        if combat_strength >= 15:
            return 8  # Major unit
        elif combat_strength >= 10:
            return 5  # Regular unit
        elif combat_strength >= 5:
            return 3  # Small unit
        else:
            return 1  # Minimal unit
    
    def _generate_vp_predictions(self, vp_status: Dict, current_turn: int) -> Dict:
        """
        🔮 Generate VP predictions for next 3-5 turns
        """
        predictions = {}
        
        try:
            turns_remaining = vp_status['max_turns'] - current_turn
            avg_vp_gain = self._calculate_avg_vp_gain()
            
            # Predict next 3-5 turns
            prediction_horizon = min(5, turns_remaining)
            
            for i in range(1, prediction_horizon + 1):
                future_turn = current_turn + i
                
                # Simple linear prediction (can be enhanced with ML later)
                predicted_vp_own = vp_status['vp_own'] + (avg_vp_gain * i)
                predicted_vp_enemy = vp_status['vp_enemy'] + (avg_vp_gain * 0.7 * i)  # Assume enemy gains slower
                
                # Calculate confidence (decreases with distance)
                confidence = max(0.5, 1.0 - (i * 0.15))
                
                predictions[future_turn] = {
                    'predicted_vp_own': predicted_vp_own,
                    'predicted_vp_enemy': predicted_vp_enemy,
                    'predicted_gap': predicted_vp_own - predicted_vp_enemy,
                    'confidence': confidence,
                    'key_factors': ['historical_trend', 'current_velocity']
                }
            
        except Exception as e:
            print(f"⚠️ [VP INTEL] Error generating predictions: {e}")
            
        return predictions
    
    def _generate_strategic_recommendation(self, vp_status: Dict, trends: Dict, 
                                         threats: Dict, opportunities: List[Dict]) -> Dict:
        """
        💡 Generate strategic recommendation based on VP analysis
        """
        try:
            # Determine current position
            vp_gap = vp_status['vp_gap']
            turns_remaining = vp_status['max_turns'] - vp_status['turn']
            
            if vp_gap > 10:
                position = "WINNING"
                strategy = "DEFENSIVE"
            elif vp_gap > 0:
                position = "LEADING"  
                strategy = "BALANCED"
            elif vp_gap > -10:
                position = "COMPETING"
                strategy = "AGGRESSIVE" 
            else:
                position = "LOSING"
                strategy = "DESPERATE"
            
            # Generate specific recommendations
            recommendations = []
            
            if strategy == "DEFENSIVE":
                recommendations.extend([
                    "Protect high-value units",
                    "Maintain VP lead through survival",
                    "Avoid risky engagements"
                ])
            elif strategy == "AGGRESSIVE":
                recommendations.extend([
                    "Target enemy high-value units",
                    "Execute VP opportunities",
                    "Accept calculated risks for VP gains"
                ])
            elif strategy == "DESPERATE":
                recommendations.extend([
                    "All-out VP hunting",
                    "Prioritize highest VP targets",
                    "Ignore defensive considerations"
                ])
            else:  # BALANCED
                recommendations.extend([
                    "Pursue safe VP opportunities", 
                    "Maintain positional advantage",
                    "Prepare for endgame scenarios"
                ])
            
            return {
                'position': position,
                'strategy': strategy,
                'confidence': 0.8,  # Base confidence
                'recommendations': recommendations,
                'priority_actions': [op['type'] for op in opportunities[:3]]
            }
            
        except Exception as e:
            print(f"⚠️ [VP INTEL] Error generating recommendation: {e}")
            return {'position': 'UNKNOWN', 'strategy': 'HOLD', 'error': str(e)}
    
    def _log_vp_analysis(self, analysis: Dict, current_turn: int):
        """Log VP analysis to CSV files"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Log VP trends
            with open(self.vp_trends_log, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, current_turn, self.nation,
                    analysis['current_status']['vp_own'],
                    analysis['current_status']['vp_enemy'], 
                    analysis['current_status']['vp_gap'],
                    analysis['trends']['direction'],
                    analysis['trends']['velocity'],
                    analysis['threats']['overall_threat'],
                    len(analysis['opportunities'])
                ])
            
            # Log predictions
            for turn, pred in analysis['predictions'].items():
                with open(self.vp_predictions_log, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp, current_turn, self.nation, turn,
                        pred['predicted_vp_own'], pred['predicted_vp_enemy'],
                        pred['confidence'], ';'.join(pred['key_factors']),
                        analysis['strategic_recommendation']['strategy']
                    ])
            
            # Log opportunities
            for opp in analysis['opportunities']:
                with open(self.vp_opportunities_log, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp, current_turn, self.nation,
                        opp['type'], opp.get('target_id', ''),
                        opp['estimated_vp'], opp['risk_level'],
                        opp['resources_required'], opp['priority_score']
                    ])
            
        except Exception as e:
            print(f"⚠️ [VP INTEL] Error logging analysis: {e}")

def integrate_vp_intelligence_system(game_engine, my_units, player_id):
    """
    🔌 Integration function for Phase 5 VP Intelligence System
    
    Called by AI Commander to get VP intelligence and strategic recommendations
    """
    try:
        # Get nation name for logging
        if hasattr(game_engine, 'current_player') and hasattr(game_engine.current_player, 'nation'):
            nation = game_engine.current_player.nation
        else:
            nation = f"Player_{player_id}"
        
        # Initialize VP Intelligence System
        vp_intel = VPIntelligenceSystem(game_engine, nation)
        
        # Get current turn
        current_turn = getattr(game_engine, 'current_turn', 1)
        
        # Perform comprehensive VP analysis
        vp_analysis = vp_intel.analyze_vp_situation(current_turn)
        
        # Return integrated analysis for AI Commander use
        return {
            'system_status': 'ACTIVE',
            'vp_intelligence_active': True,
            'current_vp_status': vp_analysis['current_status'],
            'strategic_position': vp_analysis['strategic_recommendation']['position'],
            'recommended_strategy': vp_analysis['strategic_recommendation']['strategy'],
            'vp_opportunities': len(vp_analysis['opportunities']),
            'top_opportunities': vp_analysis['opportunities'][:3],
            'threat_level': vp_analysis['threats']['overall_threat'],
            'predictions_available': len(vp_analysis['predictions']),
            'phase5_module1_status': 'OPERATIONAL'
        }
        
    except Exception as e:
        print(f"❌ [VP INTEL] Integration error: {e}")
        return {
            'system_status': 'ERROR',
            'vp_intelligence_active': False,
            'error': str(e),
            'phase5_module1_status': 'ERROR'
        }

# Test function for standalone testing
def main():
    """Test VP Intelligence System"""
    print("🧠 Testing VP Intelligence System...")
    
    # Mock game engine for testing
    class MockGameEngine:
        def __init__(self):
            self.current_turn = 5
            self.current_player_id = 1
    
    mock_engine = MockGameEngine()
    result = integrate_vp_intelligence_system(mock_engine, [], 1)
    
    print("✅ VP Intelligence System test complete!")
    print(f"📊 Result: {result}")

if __name__ == "__main__":
    main()
