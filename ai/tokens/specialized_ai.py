"""
Minimalna fabryka AI żetonów.

W aktualnym trybie wszystkie żetony korzystają z tej samej, uproszczonej
implementacji TokenAI. Plik pozostawiono dla kompatybilności importów.
"""
from __future__ import annotations

from .token_ai import TokenAI


def create_token_ai(token) -> TokenAI:
    """Zwraca instancję minimalnego TokenAI niezależnie od typu żetonu."""
    return TokenAI(token)