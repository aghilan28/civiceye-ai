from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


@dataclass(frozen=True)
class GeoContext:
    latitude: float
    longitude: float
    timestamp: datetime
    road_name: str | None
    district: str | None
    city: str
    state: str
    postal_code: str | None
    municipality_id: str
    geohash: str
    route_segment_id: str | None
    source: str


def encode_geohash(latitude: float, longitude: float, precision: int = 9) -> str:
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    bits = [16, 8, 4, 2, 1]
    geohash = []
    bit = 0
    ch = 0
    even = True

    while len(geohash) < precision:
        if even:
            mid = sum(lon_interval) / 2
            if longitude > mid:
                ch |= bits[bit]
                lon_interval[0] = mid
            else:
                lon_interval[1] = mid
        else:
            mid = sum(lat_interval) / 2
            if latitude > mid:
                ch |= bits[bit]
                lat_interval[0] = mid
            else:
                lat_interval[1] = mid
        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash.append(_BASE32[ch])
            bit = 0
            ch = 0
    return "".join(geohash)


def normalize_geo_context(payload: dict[str, Any]) -> GeoContext:
    latitude = float(payload["latitude"])
    longitude = float(payload["longitude"])
    timestamp_value = payload.get("timestamp")
    timestamp = (
        datetime.fromisoformat(str(timestamp_value).replace("Z", "+00:00"))
        if timestamp_value
        else datetime.now(timezone.utc)
    )
    return GeoContext(
        latitude=latitude,
        longitude=longitude,
        timestamp=timestamp,
        road_name=payload.get("road_name") or payload.get("roadName"),
        district=payload.get("district"),
        city=str(payload.get("city") or ""),
        state=str(payload.get("state") or ""),
        postal_code=payload.get("postal_code") or payload.get("postalCode"),
        municipality_id=str(payload.get("municipality_id") or payload.get("municipalityId") or ""),
        geohash=str(payload.get("geohash") or encode_geohash(latitude, longitude)),
        route_segment_id=payload.get("route_segment_id") or payload.get("routeSegmentId"),
        source=str(payload.get("source") or "UPLOADED_METADATA"),
    )


def route_segment_key(geohash: str, road_name: str | None) -> str:
    road = (road_name or "unknown-road").strip().lower().replace(" ", "-")
    return f"seg_{geohash[:7]}_{road[:48]}"
