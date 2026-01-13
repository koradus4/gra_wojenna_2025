"""Wspólne reguły semantyki dla generatorów heksów.

Cel: te same ograniczenia/"realizm" mają działać w Hex Inspectorze, Map Editorze
oraz w każdym innym miejscu, które woła generatory.

Ta warstwa NIE zmienia generatorów (renderingu). Normalizuje jedynie opcje,
żeby unikać oczywiście nielogicznych lub problematycznych kombinacji.
"""

from __future__ import annotations

from dataclasses import replace
from typing import List, Tuple

from generate_road_hex_tile import ROAD_WIDTH_PRESETS, SIDE_OPPOSITE as ROAD_SIDE_OPPOSITE, RoadOptions
from generate_railway_hex_tile import RailwayOptions


def normalize_road_options(options: RoadOptions) -> Tuple[RoadOptions, List[str]]:
    notes: List[str] = []

    width = options.width

    # Usuń/zdeduplikuj odnogi, które nie mają sensu.
    crossroads_in = list(options.crossroads) if options.crossroads else []
    crossroads_out: List[str] = []
    for side in crossroads_in:
        if side in (options.entry_side, options.exit_side):
            continue
        if side not in crossroads_out:
            crossroads_out.append(side)

    if crossroads_out != crossroads_in:
        notes.append("crossroads: usunięto duplikaty lub entry/exit")

    is_straight = ROAD_SIDE_OPPOSITE.get(options.entry_side) == options.exit_side
    is_junction = bool(crossroads_out)

    # Semantyka: 'piaszczysta' + 'bardzo_szeroka' wygląda jak plama.
    if options.road_type == "piaszczysta" and width == "bardzo_szeroka":
        fallback = "szeroka" if "szeroka" in ROAD_WIDTH_PRESETS else "średnia"
        width = fallback
        notes.append("piaszczysta: zdegradowano width z 'bardzo_szeroka'")

    # Semantyka: 'bardzo_szeroka' tylko dla prostej bez skrzyżowań.
    if width == "bardzo_szeroka" and (is_junction or not is_straight):
        fallback = "szeroka" if "szeroka" in ROAD_WIDTH_PRESETS else "średnia"
        if fallback != width:
            width = fallback
            notes.append("width: zdegradowano 'bardzo_szeroka' (tylko prosta bez crossroads)")

    crossroads_norm = crossroads_out or None

    if width == options.width and crossroads_norm == options.crossroads:
        return options, notes

    return replace(options, width=width, crossroads=crossroads_norm), notes


def normalize_railway_options(options: RailwayOptions) -> Tuple[RailwayOptions, List[str]]:
    notes: List[str] = []

    junctions_in = list(options.junctions) if options.junctions else []
    junctions_out: List[str] = []
    for side in junctions_in:
        if side in (options.entry_side, options.exit_side):
            continue
        if side not in junctions_out:
            junctions_out.append(side)

    if junctions_out != junctions_in:
        notes.append("junctions: usunięto duplikaty lub entry/exit")

    junction_double = bool(options.junction_double_track)
    railway_type_lower = str(options.railway_type).lower()

    # Jednotorowy: brak sensu dla 'double track' na rozjazdach, max 1 rozjazd.
    if "jednot" in railway_type_lower:
        if junction_double:
            junction_double = False
            notes.append("jednotorowy: wyłączono junction_double_track")
        if len(junctions_out) > 1:
            junctions_out = junctions_out[:1]
            notes.append("jednotorowy: ograniczono junctions do 1")

    # Ogólna zasada: wiele rozjazdów bez double-track zwykle wygląda źle.
    if len(junctions_out) > 1 and not junction_double:
        junctions_out = junctions_out[:1]
        notes.append("junctions: ograniczono do 1 (bez junction_double_track)")

    if junctions_out == junctions_in and junction_double == bool(options.junction_double_track):
        return options, notes

    return replace(options, junctions=junctions_out, junction_double_track=junction_double), notes
