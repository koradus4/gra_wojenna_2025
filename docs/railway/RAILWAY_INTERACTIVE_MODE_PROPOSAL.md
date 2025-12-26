# PROPOZYCJA: Interaktywny tryb torów kolejowych

## 📋 ANALIZA OBECNYCH SYSTEMÓW

### 🌊 RZEKI - workflow
1. **Włącz tryb rzeki** → przycisk "Włącz tryb rzeki"
2. **Klikaj kolejne heksy** (LPM) → buduje ścieżkę
3. **Walidacja:** tylko sąsiednie heksy, komunikaty błędów
4. **Cofnij:** PPM lub przycisk "Cofnij ostatni"
5. **Generuj:** przycisk "Generuj rzekę" (min 2 heksy)
6. **Dopływy:** przycisk "Dodaj dopływ" → klik na heks rzeki → wybierz sąsiada → generuj

**UI Controls:**
- ✅ Przycisk toggle trybu (zmienia kolor gdy aktywny)
- ✅ Status: "Ścieżka rzeki: X heksów"
- ✅ Przyciski: Generuj | Cofnij | Wyczyść | Dodaj dopływ
- ✅ Podgląd na żywo (overlay)
- ✅ Komunikaty popup

### 🛣️ DROGI - workflow
1. **Włącz tryb drogi** → przycisk "Włącz tryb drogi"
2. **Klikaj kolejne heksy** (LPM) → buduje ścieżkę
3. **Walidacja:** tylko sąsiednie heksy
4. **Cofnij:** PPM lub przycisk
5. **Generuj:** przycisk "Generuj drogę" (min 2 heksy)
6. **Skrzyżowania:** klik na heks drogi → przycisk "Dodaj skrzyżowanie" → wybierz sąsiadów → generuj

**UI Controls:**
- ✅ Przycisk toggle trybu
- ✅ Status: "Ścieżka drogi: X heksów"
- ✅ Przyciski: Generuj | Cofnij | Wyczyść | Dodaj skrzyżowanie
- ✅ Typ drogi (combo)
- ✅ Szerokość drogi (combo)

---

## 🚂 PROPOZYCJA DLA TORÓW KOLEJOWYCH

### Workflow

