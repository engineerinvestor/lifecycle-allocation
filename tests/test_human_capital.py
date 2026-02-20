"""Tests for human capital PV computation."""

import os
import tempfile

import pytest

from lifecycle_allocation.core.human_capital import expected_benefit, human_capital_pv
from lifecycle_allocation.core.income_models import expected_income
from lifecycle_allocation.core.models import (
    BenefitModelSpec,
    DiscountCurveSpec,
    IncomeModelSpec,
    InvestorProfile,
)


def _make_profile(**kwargs: object) -> InvestorProfile:
    defaults = dict(
        age=30,
        retirement_age=67,
        investable_wealth=100_000.0,
        after_tax_income=70_000.0,
        risk_tolerance=5,
    )
    defaults.update(kwargs)
    return InvestorProfile(**defaults)  # type: ignore[arg-type]


class TestFlatIncomeModel:
    def test_constant_regardless_of_age(self) -> None:
        profile = _make_profile()
        spec = IncomeModelSpec(type="flat")
        for age in [30, 40, 50, 60]:
            assert expected_income(age, spec, profile) == 70_000.0

    def test_zero_after_retirement(self) -> None:
        profile = _make_profile()
        spec = IncomeModelSpec(type="flat")
        assert expected_income(67, spec, profile) == 0.0
        assert expected_income(80, spec, profile) == 0.0


class TestGrowthIncomeModel:
    def test_manual_calculation(self) -> None:
        profile = _make_profile(age=30, after_tax_income=50_000.0)
        spec = IncomeModelSpec(type="growth", g=0.03)
        # At age 35: 50000 * 1.03^5
        expected = 50_000.0 * (1.03**5)
        assert expected_income(35, spec, profile) == pytest.approx(expected, rel=1e-9)

    def test_at_current_age_equals_base(self) -> None:
        profile = _make_profile(age=30, after_tax_income=50_000.0)
        spec = IncomeModelSpec(type="growth", g=0.03)
        assert expected_income(30, spec, profile) == pytest.approx(50_000.0)


class TestProfileIncomeModel:
    def test_college_peaks_around_50(self) -> None:
        profile = _make_profile(age=25, after_tax_income=50_000.0)
        spec = IncomeModelSpec(type="profile", education="college")
        incomes = {age: expected_income(age, spec, profile) for age in range(25, 67)}
        peak_age = max(incomes, key=incomes.get)  # type: ignore[arg-type]
        assert 45 <= peak_age <= 60

    def test_scales_to_current_income(self) -> None:
        profile = _make_profile(age=30, after_tax_income=80_000.0)
        spec = IncomeModelSpec(type="profile", education="college")
        assert expected_income(30, spec, profile) == pytest.approx(80_000.0, rel=1e-6)


