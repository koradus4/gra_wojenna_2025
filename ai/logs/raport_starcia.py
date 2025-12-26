"""Raport z bitwy Human vs AI na podstawie rzeczywistych logów.

Analizuje logi z:
- ai/logs/human/ (CSV + TXT) - akcje gracza ludzkiego
- ai/logs/general/ (CSV + TXT) - decyzje Generała AI
- ai/logs/commander/ (CSV + TXT) - decyzje Dowódców AI
- ai/logs/tokens/ (CSV + TXT) - akcje żetonów AI

Generuje raport Markdown z porównaniem Human vs AI.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PlayerStats:
    """Statystyki jednego gracza (Human lub AI)."""
    
    player_name: str
    player_type: str  # "HUMAN" lub "AI"
    nation: str = "Nieznana"
    
    # Ruchy
    moves_total: int = 0
    moves_success: int = 0
    moves_failed: int = 0
    distance_total: int = 0
    mp_spent: int = 0
    fuel_spent: int = 0
    
    # Ataki
    attacks_planned: int = 0
    attacks_executed: int = 0
    attacks_success: int = 0
    attacks_failed: int = 0
    damage_dealt_total: int = 0
    damage_taken_total: int = 0
    counterattacks_received: int = 0
    units_destroyed: int = 0
    units_lost: int = 0
    
    # Ekonomia (AI tylko)
    pe_total: int = 0
    pe_spent_fuel: int = 0
    pe_spent_cv: int = 0
    pe_returned: int = 0
    pe_from_kp: int = 0
    
    # Kontrola terenu
    hexes_controlled: Dict[int, int] = field(default_factory=dict)  # turn -> count
    
    # Jednostki aktywne
    active_tokens: set = field(default_factory=set)
    destroyed_tokens: set = field(default_factory=set)
    
    # Tury
    turns_played: int = 0
    
    # Szczegóły ataków (dla topowych starć)
    attack_details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BattleReport:
    """Kompletny raport z bitwy."""
    
    human_stats: Optional[PlayerStats] = None
    ai_stats: Optional[PlayerStats] = None
    game_date: Optional[str] = None
    final_turn: int = 0
    victory: Optional[str] = None
    
    # Decyzje AI (General)
    ai_decisions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Błędy i ostrzeżenia
    errors: List[str] = field(default_factory=list)


def parse_csv_log(csv_path: Path, player_stats: PlayerStats) -> None:
    """Parsuje CSV log i wypełnia statystyki gracza."""
    
    if not csv_path.exists():
        return
    
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            action_type = row.get("action_type", "")
            success = row.get("result") not in ("", "None", None)
            turn = int(row.get("turn", 0) or 0)
            
            if turn > 0:
                player_stats.turns_played = max(player_stats.turns_played, turn)
            
            # Parsuj context JSON
            context_raw = row.get("context", "{}")
            try:
                context = json.loads(context_raw) if context_raw else {}
            except Exception:
                context = {}
            
            success_flag = context.get("success", True)
            
            # Ruchy
            if action_type == "move":
                player_stats.moves_total += 1
                if success_flag:
                    player_stats.moves_success += 1
                else:
                    player_stats.moves_failed += 1
                
                # Dystans
                start_pos = context.get("start_position")
                end_pos = context.get("end_position")
                if start_pos and end_pos and isinstance(start_pos, (list, tuple)) and isinstance(end_pos, (list, tuple)):
                    distance = abs(start_pos[0] - end_pos[0]) + abs(start_pos[1] - end_pos[1])
                    player_stats.distance_total += distance
                
                # Koszty
                path_cost = context.get("path_cost", 0) or 0
                fuel_cost = context.get("fuel_cost", 0) or 0
                player_stats.mp_spent += path_cost
                player_stats.fuel_spent += fuel_cost
                
                # Token ID
                token_id = context.get("token_id")
                if token_id:
                    player_stats.active_tokens.add(token_id)
            
            # Ataki
            elif action_type == "attack":
                player_stats.attacks_executed += 1
                
                if success_flag:
                    player_stats.attacks_success += 1
                else:
                    player_stats.attacks_failed += 1
                
                # Obrażenia
                damage_dealt = context.get("damage_dealt", 0) or 0
                damage_taken = context.get("damage_taken", 0) or 0
                
                if isinstance(damage_dealt, (int, float)):
                    player_stats.damage_dealt_total += int(damage_dealt)
                if isinstance(damage_taken, (int, float)):
                    player_stats.damage_taken_total += int(damage_taken)
                
                # Kontratak
                if context.get("counterattack"):
                    player_stats.counterattacks_received += 1
                
                # Token IDs
                token_id = context.get("token_id")
                target_id = context.get("target_token_id")
                if token_id:
                    player_stats.active_tokens.add(token_id)
                
                # Zniszczone jednostki
                defender_cv_after = context.get("defender_cv_after")
                attacker_cv_after = context.get("attacker_cv_after")
                
                if defender_cv_after == 0 or defender_cv_after is None:
                    summary = row.get("summary", "")
                    if "cel zniszczony" in summary.lower():
                        player_stats.units_destroyed += 1
                        if target_id:
                            player_stats.destroyed_tokens.add(target_id)
                
                if attacker_cv_after == 0 or attacker_cv_after is None:
                    summary = row.get("summary", "")
                    if "atakujący zniszczony" in summary.lower():
                        player_stats.units_lost += 1
                        if token_id:
                            player_stats.destroyed_tokens.add(token_id)
                
                # Zapisz szczegóły ataku
                attack_detail = {
                    "turn": turn,
                    "attacker": token_id,
                    "defender": target_id,
                    "success": success_flag,
                    "damage_dealt": damage_dealt,
                    "damage_taken": damage_taken,
                    "counterattack": context.get("counterattack", False),
                    "attacker_cv_before": context.get("attacker_cv_before"),
                    "attacker_cv_after": context.get("attacker_cv_after"),
                    "defender_cv_before": context.get("defender_cv_before"),
                    "defender_cv_after": context.get("defender_cv_after"),
                }
                player_stats.attack_details.append(attack_detail)


def parse_ai_general_log(csv_path: Path, ai_stats: PlayerStats, report: BattleReport) -> None:
    """Parsuje logi Generała AI (decyzje strategiczne)."""
    
    if not csv_path.exists():
        return
    
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            message = row.get("message", "")
            context_raw = row.get("context", "{}")
            
            try:
                context = json.loads(context_raw) if context_raw else {}
            except Exception:
                context = {}
            
            # PE pozyskane
            if "Dostępne PE:" in message:
                pe_match = re.search(r"Dostępne PE:\s*(\d+)", message)
                if pe_match:
                    ai_stats.pe_total += int(pe_match.group(1))
            
            # PE z KP
            if "przydział PE z KP" in message.lower():
                pe_gain = context.get("pe_gain", 0)
                if pe_gain:
                    ai_stats.pe_from_kp += pe_gain
            
            # Decyzje strategiczne
            if any(keyword in message.lower() for keyword in ["decyzja", "strategy", "plan", "priority"]):
                decision = {
                    "timestamp": row.get("timestamp"),
                    "message": message,
                    "level": row.get("level"),
                    "context": context,
                }
                report.ai_decisions.append(decision)
            
            # Błędy
            if row.get("level") == "ERROR":
                report.errors.append(f"[GENERAL] {message}")


def parse_ai_tokens_log_text(text_path: Path, ai_stats: PlayerStats) -> None:
    """Parsuje tekstowe logi żetonów AI (zaopatrzenie, ataki)."""
    
    if not text_path.exists():
        return
    
    with text_path.open("r", encoding="utf-8") as f:
        for line in f:
            # Uzupełnianie paliwa
            if "uzupełnia paliwo" in line:
                match = re.search(r"uzupełnia paliwo o (\d+)", line)
                if match:
                    ai_stats.pe_spent_fuel += int(match.group(1))
            
            # Uzupełnianie CV
            if "uzupełnia CV" in line:
                match = re.search(r"uzupełnia CV o (\d+)", line)
                if match:
                    ai_stats.pe_spent_cv += int(match.group(1))
            
            # Zwrócone PE
            if "reserved_pe=" in line or "unused_pe=" in line:
                match = re.search(r"(?:reserved_pe|unused_pe)=(\d+)", line)
                if match:
                    ai_stats.pe_returned += int(match.group(1))
            
            # Planowane ataki
            if "planned_actions=" in line and "attack" in line:
                ai_stats.attacks_planned += 1


def analyze_survival_mechanics(human_stats: PlayerStats, ai_stats: PlayerStats) -> Dict[str, Any]:
    """Analizuje mechanikę przetrwania jednostek z minimalnym CV."""
    
    survival_data = {
        "units_with_1cv": [],  # Jednostki które miały 1 CV
        "miraculous_survivals": [],  # Jednostki które przeżyły wielokrotnie z 1 CV
        "cv_recoveries": [],  # Jednostki które odzyskały CV po zejściu do 1
        "retreat_after_damage": [],  # Jednostki które się wycofały po obrażeniach
    }
    
    # Śledź historię CV dla każdej jednostki
    unit_cv_history = {}  # token_id -> [(turn, cv_before, cv_after, position)]
    
    for attack in human_stats.attack_details:
        defender_id = attack.get("defender")
        if not defender_id:
            continue
        
        turn = attack.get("turn", 0)
        cv_before = attack.get("defender_cv_before")
        cv_after = attack.get("defender_cv_after")
        position_before = attack.get("defender_position_before")
        position_after = attack.get("defender_position_after")
        
        if defender_id not in unit_cv_history:
            unit_cv_history[defender_id] = []
        
        unit_cv_history[defender_id].append({
            "turn": turn,
            "cv_before": cv_before,
            "cv_after": cv_after,
            "damage_taken": attack.get("damage_dealt", 0),
            "position_before": position_before,
            "position_after": position_after,
            "attacker": attack.get("attacker"),
        })
    
    # Analiza wzorców
    for unit_id, history in unit_cv_history.items():
        # Sortuj po turze
        history.sort(key=lambda x: x.get("turn", 0))
        
        survivals_at_1cv = 0
        last_cv = None
        recovered_from_1cv = False
        retreated_after_damage = False
        
        for i, entry in enumerate(history):
            cv_after = entry.get("cv_after")
            cv_before = entry.get("cv_before")
            pos_before = entry.get("position_before")
            pos_after = entry.get("position_after")
            
            # Czy przeżył z 1 CV?
            if cv_after == 1:
                survivals_at_1cv += 1
                survival_data["units_with_1cv"].append({
                    "unit": unit_id,
                    "turn": entry.get("turn"),
                    "damage": entry.get("damage_taken"),
                    "attacker": entry.get("attacker"),
                })
            
            # Czy odzyskał CV po zejściu do 1?
            if last_cv == 1 and cv_before is not None and cv_before > 1:
                recovered_from_1cv = True
                survival_data["cv_recoveries"].append({
                    "unit": unit_id,
                    "recovered_from": 1,
                    "recovered_to": cv_before,
                    "turn": entry.get("turn"),
                })
            
            # Czy się wycofał po obrażeniach?
            if pos_before and pos_after and pos_before != pos_after:
                if cv_after is not None and cv_after <= 3:
                    retreated_after_damage = True
                    survival_data["retreat_after_damage"].append({
                        "unit": unit_id,
                        "turn": entry.get("turn"),
                        "cv_after": cv_after,
                        "from": pos_before,
                        "to": pos_after,
                    })
            
            last_cv = cv_after
        
        # Cuda przetrwania (>=2 razy z 1 CV)
        if survivals_at_1cv >= 2:
            survival_data["miraculous_survivals"].append({
                "unit": unit_id,
                "survivals": survivals_at_1cv,
                "recovered": recovered_from_1cv,
                "retreated": retreated_after_damage,
            })
    
    return survival_data


def generate_markdown_report(report: BattleReport) -> str:
    """Generuje raport w formacie Markdown."""
    
    lines = []
    h = report.human_stats
    a = report.ai_stats
    
    # Nagłówek
    lines.append("# 🎯 RAPORT STARCIA: Human vs AI")
    if report.game_date:
        lines.append(f"**Data gry:** {report.game_date}")
    if report.final_turn:
        lines.append(f"**Tura końcowa:** {report.final_turn}")
    if report.victory:
        lines.append(f"**Zwycięzca:** {report.victory}")
    
    lines.append("\n---\n")
    
    # Statystyki ogólne
    lines.append("## 📈 STATYSTYKI OGÓLNE\n")
    
    if h and a:
        human_name = f"{h.nation} ({h.player_type})" if h.nation != "Nieznana" else h.player_type
        ai_name = f"{a.nation} ({a.player_type})" if a.nation != "Nieznana" else a.player_type
        
        lines.append("| Metryka | Human | AI |")
        lines.append("|---------|-------|-----|")
        lines.append(f"| **Tury rozegrane** | {h.turns_played} | {a.turns_played} |")
        
        h_units_start = len(h.active_tokens) + len(h.destroyed_tokens)
        a_units_start = len(a.active_tokens) + len(a.destroyed_tokens)
        h_units_end = len(h.active_tokens)
        a_units_end = len(a.active_tokens)
        
        lines.append(f"| **Żetony aktywne** | {h_units_end} | {a_units_end} |")
        lines.append(f"| **Żetony stracone** | {len(h.destroyed_tokens)} | {len(a.destroyed_tokens)} |")
        
        if h_units_start > 0 and a_units_start > 0:
            h_survival = (h_units_end / h_units_start) * 100
            a_survival = (a_units_end / a_units_start) * 100
            lines.append(f"| **Współczynnik przetrwania** | {h_survival:.0f}% | {a_survival:.0f}% |")
        elif h_units_start > 0:
            h_survival = (h_units_end / h_units_start) * 100
            lines.append(f"| **Współczynnik przetrwania** | {h_survival:.0f}% | N/A |")
        elif a_units_start > 0:
            a_survival = (a_units_end / a_units_start) * 100
            lines.append(f"| **Współczynnik przetrwania** | N/A | {a_survival:.0f}% |")
        
        lines.append(f"| **Ruchy wykonane** | {h.moves_total} | {a.moves_total} |")
        lines.append(f"| **Ataki wykonane** | {h.attacks_executed} | {a.attacks_executed} |")
    
    lines.append("\n---\n")
    
    # Ekonomia (AI)
    if a and (a.pe_total or a.pe_spent_fuel or a.pe_spent_cv):
        lines.append("<details>")
        lines.append("<summary>💰 EKONOMIA I ZASOBY (AI)</summary>\n")
        lines.append(f"- **PE pozyskane:** {a.pe_total}")
        lines.append(f"- **PE z kluczowych punktów:** {a.pe_from_kp}")
        lines.append(f"- **Wydane na paliwo:** {a.pe_spent_fuel}")
        lines.append(f"- **Wydane na CV:** {a.pe_spent_cv}")
        
        total_spent = a.pe_spent_fuel + a.pe_spent_cv
        if a.pe_total > 0:
            percent_spent = (total_spent / a.pe_total) * 100
            lines.append(f"- **Wydane łącznie:** {total_spent} ({percent_spent:.1f}% pozyskanych)")
        
        if a.pe_returned:
            percent_returned = (a.pe_returned / a.pe_total) * 100 if a.pe_total else 0
            lines.append(f"- **Zwrócone:** {a.pe_returned} ({percent_returned:.1f}% pozyskanych)")
        
        lines.append("\n</details>\n")
    
    # Ruchy
    lines.append("<details>")
    lines.append("<summary>🚀 RUCHY I MANEWRY</summary>\n")
    
    if h:
        lines.append(f"### {h.nation} (Human)")
        lines.append(f"- Łącznie ruchów: {h.moves_total}")
        if h.moves_total:
            success_rate = (h.moves_success / h.moves_total) * 100
            lines.append(f"- Skuteczność: {success_rate:.1f}% ({h.moves_success} sukces / {h.moves_failed} błąd)")
        lines.append(f"- Dystans pokonany: {h.distance_total} heksów")
        lines.append(f"- MP zużyte: {h.mp_spent}")
        lines.append(f"- Paliwo zużyte: {h.fuel_spent}")
        if h.turns_played:
            avg_moves = h.moves_total / h.turns_played
            lines.append(f"- Średnio ruchów/turę: {avg_moves:.1f}")
    
    if a:
        lines.append(f"\n### {a.nation} (AI)")
        lines.append(f"- Łącznie ruchów: {a.moves_total}")
        if a.moves_total:
            success_rate = (a.moves_success / a.moves_total) * 100
            lines.append(f"- Skuteczność: {success_rate:.1f}% ({a.moves_success} sukces / {a.moves_failed} błąd)")
        lines.append(f"- Dystans pokonany: {a.distance_total} heksów")
        lines.append(f"- MP zużyte: {a.mp_spent}")
        if a.turns_played:
            avg_moves = a.moves_total / a.turns_played
            lines.append(f"- Średnio ruchów/turę: {avg_moves:.1f}")
    
    lines.append("\n</details>\n")
    
    # Ataki
    lines.append("<details>")
    lines.append("<summary>⚔️ ANALIZA WALK</summary>\n")
    
    lines.append("### Statystyki bojowe\n")
    lines.append("| Akcja | Human | AI |")
    lines.append("|-------|-------|-----|")
    
    if h and a:
        lines.append(f"| **Ataki wykonane** | {h.attacks_executed} | {a.attacks_executed} |")
        
        h_success_rate = (h.attacks_success / h.attacks_executed * 100) if h.attacks_executed else 0
        a_success_rate = (a.attacks_success / a.attacks_executed * 100) if a.attacks_executed else 0
        lines.append(f"| **Ataki skuteczne** | {h.attacks_success} ({h_success_rate:.0f}%) | {a.attacks_success} ({a_success_rate:.0f}%) |")
        
        lines.append(f"| **Jednostki zniszczone** | {h.units_destroyed} | {a.units_destroyed} |")
        lines.append(f"| **Jednostki stracone** | {len(h.destroyed_tokens)} | {len(a.destroyed_tokens)} |")
        lines.append(f"| **Obrażenia zadane** | {h.damage_dealt_total} | {a.damage_dealt_total} |")
        lines.append(f"| **Obrażenia otrzymane** | {h.damage_taken_total} | {a.damage_taken_total} |")
        
        h_avg_dmg = h.damage_dealt_total / h.attacks_success if h.attacks_success else 0
        a_avg_dmg = a.damage_dealt_total / a.attacks_success if a.attacks_success else 0
        lines.append(f"| **Średnie obrażenia/atak** | {h_avg_dmg:.1f} | {a_avg_dmg:.1f} |")
        
        lines.append(f"| **Kontrataki otrzymane** | {h.counterattacks_received} | {a.counterattacks_received} |")
    
    # Topowe starcia
    lines.append("\n### 🏆 Najważniejsze starcia\n")
    
    all_attacks = []
    if h:
        for attack in h.attack_details:
            attack["player"] = "Human"
            all_attacks.append(attack)
    if a:
        for attack in a.attack_details:
            attack["player"] = "AI"
            all_attacks.append(attack)
    
    # Sortuj po największych obrażeniach
    top_attacks = sorted(all_attacks, key=lambda x: x.get("damage_dealt", 0) or 0, reverse=True)[:5]
    
    for i, attack in enumerate(top_attacks, 1):
        lines.append(f"**{i}. Tura {attack['turn']}**")
        lines.append("```")
        lines.append(f"Atakujący: {attack['player']} - {attack['attacker']}")
        lines.append(f"Obrońca: {attack['defender']}")
        lines.append(f"Wynik: {'Sukces' if attack['success'] else 'Porażka'}")
        lines.append(f"Obrażenia zadane: {attack.get('damage_dealt', 0)}")
        lines.append(f"Obrażenia otrzymane: {attack.get('damage_taken', 0)}")
        
        cv_before = attack.get('defender_cv_before')
        cv_after = attack.get('defender_cv_after')
        if cv_before is not None and cv_after is not None:
            lines.append(f"CV obrońcy: {cv_before} → {cv_after}")
            if cv_after == 0:
                lines.append("Status: ZNISZCZONY")
        
        lines.append("```\n")
    
    lines.append("</details>\n")
    
    # Decyzje AI
    if report.ai_decisions:
        lines.append("<details>")
        lines.append(f"<summary>🧠 DECYZJE STRATEGICZNE (AI) - {len(report.ai_decisions)} wpisów</summary>\n")
        
        for decision in report.ai_decisions[:10]:  # Top 10
            timestamp = decision.get("timestamp", "")
            message = decision.get("message", "")
            level = decision.get("level", "INFO")
            
            symbol = "❌" if level == "ERROR" else "⚠️" if level == "WARNING" else "ℹ️"
            lines.append(f"{symbol} `{timestamp}` - {message}")
        
        lines.append("\n</details>\n")
    
    # Analiza przetrwania
    if h and a:
        survival_data = analyze_survival_mechanics(h, a)
        
        if survival_data["units_with_1cv"] or survival_data["miraculous_survivals"]:
            lines.append("<details>")
            lines.append("<summary>🍀 ANALIZA PRZETRWANIA - Jednostki z 1 CV</summary>\n")
            
            # Cuda przetrwania
            if survival_data["miraculous_survivals"]:
                lines.append("### 🎲 CUDOWNE PRZETRWANIA (≥2 razy z 1 CV)\n")
                
                # Info box o mechanice
                lines.append("> **ℹ️ Mechanika:** Jednostki mają 50% szans na przetrwanie z 1 CV gdy HP spadnie do 0.")
                lines.append("> Prawdopodobieństwa: 2x = 25%, 3x = 12.5%, 4x = 6.25%, 5x = 3.125%\n")
                
                for miracle in survival_data["miraculous_survivals"]:
                    unit = miracle["unit"]
                    count = miracle["survivals"]
                    recovered = "✅ Odzyskał CV" if miracle["recovered"] else "❌ Nie odzyskał CV"
                    retreated = "✅ Wycofał się" if miracle["retreated"] else "❌ Nie wycofał się"
                    
                    # Oblicz prawdopodobieństwo
                    probability = (0.5 ** count) * 100
                    
                    # Ostrzeżenie dla bardzo rzadkich przypadków
                    warning = ""
                    if count >= 4:
                        warning = " ⚠️ **BARDZO RZADKIE!**"
                    elif count >= 3:
                        warning = " ⚠️ Rzadkie"
                    
                    lines.append(f"**{unit}**{warning}")
                    lines.append(f"- Przetrwał z 1 CV: **{count} razy** 🎯 (prawdopodobieństwo: {probability:.2f}%)")
                    lines.append(f"- {recovered}")
                    lines.append(f"- {retreated}")
                    lines.append("")
            
            # Odzyskanie CV
            if survival_data["cv_recoveries"]:
                lines.append("### 💚 ODZYSKANIE CV\n")
                for recovery in survival_data["cv_recoveries"][:5]:
                    unit = recovery["unit"]
                    from_cv = recovery["recovered_from"]
                    to_cv = recovery["recovered_to"]
                    turn = recovery["turn"]
                    lines.append(f"- **{unit}** (tura {turn}): {from_cv} CV → {to_cv} CV ✨")
            
            # Wycofania
            if survival_data["retreat_after_damage"]:
                lines.append("\n### 🏃 WYCOFANIA PO OBRAŻENIACH\n")
                for retreat in survival_data["retreat_after_damage"][:5]:
                    unit = retreat["unit"]
                    turn = retreat["turn"]
                    cv = retreat["cv_after"]
                    from_pos = retreat["from"]
                    to_pos = retreat["to"]
                    lines.append(f"- **{unit}** (tura {turn}, CV={cv}): `{from_pos}` → `{to_pos}` 🚩")
            
            # Wszystkie przypadki 1 CV
            if survival_data["units_with_1cv"]:
                lines.append(f"\n### 📊 WSZYSTKIE PRZYPADKI 1 CV ({len(survival_data['units_with_1cv'])})\n")
                for case in survival_data["units_with_1cv"][:10]:
                    unit = case["unit"]
                    turn = case["turn"]
                    dmg = case["damage"]
                    attacker = case["attacker"]
                    lines.append(f"- Tura {turn}: **{unit}** otrzymał {dmg} obrażeń od `{attacker}` → przetrwał z 1 CV")
            
            # Statystyki ogólne
            if survival_data["miraculous_survivals"] or survival_data["cv_recoveries"]:
                lines.append("\n### 📈 PODSUMOWANIE STATYSTYCZNE\n")
                
                total_units_with_multiple_survivals = len(survival_data["miraculous_survivals"])
                total_recoveries = len(survival_data["cv_recoveries"])
                total_retreats = len(survival_data["retreat_after_damage"])
                
                lines.append(f"- **Jednostki z wielokrotnym przetrwaniem:** {total_units_with_multiple_survivals}")
                lines.append(f"- **Odzyskania CV:** {total_recoveries}")
                lines.append(f"- **Wycofania po obrażeniach:** {total_retreats}")
                
                if survival_data["miraculous_survivals"]:
                    max_survivals = max(m["survivals"] for m in survival_data["miraculous_survivals"])
                    max_prob = (0.5 ** max_survivals) * 100
                    lines.append(f"\n**🎯 Rekordowe przetrwanie:** {max_survivals}x z 1 CV (szansa: {max_prob:.3f}%)")
                
                # Wnioski
                lines.append("\n**💡 Wnioski:**")
                if total_recoveries > 0:
                    lines.append("- ✅ System uzupełniania CV działa poprawnie")
                if total_retreats > 0:
                    lines.append("- ✅ Mechanika wycofania się po obrażeniach funkcjonuje")
                if survival_data["miraculous_survivals"]:
                    avg_survivals = sum(m["survivals"] for m in survival_data["miraculous_survivals"]) / len(survival_data["miraculous_survivals"])
                    if avg_survivals >= 3:
                        lines.append("- ⚠️ Niektóre jednostki miały **wyjątkowo dużo szczęścia** w losowaniach")
                    else:
                        lines.append("- ℹ️ Wielokrotne przetrwania mieszczą się w normie statystycznej")
            
            lines.append("\n</details>\n")
    
    # Błędy
    if report.errors:
        lines.append("<details>")
        lines.append(f"<summary>⚠️ BŁĘDY I OSTRZEŻENIA ({len(report.errors)})</summary>\n")
        
        for error in report.errors[:20]:
            lines.append(f"- {error}")
        
        lines.append("\n</details>\n")
    
    # Podsumowanie
    lines.append("## 🏁 PODSUMOWANIE\n")
    
    if h and a:
        # Kto wygrał w poszczególnych kategoriach
        lines.append("### Kategorie zwycięstw\n")
        
        categories = []
        
        if h.attacks_success > a.attacks_success:
            categories.append("✅ **Human** - Więcej skutecznych ataków")
        elif a.attacks_success > h.attacks_success:
            categories.append("❌ **AI** - Więcej skutecznych ataków")
        
        if h.units_destroyed > a.units_destroyed:
            categories.append("✅ **Human** - Więcej zniszczonych jednostek przeciwnika")
        elif a.units_destroyed > h.units_destroyed:
            categories.append("❌ **AI** - Więcej zniszczonych jednostek przeciwnika")
        
        if len(h.destroyed_tokens) < len(a.destroyed_tokens):
            categories.append("✅ **Human** - Mniejsze straty własne")
        elif len(a.destroyed_tokens) < len(h.destroyed_tokens):
            categories.append("❌ **AI** - Mniejsze straty własne")
        
        if h.damage_dealt_total > a.damage_dealt_total:
            categories.append("✅ **Human** - Większe obrażenia zadane")
        elif a.damage_dealt_total > h.damage_dealt_total:
            categories.append("❌ **AI** - Większe obrażenia zadane")
        
        for cat in categories:
            lines.append(f"- {cat}")
    
    lines.append(f"\n---\n")
    lines.append(f"**Wygenerowano:** {report.game_date or 'nieznana data'}")
    lines.append("**Źródło logów:** `ai/logs/human/`, `ai/logs/general/`, `ai/logs/commander/`, `ai/logs/tokens/`")
    
    return "\n".join(lines)


def find_latest_logs(base_dir: Path) -> Dict[str, Path]:
    """Znajduje najnowsze pliki logów."""
    
    logs = {}
    
    # Human CSV
    human_csv_dir = base_dir / "human" / "csv"
    if human_csv_dir.exists():
        csv_files = sorted(human_csv_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        if csv_files:
            logs["human_csv"] = csv_files[0]
    
    # AI General CSV
    general_csv_dir = base_dir / "general" / "csv"
    if general_csv_dir.exists():
        csv_files = sorted(general_csv_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        if csv_files:
            logs["general_csv"] = csv_files[0]
    
    # AI Tokens TXT
    tokens_txt_dir = base_dir / "tokens" / "text"
    if tokens_txt_dir.exists():
        txt_files = sorted(tokens_txt_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if txt_files:
            logs["tokens_txt"] = txt_files[0]
    
    return logs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generator raportu bitwy Human vs AI na podstawie logów"
    )
    parser.add_argument(
        "--logs-dir",
        default="ai/logs",
        help="Katalog bazowy z logami (domyślnie: ai/logs)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Ścieżka do pliku wyjściowego .md (domyślnie: ai/logs/human/raporty/<data>_raport_starcia.md)",
    )
    args = parser.parse_args()
    
    base_dir = Path(args.logs_dir)
    if not base_dir.exists():
        raise SystemExit(f"❌ Katalog z logami nie istnieje: {base_dir}")
    
    # Znajdź najnowsze logi
    logs = find_latest_logs(base_dir)
    
    if not logs:
        raise SystemExit(f"❌ Nie znaleziono żadnych logów w {base_dir}")
    
    print("📂 Znalezione logi:")
    for key, path in logs.items():
        print(f"  - {key}: {path.name}")
    
    # Inicjalizuj raport
    report = BattleReport()
    human_stats = PlayerStats(player_name="Human", player_type="HUMAN")
    ai_stats = PlayerStats(player_name="AI", player_type="AI")
    
    # Parsuj logi
    if "human_csv" in logs:
        print("\n🔍 Parsowanie logów Human...")
        parse_csv_log(logs["human_csv"], human_stats)
        report.game_date = logs["human_csv"].stem
        
        # Wykryj narodowość
        if human_stats.active_tokens:
            # Próbuj wykryć z pierwszego tokena
            first_token = list(human_stats.active_tokens)[0]
            if "POL" in first_token or "P_" in first_token:
                human_stats.nation = "Polska"
    
    if "general_csv" in logs:
        print("🔍 Parsowanie logów AI General...")
        parse_ai_general_log(logs["general_csv"], ai_stats, report)
        
        # Wykryj narodowość AI
        if ai_stats.active_tokens:
            first_token = list(ai_stats.active_tokens)[0]
            if "GER" in first_token or "G_" in first_token:
                ai_stats.nation = "Niemcy"
    
    if "tokens_txt" in logs:
        print("🔍 Parsowanie logów AI Tokens...")
        parse_ai_tokens_log_text(logs["tokens_txt"], ai_stats)
    
    # Uzupełnij raport
    report.human_stats = human_stats
    report.ai_stats = ai_stats
    report.final_turn = max(human_stats.turns_played, ai_stats.turns_played)
    
    # Generuj raport
    print("\n📝 Generowanie raportu...")
    markdown = generate_markdown_report(report)
    
    # Zapisz raport
    if args.output:
        output_path = Path(args.output)
    else:
        report_dir = base_dir / "human" / "raporty"
        report_dir.mkdir(parents=True, exist_ok=True)
        output_path = report_dir / f"{report.game_date or 'najnowszy'}_raport_starcia.md"
    
    output_path.write_text(markdown, encoding="utf-8")
    print(f"\n✅ Raport zapisany: {output_path}")
    print(f"📊 Statystyki:")
    print(f"  - Human: {human_stats.attacks_executed} ataków, {human_stats.moves_total} ruchów")
    print(f"  - AI: {ai_stats.attacks_executed} ataków, {ai_stats.moves_total} ruchów")
    print(f"  - Decyzje AI: {len(report.ai_decisions)}")
    print(f"  - Błędy: {len(report.errors)}")


if __name__ == "__main__":
    main()
