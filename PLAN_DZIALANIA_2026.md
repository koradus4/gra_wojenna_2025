# PLAN DZIAŁANIA NA PRZYSZŁOŚĆ (skrót)

## 1) Unifikacja GUI generatorów (Map Editor + generate_*)
- **Audyt**: porównać sekcje generatorów w Map Editor z parametrami `generate_*`.
- **Różnice UX/parametrów**: spisać brakujące/powielone opcje.
- **Wspólny szablon UI**: presety + panel zaawansowany.
- **Spójna logika**: podgląd / seed / cache / clean.
- **Wdrożenie etapami**:
  1. Szablon UI + mapowanie parametrów
  2. Migracja generatorów po jednym
  3. Testy dymne + poprawki

## 2) Hex Inspector = Map Editor (1:1)
- Mapowanie funkcji i parametrów bez rozjazdów.
- Zestawy „realne” scenariusze: **rzeka/dopływ**, **droga/skrzyżowanie**, **jeziora**, **kolej**.
- Ujednolicenie presetów i walidacji.

## 3) Analiza mapy (pełna cyfryzacja)

### Istniejące generatory:
✅ `generate_river_hex_tile.py` – rzeki i dopływy
✅ `generate_lake_hex_tile.py` – jeziora
✅ `generate_road_hex_tile.py` – drogi i skrzyżowania
✅ `generate_railway_hex_tile.py` – kolej

### Brakujące generatory (wg analizy wizualnej mapy z 18.01.2026):

**KRYTYCZNE** (zajmują >15% mapy, kluczowe dla rozgrywki):
1. **`generate_forest_hex_tile.py`** – lasy (różna gęstość, pojedyncze drzewa vs gęste lasy)
2. **`generate_mountain_hex_tile.py`** – góry i wzgórza (tereny wzniesione, ukształtowanie)
3. **`generate_city_hex_tile.py`** – miasta, miejscowości i umocnione miejscowości (zabudowa, fortyfikacje)

**WAŻNE** (średnio częste, rozszerzenia istniejących):
4. **Mosty** – rozszerzenie `generate_river_hex_tile.py` (skrzyżowania rzek z drogami/kolejami)
5. **`generate_border_hex_tile.py`** – granice państwowe (linie wyznaczające granice)
6. **`generate_swamp_hex_tile.py`** – bagna/mokradła (w dolinach rzek)

**UZUPEŁNIAJĄCE** (rzadkie, specjalne przypadki):
7. **`generate_hill_hex_tile.py`** – pagórki (jeśli oddzielne od gór)
8. **`generate_field_hex_tile.py`** – pola uprawne (jeśli odróżniamy od równin)
9. **`generate_ford_hex_tile.py`** – brody/przeprawy (wariant rzeki, płytkie miejsca)
10. **`generate_fortification_hex_tile.py`** – umocnienia (przy miastach/granicach)

### Priorytety wdrożenia:
1. **Faza 1**: Lasy, Góry/wzgórza, Miasta (krytyczne dla pokrycia mapy)
2. **Faza 2**: Mosty (rozszerzenie rzek), Granice, Bagna (uzupełnienie funkcjonalności)
3. **Faza 3**: Pozostałe generatory wg potrzeb gameplay

## 4) Zgodność z silnikiem
- Checklist: `map_data.json`, tekstury, metadane, użycie w `engine/` i `gui/`.
- Walidacje spójności + raport z rozjazdów.

---
**Status**: plan do realizacji (krótki).
