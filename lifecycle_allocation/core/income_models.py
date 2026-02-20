"""Pluggable income projection models."""

from __future__ import annotations

import math

import pandas as pd

from lifecycle_allocation.core.models import IncomeModelSpec, InvestorProfile

# CGM education-level polynomial coefficients from Cocco, Gomes, Maenhout (2005).
# Income = exp(a0 + a1*age + a2*age^2 + a3*age^3)
# These are for log-income as a function of age/10.
CGM_COEFFICIENTS: dict[str, list[float]] = {
    "no_hs": [-2.1700, 2.7004, -0.1682, -0.0323],
    "hs": [-2.1700, 2.7004, -0.1682, -0.0323],
    "college": [-4.3148, 5.3810, -0.1682, -0.0323],
}


def _cgm_log_income(age: int, coefficients: list[float]) -> float:
    """Compute log-income from polynomial coefficients (age scaled by /10)."""
    x = age / 10.0
    return coefficients[0] + coefficients[1] * x + coefficients[2] * x**2 + coefficients[3] * x**3


def expected_income(age: int, spec: IncomeModelSpec, profile: InvestorProfile) -> float:
    """Compute expected income at a given age.

    Returns 0 if age >= retirement_age.

    Parameters
    ----------
    age : int
        The age at which to compute expected income.
    spec : IncomeModelSpec
        Income model specification (type, growth rate, education, etc.).
    profile : InvestorProfile
        Investor profile, used for current age, retirement_age, and
        after_tax_income as the base income level.

    Returns
    -------
    float
        Expected annual after-tax income in dollars.
    """
    if age >= profile.retirement_age:
        return 0.0

    base_income = profile.after_tax_income or 0.0

    if spec.type == "flat":
        return base_income

    if spec.type == "growth":
        years = age - profile.age
        return base_income * (1.0 + spec.g) ** years

    if spec.type == "profile":
        coeffs = spec.coefficients
        if coeffs is None:
            education = spec.education or "college"
            if education not in CGM_COEFFICIENTS:
                raise ValueError(f"Unknown education level: {education}")
            coeffs = CGM_COEFFICIENTS[education]

        # Scale so that the profile matches the user's stated income at current age
        log_income_at_current = _cgm_log_income(profile.age, coeffs)
        log_income_at_age = _cgm_log_income(age, coeffs)
        ratio = math.exp(log_income_at_age - log_income_at_current)
        return base_income * ratio

    if spec.type == "csv":
        if spec.path is None:
            raise ValueError("CSV income model requires a 'path' to the CSV file")
        df = pd.read_csv(spec.path)
        if "age" not in df.columns or "income" not in df.columns:
            raise ValueError("CSV must have 'age' and 'income' columns")
        # Look for an exact age match first
        row = df[df["age"] == age]
        if len(row) == 0:
            # No exact match -- fall back to linear interpolation.
            # Sort by age so interpolation works correctly.
            df = df.sort_values("age")
            ages = df["age"].values
            incomes = df["income"].values
            # Ages outside the CSV range return 0 (no extrapolation)
            if age < ages[0] or age > ages[-1]:
                return 0.0
            # Build a Series indexed by age, add the target age, and interpolate
            series = pd.Series(list(incomes), index=list(ages))
            return float(series.reindex([age]).interpolate().iloc[0])
        return float(row["income"].iloc[0])

    raise ValueError(f"Unknown income model type: {spec.type}")
