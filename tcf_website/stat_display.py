"""Normalize course/instructor stats for UI display (no Django model imports)."""

import math

# Valid ranges for review aggregates (1–5) and GPA (0–4). Values outside these are
# treated as missing in the UI (e.g. -1 sentinels from Coalesce in instructor sorting).
_STAT_BOUNDS = {
    "rating": (1.0, 5.0),
    "difficulty": (1.0, 5.0),
    "gpa": (0.0, 4.0),
}


def stat_display_value(stat_kind: str, value):
    """Return ``value`` if it is a finite number within the valid range for ``stat_kind``.

    Aggregates use sentinel values (such as -1) when sorting instructors with no data;
    those must not be shown as real ratings, difficulty, or GPA.
    """
    if stat_kind not in _STAT_BOUNDS:
        return None
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(num):
        return None
    low, high = _STAT_BOUNDS[stat_kind]
    if low <= num <= high:
        return num
    return None
