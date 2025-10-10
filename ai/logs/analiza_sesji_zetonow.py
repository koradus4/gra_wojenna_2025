"""Szybki raport z logów AI dotyczących autonomicznych żetonów.

Skrypt odczytuje plik tekstowy z katalogu `ai/logs/tokens/text`,
drukuje podsumowanie w terminalu oraz zapisuje ten sam raport w
`ai/logs/tokens/text/raporty/<nazwa_logu>_raport.txt`. Wygenerowane
pliki są objęte standardowym czyszczeniem przez `ai/logs/czyszczenie_logow.py`.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


RE_START_TURY = re.compile(r"status=([^,]+).+planned_actions=\[(.*)\]")
RE_PODSUMOWANIE = re.compile(
    r"movement_success=(True|False).*movement_attempts=(\d+).+resupply_spent=(\d+).+reserved_pe=(\d+)"
)
RE_ATTACK = re.compile(r"atak na .+success=(True|False).+damage_dealt=([\d-]+).+damage_taken=([\d-]+)")
RE_UZUPELNIANIE_PALIWA = re.compile(r"uzupełnia paliwo o (\d+)")
RE_UZUPELNIANIE_CV = re.compile(r"uzupełnia CV o (\d+)")
RE_HOLD = re.compile(r"hold_position=(True|False)")
RE_STATUS = re.compile(r"status=([^,|]+)")
RE_MODE = re.compile(r"movement_mode=([a-zA-Z_]+)")
RE_ATTEMPT = re.compile(r"attack_attempted=(True|False)")
RE_DISTANCE_TOTAL = re.compile(r"movement_distance_total=([\d-]+)")
RE_MP_SPENT = re.compile(r"movement_mp_spent=([\d-]+)")
RE_STEP_DISTANCE = re.compile(r"movement_step_distance=([\d-]+)")
RE_STEP_MP = re.compile(r"mp_spent=([\d-]+)")
RE_TOKEN_PREFIX = re.compile(r"\[TOKEN\]\s+([^:]+):")
RE_RYZYKOWNY = re.compile(
    r"ryzykowny atak na .*?ratio=([\d.]+).*?ratio_adjusted=([\d.]+).*?detection=([\d.]+).*?support=(True|False)",
    re.IGNORECASE,
)
RE_AGRESYWNY = re.compile(
    r"agresywny atak .*?ratio=([\d.]+).*?ratio_adjusted=([\d.]+).*?detection=([\d.]+).*?support=(True|False)",
    re.IGNORECASE,
)
RE_KEY_VALUE = re.compile(r"(\w+)=([^,\s]+)")

TOKEN_ASSETS_ROOT = Path("assets/tokens")
GENERAL_CSV_DIR = Path("ai/logs/general/csv")
COMMANDER_CSV_DIR = Path("ai/logs/commander/csv")
TOKEN_NATION_CACHE: dict[str, str] = {}
FALLBACK_PREFIX_MAP = {
    "P": "Piechota",
    "Z": "Zaopatrzenie",
    "R": "Zwiad",
    "AC": "Artyleria ciężka",
    "AL": "Artyleria lekka",
    "K": "Kawaleria",
    "TC": "Czołg ciężki",
    "TS": "Czołg średni",
    "TŚ": "Czołg średni",
}

STATUS_TRANSLATIONS: Dict[str, str] = {
    "attack": "atak",
    "combat": "walka",
    "hold": "utrzymanie pozycji",
    "idle": "bezczynność",
    "move": "ruch",
    "recover": "odbudowa",
    "resupply": "uzupełnianie",
    "retreat": "odwrót",
}

MODE_TRANSLATIONS: Dict[str, str] = {
    "assault": "szturm",
    "fallback": "odwrót na tyły",
    "hold": "utrzymanie pozycji",
    "move": "ruch",
    "retreat": "odwrót",
    "supply_run": "misja zaopatrzeniowa",
}

ACTION_TRANSLATIONS: Dict[str, str] = {
    "attack": "atak",
    "hold_position": "utrzymanie pozycji",
    "maneuver": "manewr",
    "move": "ruch",
    "recover_garrison": "odbudowa garnizonu",
    "refuel_minimum": "tankowanie minimalne",
    "regroup": "przegrupowanie",
    "resupply": "uzupełnienie zaopatrzenia",
    "restore_cv": "odbudowa CV",
    "withdraw": "wycofanie",
}

ACTION_PROFILE_TRANSLATIONS: Dict[str, str] = {
    "attack": "atak",
    "fallback": "odwrót na tyły",
    "hold": "utrzymanie",
    "move": "ruch",
    "recover": "odbudowa",
    "resupply": "uzupełnienie",
    "retreat": "odwrót",
}

SPECIALIST_TRANSLATIONS: Dict[str, str] = {
    "ArtillerySpecialist": "Artyleria",
    "AssaultSpecialist": "Szturm",
    "DefenseSpecialist": "Obrona",
    "GenericSpecialist": "Standardowy",
    "ReconSpecialist": "Rozpoznanie",
    "SupplySpecialist": "Zaopatrzenie",
}


def _find_latest_csv(path: Path) -> Optional[Path]:
    if path.is_file():
        return path
    if not path.exists():
        return None
    candidates = sorted(path.glob("*.csv"))
    return candidates[-1] if candidates else None


def _load_csv_rows(csv_path: Path) -> Iterable[Dict[str, str]]:
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def _parse_context_json(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _collect_purchase_summary() -> list[Dict[str, Any]]:
    purchases: list[Dict[str, Any]] = []
    general_csv = _find_latest_csv(GENERAL_CSV_DIR)
    if general_csv and general_csv.exists():
        for row in _load_csv_rows(general_csv):
            if row.get("message") != "Zakupiono jednostkę":
                continue
            context = _parse_context_json(row.get("context"))
            token_id = context.get("token_id")
            if not token_id:
                continue
            purchases.append(
                {
                    "timestamp": row.get("timestamp"),
                    "turn": context.get("turn"),
                    "commander_id": context.get("commander_id"),
                    "token_id": token_id,
                    "unit_type": context.get("unit_type"),
                    "unit_size": context.get("unit_size"),
                    "category": context.get("category"),
                    "focus": context.get("focus"),
                    "cost": context.get("cost"),
                    "folder": context.get("folder"),
                }
            )

    if not purchases:
        return []

    deployments: Dict[str, Dict[str, Any]] = {}
    commander_csv = _find_latest_csv(COMMANDER_CSV_DIR)
    if commander_csv and commander_csv.exists():
        for row in _load_csv_rows(commander_csv):
            if row.get("message") != "Wystawiono wzmocnienie":
                continue
            context = _parse_context_json(row.get("context"))
            token_id = context.get("token_id")
            if not token_id:
                continue
            deployments[str(token_id)] = {
                "timestamp": row.get("timestamp"),
                "commander_id": context.get("commander_id"),
                "spawn_q": context.get("spawn_q"),
                "spawn_r": context.get("spawn_r"),
                "cost": context.get("cost"),
            }

    for purchase in purchases:
        token_id = str(purchase.get("token_id"))
        deployment = deployments.get(token_id)
        if deployment:
            purchase["deployed"] = True
            purchase["spawn_q"] = deployment.get("spawn_q")
            purchase["spawn_r"] = deployment.get("spawn_r")
            purchase["deployment_commander_id"] = deployment.get("commander_id")
        else:
            purchase["deployed"] = False

    return purchases


def format_with_translation(key: str, mapping: Dict[str, str]) -> str:
    if not key:
        return key
    translation = mapping.get(key)
    return f"{key} ({translation})" if translation else key


def _resolve_token_nation(token_id: str) -> Optional[str]:
    if token_id in TOKEN_NATION_CACHE:
        return TOKEN_NATION_CACHE[token_id]

    if TOKEN_ASSETS_ROOT.exists():
        for nation_dir in TOKEN_ASSETS_ROOT.iterdir():
            if not nation_dir.is_dir():
                continue
            candidate = nation_dir / token_id / "token.json"
            if candidate.exists():
                try:
                    data = json.loads(candidate.read_text(encoding="utf-8"))
                except Exception:
                    nation = nation_dir.name
                else:
                    nation = data.get("nation") or nation_dir.name
                TOKEN_NATION_CACHE[token_id] = nation
                return nation
    return None


@dataclass
class MetrykiSesji:
    liczba_tur: int = 0
    ruchy_skuteczne: int = 0
    ruchy_proby: int = 0
    pe_dostepne: int = 0
    resupply_wydane: int = 0
    pe_zwrocone: int = 0
    pe_z_kp: int = 0
    paliwo_dodane: int = 0
    cv_dodane: int = 0
    hold_position: int = 0
    hold_reasons: Counter[str] = field(default_factory=Counter)
    planowane_ataki: int = 0
    ataki_wykonane: int = 0
    ataki_sukcesy: int = 0
    ataki_porazki: int = 0
    obrazenia_zadane_suma: int = 0
    obrazenia_zadane_licznik: int = 0
    obrazenia_zadane_max: int = 0
    obrazenia_przyjete_suma: int = 0
    obrazenia_przyjete_licznik: int = 0
    obrazenia_przyjete_max: int = 0
    kontrataki: int = 0
    ataki_z_wsparciem: int = 0
    ataki_bez_wsparcia: int = 0
    ryzykowne_ataki: int = 0
    ryzykowne_sukcesy: int = 0
    agresywne_ataki: int = 0
    agresywne_sukcesy: int = 0
    detekcja_suma: float = 0.0
    detekcja_probki: int = 0
    ratio_suma: float = 0.0
    ratio_adj_suma: float = 0.0
    dystans_ruchu_suma: int = 0
    mp_wydane_suma: int = 0
    braki_movement_mode: int = 0
    kroki_ruchu: int = 0
    dystans_krokow_suma: int = 0
    mp_krokow_suma: int = 0
    tury_z_ruchem: int = 0
    max_dystans_tury: int = 0


@dataclass
class SpecialistStats:
    tury: int = 0
    profile: Counter[str] = field(default_factory=Counter)
    planowane_akcje: Counter[str] = field(default_factory=Counter)
    statusy: Counter[str] = field(default_factory=Counter)
    holdy: int = 0
    ruchy_udane: int = 0
    paliwo: int = 0
    cv: int = 0
    uwagi: Counter[str] = field(default_factory=Counter)


@dataclass
class WynikiAnalizy:
    metryki: MetrykiSesji
    zaplanowane_akcje: Counter
    statusy_start: Counter
    statusy_koniec: Counter
    podsumowanie_walk: Counter
    tryby_ruchu: Counter
    kroki_dystanse: Counter
    dystanse_na_ture: Counter
    per_nacje: dict[str, dict[str, int]] = field(default_factory=dict)
    human_notes: list[str] = field(default_factory=list)
    specjalisci: dict[str, SpecialistStats] = field(default_factory=dict)
    plany_ataku: list[Dict[str, Any]] = field(default_factory=list)
    zakupione_zetony: list[Dict[str, Any]] = field(default_factory=list)


def analizuj_linie(linie: Iterable[str]) -> WynikiAnalizy:
    metryki = MetrykiSesji()
    zaplanowane_akcje: Counter[str] = Counter()
    statusy_start: Counter[str] = Counter()
    statusy_koniec: Counter[str] = Counter()
    podsumowanie_walk: Counter[str] = Counter()
    tryby_ruchu: Counter[str] = Counter()
    kroki_dystanse: Counter[int] = Counter()
    dystanse_na_ture: Counter[int] = Counter()
    oczekujace_decyzje: dict[str, dict[str, object]] = {}
    plany_ataku: list[Dict[str, Any]] = []
    per_nacje: dict[str, dict[str, int]] = {}
    paliwo_debug_total = 0
    cv_debug_total = 0
    paliwo_debug_per: Counter[str] = Counter()
    cv_debug_per: Counter[str] = Counter()
    human_notes: list[str] = []
    pending_attack_line: Optional[str] = None
    specjalisci: defaultdict[str, SpecialistStats] = defaultdict(SpecialistStats)

    def parse_int(value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        value = value.strip()
        if value in {"None", "null", "nan", ""}:
            return None
        try:
            return int(value)
        except ValueError:
            try:
                return int(float(value))
            except ValueError:
                return None

    def parse_float(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        value = value.strip()
        if value in {"None", "null", "nan", ""}:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def parse_bool(value: Optional[str]) -> Optional[bool]:
        if value is None:
            return None
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
        return None

    def nation_for(token_id: Optional[str]) -> str:
        if not token_id:
            return "nieznana"
        resolved = _resolve_token_nation(token_id)
        if resolved:
            return resolved
        prefix = token_id.split("_", 1)[0]
        fallback = FALLBACK_PREFIX_MAP.get(prefix)
        if fallback:
            TOKEN_NATION_CACHE[token_id] = fallback
            return fallback
        return prefix

    def stats_for(token_id: Optional[str] = None, *, nation: Optional[str] = None) -> dict[str, int]:
        nazwa = nation if nation is not None else nation_for(token_id)
        return per_nacje.setdefault(
            nazwa,
            {
                "available_pe": 0,
                "spent_pe": 0,
                "returned_pe": 0,
                "pe_from_kp": 0,
                "fuel_added": 0,
                "cv_added": 0,
                "cv_returned": 0,
            },
        )

    for raw_line in linie:
        linia = raw_line.rstrip("\n")
        if pending_attack_line is not None:
            linia = pending_attack_line + " " + linia.strip()
            pending_attack_line = None

        stripped = linia.strip()
        token_id = None
        prefix_match = RE_TOKEN_PREFIX.search(stripped)
        if prefix_match:
            token_id = prefix_match.group(1).strip()

        if "atak na" in stripped and ("success=" not in stripped or "damage_dealt" not in stripped):
            pending_attack_line = stripped
            continue

        if "ryzykowny atak" in linia:
            match = RE_RYZYKOWNY.search(linia)
            if match:
                ratio_raw, ratio_adj_raw, detection_raw, support_raw = match.groups()
                if token_id:
                    oczekujace_decyzje[token_id] = {
                        "typ": "ryzykowny",
                        "ratio": float(ratio_raw),
                        "ratio_adj": float(ratio_adj_raw),
                        "detection": float(detection_raw),
                        "support": support_raw == "True",
                    }
                else:
                    det = float(detection_raw)
                    metryki.ryzykowne_ataki += 1
                    metryki.detekcja_suma += det
                    metryki.detekcja_probki += 1
                    metryki.ratio_suma += float(ratio_raw)
                    metryki.ratio_adj_suma += float(ratio_adj_raw)
                    if support_raw == "True":
                        metryki.ataki_z_wsparciem += 1
                    else:
                        metryki.ataki_bez_wsparcia += 1

        if "agresywny atak" in linia:
            match = RE_AGRESYWNY.search(linia)
            if match:
                ratio_raw, ratio_adj_raw, detection_raw, support_raw = match.groups()
                if token_id:
                    oczekujace_decyzje[token_id] = {
                        "typ": "agresywny",
                        "ratio": float(ratio_raw),
                        "ratio_adj": float(ratio_adj_raw),
                        "detection": float(detection_raw),
                        "support": support_raw == "True",
                    }
                else:
                    det = float(detection_raw)
                    metryki.agresywne_ataki += 1
                    metryki.detekcja_suma += det
                    metryki.detekcja_probki += 1
                    metryki.ratio_suma += float(ratio_raw)
                    metryki.ratio_adj_suma += float(ratio_adj_raw)
                    if support_raw == "True":
                        metryki.ataki_z_wsparciem += 1
                    else:
                        metryki.ataki_bez_wsparcia += 1

        if "start tury" in linia:
            metryki.liczba_tur += 1
            pola_start = dict(RE_KEY_VALUE.findall(linia))
            specialist_name = pola_start.get("specialist")
            action_profile = pola_start.get("action_profile")
            spec_stats = specjalisci[specialist_name] if specialist_name else None

            match = RE_START_TURY.search(linia)
            if match:
                status, akcje_raw = match.groups()
                status = status.strip()
                statusy_start[status] += 1
                if spec_stats is not None:
                    spec_stats.statusy[status] += 1

                planowany_atak = False
                if akcje_raw.strip():
                    for element in akcje_raw.split(','):
                        element = element.strip().strip("'\"")
                        if not element:
                            continue
                        zaplanowane_akcje[element] += 1
                        if spec_stats is not None:
                            spec_stats.planowane_akcje[element] += 1
                        if element == "attack":
                            planowany_atak = True
                if planowany_atak:
                    metryki.planowane_ataki += 1

            if spec_stats is not None:
                spec_stats.tury += 1
                if action_profile:
                    spec_stats.profile[action_profile.strip()] += 1

            if "human_note=" in linia:
                note_start = linia.find("human_note=")
                note_content = linia[note_start + 11:].strip()
                if ", specialist_" in note_content:
                    note_content = note_content[:note_content.find(", specialist_")]
                elif "," in note_content:
                    note_content = note_content[:note_content.find(",")]
                note_content = note_content.strip()
                human_notes.append(note_content)
                if spec_stats is not None and note_content:
                    spec_stats.uwagi[note_content] += 1

            mode_match = RE_MODE.search(linia)
            if mode_match:
                tryby_ruchu[mode_match.group(1).strip()] += 1
            else:
                metryki.braki_movement_mode += 1
            if token_id:
                oczekujace_decyzje.pop(token_id, None)

        elif "koniec tury" in linia:
            match = RE_PODSUMOWANIE.search(linia)
            if match:
                sukces, proby, wydane, zwrocone = match.groups()
                if sukces == "True":
                    metryki.ruchy_skuteczne += 1
                metryki.ruchy_proby += int(proby)
                metryki.resupply_wydane += int(wydane)

            pola = dict(RE_KEY_VALUE.findall(linia))
            specialist_name = pola.get("specialist")
            spec_stats = specjalisci[specialist_name] if specialist_name else None
            statystyki_nacji = stats_for(token_id)

            przydzial = parse_int(pola.get("allocated_pe"))
            if przydzial is not None:
                statystyki_nacji["available_pe"] += przydzial
                metryki.pe_dostepne += przydzial

            wydatki = parse_int(pola.get("resupply_spent"))
            if wydatki is not None:
                statystyki_nacji["spent_pe"] += wydatki

            zwroty = parse_int(pola.get("unused_pe"))
            if zwroty is None:
                zwroty = parse_int(pola.get("reserved_pe"))
            if zwroty is not None:
                statystyki_nacji["returned_pe"] += zwroty
                metryki.pe_zwrocone += zwroty

            zatankowane = parse_int(pola.get("refueled"))
            if zatankowane is not None:
                statystyki_nacji["fuel_added"] += zatankowane
                metryki.paliwo_dodane += zatankowane
                if spec_stats is not None:
                    spec_stats.paliwo += zatankowane

            cv_przywrocone = parse_int(pola.get("combat_restored"))
            if cv_przywrocone is not None:
                statystyki_nacji["cv_added"] += cv_przywrocone
                metryki.cv_dodane += cv_przywrocone
                if spec_stats is not None:
                    spec_stats.cv += cv_przywrocone

            attempt_match = RE_ATTEMPT.search(linia)
            if attempt_match and attempt_match.group(1) == "True":
                metryki.ataki_wykonane += 1

            distance_match = RE_DISTANCE_TOTAL.search(linia)
            if distance_match:
                distance_total = int(distance_match.group(1))
                metryki.dystans_ruchu_suma += distance_total
                dystanse_na_ture[distance_total] += 1
                if distance_total > 0:
                    metryki.tury_z_ruchem += 1
                    if spec_stats is not None:
                        spec_stats.ruchy_udane += 1
                if distance_total > metryki.max_dystans_tury:
                    metryki.max_dystans_tury = distance_total

            mp_match = RE_MP_SPENT.search(linia)
            if mp_match:
                metryki.mp_wydane_suma += int(mp_match.group(1))

            hold_match = RE_HOLD.search(linia)
            if hold_match and hold_match.group(1) == "True":
                metryki.hold_position += 1
                reason = (pola.get("hold_reason") or "").strip()
                if reason:
                    metryki.hold_reasons[reason] += 1
                if spec_stats is not None:
                    spec_stats.holdy += 1

            status_match = RE_STATUS.search(linia)
            if status_match:
                status = status_match.group(1).strip()
                statusy_koniec[status] += 1
                if spec_stats is not None:
                    spec_stats.statusy[status] += 1
            if token_id:
                oczekujace_decyzje.pop(token_id, None)

        elif "plan ataku" in linia:
            pola = dict(RE_KEY_VALUE.findall(linia))
            plan: Dict[str, Any] = {
                "token": token_id,
                "executed": parse_bool(pola.get("executed")),
                "decision": pola.get("decision"),
                "reason": pola.get("reason"),
                "hold_reason": pola.get("hold_reason"),
                "target": pola.get("target"),
                "threshold": pola.get("threshold"),
                "risk_type": pola.get("risk_type"),
                "support": parse_bool(pola.get("support")),
                "ratio": parse_float(pola.get("ratio")),
                "ratio_adjusted": parse_float(pola.get("ratio_adjusted")),
                "detection": parse_float(pola.get("detection")),
                "distance": parse_int(pola.get("distance")),
                "counterattack": parse_bool(pola.get("counterattack")),
                "attacker_health": parse_float(pola.get("attacker_health")),
                "defender_health": parse_float(pola.get("defender_health")),
                "fuel_ratio": parse_float(pola.get("fuel_ratio")),
                "risk_roll": parse_float(pola.get("risk_roll")),
                "aggression_chance": parse_float(pola.get("aggression_chance")),
                "attack_success": parse_bool(pola.get("attack_success")),
                "attack_damage_dealt": parse_int(pola.get("attack_damage_dealt")),
                "attack_damage_taken": parse_int(pola.get("attack_damage_taken")),
            }

            pos_q = parse_int(pola.get("position_q"))
            pos_r = parse_int(pola.get("position_r"))
            if pos_q is not None and pos_r is not None:
                plan["position"] = (pos_q, pos_r)
            target_q = parse_int(pola.get("target_q"))
            target_r = parse_int(pola.get("target_r"))
            if target_q is not None and target_r is not None:
                plan["enemy_position"] = (target_q, target_r)

            plany_ataku.append(plan)

        elif "przydział PE z KP" in linia:
            pola = dict(RE_KEY_VALUE.findall(linia))
            przydzial_kp = parse_int(pola.get("pe_gain"))
            if przydzial_kp is not None:
                nation = pola.get("general_nation")
                if nation:
                    statystyki_nacji = stats_for(nation=nation)
                else:
                    statystyki_nacji = stats_for(token_id)
                statystyki_nacji["pe_from_kp"] += przydzial_kp
                metryki.pe_z_kp += przydzial_kp

        elif "uzupełnia paliwo" in linia:
            match = RE_UZUPELNIANIE_PALIWA.search(linia)
            if match:
                paliwo_amount = int(match.group(1))
                paliwo_debug_total += paliwo_amount
                if token_id:
                    paliwo_debug_per[nation_for(token_id)] += paliwo_amount

        elif "uzupełnia CV" in linia:
            match = RE_UZUPELNIANIE_CV.search(linia)
            if match:
                cv_amount = int(match.group(1))
                cv_debug_total += cv_amount
                if token_id:
                    cv_debug_per[nation_for(token_id)] += cv_amount

        elif "movement_step_distance" in linia:
            step_match = RE_STEP_DISTANCE.search(linia)
            if step_match:
                distance = int(step_match.group(1))
                metryki.kroki_ruchu += 1
                metryki.dystans_krokow_suma += distance
                kroki_dystanse[distance] += 1
            mp_step_match = RE_STEP_MP.search(linia)
            if mp_step_match:
                metryki.mp_krokow_suma += int(mp_step_match.group(1))

        elif "atak na" in linia and "damage_dealt" in linia:
            match = RE_ATTACK.search(linia)
            if match:
                sukces_flag, zadane_raw, przyjete_raw = match.groups()
                pary = dict(RE_KEY_VALUE.findall(linia))
                sukces_flag = pary.get("success", sukces_flag)
                damage_dealt = pary.get("damage_dealt", zadane_raw)
                damage_taken = pary.get("damage_taken", przyjete_raw)
                counterattack_flag = pary.get("counterattack")

                klucz = "sukces" if sukces_flag == "True" else "porażka"
                podsumowanie_walk[klucz] += 1

                dmg_dealt_val = parse_int(damage_dealt)
                dmg_taken_val = parse_int(damage_taken)

                if sukces_flag == "True":
                    if dmg_dealt_val is not None:
                        podsumowanie_walk["obrażenia_zadane"] += dmg_dealt_val
                        metryki.obrazenia_zadane_suma += dmg_dealt_val
                        metryki.obrazenia_zadane_licznik += 1
                        if dmg_dealt_val > metryki.obrazenia_zadane_max:
                            metryki.obrazenia_zadane_max = dmg_dealt_val
                    if dmg_taken_val is not None:
                        podsumowanie_walk["obrażenia_przyjęte"] += dmg_taken_val
                        metryki.obrazenia_przyjete_suma += dmg_taken_val
                        metryki.obrazenia_przyjete_licznik += 1
                        if dmg_taken_val > metryki.obrazenia_przyjete_max:
                            metryki.obrazenia_przyjete_max = dmg_taken_val
                    metryki.ataki_sukcesy += 1
                else:
                    if dmg_taken_val is not None:
                        metryki.obrazenia_przyjete_suma += dmg_taken_val
                        metryki.obrazenia_przyjete_licznik += 1
                        if dmg_taken_val > metryki.obrazenia_przyjete_max:
                            metryki.obrazenia_przyjete_max = dmg_taken_val
                    metryki.ataki_porazki += 1

                if counterattack_flag == "True":
                    metryki.kontrataki += 1
                    podsumowanie_walk["kontratak"] += 1

                if token_id and token_id in oczekujace_decyzje:
                    decyzja = oczekujace_decyzje.pop(token_id)
                    det = decyzja.get("detection")
                    ratio = decyzja.get("ratio")
                    ratio_adj = decyzja.get("ratio_adj")
                    support_flag = decyzja.get("support")
                    if isinstance(det, (int, float)):
                        metryki.detekcja_suma += float(det)
                        metryki.detekcja_probki += 1
                    if isinstance(ratio, (int, float)):
                        metryki.ratio_suma += float(ratio)
                    if isinstance(ratio_adj, (int, float)):
                        metryki.ratio_adj_suma += float(ratio_adj)
                    if support_flag:
                        metryki.ataki_z_wsparciem += 1
                    else:
                        metryki.ataki_bez_wsparcia += 1

                    typ = decyzja.get("typ")
                    if typ == "ryzykowny":
                        metryki.ryzykowne_ataki += 1
                        if sukces_flag == "True":
                            metryki.ryzykowne_sukcesy += 1
                    elif typ == "agresywny":
                        metryki.agresywne_ataki += 1
                        if sukces_flag == "True":
                            metryki.agresywne_sukcesy += 1

    if metryki.paliwo_dodane == 0 and paliwo_debug_total:
        metryki.paliwo_dodane = paliwo_debug_total
    if metryki.cv_dodane == 0 and cv_debug_total:
        metryki.cv_dodane = cv_debug_total

    if not any(stats["fuel_added"] for stats in per_nacje.values()) and paliwo_debug_total:
        for nazwa, kwota in paliwo_debug_per.items():
            stats_for(nation=nazwa)["fuel_added"] += kwota
    if not any(stats["cv_added"] for stats in per_nacje.values()) and cv_debug_total:
        for nazwa, kwota in cv_debug_per.items():
            stats_for(nation=nazwa)["cv_added"] += kwota

    zakupione_zetony = _collect_purchase_summary()

    return WynikiAnalizy(
        metryki=metryki,
        zaplanowane_akcje=zaplanowane_akcje,
        statusy_start=statusy_start,
        statusy_koniec=statusy_koniec,
        podsumowanie_walk=podsumowanie_walk,
        tryby_ruchu=tryby_ruchu,
        kroki_dystanse=kroki_dystanse,
        dystanse_na_ture=dystanse_na_ture,
        per_nacje=per_nacje,
        human_notes=human_notes,
        specjalisci={nazwa: stats for nazwa, stats in specjalisci.items()},
        plany_ataku=plany_ataku,
        zakupione_zetony=zakupione_zetony,
    )


def formatuj_raport(wyniki: WynikiAnalizy) -> str:
    m = wyniki.metryki
    kroki_dystanse = wyniki.kroki_dystanse
    dystanse_tury = wyniki.dystanse_na_ture
    linie: list[str] = []
    hold_translations: dict[str, str] = {
        "attack_not_viable": "atak nieopłacalny",
        "insufficient_resources": "brak zasobów",
        "danger_zone_entry": "wejście w strefę zagrożenia",
        "no_path_available": "brak ścieżki",
        "no_move_points": "brak punktów ruchu",
        "insufficient_fuel": "brak paliwa",
    }

    def format_counter(counter: Counter[str], mapping: Dict[str, str], *, limit: Optional[int] = None) -> str:
        if not counter:
            return ""
        items = counter.most_common(limit)
        return ", ".join(f"{format_with_translation(key, mapping)}×{count}" for key, count in items)

    def odmiana(n: int, form1: str, form2: str, form5: str) -> str:
        n_abs = abs(n)
        if n_abs % 100 in (12, 13, 14):
            return form5
        ostatnia = n_abs % 10
        if ostatnia == 1:
            return form1
        if ostatnia in (2, 3, 4):
            return form2
        return form5

    linie.append("=== Raport sesji żetonów ===")

    linie.append("\n--- PODSUMOWANIE ---")
    linie.append(f"- Zliczone tury: {m.liczba_tur}")
    if m.liczba_tur:
        skutecznosc = m.ruchy_skuteczne / max(1, m.liczba_tur)
        linie.append(
            f"- Skuteczne ruchy: {m.ruchy_skuteczne}/{m.liczba_tur} ({skutecznosc:.1%} tur ze skutecznym ruchem)"
        )
    linie.append(f"- hold_position ustawione: {m.hold_position} razy")
    if m.hold_reasons:
        linie.append("  • Powody:")
        for reason, licznik in m.hold_reasons.most_common():
            czytelny_powod = reason.replace("_", " ")
            polska_nazwa = hold_translations.get(reason, czytelny_powod)
            linie.append(f"    ◦ {czytelny_powod} ({polska_nazwa}): {licznik}")

    linie.append("\n--- RUCH ---")
    linie.append(
        f"- Łączny dystans pokonany: {m.dystans_ruchu_suma} {odmiana(m.dystans_ruchu_suma, 'heks', 'heksy', 'heksów')}"
    )
    linie.append(
        f"- Maksymalny dystans w jednej turze: {m.max_dystans_tury} {odmiana(m.max_dystans_tury, 'heks', 'heksy', 'heksów')}"
    )
    tury_bez_ruchu = m.liczba_tur - m.tury_z_ruchem
    linie.append(f"- Liczba tur z ruchem (>0 heksów): {m.tury_z_ruchem}")
    linie.append(f"- Liczba tur bez ruchu (0 heksów): {tury_bez_ruchu}")
    if dystanse_tury:
        linie.append("- Rozkład tur wg dystansu:")
        najwiecej_tur = 0
        najczestszy_dystans: Optional[int] = None
        for dystans in sorted(dystanse_tury):
            licznik = dystanse_tury[dystans]
            linie.append(f"    • {dystans}: {licznik}")
            if licznik > najwiecej_tur:
                najwiecej_tur = licznik
                najczestszy_dystans = dystans
        if najczestszy_dystans is not None:
            linie.append(
                f"    • Najczęstszy dystans: {najczestszy_dystans} "
                f"{odmiana(najczestszy_dystans, 'heks', 'heksy', 'heksów')}"
            )
    if m.tury_z_ruchem:
        sr_ruch_tura = m.dystans_ruchu_suma / max(1, m.tury_z_ruchem)
        linie.append(f"- Średnia długość ruchu w turze: {sr_ruch_tura:.2f} heksa")
    if m.kroki_ruchu and m.mp_krokow_suma:
        linie.append(f"- Średnia liczba MP na krok: {m.mp_krokow_suma / max(1, m.kroki_ruchu):.2f}")
    if m.liczba_tur and m.mp_wydane_suma:
        linie.append(
            f"- Średnia liczba MP wydana na turę (maintenance): {m.mp_wydane_suma / m.liczba_tur:.2f}"
        )
    linie.append("\n--- ZAOPATRZENIE ---")
    aktywne_nacje: list[str] = []
    if wyniki.per_nacje:
        aktywne_nacje = [
            nazwa
            for nazwa, stat in sorted(wyniki.per_nacje.items())
            if any(
                stat[key]
                for key in ("available_pe", "fuel_added", "cv_added", "returned_pe", "pe_from_kp")
            )
        ]
    if aktywne_nacje:
        linie.append("- PE wg nacji:")
        for nazwa in aktywne_nacje:
            stat = wyniki.per_nacje[nazwa]
            pozyskane = stat["available_pe"]
            paliwo = stat["fuel_added"]
            cv = stat["cv_added"]
            zwrocone = stat["returned_pe"]
            kp = stat["pe_from_kp"]
            linie.append(
                f"    • {nazwa}: pozyskane {pozyskane} | paliwo {paliwo} | CV {cv} | zwrócone {zwrocone} | KP {kp}"
            )

    total_pozyskane = sum(stat["available_pe"] for stat in wyniki.per_nacje.values())
    total_paliwo = sum(stat["fuel_added"] for stat in wyniki.per_nacje.values())
    total_cv = sum(stat["cv_added"] for stat in wyniki.per_nacje.values())
    total_kp = sum(stat["pe_from_kp"] for stat in wyniki.per_nacje.values())
    total_wydane = total_paliwo + total_cv
    total_zwrocone = sum(stat["returned_pe"] for stat in wyniki.per_nacje.values())
    linie.append("- Bilans ogólny:")
    linie.append(f"    • PE pozyskane: {total_pozyskane}")
    linie.append(f"    • PE z kluczowych punktów: {total_kp}")
    linie.append(f"    • Wydane na paliwo: {total_paliwo}")
    linie.append(f"    • Wydane na CV: {total_cv}")
    procent_wydane = (total_wydane / total_pozyskane * 100) if total_pozyskane else 0.0
    procent_zwrocone = (total_zwrocone / total_pozyskane * 100) if total_pozyskane else 0.0
    linie.append(
        f"    • Wydane łącznie: {total_wydane} ({procent_wydane:.1f}% pozyskanych)"
    )
    linie.append(
        f"    • Zwrócone: {total_zwrocone} ({procent_zwrocone:.1f}% pozyskanych)"
    )

    if wyniki.zakupione_zetony:
        linie.append("\n<details>")
        linie.append(
            f"<summary>Zakupione żetony ({len(wyniki.zakupione_zetony)})</summary>"
        )
        linie.append(f"- Łącznie zakupione: {len(wyniki.zakupione_zetony)}")
        for purchase in wyniki.zakupione_zetony:
            token_id = purchase.get("token_id") or "(brak id)"
            commander_id = purchase.get("commander_id")
            cost = purchase.get("cost")
            category = purchase.get("category") or purchase.get("focus")
            focus = purchase.get("focus")
            unit_desc = ", ".join(
                part for part in [purchase.get("unit_type"), purchase.get("unit_size")] if part
            )
            turn = purchase.get("turn")
            folder = purchase.get("folder")

            details = [f"token {token_id}"]
            if unit_desc:
                details.append(unit_desc)
            if category:
                label = category if category != focus else category
                details.append(f"kategoria: {label}")
            if focus and focus != category:
                details.append(f"focus: {focus}")
            if cost is not None:
                details.append(f"koszt: {cost} PE")
            if commander_id is not None:
                details.append(f"dla dowódcy {commander_id}")
            if turn is not None:
                details.append(f"tura: {turn}")
            if folder:
                details.append(f"folder: {folder}")

            if purchase.get("deployed"):
                spawn_q = purchase.get("spawn_q")
                spawn_r = purchase.get("spawn_r")
                deployment_commander_id = purchase.get("deployment_commander_id") or commander_id
                if spawn_q is not None and spawn_r is not None:
                    coords = f"({spawn_q},{spawn_r})"
                else:
                    coords = "(brak koordynatów)"
                status = (
                    f"wystawiono przez dowódcę {deployment_commander_id} na heksie {coords}"
                    if deployment_commander_id is not None
                    else f"wystawiono na heksie {coords}"
                )
            else:
                status = "oczekuje na wystawienie"

            linie.append(f"  • {' | '.join(details)} → {status}")
        linie.append("</details>")

    linie.append("\n--- ATAKI ---")
    if m.planowane_ataki or m.ataki_wykonane:
        realizacja = m.ataki_wykonane / max(1, m.planowane_ataki)
        niewykonane = max(0, m.planowane_ataki - m.ataki_wykonane)
        linie.append(
            f"- Plany: {m.planowane_ataki} | Wykonane: {m.ataki_wykonane} | Realizacja: {realizacja:.1%}"
        )
        linie.append(
            f"- Plany bez strzału: {niewykonane} {odmiana(niewykonane, 'plan', 'plany', 'planów')}"
        )
    else:
        linie.append("- Brak zaplanowanych ataków")

    oddane = m.ataki_sukcesy + m.ataki_porazki
    if oddane:
        linie.append(
            f"- Zarejestrowane starcia: {oddane} (trafienia: {m.ataki_sukcesy}, pudła: {m.ataki_porazki})"
        )
        linie.append(f"- Skuteczność strzałów: {m.ataki_sukcesy / max(1, oddane):.1%}")
        if m.ataki_wykonane and oddane != m.ataki_wykonane:
            roznica = m.ataki_wykonane - oddane
            if roznica > 0:
                linie.append(
                    f"  • Uwaga: {roznica} prób zarejestrowanych bez szczegółowego wpisu (sprawdź logi)."
                )
    else:
        if m.ataki_wykonane:
            linie.append(
                f"- Brak szczegółowych logów ataków (wykonane wg podsumowania: {m.ataki_wykonane})"
            )
        else:
            linie.append("- Brak odnotowanych starć")

    if m.obrazenia_zadane_licznik:
        sr_zadane = m.obrazenia_zadane_suma / max(1, m.obrazenia_zadane_licznik)
        linie.append(
            f"- Średnie obrażenia zadane (na trafienie): {sr_zadane:.2f} (max: {m.obrazenia_zadane_max})"
        )
    if m.obrazenia_przyjete_licznik:
        sr_przyjete = m.obrazenia_przyjete_suma / max(1, m.obrazenia_przyjete_licznik)
        linie.append(
            f"- Średnie obrażenia przyjęte na starcie: {sr_przyjete:.2f} (max: {m.obrazenia_przyjete_max})"
        )

    if wyniki.plany_ataku:
        linie.append("")
        linie.append("<details>")
        linie.append(f"<summary>Plany ataku ({len(wyniki.plany_ataku)})</summary>")
        for plan in wyniki.plany_ataku:
            executed = plan.get("executed") is True
            symbol = "✅" if executed else "❌"
            color = "green" if executed else "red"
            token_name = plan.get("token") or "?"
            target = plan.get("target") or "brak_celu"

            ratio_adj = plan.get("ratio_adjusted")
            ratio_base = plan.get("ratio")
            detection_val = plan.get("detection")
            support_flag = plan.get("support")
            threshold = plan.get("threshold")
            reason = plan.get("hold_reason") or plan.get("reason")
            risk_type = plan.get("risk_type")
            distance = plan.get("distance")

            ratio_adj_txt = f"{ratio_adj:.2f}" if isinstance(ratio_adj, (int, float)) else "--"
            ratio_base_txt = f"{ratio_base:.2f}" if isinstance(ratio_base, (int, float)) else "--"
            detection_txt = f"{detection_val:.2f}" if isinstance(detection_val, (int, float)) else "--"
            support_txt = "wsparcie" if support_flag else "solo"

            parts: list[str] = [f"{symbol} {token_name} → {target}"]
            parts.append(f"ratio_adj={ratio_adj_txt}")
            parts.append(f"ratio={ratio_base_txt}")
            parts.append(f"det={detection_txt}")
            if distance is not None:
                parts.append(f"dist={distance}")
            parts.append(support_txt)
            if threshold:
                parts.append(f"prog={threshold}")
            if risk_type:
                parts.append(f"tryb={risk_type}")

            result_txt = None
            if executed:
                success_flag = plan.get("attack_success")
                if success_flag is True:
                    result_txt = "wynik: sukces"
                elif success_flag is False:
                    result_txt = "wynik: porażka"
                dmg_dealt = plan.get("attack_damage_dealt")
                dmg_taken = plan.get("attack_damage_taken")
                if isinstance(dmg_dealt, int):
                    parts.append(f"zadane={dmg_dealt}")
                if isinstance(dmg_taken, int):
                    parts.append(f"otrzymane={dmg_taken}")
            if result_txt:
                parts.append(result_txt)

            if reason:
                reason_txt = str(reason).replace("_", " ")
                parts.append(f"powód: {reason_txt}")

            entry = " | ".join(parts)
            linie.append(f"  - <span style=\"color:{color}\">{entry}</span>")
    linie.append("</details>")
    linie.append("")

    if m.kontrataki:
        linie.append(f"- Kontrataki przeciwnika: {m.kontrataki}")

    if m.ataki_z_wsparciem or m.ataki_bez_wsparcia:
        linie.append(
            f"- Wsparcie sojusznicze: {m.ataki_z_wsparciem} z osłoną / {m.ataki_bez_wsparcia} bez wsparcia"
        )

    if m.ryzykowne_ataki or m.agresywne_ataki:
        linie.append("- Decyzje ofensywne przy niepewności:")
        if m.ryzykowne_ataki:
            skut = m.ryzykowne_sukcesy / max(1, m.ryzykowne_ataki)
            linie.append(
                f"  • Ryzykowne ataki: {m.ryzykowne_ataki} (trafienia: {m.ryzykowne_sukcesy}, skuteczność: {skut:.1%})"
            )
        if m.agresywne_ataki:
            skut = m.agresywne_sukcesy / max(1, m.agresywne_ataki)
            linie.append(
                f"  • Agresywne ataki (niska detekcja): {m.agresywne_ataki} (trafienia: {m.agresywne_sukcesy}, skuteczność: {skut:.1%})"
            )
        if m.detekcja_probki:
            det_avg = m.detekcja_suma / max(1, m.detekcja_probki)
            ratio_avg = m.ratio_suma / max(1, m.detekcja_probki)
            ratio_adj_avg = m.ratio_adj_suma / max(1, m.detekcja_probki)
            linie.append(
                f"  • Śr. poziom detekcji: {det_avg:.2f} | Śr. stosunek CV: {ratio_avg:.2f} → {ratio_adj_avg:.2f}"
            )

    if wyniki.podsumowanie_walk:
        sukcesy = wyniki.podsumowanie_walk.get("sukces", 0)
        porazki = wyniki.podsumowanie_walk.get("porażka", 0)
        linie.append(
            f"- Wynik starć wg logów: {sukcesy} {odmiana(sukcesy, 'sukces', 'sukcesy', 'sukcesów')} / {porazki} {odmiana(porazki, 'porażka', 'porażki', 'porażek')}"
        )
        if sukcesy:
            linie.append(
                f"  • Obrażenia zadane łącznie: {wyniki.podsumowanie_walk.get('obrażenia_zadane', 0)}"
            )
            linie.append(
                f"  • Obrażenia przyjęte łącznie (przy trafieniach): {wyniki.podsumowanie_walk.get('obrażenia_przyjęte', 0)}"
            )
        if wyniki.podsumowanie_walk.get("kontratak"):
            linie.append(
                f"  • Kontrataki odnotowane w logach: {wyniki.podsumowanie_walk.get('kontratak', 0)}"
            )

    linie.append("\n--- TRYBY I AKCJE ---")
    if wyniki.tryby_ruchu:
        linie.append("- Użycie trybów ruchu:")
        for tryb, licznik in wyniki.tryby_ruchu.most_common():
            linie.append(f"    • {format_with_translation(tryb, MODE_TRANSLATIONS)}: {licznik}")
    if wyniki.zaplanowane_akcje:
        linie.append("- Najczęściej planowane akcje:")
        for akcja, licznik in wyniki.zaplanowane_akcje.most_common():
            linie.append(f"    • {format_with_translation(akcja, ACTION_TRANSLATIONS)}: {licznik}")

    if wyniki.specjalisci:
        linie.append("\n--- SPECJALIŚCI ---")
        for nazwa, stats in sorted(wyniki.specjalisci.items(), key=lambda item: item[1].tury, reverse=True):
            etykieta = format_with_translation(nazwa, SPECIALIST_TRANSLATIONS)
            elementy: list[str] = []
            if stats.tury:
                elementy.append(f"{stats.tury} {odmiana(stats.tury, 'tura', 'tury', 'tur')}")
            profile_txt = format_counter(stats.profile, ACTION_PROFILE_TRANSLATIONS, limit=3)
            if profile_txt:
                elementy.append(f"profile: {profile_txt}")
            akcje_txt = format_counter(stats.planowane_akcje, ACTION_TRANSLATIONS, limit=3)
            if akcje_txt:
                elementy.append(f"akcje: {akcje_txt}")
            statusy_txt = format_counter(stats.statusy, STATUS_TRANSLATIONS, limit=3)
            if statusy_txt:
                elementy.append(f"statusy: {statusy_txt}")
            zasoby = []
            if stats.paliwo:
                zasoby.append(f"paliwo +{stats.paliwo}")
            if stats.cv:
                zasoby.append(f"CV +{stats.cv}")
            if zasoby:
                elementy.append(", ".join(zasoby))
            if stats.holdy:
                elementy.append(f"hold {stats.holdy}×")
            if stats.ruchy_udane:
                elementy.append(f"ruch>0 {stats.ruchy_udane}×")
            if stats.uwagi:
                notatki = "; ".join(f"{note}×{count}" for note, count in stats.uwagi.most_common(2))
                elementy.append(f"notatki: {notatki}")
            linia_spec = " | ".join(elementy) if elementy else "brak aktywności"
            linie.append(f"- {etykieta}: {linia_spec}")

    if m.braki_movement_mode:
        linie.append(
            f"\nUWAGA: {m.braki_movement_mode} wpisów bez movement_mode (warto sprawdzić logowanie)."
        )
    
    # Notatki specjalistów (human_notes)
    return "\n".join(linie)


def wybierz_najnowszy(path: Path) -> Optional[Path]:
    if path.is_file():
        return path
    kandydaci = sorted(path.glob("*.log"))
    return kandydaci[-1] if kandydaci else None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analiza logów sesji żetonów (TokenAI)"
    )
    parser.add_argument(
        "sciezka",
        nargs="?",
        default="ai/logs/tokens/text",
        help="Ścieżka do pliku logu lub katalogu (domyślnie najnowszy log tekstowy żetonów)",
    )
    args = parser.parse_args()

    kandydat = wybierz_najnowszy(Path(args.sciezka))
    if not kandydat or not kandydat.exists():
        raise SystemExit(f"Brak pliku logu pod ścieżką {args.sciezka!r}")

    with kandydat.open("r", encoding="utf-8") as fh:
        wyniki = analizuj_linie(fh)

    raport = formatuj_raport(wyniki)
    print(raport)

    raport_dir = kandydat.parent / "raporty"
    raport_dir.mkdir(parents=True, exist_ok=True)
    raport_path = raport_dir / f"{kandydat.stem}_raport.txt"
    raport_path.write_text(raport, encoding="utf-8")
    print(f"\nRaport zapisany do pliku: {raport_path}")


if __name__ == "__main__":
    main()
