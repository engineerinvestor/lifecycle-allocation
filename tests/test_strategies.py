"""Tests for reference strategies."""

import pytest

from lifecycle_allocation.core.models import (
    InvestorProfile,
    MarketAssumptions,
)
from lifecycle_allocation.core.strategies import (
    compare_strategies,
    strategy_n_minus_age,
    strategy_parametric_tdf,
    strategy_sixty_forty,
)


class TestSixtyForty:
    def test_always_returns_060(self) -> None:
        for age in [22, 30, 50, 70, 90]:
            assert strategy_sixty_forty(age) == 0.60


class TestNMinusAge:
    def test_default_n100(self) -> None:
        assert strategy_n_minus_age(30) == pytest.approx(0.70)
        assert strategy_n_minus_age(60) == pytest.approx(0.40)

    def test_n110(self) -> None:
        assert strategy_n_minus_age(30, n=110) == pytest.approx(0.80)

    def test_clamps_to_0(self) -> None:
        assert strategy_n_minus_age(110) == 0.0

    def test_clamps_to_1(self) -> None:
        assert strategy_n_minus_age(0, n=200) == 1.0


class TestParametricTDF:
    def test_young_investor(self) -> None:
        assert strategy_parametric_tdf(22) == pytest.approx(0.90)

    def test_at_retirement(self) -> None:
        assert strategy_parametric_tdf(67) == pytest.approx(0.50)

    def test_old_investor(self) -> None:
        assert strategy_parametric_tdf(90) == pytest.approx(0.30)

    def test_monotonically_decreasing(self) -> None:
        allocs = [strategy_parametric_tdf(age) for age in range(22, 91)]
        for i in range(len(allocs) - 1):
            assert allocs[i] >= allocs[i + 1]

    def test_values_in_range(self) -> None:
        for age in range(20, 100):
            a = strategy_parametric_tdf(age)
            assert 0.0 <= a <= 1.0


class TestCompareStrategies:
    def test_returns_dataframe_with_at_least_4_rows(self) -> None:
        profile = InvestorProfile(
            age=30,
            retirement_age=67,
            investable_wealth=100_000.0,
            after_tax_income=70_000.0,
            risk_tolerance=5,
        )
        market = MarketAssumptions()
        df = compare_strategies(profile, market)
        assert len(df) >= 4
        assert "strategy" in df.columns
        assert "allocation" in df.columns
        assert "description" in df.columns

    def test_all_allocations_are_valid(self) -> None:
        profile = InvestorProfile(
            age=30,
            retirement_age=67,
            investable_wealth=100_000.0,
            after_tax_income=70_000.0,
            risk_tolerance=5,
        )
        market = MarketAssumptions()
        df = compare_strategies(profile, market)
        for alloc in df["allocation"]:
            assert 0.0 <= alloc <= 2.0  # generous upper bound

    def test_user_supplied_strategies(self) -> None:
        profile = InvestorProfile(
            age=30,
            retirement_age=67,
            investable_wealth=100_000.0,
            after_tax_income=70_000.0,
            risk_tolerance=5,
        )
        market = MarketAssumptions()
        df = compare_strategies(profile, market, strategies={"My Strategy": 0.75})
        assert len(df) >= 5
        assert "My Strategy" in df["strategy"].values
