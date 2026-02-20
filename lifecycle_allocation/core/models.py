"""Core data models for lifecycle allocation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def risk_tolerance_to_gamma(rt: int) -> float:
    """Convert risk tolerance (1-10 scale) to gamma (risk aversion coefficient).

    Log-linear mapping: gamma = 10 * 0.2^((rt - 1) / 9)
    rt=1 -> gamma=10 (conservative), rt=5 -> ~4.47, rt=10 -> gamma=2 (aggressive)
    """
    if not (1 <= rt <= 10):
        raise ValueError(f"risk_tolerance must be between 1 and 10, got {rt}")
    return float(10.0 * (0.2 ** ((rt - 1) / 9.0)))


@dataclass
class IncomeModelSpec:
    """Specification for income projection model."""

    type: str = "flat"
    g: float = 0.0
    education: str | None = None
    coefficients: list[float] | None = None
    path: str | None = None

    def __post_init__(self) -> None:
        valid_types = ("flat", "growth", "profile", "csv")
        if self.type not in valid_types:
            raise ValueError(f"income_model type must be one of {valid_types}, got '{self.type}'")


@dataclass
class BenefitModelSpec:
    """Specification for retirement benefit model."""

    type: str = "none"
    annual_benefit: float = 0.0
    replacement_rate: float = 0.0

    def __post_init__(self) -> None:
        valid_types = ("none", "flat", "schedule")
        if self.type not in valid_types:
            raise ValueError(f"benefit_model type must be one of {valid_types}, got '{self.type}'")


@dataclass
class MortalitySpec:
    """Specification for mortality/survival model."""

    type: str = "none"
    mode: float = 0.0
    dispersion: float = 0.0
    path: str | None = None

    def __post_init__(self) -> None:
        valid_types = ("none", "parametric", "table")
        if self.type not in valid_types:
            raise ValueError(
                f"mortality_model type must be one of {valid_types}, got '{self.type}'"
            )


@dataclass
class DiscountCurveSpec:
    """Specification for discount curve."""

    type: str = "constant"
    rate: float = 0.02

    def __post_init__(self) -> None:
        valid_types = ("constant", "term_structure")
        if self.type not in valid_types:
            raise ValueError(
                f"discount_curve type must be one of {valid_types}, got '{self.type}'"
            )


@dataclass
class ConstraintsSpec:
    """Allocation constraints."""

    allow_leverage: bool = False
    max_leverage: float = 1.0
    allow_short: bool = False
    min_allocation: float = 0.0

    def __post_init__(self) -> None:
        if self.max_leverage < 1.0:
            raise ValueError(f"max_leverage must be >= 1.0, got {self.max_leverage}")


@dataclass
class MarketAssumptions:
    """Capital market assumptions."""

    mu: float = 0.05
    r: float = 0.02
    sigma: float = 0.18
    real: bool = True
    borrowing_spread: float = 0.0

    def __post_init__(self) -> None:
        if self.sigma <= 0:
            raise ValueError(f"sigma must be > 0, got {self.sigma}")
        if self.borrowing_spread < 0:
            raise ValueError(f"borrowing_spread must be >= 0, got {self.borrowing_spread}")


@dataclass
class InvestorProfile:
    """Complete investor profile."""

    age: int
    retirement_age: int
    investable_wealth: float
    after_tax_income: float | None = None
    risk_tolerance: int | None = None
    risk_aversion: float | None = None
    income_model: IncomeModelSpec = field(default_factory=IncomeModelSpec)
    benefit_model: BenefitModelSpec = field(default_factory=BenefitModelSpec)
    mortality_model: MortalitySpec = field(default_factory=MortalitySpec)

    def __post_init__(self) -> None:
        if self.risk_tolerance is None and self.risk_aversion is None:
            raise ValueError("Must provide either risk_tolerance (1-10) or risk_aversion (gamma)")
        if self.investable_wealth <= 0:
            raise ValueError(
                f"investable_wealth must be > 0, got {self.investable_wealth}. "
                "This model requires positive financial wealth."
            )
        if self.risk_tolerance is not None and not (1 <= self.risk_tolerance <= 10):
            raise ValueError(f"risk_tolerance must be between 1 and 10, got {self.risk_tolerance}")
        if self.risk_aversion is not None and self.risk_aversion <= 0:
            raise ValueError(f"risk_aversion (gamma) must be > 0, got {self.risk_aversion}")

    @property
    def gamma(self) -> float:
        """Resolve risk aversion coefficient from either risk_aversion or risk_tolerance."""
        if self.risk_aversion is not None:
            return self.risk_aversion
        assert self.risk_tolerance is not None
        return risk_tolerance_to_gamma(self.risk_tolerance)


@dataclass
class AllocationResult:
    """Result of an allocation computation."""

    alpha_star: float
    alpha_unconstrained: float
    alpha_recommended: float
    human_capital: float
    leverage_applied: bool
    borrowing_cost_drag: float
    explain: str
    components: dict[str, Any]
