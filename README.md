# Kampania 1939 - Gra Human vs Human

## Opis
Strategiczna gra turowa osadzona w realiach września 1939 roku. Czysta gra dla ludzi bez elementów AI.

## Wymagania
- Python 3.8+
- Tkinter (zazwyczaj dołączony do Python)
- Pillow
- NumPy

## Instalacja
```bash
pip install -r requirements.txt
```

## Uruchomienie
```bash
python main.py
```

lub alternatywnie:
```bash
python main_alternative.py
```

## Struktura Gry
- **Gracze**: Do 6 graczy (3 polscy + 3 niemieccy)
- **Role**: Generał, Dowódca 1, Dowódca 2 dla każdej strony
- **Tryb**: Human vs Human (wszyscy gracze to ludzie)

## Podstawowe Elementy
- `/engine/` - Silnik gry, mechaniki
- `/gui/` - Interfejs użytkownika
- `/core/` - Logika biznesowa (ekonomia, tury, zwycięstwo)
- `/assets/` - Zasoby graficzne i dane
- `/data/` - Dane map i konfiguracji

## Rozgrywka
1. Uruchom grę
2. Wybierz nacje i czasy dla graczy na ekranie startowym
3. Każdy gracz wykonuje swoją turę zgodnie z rolą:
   - **Generał**: Zarządza ekonomią, strategią
   - **Dowódca**: Kieruje jednostkami w terenie

Gra została oczyszczona ze wszystkich elementów AI i jest gotowa do gry human vs human.
