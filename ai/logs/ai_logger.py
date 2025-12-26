"""
System logowania AI - centralne logowanie wszystkich działań AI
"""
import csv
import datetime
import json
import os
from typing import Any, Dict, Optional

class AILogger:
    """Centralne logowanie działań AI"""

    def __init__(self, log_dir: str = None):
        if log_dir is None:
            # Domyślny folder logs w ai/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.log_dir = current_dir
        else:
            self.log_dir = log_dir

        # Utwórz folder jeśli nie istnieje
        os.makedirs(self.log_dir, exist_ok=True)

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        self._current_date = today

        # Przygotuj strukturę katalogów dla poszczególnych komponentów
        self._component_paths: Dict[str, Dict[str, str]] = {
            "GENERAL": self._prepare_component_paths("general"),
            "COMMANDER": self._prepare_component_paths("commander"),
            "TOKEN": self._prepare_component_paths("tokens"),
            "DEBUG": self._prepare_component_paths("debug"),
        }

    def _prepare_component_paths(self, folder_name: str) -> Dict[str, str]:
        component_root = os.path.join(self.log_dir, folder_name)
        text_dir = os.path.join(component_root, "text")
        csv_dir = os.path.join(component_root, "csv")

        for path in (component_root, text_dir, csv_dir):
            os.makedirs(path, exist_ok=True)

        return {
            "text": os.path.join(text_dir, f"{self._current_date}.log"),
            "csv": os.path.join(csv_dir, f"{self._current_date}.csv"),
        }

    def _format_context_for_text(self, context: Dict[str, Any]) -> str:
        if not context:
            return ""
        formatted_pairs = ", ".join(f"{key}={value}" for key, value in context.items())
        return f" | {formatted_pairs}"

    def _format_context_for_console(self, context: Dict[str, Any]) -> str:
        if not context:
            return ""
        formatted_pairs = ", ".join(f"{key}={value}" for key, value in context.items())
        return f" [{formatted_pairs}]"

    def _write_text_entry(self, component: str, timestamp: str, level: str, message: str, context: Dict[str, Any]):
        log_file = self._component_paths[component]["text"]
        log_entry = f"[{timestamp}] [{level}] [{component}] {message}{self._format_context_for_text(context)}\n"

        try:
            with open(log_file, "a", encoding="utf-8") as file_handle:
                file_handle.write(log_entry)
        except Exception as error:
            print(f"⚠️ Błąd zapisu loga (text): {error}")

    def _write_csv_entry(self, component: str, iso_timestamp: str, level: str, message: str, context: Dict[str, Any]):
        log_file = self._component_paths[component]["csv"]
        fieldnames = ["timestamp", "component", "level", "message", "context"]
        serialized_context = json.dumps(context, ensure_ascii=False) if context else ""

        try:
            file_exists = os.path.exists(log_file)
            with open(log_file, "a", newline="", encoding="utf-8") as file_handle:
                writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(
                    {
                        "timestamp": iso_timestamp,
                        "component": component,
                        "level": level,
                        "message": message,
                        "context": serialized_context,
                    }
                )
        except Exception as error:
            print(f"⚠️ Błąd zapisu loga (csv): {error}")

    def _log(self, component: str, message: str, level: str, console_label: str, console_icon: str, context: Dict[str, Any], force_console: bool = False):
        now = datetime.datetime.now()
        timestamp = now.strftime("%H:%M:%S")
        iso_timestamp = now.isoformat(timespec="seconds")

        safe_context = context or {}

        self._write_text_entry(component, timestamp, level, message, safe_context)
        self._write_csv_entry(component, iso_timestamp, level, message, safe_context)

        if force_console or level == "DEBUG":
            console_context = self._format_context_for_console(safe_context)
            print(f"{console_icon} [{console_label}] {message}{console_context}")
    
    def log_general(self, message: str, level: str = "INFO", **context: Any):
        """Loguje działania AI Generała"""
        self._log("GENERAL", message, level, "AI-GEN", "🎖️", context, force_console=False)
    
    def log_commander(self, message: str, level: str = "INFO", **context: Any):
        """Loguje działania AI Komendanta"""
        self._log("COMMANDER", message, level, "AI-CMD", "⚔️", context, force_console=False)
    
    def log_token(self, message: str, level: str = "INFO", **context: Any):
        """Loguje działania żetonów AI"""
        self._log("TOKEN", message, level, "AI-TOK", "🤖", context, force_console=False)
    
    def log_debug(self, message: str, **context: Any):
        """Loguje informacje debugowe"""
        self._log("DEBUG", message, "DEBUG", "AI-DBG", "🐛", context, force_console=True)
    
    def log_error(self, message: str, component: str = "GENERAL", **context: Any):
        """Loguje błędy AI"""
        combined_context = {"source": component}
        combined_context.update(context)
        self._log("DEBUG", message, "ERROR", "AI-ERR", "❌", combined_context, force_console=True)


# Globalna instancja loggera AI
_ai_logger: Optional[AILogger] = None

def get_ai_logger() -> AILogger:
    """Zwraca globalną instancję AI loggera"""
    global _ai_logger
    if _ai_logger is None:
        _ai_logger = AILogger()
    return _ai_logger

def _sanitize_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Zapobiega kolizji nazw parametrów przy delegowaniu do loggera."""
    if not context:
        return {}

    sanitized = dict(context)
    if "level" in sanitized:
        sanitized["context_level"] = sanitized.pop("level")
    return sanitized


def log_general(message: str, level: str = "INFO", **context: Any):
    """Skrót do logowania generała"""
    get_ai_logger().log_general(message, level, **_sanitize_context(context))


def log_commander(message: str, level: str = "INFO", **context: Any):
    """Skrót do logowania komendanta"""
    get_ai_logger().log_commander(message, level, **_sanitize_context(context))


def log_token(message: str, level: str = "INFO", **context: Any):
    """Skrót do logowania tokenów"""
    get_ai_logger().log_token(message, level, **_sanitize_context(context))


def log_debug(message: str, **context: Any):
    """Skrót do logowania debug"""
    get_ai_logger().log_debug(message, **_sanitize_context(context))


def log_error(message: str, component: str = "GENERAL", **context: Any):
    """Skrót do logowania błędów"""
    get_ai_logger().log_error(message, component, **_sanitize_context(context))