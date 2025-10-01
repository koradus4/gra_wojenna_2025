# Pipeline gry – stan na 1 października 2025

1. Launcher (`ai_launcher.py`) buduje UI, zbiera konfigurację AI/Human i potwierdza start.
2. Przy starcie powstaje `GameEngine` z mapą, indeksami żetonów i stanem początkowym.
3. Tworzeni są gracze (`engine.player.Player`) z rolami, czasem tury i ekonomią (`EconomySystem`).
4. Przypisywane są flagi AI (`is_ai`, `is_ai_commander`) według wyboru w launcherze.
5. Silnik synchronizuje widoczność (`update_all_players_visibility`) i ekonomię graczy.
6. `TurnManager` ustawia kolejkę tur i bieżącą fazę w `utils.turn_context`.
7. Na początku każdej tury `game_engine.current_player_obj` wskazuje aktywnego gracza.
8. Silnik loguje stan punktów kluczowych (`log_key_points_status`).
9. Jeśli tura należy do Generała AI, tworzony jest `GeneralAI` i uruchamia `execute_turn`.
10. `GeneralAI` generuje PE w `EconomySystem`, aktualizuje rezerwę i dzieli budżet między dowódców.
11. Generał zapisuje decyzje w logach CSV/tekst (`ai/logs/general/...`).
12. Jeśli tura należy do Dowódcy AI, tworzony jest `CommanderAI` i uruchamia `execute_turn`.
13. `CommanderAI` filtruje własne żetony po ownerze, dzieli PE po równo i wywołuje `TokenAI`.
14. Każdy żeton otrzymuje `TokenAI.execute_turn(engine, player, share)` z budżetem PE.
15. `TokenAI` loguje wejście (`ai/logs/tokens/...`) i zbiera dane o paliwie, MP i pozycji.
16. Token generuje kandydatów ruchu, wybiera dystans do najbliższego wroga lub najtańszy patrol.
17. Token woła `MoveAction` przez `engine.execute_action` i aktualizuje zasoby według rezultatu.
18. Token bada wrogów w zasięgu, woła `CombatAction` i interpretuje losowe modyfikatory walki.
19. Token zużywa pozostałe PE na `resupply` (paliwo → combat_value) i zapisuje raport końcowy.
20. `CommanderAI` sumuje wydane PE, zwraca resztę do ekonomii i loguje podsumowanie tury.
21. Po turze AI lub człowieka `TurnManager.next_turn()` przesuwa indeks do kolejnego gracza.
22. Przy końcu pełnej tury `game_engine.process_key_points` rozdziela VP i efekty terenowe.
23. Silnik czyści bufory widoczności (`clear_temp_visibility`) i ponownie liczy widoczne heksy.
24. System zwycięstwa (`VictoryConditions`) sprawdza limit tur, VP i warunek eliminacji.
25. Po spełnieniu warunku wypisywany jest raport zwycięstwa i pętla gry jest przerywana.
26. Zamknięcie launchera wywołuje archiwizację sesji (`utils.session_archiver.archive_sessions`).
27. Skrypt logowania (`ai/logs/czyszczenie_logow.py`) dostępny z UI usuwa stare artefakty analityczne.
28. Testy jednostkowe AI (`ai/tests/`) mogą być uruchamiane niezależnie dla walidacji heurystyk.
