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
- Lista brakujących generatorów względem danych mapy.
- Priorytety wdrożenia (kolejność): krytyczne → często używane → pozostałe.

## 4) Zgodność z silnikiem
- Checklist: `map_data.json`, tekstury, metadane, użycie w `engine/` i `gui/`.
- Walidacje spójności + raport z rozjazdów.

---
**Status**: plan do realizacji (krótki).
