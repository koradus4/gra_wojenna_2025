"""Moduł specjalizacji AI dla żetonów.

Zapewnia delikatne, bezpieczne rozszerzenia zachowań `TokenAI` tak, aby
różne typy jednostek korzystały z dedykowanych heurystyk, jednocześnie
pozostając kompatybilne z przyszłymi warstwami dowodzenia.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Type


# ---------------------------------------------------------------------------
# Współdzielona pamięć rozpoznania
# ---------------------------------------------------------------------------


@dataclass
class SharedIntelMemory:
    """Minimalna współdzielona pamięć kontaktów przeciwnika.
    
    Zapamiętuje ostatnie meldunki wykryć wraz z prostym licznikiem czasu.
    Nie ma ambicji bycia pełnym systemem – jedynie wspiera specjalistów
    w podejmowaniu bardziej świadomych decyzji.
    """

    _reports: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _tick: int = 0

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Zwraca kopię danych, aby uniknąć mutacji przez użytkowników."""
        return {enemy_id: dict(payload) for enemy_id, payload in self._reports.items()}

    def ingest(self, reporter_id: str, detection_map: Optional[Dict[str, Dict[str, Any]]]) -> None:
        """Aktualizuje pamięć na podstawie lokalnej mapy detekcji."""
        if not detection_map:
            return
        self._tick += 1
        for enemy_id, info in detection_map.items():
            if not isinstance(info, dict):
                continue
            payload = dict(info)
            payload.setdefault("last_seen_by", reporter_id)
            payload["timestamp"] = self._tick
            self._reports[enemy_id] = payload

    def forget(self, max_age: int = 12) -> None:
        """Usuwa najstarsze meldunki, aby pamięć nie rosła bez kontroli."""
        if max_age <= 0:
            return
        threshold = self._tick - max_age
        stale_keys = [enemy_id for enemy_id, info in self._reports.items() if info.get("timestamp", 0) <= threshold]
        for enemy_id in stale_keys:
            self._reports.pop(enemy_id, None)


_GLOBAL_SHARED_INTEL = SharedIntelMemory()


def get_shared_intel_memory() -> SharedIntelMemory:
    return _GLOBAL_SHARED_INTEL


def _flag(context: Dict[str, Any], flag: str) -> None:
    """Pomocnik: dodaje flagę do kontekstu dla celów diagnostycznych."""
    if not flag:
        return
    flags = context.setdefault("specialist_flags", set())
    if isinstance(flags, set):
        flags.add(flag)
    else:
        merged = set(flags) if hasattr(flags, "__iter__") else set()
        merged.add(flag)
        context["specialist_flags"] = merged


# ---------------------------------------------------------------------------
# Bazowa klasa specjalistów
# ---------------------------------------------------------------------------


