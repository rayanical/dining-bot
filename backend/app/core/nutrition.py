"""Nutrition goal helpers.

Maps textual goals to calorie/protein targets so downstream code can compute
progress against a user's intent without changing the DB schema.
"""
from __future__ import annotations

from typing import Optional, Tuple

# Default targets used when no goal is provided or goal is unrecognized.
DEFAULT_CALORIES = 2200
DEFAULT_PROTEIN_G = 100

# Simple mapping of goal keywords to targets.
GOAL_PRESETS = {
    "lose weight": (1800, 110),
    "weight loss": (1800, 110),
    "cutting": (1800, 120),
    "maintain": (2200, 110),
    "maintenance": (2200, 110),
    "gain muscle": (2600, 150),
    "muscle gain": (2600, 150),
    "bulk": (2800, 160),
}


def goal_to_targets(goal: Optional[str]) -> Tuple[int, int]:
    """Return (calories_target, protein_target_g) for a textual goal.

    Args:
        goal: Goal text saved in the user's profile.

    Returns:
        Tuple of calorie target (int) and protein target grams (int).
    """
    if not goal:
        return DEFAULT_CALORIES, DEFAULT_PROTEIN_G

    normalized = goal.strip().lower()
    # Exact match lookup first
    if normalized in GOAL_PRESETS:
        return GOAL_PRESETS[normalized]

    # Fuzzy contains checks for common words
    if "lose" in normalized or "cut" in normalized:
        return GOAL_PRESETS["lose weight"]
    if "gain" in normalized or "bulk" in normalized:
        return GOAL_PRESETS["gain muscle"]
    if "maintain" in normalized or "maintenance" in normalized:
        return GOAL_PRESETS["maintain"]

    return DEFAULT_CALORIES, DEFAULT_PROTEIN_G