#### FAZA 1: Budowanie ścieżki głównej
1. **Kliknij:** "Włącz tryb torów" 
   - Przycisk zmienia się → "Wyłącz tryb torów" (kolor: #6a6a6a)
   - Popup: "Tryb torów aktywny. Kliknij LPM aby zbudować trasę. Min 2 heksy."

2. **Klikaj kolejne heksy** (LPM)
   - ✅ Dodaje do `railway_path[]`
   - ✅ Walidacja: musi być **sąsiad** poprzedniego heksa
   - ❌ Błąd jeśli nie sąsiaduje → messagebox
   - ✅ Podświetlenie trasy na mapie (niebieski overlay jak rzeka)
   - ✅ Status: "Trasa torów: X heksów"

3. **Cofnij ostatni** (PPM lub przycisk)
   - Usuwa ostatni heks z `railway_path[]`

4. **Wybierz typ toru:** Jednotorowy / Dwutorowy (radio buttons)

5. **Kliknij:** "🚂 Generuj tory" (aktywny gdy ≥2 heksy)
   - Automatycznie:
     - Entry side = kierunek z heksa[0] do heksa[1]
     - Exit side = kierunek z heksa[-2] do heksa[-1]
   - Generuje tory dla każdego heksa w ścieżce
   - Zapisuje metadane (połączenia między heksami)

#### FAZA 2: Dodawanie rozjazdów (opcjonalne)
6. **Kliknij na heks** który już ma tory (zaznacz go)

7. **Kliknij:** "➕ Dodaj rozjazd"
   - Podświetla **dozwolone sąsiednie heksy** (zielone podświetlenie)
   - Walidacja: musi tworzyć ≥25° z głównym torem
   - Komunikat: "Wybierz heks dla rozjazdu (zielone = dozwolone)"

8. **Kliknij sąsiada** (zielony heks)
   - Dodaje do `railway_junction_hexes[]` dla tego heksa
   - Pokazuje w statusie: "Rozjazd dodany z {side}"

9. **Kliknij:** "🔄 Regeneruj tory" 
   - Regeneruje heks z rozjazdem
   - Zachowuje tło i główne tory

#### FAZA 3: Przedłużanie trasy
10. **Kliknij:** "📏 Przedłuż trasę"
    - Podświetla ostatni heks trasy
    - Czeka na kliknięcie sąsiada
    - Dodaje do `railway_path[]`
    - Kontynuacja od kroku 2

---

## 🎨 ZMIANY W UI

### Panel "Tory kolejowe (beta)"

```
[-] Tory kolejowe (beta)
├─ [Włącz tryb torów]  ← Toggle button (jak rzeka/droga)
│
├─ Status: "Trasa torów: 0 heksów"  ← Dynamiczny
│
├─ ┌─ Typ toru ──────────────┐
│  │ ○ Jednotorowy           │
│  │ ● Dwutorowy             │
│  └─────────────────────────┘
│
├─ Seed: [42] [🎲]
│
├─ [🚂 Generuj tory]      ← Aktywny gdy ≥2 heksy
├─ [↩️ Cofnij ostatni]     ← Aktywny gdy ≥1 heks
├─ [🗑️ Wyczyść trasę]      ← Aktywny gdy ≥1 heks
│
└─ ┌─ Rozjazdy (dla zaznaczonego heksa) ───┐
   │ [➕ Dodaj rozjazd]       ← Aktywny gdy heks wybrany
   │ [🔄 Regeneruj tory]     ← Gdy są zmiany
   │ Status: ""
   └──────────────────────────────────────┘
```

### Usunięte kontrolki
- ❌ Combobox "Wejście/Wyjście" - **automatyczne** na podstawie ścieżki
- ❌ Checkboxy rozjazdów - zastąpione **trybem dodawania**

---

## 💻 IMPLEMENTACJA - nowe funkcje

### Zmienne
```python
self.railway_mode_active = False
self.railway_path: list[str] = []  # ["5,3", "6,3", "7,4"]
self.railway_junctions: dict[str, list[str]] = {}  # {"6,3": ["top_left", "top_right"]}
self.railway_junction_mode = False  # Tryb dodawania rozjazdu
self.railway_junction_target_hex: str | None = None  # Heks do którego dodajemy rozjazd
```

### Funkcje
```python
def toggle_railway_mode()
def _set_railway_mode(active: bool)
def _railway_update_status()
def _railway_handle_left_click(hex_id: str)
def _railway_handle_right_click(hex_id: str)
def railway_pop_last_hex()
def clear_railway_path()
def generate_railway_path()  # Generuje dla całej ścieżki
def start_railway_junction_mode()  # Rozpoczyna dodawanie rozjazdu
def _railway_add_junction(junction_hex: str)  # Dodaje rozjazd
def _railway_get_allowed_junctions(hex_id: str) -> list[str]  # Walidacja
def regenerate_railway_hex(hex_id: str)  # Regeneruje z rozjazdami
```

### Logika generowania
```python
def generate_railway_path():
    for i in range(len(railway_path)):
        hex_id = railway_path[i]
        
        # Określ entry/exit z sąsiadów w ścieżce
        if i == 0:
            entry_side = None  # Pierwszy heks - brak entry
            exit_side = _get_direction(hex_id, railway_path[i+1])
        elif i == len(railway_path) - 1:
            entry_side = _get_direction(railway_path[i-1], hex_id)
            exit_side = None  # Ostatni heks - brak exit
        else:
            entry_side = _get_direction(railway_path[i-1], hex_id)
            exit_side = _get_direction(hex_id, railway_path[i+1])
        
        # Pobierz rozjazdy dla tego heksa
        junctions = railway_junctions.get(hex_id, [])
        
        # Generuj tory
        generate_railway_for_hex(
            hex_id=hex_id,
            entry_side=entry_side,
            exit_side=exit_side,
            junctions=junctions,
            railway_type=railway_type_var.get(),
        )
```

---

## 🎯 PRZEWAGI INTERAKTYWNEGO TRYBU

### ✅ Zalety
1. **Intuicyjny** - identyczny workflow jak rzeki/drogi
2. **Wizualny feedback** - widzisz trasę przed generowaniem
3. **Bezpieczny** - walidacja sąsiadów, komunikaty błędów
4. **Elastyczny** - łatwo cofnąć, wyczyścić, przedłużyć
5. **Rozjazdy na żywo** - dodajesz gdzie chcesz, widzisz dozwolone miejsca
6. **Automatyka** - entry/exit kalkulowane automatycznie
7. **Spójność UI** - pasuje do rzek i dróg

### ⚠️ Różnice od obecnego
- ❌ Nie ma ręcznego wyboru entry/exit (automatyczne)
- ✅ Tryb interaktywny (włącz/klikaj/generuj)
- ✅ Podgląd trasy na żywo
- ✅ Rozjazdy dodawane osobno (jak dopływy w rzece)

---

## 📝 PRZYKŁAD UŻYCIA

### Scenariusz: Tor prosty z rozjazdem

1. Kliknij **"Włącz tryb torów"**
2. Kliknij heks A (5,3)
3. Kliknij heks B (6,3) - sąsiad → dodany
4. Kliknij heks C (7,3) - sąsiad → dodany
5. Status: "Trasa torów: 3 heksy"
6. Wybierz **"Dwutorowy"**
7. Kliknij **"🚂 Generuj tory"**
   - Heks A: exit=right (do B)
   - Heks B: entry=left (z A), exit=right (do C)
   - Heks C: entry=left (z B)
   - ✅ Wygenerowane!

8. Kliknij heks B (środkowy)
9. Kliknij **"➕ Dodaj rozjazd"**
10. Podświetlają się dozwolone sąsiedzi (np. top, top_right)
11. Kliknij heks (6,2) - góra
12. Status: "Rozjazd dodany z top"
13. Kliknij **"🔄 Regeneruj tory"**
    - Heks B regeneruje się z rozjazdem top
    - ✅ Gotowe!

---

## 🚀 REKOMENDACJA

**TAK - wdrożyć interaktywny tryb!**

### Powody:
1. ✅ **Spójność** - rzeki i drogi już tak działają
2. ✅ **UX** - znacznie lepsze doświadczenie użytkownika
3. ✅ **Wizualizacja** - widzisz co robisz
4. ✅ **Mniej błędów** - walidacja w locie
5. ✅ **Elastyczność** - łatwe modyfikacje
6. ✅ **Kod** - możemy wykorzystać wzorce z rzek/dróg

### Plan wdrożenia:
1. **Faza 1:** Podstawowy tryb (włącz → klikaj → generuj)
2. **Faza 2:** Rozjazdy (dodawanie jak dopływy)
3. **Faza 3:** Przedłużanie tras
4. **Faza 4:** Modyfikacja istniejących tras

---

## ❓ PYTANIA DO USTALENIA

1. **Czy generować OD RAZU** przy każdym kliknięciu (jak podgląd rzeki)?
   - Lub tylko po "Generuj tory"?

2. **Czy automatycznie łączyć** sąsiednie heksy?
   - Jeśli heks ma już tory i klikam sąsiada - połączyć automatycznie?

3. **Wizualizacja trasy** - jaki kolor overlay?
   - Rzeka = niebieski, droga = brązowy, tory = szary?

4. **Tryb edycji** - czy pozwolić na zmianę typu toru po wygenerowaniu?
   - Regenerować automatycznie czy osobny przycisk?

---

**Czekam na Twoją opinię! Czy wdrażać taki system?** 🚂
