"""Distance helpers and known neighborhood centers."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

# Fallback only -- used if data/neighborhoods.json is missing or unreadable.
# The checked coordinates (with their source links) live in that file; see
# load_areas() below and PREP-NEXT-WEEK.md for how they were verified.
_FALLBACK_AREAS = {
    "downtown san jose": (37.3382, -121.8863),
    "sjsu": (37.3352, -121.8811),
    "willow glen": (37.3046, -121.8982),
    "almaden": (37.2203, -121.8654),
    "cambrian": (37.2583, -121.9204),
    "evergreen": (37.3096, -121.8111),
    "santa clara": (37.3541, -121.9552),
    "sunnyvale": (37.3715, -122.0375),
    "campbell": (37.2872, -121.9500),
    "milpitas": (37.4323, -121.8996),
}


def load_areas(path: Optional[str] = None) -> dict[str, tuple[float, float]]:
    """Named-area centers a user can pick instead of exact coordinates.

    Reads data/neighborhoods.json (checked addresses with source links); if
    that file is missing, unreadable, or empty, falls back to the built-in
    table above rather than crashing -- same "bad data degrades, never
    crashes" rule the rest of this engine follows. Defaults to
    data/neighborhoods.json next to the project root (not the current
    working directory), so it loads the same way whether the engine is run
    from its own folder or launched from somewhere else.
    """
    if path is None:
        path = str(Path(__file__).resolve().parent.parent / "data" / "neighborhoods.json")
    p = Path(path)
    if p.exists():
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            areas = {
                str(a["name"]).lower(): (float(a["latitude"]), float(a["longitude"]))
                for a in raw.get("areas", [])
                if "name" in a and "latitude" in a and "longitude" in a
            }
            if areas:
                return areas
        except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError):
            pass
    return dict(_FALLBACK_AREAS)


AREAS = load_areas()


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_venues(path: str) -> dict[str, tuple[float, float]]:
    """Read the venue fallback table: {lowercase name or address text: {lat, lon}}."""
    import json
    from pathlib import Path

    p = Path(path)
    if not p.exists():
        return {}
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {k.lower(): (v["lat"], v["lon"]) for k, v in raw.items()
            if isinstance(v, dict) and "lat" in v and "lon" in v}


def fill_coordinates(events, venues: dict[str, tuple[float, float]]) -> int:
    """Give coordinate-less in-person events a location from the venue table. Returns count filled."""
    filled = 0
    for ev in events:
        if ev.lat is not None and ev.lon is not None:
            continue
        text = f"{ev.venue_name} {ev.address}".lower()
        for key, (lat, lon) in venues.items():
            if key in text:
                ev.lat, ev.lon = lat, lon
                filled += 1
                break
    return filled


def resolve_point(area: Optional[str], lat: Optional[float], lon: Optional[float]):
    """Return (lat, lon) from explicit coordinates or a named area."""
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    if area and area.lower() in AREAS:
        return AREAS[area.lower()]
    return None
