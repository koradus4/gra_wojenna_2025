"""Moduł rekomendacji i auto-egzekucji strategii AI.

Przeniesione z AdaptiveAICommander:
 - _generate_action_recommendations
 - _execute_strategic_plan
"""
from __future__ import annotations
from typing import List, Dict, Any


def _generate_action_recommendations(ai) -> List[str]:
    recommendations: List[str] = []
    state = getattr(ai, 'strategic_state', 'TIED')
    if state == "LOSING":
        recommendations.extend([
            "PRIORYTET: Skupić wszystkie siły na wysokowartościowych VP",
            "TAKTYKA: Agresywne ataki na słabe punkty wroga",
            "ZAKUPY: Szybkie jednostki atakujące",
            "BUDŻET: Maksymalnie w nowe jednostki"
        ])
    elif state == "WINNING":
        recommendations.extend([
            "PRIORYTET: Utrzymać kontrolę nad ekonomicznymi punktami",
            "TAKTYKA: Defensywne pozycje, unikać ryzyka",
            "ZAKUPY: Ciężkie jednostki obronne",
            "BUDŻET: Focus na resupply istniejących sił"
        ])
    else:  # TIED
        recommendations.extend([
            "PRIORYTET: Zbalansowany rozwój ekonomiczny i militarny",
            "TAKTYKA: Oportunistyczne zajmowanie wolnych punktów",
            "ZAKUPY: Uniwersalne jednostki",
            "BUDŻET: Zrównoważona alokacja"
        ])

    try:
        recon = getattr(ai, 'reconnaissance_data', {})
        enemy_count = recon.get('enemy_count', 0)
        # Ostrożnie z get_my_units -> unikamy importu cyrkularnego; uproszczona heurystyka
        my_count = getattr(ai.commander, 'cached_my_unit_count', None)
        if my_count is None:
            my_count = enemy_count  # neutral fallback
        if enemy_count > my_count:
            recommendations.append("UWAGA: Wróg ma przewagę liczebną - unikaj otwartej walki")
    except Exception:
        pass

    return recommendations


def _execute_strategic_plan(ai, strategic_plan: Dict[str, Any], game_engine) -> None:
    try:
        print("🤖 [AUTO EXEC] Wykonuję strategiczny plan...")
        # Placeholder przyszłych automatycznych akcji (zakupy, deployment, priorytety)
        print("📋 [AUTO EXEC] Plan przygotowany do manualnej egzekucji")
    except Exception as e:
        print(f"❌ [AUTO EXEC] Błąd wykonania planu: {e}")

__all__ = ["_generate_action_recommendations", "_execute_strategic_plan"]