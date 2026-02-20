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

    Implements the Merton-style optimal equity allocation with separate
    lending and borrowing rates. See SPEC.md section 4.2 for the full
    algorithm.

    Parameters
    ----------
    market : MarketAssumptions
        Capital market assumptions (mu, r, sigma, borrowing_spread).
    gamma : float
        Risk aversion coefficient. Higher values produce lower allocations.
    constraints : ConstraintsSpec or None
        Allocation constraints. If None, defaults are used (no leverage).
    variant : str
        Calculation variant. ``"merton"`` uses arithmetic returns;
        ``"log_return"`` applies a log-return correction.

    Returns
    -------
    tuple of (float, bool, float)
        - ``alpha`` -- the baseline risky share, clamped to [0, 1] or
          [0, max_leverage] depending on constraints.
        - ``leverage_applied`` -- True if the result uses the borrowing rate.
        - ``borrowing_cost_drag`` -- reduction in alpha due to the borrowing
          spread (``alpha_unlev - alpha_lev``). Zero when no leverage.

    Notes
    -----
    The two-tier algorithm:

    1. Compute ``alpha_unlev = (mu - r) / (gamma * sigma^2)``
    2. If ``alpha_unlev <= 1`` or leverage is disabled: clamp to [0, 1]
    3. If leverage is allowed and ``alpha_unlev > 1``:
       - Compute ``alpha_lev = (mu - r_b) / (gamma * sigma^2)``
       - If ``alpha_lev > 1``: leverage is optimal, cap at ``max_leverage``
       - If ``alpha_lev <= 1``: borrowing cost kills the benefit, return 1.0
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

    # Step 1: Compute the unleveraged (lending-rate) optimal allocation
    alpha_unlev = equity_premium / (gamma * sigma_sq)

    if alpha_unlev <= 1.0 or not constraints.allow_leverage:
        # Lending regime: no borrowing needed, clamp to [0, 1]
        clamped = max(0.0, min(alpha_unlev, 1.0))
        return clamped, False, 0.0

    # Step 2: Unleveraged alpha > 1 and leverage allowed -- switch to
    # the borrowing rate (r_b = r + spread) to compute the leveraged alpha
    r_b = market.r + market.borrowing_spread
    if variant == "merton":
        equity_premium_lev = market.mu - r_b
    else:
        equity_premium_lev = math.log(1 + market.mu) - math.log(1 + r_b) + 0.5 * sigma_sq

    alpha_lev = equity_premium_lev / (gamma * sigma_sq)

    # Drag measures how much the borrowing spread reduces the optimal alpha
    drag = alpha_unlev - alpha_lev

    if alpha_lev <= 1.0:
        # Step 3a: Borrowing cost eliminates the leverage benefit entirely.
        # The investor is better off at exactly 100% equity.
        return 1.0, False, drag

    # Step 3b: Leverage is still optimal after accounting for borrowing cost.
    # Cap at the user's maximum leverage constraint.
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
    Combines the baseline risky share from ``alpha_star()`` with a human
    capital adjustment: ``alpha = alpha* x (1 + H/W)``.

    Parameters
    ----------
    profile : InvestorProfile
        Investor demographics, income model, and risk preferences.
    market : MarketAssumptions
        Capital market assumptions (returns, volatility, borrowing spread).
    curve : DiscountCurveSpec or None
        Discount curve for human capital PV. Defaults to constant 2%.
    constraints : ConstraintsSpec or None
        Allocation constraints (leverage, shorting). Defaults to no leverage.
    t_max : int
        Maximum age for human capital computation (default 100).
    variant : str
        Calculation variant passed to ``alpha_star()``.

    Returns
    -------
    AllocationResult
        Complete result including recommended allocation, human capital,
        explanation text, and all intermediate components.

    Notes
    -----
    The algorithm:

    1. Compute ``alpha*`` via the two-tier borrowing rate model
    2. Compute human capital PV (H) from income, benefits, mortality, discounting
    3. Raw allocation: ``alpha* x (1 + H/W)``
    4. Clamp to [0, 1] (default) or [0, max_leverage] (if leverage enabled)
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

    # Assemble all intermediate values for the explanation builder and
    # for user inspection via AllocationResult.components
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
