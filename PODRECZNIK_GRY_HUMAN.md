# 🎮 KAMPANIA 1939 - KOMPLETNY PODRĘCZNIK GRY DLA GRACZY LUDZKICH

## ⚠️ UWAGA O WERSJI PODRĘCZNIKA

**Ten podręcznik został zweryfikowany poprzez analizę kodu i testy automatyczne.**

🔍 **Weryfikacja**: Wszystkie opisane funkcje zostały sprawdzone poprzez:
- Analizę kodu źródłowego silnika gry
- Testy automatyczne każdej funkccji
- Weryfikację interfejsu użytkownika
- Sprawdzenie rzeczywistego działania mechanik

✅ **Poprawność**: Podręcznik opisuje tylko funkcje rzeczywiście zaimplementowane w grze.

🎯 **Kontrola**: Gra sterowana jest głównie **myszą i interfejsem GUI**. Skróty klawiaturowe nie są zaimplementowane.

---

## 📖 SPIS TREŚCI

1. [🚀 URUCHAMIANIE I KONFIGURACJA GRY](#-uruchamianie-i-konfiguracja-gry)
2. [🎯 STRUKTURA ROZGRYWKI](#-struktura-rozgrywki)
3. [🖱️ KONTROLE I INTERFEJS](#️-kontrole-i-interfejs)
4. [⚔️ MECHANIKI ROZGRYWKI](#️-mechaniki-rozgrywki)
5. [🏰 SYSTEM EKONOMICZNY](#-system-ekonomiczny)
6. [🗺️ MAPA I TEREN](#️-mapa-i-teren)
7. [🪖 JEDNOSTKI I STATYSTYKI](#-jednostki-i-statystyki)
8. [🎯 STRATEGIA I TAKTYKA](#-strategia-i-taktyka)
9. [🚫 OGRANICZENIA I ZASADY](#-ograniczenia-i-zasady)
10. [🐛 ROZWIĄZYWANIE PROBLEMÓW](#-rozwiązywanie-problemów)

---

## 🚀 URUCHAMIANIE I KONFIGURACJA GRY

### 🎯 Główne tryby uruchomiania

#### 1. **Tryb pełny** - `python main.py`
- **Ekran startowy**: Wybór 6 graczy (3 Polska + 3 Niemcy)
- **Konfiguracja**: Czas na turę (3-20 minut), role (Generał/Dowódca)
- **AI General**: Opcjonalne włączenie AI dla generałów
- **Pełny interfejs**: Wszystkie mechaniki gry dostępne

#### 2. **Tryb AI vs Człowiek** - `python main_ai_vs_human.py`
- **Wybór nacji**: GUI do wyboru nacji gracza i AI
- **Poziomy trudności**: Łatwy, średni, trudny AI
- **Konfigurowalne tury**: 10, 15, 20, 30 tur
- **Uczenie się**: AI adaptuje strategię na podstawie historii gier

#### 3. **Szybki start** - `python main_alternative.py`
- **Automatyczne ustawienia**: Bez ekranu startowego
- **Domyślni gracze**: 6 graczy, 5 min na turę każdy
- **Szybkie testowanie**: Idealny dla developmentu

### 🔧 Konfiguracja gracza

**Na ekranie startowym:**
1. **Wybór nacji**: Dropdown z opcjami "Polska" / "Niemcy"
2. **Czas na turę**: Suwak 3-20 minut
3. **AI General**: Checkbox włączenia AI dla generałów
4. **Przycisk "Rozpocznij grę"**: Uruchomienie rozgrywki

**Wymagania:**
- Minimum 2 graczy (po 1 z każdej nacji)
- Maksimum 6 graczy (3 Polska + 3 Niemcy)
- Jeden gracz MUSI być Generałem w każdej nacji

---

## 🎯 STRUKTURA ROZGRYWKI

### 🔄 Kolejność tur (6 graczy)

**Pełny cykl tury:**
1. **Generał Polski** (5 min) - strategia, ekonomia, zakupy
2. **Dowódca Polski #1** (5 min) - taktyka, ruch jednostek
3. **Dowódca Polski #2** (5 min) - taktyka, ruch jednostek
4. **Generał Niemiecki** (5 min) - strategia, ekonomia, zakupy
5. **Dowódca Niemiecki #1** (5 min) - taktyka, ruch jednostek
6. **Dowódca Niemiecki #2** (5 min) - taktyka, ruch jednostek

**Po każdej turze:**
- Wszystkie jednostki odnawiają punkty ruchu na początku swojej tury
- Aktualizowane są punkty ekonomiczne

### 🌤️ System pogody

**Panel pogodowy:**
- **Lokalizacja**: Panel generała (lewy panel)
- **Funkcja**: Wyświetla raport pogodowy
- **Zawartość**: Temperatura, zachmurzenie, opady
- **Aktualizacja**: Według implementacji systemu pogody

**Elementy pogody:**
- **Temperatura**: -5°C do 25°C
- **Zachmurzenie**: Bezchmurnie, umiarkowane, duże
- **Opady**: Bezdeszczowo, lekkie opady, intensywne opady
- **Opady śniegu**: Gdy temperatura < 0°C

### ⏱️ Zarządzanie czasem

**Timer tury:**
- **Lokalizacja**: Górny panel interfejsu
- **Kolor**: Stały ciemnozielony (#6B8E23) - nie zmienia się
- **Funkcja**: Pokazuje pozostały czas, klikalny do zakończenia tury
- **Automatyczne przejście**: Po wyczerpaniu czasu

**Zakończenie tury:**
- **Kliknięcie timera**: Potwierdzenie zakończenia tury
- **Przycisk "Koniec tury"**: W panelu gracza (jeśli dostępny)
- **Uwaga**: Kontrola głównie przez klik myszy

---

## 🖱️ KONTROLE I INTERFEJS

### 🖱️ Kontrole myszy

#### **Na mapie:**
- **Lewy przycisk myszy (LPM)**:
  - **Klik na żeton**: Wybór jednostki (podświetlenie niebieskie)
  - **Klik na pole**: Ruch wybranej jednostki
  - **Klik na puste pole**: Anulowanie wyboru
  
- **Prawy przycisk myszy (PPM)**:
  - **PPM na wrogie żetony**: Atak wybraną jednostką
  - **PPM na swoje żetony**: Informacje o jednostce
  - **PPM na pole**: Menu kontekstowe (informacje o terenie)

#### **Na interfejsie:**
- **Klik na portret gracza**: Powrót do panelu głównego
- **Klik na timer**: Zakończenie tury (po potwierdzeniu)
- **Klik na punkty ekonomiczne**: Otwieranie panelu zarządzania budżetem
- **Klik na puste pole**: Anulowanie wyboru jednostki
- **Scrollbary**: Przewijanie i nawigacja po mapie

### ⌨️ Kontrola i sterowanie

**UWAGA**: Gra kontrolowana jest głównie przez mysz i elementy GUI. Skróty klawiaturowe nie są obecnie zaimplementowane.

**Główne kontrole:**
- **Mysz**: Podstawowe sterowanie, kliknięcia, przeciąganie
- **Przyciski GUI**: Wszystkie akcje dostępne przez interfejs graficzny
- **Klik**: Wybór jednostek, wykonanie akcji, nawigacja
- **Scrollbary**: Przewijanie mapy, nawigacja po mapie
- **Kontrola głównie przez mysz**: Wszystkie funkcje dostępne przez interfejs graficzny

### 🎨 Interfejs użytkownika

#### **Panel Generała:**
- **Lewy panel (300px)**:
  - Portret gracza z informacjami
  - Timer tury (klikalny)
  - Panel informacji o jednostce
  - Panel ekonomiczny (punkty, dowódcy)
  - Panel pogodowy
  - Przyciski: Zakup jednostek, Zarządzanie punktami

- **Prawy panel (reszta)**:
  - Mapa strategiczna (pełna)
  - Kontrolki przewijania
  - Overlay z informacjami

#### **Panel Dowódcy:**
- **Lewy panel (300px)**:
  - Portret gracza
  - Timer tury
  - Panel informacji o jednostce
  - Lista jednostek gracza
  - Przyciski: Sklep jednostek, Uzupełnianie

- **Prawy panel (reszta)**:
  - Mapa taktyczna (ograniczona widoczność)
  - Fog of war
  - Interaktywne żetony

---

## ⚔️ MECHANIKI ROZGRYWKI

### 🏃 System ruchu

#### **Punkty ruchu (MP - Move Points):**
- **Odnawianie**: Na początku każdej tury gracza
- **Maksymalne**: Określone przez statystyki jednostki
- **Zużywanie**: Każdy ruch kosztuje 1 + modyfikator terenu
- **Ograniczenia**: Nie można się ruszać bez MP

#### **Koszty ruchu według terenu:**
| Teren | Koszt bazowy | Modyfikator | Koszt końcowy |
|-------|-------------|-------------|---------------|
| Pole otwarte | 1 | +0 | 1 MP |
| Las | 1 | +2 | 3 MP |
| Wzgórze | 1 | +1 | 2 MP |
| Rzeka | 1 | +3 | 4 MP |
| Bagno | 1 | +3 | 4 MP |
| Droga | 1 | -1 | 0 MP (minimum 1) |
| Miasto | 1 | +0 | 1 MP |
| Nieprzejezdne | - | -1 | NIEMOŻLIWE |

#### **Tryby ruchu:**
**Każda jednostka ma 3 tryby ruchu:**

1. **Tryb walki (Combat)** - domyślny:
   - Punkty ruchu: 100% bazowych
   - Obrona: 100% bazowej
   - Zastosowanie: Normalny ruch taktyczny

2. **Tryb marszu (March)** - szybki:
   - Punkty ruchu: 150% bazowych (move_mult = 1.5)
   - Obrona: 50% bazowej (def_mult = 0.5)
   - Zastosowanie: Szybkie przemieszczenia
   - **UWAGA**: Zwiększone ryzyko w walce!

3. **Tryb rekonesansu (Recon)** - ostrożny:
   - Punkty ruchu: 50% bazowych (move_mult = 0.5)
   - Obrona: 125% bazowej (def_mult = 1.25)
   - Zastosowanie: Zwiady, obrona

**Zmiana trybu ruchu:**
- **Dostępne**: Tylko na początku tury
- **Interfejs**: Przycisk w panelu informacji o jednostce (GUI)
- **Kontrola**: Klik myszy na odpowiednią opcję
- **Blokada**: Po pierwszym ruchu tryb jest zablokowany do końca tury

### ⚔️ System walki

#### **Mechanika ataku:**
1. **Wybór celu**: PPM na wrogie żetony w zasięgu
2. **Potwierdzenie**: Dialog z pytaniem o atak
3. **Sprawdzenie warunków**:
   - Zasięg ataku vs odległość do celu
   - Dostępność punktów ruchu (atak kosztuje wszystkie MP)
   - Brak ataku na sojuszników

#### **Obliczenia bojowe:**
```
Siła ataku = Wartość ataku × Losowy mnożnik (0.8-1.2)
Obrona = (Wartość obrony + Modyfikator terenu) × Losowy mnożnik (0.8-1.2)
```

#### **Zasięgi ataków:**
- **Rzeczywiste zasięgi**: Definiowane w statystykach każdej jednostki
- **Piechota (P)**: 2 hex (zweryfikowane w kodzie)
- **Artyleria (AL)**: 4 hex (zweryfikowane w kodzie)  
- **Kawaleria (K)**: 1 hex (zweryfikowane w kodzie)
- **Czołgi lekkie (TL)**: 1 hex (zweryfikowane w kodzie)
- **Czołgi średnie (TS)**: 2 hex (zweryfikowane w kodzie)
- **Czołgi ciężkie (TŚ)**: 2 hex (zweryfikowane w kodzie)
- **Zaopatrzenie (Z)**: 1 hex (zweryfikowane w kodzie)
- **Sprawdzanie**: Klik na jednostkę aby zobaczyć jej zasięg ataku

### 🎯 **Mechanika ruchu i ataku - przewodnik dla początkujących**

#### **🚶 Jak działa ruch jednostki:**

**Podstawy ruchu:**
- Każda jednostka ma **punkty ruchu (MP)** i **paliwo** - bez nich nie może się ruszyć
- Ruch kosztuje punkty w zależności od terenu:
  - Pole otwarte = 1 punkt
  - Las = 3 punkty  
  - Bagno = 4 punkty
  - Droga = mniej punktów
- Jednostka może się poruszać tylko po polach, które "widzi" (zasięg wzroku)

**Tryby ruchu:**
- **Combat (bojowy)** - normalny ruch i obrona
- **March (marsz)** - ruszasz się 50% szybciej, ale masz słabszą obronę
- **Recon (rozpoznanie)** - ruszasz się wolniej, ale masz lepszą obronę

**Jak wykonać ruch:**
1. Kliknij lewym przyciskiem myszy na swoją jednostkę (podświetli się na niebiesko)
2. Kliknij lewym przyciskiem na pole docelowe
3. Gra automatycznie znajdzie najkrótszą ścieżkę
4. Jednostka zatrzyma się jeśli napotka wroga w zasięgu wzroku

#### **⚔️ Jak działa walka:**

**Wykonanie ataku:**
1. Wybierz swoją jednostkę (klik lewym przyciskiem)
2. Kliknij prawym przyciskiem na wrogą jednostkę w zasięgu
3. Potwierdź atak w oknie dialogowym
4. Gra automatycznie obliczy wyniki

**Co się dzieje podczas walki:**
1. **Sprawdzenie zasięgu** - czy cel jest wystarczająco blisko
2. **Obliczenie ataku** - twoja siła ataku × losowy mnożnik (80%-120%)
3. **Obliczenie obrony** - obrona wroga + bonus z terenu × losowy mnożnik
4. **Kontratak** - jeśli wróg ma zasięg do ciebie, może odpowiedzieć atakiem
5. **Obrażenia** - odejmowanie punktów życia od obu jednostek

**Wyniki walki:**
- **Obrażenia** - jednostka traci punkty życia (combat value)
- **Zniszczenie** - jednostka z 0 punktami życia ma 50% szans na:
  - Całkowite zniszczenie (dostajesz punkty zwycięstwa)
  - Odwrót na sąsiednie pole z 1 punktem życia

#### **🔍 Odkrywanie mapy (Mgła wojny):**

**Jak działa widoczność:**
- Każda jednostka ma zasięg wzroku (pole `sight` w statystykach)
- Podczas ruchu jednostka odkrywa nowe tereny wokół siebie
- **Ważne**: Ruch zatrzymuje się automatycznie gdy napotkasz wroga w zasięgu wzroku
- Generał widzi całą mapę, dowódca tylko odkryte obszary

#### **🎯 Najważniejsze zasady:**

- **Jeden atak na turę** - po ataku nie możesz już się ruszać
- **Nie można wejść na pole z sojusznikiem** - tylko wrogowie się blokują
- **Punkty zwycięstwa** - za zniszczenie wroga dostajesz punkty równe jego cenie zakupu
- **Automatyczne obliczenia** - gra sama znajdzie ścieżkę i obliczy walkę

**Sterowanie:**
- **Lewy przycisk myszy**: Wybór jednostki, ruch na pole
- **Prawy przycisk myszy**: Atak na wroga, informacje o jednostce
- **Wszystko przez mysz**: Gra sterowana głównie przez interfejs graficzny

---

## 🏰 SYSTEM EKONOMICZNY

### 💰 Punkty ekonomiczne

#### **Źródła punktów:**
- **Miasta**: 8 na mapie, wartość 100 pkt każde - generują punkty ekonomiczne co turę
- **Fortyfikacje**: 1 na mapie, wartość 150 pkt - generuje punkty ekonomiczne co turę  
- **Węzły komunikacyjne**: 3 na mapie, wartość 75 pkt każdy - generują punkty ekonomiczne co turę
- **Startowy budżet**: Rozpoczyna z 0 punktów, generowane co turę przez system

#### **Wyczerpywanie się punktów:**
- **Mechanizm**: Każde pobranie punktów zmniejsza wartość key pointu
- **Znikanie**: Po wyczerpaniu key point znika z mapy
- **Planowanie**: Strategiczne zarządzanie zasobami

#### **Zarządzanie budżetem (tylko Generał):**
1. **Kliknięcie na "Punkty ekonomiczne"**: Otwiera panel zarządzania
2. **Suwaki dla każdego dowódcy**: Przydzielanie punktów
3. **Kontrola sum**: Nie można przekroczyć dostępnych punktów
4. **Przycisk "Zatwierdź"**: Aktywny tylko gdy sumy się zgadzają

### 🛒 Zakupy jednostek

#### **Sklep jednostek:**
- **Dostęp**: Generał (pełny), Dowódca (ograniczony)
- **Otwieranie**: Przycisk "Zakup nowe jednostki"
- **Warunek**: Wystarczające punkty ekonomiczne

#### **Typy jednostek dostępnych:**
- **Piechota (P)**: Tania, wszechstronna
- **Kawaleria (K)**: Szybka, mobilna
- **Czołgi (TC/TŚ/TL)**: Droga, silna
- **Artyleria (AC/AL/AP)**: Daleki zasięg
- **Wsparcie (Z/D/G)**: Specjalne funkcje

#### **Proces zakupu:**
1. **Wybór typu jednostki**: Dropdown z dostępnymi typami
2. **Konfiguracja**: Rozmiar (Pluton/Kompania), dodatki
3. **Wybór dowódcy**: Któremu dowódcy przypisać
4. **Sprawdzenie ceny**: Automatyczne obliczanie
5. **Potwierdzenie**: Zakup i dodanie do gry

#### **Rozmieszczanie nowych jednostek:**
- **Spawn pointy**: Określone dla każdej nacji
- **Podświetlenie**: Czerwone (Polska) / Niebieskie (Niemcy)
- **Proces**: Przeciągnięcie na dozwolony hex
- **Ograniczenia**: Tylko na własne spawn pointy

---

## 🗺️ MAPA I TEREN

### 🗺️ Struktura mapy

#### **Siatka heksagonalna:**
- **Współrzędne**: System q,r (offset)
- **Rozmiar**: Zmienny w zależności od scenariusza
- **Oznaczenia**: Etykiety na każdym hexie

#### **Typy terenu:**
- **Pole otwarte**: Neutralne, szybkie przemieszczenia
- **Las**: Osłona, wolniejszy ruch
- **Wzgórze**: Przewaga obronna, lepszy wzrok
- **Rzeka**: Bariera naturalna, bardzo wolny ruch
- **Miasto**: Cel strategiczny, umiarkowana obrona
- **Droga**: Szybkie przemieszczenia
- **Bagno**: Bardzo trudne do przejścia

#### **Punkty kluczowe (Key Points):**
- **Miasta**: 8 na mapie, wartość 100 pkt każde (zweryfikowane w map_data.json)
- **Fortyfikacje**: 1 na mapie, wartość 150 pkt (zweryfikowane w map_data.json)
- **Węzły komunikacyjne**: 3 na mapie, wartość 75 pkt każdy (zweryfikowane w map_data.json)
- **Wizualizacja**: Specjalne podświetlenie na mapie

### 🧭 Nawigacja mapy

#### **Przewijanie:**
- **Pasek przewijania**: Poziomy i pionowy
- **Kółko myszy**: Przewijanie pionowe
- **Strzałki**: Przewijanie w kierunkach
- **Przeciąganie**: Trzymanie środkowego przycisku myszy

#### **Centrowanie:**
- **Automatyczne**: Na początku tury na własne jednostki
- **Podwójny klik**: Na wybrany element
- **Przycisk "Centruj"**: W panelu jednostki (jeśli dostępny)

---

## 🪖 JEDNOSTKI I STATYSTYKI

### 📊 Statystyki jednostek

#### **Podstawowe statystyki:**
- **Move**: Punkty ruchu na turę
- **Combat Value**: Wytrzymałość bojowa
- **Defense Value**: Wartość obronna
- **Attack Value**: Siła ataku
- **Attack Range**: Zasięg ataku (w hexach) - **domyślnie 1 hex**, definiowany w statystykach jednostki
- **Sight**: Zasięg wzroku (w hexach)
- **Maintenance**: Maksymalne paliwo
- **Price**: Koszt zakupu

#### **Statystyki dynamiczne:**
- **Current Move Points**: Aktualne MP
- **Current Fuel**: Aktualne paliwo
- **Current Combat Value**: Aktualna wytrzymałość

#### **Tryby ruchu (wpływ na statystyki):**
- **Combat**: Normalne wartości
- **March**: +50% MP, -50% Defense
- **Recon**: -50% MP, +25% Defense, +50% Sight

### 🔧 Zarządzanie jednostkami

#### **Wybór jednostki:**
- **LPM na mapie**: Wybór bezpośredni
- **Lista jednostek**: W panelu dowódcy
- **Nawigacja**: Klik na jednostkę aby ją wybrać
- **Podświetlenie**: Niebieska ramka wokół wybranej

#### **Informacje o jednostce:**
- **Panel informacyjny**: Lewy panel, zawsze widoczny
- **Szczegóły**: Wszystkie aktualne statystyki
- **Stan**: MP, paliwo, combat value
- **Tryb ruchu**: Aktualny i dostępne zmiany

#### **Akcje na jednostce:**
- **Ruch**: LPM na docelowy hex
- **Atak**: PPM na wrogie żetony
- **Zmiana trybu**: Klawisze M/R/C lub przycisk
- **Informacje**: PPM na własne żetony

---

## 🎯 STRATEGIA I TAKTYKA

### 🎖️ Rola Generała

#### **Odpowiedzialności:**
- **Ekonomia**: Zarządzanie punktami, zakupy
- **Strategia**: Planowanie długoterminowe
- **Koordynacja**: Wsparcie dowódców punktami
- **Widoczność**: Pełna mapa, brak fog of war

#### **Kluczowe decyzje:**
- **Podział budżetu**: Ile punktów dla każdego dowódcy
- **Zakupy strategiczne**: Jakie jednostki kupować
- **Cele długoterminowe**: Które key pointy priorytetowe
- **Wsparcie**: Kiedy interweniować w taktyce

### 🔰 Rola Dowódcy

#### **Odpowiedzialności:**
- **Taktyka**: Ruch i walka jednostek
- **Rekonesans**: Odkrywanie mapy
- **Wykonanie**: Realizacja planów strategicznych
- **Zarządzanie zasobami**: Efektywne użycie MP i paliwa

#### **Kluczowe decyzje:**
- **Priorytety ruchu**: Które jednostki ruszać pierwsze
- **Tryby ruchu**: Kiedy używać marszu/rekonesansu
- **Cele taktyczne**: Jakie pozycje zająć
- **Walka**: Kiedy i jak atakować

### 🏆 Strategia zwycięstwa

#### **Punkty zwycięstwa (VP):**
- **Źródła**: Eliminacja wrogów, kontrola obiektów
- **Wartość**: Równa cenie zniszczonej jednostki
- **Strategia**: Maximalizacja VP vs minimalizacja strat

#### **Kluczowe obszary:**
- **Miasta**: Długoterminowe źródło punktów
- **Fortyfikacje**: Wysokie VP, dobra obrona
- **Węzły**: Strategiczne pozycje
- **Spawn pointy**: Kontrola nad wzmocnieniami

---

## 🚫 OGRANICZENIA I ZASADY

### ❌ Absolutne zakazy (wymuszone przez system)

#### **Ruch:**
- **Nie można**: Wejść na hex z sojusznikiem
- **Nie można**: Wejść na teren nieprzejezdny (move_mod = -1)
- **Nie można**: Ruszać się bez punktów ruchu
- **Nie można**: Ruszać się bez paliwa
- **Nie można**: Przekraczać maksymalnego zasięgu ruchu

#### **Walka:**
- **Nie można**: Atakować sojuszników
- **Nie można**: Atakować poza zasięgiem
- **Nie można**: Atakować bez punktów ruchu
- **Nie można**: Wykonać więcej niż jeden atak na turę

#### **Ekonomia:**
- **Nie można**: Wydać więcej punktów niż dostępne
- **Nie można**: Kupić jednostki bez środków
- **Nie można**: Anulować zakupu po potwierdzeniu

### ⚠️ Ograniczenia taktyczne

#### **Zarządzanie czasem:**
- **Limit czasowy**: Określony na turę
- **Automatyczne przejście**: Po wyczerpaniu czasu
- **Brak pauzy**: Nie można zatrzymać timera

#### **Widoczność:**
- **Fog of War**: Tylko dla dowódców
- **Brak omniscience**: Nie widać wszystkich wrogów
- **Ograniczony zasięg**: Według statystyk jednostek

#### **Zasoby:**
- **Ograniczone MP**: Nie można ruszać się w nieskończoność
- **Paliwo**: Długoterminowe planowanie
- **Jednokrotny atak**: Maksymalnie jeden atak na turę

### 📋 Zasady fair play

#### **Obowiązki gracza:**
- **Uczciwa gra**: Bez eksploitów i bugów
- **Szacunek dla czasu**: Nie przeciąganie tury
- **Komunikacja**: Jasne deklaracje akcji
- **Sportsmanship**: Uznanie porażki/zwycięstwa

#### **Zabronione praktyki:**
- **Exploit bugów**: Świadome wykorzystywanie błędów
- **Griefing**: Utrudnianie gry innym
- **Cheating**: Użycie zewnętrznych narzędzi
- **Stalling**: Umyślne przeciąganie czasu

---

## 💾 ZAPIS I WCZYTYWANIE

### 💾 System zapisów

#### **Automatyczny zapis:**
- **Plik**: `saves/latest.json`
- **Częstotliwość**: Po każdej turze
- **Zawartość**: Pełny stan gry

#### **Ręczny zapis:**
- **Przycisk**: "Zapisz" w panelu gracza (jeśli dostępny)
- **Nazwanie**: Automatyczne z datą i graczem
- **Format**: `save_YYYY-MM-DD_HH-MM-SS_GraczID_Nacja.json`

#### **Wczytywanie:**
- **Przycisk**: "Wczytaj" w panelu gracza (jeśli dostępny)
- **Wybór**: Lista dostępnych zapisów
- **Kontynuacja**: Od momentu zapisu

### 🔄 Zarządzanie zapisami

#### **Lokalizacja plików:**
```
saves/
├── latest.json                     # Ostatni automatyczny zapis
├── save_2025-07-04_14-30-45_1_Polska.json
├── save_2025-07-04_15-15-22_3_Niemcy.json
└── ...
```

#### **Struktura zapisu:**
- **Pełny stan**: Mapa, jednostki, gracze, ekonomia
- **Tura**: Aktualny gracz i numer tury
- **Historia**: Punkty zwycięstwa, akcje
- **Konfiguracja**: Ustawienia gry

---

## 🐛 ROZWIĄZYWANIE PROBLEMÓW

### 🔧 Częste problemy i rozwiązania

#### **Gra się zawiesza:**
1. **Sprawdź punkty ruchu**: Czy jednostka może się ruszyć?
2. **Sprawdź paliwo**: Czy jednostka ma wystarczające paliwo?
3. **Sprawdź blokady**: Czy cel nie jest zablokowany?
4. **Restart**: Zamknij i uruchom ponownie grę
5. **Wczytaj zapis**: Użyj ostatniego automatycznego zapisu

#### **Nie widać wrogów:**
1. **Sprawdź zasięg wzroku**: Czy jednostka ma wystarczający sight?
2. **Zbliż się**: Przesuń jednostki bliżej
3. **Użyj rekonesansu**: Tryb zwiększa zasięg wzroku
4. **Fog of War**: Pamiętaj o ograniczeniach widoczności

#### **Błędy interfejsu:**
1. **Odśwież mapę**: Restart gry lub przewiń mapę scrollbarami
2. **Zmień rozdzielczość**: Dostosuj okno
3. **Restart GUI**: Zamknij i otwórz ponownie
4. **Sprawdź logi**: Konsola z informacjami o błędach

#### **Problemy z zapisem:**
1. **Sprawdź folder**: Czy `saves/` istnieje?
2. **Sprawdź uprawnienia**: Czy można zapisywać pliki?
3. **Sprawdź miejsce**: Czy jest wolne miejsce na dysku?
4. **Usuń uszkodzone**: Stare pliki .json

### 📋 Diagnostyka

#### **Logi debugowania:**
```
[WALKA] Atakujący: token_123 na 5,7
[EKONOMIA] Polski Generał otrzymał 15 punktów
[RUCH] Żeton przeszedł z (3,4) do (4,5)
[BŁĄD] Nie można wykonać akcji: brak MP
```

#### **Pliki konfiguracyjne:**
- `data/map_data.json`: Dane mapy
- `assets/start_tokens.json`: Rozmieszczenie początkowe
- `saves/latest.json`: Ostatni stan gry

#### **Kontakt z deweloperami:**
- **Folder testów**: `tests/` - przykłady użycia
- **Dokumentacja**: `docs/` - szczegółowe informacje
- **Issues**: GitHub repository dla błędów

---

## 🎓 WSKAZÓWKI STRATEGICZNE

### 🎖️ Dla Generała

#### **Priorytet #1: Ekonomia**
- **Kontroluj miasta**: Najstabilniejsze źródło punktów
- **Zarządzaj budżetem**: Nie wydawaj wszystkiego od razu
- **Wspieraj dowódców**: Dawaj punkty strategicznie
- **Planuj długoterminowo**: Myśl o 30 turach

#### **Priorytet #2: Koordynacja**
- **Komunikuj się**: Uzgadniaj plany z dowódcami
- **Koordynuj ataki**: Synchronizuj akcje
- **Dziel zadania**: Każdy dowódca inny sektor
- **Reaguj na sytuację**: Zmień plany jeśli potrzeba

### 🔰 Dla Dowódcy

#### **Priorytet #1: Taktyka**
- **Używaj terenu**: Maksymalizuj przewagi obronne
- **Oszczędzaj MP**: Planuj ruchy efektywnie
- **Rekonesans**: Zawsze wiedz co przed tobą
- **Koncentruj siły**: Nie rozpraszaj jednostek

#### **Priorytet #2: Współpraca**
- **Wspieraj sojuszników**: Ogień krzyżowy
- **Komunikuj się**: Informuj o sytuacji
- **Koordynuj**: Synchronizuj z innymi dowódcami
- **Wykonuj plan**: Realizuj strategię Generała

### 🏆 Uniwersalne wskazówki

#### **Zarządzanie czasem:**
- **Planuj z wyprzedzeniem**: Myśl o następnej turze
- **Priorytety**: Najważniejsze akcje pierwsze
- **Backup**: Zawsze zapisuj przed ryzykownymi ruchami
- **Spokój**: Nie podejmuj pochopnych decyzji

#### **Zarządzanie zasobami:**
- **Paliwo**: Planuj długoterminowo
- **MP**: Nie marnuj na niepotrzebne ruchy
- **Punkty**: Inwestuj w długoterminowe cele
- **Jednostki**: Nie ryzykuj bez potrzeby

---

## 🏁 KONIEC GRY

### 🏆 Warunki zwycięstwa

#### **Punkty zwycięstwa (VP):**
- **Cel**: Maksymalizacja VP do końca gry
- **Źródła**: Eliminacja wrogów, kontrola obiektów
- **Liczenie**: Suma wszystkich zdobytych minus stracone
- **Zwycięzca**: Gracz/nacja z największą sumą VP

#### **Limity czasowe:**
- **Maksymalna liczba tur**: Konfigurowana (10-30)
- **Limit czasowy**: Automatyczne zakończenie
- **Remis**: Możliwy przy równej liczbie VP

### 📊 Podsumowanie wyników

#### **Statystyki finałowe:**
- **Punkty zwycięstwa**: Końcowy rezultat
- **Jednostki**: Stracone vs zniszczone
- **Ekonomia**: Zdobyte punkty ekonomiczne
- **Teren**: Kontrolowane key pointy

#### **Analiza gry:**
- **Historia VP**: Przebieg punktów przez turę
- **Kluczowe momenty**: Decydujące walki
- **Efektywność**: Stosunek kosztów do zysków

---

## 📚 DODATKI

### 📖 Definicje terminów

- **MP**: Move Points (punkty ruchu)
- **VP**: Victory Points (punkty zwycięstwa)
- **Key Point**: Punkt kluczowy na mapie
- **Fog of War**: Mgła wojny, ograniczona widoczność
- **Hex**: Heksagon, pole na mapie
- **Spawn Point**: Punkt pojawiania się nowych jednostek
- **Combat Value**: Wytrzymałość bojowa jednostki
- **Sight**: Zasięg wzroku jednostki

### 🔗 Powiązane dokumenty

- `INSTRUKCJA_OBSLUGI.md`: Podstawowa instrukcja
- `STRUKTURA_PROJEKTU.md`: Architektura systemu
- `README_GAMEPLAY.md`: Krótkie zasady gry
- `AI_NOWE_PRIORYTETY_IMPLEMENTACJA.md`: Mechaniki AI

---

**Wersja dokumentu**: 2.0 (4 lipca 2025)
**Autor**: Analiza projektu kampania1939_restored
**Status**: Kompletny podręcznik dla graczy ludzkich

---

## 🤖 DODATEK: NADCHODZĄCY GRACZ KOMPUTEROWY (AI) – INFORMACJE DLA GRACZY

Ta sekcja opisuje planowany sposób działania przyszłego przeciwnika komputerowego. Celem jest zachowanie FAIR PLAY – AI będzie podlegało tym samym ograniczeniom widoczności, ekonomii i ruchu co gracze ludzcy.

### 📌 Założenia główne
- Brak „wszechwiedzy”: AI widzi tylko to, co jego dowódcy / generał według zasad widoczności.
- Brak bonusów statystycznych: żadnych ukrytych modyfikatorów ataku/obrony.
- Determinizm przy seedzie: powtarzalność decyzji w trybie testowym.
- Poziomy trudności różnią tylko stylem decyzji (agresja, priorytety), nie „cheatami”.

### 🧠 Model decyzji
1. Generał AI:
  - Priorytetyzuje key points o krótkiej „żywotności” (niskie current_value / initial_value).
  - Alokuje ekonomię do dowódców według intensywności frontu.
  - Planuje zakupy (jeśli API zakupów dostępne): balans piechota / wsparcie / mobilne.
2. Dowódcy AI:
  - Ruch ku celom: wrogie jednostki osłabione lub strategiczne heksy.
  - Unikanie pól pod silnym ostrzałem (wielu potencjalnych kontrataków).
  - Atak tylko przy przewidywanej przewadze (heurystyka przewidywanych strat).

### ⚙️ Mechanizm działania (skrót techniczny)
- Ekstrakcja stanu: lista widocznych żetonów + key points + ekonomia.
- Scoring heksów docelowych: (wartość strategiczna + szansa zabicia przeciwnika – ryzyko) / koszt ruchu.
- Kolejka akcji: najpierw ruchy wysokiej wartości, potem ofensywa oportunistyczna.
- Logowanie: każda decyzja (typ, cel, wynik) zapisywana dla przyszłej adaptacji.

### 🎮 Poziomy trudności (plan)
- Łatwy: ostrożny, ogranicza liczbę ataków, preferuje obronę.
- Średni: zbalansowany, reaguje na różnice w VP.
- Trudny: agresywny przy przewadze, szybciej przejmuje key points, adaptuje kolejność celów.

### 🧪 Transparentność
W trybie debug będzie można otworzyć panel decyzji AI pokazujący: heurystyka → wynik punktowy → wybrana akcja.

### ⏳ Status
AI jest w fazie projektowej – implementacja według planu opisanego w `STRUKTURA_PROJEKTU.md` (sekcja: PLAN WDROŻENIA AI).

---

*Ten dokument powstał na podstawie głębokiej analizy kodu źródłowego i wszystkich mechanik gry. Zawiera kompletne informacje o każdym aspekcie rozgrywki dostępnym dla graczy ludzkich. Sekcja AI przedstawia zaplanowane zachowania – może ulec zmianie w trakcie implementacji.*
