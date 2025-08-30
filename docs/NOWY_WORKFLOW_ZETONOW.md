# Nowy Workflow Żetonów w Map Editor

## 🎯 Główne Funkcje

### Stała Paleta Żetonów
- **Lokalizacja**: Panel boczny (prawa strona)
- **Źródło danych**: `assets/tokens/index.json` (ładowany raz na start)
- **Miniaturki**: 32x32 pikseli z etykietami
- **Auto-refresh**: Po każdej zmianie mapy

### Filtry
- **Checkbox Unikalność**: ON (domyślnie) - ukrywa już użyte żetony
- **Przyciski Nacji**: Wszystkie/Polska/Niemcy (wzajemnie wykluczające)
- **Dropdown Typ**: Wybór typu jednostki (AL, K, P, itp.)
- **Dropdown Rozmiar**: Pluton/Kompania/Batalion
- **Pole wyszukiwania**: Filtr po ID lub nazwie (live search)

## 🖱️ Tryby Selekcji

### Podstawowy Workflow
1. **LPM na żeton w palecie**: Wybiera żeton (podświetlenie pomarańczowe)
2. **LPM na mapie**: Wstawia wybrany żeton
3. **Automatyczne wyczyszczenie selekcji** (chyba że Shift)

### Zaawansowane Opcje
- **Shift+LPM**: Tryb wielokrotnego wstawiania (bez resetowania selekcji)
- **PPM na mapie**: Usuwa żeton z heksu
- **Delete (klawisz)**: Usuwa żeton z zaznaczonego heksu
- **LPM w pustą przestrzeń**: Czyści wybór żetonu

## 👻 Ghost Preview
- **Półprzezroczysta miniatura** pod kursorem
- **Zielona obwódka**: Można postawić żeton
- **Czerwona obwódka + ✗**: Blokada (duplikat w trybie unikalności)
- **Zoom istniejących żetonów**: Powiększenie przy hover

## 💾 Auto-Save System
- **Natychmiastowy zapis**: `map_data.json` przy każdej zmianie
- **Debounce eksport**: `start_tokens.json` (500ms opóźnienie)
- **Brak popup-ów**: Tylko console output

## 🔍 Mini Panel Walidacji
- **Liczba żetonów per nacja**: Polska: X, Niemcy: Y
- **🔴 Duplikaty**: Liczba duplikatów (jeśli unikalność ON)
- **🟡 Brakujące obrazy**: Liczba martwych linków
- **Auto-refresh**: Co 3 sekundy

## ⚙️ Struktura Danych (Bez Zmian)
```json
hex_data[hex_id]["token"] = {
    "unit": "token_id",
    "image": "relative/path/to/image.png"
}

start_tokens.json = [
    {"id": "token_id", "q": 1, "r": 2},
    ...
]
```

## 🎮 Skróty Klawiszowe
- **Delete**: Usuń żeton z zaznaczonego heksu
- **Shift (hold)**: Tryb wielokrotnego wstawiania
- **Mouse Wheel**: Przewijanie palety żetonów

## 🔄 Kompatybilność
- **Zachowane stare metody**: Dialog żetonów nadal istnieje (przestarzały)
- **Struktura danych**: Pełna kompatybilność wsteczna
- **Eksport**: Ten sam format `start_tokens.json`

## 🐛 Edge Cases
- **Brakujące obrazy**: Automatyczne usuwanie z mapy
- **Nieistniejące żetony**: Filtrowanie przy ładowaniu
- **Duplikaty w trybie unikalności**: Wizualna blokada
- **Zniszczone dialogi**: Graceful fallback
- **Przewijanie palety**: Mouse wheel support

## 🚀 Korzyści
1. **Szybkość**: Brak okien dialogowych
2. **Wygoda**: Wszystko w jednym miejscu
3. **Przejrzystość**: Live preview i walidacja
4. **Unikalność**: Kontrola duplikatów
5. **Auto-save**: Brak straconej pracy
6. **Elastyczność**: Filtry na żywo

## 🔮 Przyszłe Rozszerzenia
- **Cofnij/Odtwórz**: Stos ostatnich 50 operacji
- **Drag & Drop**: Przeciąganie żetonów między heksami
- **Bulk Operations**: Zaznaczanie wielu heksów
- **Custom Categories**: Własne grupy żetonów
- **Quick Stats**: Analiza sił per nacja
