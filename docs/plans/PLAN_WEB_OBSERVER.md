# 🌐 PLAN: OBSERWATOR GRY W PRZEGLĄDARCE

## 📋 CEL PROJEKTU
Stworzenie systemu do oglądania rozgrywki w czasie rzeczywistym przez przeglądarkę internetową jako obserwator (bez możliwości ingerencji w grę).

---

## 🎯 FUNKCJONALNOŚCI

### ✅ PODSTAWOWE
- **Mapa hexowa na żywo** - pozycje wszystkich żetonów
- **Panel aktualnego gracza** - kto teraz gra, jaką ma rolę
- **Ekonomia graczy** - punkty ekonomiczne każdej nacji
- **Informacje o turze** - numer tury, pogoda, czas pozostały
- **Automatyczne odświeżanie** co 5-10 sekund

### 🚀 ZAAWANSOWANE (OPCJONALNE)
- **Historia ruchów** - replay ostatnich akcji
- **Wykresy statystyk** - ekonomia, straty, zdobyte punkty
- **Zoom mapy** - przybliżanie konkretnych obszarów
- **Tryb mobilny** - oglądanie na telefonie/tablecie
- **Eksport do video** - nagrywanie całej rozgrywki

---

## 🛠️ ARCHITEKTURA TECHNICZNA

### 1. **EKSPORTER DANYCH (Python)**
```
Lokalizacja: utils/web_exporter.py
Zadanie: Eksportuje stan gry do JSON co turę
```

### 2. **SERWER WEB (Python)**
```
Lokalizacja: web_server/app.py
Framework: Flask (prosty serwer HTTP)
Port: 8080
```

### 3. **FRONTEND (HTML/JS)**
```
Lokalizacja: web_server/static/
Technologie:
- HTML5 + CSS3 (interfejs)
- JavaScript (logika)
- Leaflet.js (mapa hexowa)
- Chart.js (wykresy)
```

---

## 📁 STRUKTURA PLIKÓW

```
kampania1939_restored/
├── web_observer/
│   ├── server.py              # Serwer Flask
│   ├── templates/
│   │   └── index.html         # Główna strona
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css      # Style CSS
│   │   ├── js/
│   │   │   ├── main.js        # Główna logika JS
│   │   │   ├── map_renderer.js # Renderowanie mapy
│   │   │   └── data_updater.js # Aktualizacja danych
│   │   └── libs/              # Biblioteki JS
│   └── data/
│       └── game_state.json    # Aktualny stan gry
├── utils/
│   └── web_exporter.py        # Eksporter danych z gry
└── main_alternative.py        # MODYFIKACJA: dodaj eksport
```

---

## 🔧 IMPLEMENTACJA - KROK PO KROKU

### **FAZA 1: EKSPORTER DANYCH (1 dzień)**

#### 1.1 Stwórz eksporter (`utils/web_exporter.py`)
```python
def export_game_state(game_engine, players, turn_manager):
    """Eksportuje aktualny stan gry do JSON"""
    
def export_to_file(data, filepath="web_observer/data/game_state.json"):
    """Zapisuje dane do pliku JSON"""
```

#### 1.2 Zmodyfikuj `main_alternative.py`
- Dodaj import web_exporter
- Wywołaj eksport po każdej turze
- Miejsce: po linii `is_full_turn_end = turn_manager.next_turn()`

### **FAZA 2: SERWER WEB (0.5 dnia)**

#### 2.1 Stwórz serwer Flask (`web_observer/server.py`)
```python
from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/game_state')
def get_game_state():
    # Zwróć aktualny stan gry z JSON
```

#### 2.2 Uruchomienie serwera
```bash
cd web_observer
python server.py
# Serwer dostępny: http://localhost:8080
```

### **FAZA 3: FRONTEND - PODSTAWY (1 dzień)**

