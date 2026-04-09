# Moduł AI – Kampania 1939

Moduł `ai/` dostarcza gracza komputerowego (AI) dla gry Kampania 1939.

## Struktura

```
ai/
├── __init__.py          # Eksport głównych klas
├── base_agent.py        # Klasa bazowa BaseAgent (ABC)
├── state_adapter.py     # Ekstrakcja stanu z GameEngine → struktury AI
├── evaluator.py         # Heurystyki i funkcje oceny (scoring)
├── tactical_agent.py    # Decyzje ruchu i walki (dowódca)
├── strategic_agent.py   # Priorytety key points, ekonomia, zakupy (generał)
├── decision_queue.py    # Kolejkowanie i filtrowanie akcji
├── memory/              # Logi i dane adaptacyjne (Faza 8)
└── README.md            # Ten plik
```

## Szybki start

```python
from ai import TacticalAgent, StrategicAgent
from ai.state_adapter import StateAdapter

adapter = StateAdapter()
state = adapter.extract(engine, player)

# Dowódca
agent = TacticalAgent(player_id=1, nation="Polska", difficulty="normal", seed=42)
actions = agent.decide(state)

# Generał
general_agent = StrategicAgent(player_id=0, nation="Polska")
directives = general_agent.decide(state)
```

## Plan wdrożenia (fazy)

| Faza | Zakres                         | Status     |
|------|--------------------------------|------------|
| 0    | Dokumentacja kontraktu         | ✅ gotowe  |
| 1    | Szkielet modułu                | ✅ gotowe  |
| 2    | Adapter stanu                  | ✅ gotowe  |
| 3    | Ruch taktyczny                 | ✅ szkielet|
| 4    | Walka selektywna               | ✅ szkielet|
| 5    | Strategia key points           | ✅ szkielet|
| 6    | Ekonomia / zakupy              | ⏳ stub    |
| 7    | Poziomy trudności              | ⏳ plan    |
| 8    | Logowanie decyzji              | ⏳ plan    |
| 9    | Adaptacja (opcjonalnie)        | ⏳ plan    |

## Zasady fair play

- Brak podejmowania akcji na podstawie niewidocznych wrogów.
- Brak modyfikacji punktów ruchu / paliwa poza systemem.
- Zakupy tylko przez publiczne API zakupów (`engine.purchase_unit`).
- Decyzje deterministyczne przy ustalonym `seed` (testowalność).
