"""Lifecycle portfolio allocation framework inspired by Choi et al."""

__version__ = "0.1.0"

from lifecycle_allocation.core.allocation import alpha_star, recommended_stock_share
from lifecycle_allocation.core.human_capital import human_capital_pv
from lifecycle_allocation.core.models import (
    AllocationResult,
    BenefitModelSpec,
    ConstraintsSpec,
    DiscountCurveSpec,
    IncomeModelSpec,
    InvestorProfile,
    MarketAssumptions,
    MortalitySpec,
    risk_tolerance_to_gamma,
)
from lifecycle_allocation.core.strategies import compare_strategies

__all__ = [
    "AllocationResult",
    "BenefitModelSpec",
    "ConstraintsSpec",
    "DiscountCurveSpec",
    "IncomeModelSpec",
    "InvestorProfile",
    "MarketAssumptions",
    "MortalitySpec",
    "alpha_star",
    "compare_strategies",
    "human_capital_pv",
    "recommended_stock_share",
    "risk_tolerance_to_gamma",
]
