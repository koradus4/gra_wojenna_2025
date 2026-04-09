# -*- coding: utf-8 -*-
"""
Moduł AI – gracz komputerowy dla gry Kampania 1939.

Eksportuje główne klasy agentów:
- BaseAgent        – klasa bazowa
- TacticalAgent    – decyzje ruchu i walki (dowódca)
- StrategicAgent   – priorytety key points, ekonomia, zakupy (generał)
"""

from .base_agent import BaseAgent
from .tactical_agent import TacticalAgent
from .strategic_agent import StrategicAgent

__all__ = [
    "BaseAgent",
    "TacticalAgent",
    "StrategicAgent",
]
