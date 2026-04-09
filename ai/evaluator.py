# -*- coding: utf-8 -*-
"""
Evaluator – heurystyki i funkcje oceny (scoring) dla agentów AI.

Formuła punktacji heksa docelowego (z STRUKTURA_PROJEKTU.md):
  SCORE = (V_strategiczna + V_ofensywna - R_ryzyko) / (1 + koszt_ruchu)
"""

import math
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Domyślne wagi heurystyki (konfigurowalne przez poziom trudności)
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS = {
    "key_point_type": {
        "city": 20,
        "supply": 15,
        "crossroads": 10,
        None: 5,
    },
    "key_point_urgency_bonus": 10,   # bonus gdy KP wyczerpie się w ≤ 3 turach
    "key_point_urgency_turns": 3,    # próg tur
    "offense_value_ratio": 0.8,      # atak gdy own CV ≥ ratio * enemy CV
    "max_loss_ratio": 0.6,           # nie atakuj gdy straty > 60% własnego CV
    "danger_range_penalty": 5,       # kara za każdą wrogą jednostkę w zasięgu
    "defense_mod_bonus": 3,          # bonus za każdy stopień mod obrony terenu
}


class Evaluator:
    """Funkcje oceny akcji dla agentów AI."""

    def __init__(self, weights: Optional[Dict[str, Any]] = None):
        self.weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    # ------------------------------------------------------------------
    # Ocena ruchu
    # ------------------------------------------------------------------

    def score_move(
        self,
        token: Dict[str, Any],
        dest_q: int,
        dest_r: int,
        state: Dict[str, Any],
        move_cost: int = 1,
        defense_mod: float = 0,
    ) -> float:
        """
        Oblicz wynik (score) dla ruchu żetonu na pole (dest_q, dest_r).

        Parametry:
            token      – słownik żetonu (z StateAdapter)
            dest_q/r   – cel ruchu
            state      – bieżący stan gry
            move_cost  – koszt MP trasy (A*)
            defense_mod – modyfikator obrony terenu na polu docelowym

        Zwraca:
            Wynik numeryczny (wyższy = lepszy ruch).
        """
        v_strategic = self._strategic_value(dest_q, dest_r, state)
        v_offensive = self._offensive_value(token, dest_q, dest_r, state)
        r_risk = self._risk_value(token, dest_q, dest_r, state)
        r_risk -= defense_mod * self.weights["defense_mod_bonus"]
        denominator = 1 + move_cost
        return (v_strategic + v_offensive - r_risk) / denominator

    def _strategic_value(
        self, dest_q: int, dest_r: int, state: Dict[str, Any]
    ) -> float:
        """Wartość strategiczna heksa – zbliżenie do key pointów."""
        score = 0.0
        w = self.weights
        for kp in state.get("key_points", []):
            dist = _hex_distance(dest_q, dest_r, kp["q"], kp["r"])
            if dist == 0:
                kp_type_score = w["key_point_type"].get(
                    kp.get("type"), w["key_point_type"][None]
                )
                # Bonus za pilność
                urgency = 0
                initial = kp.get("initial") or 1
                current = kp.get("current") or 0
                turns_left = math.ceil(current / max(1, 0.1 * initial))
                if turns_left <= w["key_point_urgency_turns"]:
                    urgency = w["key_point_urgency_bonus"]
                score += kp_type_score + urgency
            else:
                # Małe zbliżenie – proporcjonalny bonus malejący z dystansem
                score += 1.0 / (dist + 1)
        return score

    def _offensive_value(
        self,
        token: Dict[str, Any],
        dest_q: int,
        dest_r: int,
        state: Dict[str, Any],
    ) -> float:
        """Wartość ofensywna – możliwość ataku na słabą jednostkę wroga."""
        score = 0.0
        own_cv = token.get("cv", 0)
        atk_range = token.get("rng", 1)
        for enemy in state.get("enemy_visible", []):
            dist = _hex_distance(dest_q, dest_r, enemy["q"], enemy["r"])
            if dist <= atk_range:
                enemy_cv = enemy.get("cv", 1)
                if own_cv >= self.weights["offense_value_ratio"] * enemy_cv:
                    score += own_cv - enemy_cv + enemy.get("price", 0) * 0.1
        return score

    def _risk_value(
        self,
        token: Dict[str, Any],
        dest_q: int,
        dest_r: int,
        state: Dict[str, Any],
    ) -> float:
        """Ryzyko – kara za pozostawanie w zasięgu wrogich ataków."""
        risk = 0.0
        penalty = self.weights["danger_range_penalty"]
        for enemy in state.get("enemy_visible", []):
            enemy_range = enemy.get("rng", 1)
            dist = _hex_distance(dest_q, dest_r, enemy["q"], enemy["r"])
            if dist <= enemy_range:
                risk += penalty
        return risk

    # ------------------------------------------------------------------
    # Ocena ataku
    # ------------------------------------------------------------------

    def should_attack(
        self,
        attacker: Dict[str, Any],
        defender: Dict[str, Any],
    ) -> bool:
        """
        Zdecyduj czy warto atakować jednostkę wroga.

        Zasady:
        - Nie atakuj jeśli własne CV < offense_value_ratio * CV wroga
          (zbyt duża dysproporcja sił).
        - Nie atakuj jeśli przewidywane straty > max_loss_ratio * własnego CV.
          Uproszczona estymacja strat: min(own_cv, defender_cv) * 0.5
        """
        own_cv = attacker.get("cv", 0)
        def_cv = defender.get("cv", 0)
        # Nie atakuj gdy przeciwnik jest wyraźnie silniejszy
        if own_cv < self.weights["offense_value_ratio"] * def_cv:
            return False
        estimated_loss = min(own_cv, def_cv) * 0.5
        return estimated_loss <= self.weights["max_loss_ratio"] * own_cv

    def score_attack(
        self,
        attacker: Dict[str, Any],
        defender: Dict[str, Any],
    ) -> float:
        """Wynik ataku (wyższy = bardziej opłacalny)."""
        own_cv = attacker.get("cv", 1)
        def_cv = defender.get("cv", 1)
        price = defender.get("price", 0)
        advantage = own_cv - def_cv
        return advantage + price * 0.1


# ---------------------------------------------------------------------------
# Pomocnicza funkcja dystansu heksów (offset-free, cube coords)
# ---------------------------------------------------------------------------

def _hex_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    """Dystans między dwoma heksami we współrzędnych axial (cube-distance)."""
    dq = q2 - q1
    dr = r2 - r1
    return (abs(dq) + abs(dr) + abs(dq + dr)) // 2
