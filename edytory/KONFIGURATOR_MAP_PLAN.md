# Konfigurator mapy / generator heksow – plan prac

## Cel
- Umozliwic definiowanie rozmiaru mapy (hex_size, grid_cols, grid_rows) bez recznego edytowania JSON.
- Odejsc od statycznego tla JPG na rzecz renderu z płytek lub przynajmniej kontrolowanego skalowania.
- Zapewnic, ze nowe mapy sa w pelni zgodne z silnikiem, GUI, testami i narzedziami.

## Kontekst
- Aktualny edytor (`edytory/map_editor_prototyp.py`) zaklada siatke 56x40 i hex_size 30, duzo logiki zapisuje od razu do `data/map_data.json`.
- Runtime (`engine/board.Board`, `engine/engine.GameEngine`) czyta parametry z `meta` mapy, wiec jest gotowy na inne wymiary.
- GUI i testy korzystaja z `assets/mapa_globalna.jpg` jako tla.

## Zaleznosci do przejrzenia
1. GUI: `gui/panel_gracza.py`, `gui/panel_dowodcy.py`, `gui/panel_generala.py`, testy GUI (np. `tests/gui/test_panel_gracza_gui.py`) – wszedzie hardcode `assets/mapa_globalna.jpg`.
2. Silnik: `engine/board.py`, `engine/engine.py`, `engine/player.py`, launchery (`main.py`, `launchers/main_basic.py`, `launchers/main_alternative.py`, `ai_launcher.py`) – ustawienia `map_path="data/map_data.json"`.
3. Narzedzia/testy: liczne skrypty w `tools/`, `czyszczenie/`, `scripts/`, `tests/` oraz dokumentacja (`docs/`, `plans/`, `STRUKTURA_PROJEKTU.md`) zakladaja `data/map_data.json`.
4. Eksport startowych zetonow: `assets/start_tokens.json` – musi byc czyszczony po zmianie siatki.
5. Kopie i cleaner: `czyszczenie/game_cleaner.py`, `czyszczenie/reset_tokens_simple.py`, backupy – kopiowanie/przywracanie `map_data.json`.

### Wyniki wstepnego grepa
- `assets/mapa_globalna.jpg`: GUI (panele), testy GUI, `engine/player.py`, domyslna mapa w edytorze.
- `data/map_data.json`: praktycznie caly runtime (silnik, testy jednostkowe/integracyjne, narzedzia diagnostyczne i cleaning, dokumentacja). Zmiana format/ścieżka wymaga koordynacji globalnej.
- Magic numbers 56/40/30: startowa siatka w `map_editor_prototyp.py` (`CONFIG`), potwierdzone w `data/map_data.json` oraz opisach (`plans/REPREZENTACJA_AI_NIEMCY.md`). Inne trafienia 40 pochodzą z losowych stałych (np. formatowanie logów) i nie są związane z mapą.

## Etapy prac
1. **Audyt danych**
   - Zebrac wszystkie hardcode na liczbie kolumn/wierszy i sciezce JPG.
   - Dodac do test planu liste plikow do aktualizacji.

