import math
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "edytory" / "map_editor_prototyp.py"

spec = importlib.util.spec_from_file_location("map_editor_prototyp", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # type: ignore[arg-type]

EDGE_BLEND_PROFILES = module.EDGE_BLEND_PROFILES
mix_hex_colors = module.mix_hex_colors

def simulate_bleed():
    grid_size = 8
    local_pixels = [["#2ecc71" for _ in range(grid_size)] for _ in range(grid_size)]
    neighbor_pixels = [["#1f3a93" for _ in range(grid_size)] for _ in range(grid_size)]

    band_mask = [[False] * grid_size for _ in range(grid_size)]
    band_distance = [[None] * grid_size for _ in range(grid_size)]
    max_distance = 3
    for row in range(grid_size):
        for col in range(4, grid_size):
            band_mask[row][col] = True
            band_distance[row][col] = col - 4

    neighbor_distance = [[None] * grid_size for _ in range(grid_size)]
    neighbor_max_distance = 3
    for row in range(grid_size):
        for col in range(4):
            neighbor_distance[row][col] = col

    source_row = [[None] * grid_size for _ in range(grid_size)]
    source_col = [[None] * grid_size for _ in range(grid_size)]
    for row in range(grid_size):
        for col in range(4):
            source_row[row][col] = row
            source_col[row][col] = 4 + col

    strength = 65
    strength_factor = strength / 100.0
    profile_meta = EDGE_BLEND_PROFILES["smooth"]
    exponent = profile_meta["exponent"]
    bleed_depth = 4
    neighbor_effective_max = min(neighbor_max_distance, bleed_depth - 1)

    # local pass
    for row in range(grid_size):
        for col in range(grid_size):
            if not band_mask[row][col]:
                continue
            distance_value = band_distance[row][col]
            if distance_value is None:
                continue
            ratio = 0.0 if max_distance <= 0 else float(distance_value) / float(max_distance)
            weight = strength_factor * (1.0 - math.pow(ratio, exponent))
            if weight <= 0.0:
                continue
            neighbor_row = row
            neighbor_col = col - 4
            neighbor_color = None
            if 0 <= neighbor_row < grid_size and 0 <= neighbor_col < grid_size:
                neighbor_color = neighbor_pixels[neighbor_row][neighbor_col]
            current_color = local_pixels[row][col]
            local_pixels[row][col] = mix_hex_colors(current_color, neighbor_color, weight)

    if bleed_depth > 0:
        for nr in range(grid_size):
            for nc in range(grid_size):
                distance_value = neighbor_distance[nr][nc]
                if distance_value is None or distance_value >= bleed_depth:
                    continue
                if neighbor_effective_max <= 0:
                    neighbor_weight = strength_factor
                else:
                    neighbor_ratio = 0.0 if neighbor_effective_max <= 0 else float(distance_value) / float(neighbor_effective_max)
                    neighbor_ratio = max(0.0, min(1.0, neighbor_ratio))
                    neighbor_weight = strength_factor * (1.0 - math.pow(neighbor_ratio, exponent))
                if neighbor_weight <= 0.0:
                    continue
                src_row = source_row[nr][nc]
                src_col = source_col[nr][nc]
                if src_row is None or src_col is None:
                    continue
                source_color = local_pixels[src_row][src_col]
                neighbor_color = neighbor_pixels[nr][nc]
                neighbor_pixels[nr][nc] = mix_hex_colors(neighbor_color, source_color, neighbor_weight)

    return local_pixels, neighbor_pixels


def main():
    local_pixels, neighbor_pixels = simulate_bleed()
    sample_row = 3
    print("Sample neighbor row after bleed:")
    for col in range(4):
        print(col, neighbor_pixels[sample_row][col])

if __name__ == "__main__":
    main()
