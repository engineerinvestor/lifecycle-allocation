"""Tests for core allocation computation."""

import pytest

from lifecycle_allocation.core.allocation import alpha_star, recommended_stock_share
from lifecycle_allocation.core.models import (
    ConstraintsSpec,
    InvestorProfile,
    MarketAssumptions,
)


class TestAlphaStar:
    def test_basic_computation(self) -> None:
        market = MarketAssumptions(mu=0.05, r=0.02, sigma=0.18)
        # (0.05 - 0.02) / (4.0 * 0.18^2) = 0.03 / 0.1296 = 0.2315
        a, lev, drag = alpha_star(market, gamma=4.0)
        assert a == pytest.approx(0.03 / (4.0 * 0.18**2), rel=1e-6)
        assert not lev
        assert drag == 0.0

    def test_monotonicity_in_gamma(self) -> None:
        market = MarketAssumptions(mu=0.05, r=0.02, sigma=0.18)
        gammas = [2.0, 3.0, 4.0, 6.0, 8.0, 10.0]
        alphas = [alpha_star(market, g)[0] for g in gammas]
        for i in range(len(alphas) - 1):
            assert alphas[i] >= alphas[i + 1]

    def test_monotonicity_in_sigma(self) -> None:
        sigmas = [0.10, 0.15, 0.20, 0.25, 0.30]
        alphas = [
            alpha_star(MarketAssumptions(mu=0.05, r=0.02, sigma=s), gamma=4.0)[0] for s in sigmas
        ]
        for i in range(len(alphas) - 1):
            assert alphas[i] >= alphas[i + 1]

    def test_increases_with_equity_premium(self) -> None:
        mus = [0.03, 0.05, 0.07, 0.10]
        alphas = [
            alpha_star(MarketAssumptions(mu=m, r=0.02, sigma=0.18), gamma=4.0)[0] for m in mus
        ]
        for i in range(len(alphas) - 1):
            assert alphas[i] <= alphas[i + 1]

    def test_leverage_disabled_never_exceeds_1(self) -> None:
        # Very aggressive params that would push alpha > 1
        market = MarketAssumptions(mu=0.10, r=0.02, sigma=0.10)
        constraints = ConstraintsSpec(allow_leverage=False)
        a, lev, _ = alpha_star(market, gamma=2.0, constraints=constraints)
        assert a <= 1.0
        assert not lev

    def test_leverage_enabled_with_spread_kills_benefit(self) -> None:
        # alpha_unlev > 1, but borrowing cost pushes alpha_lev <= 1
        market = MarketAssumptions(mu=0.06, r=0.02, sigma=0.18, borrowing_spread=0.02)
        constraints = ConstraintsSpec(allow_leverage=True, max_leverage=2.0)
        # alpha_unlev = 0.04 / (4 * 0.0324) = 0.3086... actually that's < 1
        # Need smaller gamma to push unlev > 1
        # With gamma=1: alpha_unlev = 0.04/0.0324 = 1.235
        # alpha_lev = (0.06 - 0.04) / (1 * 0.0324) = 0.617 <= 1
        a, lev, drag = alpha_star(market, gamma=1.0, constraints=constraints)
        assert a == 1.0
        assert not lev
        assert drag > 0

    def test_leverage_enabled_zero_spread(self) -> None:
        # With zero spread, alpha_lev == alpha_unlev
        market = MarketAssumptions(mu=0.10, r=0.02, sigma=0.10, borrowing_spread=0.0)
        constraints = ConstraintsSpec(allow_leverage=True, max_leverage=5.0)
        a, lev, drag = alpha_star(market, gamma=2.0, constraints=constraints)
        alpha_expected = (0.10 - 0.02) / (2.0 * 0.01)
        assert a == pytest.approx(min(alpha_expected, 5.0), rel=1e-6)
        assert lev
        assert drag == pytest.approx(0.0)

    def test_max_leverage_cap(self) -> None:
        market = MarketAssumptions(mu=0.10, r=0.02, sigma=0.10, borrowing_spread=0.0)
        constraints = ConstraintsSpec(allow_leverage=True, max_leverage=1.5)
        a, lev, _ = alpha_star(market, gamma=2.0, constraints=constraints)
        assert a <= 1.5

    def test_mu_less_than_r_b_no_leverage(self) -> None:
        # mu <= r_b means even unlev is low or leverage is clearly suboptimal
        market = MarketAssumptions(mu=0.03, r=0.02, sigma=0.18, borrowing_spread=0.02)
        constraints = ConstraintsSpec(allow_leverage=True, max_leverage=2.0)
        a, lev, _ = alpha_star(market, gamma=4.0, constraints=constraints)
        assert a <= 1.0
        assert not lev

    def test_log_return_variant(self) -> None:
        market = MarketAssumptions(mu=0.05, r=0.02, sigma=0.18)
        a_merton, _, _ = alpha_star(market, gamma=4.0, variant="merton")
        a_log, _, _ = alpha_star(market, gamma=4.0, variant="log_return")
        # Log return adds 0.5*sigma^2 to numerator, so it's higher
        assert a_log > a_merton

    def test_unknown_variant_raises(self) -> None:
        market = MarketAssumptions()
        with pytest.raises(ValueError, match="Unknown alpha_star variant"):
            alpha_star(market, gamma=4.0, variant="unknown")


