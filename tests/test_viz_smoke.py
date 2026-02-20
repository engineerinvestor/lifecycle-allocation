"""Smoke tests for visualization functions."""

import os
import tempfile

import matplotlib

matplotlib.use("Agg")

from lifecycle_allocation.core.allocation import recommended_stock_share
from lifecycle_allocation.core.models import (
    InvestorProfile,
    MarketAssumptions,
)
from lifecycle_allocation.core.strategies import compare_strategies
from lifecycle_allocation.viz.charts import plot_balance_sheet, plot_strategy_bars


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


class TestPlotBalanceSheet:
    def test_produces_figure(self) -> None:
        profile = _make_profile()
        market = MarketAssumptions()
        result = recommended_stock_share(profile, market)
        fig = plot_balance_sheet(result, profile)
        assert fig is not None

    def test_saves_to_file(self) -> None:
        profile = _make_profile()
        market = MarketAssumptions()
        result = recommended_stock_share(profile, market)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            plot_balance_sheet(result, profile, save_path=path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_zero_human_capital(self) -> None:
        profile = _make_profile(age=70, retirement_age=67)
        market = MarketAssumptions()
        result = recommended_stock_share(profile, market)
        fig = plot_balance_sheet(result, profile)
        assert fig is not None


class TestPlotStrategyBars:
    def test_produces_figure(self) -> None:
        profile = _make_profile()
        market = MarketAssumptions()
        df = compare_strategies(profile, market)
        fig = plot_strategy_bars(df)
        assert fig is not None

    def test_saves_to_file(self) -> None:
        profile = _make_profile()
        market = MarketAssumptions()
        df = compare_strategies(profile, market)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            plot_strategy_bars(df, save_path=path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_all_strategies_equal(self) -> None:
        import pandas as pd

        df = pd.DataFrame(
            {
                "strategy": ["A", "B", "C"],
                "allocation": [0.5, 0.5, 0.5],
                "description": ["x", "y", "z"],
            }
        )
        fig = plot_strategy_bars(df)
        assert fig is not None
