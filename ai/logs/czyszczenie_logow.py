"""Proste narzędzie do czyszczenia logów AI w pakiecie `ai.logs`."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Iterable

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.session_manager import SESSION_ROOT

TOKENS_ROOT = PROJECT_ROOT / "assets" / "tokens"
START_TOKENS_PATH = PROJECT_ROOT / "assets" / "start_tokens.json"
TOKENS_INDEX_PATH = TOKENS_ROOT / "index.json"
PURCHASED_TOKENS_DIR = PROJECT_ROOT / "purchased_tokens"
TARGET_DIRS = [
    PACKAGE_ROOT / "commander" / "csv",
    PACKAGE_ROOT / "commander" / "text",
    PACKAGE_ROOT / "general" / "csv",
    PACKAGE_ROOT / "general" / "text",
    PACKAGE_ROOT / "general" / "raporty",
    PACKAGE_ROOT / "human" / "csv",
    PACKAGE_ROOT / "human" / "text",
    PACKAGE_ROOT / "human" / "raporty",
    PACKAGE_ROOT / "tokens" / "csv",
    PACKAGE_ROOT / "tokens" / "text",
    PACKAGE_ROOT / "tokens" / "raporty",
    PACKAGE_ROOT / "debug" / "csv",
    PACKAGE_ROOT / "debug" / "text",
]


def _relative_to_project(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _iter_log_files() -> list[Path]:
    files: list[Path] = []
    for directory in TARGET_DIRS:
        if directory.exists():
            files.extend(path for path in directory.rglob("*") if path.is_file())
    return files


def _iter_log_directories() -> Iterable[Path]:
    directories: list[Path] = []
    for directory in TARGET_DIRS:
        if directory.exists():
            directories.extend(
                path for path in directory.rglob("*") if path.is_dir()
            )
    return sorted(directories, key=lambda p: len(p.parts), reverse=True)


def _json_contains_nowy(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and str(item.get("id", "")).startswith("nowy_"):
                return True
    return False


def _strip_nowy_entries(path: Path, *, verbose: bool) -> int:
    if not path.exists():
        return 0

    relative = _relative_to_project(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        if verbose:
            print(f"⚠️ Nie udało się odczytać {relative}: {error}")
        return 0

    if not isinstance(data, list):
        return 0

    filtered = [item for item in data if not (
        isinstance(item, dict) and str(item.get("id", "")).startswith("nowy_")
    )]

    removed = len(data) - len(filtered)
    if removed:
        path.write_text(
            json.dumps(filtered, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        if verbose:
            print(f"✅ Usunięto {removed} wpisów nowy_* z {relative}")
    elif verbose:
        print(f"ℹ️ Brak wpisów nowy_* w {relative}")

    return removed


def _clean_nowe_dla_directories(*, verbose: bool) -> tuple[int, int]:
    if not TOKENS_ROOT.exists():
        return (0, 0)

    files_removed = 0
    dirs_removed = 0

    for folder in TOKENS_ROOT.glob("nowe_dla_*"):
        if not folder.is_dir():
            continue

        file_count = sum(1 for item in folder.rglob("*") if item.is_file())
        try:
            shutil.rmtree(folder)
            files_removed += file_count
            dirs_removed += 1
            if verbose:
                print(
                    f"✅ Usunięto katalog {folder.name} (plików: {file_count})"
                )
        except OSError as error:
            if verbose:
                print(f"⚠️ Nie można usunąć {folder}: {error}")

    return files_removed, dirs_removed


def _clean_aktualne_files(*, verbose: bool) -> int:
    aktualne_dir = TOKENS_ROOT / "aktualne"
    if not aktualne_dir.exists():
        return 0

    removed = 0
    for path in aktualne_dir.glob("nowy_*"):
        if not path.is_file():
            continue
        try:
            path.unlink()
            removed += 1
            if verbose:
                print(f"✅ Usunięto {path.name} z assets/tokens/aktualne/")
        except OSError as error:
            if verbose:
                print(f"⚠️ Nie można usunąć {path}: {error}")
    return removed


def _clean_purchased_tokens_dir(*, verbose: bool) -> tuple[int, int]:
    if not PURCHASED_TOKENS_DIR.exists():
        return (0, 0)

    files_removed = 0
    dirs_removed = 0

    for item in PURCHASED_TOKENS_DIR.iterdir():
        try:
            if item.is_file():
                item.unlink()
                files_removed += 1
                if verbose:
                    print(f"✅ Usunięto {item.name} z purchased_tokens/")
            elif item.is_dir():
                file_count = sum(1 for child in item.rglob("*") if child.is_file())
                shutil.rmtree(item)
                files_removed += file_count
                dirs_removed += 1
                if verbose:
                    print(
                        f"✅ Usunięto katalog {item.name} z purchased_tokens/ (plików: {file_count})"
                    )
        except OSError as error:
            if verbose:
                print(f"⚠️ Nie można usunąć {item}: {error}")

    return files_removed, dirs_removed


def _clean_purchased_token_assets(*, verbose: bool) -> dict[str, int]:
    stats = {
        "files_removed": 0,
        "dirs_removed": 0,
        "json_entries_removed": 0,
        "json_files_updated": 0,
    }

    stats["files_removed"] += _clean_aktualne_files(verbose=verbose)

    nowe_files_removed, nowe_dirs_removed = _clean_nowe_dla_directories(verbose=verbose)
    stats["files_removed"] += nowe_files_removed
    stats["dirs_removed"] += nowe_dirs_removed

    purchased_files_removed, purchased_dirs_removed = _clean_purchased_tokens_dir(verbose=verbose)
    stats["files_removed"] += purchased_files_removed
    stats["dirs_removed"] += purchased_dirs_removed

    index_removed = _strip_nowy_entries(TOKENS_INDEX_PATH, verbose=verbose)
    if index_removed:
        stats["json_entries_removed"] += index_removed
        stats["json_files_updated"] += 1

    start_removed = _strip_nowy_entries(START_TOKENS_PATH, verbose=verbose)
    if start_removed:
        stats["json_entries_removed"] += start_removed
        stats["json_files_updated"] += 1

    return stats


def _token_cleanup_required() -> bool:
    if not TOKENS_ROOT.exists():
        return PURCHASED_TOKENS_DIR.exists() and any(PURCHASED_TOKENS_DIR.iterdir())

    aktualne_dir = TOKENS_ROOT / "aktualne"
    if aktualne_dir.exists() and any(aktualne_dir.glob("nowy_*")):
        return True

    if any(folder for folder in TOKENS_ROOT.glob("nowe_dla_*") if folder.exists()):
        return True

    if PURCHASED_TOKENS_DIR.exists() and any(PURCHASED_TOKENS_DIR.iterdir()):
        return True

    if _json_contains_nowy(TOKENS_INDEX_PATH):
        return True

    if _json_contains_nowy(START_TOKENS_PATH):
        return True

    return False


def _confirm_prompt() -> bool:
    answer = input("Na pewno usunąć logi AI (commander/general/tokens/debug)? [t/N]: ").strip().lower()
    return answer in {"t", "tak", "y", "yes"}


def clean_logs(*, confirm: bool = True, verbose: bool = True) -> int:
    """Usuwa logi AI oraz resetuje zakupione żetony do stanu początkowego."""

    log_targets_exist = any(directory.exists() for directory in TARGET_DIRS)
    token_targets_exist = _token_cleanup_required()
    session_logs_dir = PROJECT_ROOT / SESSION_ROOT

    if not log_targets_exist and not token_targets_exist:
        if verbose:
            print("Brak logów AI ani zakupionych żetonów do usunięcia.")
        return 0

    if confirm and not _confirm_prompt():
        if verbose:
            print("Przerwano czyszczenie logów.")
        return 0

    removed_files = 0
    removed_dirs = 0

    if log_targets_exist:
        files = _iter_log_files()
        directories = list(_iter_log_directories())

        if not files and not directories and verbose:
            print("Logi AI są już puste.")

        for path in files:
            try:
                path.unlink()
                removed_files += 1
                if verbose:
                    print(f"✅ Usunięto: {path.relative_to(PACKAGE_ROOT)}")
            except FileNotFoundError:
                continue
            except PermissionError as error:
                if verbose:
                    print(f"⚠️ Brak uprawnień do usunięcia {path}: {error}")
            except OSError as error:
                if verbose:
                    print(f"⚠️ Błąd podczas usuwania {path}: {error}")

        for directory in directories:
            try:
                if not any(directory.iterdir()):
                    directory.rmdir()
                    removed_dirs += 1
                    if verbose:
                        print(
                            f"✅ Usunięto pusty katalog: {directory.relative_to(PACKAGE_ROOT)}"
                        )
            except OSError as error:
                if verbose:
                    print(f"⚠️ Nie można usunąć katalogu {directory}: {error}")
    elif verbose:
        print("ℹ️ Brak katalogów logów AI – pomijam czyszczenie logów.")

    token_stats = _clean_purchased_token_assets(verbose=verbose)

    total_files = removed_files + token_stats["files_removed"]
    total_dirs = removed_dirs + token_stats["dirs_removed"]
    json_entries_removed = token_stats["json_entries_removed"]
    logs_dir_removed = False

    if session_logs_dir.exists():
        try:
            shutil.rmtree(session_logs_dir)
            logs_dir_removed = True
            if verbose:
                print("✅ Usunięto katalog ai/logs/sessions (sesje)")
        except OSError as error:
            if verbose:
                print(f"⚠️ Nie można usunąć katalogu ai/logs/sessions: {error}")

    if verbose:
        summary_parts: list[str] = []
        summary_parts.append(f"pliki: {total_files}")
        if total_dirs:
            summary_parts.append(f"katalogi: {total_dirs}")
        if json_entries_removed:
            summary_parts.append(f"wpisy JSON: {json_entries_removed}")
        if logs_dir_removed:
            summary_parts.append("logs/: usunięto")
        print("Podsumowanie czyszczenia -> " + ", ".join(summary_parts))

    return total_files + token_stats["json_files_updated"]


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Czyści katalog logs/ całkowicie.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Nie pytaj o potwierdzenie (przydatne w automatyzacji).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Alias dla --yes (zachowana kompatybilność ze starszymi skryptami).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Nie wypisuj szczegółowych komunikatów.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_arguments(argv)
    auto_confirm = args.yes or args.all
    clean_logs(confirm=not auto_confirm, verbose=not args.quiet)

if __name__ == "__main__":
    main()
