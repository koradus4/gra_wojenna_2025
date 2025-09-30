# Pipeline tury żetonu AI

Poniższy opis podsumowuje, jak wygląda pełna sekwencja działań dla jednego żetonu sterowanego przez AI w aktualnym buildzie. Pipeline łączy logikę komendanta (`ai/commander/commander_ai.py`), bazowego AI żetonu (`ai/tokens/token_ai.py`) oraz specjalizacji żetonów.

## 1. Przygotowanie tury przez Komendanta

1. **Reset puli PE i odzyskanie przydziałów**  
   Komendant odzyskuje niewykorzystane punkty ekonomiczne (PE) i czyści poprzednie przydziały (`_reclaim_unused_allowances`).
2. **Przeniesienie nowych PE**  
   Z bieżącej ekonomii gracza cała dostępna wartość `economic_points` trafia do rezerwy komendanta.
3. **Zebranie żetonów gracza**  
   `get_my_tokens` filtruje żetony należące do nacji gracza (bez garnizonów).
4. **Priorytetyzacja i przydział PE**  
   `_prioritize_tokens` i `_allocate_allowances` nadają kolejność (preferując jednostki bojowe z kontaktem ogniowym, na kluczowych punktach, itp.) i przypisują budżet aktywacyjny.
5. **Wybór żetonów do aktywacji**  
   Lista `tokens_to_move` zawiera tylko te żetony, które mają przydział, paliwo i punkty ruchu. Dla każdego z nich powstaje instancja odpowiadającego AI (`create_token_ai`).

## 2. Start tury żetonu

1. **Log startu i porządkowanie pamięci**  
   `execute_turn` w `TokenAI` loguje rozpoczęcie, czyści przeterminowane wpisy o nieudanych ruchach (`_cleanup_failed_targets`).
2. **Odczyt pamięci / stanu**  
   Każdy żeton ma pamięć (`ai_memory`) dzieloną między tury: zapamiętani wrogowie, nieudane cele, rezerwacje.

## 3. Pozyskanie informacji o otoczeniu

1. **Wykrywanie wrogów**  
   `find_enemies_in_sight` skanuje zasięg wzroku, zapamiętuje widzianych przeciwników i loguje wynik.
2. **Wybór priorytetów ruchu** (`decide_move_target`)
   - Jeśli wróg jest w zasięgu wzroku → kierunek na jego heks.
   - Jeśli brak kontaktu, ale są wpisy z pamięci wspólnej (`_select_recent_enemy_target`) → marsz na ostatnio znany heks.
   - Kolejno: najbliższy kluczowy punkt (`_find_closest_objective`) lub patrol (`_select_patrol_target`).
   - Jeżeli wszystkie opcje zawiodą → brak ruchu.

## 4. Planowanie ruchu i rezerwacja heksów

1. **Plan podstawowy** (`_plan_move_target`)
   - Sprawdza, czy cel nie jest świeżo oznaczony jako problematyczny (ostatnie niepowodzenia).
   - Weryfikuje zajętość heksu. Jeśli stoi na nim sojuszniczy transport zaopatrzeniowy, zgłasza prośbę o ustąpienie (`_request_supply_vacate`).
   - Rezerwuje heks docelowy lub heks podejścia i zapisuje klucz rezerwacji w `engine.ai_reserved_hexes`.
2. **Brak planu podstawowego → fallback planowania**  
   Jeśli nie można zarezerwować heksu docelowego, AI rozważa alternatywy:
   - `self._is_recent_failure` i `_find_staging_hex` szukają obejścia.
   - `_prepare_fallback_plan` może wskazać heks do obejścia lub patrol.

## 5. Wykonanie ruchu

1. **Podstawowa próba ruchu** (`_attempt_move_to_hex`)
   - Tworzy `MoveAction` i wywołuje `engine.execute_action`.
   - Na podstawie wyniku aktualizuje logi, pamięć o niepowodzeniach (`_record_move_failure`) i zwalnia rezerwację.
2. **Ruch awaryjny**  
   - Jeżeli ruch podstawowy się nie powiedzie i `self._can_attempt_fallback` na to pozwala, `_select_fallback_after_failure` wybiera alternatywny heks (staging lub patrol).
   - Fallback także przechodzi przez `_attempt_move_to_hex`; kolejne porażki trafiają do logów.
3. **Zwolnienie rezerwacji**  
   Po zakończeniu prób ruchu (sukces lub porażka) rezerwacja heksu jest zwalniana.

## 6. Faza walki

1. **Decyzja o ataku** (`decide_attack_target`)
   - Ponownie ocenia widzianych wrogów z `find_enemies_in_sight`.
   - Sprawdza zasięg i dostępność ataku (`can_attack_target`).
2. **Wykonanie walki**  
   Jeśli wybrano cel, inicjuje `CombatAction`. Wynik jest logowany (sukces/porażka).
   Jeżeli brak celu – log informacyjny.

## 7. Zakończenie tury żetonu

1. **Log końcowy**  
   `execute_turn` zamyka turę logiem INFO.
2. **Aktualizacje pamięci**  
   Wpisy o nieudanych heksach zachowują datę (turę) i przyczynę, by unikać powtarzania błędów w następnych turach.

## 8. Po turze żetonu – działania komendanta

1. **Rejestrowanie zużycia PE**  
   Po powrocie z `execute_turn` komendant aktualizuje statystyki (`_record_consumption`).
2. **Raport końcowy**  
   `CommanderAI.execute_turn` zestawia liczbę aktywowanych żetonów, zużyte PE i pozostające rezerwy.

---

### Dodatkowe uwagi

- **Wspólna pamięć o wrogu** – `engine.ai_enemy_memory` umożliwia żetonom i komendantowi współdzielenie informacji o wrogach (z czasem wpisy wygasają).
- **Specjalizowane AI** – `SupplyTokenAI`, `CavalryTokenAI` itd. nadpisują fragmenty bazowego algorytmu (np. reakcji na prośby o zwolnienie heksu, agresja kawalerii), ale pipeline pozostaje taki sam.
- **Logowanie** – wszystkie kluczowe decyzje i błędy (rezerwacje, porażki ruchu, fallbacki) są logowane przez `ai.logs.log_token` / `log_commander`, co pozwala odtworzyć krok po kroku przebieg tury.