class TestCSVIncomeModel:
    def test_loads_correct_values(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("age,income\n30,50000\n40,60000\n50,70000\n60,80000\n")
            f.flush()
            try:
                profile = _make_profile(age=30)
                spec = IncomeModelSpec(type="csv", path=f.name)
                assert expected_income(30, spec, profile) == pytest.approx(50_000.0)
                assert expected_income(40, spec, profile) == pytest.approx(60_000.0)
            finally:
                os.unlink(f.name)

    def test_missing_path_raises(self) -> None:
        profile = _make_profile()
        spec = IncomeModelSpec(type="csv")
        with pytest.raises(ValueError, match="path"):
            expected_income(30, spec, profile)

    def test_malformed_csv_raises(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("x,y\n1,2\n")
            f.flush()
            try:
                profile = _make_profile()
                spec = IncomeModelSpec(type="csv", path=f.name)
                with pytest.raises(ValueError, match="age.*income"):
                    expected_income(30, spec, profile)
            finally:
                os.unlink(f.name)


class TestHumanCapitalPV:
    def test_flat_income_constant_discount_closed_form(self) -> None:
        """Flat income Y, constant rate r, no mortality, N years to retirement.
        H = Y * (1 - (1+r)^{-N}) / r
        """
        age = 30
        ret_age = 67
        income = 70_000.0
        rate = 0.03
        # Income at ages 31..66 = 36 payments, discounted by (1+r)^k
        num_payments = ret_age - age - 1  # 36
        expected_h = income * (1.0 - (1.0 + rate) ** (-num_payments)) / rate

        profile = _make_profile(
            age=age,
            retirement_age=ret_age,
            after_tax_income=income,
            income_model=IncomeModelSpec(type="flat"),
            benefit_model=BenefitModelSpec(type="none"),
        )
        curve = DiscountCurveSpec(type="constant", rate=rate)
        h = human_capital_pv(profile, curve, t_max=100)

        assert h == pytest.approx(expected_h, rel=1e-6)

    def test_growth_income_geometric_series(self) -> None:
        """Growth income Y*(1+g)^k, constant discount r.
        PV = sum_{k=1}^{N} Y*(1+g)^k / (1+r)^k = Y*(1+g)/(r-g) * (1 - ((1+g)/(1+r))^N) when r != g
        """
        age = 30
        ret_age = 67
        income = 70_000.0
        rate = 0.04
        g = 0.02
        n = 36  # ages 31..66

        # Each payment at age (age + k): income * (1+g)^k
        # Discounted: income * (1+g)^k / (1+r)^k = income * ((1+g)/(1+r))^k
        # Sum = income * sum_{k=1}^{N} ((1+g)/(1+r))^k
        ratio = (1.0 + g) / (1.0 + rate)
        expected_h = income * ratio * (1.0 - ratio**n) / (1.0 - ratio)

        profile = _make_profile(
            age=age,
            retirement_age=ret_age,
            after_tax_income=income,
            income_model=IncomeModelSpec(type="growth", g=g),
            benefit_model=BenefitModelSpec(type="none"),
        )
        curve = DiscountCurveSpec(type="constant", rate=rate)
        h = human_capital_pv(profile, curve, t_max=100)

        assert h == pytest.approx(expected_h, rel=1e-6)

    def test_zero_income_gives_zero_h(self) -> None:
        profile = _make_profile(after_tax_income=0.0)
        curve = DiscountCurveSpec(type="constant", rate=0.03)
        h = human_capital_pv(profile, curve)
        assert h == pytest.approx(0.0)

    def test_retired_no_benefits_gives_zero_h(self) -> None:
        profile = _make_profile(
            age=70,
            retirement_age=67,
            after_tax_income=70_000.0,
            benefit_model=BenefitModelSpec(type="none"),
        )
        h = human_capital_pv(profile)
        assert h == pytest.approx(0.0)

    def test_retired_with_flat_benefit(self) -> None:
        """Retired person with flat benefit = annuity PV."""
        age = 70
        benefit = 30_000.0
        rate = 0.03
        t_max = 100

        # Benefits at ages 71..100 = 30 payments
        n = t_max - age  # 30
        expected_h = benefit * (1.0 - (1.0 + rate) ** (-n)) / rate

        profile = _make_profile(
            age=age,
            retirement_age=67,
            after_tax_income=70_000.0,
            benefit_model=BenefitModelSpec(type="flat", annual_benefit=benefit),
        )
        curve = DiscountCurveSpec(type="constant", rate=rate)
        h = human_capital_pv(profile, curve, t_max=t_max)

        assert h == pytest.approx(expected_h, rel=1e-6)

    def test_none_income_treated_as_zero(self) -> None:
        profile = _make_profile(after_tax_income=None)
        h = human_capital_pv(profile)
        assert h == pytest.approx(0.0)


class TestExpectedBenefit:
    def test_none_model_returns_zero(self) -> None:
        profile = _make_profile(age=70, retirement_age=67)
        spec = BenefitModelSpec(type="none")
        assert expected_benefit(75, spec, profile) == 0.0

    def test_flat_benefit_after_retirement(self) -> None:
        profile = _make_profile(age=70, retirement_age=67)
        spec = BenefitModelSpec(type="flat", annual_benefit=25_000.0)
        assert expected_benefit(75, spec, profile) == 25_000.0

    def test_flat_benefit_before_retirement_is_zero(self) -> None:
        profile = _make_profile(age=30, retirement_age=67)
        spec = BenefitModelSpec(type="flat", annual_benefit=25_000.0)
        assert expected_benefit(50, spec, profile) == 0.0

    def test_replacement_rate(self) -> None:
        profile = _make_profile(age=70, retirement_age=67, after_tax_income=100_000.0)
        spec = BenefitModelSpec(type="flat", replacement_rate=0.4)
        assert expected_benefit(75, spec, profile) == pytest.approx(40_000.0)
