"""YAML/JSON profile loading."""

from __future__ import annotations

from pathlib import Path

import yaml

from lifecycle_allocation.core.models import (
    BenefitModelSpec,
    ConstraintsSpec,
    DiscountCurveSpec,
    IncomeModelSpec,
    InvestorProfile,
    MarketAssumptions,
    MortalitySpec,
)


def load_profile(
    path: str | Path,
) -> tuple[InvestorProfile, MarketAssumptions, DiscountCurveSpec, ConstraintsSpec]:
    """Load an investor profile from a YAML file.

    Parses a YAML profile into the four configuration objects needed to
    run an allocation computation. Missing sections use defaults.

    Parameters
    ----------
    path : str or Path
        Path to a YAML file containing the investor profile.

    Returns
    -------
    tuple of (InvestorProfile, MarketAssumptions, DiscountCurveSpec, ConstraintsSpec)
        The four configuration objects parsed from the YAML file.

    Raises
    ------
    ValueError
        If the YAML content is not a mapping, or if required fields
        (``age``, ``investable_wealth``) are missing.
    FileNotFoundError
        If the specified path does not exist.
    """
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping, got {type(data).__name__}")

    # Parse each optional section from the YAML, falling back to defaults
    # when a section is missing. Order: income -> benefits -> mortality ->
    # profile -> market -> discount curve -> constraints.

    # Income model
    income_data = data.get("income_model", {})
    income_model = IncomeModelSpec(
        type=income_data.get("type", "flat"),
        g=income_data.get("g", 0.0),
        education=income_data.get("education"),
        coefficients=income_data.get("coefficients"),
        path=income_data.get("path"),
    )

    # Benefit model
    benefit_data = data.get("benefit_model", {})
    benefit_model = BenefitModelSpec(
        type=benefit_data.get("type", "none"),
        annual_benefit=benefit_data.get("annual_benefit", 0.0),
        replacement_rate=benefit_data.get("replacement_rate", 0.0),
    )

    # Mortality model
    mortality_data = data.get("mortality_model", {})
    mortality_model = MortalitySpec(
        type=mortality_data.get("type", "none"),
    )

    # Profile
    profile = InvestorProfile(
        age=data["age"],
        retirement_age=data.get("retirement_age", 67),
        investable_wealth=data["investable_wealth"],
        after_tax_income=data.get("after_tax_income"),
        risk_tolerance=data.get("risk_tolerance"),
        risk_aversion=data.get("risk_aversion"),
        income_model=income_model,
        benefit_model=benefit_model,
        mortality_model=mortality_model,
    )

    # Market assumptions
    market_data = data.get("market", {})
    market = MarketAssumptions(
        mu=market_data.get("mu", 0.05),
        r=market_data.get("r", 0.02),
        sigma=market_data.get("sigma", 0.18),
        real=market_data.get("real", True),
        borrowing_spread=market_data.get("borrowing_spread", 0.0),
    )

    # Discount curve
    curve_data = data.get("discount_curve", {})
    curve = DiscountCurveSpec(
        type=curve_data.get("type", "constant"),
        rate=curve_data.get("rate", 0.02),
    )

    # Constraints
    constraints_data = data.get("constraints", {})
    constraints = ConstraintsSpec(
        allow_leverage=constraints_data.get("allow_leverage", False),
        max_leverage=constraints_data.get("max_leverage", 1.0),
        allow_short=constraints_data.get("allow_short", False),
        min_allocation=constraints_data.get("min_allocation", 0.0),
    )

    return profile, market, curve, constraints
