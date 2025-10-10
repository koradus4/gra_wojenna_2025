"""Helpery do generowania blueprintów i assetów żetonów dla AI i GUI."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from PIL import Image, ImageDraw, ImageFont

from balance.model import build_unit_names, compute_token
from edytory.token_editor_prototyp import create_flag_background

__all__ = [
    "TokenAssetBundle",
    "generate_token_assets",
]

_DEFAULT_IMAGE_SIZE = (240, 240)
_PREVIEW_IMAGE_SIZE = (120, 120)


@dataclass
class TokenAssetBundle:
    """Opis wygenerowanych assetów."""

    token_id: str
    folder: Path
    json_path: Path
    image_path: Path
    blueprint: dict
    cost: int


def _safe_filename(value: str) -> str:
    value = value or "token"
    value = value.strip()
    value = re.sub(r"[<>:\\/|?*]", "_", value)
    if len(value) > 64:
        value = value[:64]
    return value


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    line = words[0]
    for word in words[1:]:
        candidate = f"{line} {word}" if line else word
        if draw.textlength(candidate, font=font) <= max_width:
            line = candidate
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def _render_token_image(destination: Path, nation: str, unit_type: str, unit_size: str) -> None:
    width, height = _DEFAULT_IMAGE_SIZE
    token_img = create_flag_background(nation, width, height)
    draw = ImageDraw.Draw(token_img)
    draw.rectangle([0, 0, width, height], outline="black", width=6)

    unit_labels = {
        "P": "Piechota",
        "K": "Kawaleria",
        "R": "Zwiad",
        "TC": "Czołg ciężki",
        "TŚ": "Czołg średni",
        "TL": "Czołg lekki",
        "TS": "Sam. pancerny",
        "AC": "Artyleria ciężka",
        "AL": "Artyleria lekka",
        "AP": "Artyleria plot",
        "Z": "Zaopatrzenie ⭐ PE",
        "D": "Dowództwo",
        "G": "Generał",
    }
    unit_type_full = unit_labels.get(unit_type, unit_type)
    unit_symbol = {"Pluton": "***", "Kompania": "I", "Batalion": "II"}.get(unit_size, "")

    try:
        font_type = ImageFont.truetype("arialbd.ttf", 38)
        font_size = ImageFont.truetype("arial.ttf", 22)
        font_symbol = ImageFont.truetype("arialbd.ttf", 36)
    except Exception:
        font_type = font_size = font_symbol = ImageFont.load_default()

    margin = 12

    text_colors = {
        "Polska": "black",
        "Niemcy": "blue",
        "Wielka Brytania": "black",
        "Japonia": "black",
        "Stany Zjednoczone": "black",
        "Francja": "black",
        "Związek Radziecki": "white",
    }
    text_color = text_colors.get(nation, "black")

    max_text_width = int(width * 0.9)
    type_lines = _wrap_text(draw, unit_type_full, font_type, max_text_width)

    total_type_height = sum(draw.textbbox((0, 0), line, font=font_type)[3] - draw.textbbox((0, 0), line, font=font_type)[1] for line in type_lines)
    if type_lines:
        total_type_height += (len(type_lines) - 1) * 4

    bbox_size = draw.textbbox((0, 0), unit_size, font=font_size)
    bbox_symbol = draw.textbbox((0, 0), unit_symbol, font=font_symbol)

    size_height = bbox_size[3] - bbox_size[1]
    symbol_height = bbox_symbol[3] - bbox_symbol[1]

    gap_type_to_size = margin * 2
    gap_size_to_symbol = 4
    total_height = total_type_height + gap_type_to_size + size_height + gap_size_to_symbol + symbol_height
    y = (height - total_height) // 2

    for line in type_lines:
        bbox = draw.textbbox((0, 0), line, font=font_type)
        x = (width - (bbox[2] - bbox[0])) / 2
        draw.text((x, y), line, fill=text_color, font=font_type)
        y += bbox[3] - bbox[1] + 4
    y += gap_type_to_size - 4

    bbox_size = draw.textbbox((0, 0), unit_size, font=font_size)
    x_size = (width - (bbox_size[2] - bbox_size[0])) / 2
    draw.text((x_size, y), unit_size, fill=text_color, font=font_size)
    y += bbox_size[3] - bbox_size[1] + gap_size_to_symbol

    bbox_symbol = draw.textbbox((0, 0), unit_symbol, font=font_symbol)
    x_symbol = (width - (bbox_symbol[2] - bbox_symbol[0])) / 2
    draw.text((x_symbol, y), unit_symbol, fill=text_color, font=font_symbol)

    token_img.save(destination)


def _ensure_support_list(supports: Optional[Iterable[str]]) -> list[str]:
    if not supports:
        return []
    return [str(value) for value in supports]


def generate_token_assets(
    *,
    commander_id: int | str,
    nation: str,
    unit_type: str,
    unit_size: str,
    supports: Optional[Iterable[str]] = None,
    quality: str = "standard",
    base_folder: Path | None = None,
    timestamp: Optional[datetime] = None,
) -> TokenAssetBundle:
    """Tworzy folder nowego żetonu wraz z token.json i token.png."""

    supports_list = _ensure_support_list(supports)
    stats = compute_token(unit_type, unit_size, nation, supports_list, quality=quality)
    names = build_unit_names(nation, unit_type, unit_size)

    commander_id = str(commander_id)
    clean_label = _safe_filename(names["label"])
    ts = (timestamp or datetime.utcnow()).strftime("%Y%m%d%H%M%S")

    token_id = f"nowy_{unit_type}_{unit_size}__{commander_id}_{clean_label}_{ts}"

    tokens_root = Path(base_folder or Path("assets") / "tokens")
    target_folder = tokens_root / f"nowe_dla_{commander_id}" / token_id
    target_folder.mkdir(parents=True, exist_ok=True)

    image_rel_path = (target_folder / "token.png").as_posix()
    blueprint = {
        "id": token_id,
        "nation": nation,
        "unitType": unit_type,
        "unitSize": unit_size,
        "shape": "prostokąt",
        "label": names["label"],
        "unit_full_name": names["unit_full_name"],
        "move": stats.movement,
        "attack": {"range": stats.attack_range, "value": stats.attack_value},
        "combat_value": stats.combat_value,
        "defense_value": stats.defense_value,
        "maintenance": stats.maintenance,
        "price": stats.total_cost,
        "sight": stats.sight,
        "support_upgrades": supports_list,
        "image": image_rel_path,
        "w": _DEFAULT_IMAGE_SIZE[0],
        "h": _DEFAULT_IMAGE_SIZE[1],
        "quality": quality,
    }

    json_path = target_folder / "token.json"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(blueprint, handle, indent=2, ensure_ascii=False)

    image_path = target_folder / "token.png"
    _render_token_image(image_path, nation, unit_type, unit_size)

    preview_path = target_folder / "token_preview.png"
    try:
        preview = Image.open(image_path).resize(_PREVIEW_IMAGE_SIZE, Image.LANCZOS)
        preview.save(preview_path)
    except Exception:
        preview_path = None

    return TokenAssetBundle(
        token_id=token_id,
        folder=target_folder,
        json_path=json_path,
        image_path=image_path,
        blueprint=blueprint,
        cost=stats.total_cost,
    )
