"""
TEST INTEGRACYJNY (REAL GAME): Graduowana widoczność na prawdziwej mapie
Uruchamia prawdziwy GameEngine, umieszcza dwa żetony i pokazuje różnice
w ujawnianych informacjach zależnie od odległości (1..N) oraz mapowe symbole/opacity.

Wykorzystuje realne komponenty:
- engine.engine.GameEngine (mapa + heksy),
- engine.action_refactored_clean.VisionService (detekcja + widoczność),
- engine.engine.clear_temp_visibility (zerowanie tymczasowej widoczności),
- gui.detection_display (mapowe symbole, statusy, pola panelu),
- engine.detection_filter.apply_detection_filter (filtrowanie danych przeciwnika).
"""

from typing import List, Tuple, Set


def _pick_central_free_tile(engine) -> Tuple[int, int]:
    """Znajdź wolny heks z pełnym sąsiedztwem (6 sąsiadów istnieje w mapie).
    Jeśli nie znajdzie idealnego, zwróci pierwszy wolny heks z mapy.
    """
    occupied = {(t.q, t.r) for t in engine.tokens if t.q is not None and t.r is not None}
    for key in engine.board.terrain.keys():
        q, r = map(int, key.split(","))
        if (q, r) in occupied:
            continue
        neighs = engine.board.neighbors(q, r)
        if all(engine.board.get_tile(nq, nr) is not None for nq, nr in neighs):
            return q, r
    # fallback: pierwszy wolny heks
    for key in engine.board.terrain.keys():
        q, r = map(int, key.split(","))
        if (q, r) not in occupied:
            return q, r
    # ostatecznie: (0,0) (jeśli mapy by brakło – defensywnie)
    return 0, 0


def _ring_positions(board, center: Tuple[int, int], radius: int) -> List[Tuple[int, int]]:
    """Zwraca listę heksów w dokładnie zadanym dystansie (axial distance == radius),
    które istnieją na mapie (board.get_tile != None)."""
    cq, cr = center
    results = []
    for key in board.terrain.keys():
        q, r = map(int, key.split(","))
        if board.hex_distance((cq, cr), (q, r)) == radius:
            results.append((q, r))
    return results


