"""Uproszczony reset startowych żetonów.

Skrypt usuwa wszystkie aktualne zasoby z folderu ``assets/tokens`` (łącznie z
indeksem), czyści ``assets/start_tokens.json`` oraz usuwa powiązania żetonów z
``data/map_data.json``. Działa bez dodatkowych opcji – wystarczy go uruchomić.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"

START_TOKENS_FILE = ASSETS_DIR / "start_tokens.json"
MAP_DATA_FILE = DATA_DIR / "map_data.json"
TOKENS_DIR = ASSETS_DIR / "tokens"
TOKENS_INDEX_FILE = TOKENS_DIR / "index.json"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def reset_start_tokens() -> bool:
    try:
        START_TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
        START_TOKENS_FILE.write_text("[]", encoding="utf-8")
        print(f"✅ Wyczyszczono {_rel(START_TOKENS_FILE)}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Nie udało się zapisać {_rel(START_TOKENS_FILE)}: {exc}")
        return False


def clear_map_tokens() -> bool:
    if not MAP_DATA_FILE.exists():
        print(f"ℹ️ Brak {_rel(MAP_DATA_FILE)} – pomijam czyszczenie mapy")
        return True

    try:
        data = json.loads(MAP_DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"❌ Nie udało się odczytać {_rel(MAP_DATA_FILE)} (błędny JSON): {exc}")
        return False

    removed = 0
    terrain = data.get("terrain")
    if isinstance(terrain, dict):
        for info in terrain.values():
            if isinstance(info, dict) and "token" in info:
                info.pop("token", None)
                removed += 1

    if removed:
        try:
            MAP_DATA_FILE.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"✅ Usunięto {removed} wpisów żetonów z {_rel(MAP_DATA_FILE)}")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Nie udało się zapisać {_rel(MAP_DATA_FILE)}: {exc}")
            return False
    else:
        print(f"ℹ️ {_rel(MAP_DATA_FILE)} nie zawierało przypisanych żetonów")

    return True


def purge_tokens_dir() -> bool:
    if TOKENS_DIR.exists():
        try:
            shutil.rmtree(TOKENS_DIR)
            print(f"✅ Usunięto katalog {_rel(TOKENS_DIR)}")
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Nie udało się usunąć {_rel(TOKENS_DIR)}: {exc}")
            return False
    else:
        print(f"ℹ️ {_rel(TOKENS_DIR)} nie istnieje – utworzę pusty katalog")

    try:
        TOKENS_DIR.mkdir(parents=True, exist_ok=True)
        TOKENS_INDEX_FILE.write_text("[]", encoding="utf-8")
        print(f"✅ Utworzono pusty {_rel(TOKENS_INDEX_FILE)}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Nie udało się odtworzyć {_rel(TOKENS_INDEX_FILE)}: {exc}")
        return False


def main() -> int:
    print("🧹 Reset startowych żetonów – wersja uproszczona")

    ok = True
    if not purge_tokens_dir():
        ok = False
    if not reset_start_tokens():
        ok = False
    if not clear_map_tokens():
        ok = False

    if ok:
        print("🏁 Gotowe – wszystkie rozmieszczone żetony zostały usunięte")
        return 0

    print("❌ Reset żetonów zakończył się z błędami")
    return 1


if __name__ == "__main__":
    sys.exit(main())
