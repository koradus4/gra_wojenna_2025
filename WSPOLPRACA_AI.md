# Współpraca z Copilotem (zasady pracy)

Ten plik opisuje zasady współpracy przy zmianach w repozytorium. Celem jest powtarzalność pracy i brak „zaskoczeń”.

## 1) Dlaczego czasem „zapominam” ustalenia

Copilot nie ma trwałej pamięci jak człowiek. Działa na podstawie:
- bieżącej rozmowy (jej kontekst może być skracany),
- plików w repo (to jest najtrwalsze źródło prawdy).

Dlatego kluczowe zasady zapisujemy tutaj.

## 2) Zasada zgody przed zmianami

**Zanim zrobię jakiekolwiek zmiany w projekcie, najpierw proszę o zgodę.**

Minimalny „pakiet zgody”:
- co zmieniam (1–2 zdania),
- w jakich plikach,
- jak sprawdzę poprawność.

Wyjątki: brak (chyba że jawnie ustalisz inaczej w tej samej rozmowie).

## 3) Zasada weryfikacji po zmianach

Po każdej zmianie potwierdzam poprawność wykonanej pracy.

### A) Preferowane: testy
- Uruchomienie istniejących testów jednostkowych/integracyjnych (`pytest`, skrypty w `tests/`, zadania VS Code).
- Uruchomienie smoke testów (np. szybkie scenariusze uruchomieniowe).

### B) Inne sposoby potwierdzania poprawności (gdy testów brak / nie obejmują zmiany)

Co najmniej jeden z poniższych sposobów (dobierany do zmiany):
- **Replay deterministyczny / odtwarzalność**: użycie zapisanej konfiguracji (`hex_config.json` / `case.json`) i uruchomienie `scripts/replay_hex_case.py`.
- **Smoke-run aplikacji/skryptu**: uruchomienie konkretnego entrypointu z minimalną konfiguracją (np. 1 tura, tryb „--clean”).
- **Walidacja statyczna**: sprawdzenie błędów analizy (Problems / Pylance) i brak nowych błędów w zmienianych plikach.
- **Kontrola artefaktów wyjściowych**: sprawdzenie, że generowane pliki powstają (np. PNG/JSON w `_hex_inspector_output/`) i mają sensowną strukturę.
- **Porównanie wyników (diff wizualny/logiczy)**: porównanie „przed/po” na tym samym seedzie / configu.
- **Sanity-check logów**: potwierdzenie, że logi nie zawierają wyjątków, tracebaków i że kluczowe kroki się wykonują.

W raporcie po zmianach zawsze podaję:
- jaką metodą sprawdziłem poprawność (konkretna komenda/zadanie),
- gdzie są wyniki (np. folder replay, wygenerowane pliki).

## 4) Zasada minimalnego wpływu

- Zmieniam tylko to, co jest potrzebne do celu.
- Nie robię refactorów „przy okazji” bez zgody.
- Nie zmieniam formatu plików/struktur bez uzasadnienia.

## 5) Zasada architektury dla generatorów/QA

- **Hex Inspector i replay** są narzędziami testowymi/QA.
- Poprawki logiki/semantyki trafiają do generatorów (`edytory/generate_*.py`).
- Exporty są tak projektowane, żeby były odtwarzalne (seed + JSON).

## 6) Jak najlepiej współpracować na co dzień

Najlepszy workflow:
1. Ty wrzucasz problem + (jeśli możliwe) repro (`hex_config.json` / `case.json`).
2. Ja proponuję zmianę i proszę o zgodę.
3. Po akceptacji wprowadzam zmianę.
4. Potwierdzam poprawność (test/replay/smoke).
5. Zostawiam krótką notatkę „co zmieniłem” + „jak odtworzyć”.

## 7) Zasada pełnej analizy + zwięzłej odpowiedzi

- Jeśli proponuję Ci rozwiązanie, to **powstaje ono po pełnej analizie** (reasoning z kodem, analiza repo/artefaktów; gdy ma to sens również inne formy analizy, np. porównanie wyników renderu/„vision reasoning”).
- Natomiast **odpowiedź dla Ciebie ma być prosta i krótka**: bez zbędnego rozpisywania — interesują Cię przede wszystkim **efekty**, co konkretnie się zmieniło i jak to sprawdzić.
