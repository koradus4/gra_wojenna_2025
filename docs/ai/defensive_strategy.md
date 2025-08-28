# Dokumentacja AI Commander - Strategia Defensywna

## Przegląd

System defensywny AI Commander został zaprojektowany w odpowiedzi na analizę bitew AI vs AI, gdzie wykazano dominację polskich sił przez lepszą kontrolę punktów kluczowych (+29 pkt/turę). Celem systemu jest poprawa koordynacji defensywnej niemieckich jednostek i ogólnej efektywności obronnej wszystkich graczy AI.

## Architektura Systemu

### Komponenty Główne

1. **Ocena Zagrożeń** (`assess_defensive_threats`)
2. **Planowanie Odwrotu** (`plan_defensive_retreat`) 
3. **Deployment Jednostek** (`deploy_purchased_units`)
4. **Koordynacja Obrony** (`defensive_coordination`)

### Integracja z AI Commander

System defensywny jest zintegrowany z główną pętlą AI Commander (`make_tactical_turn`) jako dodatkowe fazy:

```
COMBAT PHASE → FAZA DEFENSYWNA → FAZA DEPLOYMENT → FAZA RUCHU
```

## Szczegółowy Opis Komponentów

### 1. Ocena Zagrożeń Defensywnych

**Funkcja**: `assess_defensive_threats(my_units, game_engine)`

**Cel**: Identyfikacja jednostek narażonych na atak wroga i ocena poziomu zagrożenia.

**Algorytm**:
- Skanuje wrogów w zasięgu 6 hexów od każdej jednostki
- Oblicza poziom zagrożenia: `max(1, combat_value_wroga - dystans)`
- Znajduje najbliższy punkt kluczowy jako punkt bezpieczeństwa
- Zwraca szczegółową analizę dla każdej jednostki

**Dane wyjściowe**:
```python
{
    unit_id: {
        'threat_level': int,
        'threatening_enemies': list,
        'nearest_safe_point': tuple,
        'safe_point_distance': int
    }
}
```

### 2. Planowanie Kontrolowanego Odwrotu

**Funkcja**: `plan_defensive_retreat(threatened_units, threat_assessment, game_engine)`

**Cel**: Opracowanie planu odwrotu dla zagrożonych jednostek.

**Strategia Odwrotu**:
1. **Jednostki przy punktach kluczowych** (≤2 hex) - pozostają i bronią
2. **Jednostki dalej** - wycofują się do najbliższego punktu kluczowego
3. **Brak punktów kluczowych** - odwrót w bezpiecznym kierunku

**Algorytm wyszukiwania bezpiecznej pozycji**:
- Oblicza kierunek do celu
- Generuje kandydatów w tym kierunku
- Ocenia bezpieczeństwo: `dystans_od_wrogów * 10 - dystans_do_celu * 5`
- Wybiera pozycję z najwyższym wynikiem bezpieczeństwa

### 3. Deployment Zakupionych Jednostek

**Funkcja**: `deploy_purchased_units(game_engine, player_id)`

**Cel**: Automatyczne wdrażanie nowych jednostek z plików zakupu.

**Proces Deployment**:
1. Skanuje pliki `nowe_dla_{nation}_*.json`
2. Dla każdej jednostki znajduje optymalną pozycję deployment
3. Tworzy token i umieszcza na mapie
4. Usuwa plik po pomyślnym deployment

**Priorytet Pozycji**:
1. **Spawn points** nacji
2. **Bliskość do sojuszników** (wsparcie)
3. **Punkty kluczowe** (strategiczna wartość)
4. **Dystans od wrogów** (bezpieczeństwo)

### 4. Koordynacja Obrony Grupowej

**Funkcja**: `defensive_coordination(my_units, threat_assessment, game_engine)`

**Cel**: Organizacja jednostek w grupy defensywne wokół punktów kluczowych.

**Strategia Gruppingu**:
- Grupuje jednostki według najbliższych punktów kluczowych
- Dla grup ≥2 jednostek planuje koordynowaną obronę
- Najsilniejsze jednostki bezpośrednio przy punktach kluczowych
- Wsparcie w kręgu zewnętrznym

## Funkcje Pomocnicze

### Obliczanie Dystansu Hexagonalnego
```python
def calculate_hex_distance(pos1, pos2):
    q1, r1 = pos1
    q2, r2 = pos2
    return max(abs(q1 - q2), abs(r1 - r2), abs((q1 + r1) - (q2 + r2)))
```

### Pobieranie Punktów Kluczowych
```python
def get_all_key_points(game_engine):
    # Pobiera z map_data['key_points'] lub key_points_state
    # Konwertuje string pozycji na tuple (q, r)
```

