"""
Prosty kontekst tury dla loggerów PL.

Zapewnia globalne (per-proces) przechowywanie numeru bieżącej tury, aby
logger mógł wstrzyknąć pole 'turn' gdy nie zostało jawnie przekazane.
"""
from __future__ import annotations
from typing import Optional
import threading

_turn_ctx = threading.local()


def set_current_turn(turn: Optional[int]) -> None:
    """Ustawia bieżący numer tury w kontekście wątku."""
    _turn_ctx.current_turn = turn


def get_current_turn(default: Optional[int] = None) -> Optional[int]:
    """Zwraca bieżący numer tury z kontekstu (lub default jeśli brak)."""
    return getattr(_turn_ctx, 'current_turn', default)


def clear_current_turn() -> None:
    """Czyści zapisany numer tury."""
    if hasattr(_turn_ctx, 'current_turn'):
        delattr(_turn_ctx, 'current_turn')

# --- correlation_id dla korelowania wpisów w obrębie jednej decyzji/akcji ---

def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Ustawia bieżący correlation_id dla powiązania wpisów logów.

    Zalecane: ustawiaj przed blokiem działań (np. analiza ruchu/ataku),
    a po zakończeniu wyczyść przez clear_correlation_id().
    """
    _turn_ctx.correlation_id = correlation_id


def get_correlation_id(default: Optional[str] = None) -> Optional[str]:
    """Zwraca bieżący correlation_id (lub default jeśli brak)."""
    return getattr(_turn_ctx, 'correlation_id', default)


def clear_correlation_id() -> None:
    """Czyści zapisany correlation_id."""
    if hasattr(_turn_ctx, 'correlation_id'):
        delattr(_turn_ctx, 'correlation_id')
