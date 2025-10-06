# OPIS KATALOGU GUI – Przewodnik (23.09.2025)

## Przeznaczenie
Pakiet `gui/` zawiera panele interfejsu użytkownika gry „Kampania 1939” dla trybu human vs human. GUI komunikuje się z silnikiem (`engine/`) i warstwą logiki (`core/`) przez publiczne API – nie przechowuje własnego stanu gry poza tymczasowymi elementami UI.

## Kluczowe komponenty
- `panel_generala.py` – Główne okno generała: portret, ekonomia, panel pogody, mapa, przydział punktów dowódcom, sklep jednostek.
- `panel_dowodcy.py` – Główne okno dowódcy: portret, timer tury, panel pogody, mapa, przycisk wystawiania jednostek, tankowanie wybranej jednostki.
- `panel_mapa.py` – Widok mapy (Canvas): render tła, siatki hexów, mgły wojny (FoW), żetonów, markerów, podświetleń. Od 23.09.2025: nakładka przyciemnienia wieczorem/nocą.
- `panel_pogodowy.py` – Zwięzły raport: „Data/Dzień | Pora dnia | Pogoda”. Aktualizowany poprzez `update_weather()` z `TurnManager.get_ui_weather_report()`.
- `panel_gracza.py`, `panel_ekonomiczny.py` – Panele informacyjne dla gracza i ekonomii.
- `token_shop.py`, `deploy_new_tokens.py` – Zakupy i wystawianie jednostek.
- `tooltip_token_info.py`, `detection_display.py` – Tooltips i prezentacja poziomów detekcji.

## Integracja z porami dnia (NOWE)
- `TurnManager.get_ui_weather_report()` zwraca jednowierszowy raport zawierający porę dnia.
- `panel_generala.py` i `panel_dowodcy.py` parsują frazę „Pora dnia: …” i wywołują `PanelMapa.update_daylight_overlay(phase)`.
- `PanelMapa.update_daylight_overlay(phase)` nakłada półprzezroczysty prostokąt na Canvas:
  - rano/dzień – brak nakładki,
  - wieczór – szachownica `gray25` (delikatne przyciemnienie),
  - noc – `gray50` (wyraźniejsze przyciemnienie).
- Jest to efekt wyłącznie wizualny; logika widoczności i FoW działa bez zmian.

## Zależności i kontrakty
- GUI zakłada publiczne metody silnika: `game_engine.board`, `game_engine.tokens`, `game_engine.update_all_players_visibility(players)`, a także dostęp do aktualnego gracza `game_engine.current_player_obj`.
- `PanelMapa` korzysta z `Board.hex_to_pixel()` i `engine.hex_utils.get_hex_vertices()` do rysowania.
- Widoczność jest filtrowana na podstawie `player.visible_hexes`, `player.visible_tokens` oraz tymczasowych zestawów (`temp_visible_*`).

## Wskazówki rozwojowe
- Utrzymuj pojedynczy punkt aktualizacji pogody: zawsze podawaj wynik `TurnManager.get_ui_weather_report()`.
- Przy nowych efektach graficznych używaj tagów Canvas i `tag_raise`, aby overlay pozostawał nad innymi elementami.
- Staraj się nie umieszczać logiki gry w GUI – jedynie prezentacja i delegacja zdarzeń.

## Logowanie i czyszczenie
- Panele generała i dowódców korzystają z tego samego menedżera sesji co AI – logi trafiają do `ai/logs/sessions/<timestamp>/`.
- Przyciski „Wyczyść logi” oraz funkcje diagnostyczne wywołują `ai/logs/czyszczenie_logow.py` lub `utils/session_manager.py.clean_current_session`, dlatego przy zmianie ścieżek należy aktualizować jedynie te moduły pomocnicze.

## Pliki pomocnicze
- `ai_config_panel.py` – Panel konfiguracji AI (historyczny; w projekcie bez AI pozostaje jako referencja GUI).
- `opcje_dostepnosci.py` – Opcje ułatwień dostępu.

---
Ostatnia zmiana: 23.09.2025 – dodano opis pór dnia i nakładki przyciemniającej w `PanelMapa`.