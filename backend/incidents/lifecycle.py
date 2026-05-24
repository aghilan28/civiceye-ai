from __future__ import annotations


INCIDENT_TRANSITIONS: dict[str, set[str]] = {
    "DETECTED": {"VERIFIED", "REOPENED"},
    "VERIFIED": {"ASSIGNED", "REOPENED"},
    "ASSIGNED": {"IN_PROGRESS", "REOPENED"},
    "IN_PROGRESS": {"TEMPORARY_FIX", "COMPLETED", "REOPENED"},
    "TEMPORARY_FIX": {"IN_PROGRESS", "COMPLETED", "REOPENED"},
    "COMPLETED": {"REOPENED"},
    "REOPENED": {"VERIFIED", "ASSIGNED", "IN_PROGRESS"},
}


def can_transition(from_status: str, to_status: str) -> bool:
    return to_status in INCIDENT_TRANSITIONS.get(from_status, set())


def assert_transition(from_status: str, to_status: str) -> None:
    if not can_transition(from_status, to_status):
        raise ValueError(f"Invalid incident transition: {from_status} -> {to_status}")
