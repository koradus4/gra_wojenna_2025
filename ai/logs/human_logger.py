"""Human action logging utilities.

This module mirrors the structure of :mod:`ai.logs.ai_logger` but focuses on
recording what the human player does during Human vs AI sessions.  Logs are
written both to a text file (readable summary) and to a CSV file (structured
for later analytics).
"""
from __future__ import annotations

import csv
import datetime as _dt
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

__all__ = [
    "HumanActionLogger",
    "log_human_action",
    "get_human_logger",
]


def _sanitize_value(value: Any) -> Any:
    """Convert values to JSON-friendly representations."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _sanitize_value(v) for k, v in value.items()}
    return str(value)


def _sanitize_context(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not context:
        return {}
    return {str(key): _sanitize_value(value) for key, value in context.items()}


@dataclass
class PlayerSnapshot:
    """Minimal information about a player for logging purposes."""

    player_type: str
    player_id: Optional[int]
    nation: Optional[str]
    role: Optional[str]
    name: Optional[str]

    @classmethod
    def from_player(cls, player: Any) -> "PlayerSnapshot":
        if player is None:
            return cls("UNKNOWN", None, None, None, None)
        player_type = "AI" if getattr(player, "is_ai", False) else "HUMAN"
        player_id = getattr(player, "id", None)
        nation = getattr(player, "nation", None)
        role = getattr(player, "role", None)
        name = getattr(player, "name", None)
        return cls(player_type, player_id, nation, role, name)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_type": self.player_type,
            "player_id": self.player_id,
            "player_nation": self.nation,
            "player_role": self.role,
            "player_name": self.name,
        }

    def format_for_text(self) -> str:
        parts = []
        if self.player_id is not None:
            parts.append(f"ID={self.player_id}")
        if self.nation:
            parts.append(self.nation)
        if self.role:
            parts.append(self.role)
        if self.name and self.name not in parts:
            parts.append(self.name)
        descriptor = ", ".join(parts) if parts else "nieznany gracz"
        return f"{self.player_type}({descriptor})"


class HumanActionLogger:
    """Centralised logger dedicated to human (and optionally AI) actions."""

    def __init__(self, log_dir: Optional[str] = None) -> None:
        if log_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(current_dir, "human")
        self._base_dir = log_dir
        self._text_dir = os.path.join(self._base_dir, "text")
        self._csv_dir = os.path.join(self._base_dir, "csv")
        for path in (self._base_dir, self._text_dir, self._csv_dir):
            os.makedirs(path, exist_ok=True)
        self._current_date = ""
        self._text_path: Optional[str] = None
        self._csv_path: Optional[str] = None
        self._ensure_current_paths()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_current_paths(self) -> None:
        today = _dt.datetime.now().strftime("%Y-%m-%d")
        if today == self._current_date and self._text_path and self._csv_path:
            return
        self._current_date = today
        self._text_path = os.path.join(self._text_dir, f"{today}.log")
        self._csv_path = os.path.join(self._csv_dir, f"{today}.csv")
        if not os.path.exists(self._csv_path):
            with open(self._csv_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "timestamp",
                        "turn",
                        "player_type",
                        "player_id",
                        "player_nation",
                        "player_role",
                        "player_name",
                        "action_type",
                        "summary",
                        "result",
                        "context",
                    ],
                )
                writer.writeheader()

    def _append_text_entry(self, timestamp: _dt.datetime, player: PlayerSnapshot, turn: Optional[int], action_type: str, summary: str, result: Optional[str], context: Dict[str, Any]) -> None:
        if not self._text_path:
            return
        turn_txt = f"TURA {turn}" if turn is not None else "TURA ?"
        result_txt = f" | wynik={result}" if result else ""
        context_txt = ""
        if context:
            serialised_context = ", ".join(f"{key}={value}" for key, value in context.items())
            context_txt = f" | {serialised_context}"
        entry = (
            f"[{timestamp.strftime('%H:%M:%S')}] "
            f"[{turn_txt}] "
            f"[{player.format_for_text()}] "
            f"{action_type}: {summary}{result_txt}{context_txt}\n"
        )
        with open(self._text_path, "a", encoding="utf-8") as handle:
            handle.write(entry)

    def _append_csv_entry(self, timestamp: _dt.datetime, player: PlayerSnapshot, turn: Optional[int], action_type: str, summary: str, result: Optional[str], context: Dict[str, Any]) -> None:
        if not self._csv_path:
            return
        payload = {
            "timestamp": timestamp.isoformat(timespec="seconds"),
            "turn": turn,
            "player_type": player.player_type,
            "player_id": player.player_id,
            "player_nation": player.nation,
            "player_role": player.role,
            "player_name": player.name,
            "action_type": action_type,
            "summary": summary,
            "result": result,
            "context": json.dumps(context, ensure_ascii=False) if context else "",
        }
        with open(self._csv_path, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(payload.keys()))
            writer.writerow(payload)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def log_action(
        self,
        player: PlayerSnapshot,
        turn: Optional[int],
        action_type: str,
        summary: str,
        result: Optional[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._ensure_current_paths()
        timestamp = _dt.datetime.now()
        safe_context = _sanitize_context(context)
        try:
            self._append_text_entry(timestamp, player, turn, action_type, summary, result, safe_context)
            self._append_csv_entry(timestamp, player, turn, action_type, summary, result, safe_context)
        except Exception as exc:  # pragma: no cover - safety net
            print(f"⚠️ [HumanActionLogger] Nie udało się zapisać logu: {exc}")


# ----------------------------------------------------------------------
# Global helper
# ----------------------------------------------------------------------
_human_logger: Optional[HumanActionLogger] = None


def get_human_logger() -> HumanActionLogger:
    global _human_logger
    if _human_logger is None:
        _human_logger = HumanActionLogger()
    return _human_logger


def log_human_action(
    player: Any,
    turn: Optional[int],
    action_type: str,
    summary: str,
    result: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Convenience wrapper used by the engine.

    Parameters
    ----------
    player:
        Player instance (or compatible object).
    turn:
        Active turn number; ``None`` if unknown.
    action_type:
        Short action identifier, e.g. ``"move"`` or ``"attack"``.
    summary:
        Human readable summary explaining co i jak.
    result:
        Optional result string (success / error message).
    context:
        Extra data serialised to JSON for post-processing.
    """

    snapshot = PlayerSnapshot.from_player(player)
    logger = get_human_logger()
    logger.log_action(snapshot, turn, action_type, summary, result, context)
