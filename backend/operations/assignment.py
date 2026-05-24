from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DepartmentLoad:
    id: str
    type: str
    district_codes: list[str]
    open_incidents: int
    active_crews: int


def assign_department(
    *,
    severity: str,
    district_code: str | None,
    departments: list[DepartmentLoad],
) -> DepartmentLoad | None:
    if not departments:
        return None

    def score(department: DepartmentLoad) -> float:
        geo_match = 0.0 if district_code and district_code in department.district_codes else 0.22
        load = department.open_incidents / max(department.active_crews, 1)
        sla_pressure = {"CRITICAL": -0.35, "HIGH": -0.18, "MEDIUM": 0.0, "LOW": 0.08}.get(severity, 0.0)
        return load + geo_match + sla_pressure

    return sorted(departments, key=score)[0]
