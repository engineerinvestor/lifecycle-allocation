"""Survival probability models."""

from __future__ import annotations

from lifecycle_allocation.core.models import MortalitySpec


def survival_prob(from_age: int, to_age: int, spec: MortalitySpec) -> float:
    """Compute survival probability S(from_age -> to_age).

    Returns a value in [0, 1].
    """
    if to_age <= from_age:
        return 1.0

    if spec.type == "none":
        return 1.0

    raise ValueError(f"Unknown mortality model type: {spec.type}")