def test_visibility_real_game_scenario():
    print("🧭 REAL-GAME TEST: Graduowana widoczność na prawdziwej mapie")
    print("=" * 80)

    # Importy dopiero tutaj, żeby test startował nawet jeśli ścieżki PYTHONPATH się różnią
    from engine.engine import GameEngine, clear_temp_visibility
    from engine.player import Player
    from engine.token import Token
    from engine.action_refactored_clean import VisionService
    from engine.detection_filter import apply_detection_filter
    from gui.detection_display import (
        get_display_info_for_enemy,
        get_map_display_symbol,
        format_detection_status,
        get_info_panel_content,
    )

    # 1) Prawdziwy silnik + mapa + tokeny
    engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json",
        tokens_start_path="assets/start_tokens.json",
        seed=123,
        read_only=True,
    )

    # 2) Dwóch graczy HvsH (bez AI) – role istotne dla widoczności w engine
    pl = Player(1, "Polska", "Dowódca")
    de = Player(5, "Niemcy", "Dowódca")
    engine.players = [pl, de]

    # 3) Wybierz wolny heks i postaw obserwatora (Polska)
    obs_q, obs_r = _pick_central_free_tile(engine)
    observer = Token(
        id="TEST_OBSERVER_PL",
        owner=f"{pl.id} ({pl.nation})",
        stats={
            "move": 6,
            "combat_value": 3,
            "defense_value": 3,
            "maintenance": 1,
            "price": 0,
            "sight": 4,
            "unitType": "P",
            "unitSize": "Pluton",
            "label": "Zwiad testowy",
            "unit_full_name": "Zwiad (test)",
            "attack": {"value": 2, "range": 1},
            "nation": "Polska",
        },
        q=obs_q,
        r=obs_r,
    )

    # 4) Wróg (Niemcy) – obiekt do obserwacji
    enemy = Token(
        id="TEST_ENEMY_DE",
        owner=f"{de.id} ({de.nation})",
        stats={
            "move": 5,
            "combat_value": 7,
            "defense_value": 5,
            "maintenance": 2,
            "price": 0,
            "sight": 3,
            "unitType": "TL",
            "unitSize": "Pluton",
            "label": "Czołg (test)",
            "unit_full_name": "Panzer (test)",
            "attack": {"value": 8, "range": 2},
            "nation": "Niemcy",
        },
        q=None,
        r=None,
    )

    # Dodaj do silnika i podłącz do planszy
    engine.tokens.append(observer)
    engine.tokens.append(enemy)
    engine.board.set_tokens(engine.tokens)

    print(f"🎯 Obserwator: {observer.id} na ({observer.q}, {observer.r}), sight={observer.stats.get('sight', 0)}")
    print(f"🎯 Wróg: {enemy.id} (CV={enemy.stats.get('combat_value')}) – będzie ustawiany w różnych odległościach")

    max_sight = observer.stats.get("sight", 4)
    # Zbuduj scenariusze dla odległości 1..(max_sight+1), gdzie ostatni jest poza zasięgiem
    distances = list(range(1, max_sight + 2))

    for dist in distances:
        # Znajdź miejsce w dokładnej odległości od obserwatora
        candidates = _ring_positions(engine.board, (observer.q, observer.r), dist)
        # Wybierz pierwszy wolny
        placed = False
        for (eq, er) in candidates:
            occupied_now = any(t.q == eq and t.r == er for t in engine.tokens if t is not enemy)
            if not occupied_now:
                enemy.set_position(eq, er)
                placed = True
                break
        if not placed:
            # Jeśli brak idealnego kandydata, pomiń ten dystans
            print(f"⚠️  Brak wolnego heksa dokładnie w odległości {dist} – pomijam")
            continue

        # Wyczyść tymczasową widoczność i przelicz na podstawie obserwatora
        clear_temp_visibility(engine.players)
        # Przygotuj strukturę temp na graczu PL (na wszelki wypadek)
        if not hasattr(pl, 'temp_visible_hexes'):
            pl.temp_visible_hexes = set()
        if not hasattr(pl, 'temp_visible_tokens'):
            pl.temp_visible_tokens = set()
        if not hasattr(pl, 'temp_visible_token_data'):
            pl.temp_visible_token_data = {}

        # Zbuduj pseudo-ścieżkę (stanie w miejscu) i aktualizuj widzialność pozycją obserwatora
        VisionService.update_player_vision(
            engine=engine,
            player=pl,
            token=observer,
            path=[(observer.q, observer.r)],
            final_pos=(observer.q, observer.r),
        )

        # Wylicz dystans i detection_level według serwisu
        real_distance = engine.board.hex_distance((observer.q, observer.r), (enemy.q, enemy.r))
        detection_level = VisionService.calculate_detection_level(real_distance, max_sight)

        print("-" * 80)
        print(f"📡 Dystans: {real_distance} (target poza zasięgiem sight={max_sight} => 0.0)" )
        print(f"🔍 Detection level: {detection_level:.2f}")

        # Filtruj informacje o wrogu
        filtered = apply_detection_filter(enemy, detection_level)
        print("📋 Filtered info:")
        print(f"  ID: {filtered['id']}")
        print(f"  CV: {filtered['combat_value']}")
        print(f"  Quality: {filtered['info_quality']}")

        # GUI mapping
        display_info = get_display_info_for_enemy(enemy, detection_level)
        map_symbol = get_map_display_symbol(enemy, detection_level)
        status = format_detection_status(detection_level)
        panel = get_info_panel_content(enemy, detection_level)

        print("🖥️  GUI:")
        print(f"  Nazwa: {display_info['display_name']}")
        print(f"  Status: {status}")
        print(f"  Symbol: {map_symbol['symbol']} (opacity: {map_symbol['opacity']})")
        print(f"  Tooltip: {display_info['tooltip']}")
        print(f"  Panel pól: {len(panel['fields'])}")

    print("=" * 80)
    print("✅ KONIEC: Real-game test graduowanej widoczności (wizualny raport powyżej)")
