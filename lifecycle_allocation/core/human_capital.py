"""Human capital present value computation."""

from __future__ import annotations

from lifecycle_allocation.core.discounting import discount_factor
from lifecycle_allocation.core.income_models import expected_income
from lifecycle_allocation.core.models import (
    BenefitModelSpec,
    DiscountCurveSpec,
    InvestorProfile,
)
from lifecycle_allocation.core.mortality import survival_prob


def expected_benefit(age: int, spec: BenefitModelSpec, profile: InvestorProfile) -> float:
    """Compute expected retirement benefit at a given age.

    Returns 0 if age < retirement_age or benefit model is 'none'.
    """
    if age < profile.retirement_age:
        return 0.0

    if spec.type == "none":
        return 0.0

    if spec.type == "flat":
        if spec.annual_benefit > 0:
            return spec.annual_benefit
        # Use replacement rate on income
        base_income = profile.after_tax_income or 0.0
        return base_income * spec.replacement_rate

    raise ValueError(f"Unknown benefit model type: {spec.type}")


def human_capital_pv(
    profile: InvestorProfile,
    curve: DiscountCurveSpec | None = None,
    *,
    t_max: int = 100,
) -> float:
    """Compute the present value of human capital.

    H_t = sum_{s=t+1..T_max} E[CF_s] * S(t->s) / D(t->s)

    Where CF_s is income (pre-retirement) or benefits (post-retirement).
    """
    if curve is None:
        curve = DiscountCurveSpec()

    current_age = profile.age
    pv = 0.0

    for future_age in range(current_age + 1, t_max + 1):
        # Get cash flow for this age
        if future_age < profile.retirement_age:
            cf = expected_income(future_age, profile.income_model, profile)
        else:
            cf = expected_benefit(future_age, profile.benefit_model, profile)

        if cf <= 0:
            continue

        s = survival_prob(current_age, future_age, profile.mortality_model)
        d = discount_factor(current_age, future_age, curve)

        pv += cf * s / d

    return pv
