"""Human-readable explanation text generation."""

from __future__ import annotations

from typing import Any

from lifecycle_allocation.core.models import ConstraintsSpec

LEVERAGE_DISCLOSURES = [
    (
        "Borrowing spread reduces effective risk premium: The leveraged allocation uses "
        "mu - r_b rather than mu - r, so the optimal leveraged equity share is always lower "
        "than frictionless theory suggests."
    ),
    (
        "Margin calls and forced deleveraging: Real-world margin lending can force liquidation "
        "at market troughs, creating procyclical risk not captured by this static model."
    ),
    (
        "Amplified volatility and tail risk: Leverage scales both returns and losses. Under "
        "non-normal return distributions, the realized downside can be substantially worse "
        "than the Gaussian model implies."
    ),
    (
        "Tax treatment of margin interest: Deductibility of margin interest varies by "
        "jurisdiction and investor situation; the model does not account for this."
    ),
    (
        "Volatility drag under discrete rebalancing: The model assumes continuous rebalancing. "
        "In practice, discrete rebalancing under leverage introduces volatility drag that "
        "reduces compound returns."
    ),
]


def build_explanation(components: dict[str, Any], constraints: ConstraintsSpec | None) -> str:
    """Build a human-readable explanation of the allocation result.

    Parameters
    ----------
    components : dict
        Intermediate computation values. Expected keys:

        - ``human_capital`` (float): PV of future earnings/benefits
        - ``investable_wealth`` (float): current financial wealth
        - ``alpha_star`` (float): baseline risky share
        - ``alpha_unconstrained`` (float): allocation before clamping
        - ``alpha_recommended`` (float): final clamped allocation
        - ``leverage_applied`` (bool): whether leverage is in the result
    constraints : ConstraintsSpec or None
        Allocation constraints, used to determine if leverage disclosures
        should be included.

    Returns
    -------
    str
        Multi-line explanation text including balance sheet summary,
        allocation derivation, and leverage risk disclosures (if applicable).
    """
    lines: list[str] = []

    h = components.get("human_capital", 0.0)
    w = components.get("investable_wealth", 0.0)
    hw_ratio = h / w if w > 0 else 0.0
    a_star = components.get("alpha_star", 0.0)
    a_unconstrained = components.get("alpha_unconstrained", 0.0)
    a_recommended = components.get("alpha_recommended", 0.0)
    leverage_applied = components.get("leverage_applied", False)

    lines.append("=== Lifecycle Allocation Explanation ===")
    lines.append("")
    lines.append(f"Financial wealth (W): ${w:,.0f}")
    lines.append(f"Human capital (H):    ${h:,.0f}")
    lines.append(f"Total wealth (W+H):   ${w + h:,.0f}")
    lines.append(f"H/W ratio:            {hw_ratio:.2f}")
    lines.append("")
    lines.append(f"Baseline risky share (alpha*): {a_star:.1%}")

    if hw_ratio > 0:
        lines.append(
            f"Human capital adjustment: alpha* x (1 + H/W) = "
            f"{a_star:.1%} x (1 + {hw_ratio:.2f}) = {a_unconstrained:.1%}"
        )
    else:
        lines.append("No human capital adjustment (H = 0).")

    if a_unconstrained != a_recommended:
        lines.append(f"After constraints: {a_recommended:.1%}")
    else:
        lines.append(f"Recommended stock allocation: {a_recommended:.1%}")

    # Leverage disclosures
    if leverage_applied and a_recommended > 1.0:
        lines.append("")
        lines.append("--- Leverage Risk Disclosures ---")
        for i, disclosure in enumerate(LEVERAGE_DISCLOSURES, 1):
            lines.append(f"{i}. {disclosure}")

    lines.append("")
    lines.append(
        "Disclaimer: This is for education and research purposes only. "
        "It is not investment advice."
    )

    return "\n".join(lines)
