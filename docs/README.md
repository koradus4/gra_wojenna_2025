# Dokumentacja Projektu Gra Wojenna — Wersja 4.2 (bez AI)

UWAGA — 22.09.2025: Cały system AI został usunięty z projektu. Gra działa wyłącznie w trybie Human vs Human (HvsH). Wszelkie sekcje dotyczące AI zostały zarchiwizowane lub usunięte. Ten plik odzwierciedla aktualny stan projektu bez AI.

## Struktura Dokumentacji (aktualna)

```
docs/
├── README.md                    # Ten plik — przegląd dokumentacji (aktualny bez AI)
├── STRUKTURA_PROJEKTU.md        # Główny dokument — struktura i stan projektu (bez AI)
├── TOKEN_EDITOR_FIX.md          # Poprawki edytora tokenów
├── TOKEN_BALANCING_GUIDE.md     # Przewodnik balansowania
├── HEX_BALANCING_GUIDE.md       # Balansowanie planszy hexagonalnej
├── ARTILLERY_SHOT_LIMITS.md     # Ograniczenia artylerii
├── HUMAN_VISION_SYSTEM.md       # System wizji graczy (dla HvsH)
├── IMPLEMENTACJA_WORKFLOW_ZAKONCZONA.md
├── NOWY_WORKFLOW_ZETONOW.md
├── logging/
│   ├── README.md
│   ├── PODSUMOWANIE_SYSTEMU_LOGOWANIA.md
│   ├── IMPLEMENTACJA_LOGGING_SYSTEM.md
│   ├── ANALIZA_LOGOWANIA_I_CZYSZCZENIA.md
│   └── demo_logging_system.py
└── cleaning/
    ├── README.md
    ├── ANALIZA_BEZPIECZENSTWA_CZYSZCZENIA.md
    └── FINALNY_RAPORT_BEZPIECZENSTWA.md
```

## Najważniejsze informacje (4.2)

- Projekt działa wyłącznie w trybie Human vs Human (HvsH).
- Pakiet i dokumentacja AI zostały usunięte. Pozostałe wzmianki traktuj jako archiwalne.
- Aktualny, polski system logowania i czyszczenia logów pozostaje dostępny i wspierany.

## System logowania i czyszczenia (polski)

- Zintegrowany polski system logowania z rotacją sesji i oddzielnymi katalogami.
- Inteligentne czyszczenie logów (ochrona danych analitycznych/ML, rotacja archiwum).
- Szczegóły: dokumenty w `docs/logging/` i `docs/cleaning/`.

## Przegląd gry (bez AI)

- Rozgrywka toczy się wyłącznie między dwoma graczami (HvsH).
- Interfejs startowy pozwala wybrać podstawowe parametry (np. limit tur, tryb zwycięstwa).
- Funkcje AI nie są dostępne — wszelkie wcześniejsze wzmianki w dokumentacji są historyczne.

## Narzędzia i skrypty

- Narzędzia i testy zależne od AI zostały usunięte z repozytorium.
- Dostępne są wyłącznie neutralne narzędzia (np. czyszczenie logów w `czyszczenie/`, utilsy w `utils/`).

## Dokumenty — co warto przeczytać teraz

1. [STRUKTURA_PROJEKTU.md](../STRUKTURA_PROJEKTU.md) — przegląd aktualnej struktury i statusu (bez AI).
2. `docs/logging/` — polski system logowania, rotacja sesji, ochrona danych.
3. `docs/cleaning/` — bezpieczne czyszczenie logów i archiwizacja.

## 🚀 Quick Start (HvsH)

Uruchomienie gry w trybie Human vs Human:

1) Uruchom `main.py` i skonfiguruj grę na ekranie startowym (limit tur, tryb zwycięstwa).
2) Graj naprzemiennie dwiema stronami na jednym komputerze.

Opcjonalnie:
- Korzystaj z polskiego systemu logowania (sesje/archiwum) — szczegóły w `docs/logging/`.
- Czyść bezpiecznie logi przez narzędzia w `czyszczenie/`.

## Analiza i metryki

Obecnie metryki związane z AI nie mają zastosowania. Zalecane jest koncentrowanie się na metrykach rozgrywki HvsH oraz jakości logów (patrz `docs/logging/`).

## Rozszerzanie systemu (bez AI)

Skupiamy się na mechanikach rdzeniowych, UI oraz narzędziach wspierających (logowanie, czyszczenie). Jeśli AI powróci w przyszłości, dokumentacja zostanie przywrócona w rozdzielnym archiwum.

## Znane problemy i wsparcie

- Jeśli natrafisz na stare wzmianki o AI w dokumentach, potraktuj je jako archiwalne. W przyszłości mogą zostać przeniesione do `docs/archives/`.

## Kontakt i wsparcie

Zgłaszanie problemów: prosimy o dołączanie logów z bieżącej sesji (`logs/sesja_aktualna/`) oraz krótkiego opisu kroków odtworzenia.

## Historia zmian (skrót)

- 22.09.2025 — Usunięto cały system AI; projekt działa jako HvsH. Dokumentacja dostosowana.

—

Ostatnia aktualizacja: 22 września 2025
Autorzy: Zespół projektu
Wersja dokumentacji: 4.2
