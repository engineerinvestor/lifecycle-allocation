"""Chart functions for lifecycle allocation visualization."""

from __future__ import annotations

from pathlib import Path


def _is_notebook() -> bool:
    try:
        from IPython import get_ipython  # type: ignore[import-not-found]

        return get_ipython() is not None
    except ImportError:
        return False


import matplotlib  # noqa: E402

if not _is_notebook():
    matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from lifecycle_allocation.core.allocation import recommended_stock_share  # noqa: E402
from lifecycle_allocation.core.models import (  # noqa: E402
    AllocationResult,
    HumanCapitalSpec,
    InvestorProfile,
    MarketAssumptions,
)
from lifecycle_allocation.viz.themes import THEME, apply_theme  # noqa: E402


def plot_balance_sheet(
    result: AllocationResult,
    profile: InvestorProfile,
    *,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
) -> Figure:
    """Plot the personal balance sheet: W, H, and W+H.

    Creates a bar chart showing financial wealth, human capital, and their
    sum, with the H/W ratio annotated in the title.

    Parameters
    ----------
    result : AllocationResult
        Allocation result containing human_capital value.
    profile : InvestorProfile
        Investor profile containing investable_wealth.
    ax : Axes or None
        Matplotlib axes to draw on. If None, a new figure is created.
    save_path : str, Path, or None
        If provided, saves the figure to this path at 150 DPI.

    Returns
    -------
    Figure
        The matplotlib Figure containing the chart.
    """
    colors = THEME["colors"]
    w = profile.investable_wealth
    h = result.human_capital
    total = w + h
    hw_ratio = h / w if w > 0 else 0.0
    beta_h = result.components.get("human_capital_beta", 0.0)

    if ax is None:
        fig, ax = plt.subplots(figsize=THEME["figsize"])
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
    assert ax is not None and fig is not None

    if beta_h > 0:
        # Show H decomposed into bond-like and equity-like portions
        h_bond = result.components.get("human_capital_bond_like", h)
        h_equity = result.components.get("human_capital_equity_like", 0.0)

        labels = ["Financial\nWealth (W)", "H (Bond-like)", "H (Equity-like)", "Total\n(W + H)"]
        values = [w, h_bond, h_equity, total]
        bar_colors = [colors["wealth"], colors["human_capital"], "#FF9800", colors["total"]]
    else:
        labels = ["Financial\nWealth (W)", "Human\nCapital (H)", "Total\n(W + H)"]
        values = [w, h, total]
        bar_colors = [colors["wealth"], colors["human_capital"], colors["total"]]

    bars = ax.bar(labels, values, color=bar_colors, width=THEME["bar_width"])

    # Annotate values
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"${val:,.0f}",
            ha="center",
            va="bottom",
            fontsize=THEME["font_size"]["annotation"],
            fontweight="bold",
        )

    title = f"Personal Balance Sheet (H/W = {hw_ratio:.1f}x)"
    if beta_h > 0:
        title += f", beta={beta_h:.2f}"
    ax.set_title(title, fontsize=THEME["font_size"]["title"], fontweight="bold")
    ax.set_ylabel("Value ($)", fontsize=THEME["font_size"]["label"])
    apply_theme(ax)

    fig.tight_layout()

    if save_path:
        fig.savefig(str(save_path), dpi=150, bbox_inches="tight")

    return fig


def plot_strategy_bars(
    comparison_df: pd.DataFrame,
    *,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
) -> Figure:
    """Plot horizontal bar chart comparing allocation strategies.

    Parameters
    ----------
    comparison_df : pd.DataFrame
        DataFrame from ``compare_strategies()`` with columns ``strategy``
        and ``allocation``.
    ax : Axes or None
        Matplotlib axes to draw on. If None, a new figure is created.
    save_path : str, Path, or None
        If provided, saves the figure to this path at 150 DPI.

    Returns
    -------
    Figure
        The matplotlib Figure containing the chart.
    """
    colors = THEME["colors"]
    color_map = {
        "Choi Lifecycle": colors["choi"],
        "60/40": colors["sixty_forty"],
        "100-minus-age": colors["n_minus_age"],
        "Target-Date Fund": colors["tdf"],
    }

    if ax is None:
        fig, ax = plt.subplots(figsize=THEME["figsize"])
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
    assert ax is not None and fig is not None

    strategies = comparison_df["strategy"].tolist()
    allocations = comparison_df["allocation"].tolist()
    bar_colors = [color_map.get(s, colors["user"]) for s in strategies]

    y_pos = range(len(strategies))
    ax.barh(y_pos, allocations, color=bar_colors, height=0.5)

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(strategies)
    ax.set_xlabel("Stock Allocation (%)", fontsize=THEME["font_size"]["label"])
    ax.set_title(
        "Strategy Comparison",
        fontsize=THEME["font_size"]["title"],
        fontweight="bold",
    )

    # Annotate percentages
    for i, alloc in enumerate(allocations):
        ax.text(
            alloc + 0.01,
            i,
            f"{alloc:.0%}",
            va="center",
            fontsize=THEME["font_size"]["annotation"],
        )

    # Format x-axis as percentage
    ax.set_xlim(0, max(allocations) * 1.2 + 0.05)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))

    apply_theme(ax)
    fig.tight_layout()

    if save_path:
        fig.savefig(str(save_path), dpi=150, bbox_inches="tight")

    return fig


def plot_beta_sensitivity(
    profile: InvestorProfile,
    market: MarketAssumptions,
    *,
    betas: list[float] | None = None,
    ax: Axes | None = None,
    save_path: str | Path | None = None,
) -> Figure:
    """Plot recommended allocation vs. human capital beta.

    Shows how the equity allocation decreases as human capital becomes
    more equity-like (higher beta).

    Parameters
    ----------
    profile : InvestorProfile
        Base investor profile. The human_capital_model.beta will be
        varied across the specified range.
    market : MarketAssumptions
        Capital market assumptions.
    betas : list of float or None
        Beta values to evaluate. Defaults to 0.0, 0.1, ..., 1.0.
    ax : Axes or None
        Matplotlib axes to draw on. If None, a new figure is created.
    save_path : str, Path, or None
        If provided, saves the figure to this path at 150 DPI.

    Returns
    -------
    Figure
        The matplotlib Figure containing the chart.
    """
    import copy

    if betas is None:
        betas = [i / 10.0 for i in range(11)]

    allocations = []
    for b in betas:
        p = copy.copy(profile)
        p.human_capital_model = HumanCapitalSpec(beta=b)
        r = recommended_stock_share(p, market)
        allocations.append(r.alpha_recommended)

    if ax is None:
        fig, ax = plt.subplots(figsize=THEME["figsize"])
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
    assert ax is not None and fig is not None

    ax.plot(betas, allocations, linewidth=2.5, color=THEME["colors"]["choi"], marker="o")
    ax.set_xlabel("Human Capital Beta", fontsize=THEME["font_size"]["label"])
    ax.set_ylabel("Recommended Stock Allocation", fontsize=THEME["font_size"]["label"])
    ax.set_title(
        "Allocation Sensitivity to Human Capital Beta",
        fontsize=THEME["font_size"]["title"],
        fontweight="bold",
    )
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.set_xlim(0, 1)
    apply_theme(ax)
    fig.tight_layout()

    if save_path:
        fig.savefig(str(save_path), dpi=150, bbox_inches="tight")

    return fig
