"""
Panel konfiguracji AI – wycofany.

Moduł AI został usunięty, więc panel ustawień AI nie jest dostępny.
"""

from tkinter import ttk


class AIConfigPanel:
    def __init__(self, parent_frame: ttk.Frame, compact_mode: bool = False):
        self.parent = parent_frame
        raise RuntimeError(
            "Panel konfiguracji AI został wycofany – AI usunięte z projektu."
        )