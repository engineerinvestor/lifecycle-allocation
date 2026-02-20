"""Discount curve abstractions."""

from __future__ import annotations

from lifecycle_allocation.core.models import DiscountCurveSpec


def discount_factor(from_age: int, to_age: int, curve: DiscountCurveSpec) -> float:
    """Compute the discount factor D(from_age -> to_age).

    Returns a value >= 1.0 (the amount $1 today grows to by to_age).
    To get PV, divide future cash flow by this factor.
    """
    n = to_age - from_age
    if n <= 0:
        return 1.0

    if curve.type == "constant":
        return (1.0 + curve.rate) ** n

    raise ValueError(f"Unknown discount curve type: {curve.type}")
