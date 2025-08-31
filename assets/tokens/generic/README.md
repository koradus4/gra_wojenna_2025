# Ikony kontaktów wroga na podstawie detection_level

## Struktura folderów
- `unknown_contact.png` - Minimalna informacja (detection_level < 0.5)
- `tank_contact.png` - Częściowa identyfikacja czołgu (0.5 <= detection_level < 0.8)
- `infantry_contact.png` - Częściowa identyfikacja piechoty (0.5 <= detection_level < 0.8)
- `artillery_contact.png` - Częściowa identyfikacja artylerii (0.5 <= detection_level < 0.8)

## Zasady wyświetlania
1. **detection_level >= 0.8**: Pełna ikona jednostki
2. **detection_level >= 0.5**: Generyczna ikona kategorii (tank_contact.png, etc.)
3. **detection_level < 0.5**: Ikona nieznany kontakt (unknown_contact.png)

## Wizualne wskazówki
- Przezroczystość ikony: 0.4 + (detection_level * 0.6)
- Tooltip z poziomem pewności: "Poziom pewności: XX%"
- Ukryte szczegóły w token_info_panel

## Implementacja
Ikony są wybierane przez `_get_token_image_path()` w `panel_mapa.py`