#### 3.1 HTML Template (`templates/index.html`)
```html
<!DOCTYPE html>
<html>
<head>
    <title>Kampania 1939 - Obserwator</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div id="game-container">
        <div id="map-container"></div>
        <div id="info-panel"></div>
    </div>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

#### 3.2 JavaScript Logika (`static/js/main.js`)
```javascript
// Automatyczne odświeżanie co 5 sekund
setInterval(updateGameState, 5000);

function updateGameState() {
    fetch('/api/game_state')
        .then(response => response.json())
        .then(data => {
            updateMap(data.tokens);
            updatePlayerInfo(data.current_player);
            updateEconomy(data.players);
        });
}
```

### **FAZA 4: MAPA HEXOWA (1 dzień)**

#### 4.1 Instaluj Leaflet.js
```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

#### 4.2 Renderer mapy (`static/js/map_renderer.js`)
```javascript
function initializeMap() {
    // Stwórz mapę Leaflet z custom hex grid
}

function renderTokens(tokens) {
    // Renderuj żetony na mapie
}

function updateTokenPositions(tokens) {
    // Aktualizuj pozycje żetonów
}
```

### **FAZA 5: PANELE INFORMACYJNE (0.5 dnia)**

#### 5.1 Panel gracza
- Aktualny gracz, rola, nacja
- Pozostały czas na turę
- Numer tury

#### 5.2 Panel ekonomii
- Punkty ekonomiczne każdej nacji
- Historia punktów (wykres)

---

## 🧪 TESTOWANIE

### 1. **Test lokalny**
```bash
# Terminal 1: Uruchom grę
python main_alternative.py

# Terminal 2: Uruchom serwer web
cd web_observer && python server.py

# Przeglądarka: http://localhost:8080
```

### 2. **Test funkcjonalności**
- ✅ Mapa się ładuje
- ✅ Żetony są widoczne
- ✅ Dane się odświeżają
- ✅ Panel gracza aktualizuje się
- ✅ Nie ma błędów w konsoli

---

## 📱 OPCJE ROZSZERZEŃ

### **TRYB REPLAY**
- Zapisywanie historii wszystkich tur
- Możliwość przewijania do tyłu
- Eksport do GIF/MP4

### **TRYB MOBILNY**
- Responsywne CSS
- Touch controls dla mapy
- Kompaktowe panele

### **SHARING**
- Link do udostępniania obserwacji
- Zapis replay do pliku
- Stream na Twitch/YouTube

---

## ⏱️ HARMONOGRAM

| Faza | Czas | Priorytet |
|------|------|-----------|
| Eksporter danych | 1 dzień | KRYTYCZNY |
| Serwer web | 0.5 dnia | KRYTYCZNY |
| Frontend podstawy | 1 dzień | KRYTYCZNY |
| Mapa hexowa | 1 dzień | WYSOKI |
| Panele info | 0.5 dnia | ŚREDNI |
| **SUMA MINIMUM** | **4 dni** | - |
| Rozszerzenia | +2-3 dni | NISKI |

---

## 🚀 QUICK START

### Kiedy masz 30 minut:
1. Stwórz `web_observer/` folder
2. Zainstaluj Flask: `pip install flask`
3. Skopiuj plan do `PLAN_WEB_OBSERVER.md`

### Kiedy masz 2 godziny:
1. Zrób FAZĘ 1 (eksporter)
2. Przetestuj czy eksportuje dane

### Kiedy masz weekend:
1. Zrób FAZY 1-4
2. Będziesz mieć działającą mapę w przeglądarce! 🎉

---

## 💡 NOTATKI TECHNICZNE

- **JSON Format**: Użyj istniejących struktur z `saves/latest.json`
- **WebSocket**: Opcjonalnie zamiast polling, dla natychmiastowych aktualizacji
- **Cache**: Dodaj cache dla statycznych zasobów (mapy, ikony)
- **Security**: Dla demo localhost wystarczy, dla produkcji dodaj HTTPS

---

*Plan stworzony: 2 lipca 2025*  
*Ostatnia aktualizacja: 2 lipca 2025*
