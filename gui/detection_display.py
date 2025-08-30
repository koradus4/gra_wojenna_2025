"""
GUI Helper - Graduowana widoczność dla interfejsu użytkownika
POZIOM 1: Podstawowe wyświetlanie informacji w zależności od detection_level
"""

def get_display_info_for_enemy(token, detection_level=1.0):
    """Zwraca informacje do wyświetlenia w GUI na podstawie poziomu detekcji
    
    Args:
        token: Obiekt Token wroga
        detection_level: Poziom detekcji 0.0-1.0
        
    Returns:
        dict: Informacje do wyświetlenia w GUI
    """
    if detection_level >= 0.8:
        # PEŁNA INFORMACJA
        return {
            'display_name': getattr(token, 'id', 'Unknown'),
            'combat_value': str(getattr(token, 'combat_value', '?')),
            'nation': token.stats.get('nation', 'Unknown'),
            'unit_type': token.stats.get('type', 'Unknown'),
            'tooltip': f"Pełna identyfikacja (poziom pewności: {detection_level:.0%})",
            'style': 'full_info',  # CSS class dla pełnych informacji
            'icon_opacity': 1.0
        }
    elif detection_level >= 0.5:
        # CZĘŚCIOWA INFORMACJA
        cv = getattr(token, 'combat_value', 0)
        estimated_cv = f"~{max(1, cv-2)}-{cv+2}"
        
        return {
            'display_name': f"Kontakt #{token.id[-2:] if hasattr(token, 'id') else '??'}",
            'combat_value': estimated_cv,
            'nation': token.stats.get('nation', 'Prawdopodobnie...'),
            'unit_type': estimate_unit_category(token),
            'tooltip': f"Częściowa identyfikacja (poziom pewności: {detection_level:.0%})",
            'style': 'partial_info',  # CSS class dla częściowych informacji
            'icon_opacity': 0.7
        }
    else:
        # MINIMALNA INFORMACJA
        return {
            'display_name': "Nieznany kontakt",
            'combat_value': "???",
            'nation': "???",
            'unit_type': "Kontakt",
            'tooltip': f"Minimalny kontakt (poziom pewności: {detection_level:.0%})",
            'style': 'minimal_info',  # CSS class dla minimalnych informacji
            'icon_opacity': 0.4
        }

def estimate_unit_category(token):
    """Szacuj kategorię jednostki na podstawie widocznych cech"""
    cv = getattr(token, 'combat_value', 0)
    
    if cv <= 3:
        return "Lekka jednostka"
    elif cv <= 6:
        return "Średnia jednostka"  
    else:
        return "Ciężka jednostka"

def get_map_display_symbol(token, detection_level=1.0):
    """Zwraca symbol do wyświetlenia na mapie
    
    Args:
        token: Obiekt Token
        detection_level: Poziom detekcji
        
    Returns:
        dict: Informacje o symbolu
    """
    base_symbol = "🔲"  # Podstawowy symbol jednostki
    
    if detection_level >= 0.8:
        # Pełny symbol z detalami
        unit_type = token.stats.get('type', 'unknown')
        if 'tank' in unit_type.lower():
            symbol = "🟫"  # Czołg
        elif 'infantry' in unit_type.lower():
            symbol = "👥"  # Piechota
        elif 'artillery' in unit_type.lower():
            symbol = "💥"  # Artyleria
        else:
            symbol = "🔲"  # Ogólna jednostka
            
        return {
            'symbol': symbol,
            'opacity': 1.0,
            'border': 'solid',
            'tooltip_prefix': 'Zidentyfikowany:'
        }
    elif detection_level >= 0.5:
        # Częściowy symbol
        return {
            'symbol': "❓",  # Znak zapytania
            'opacity': 0.8,
            'border': 'dashed',
            'tooltip_prefix': 'Prawdopodobnie:'
        }
    else:
        # Minimalny symbol
        return {
            'symbol': "⚫",  # Kropka
            'opacity': 0.5,
            'border': 'dotted',
            'tooltip_prefix': 'Kontakt:'
        }

def should_show_in_list(token, detection_level=1.0, min_detection=0.3):
    """Sprawdź czy token powinien być pokazany na liście jednostek
    
    Args:
        token: Obiekt Token
        detection_level: Poziom detekcji
        min_detection: Minimalny poziom do pokazania
        
    Returns:
        bool: True jeśli pokazać
    """
    return detection_level >= min_detection

def format_detection_status(detection_level):
    """Formatuj status detekcji dla UI"""
    if detection_level >= 0.8:
        return "🔍 Zidentyfikowany"
    elif detection_level >= 0.5:
        return "👁️ Częściowo rozpoznany"
    elif detection_level >= 0.3:
        return "📡 Wykryty kontakt"
    else:
        return "❔ Nieznany"

def get_info_panel_content(token, detection_level=1.0):
    """Zwraca zawartość panelu informacyjnego dla tokena
    
    Returns:
        dict: Zawartość panelu z uwzględnieniem poziomu detekcji
    """
    display_info = get_display_info_for_enemy(token, detection_level)
    
    content = {
        'title': display_info['display_name'],
        'status': format_detection_status(detection_level),
        'fields': []
    }
    
    # Dodaj pola w zależności od poziomu detekcji
    if detection_level >= 0.8:
        content['fields'] = [
            ('Siła bojowa', display_info['combat_value']),
            ('Nacja', display_info['nation']),
            ('Typ jednostki', display_info['unit_type']),
            ('Pozycja', f"({token.q}, {token.r})"),
        ]
    elif detection_level >= 0.5:
        content['fields'] = [
            ('Szacowana siła', display_info['combat_value']),
            ('Prawdopodobna nacja', display_info['nation']),
            ('Kategoria', display_info['unit_type']),
            ('Pozycja', f"({token.q}, {token.r})"),
        ]
    else:
        content['fields'] = [
            ('Siła bojowa', 'Nieznana'),
            ('Pochodzenie', 'Nieznane'),
            ('Typ', 'Nieznany'),
            ('Pozycja', f"({token.q}, {token.r})"),
        ]
    
    return content

# CSS styles dla różnych poziomów informacji
GUI_STYLES = """
.full_info {
    border: 2px solid #00ff00;
    background-color: rgba(0, 255, 0, 0.1);
    color: #ffffff;
}

.partial_info {
    border: 2px dashed #ffff00;
    background-color: rgba(255, 255, 0, 0.1);
    color: #cccccc;
}

.minimal_info {
    border: 2px dotted #ff6600;
    background-color: rgba(255, 102, 0, 0.1);
    color: #999999;
}

.detection_high { opacity: 1.0; }
.detection_medium { opacity: 0.7; }
.detection_low { opacity: 0.4; }
"""

# Eksport funkcji
__all__ = [
    'get_display_info_for_enemy',
    'get_map_display_symbol', 
    'should_show_in_list',
    'format_detection_status',
    'get_info_panel_content',
    'GUI_STYLES'
]
