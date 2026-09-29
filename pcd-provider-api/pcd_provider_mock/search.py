import json
import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import Address, Provider

DEFAULT_DATA_DIR = Path(__file__).parent / "data"
EARTH_RADIUS_MILES = 3958.8


def data_dir() -> Path:
    # Overridable so testers can mount their own provider set without a rebuild.
    return Path(os.environ.get("PCD_MOCK_DATA_DIR") or DEFAULT_DATA_DIR)


@lru_cache(maxsize=1)
def load_zip_centroids() -> dict[str, dict[str, Any]]:
    with open(data_dir() / "zip_centroids.json", encoding="utf-8") as fh:
        data: dict[str, dict[str, Any]] = json.load(fh)
    return data


@lru_cache(maxsize=1)
def load_providers() -> list[dict[str, Any]]:
    with open(data_dir() / "providers.json", encoding="utf-8") as fh:
        data: list[dict[str, Any]] = json.load(fh)
    return data


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def search_providers(zip_code: str, radius_miles: int, specialty: str,
                     plan_type: str) -> list[Provider] | None:
    """Providers within the radius, nearest first; None when the zip is unknown."""
    centre = load_zip_centroids().get(zip_code)
    if centre is None:
        return None

    matches: list[Provider] = []
    for row in load_providers():
        if row["specialty"].casefold() != specialty.casefold():
            continue
        if plan_type.casefold() not in (p.casefold() for p in row["plan_types"]):
            continue
        distance = haversine_miles(centre["lat"], centre["lon"], row["lat"], row["lon"])
        if distance > radius_miles:
            continue
        matches.append(Provider(
            pcd_id=row["pcd_id"],
            provider_name=row["provider_name"],
            practice_name=row["practice_name"],
            specialty=row["specialty"],
            address=Address(**row["address"]),
            distance_miles=round(distance, 1),
        ))
    matches.sort(key=lambda p: p.distance_miles)
    return matches
