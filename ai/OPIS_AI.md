# AI – opis modułów

Warstwa AI jest aktywna i używana przez `ai_launcher.py`.

## Struktura
- general/ – logika generała i dystrybucji PE.
- commander/ – logika dowódców i decyzji taktycznych.
- tokens/ – zachowania pojedynczych żetonów.
- logs/ – logi sesji AI.
- tests/ – testy jednostkowe AI.

## Punkty wejścia
- `ai_launcher.py` – konfiguracja AI/Human per gracz.
- `ai/__init__.py` – eksport klas AI.
