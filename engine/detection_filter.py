"""
Detection Filter - System graduowanej widoczności przeciwników
Poziom 1: Podstawowe filtrowanie informacji na podstawie detection_level
"""

def apply_detection_filter(token, detection_level=1.0):
    """Filtruje informacje o wrogu na podstawie poziomu detekcji
    
    Args:
        token: Obiekt Token wroga
        detection_level: Poziom detekcji 0.0-1.0
        
    Returns:
        dict: Przefiltrowane informacje o wrogu
    """
    if detection_level >= 0.8:
        # BLISKO - pełne informacje
        return {
            'id': token.id,
            'q': token.q,
            'r': token.r,
            'combat_value': getattr(token, 'combat_value', 0),
            'nation': token.stats.get('nation', 'Unknown'),
            'type': token.stats.get('type', 'Unknown'),
            'detection_level': detection_level,
            'info_quality': 'FULL'
        }
    elif detection_level >= 0.5:
        # ŚREDNIO - ograniczone informacje
        return {
            'id': f"CONTACT_{token.id[-3:]}",  # Skrócone ID
            'q': token.q,
            'r': token.r,
            'combat_value': f"~{estimate_range(getattr(token, 'combat_value', 0))}",
            'nation': token.stats.get('nation', 'Unknown'),  # Nacja widoczna z wyglądu
            'type': estimate_unit_type(token),
            'detection_level': detection_level,
            'info_quality': 'PARTIAL'
        }
    else:
        # DALEKO - minimalne informacje
        return {
            'id': "UNKNOWN_CONTACT",
            'q': token.q,
            'r': token.r,
            'combat_value': "???",
            'nation': "???",
            'type': "CONTACT",
            'detection_level': detection_level,
            'info_quality': 'MINIMAL'
        }

def estimate_range(value):
    """Szacuj przedział wartości dla częściowej detekcji"""
    if value <= 2:
        return "1-3"
    elif value <= 5:
        return "3-7"
    elif value <= 8:
        return "6-10"
    else:
        return "8+"

def estimate_unit_type(token):
    """Szacuj typ jednostki na podstawie widocznych cech"""
    # Prosty algorytm na podstawie statystyk
    combat_value = getattr(token, 'combat_value', 0)
    
    if combat_value <= 3:
        return "light_unit"
    elif combat_value <= 6:
        return "medium_unit"
    else:
        return "heavy_unit"

def get_detection_info_for_player(player, token_id, include_temp=True):
    """Pobierz informacje o detekcji konkretnego tokena dla gracza

    Args:
        player: Obiekt gracza
        token_id: ID tokena
        include_temp: Czy uwzględnić dane tymczasowe z bieżącej tury

    Returns:
        dict lub None: Informacje o detekcji (np. {'detection_level': 0.7, ...})
    """
    if not player or not token_id:
        return None

    # Najpierw spróbuj danych tymczasowych (aktualna tura / wizja ruchu)
    if include_temp and hasattr(player, 'temp_visible_token_data'):
        token_data = player.temp_visible_token_data.get(token_id)
        if token_data:
            return token_data

    # Zgodność wsteczna - stare implementacje używały persistent `visible_token_data`
    if hasattr(player, 'visible_token_data'):
        return player.visible_token_data.get(token_id)

    return None

def is_token_detected(player, token_id, min_detection_level=0.3):
    """Sprawdź czy token jest wykryty na wystarczającym poziomie
    
    Args:
        player: Obiekt gracza
        token_id: ID tokena
        min_detection_level: Minimalny poziom detekcji
        
    Returns:
        bool: True jeśli wykryty na wystarczającym poziomie
    """
    detection_info = get_detection_info_for_player(player, token_id)
    if not detection_info:
        return False
        
    return detection_info.get('detection_level', 0.0) >= min_detection_level

# Eksport funkcji
__all__ = [
    'apply_detection_filter', 
    'get_detection_info_for_player', 
    'is_token_detected',
    'estimate_range',
    'estimate_unit_type'
]