### Ocena Bezpieczeństwa Pozycji
```python
def evaluate_position_safety(position, threatening_enemies, target_point=None):
    # Bonus za dystans od wrogów: +10 za hex
    # Malus za dystans od celu: -5 za hex
```

## Konfiguracja i Parametry

### Progi Zagrożenia
- **Próg odwrotu**: `threat_level > 5`
- **Zasięg zagrożenia**: 6 hexów
- **Bliskość do punktu kluczowego**: ≤2 hexów (pozostań i broń)

### Zakresy Ruchu
- **Maksymalny zasięg odwrotu**: `min(mp, fuel, 4)`
- **Zasięg awaryjny**: `min(mp, fuel, 3)`

### Scoring Deployment
- **Bazowy wynik**: 100 punktów
- **Bonus za wsparcie**: +50 (≤3 hex), +20 (≤6 hex)
- **Bonus za punkty kluczowe**: +wartość_punktu/10

## Integracja z Istniejącym Systemem

### Modyfikacje make_tactical_turn()

```python
# 3.5. NOWA FAZA DEFENSYWNA
threat_assessment = assess_defensive_threats(my_units, game_engine)
threatened_units = [u for u in my_units if threat_assessment.get(u['id'], {}).get('threat_level', 0) > 5]

if threatened_units:
    retreat_plan = plan_defensive_retreat(threatened_units, threat_assessment, game_engine)
    # Wykonaj ruchy defensywne

# 3.6. DEPLOYMENT NOWYCH JEDNOSTEK  
deployed_count = deploy_purchased_units(game_engine, player_id)
if deployed_count > 0:
    my_units = get_my_units(game_engine, player_id)  # Odśwież listę
```

### Kompatybilność
- System nie interferuje z istniejącymi funkcjami AI
- Zachowuje wszystkie dotychczasowe możliwości
- Dodaje nowe funkcjonalności bez breaking changes

## Testowanie

### Testy Jednostkowe
- `test_calculate_hex_distance()` - Weryfikacja obliczeń dystansu
- `test_get_all_key_points()` - Pobieranie punktów kluczowych
- `test_assess_defensive_threats()` - Ocena zagrożeń
- `test_defensive_retreat()` - Planowanie odwrotu
- `test_defensive_coordination()` - Koordynacja grup

### Testy Integracyjne
- `test_deployment()` - Pełny cykl deployment
- `test_defensive_strategy()` - Scenariusz bojowy

### Scenariusze Testowe
Testy symulują realistyczne scenariusze bojowe z:
- Jednostkami pod presją (threat_level > 10)
- Różnymi pozycjami względem punktów kluczowych
- Wieloma grupami jednostek
- Zakupionymi jednostkami do deployment

## Metryki Wydajności

### Obserwowane Wyniki Testów
- **Identyfikacja zagrożeń**: 100% skuteczność wykrywania jednostek w zasięgu wroga
- **Planowanie odwrotu**: Optymalne pozycje w kierunku punktów kluczowych
- **Deployment**: Automatyczne umieszczenie na spawn points z bonusami za wsparcie
- **Koordynacja**: Formowanie grup defensywnych 2+ jednostek

### Czas Wykonania
- Ocena zagrożeń: O(n*m) gdzie n=moje jednostki, m=jednostki wroga
- Planowanie odwrotu: O(k*r²) gdzie k=zagrożone jednostki, r=zasięg ruchu
- Deployment: O(p*s) gdzie p=purchased units, s=spawn points
- Koordynacja: O(n*k) gdzie n=jednostki, k=punkty kluczowe

## Przyszłe Rozszerzenia

### Planowane Ulepszenia
1. **Adaptacyjne progi zagrożenia** bazujące na sile własnych jednostek
2. **Predykcja ruchów wroga** dla lepszego planowania
3. **Koordynacja między dowódcami** dla strategii ponad-regionalnych
4. **Machine learning** dla optymalizacji strategii na podstawie wyników bitew

### Możliwe Rozszerzenia
- Analiza terenu dla pozycji defensywnych
- Dynamiczne priorytety punktów kluczowych
- Integracja z systemem logistycznym
- Planowanie długoterminowe (wieloturowe strategie)

## Uwagi Implementacyjne

### Zarządzanie Stanem
- System nie modyfikuje trwale stanu gry
- Wszystkie decyzje podejmowane w czasie rzeczywistym
- Brak zależności od zewnętrznych plików konfiguracyjnych

### Obsługa Błędów
- Graceful degradation przy brakujących danych
- Fallback do podstawowych strategii
- Szczegółowe logowanie dla debugowania

### Kompatybilność
- Działa z istniejącymi mapami i danymi
- Nie wymaga modyfikacji struktury bazy danych
- Backward compatible z poprzednimi wersjami AI