class TokenSpecialist:
    """Interfejs rozszerzeń zachowania `TokenAI`.
    
    Specjaliści działają delikatnie: mogą wzbogacać kontekst, korygować
    wybór profilu akcji lub priorytetyzować czynności. Wszystkie metody
    mają bezpieczne domyślne implementacje, dzięki czemu brak przydzielonego
    specjalisty nie psuje logiki bazowej.
    """

    handled_types: Set[str] = set()

    def __init__(self, token, shared_intel: SharedIntelMemory):
        self.token = token
        self.shared_intel = shared_intel

    # --- cykl tury -----------------------------------------------------
    def on_turn_start(self, memory: Dict[str, Any]) -> None:
        """Wywoływane na początku tury; okazja do czyszczenia pamięci."""
        if self.shared_intel:
            self.shared_intel.forget(max_age=18)

    def extend_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rozszerza kontekst o dane specjalisty (np. cele, sygnały)."""
        if self.shared_intel:
            context.setdefault("shared_enemy_detection", self.shared_intel.snapshot())
        context.setdefault("specialist_flags", set())
        return context

    def adjust_status(self, status: str, context: Dict[str, Any]) -> str:
        """Pozwala skorygować status (np. normal→retreat przy zagrożeniu)."""
        return status

    def adjust_movement_mode(self, movement_mode: str, status: str, context: Dict[str, Any]) -> str:
        """Pozwala zmienić tryb ruchu (march/combat/recon)."""
        return movement_mode

    def suggest_movement_target(self, context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Sugeruje cel ruchu (np. KP dla konwoju). None = brak sugestii."""
        return None

    def choose_action_profile(self, profile_key: str, status: str, context: Dict[str, Any]) -> str:
        """Zmienia profil akcji (retreat/recovery/combat/patrol)."""
        return profile_key

    def adjust_actions(
        self,
        planned_actions: List[str],
        status: str,
        context: Dict[str, Any],
        pe_budget: int,
    ) -> List[str]:
        """Modyfikuje kolejkę akcji przed ich wykonaniem."""
        return list(planned_actions)

    def update_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook po akcjach – pozwala zaaktualizować dane kontekstu."""
        return context

    def after_turn(self, context: Dict[str, Any], reports: Dict[str, Any]) -> None:
        """Wywoływane na końcu tury; okazja do zapisania obserwacji."""
        if self.shared_intel:
            detection_map = context.get("enemy_detection")
            reporter_id = getattr(self.token, "id", None)
            if reporter_id:
                self.shared_intel.ingest(reporter_id, detection_map)


class GenericSpecialist(TokenSpecialist):
    """Domyślny specjalista – zachowuje pełną kompatybilność z bazowym AI."""


# ---------------------------------------------------------------------------
# Specjalista zaopatrzenia
# ---------------------------------------------------------------------------


class SupplySpecialist(TokenSpecialist):
    """Specjalista dla jednostek zaopatrzeniowych (Z, ZA, SUPPLY).
    
    Cel: utrzymać najbardziej wartościowy Key Point na mapie, unikając walki.
    """

    handled_types = {"Z", "ZA", "SUPPLY"}

    def __init__(self, token, shared_intel: SharedIntelMemory):
        super().__init__(token, shared_intel)
        self._assigned_kp: Optional[Tuple[int, int]] = getattr(token, "supply_assigned_kp", None)
        self._kp_locked_turns: int = int(getattr(token, "supply_kp_lock_turns", 0) or 0)
        self._persist_state()

    def on_turn_start(self, memory: Dict[str, Any]) -> None:
        super().on_turn_start(memory)
        # Dekrementacja blokady KP
        if self._kp_locked_turns > 0:
            self._kp_locked_turns -= 1
        self._persist_state()

    def extend_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context = super().extend_context(context)
        # Wybór najlepszego KP
        board = context.get("board")
        if board and hasattr(board, "key_points"):
            best_kp = self._choose_best_kp(context)
            if best_kp:
                context["supply_target_kp"] = best_kp
                if best_kp != self._assigned_kp:
                    old_kp = self._assigned_kp
                    self._assigned_kp = best_kp
                    self._kp_locked_turns = 3  # Blokada na 3 tury
                    self._persist_state()
                    _flag(context, "zmiana_celu_kp")

                    # Zwięzły opis do raportu
                    scoring = context.get("kp_scoring_details", {})
                    context["human_note"] = self._format_target_note(old_kp, best_kp, scoring)
            elif self._assigned_kp:
                context["supply_target_kp"] = self._assigned_kp
        elif self._assigned_kp:
            context["supply_target_kp"] = self._assigned_kp

        objective = context.get("supply_target_kp") or self._assigned_kp
        if objective:
            context["specialist_objective"] = objective
        self._persist_state()
        return context

    def _choose_best_kp(self, context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Wybiera najlepszy Key Point – minimalistyczny scoring: wartość / dystans.
        
        Konwój nie ma wywiadu, nie zna całej mapy zagrożeń. Jedynie wybiera
        najbardziej wartościowy cel w zasięgu, unikając widzialnych wrogów.
        """
        board = context.get("board")
        if not board or not hasattr(board, "key_points"):
            return None

        my_pos = context.get("position")
        if None in my_pos:
            return None

        danger_zones = context.get("danger_zones", {})

        # Jeśli KP jest zablokowany i nie ma bezpośredniego zagrożenia, trzymamy cel
        if self._kp_locked_turns > 0 and self._assigned_kp:
            kp_danger = danger_zones.get(self._assigned_kp, 0)
            if kp_danger < 2:
                return self._assigned_kp

        candidates = []
        for kp_key, kp_data in board.key_points.items():
            # Parsuj klucz - może być string "q,r" lub tupla (q,r)
            if isinstance(kp_key, str):
                try:
                    parts = kp_key.split(",")
                    kp_hex = (int(parts[0]), int(parts[1]))
                except (ValueError, IndexError):
                    continue
            else:
                kp_hex = kp_key
            if not isinstance(kp_data, dict):
                continue
            kp_value = kp_data.get("value", 0)
            if kp_value <= 0:
                continue

            distance = self._hex_distance(my_pos, kp_hex, board)
            threat = danger_zones.get(kp_hex, 0)

            # Minimalistyczny scoring: wartość / dystans, mocna kara za widzianych wrogów
            score = kp_value / (distance + 1) - (threat * 3)
            candidates.append((score, kp_hex, kp_value, distance, threat))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0]
        
        # Diagnostyka do logu (dla raportu)
        context.setdefault("kp_scoring_details", {}).update({
            "best_kp": best[1],
            "kp_value": best[2],
            "distance": best[3],
            "threat": best[4],
            "score": round(best[0], 2),
        })
        
        return best[1]

    def _hex_distance(self, start: Tuple[int, int], end: Tuple[int, int], board) -> int:
        """Oblicza dystans hex (fallback do axial, jeśli board nie wspiera)."""
        if board and hasattr(board, "hex_distance"):
            try:
                return board.hex_distance(start, end)
            except Exception:
                pass
        # Fallback axial
        sq, sr = start
        eq, er = end
        return int((abs(sq - eq) + abs(sr - er) + abs((sq - sr) - (eq - er))) / 2)

    def suggest_movement_target(self, context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Konwój zawsze podąża do przypisanego KP."""
        target_kp = context.get("supply_target_kp") or self._assigned_kp
        my_pos = context.get("position")
        if target_kp and my_pos != target_kp:
            return target_kp
        return None

    def adjust_status(self, status: str, context: Dict[str, Any]) -> str:
        """Zaopatrzenie przy wysokim zagrożeniu przełącza się na retreat."""
        danger = (context.get("danger_zones") or {}).get(context.get("position"), 0)
        if danger >= 3 and status == "normal":
            _flag(context, "wrog_w_zasiegu")
            context["human_note"] = f"Wycofanie: wrogów {danger} w bezpośrednim zasięgu"
            return "threatened"
        return status

    def adjust_actions(
        self,
        planned_actions: List[str],
        status: str,
        context: Dict[str, Any],
        pe_budget: int,
    ) -> List[str]:
        """Konwoje nie atakują i priorytetyzują paliwo."""
        result = list(planned_actions)
        my_pos = context.get("position")

        # Priorytet paliwa
        fuel = context.get("current_fuel", 0)
        max_fuel = max(1, context.get("max_fuel", 1))
        fuel_pct = int(fuel / max_fuel * 100)
        if fuel < max_fuel * 0.8 and "refuel_minimum" not in result and pe_budget > 0:
            _flag(context, "niski_poziom_paliwa")
            result.insert(0, "refuel_minimum")
            context["human_note"] = f"Tankowanie: paliwo {fuel_pct}%"

        # Usuwamy atak i – tylko przy realnym zagrożeniu – dodajemy wycofanie
        if "attack" in result:
            result = [action for action in result if action != "attack"]
            danger_zones = context.get("danger_zones") or {}
            danger_here = danger_zones.get(my_pos, 0) if my_pos else 0
            visible_enemies = context.get("visible_enemies") or []
            board = context.get("board")
            nearest_enemy_distance = None
            if board and visible_enemies:
                distances = []
                for enemy in visible_enemies:
                    enemy_pos = getattr(enemy, "q", None), getattr(enemy, "r", None)
                    if None in enemy_pos:
                        continue
                    try:
                        distances.append(board.hex_distance(my_pos, enemy_pos))
                    except Exception:
                        continue
                if distances:
                    nearest_enemy_distance = min(distances)
            should_withdraw = (
                status in {"threatened", "urgent_retreat"}
                or danger_here >= 2
                or (nearest_enemy_distance is not None and nearest_enemy_distance <= 2)
            )
            has_objective = bool(context.get("supply_target_kp"))

            if should_withdraw or not has_objective:
                if "withdraw" not in result:
                    result.append("withdraw")
                if should_withdraw:
                    if "human_note" not in context:
                        context["human_note"] = "Wycofanie: zagrożenie w pobliżu"
                    _flag(context, "wycofanie_przy_zagrozeniu")
                elif "human_note" not in context:
                    context["human_note"] = "Unik walki: konwój bez zadania bojowego"
            else:
                result = [a for a in result if a != "withdraw"]
                if "human_note" not in context:
                    context["human_note"] = "Kontynuacja drogi do punktu zaopatrzenia"
            _flag(context, "pacyfista")

        # Przy garnizonie na KP: hold_position
        target_kp = context.get("supply_target_kp")
        if my_pos == target_kp and target_kp:
            _flag(context, "garnizon_na_kp")
            # Czyścimy maneuver, bo już jesteśmy na miejscu
            result = [a for a in result if a not in {"maneuver", "withdraw"}]
            self._persist_state()
            if "human_note" not in context:
                context["human_note"] = f"Garnizon: KP {target_kp} zabezpieczony"

        return result

    def _persist_state(self) -> None:
        setattr(self.token, "supply_assigned_kp", self._assigned_kp)
        setattr(self.token, "supply_kp_lock_turns", self._kp_locked_turns)

    @staticmethod
    def _format_target_note(
        old_kp: Optional[Tuple[int, int]],
        new_kp: Tuple[int, int],
        scoring: Optional[Dict[str, Any]],
    ) -> str:
        prefix = f"Cel {old_kp}→{new_kp}" if old_kp else f"Cel KP {new_kp}"
        if not scoring:
            return prefix
        kp_val = scoring.get("kp_value")
        dist = scoring.get("distance")
        threat = scoring.get("threat")
        score_val = scoring.get("score")
        details = []
        if kp_val is not None:
            details.append(f"wart {kp_val}")
        if dist is not None:
            details.append(f"dyst {dist}")
        if threat is not None:
            details.append(f"zag {threat}")
        if score_val is not None:
            details.append(f"score {score_val}")
        return prefix + (" | " + ", ".join(details) if details else "")


# ---------------------------------------------------------------------------
# Specjalista zwiadu
# ---------------------------------------------------------------------------


class ReconSpecialist(TokenSpecialist):
    """Specjalista zwiadu – optymalizuje wykrywanie i unika otwartej walki."""

    handled_types = {"R", "RECON"}

    def __init__(self, token, shared_intel: SharedIntelMemory):
        super().__init__(token, shared_intel)
        self._last_interest: Optional[Tuple[int, int]] = getattr(token, "recon_last_target", None)

    def extend_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context = super().extend_context(context)
        board = context.get("board")
        my_pos = context.get("position")
        if not board or not isinstance(my_pos, tuple) or None in my_pos:
            return context

        detection_map = context.get("enemy_detection") or {}
        shared_contacts = context.get("shared_enemy_detection") or {}
        danger_zones = context.get("danger_zones") or {}

        target = self._pick_interest_hex(
            my_pos,
            board,
            detection_map,
            shared_contacts,
            danger_zones,
        )

        if target:
            if target != self._last_interest:
                _flag(context, "nowy_cel_zwiadu")
            self._last_interest = target
            self._persist_state()
            context["recon_interest_hex"] = target
        elif self._last_interest:
            if self._distance(board, my_pos, self._last_interest) <= 8:
                context["recon_interest_hex"] = self._last_interest
                _flag(context, "utrzymany_cel")
            else:
                self._clear_target()

        context["recon_contacts"] = len(detection_map)
        return context

    def adjust_status(self, status: str, context: Dict[str, Any]) -> str:
        if status in {"urgent_retreat", "low_fuel"}:
            return status

        my_pos = context.get("position")
        danger_here = (context.get("danger_zones") or {}).get(my_pos, 0)
        heavy_close = self._count_heavy_enemies(context, max_distance=2)
        if danger_here >= 2 or heavy_close:
            _flag(context, "zagrozenie_dla_zwiadu")
            return "threatened"
        return status

    def adjust_movement_mode(self, movement_mode: str, status: str, context: Dict[str, Any]) -> str:
        if status in {"urgent_retreat", "threatened"}:
            return movement_mode

        current_mp = context.get("current_mp", 0)
        max_mp = max(1, context.get("max_mp", 1))
        current_fuel = context.get("current_fuel", 0)
        max_fuel = max(1, context.get("max_fuel", 1))

        if current_mp / max_mp >= 0.4 and current_fuel / max_fuel >= 0.4:
            if movement_mode != "recon":
                _flag(context, "tryb_recon")
            return "recon"
        return movement_mode

    def suggest_movement_target(self, context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        target = context.get("recon_interest_hex") or self._last_interest
        my_pos = context.get("position")
        if target and my_pos != target:
            return target
        return None

    def adjust_actions(
        self,
        planned_actions: List[str],
        status: str,
        context: Dict[str, Any],
        pe_budget: int,
    ) -> List[str]:
        result = list(planned_actions)
        if "attack" in result and not self._favorable_engagement(context):
            result = [action for action in result if action != "attack"]
            _flag(context, "unik_walki")

        if "maneuver" in result:
            result = [action for action in result if action != "maneuver"]
            result.insert(0, "maneuver")

        if "refuel_minimum" in result and context.get("current_fuel", 0) > context.get("max_fuel", 1) * 0.75:
            result = [action for action in result if action != "refuel_minimum"]

        return result

    def update_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        my_pos = context.get("position")
        target = context.get("recon_interest_hex") or self._last_interest
        if target and my_pos == target:
            _flag(context, "melduj_kontakt")
            note = self._format_contact_note(context, target)
            context["human_note"] = note
            self._clear_target()
        return context

    def after_turn(self, context: Dict[str, Any], reports: Dict[str, Any]) -> None:
        super().after_turn(context, reports)
        if context.get("enemy_detection"):
            context.setdefault("specialist_flags", set()).add("kontakt_zebrany")

    def _pick_interest_hex(
        self,
        my_pos: Tuple[int, int],
        board,
        detection_map: Dict[str, Dict[str, Any]],
        shared_contacts: Dict[str, Dict[str, Any]],
        danger_zones: Dict[Tuple[int, int], int],
    ) -> Optional[Tuple[int, int]]:
        candidates: List[Tuple[float, Tuple[int, int]]] = []

        for info in detection_map.values():
            q, r = info.get("q"), info.get("r")
            if q is None or r is None:
                continue
            target = (q, r)
            danger = danger_zones.get(target, 0)
            distance = self._distance(board, my_pos, target)
            if distance <= 0:
                continue
            detection_level = float(info.get("detection_level", 0.0) or 0.0)
            score = (1.0 - min(detection_level, 1.0)) * 5 + max(0, distance - 1) * 0.3 - danger
            candidates.append((score, target))

        for enemy_id, info in shared_contacts.items():
            if enemy_id in detection_map:
                continue
            q, r = info.get("q"), info.get("r")
            if q is None or r is None:
                continue
            target = (q, r)
            distance = self._distance(board, my_pos, target)
            danger = danger_zones.get(target, 0)
            timestamp = float(info.get("timestamp", 0) or 0)
            score = 1.5 + timestamp * 0.05 - danger - distance * 0.1
            candidates.append((score, target))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_target = candidates[0]
        if best_score <= 0:
            return None
        return best_target

    def _select_contact_summary(
        self,
        context: Dict[str, Any],
        target: Tuple[int, int],
    ) -> Optional[Dict[str, Any]]:
        detection_map = context.get("enemy_detection") or {}
        shared_contacts = context.get("shared_enemy_detection") or {}
        candidates: List[Tuple[int, float, float, Dict[str, Any]]] = []

        def consider(source_priority: int, data: Dict[str, Any]) -> None:
            q, r = data.get("q"), data.get("r")
            if q is None or r is None or (q, r) != target:
                return
            detection_level = float(
                data.get("detection_level")
                or data.get("confidence")
                or data.get("signal_strength")
                or 0.0
            )
            timestamp = float(data.get("timestamp") or 0.0)
            candidates.append((source_priority, detection_level, timestamp, data))

        for info in detection_map.values():
            consider(2, info)
        for info in shared_contacts.values():
            consider(1, info)

        if not candidates:
            return None

        candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        return candidates[0][3]

    def _format_contact_note(self, context: Dict[str, Any], target: Tuple[int, int]) -> str:
        contact = self._select_contact_summary(context, target)
        target_text = f"({target[0]},{target[1]})"
        if not contact:
            return f"Zwiad: cel {target_text} zweryfikowany, brak nowych kontaktów."

        label = contact.get("id") or contact.get("token_id") or contact.get("enemy_id") or "kontakt"
        unit_type = contact.get("type") or contact.get("category")
        detection_level = contact.get("detection_level") or contact.get("confidence")

        parts = [str(label)]
        if unit_type:
            parts.append(str(unit_type))
        if detection_level:
            try:
                parts.append(f"det={float(detection_level):.2f}")
            except (ValueError, TypeError):
                parts.append(f"det={detection_level}")

        summary = " ".join(parts)
        return f"Zwiad: potwierdzono {summary} w {target_text}."

    def _count_heavy_enemies(self, context: Dict[str, Any], max_distance: int = 2) -> int:
        board = context.get("board")
        my_pos = context.get("position")
        if not board or not isinstance(my_pos, tuple) or None in my_pos:
            return 0
        visible = context.get("visible_enemies") or []
        my_cv = context.get("max_cv", context.get("combat_value", 0)) or 0
        heavy = 0
        for enemy in visible:
            enemy_pos = (getattr(enemy, "q", None), getattr(enemy, "r", None))
            if None in enemy_pos:
                continue
            try:
                distance = board.hex_distance(my_pos, enemy_pos)
            except Exception:
                continue
            if max_distance is not None and distance > max_distance:
                continue
            enemy_cv = getattr(enemy, "combat_value", None)
            if enemy_cv is None:
                enemy_cv = getattr(enemy, "stats", {}).get("combat_value")
            enemy_cv = enemy_cv or 0
            if enemy_cv >= my_cv * 0.8:
                heavy += 1
        return heavy

    def _favorable_engagement(self, context: Dict[str, Any]) -> bool:
        visible = context.get("visible_enemies") or []
        if not visible:
            return False
        my_cv = context.get("combat_value", 0)
        if my_cv <= 0:
            return False
        weakest = min(
            (
                getattr(enemy, "combat_value", None)
                or getattr(enemy, "stats", {}).get("combat_value", 0)
                or 0
            )
            for enemy in visible
        )
        nearby_danger = (context.get("danger_zones") or {}).get(context.get("position"), 0)
        return weakest < my_cv * 0.7 and nearby_danger <= 1 and len(visible) == 1

    def _distance(self, board, start: Tuple[int, int], end: Tuple[int, int]) -> float:
        if board is None or not start or not end or None in (*start, *end):
            return 9999.0
        try:
            return float(board.hex_distance(start, end))
        except Exception:
            return 9999.0

    def _persist_state(self) -> None:
        setattr(self.token, "recon_last_target", self._last_interest)

    def _clear_target(self) -> None:
        self._last_interest = None
        setattr(self.token, "recon_last_target", None)


# ---------------------------------------------------------------------------
# Specjaliści ofensywni (kawaleria / piechota / czołgi / artyleria)
# ---------------------------------------------------------------------------


class CavalrySpecialist(TokenSpecialist):
    """Kawaleria: agresywne flankowanie i szybkie rajdy."""

    handled_types = {"K", "CAV"}

    def __init__(self, token, shared_intel: SharedIntelMemory):
        super().__init__(token, shared_intel)
        self._last_target: Optional[Tuple[int, int]] = getattr(token, "cavalry_last_target", None)

    def on_turn_start(self, memory: Dict[str, Any]) -> None:
        super().on_turn_start(memory)
        # Kawaleria żyje szybko – nie trzymamy celów dłużej niż 3 tury
        if memory.get("cavalry_target_cooldown"):
            memory["cavalry_target_cooldown"] = max(0, memory["cavalry_target_cooldown"] - 1)

    def extend_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context = super().extend_context(context)
        target = self._select_target_hex(context)
        if target:
            context["cavalry_target_hex"] = target
            if target != self._last_target:
                _flag(context, "kawaleria_nowy_cel")
                self._last_target = target
                setattr(self.token, "cavalry_last_target", target)
        elif self._last_target:
            context["cavalry_target_hex"] = self._last_target
        return context

    def adjust_status(self, status: str, context: Dict[str, Any]) -> str:
        if status == "urgent_retreat" and context.get("visible_enemies"):
            _flag(context, "kawaleria_mimo_strat")
            return "threatened"
        if status == "low_fuel" and context.get("current_fuel", 0) >= max(1, context.get("max_fuel", 1)) * 0.3:
            return "normal"
        return status

    def adjust_movement_mode(self, movement_mode: str, status: str, context: Dict[str, Any]) -> str:
        target = context.get("cavalry_target_hex")
        if target and not context.get("visible_enemies"):
            return "march"
        return movement_mode

    def suggest_movement_target(self, context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        return context.get("cavalry_target_hex") or self._last_target

    def adjust_actions(
        self,
        planned_actions: List[str],
        status: str,
        context: Dict[str, Any],
        pe_budget: int,
    ) -> List[str]:
        result = [action for action in planned_actions if action != "maneuver"]
        result.insert(0, "maneuver")

        max_cv = context.get("max_cv", 0) or 0
        combat_value = context.get("combat_value", 0) or 0
        if pe_budget > 0 and max_cv > 0 and combat_value < max_cv * 0.75:
            result = [action for action in result if action != "restore_cv"]
            insert_at = 1 if result and result[0] == "maneuver" else 0
            result.insert(insert_at, "restore_cv")
            _flag(context, "kawaleria_cv")

        visible = bool(context.get("visible_enemies")) or bool(context.get("shared_enemy_detection"))
        if visible and "attack" not in result:
            insert_at = 2 if result[:2] == ["maneuver", "restore_cv"] else 1
            result.insert(min(insert_at, len(result)), "attack")
            _flag(context, "kawaleria_atak")

        max_fuel = context.get("max_fuel", 0) or 0
        current_fuel = context.get("current_fuel", 0) or 0
        if max_fuel and current_fuel / max_fuel >= 0.65:
            result = [action for action in result if action != "refuel_minimum"]

        return result

    def update_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        target = context.get("cavalry_target_hex")
        if target and context.get("position") == target:
            context["human_note"] = "Kawaleria: flankowanie udane, cel osiągnięty."
            _flag(context, "kawaleria_flank")
        return context

    def _select_target_hex(self, context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        board = context.get("board")
        my_pos = context.get("position")
        visible = context.get("visible_enemies") or []
        if board and visible and my_pos and None not in my_pos:
            def score(enemy) -> float:
                enemy_pos = (getattr(enemy, "q", None), getattr(enemy, "r", None))
                if None in enemy_pos:
                    return -999.0
                try:
                    dist = board.hex_distance(my_pos, enemy_pos)
                except Exception:
                    dist = 99
                cv = getattr(enemy, "combat_value", None) or getattr(enemy, "stats", {}).get("combat_value", 6)
                return -dist + (6 - cv) * 0.2

            target_enemy = max(visible, key=score)
            enemy_pos = (getattr(target_enemy, "q", None), getattr(target_enemy, "r", None))
            if None not in enemy_pos:
                return enemy_pos
        return None


class InfantrySpecialist(TokenSpecialist):
    """Piechota: agresywne szturmy i utrzymanie zajętych heksów."""

    handled_types = {"P", "INF"}

    def __init__(self, token, shared_intel: SharedIntelMemory):
        super().__init__(token, shared_intel)
        self._focus_hex: Optional[Tuple[int, int]] = getattr(token, "infantry_focus_hex", None)

    def extend_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context = super().extend_context(context)
        target = self._select_focus_hex(context)
        if target:
            context["infantry_focus_hex"] = target
            if target != self._focus_hex:
                _flag(context, "piechota_nowt")
                self._focus_hex = target
                setattr(self.token, "infantry_focus_hex", target)
        elif self._focus_hex:
            context["infantry_focus_hex"] = self._focus_hex
        return context

    def suggest_movement_target(self, context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        target = context.get("infantry_focus_hex") or self._focus_hex
        if target and context.get("position") != target:
            return target
        return None

    def adjust_actions(
        self,
        planned_actions: List[str],
        status: str,
        context: Dict[str, Any],
        pe_budget: int,
    ) -> List[str]:
        result = list(planned_actions)
        max_cv = context.get("max_cv", 0) or 0
        combat_value = context.get("combat_value", 0) or 0
        if pe_budget > 0 and max_cv > 0 and combat_value < max_cv * 0.9:
            result = [action for action in result if action != "restore_cv"]
            result.insert(0, "restore_cv")
            _flag(context, "piechota_cv")

        focus_hex = context.get("infantry_focus_hex")
        if focus_hex and context.get("position") != focus_hex:
            if "maneuver" in result:
                result = [a for a in result if a != "maneuver"]
            insert_at = 1 if result and result[0] == "restore_cv" else 0
            result.insert(insert_at, "maneuver")
        elif "maneuver" in result and context.get("visible_enemies"):
            # Pozostajemy w zwarciu – manewr na koniec
            result = [a for a in result if a != "maneuver"]
            result.append("maneuver")

        if context.get("visible_enemies") and "attack" not in result:
            insert_at = 1 if result and result[0] == "restore_cv" else 0
            result.insert(insert_at, "attack")
            _flag(context, "piechota_atak")

        max_fuel = context.get("max_fuel", 0) or 0
        current_fuel = context.get("current_fuel", 0) or 0
        if max_fuel and current_fuel / max_fuel >= 0.75:
            result = [action for action in result if action != "refuel_minimum"]

        return result

    def update_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        focus_hex = context.get("infantry_focus_hex")
        if focus_hex and context.get("position") == focus_hex:
            context.setdefault("human_note", "Piechota: cel zdobyty, przygotowujemy obronę.")
            _flag(context, "piechota_hold")
        return context

    def _select_focus_hex(self, context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        board = context.get("board")
        my_pos = context.get("position")
        visible = context.get("visible_enemies") or []
        if board and visible and my_pos and None not in my_pos:
            def distance(enemy) -> int:
                enemy_pos = (getattr(enemy, "q", None), getattr(enemy, "r", None))
                if None in enemy_pos:
                    return 999
                try:
                    return board.hex_distance(my_pos, enemy_pos)
                except Exception:
                    return 999

            target_enemy = min(visible, key=distance)
            enemy_pos = (getattr(target_enemy, "q", None), getattr(target_enemy, "r", None))
            if None not in enemy_pos:
                return enemy_pos
        return None


class TankSpecialist(TokenSpecialist):
    """Czołgi i wozy pancerne: ofensywa z priorytetem CV."""

    handled_types = {"C", "T", "TL", "TS", "TŚ", "TC", "ARM"}

    VARIANT_RULES: Dict[str, Dict[str, Any]] = {
        "TL": {"role": "light", "cv_threshold": 0.85, "fuel_keep": 0.4},
        "TS": {"role": "car", "cv_threshold": 0.8, "fuel_keep": 0.5},
        "TŚ": {"role": "medium", "cv_threshold": 0.92, "fuel_keep": 0.35},
        "TC": {"role": "heavy", "cv_threshold": 0.97, "fuel_keep": 0.3},
    }

    def __init__(self, token, shared_intel: SharedIntelMemory):
        super().__init__(token, shared_intel)
        unit_type = (_normalize_unit_type(token) or "").upper()
        self.rules = dict(self.VARIANT_RULES.get(unit_type, {"role": "medium", "cv_threshold": 0.9, "fuel_keep": 0.35}))
        self.unit_type = unit_type

    def adjust_status(self, status: str, context: Dict[str, Any]) -> str:
        role = self.rules.get("role")
        if status == "urgent_retreat" and role in {"medium", "heavy"} and context.get("visible_enemies"):
            _flag(context, "czolg_trwa_w_natarciu")
            return "threatened"
        if status == "low_fuel" and context.get("visible_enemies"):
            return "normal"
        return status

    def adjust_movement_mode(self, movement_mode: str, status: str, context: Dict[str, Any]) -> str:
        role = self.rules.get("role")
        if role in {"light", "car"} and not context.get("visible_enemies"):
            return "march"
        return movement_mode

    def adjust_actions(
        self,
        planned_actions: List[str],
        status: str,
        context: Dict[str, Any],
        pe_budget: int,
    ) -> List[str]:
        result = list(planned_actions)
        role = self.rules.get("role")
        max_cv = context.get("max_cv", 0) or 0
        combat_value = context.get("combat_value", 0) or 0
        if pe_budget > 0 and max_cv > 0 and combat_value < max_cv * self.rules.get("cv_threshold", 0.9):
            result = [a for a in result if a != "restore_cv"]
            result.insert(0, "restore_cv")
            _flag(context, "czolg_cv")

        visible = bool(context.get("visible_enemies")) or bool(context.get("shared_enemy_detection"))
        if visible:
            if "attack" in result:
                result.remove("attack")
            insert_at = 1 if result and result[0] == "restore_cv" else 0
            result.insert(insert_at, "attack")
            _flag(context, "czolg_atak")
        elif role in {"light", "car"} and "attack" in result:
            # Gdy brak celu – poluj dalej
            result.remove("attack")
            result.append("attack")

        if "maneuver" in result and role in {"medium", "heavy"}:
            result.remove("maneuver")
            result.append("maneuver")
        elif "maneuver" in result and role in {"light", "car"}:
            result.remove("maneuver")
            insert_at = 1 if result and result[0] == "restore_cv" else 0
            result.insert(insert_at, "maneuver")

        max_fuel = context.get("max_fuel", 0) or 0
        current_fuel = context.get("current_fuel", 0) or 0
        if max_fuel and current_fuel / max_fuel >= self.rules.get("fuel_keep", 0.35) + 0.35:
            result = [a for a in result if a != "refuel_minimum"]

        return result


class ArtillerySpecialist(TokenSpecialist):
    """Artyleria: ciągły ogień i bezpieczne repozycjonowanie."""

    handled_types = {"AL", "AC", "AP", "AR", "ART"}

    def __init__(self, token, shared_intel: SharedIntelMemory):
        super().__init__(token, shared_intel)
        unit_type = (_normalize_unit_type(token) or "").upper()
        if unit_type in {"AL"}:
            self.variant = "light"
        elif unit_type in {"AC"}:
            self.variant = "heavy"
        elif unit_type in {"AP", "AR"}:
            self.variant = "aa"
        else:
            self.variant = "heavy"
        self._needs_reposition = False

    def on_turn_start(self, memory: Dict[str, Any]) -> None:
        super().on_turn_start(memory)
        # Jeżeli poprosiliśmy o repozycjonowanie w poprzedniej turze – realizujemy teraz
        if self._needs_reposition:
            memory["artillery_reposition"] = True

    def extend_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context = super().extend_context(context)
        context["artillery_variant"] = self.variant
        if self.variant == "light" and self._needs_reposition:
            _flag(context, "arty_reposition")
            context.setdefault("human_note", "Artyleria: zmiana pozycji po salwie.")
        return context

    def adjust_actions(
        self,
        planned_actions: List[str],
        status: str,
        context: Dict[str, Any],
        pe_budget: int,
    ) -> List[str]:
        if self.variant == "aa":
            return list(planned_actions)

        result = list(planned_actions)

        if self._needs_reposition:
            if "maneuver" in result:
                result.remove("maneuver")
            result.insert(0, "maneuver")
            _flag(context, "arty_ruch_po_salve")

        if context.get("visible_enemies") and "attack" not in result:
            insert_at = 1 if result and result[0] == "maneuver" else 0
            result.insert(insert_at, "attack")

        if pe_budget > 0 and context.get("max_cv", 0) and context.get("combat_value", 0) < context["max_cv"] * (0.9 if self.variant == "heavy" else 0.85):
            result = [a for a in result if a != "restore_cv"]
            insert_at = 1 if result and result[0] == "maneuver" else 0
            result.insert(insert_at, "restore_cv")

        return result

    def after_turn(self, context: Dict[str, Any], reports: Dict[str, Any]) -> None:
        super().after_turn(context, reports)
        if self.variant == "aa":
            return
        attack_report = reports.get("attack")
        if attack_report:
            self._needs_reposition = True
        movement_report = reports.get("movement") or {}
        if movement_report.get("success"):
            self._needs_reposition = False



# ---------------------------------------------------------------------------
# Rejestr i fabryka specjalistów
# ---------------------------------------------------------------------------


SPECIALIST_CLASSES: List[Type[TokenSpecialist]] = [
    SupplySpecialist,
    ReconSpecialist,
    CavalrySpecialist,
    InfantrySpecialist,
    TankSpecialist,
    ArtillerySpecialist,
]


def _normalize_unit_type(token) -> str:
    """Wydobywa znormalizowany typ jednostki (np. 'Z', 'K', 'P')."""
    unit_type = None
    stats = getattr(token, "stats", {}) or {}
    raw = stats.get("unitType") or stats.get("unit_type")
    if raw:
        unit_type = str(raw).upper()
    else:
        # Spróbuj wydobyć kod prefixu z identyfikatora (np. "K_", "P_", "Z_")
        token_id = getattr(token, "id", "") or ""
        if "_" in token_id:
            unit_type = token_id.split("_")[0].upper()
    return unit_type or "GENERIC"


def build_specialist(token, shared_intel: Optional[SharedIntelMemory] = None) -> TokenSpecialist:
    """Buduje odpowiedniego specjalistę dla danego żetonu."""
    shared_intel = shared_intel or get_shared_intel_memory()
    normalized_type = _normalize_unit_type(token)
    for specialist_cls in SPECIALIST_CLASSES:
        if normalized_type in specialist_cls.handled_types:
            return specialist_cls(token, shared_intel)
    return GenericSpecialist(token, shared_intel)


def create_token_ai(token):
    """Publiczna fabryka AI – zachowuje kompatybilny podpis."""
    from .token_ai import TokenAI  # Opóźniony import, aby uniknąć cykli.

    specialist = build_specialist(token, get_shared_intel_memory())
    return TokenAI(token, specialist=specialist)


__all__ = [
    "SharedIntelMemory",
    "TokenSpecialist",
    "SupplySpecialist",
    "ReconSpecialist",
    "CavalrySpecialist",
    "InfantrySpecialist",
    "TankSpecialist",
    "ArtillerySpecialist",
    "build_specialist",
    "get_shared_intel_memory",
    "create_token_ai",
]