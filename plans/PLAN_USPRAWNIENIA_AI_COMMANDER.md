# PLAN USPRAWNIENIA AI COMMANDER 
## Analiza i usprawnienia trybu niezależnego (28.08.2025)

---

## 📋 OBSZARY DO UZGODNIENIA

## ✅ Jutrzejszy pakiet – skrócone punkty do rozkminy

1. Licznik ruchów: poprawne inkrementowanie + logowanie moved_units / movable_units.
2. Log skip_reason dla każdej jednostki nieporuszonej (no_target, no_path, zero_mp, garrison_hold, dithering_block, threat_retreat).
3. Anti‑dithering artylerii: histereza (utrzymaj pozycję gdy w promieniu 1–2 heksów ≥2 tury).
4. Rotacja garnizonów: turns_static > 5 i brak wroga → zwolnij garrison.
5. Momentum push: jeśli momentum < 0.3 przez 3 tury → obniż priorytet zbędnych garnizonów, bonus do wolnych kluczowych punktów.
6. Minimalna aktywność: gdy moved_units == 0 wymuś 1 ruch (wybór najbardziej sensownej jednostki idle).
7. Decay garrison_lock: automatyczna rewalidacja potrzeby garnizonu po zejściu timera.
8. Losowy tie‑break (±0.05) przy remisach priorytetów celów.
9. Watchdog stagnacji: 3 tury z rzędu moved_units == 0 → log STAGNATION_ALERT + agregat skip_reason.
10. KPI do monitorowania: idle ratio, momentum, garrison saturation, dithering count, średnia długość ruchu.

// Po analizie: ewentualny wybór kolejności implementacji (min. 1–3 + 5 na start).