2. **MVP konfiguratora**
   - W edytorze: dialog ustawien z walidacja (min/max, potwierdzenie utraty danych poza nowa siatka).
   - Po zmianie: przebudowa `hex_centers`, usuniecie terrain/token/spawn/key_points z heksow spoza zakresu, auto eksport JSON.
   - Ostrzezenie o tle, jezeli obecny obraz nie miesci nowej siatki.
   - **Dialog konfiguratora – szkic UI**:
     - Przycisk w panelu edytora (`Konfiguracja mapy…`).
     - Okno modalne (Toplevel) z trzema polami liczbowymi (`Szerokość (kolumny)`, `Wysokość (wiersze)`, `Rozmiar heksa`), sliderami lub spinboxami; default = aktualne wartości.
     - Sekcja „Skutki zmiany” – tekstowa lista z dynamiczną informacją: liczba heksów, ile wpisów terrain/spawn/key_points zostanie utraconych, status zgodności tła (np. ✅ mieści się / ⚠️ wyjdzie poza obraz).
     - Checkbox „Eksportuj startowe żetony po zmianie” (domyślnie ON) oraz „Zrób kopię map_data.json przed zmianą”.
     - Przyciski `Anuluj` / `Zastosuj`, przy `Zastosuj` dodatkowy popup potwierdzający, jeśli coś znika.
     - Obsługa zapamiętywania ostatnio użytych parametrów (np. w `configparser` albo w meta edytora).
    - **Logika zastosowania zmian** (do zaimplementowania w `MapEditor`):
     1. Odczytaj i zwalifiduj wejście (`cols` 10-120?, `rows` 10-120?, `hex_size` 16-60?).
     2. Jeżeli wartości identyczne z bieżącymi → zamknij dialog bez działań.
     3. Przygotuj listę heksów, które wyjdą poza zakres: sprawdź `hex_data.keys()`, `key_points`, `spawn_points`; policz ile wpisów zostaje usuniętych i pokaż w dialogu.
     4. Jeśli użytkownik potwierdzi, wykonaj:
        - Aktualizację `self.config['grid_cols']`, `self.config['grid_rows']`, `self.hex_size`.
        - Usuń dane heksów/spawnów/kp spoza zakresu.
        - Zaktualizuj `self.canvas`, w razie potrzeby przeładuj tło albo zgłoś ostrzeżenie.
        - Wywołaj `save_data()` i (jeśli checkbox) `export_start_tokens()`.
        - Włącz auto-save dopiero po zakończeniu procesu, aby uniknąć częściowych zapisów.
     5. Jeżeli włączona opcja kopii → zapisz `data/map_data.json.bak-<timestamp>` przed zmianą.
   - Format: `map_data.json.bak-YYYYMMDD-HHMMSS` (np. `map_data.json.bak-20251010-1945`).
   - Przechowuj maksymalnie 5 najnowszych kopii (starsze usuwaj automatycznie, aby katalog się nie rozrastał).
     6. Po sukcesie wypisz status w konsoli i zaktualizuj etykiety info panelu.

    - **Limity / preset scenariuszowy**
       - Twarde minimum: `cols` >= 10, `rows` >= 10, `hex_size` >= 16 (żeby uniknąć zerowych siatek).
       - Ostrzeżenie wydajności/grywalności: `cols` > 120 lub `rows` > 90, `hex_size` > 48 (można kontynuować, ale UI informuje o potencjalnych skutkach: duża mapa, dłuższe ruchy, dopasowanie tła).
       - W dialogu dodać presety scenariuszowe (np. „Szybka potyczka” 30×20, „Standard” 56×40, „Kampania” 120×80) oraz możliwość ręcznej korekty.
       - W sekcji „Skutki zmiany” pokazywać również szacowaną długość przejazdu jednotki kawalerii (przykładowo maksymalny MP * koszt heksu) dla kontekstu balansowego.

    - **Wsparcie pod przyszłe scenariusze historyczne**
       - Notować w meta mapy (lub osobnym pliku scenariusza) referencję do realnego obszaru (np. skala kilometrowa), aby łatwiej kontrolować, czy jedna tura ruchu odpowiada realistycznym dystansom.
       - Przy planowanej kampanii (np. Bzura) przewidzieć narzędzie do dzielenia formacji: checkbox „Rozbij jednostki według scenariusza” mógłby generować mniejsze żetony i dopasowywać ich wejścia do rozmiaru mapy.
       - Potencjalnie dodać w dialogu informację o maksymalnej liczbie heksów w zasięgu ruchu aktualnie wybranej jednostki (reguła: `maxMovePoints / (1 + min(move_mod))`) dla kontroli, czy mapa nie jest „przejezdna w turę”.

3. **Renderer tilesetowy (opcjonalny, docelowy)**
   - Przygotowac katalog `assets/tiles/<terrain>.png` (wzorce dla kazdego terrain_key).
   - Skrypt renderujacy bitmape z `map_data.json` (np. `tools/map_renderer.py`).
   - Integracja z edytorem: generowanie podgladu i eksport nowego tla do `assets/maps/<nazwa>.png`.

4. **Scenariusze**
   - Struktura `data/maps/<scenariusz>.json` + startowe zetony.
   - W launcherze mozliwosc wyboru scenariusza.

5. **Aktualizacja testow i narzedzi**
   - Testy jednostkowe: pobierac parametry z JSON, zamiast zakladania 56x40.
   - Narzedzia czyszczace/diagnostyczne: uzyc modulow wspolnych do ladowania mapy.

## Otwarte pytania
- Czy generujemy tileset w oparciu o istniejace grafiki, czy potrzebne nowe assety?
- Jak zachowujemy kompatybilnosc z zapisami (czy stare save beda dzialac po zmianie mapy)?
- Czy wprowadzamy wersjonowanie plikow map (np. meta.version)?

## Krótkie KPI
- Konfigurator pozwala zapisac mniejsza/wieksza siatke bez bledow eksportu.
- Render wygenerowanej mapy pokrywa sie z danymi terrain/spawn/key_points.
- Testy integracyjne przechodza po zmianie mapy.

## Kolejne kroki (na start)
1. Przejsc kod z grepem po `map_data.json`, `mapa_globalna.jpg`, magicznych liczbach 56/40.
2. Spisac wyniki audytu w tej notatce.
3. Zaprojektowac interfejs dialogu konfiguratora (mock UI) i logike czyszczenia danych poza siatka.
