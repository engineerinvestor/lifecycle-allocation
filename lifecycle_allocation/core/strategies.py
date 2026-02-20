"""Reference strategies for comparison: 60/40, N-minus-age, parametric TDF."""

from __future__ import annotations

import pandas as pd

from lifecycle_allocation.core.allocation import recommended_stock_share
from lifecycle_allocation.core.models import (
    ConstraintsSpec,
    DiscountCurveSpec,
    InvestorProfile,
    MarketAssumptions,
)


def strategy_sixty_forty(age: int) -> float:
    """Classic 60/40 — always 60% stocks."""
    return 0.60


def strategy_n_minus_age(age: int, n: int = 100) -> float:
    """N-minus-age rule: (N - age)/100, clamped to [0, 1]."""
    return max(0.0, min((n - age) / 100.0, 1.0))


def strategy_parametric_tdf(age: int, retirement_age: int = 67) -> float:
    """Parametric target-date fund glide path.

    Linear glide from 90% at age 22 to 50% at retirement to 30% at age 90+.
    """
    if age <= 22:
        return 0.90
    if age >= 90:
        return 0.30

    if age <= retirement_age:
        # Linear from 90% at 22 to 50% at retirement_age
        fraction = (age - 22) / (retirement_age - 22)
        return 0.90 - fraction * (0.90 - 0.50)
    else:
        # Linear from 50% at retirement_age to 30% at 90
        fraction = (age - retirement_age) / (90 - retirement_age)
        return 0.50 - fraction * (0.50 - 0.30)


def compare_strategies(
    profile: InvestorProfile,
    market: MarketAssumptions,
    curve: DiscountCurveSpec | None = None,
    constraints: ConstraintsSpec | None = None,
    *,
    strategies: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Compare the Choi lifecycle allocation against heuristic strategies.

    Returns a DataFrame with columns: strategy, allocation, description.
    """
    result = recommended_stock_share(profile, market, curve, constraints)
    age = profile.age

    rows: list[dict[str, object]] = [
        {
            "strategy": "Choi Lifecycle",
            "allocation": result.alpha_recommended,
            "description": "Human-capital-adjusted Merton rule",
        },
        {
            "strategy": "60/40",
            "allocation": strategy_sixty_forty(age),
            "description": "Classic fixed 60% equity / 40% bonds",
        },
        {
            "strategy": "100-minus-age",
            "allocation": strategy_n_minus_age(age, 100),
            "description": f"Equity = (100 - {age}) / 100",
        },
        {
            "strategy": "Target-Date Fund",
            "allocation": strategy_parametric_tdf(age, profile.retirement_age),
            "description": "Parametric TDF glide path",
        },
    ]

    if strategies:
        for name, alloc in strategies.items():
            rows.append({"strategy": name, "allocation": alloc, "description": "User-supplied"})

    return pd.DataFrame(rows)
