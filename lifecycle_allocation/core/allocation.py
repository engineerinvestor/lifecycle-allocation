"""Core allocation computation: alpha_star and recommended_stock_share."""

from __future__ import annotations

import math

from lifecycle_allocation.core.explain import build_explanation
from lifecycle_allocation.core.human_capital import human_capital_pv
from lifecycle_allocation.core.models import (
    AllocationResult,
    ConstraintsSpec,
    DiscountCurveSpec,
    InvestorProfile,
    MarketAssumptions,
)


def alpha_star(
    market: MarketAssumptions,
    gamma: float,
    constraints: ConstraintsSpec | None = None,
    *,
    variant: str = "merton",
) -> tuple[float, bool, float]:
    """Compute the baseline risky share using the two-tier borrowing rate model.

    Returns:
        (alpha, leverage_applied, borrowing_cost_drag)
    """
    if constraints is None:
        constraints = ConstraintsSpec()

    sigma_sq = market.sigma**2

    if variant == "merton":
        equity_premium = market.mu - market.r
    elif variant == "log_return":
        equity_premium = math.log(1 + market.mu) - math.log(1 + market.r) + 0.5 * sigma_sq
    else:
        raise ValueError(f"Unknown alpha_star variant: {variant}")

    alpha_unlev = equity_premium / (gamma * sigma_sq)

    if alpha_unlev <= 1.0 or not constraints.allow_leverage:
        # No leverage regime
        clamped = max(0.0, min(alpha_unlev, 1.0))
        return clamped, False, 0.0

    # Leverage regime: compute with borrowing rate
    r_b = market.r + market.borrowing_spread
    if variant == "merton":
        equity_premium_lev = market.mu - r_b
    else:
        equity_premium_lev = math.log(1 + market.mu) - math.log(1 + r_b) + 0.5 * sigma_sq

    alpha_lev = equity_premium_lev / (gamma * sigma_sq)

    # Borrowing cost drag: how much alpha is reduced by the spread
    drag = alpha_unlev - alpha_lev

    if alpha_lev <= 1.0:
        # Borrowing cost kills the leverage benefit
        return 1.0, False, drag

    # Leverage is optimal — cap at max_leverage
    result = min(alpha_lev, constraints.max_leverage)
    return result, True, drag


def recommended_stock_share(
    profile: InvestorProfile,
    market: MarketAssumptions,
    curve: DiscountCurveSpec | None = None,
    constraints: ConstraintsSpec | None = None,
    *,
    t_max: int = 100,
    variant: str = "merton",
) -> AllocationResult:
    """Compute the recommended stock allocation incorporating human capital.

    This is the main entry point for computing a lifecycle allocation.
    """
    if curve is None:
        curve = DiscountCurveSpec()
    if constraints is None:
        constraints = ConstraintsSpec()

    gamma = profile.gamma
    a_star, leverage_applied, drag = alpha_star(market, gamma, constraints, variant=variant)

    h = human_capital_pv(profile, curve, t_max=t_max)
    w = profile.investable_wealth

    # Raw allocation with human capital adjustment
    alpha_unconstrained = a_star * (1.0 + h / w)

    # Clamp
    upper = constraints.max_leverage if constraints.allow_leverage else 1.0
    alpha_recommended = max(0.0, min(alpha_unconstrained, upper))

    # Check if the final result actually uses leverage
    final_leverage = leverage_applied and alpha_recommended > 1.0

    components = {
        "human_capital": h,
        "investable_wealth": w,
        "hw_ratio": h / w,
        "gamma": gamma,
        "alpha_star": a_star,
        "alpha_unconstrained": alpha_unconstrained,
        "alpha_recommended": alpha_recommended,
        "leverage_applied": final_leverage,
        "borrowing_cost_drag": drag,
        "mu": market.mu,
        "r": market.r,
        "sigma": market.sigma,
        "borrowing_spread": market.borrowing_spread,
    }

    explain = build_explanation(components, constraints)

    return AllocationResult(
        alpha_star=a_star,
        alpha_unconstrained=alpha_unconstrained,
        alpha_recommended=alpha_recommended,
        human_capital=h,
        leverage_applied=final_leverage,
        borrowing_cost_drag=drag,
        explain=explain,
        components=components,
    )
