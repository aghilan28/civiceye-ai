from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CivicModelSpec:
    model_type: str
    canonical_class: str
    department: str
    severity_weight: float
    default_threshold: float
    gpu_required: bool
    edge_compatible: bool


MODEL_CATALOG: dict[str, CivicModelSpec] = {
    "POTHOLE": CivicModelSpec("POTHOLE", "pothole", "ROADS", 0.72, 0.25, True, True),
    "ROAD_CRACK": CivicModelSpec("ROAD_CRACK", "road_crack", "ROADS", 0.58, 0.3, True, True),
    "FLOODING": CivicModelSpec("FLOODING", "flooding", "DRAINAGE", 0.94, 0.35, True, True),
    "GARBAGE_OVERFLOW": CivicModelSpec("GARBAGE_OVERFLOW", "garbage_overflow", "SMART_INFRASTRUCTURE", 0.44, 0.35, False, True),
    "DRAINAGE_BLOCKAGE": CivicModelSpec("DRAINAGE_BLOCKAGE", "drainage_blockage", "DRAINAGE", 0.8, 0.32, True, True),
    "FALLEN_TREE": CivicModelSpec("FALLEN_TREE", "fallen_tree", "ROADS", 0.88, 0.35, True, True),
    "STREETLIGHT_FAILURE": CivicModelSpec("STREETLIGHT_FAILURE", "damaged_streetlight", "UTILITIES", 0.5, 0.4, False, True),
    "TRAFFIC_SIGNAL_FAILURE": CivicModelSpec("TRAFFIC_SIGNAL_FAILURE", "traffic_signal_failure", "SMART_INFRASTRUCTURE", 0.82, 0.4, False, True),
    "ROAD_EROSION": CivicModelSpec("ROAD_EROSION", "road_erosion", "ROADS", 0.83, 0.32, True, True),
    "INFRASTRUCTURE_COLLAPSE": CivicModelSpec("INFRASTRUCTURE_COLLAPSE", "infrastructure_collapse_indicator", "ROADS", 1.0, 0.45, True, False),
    "ILLEGAL_DUMPING": CivicModelSpec("ILLEGAL_DUMPING", "illegal_dumping", "SMART_INFRASTRUCTURE", 0.47, 0.38, False, True),
    "LANE_DEGRADATION": CivicModelSpec("LANE_DEGRADATION", "lane_degradation", "ROADS", 0.66, 0.32, True, True),
    "ROAD_OBSTRUCTION": CivicModelSpec("ROAD_OBSTRUCTION", "road_obstruction", "ROADS", 0.9, 0.35, True, True),
    "MANHOLE_DAMAGE": CivicModelSpec("MANHOLE_DAMAGE", "manhole_damage", "DRAINAGE", 0.76, 0.35, True, True),
}


def supported_model_types() -> list[str]:
    return list(MODEL_CATALOG)


def model_spec(model_type: str) -> CivicModelSpec:
    return MODEL_CATALOG[model_type]
