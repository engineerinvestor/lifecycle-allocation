"""Core data models for lifecycle allocation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def risk_tolerance_to_gamma(rt: int) -> float:
    """Convert risk tolerance (1-10 scale) to gamma (risk aversion coefficient).

    Log-linear mapping: gamma = 10 * 0.2^((rt - 1) / 9)
    rt=1 -> gamma=10 (conservative), rt=5 -> ~4.47, rt=10 -> gamma=2 (aggressive)

    Parameters
    ----------
    rt : int
        Risk tolerance on a 1-10 scale, where 1 is the most conservative
        (gamma=10) and 10 is the most aggressive (gamma=2).

    Returns
    -------
    float
        Risk aversion coefficient (gamma). Higher values mean more risk-averse.
    """
    if not (1 <= rt <= 10):
        raise ValueError(f"risk_tolerance must be between 1 and 10, got {rt}")
    return float(10.0 * (0.2 ** ((rt - 1) / 9.0)))


@dataclass
class IncomeModelSpec:
    """Specification for income projection model.

    Attributes
    ----------
    type : str
        Income model type. One of ``"flat"`` (constant income), ``"growth"``
        (constant real growth), ``"profile"`` (CGM education-based polynomial),
        or ``"csv"`` (user-supplied CSV file).
    g : float
        Annual real income growth rate. Only used when ``type="growth"``.
    education : str or None
        Education level for CGM profile model. One of ``"no_hs"``, ``"hs"``,
        or ``"college"``. Only used when ``type="profile"`` and ``coefficients``
        is not provided.
    coefficients : list of float or None
        Custom polynomial coefficients for the profile model. Overrides
        ``education`` if provided. Expected format: [a0, a1, a2, a3].
    path : str or None
        Path to a CSV file with ``age`` and ``income`` columns. Required
        when ``type="csv"``.
    """

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
    """Specification for retirement benefit model.

    Attributes
    ----------
    type : str
        Benefit model type. One of ``"none"`` (no benefits), ``"flat"``
        (constant annual benefit post-retirement), or ``"schedule"``
        (user-supplied benefit schedule).
    annual_benefit : float
        Fixed annual benefit amount in dollars. Used when ``type="flat"``
        and this value is > 0. Takes priority over ``replacement_rate``.
    replacement_rate : float
        Fraction of pre-retirement income received as a benefit. Used when
        ``type="flat"`` and ``annual_benefit`` is 0.
    """

    type: str = "none"
    annual_benefit: float = 0.0
    replacement_rate: float = 0.0

    def __post_init__(self) -> None:
        valid_types = ("none", "flat", "schedule")
        if self.type not in valid_types:
            raise ValueError(f"benefit_model type must be one of {valid_types}, got '{self.type}'")


@dataclass
class MortalitySpec:
    """Specification for mortality/survival model.

    Attributes
    ----------
    type : str
        Mortality model type. One of ``"none"`` (assume survival to T_max),
        ``"parametric"`` (Gompertz-style survival curve), or ``"table"``
        (user-supplied survival probabilities).
    mode : float
        Modal age of death for the parametric model. Ignored when
        ``type="none"`` or ``type="table"``.
    dispersion : float
        Dispersion parameter for the parametric model. Controls the spread
        of the survival curve around the mode.
    path : str or None
        Path to a CSV file with survival probabilities. Required when
        ``type="table"``.
    """

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
    """Specification for discount curve used to discount future cash flows.

    Attributes
    ----------
    type : str
        Discount curve type. One of ``"constant"`` (flat rate) or
        ``"term_structure"`` (piecewise term structure).
    rate : float
        Constant annual discount rate (decimal). Used when ``type="constant"``.
        For example, 0.02 means 2% per year.
    """

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
    """Allocation constraints controlling the allowed range of equity exposure.

    Attributes
    ----------
    allow_leverage : bool
        If True, the allocation can exceed 100% (borrowing to invest). When
        enabled, the two-tier borrowing rate model applies.
    max_leverage : float
        Maximum allowed equity allocation as a multiple of wealth. Must be
        >= 1.0. Only effective when ``allow_leverage=True``.
    allow_short : bool
        If True, negative equity allocations are permitted.
    min_allocation : float
        Minimum equity allocation floor. Only meaningful when
        ``allow_short=True``.
    """

    allow_leverage: bool = False
    max_leverage: float = 1.0
    allow_short: bool = False
    min_allocation: float = 0.0

    def __post_init__(self) -> None:
        if self.max_leverage < 1.0:
            raise ValueError(f"max_leverage must be >= 1.0, got {self.max_leverage}")


@dataclass
class MarketAssumptions:
    """Capital market assumptions for the stock/bond asset universe.

    Attributes
    ----------
    mu : float
        Expected annual stock return (decimal). For example, 0.05 means 5%.
    r : float
        Risk-free rate (decimal). Used as the lending rate in the two-tier
        borrowing model.
    sigma : float
        Annual stock return volatility (decimal). Must be > 0.
    real : bool
        If True, all return assumptions are in real (inflation-adjusted) terms.
    borrowing_spread : float
        Spread above the risk-free rate for margin borrowing (decimal). The
        borrowing rate is ``r + borrowing_spread``. Only affects results when
        leverage is enabled and optimal. Must be >= 0.
    """

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
    """Complete investor profile combining demographics, income, and preferences.

    Attributes
    ----------
    age : int
        Current age in years.
    retirement_age : int
        Expected retirement age. Income stops and benefits begin at this age.
    investable_wealth : float
        Current investable financial wealth in dollars. Must be > 0.
    after_tax_income : float or None
        Current annual after-tax income. Required for income models that
        project future earnings.
    risk_tolerance : int or None
        Risk tolerance on a 1-10 scale. Converted to gamma via
        ``risk_tolerance_to_gamma()``. Provide either this or ``risk_aversion``.
    risk_aversion : float or None
        Risk aversion coefficient (gamma) directly. Higher values mean more
        risk-averse. Provide either this or ``risk_tolerance``.
    income_model : IncomeModelSpec
        Specification for projecting future income.
    benefit_model : BenefitModelSpec
        Specification for retirement benefits (e.g., Social Security proxy).
    mortality_model : MortalitySpec
        Specification for survival probability modeling.
    """

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
    """Result of an allocation computation.

    Attributes
    ----------
    alpha_star : float
        Baseline risky share from the two-tier Merton model, before human
        capital adjustment.
    alpha_unconstrained : float
        Raw allocation after human capital adjustment, before clamping:
        ``alpha_star * (1 + H/W)``.
    alpha_recommended : float
        Final recommended equity allocation after applying constraints
        (clamped to [0, 1] or [0, max_leverage]).
    human_capital : float
        Present value of future earnings and benefits.
    leverage_applied : bool
        True if the final allocation exceeds 1.0 using the borrowing rate.
    borrowing_cost_drag : float
        Reduction in alpha_star caused by the borrowing spread.
    explain : str
        Human-readable explanation of the allocation result.
    components : dict
        Intermediate values for debugging and education (H, W, H/W, gamma,
        market assumptions, etc.).
    """

    alpha_star: float
    alpha_unconstrained: float
    alpha_recommended: float
    human_capital: float
    leverage_applied: bool
    borrowing_cost_drag: float
    explain: str
    components: dict[str, Any]