class TestRecommendedStockShare:
    def _simple_profile(self, **kwargs: object) -> InvestorProfile:
        defaults = dict(
            age=30,
            retirement_age=67,
            investable_wealth=100_000.0,
            after_tax_income=70_000.0,
            risk_tolerance=5,
        )
        defaults.update(kwargs)
        return InvestorProfile(**defaults)  # type: ignore[arg-type]

    def test_with_zero_human_capital(self) -> None:
        # Retired person with no benefits -> H = 0
        profile = self._simple_profile(age=70, retirement_age=67)
        market = MarketAssumptions(mu=0.05, r=0.02, sigma=0.18)
        result = recommended_stock_share(profile, market)
        a_star_val, _, _ = alpha_star(market, profile.gamma)
        assert result.human_capital == pytest.approx(0.0)
        assert result.alpha_recommended == pytest.approx(a_star_val, rel=1e-6)

    def test_human_capital_increases_equity(self) -> None:
        # Young person with high H/W should have higher equity than alpha_star alone
        profile = self._simple_profile()
        market = MarketAssumptions(mu=0.05, r=0.02, sigma=0.18)
        result = recommended_stock_share(profile, market)
        a_star_val, _, _ = alpha_star(market, profile.gamma)
        # With human capital, unconstrained alpha should be higher
        assert result.alpha_unconstrained > a_star_val
        assert result.human_capital > 0

    def test_clamping_never_negative(self) -> None:
        # Even with weird params, result should be >= 0
        profile = self._simple_profile()
        # Very low mu means alpha_star is very low
        market = MarketAssumptions(mu=0.01, r=0.02, sigma=0.30)
        result = recommended_stock_share(profile, market)
        assert result.alpha_recommended >= 0.0

    def test_clamping_never_exceeds_upper_bound(self) -> None:
        profile = self._simple_profile()
        market = MarketAssumptions(mu=0.05, r=0.02, sigma=0.18)
        constraints = ConstraintsSpec(allow_leverage=False)
        result = recommended_stock_share(profile, market, constraints=constraints)
        assert result.alpha_recommended <= 1.0

    def test_leverage_allows_above_1(self) -> None:
        # Young person with huge H/W and leverage allowed
        profile = self._simple_profile(
            investable_wealth=10_000.0, after_tax_income=100_000.0, risk_aversion=2.0
        )
        market = MarketAssumptions(mu=0.07, r=0.02, sigma=0.15, borrowing_spread=0.0)
        constraints = ConstraintsSpec(allow_leverage=True, max_leverage=3.0)
        result = recommended_stock_share(profile, market, constraints=constraints)
        # With huge H/W and aggressive params, should push above 1
        assert result.alpha_unconstrained > 1.0

    def test_result_has_explanation(self) -> None:
        profile = self._simple_profile()
        market = MarketAssumptions()
        result = recommended_stock_share(profile, market)
        assert "Lifecycle Allocation" in result.explain
        assert "Disclaimer" in result.explain

    def test_result_components_populated(self) -> None:
        profile = self._simple_profile()
        market = MarketAssumptions()
        result = recommended_stock_share(profile, market)
        assert "human_capital" in result.components
        assert "gamma" in result.components
        assert "hw_ratio" in result.components
