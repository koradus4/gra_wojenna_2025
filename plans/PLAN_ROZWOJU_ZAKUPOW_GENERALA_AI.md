# Plan rozwoju zakupów Generała AI

(Dokument przeniesiony z `docs/plans/PLAN_ROZWOJU_ZAKUPOW_GENERALA_AI.md`)

Dokument koncentruje się wyłącznie na WARSTWIE STRATEGICZNO–EKONOMICZNEJ (zakupy, alokacja, priorytety). Ruch, walka, deploy – poza zakresem.

## 1. Cel
Usprawnić decyzje zakupowe AI Generała tak, by odzwierciedlały rolę ludzkiego generała: kontrola struktury armii, świadome priorytety, zarządzanie ryzykiem ekonomicznym (utrzymanie), przygotowanie na przyszłe tury.

## 2. Stan obecny (skrót)
- Heurystyki: zaopatrzenie, artyleria, pancerz przeciwnika, mobilność, różnorodność.
- Jednostkowy wybór szablonu (template) – brak planu wieloturu.
- Prosty wybór wsparć – brak optymalizacji kombinacji.
- Brak rezerwy strategicznej i prognozy maintenance.
- Brak kompozycji docelowej (procentowe udziały typów).
- Brak alokacji per dowódca (globalny budżet).
- Log: tylko granularne zakupy (CSV), brak podsumowania tury.

## 3. Luki
| Obszar | Brak | Skutek |
|--------|------|--------|
| Kompozycja | Docelowych udziałów klas | Chaotyczny rozwój składu |
| Budżet | Rezerwy / wielotur | Niemożność kupna drogich jednostek |
| Maintenance | Prognozy i limitów | Ryzyko długu ekonomicznego |
| Wsparcia | Oceny kombinacji | Niska efektywność koszt/siła |
| Alokacja | Przydział do sektorów/dowódców | Nierównowaga frontów |
| Adaptacja | Pętla feedbacku | Powtarzanie błędów kompozycji |
| Logowanie | Podsumowania strategicznego | Mała diagnozowalność |
| Ochrona ryzyka | Guard rails ekonomii | Nadmierne wydatki w złej chwili |

## 4. Fazy wdrożenia
1. Kompozycja docelowa (target composition) + scoring odchyleń.
2. Budżet 2.0 (rezerwa wielotur + limity maintenance).
3. Optymalizator wsparć (ograniczone przeszukiwanie kombinacji).
4. Alokacja do dowódców (prosty model sektorów / klastrów).
5. Adaptacyjna korekta wag (feedback strat + luki niezamknięte).
6. Log strategiczny tury (agregaty, flagi ryzyka, JSON kompozycji).
7. Zaawansowana różnorodność (limity min/max, anty‑spam).
8. Economic Risk Guard (progi maintenance_ratio + hamulec wydatków).

## 5. Szczegóły wybranych elementów
### 5.1 Target Composition
Słownik udziałów klas (np. artyleria, pancerz, piechota, supply, rozpoznanie). Oblicz aktualny udział, wyznacz największą lukę; premiuj zakup, który ją zmniejsza.

### 5.2 Budżet 2.0
Oblicz: expected_income_next_turn, total_maintenance_after. Wyznacz spending_cap = dynamiczna funkcja (luki + maintenance_ratio). Rezerwa minimalna na ciężką jednostkę.

### 5.3 Optymalizator wsparć
Enumeracja do małej głębokości (np. ≤3 wsparcia). Ocena = (combat_gain + strategic_bonus − price_penalty). Cache per (unit_type,size).

### 5.4 Alokacja do dowódców
Grupowanie istniejących jednostek (np. proste podział na sektory mapy). Lokalny deficyt klas → wybór dowódcy właściciela nowej jednostki.

### 5.5 Adaptacyjna korekta
Jeśli luka klasowa nie maleje ≥2 tury: waga heurystyki *1.3 (clamp). Damping maks. zmiana 0.3 na turę.

### 5.6 Log strategiczny
Plik: logs/ai_purchase_summary_YYYYMMDD.csv (1 wiersz / tura). Kolumny: turn, spent, reserve_end, maintenance_next, largest_gap, gap_value, purchases_json, composition_json, warnings.

### 5.7 Różnorodność zaawansowana
Minimalne proporcje (np. supply ≥ 1 na 6 jednostek bojowych). Maks. udział podtypu (np. TL ≤ 35% pancerza). Wymuszenie zakupu brakującej kategorii jeśli naruszono minimum.

### 5.8 Economic Risk Guard
maintenance_ratio = maintenance / expected_income_next_turn. Progi: >0.55 (żółta flaga), >0.7 (czerwona – obcięcie spending_cap + priorytet supply).

## 6. Interfejs planera
`plan_purchases(state) -> PurchasePlan` zwraca listę `PlannedPurchase` + meta (spending_cap, reserve_after, warnings, reason_tags).

## 7. Testy
- Jednostkowe: scoring kompozycji, ranking wsparć.
- Scenariusze: brak artylerii → zakup w 1 turze; wzrost maintenance → rezerwa.
- Property: brak przekroczenia limitów max; wymuszenie minima.
- Regressions: snapshot planu dla kontrolowanych wejść.

## 8. Metryki "sukcesu"
- Malejąca suma odchyleń kompozycji w horyzoncie 5 tur.
- maintenance_ratio < 0.7 w testach.
- Test coverage modułu planera ≥ 85%.
- Czas planowania < ~30 ms (orientacyjnie) przy 50 jednostkach.

## 9. Ryzyka
| Ryzyko | Efekt | Mitigacja |
|--------|-------|-----------|
| Złożoność wsparć | Spowolnienie | Limit szerokości + cache |
| Nadmierna rezerwa | Spowolniony wzrost | Min spending floor |
| Oscylacje wag | Niestabilne zakupy | Damping zmian |
| Pomiar maintenance niedokładny | Błędne hamowanie | Safety margin |

## 10. Minimalny zakres "DONE" etapu bazowego
Fazy 1–4 + log strategiczny, testy kluczowe przechodzą, brak regresji istniejących testów AI.

---
Aktualizować iteracyjnie po każdej fazie (sekcja zmian może zostać dopisana w przyszłości).
