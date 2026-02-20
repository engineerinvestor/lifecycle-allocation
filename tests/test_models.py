"""Tests for core data models."""

import pytest

from lifecycle_allocation.core.models import (
    BenefitModelSpec,
    ConstraintsSpec,
    DiscountCurveSpec,
    IncomeModelSpec,
    InvestorProfile,
    MarketAssumptions,
    MortalitySpec,
    risk_tolerance_to_gamma,
)


class TestRiskToleranceToGamma:
    def test_rt_1_gives_gamma_10(self) -> None:
        assert risk_tolerance_to_gamma(1) == pytest.approx(10.0)

    def test_rt_10_gives_gamma_2(self) -> None:
        assert risk_tolerance_to_gamma(10) == pytest.approx(2.0)

    def test_rt_5_gives_about_4_47(self) -> None:
        expected = 10.0 * (0.2 ** (4.0 / 9.0))
        assert risk_tolerance_to_gamma(5) == pytest.approx(expected, rel=1e-6)

    def test_monotonically_decreasing(self) -> None:
        gammas = [risk_tolerance_to_gamma(rt) for rt in range(1, 11)]
        for i in range(len(gammas) - 1):
            assert gammas[i] > gammas[i + 1]

    def test_rt_0_raises(self) -> None:
        with pytest.raises(ValueError, match="between 1 and 10"):
            risk_tolerance_to_gamma(0)

    def test_rt_11_raises(self) -> None:
        with pytest.raises(ValueError, match="between 1 and 10"):
            risk_tolerance_to_gamma(11)


class TestInvestorProfile:
    def test_minimal_with_risk_tolerance(self) -> None:
        p = InvestorProfile(age=30, retirement_age=67, investable_wealth=100_000, risk_tolerance=5)
        assert p.gamma == pytest.approx(risk_tolerance_to_gamma(5))

    def test_minimal_with_risk_aversion(self) -> None:
        p = InvestorProfile(
            age=30, retirement_age=67, investable_wealth=100_000, risk_aversion=4.0
        )
        assert p.gamma == 4.0

    def test_risk_aversion_takes_precedence(self) -> None:
        p = InvestorProfile(
            age=30,
            retirement_age=67,
            investable_wealth=100_000,
            risk_tolerance=5,
            risk_aversion=3.0,
        )
        assert p.gamma == 3.0

    def test_no_risk_params_raises(self) -> None:
        with pytest.raises(ValueError, match="risk_tolerance.*risk_aversion"):
            InvestorProfile(age=30, retirement_age=67, investable_wealth=100_000)

    def test_wealth_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="investable_wealth must be > 0"):
            InvestorProfile(age=30, retirement_age=67, investable_wealth=0, risk_tolerance=5)

    def test_wealth_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="investable_wealth must be > 0"):
            InvestorProfile(age=30, retirement_age=67, investable_wealth=-1000, risk_tolerance=5)

    def test_risk_tolerance_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="between 1 and 10"):
            InvestorProfile(age=30, retirement_age=67, investable_wealth=100_000, risk_tolerance=0)

    def test_negative_gamma_raises(self) -> None:
        with pytest.raises(ValueError, match="risk_aversion.*must be > 0"):
            InvestorProfile(
                age=30, retirement_age=67, investable_wealth=100_000, risk_aversion=-1.0
            )

    def test_default_sub_models(self) -> None:
        p = InvestorProfile(age=30, retirement_age=67, investable_wealth=100_000, risk_tolerance=5)
        assert p.income_model.type == "flat"
        assert p.benefit_model.type == "none"
        assert p.mortality_model.type == "none"


class TestMarketAssumptions:
    def test_defaults(self) -> None:
        m = MarketAssumptions()
        assert m.mu == 0.05
        assert m.r == 0.02
        assert m.sigma == 0.18
        assert m.borrowing_spread == 0.0

    def test_sigma_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="sigma must be > 0"):
            MarketAssumptions(sigma=0)

    def test_negative_spread_raises(self) -> None:
        with pytest.raises(ValueError, match="borrowing_spread must be >= 0"):
            MarketAssumptions(borrowing_spread=-0.01)


class TestConstraintsSpec:
    def test_defaults(self) -> None:
        c = ConstraintsSpec()
        assert c.allow_leverage is False
        assert c.max_leverage == 1.0

    def test_max_leverage_below_1_raises(self) -> None:
        with pytest.raises(ValueError, match="max_leverage must be >= 1.0"):
            ConstraintsSpec(max_leverage=0.5)


class TestSubModelSpecs:
    def test_invalid_income_type_raises(self) -> None:
        with pytest.raises(ValueError, match="income_model type"):
            IncomeModelSpec(type="invalid")

    def test_invalid_benefit_type_raises(self) -> None:
        with pytest.raises(ValueError, match="benefit_model type"):
            BenefitModelSpec(type="invalid")

    def test_invalid_mortality_type_raises(self) -> None:
        with pytest.raises(ValueError, match="mortality_model type"):
            MortalitySpec(type="invalid")

    def test_invalid_discount_type_raises(self) -> None:
        with pytest.raises(ValueError, match="discount_curve type"):
            DiscountCurveSpec(type="invalid")
