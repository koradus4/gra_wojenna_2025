import csv
import json

from ai.logs.human_logger import HumanActionLogger, PlayerSnapshot
from engine.action_refactored_clean import MoveAction
from engine.engine import GameEngine
from engine.player import Player


def _find_adjacent_destination(engine, token):
    start = (token.q, token.r)
    for neighbor in engine.board.neighbors(*start):
        tile = engine.board.get_tile(*neighbor)
        if not tile or getattr(tile, "move_mod", -1) < 0:
            continue
        if engine.board.is_occupied(*neighbor):
            continue
        return neighbor
    raise RuntimeError("Brak dostępnego pola do ruchu w teście")


def test_human_action_logger_writes_text_and_csv(tmp_path):
    logger = HumanActionLogger(log_dir=str(tmp_path))
    snapshot = PlayerSnapshot(
        player_type="HUMAN",
        player_id=7,
        nation="Polska",
        role="Dowódca",
        name="Testowy Gracz",
    )

    logger.log_action(
        snapshot,
        turn=3,
        action_type="move",
        summary="Testowy ruch",
        result="OK",
        context={"path_cost": 2, "extras": {"a": 1}},
    )

    text_dir = tmp_path / "text"
    csv_dir = tmp_path / "csv"

    text_files = list(text_dir.glob("*.log"))
    csv_files = list(csv_dir.glob("*.csv"))

    assert text_files, "Oczekiwano pliku tekstowego z logiem"
    assert csv_files, "Oczekiwano pliku CSV z logiem"

    text_content = text_files[0].read_text(encoding="utf-8")
    assert "Testowy ruch" in text_content
    assert "HUMAN" in text_content

    with open(csv_files[0], newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter=",")
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]
    assert row["action_type"] == "move"
    context_payload = json.loads(row["context"])
    assert context_payload["path_cost"] == 2
    assert context_payload["extras"]["a"] == 1


def test_game_engine_execute_action_logs_move(monkeypatch):
    captured = {}

    def fake_log_action(**kwargs):
        captured["call"] = kwargs

    monkeypatch.setattr("ai.logs.human_logger.log_human_action", fake_log_action)

    engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json",
        tokens_start_path="assets/start_tokens.json",
        seed=321,
    )

    token = next((t for t in engine.tokens if getattr(t, "owner", None)), None)
    assert token is not None, "Brak żetonu do przetestowania ruchu"

    owner_str = str(getattr(token, "owner", "")).strip()
    owner_id = None
    owner_nation = None
    if owner_str:
        try:
            owner_id = int(owner_str.split("(")[0].strip())
        except Exception:
            owner_id = 1
        if "(" in owner_str and ")" in owner_str:
            owner_nation = owner_str.split("(")[1].split(")")[0].strip()

    player = Player(owner_id or 1, owner_nation or "Polska", "Dowódca")
    player.name = "Tester"
    engine.players = [player]
    start_position = (token.q, token.r)
    destination = _find_adjacent_destination(engine, token)

    action = MoveAction(token.id, destination[0], destination[1])
    result = engine.execute_action(action, player=player)

    assert hasattr(result, "success") and result.success
    assert "call" in captured, "Logger powinien zostać wywołany"

    payload = captured["call"]
    assert payload["action_type"] == "move"
    context = payload["context"]
    assert context["token_id"] == token.id
    assert tuple(context["start_position"]) == (start_position[0], start_position[1])
    assert tuple(context["end_position"]) == (destination[0], destination[1])
    assert payload["summary"].startswith(token.id)
