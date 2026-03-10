#!/usr/bin/env python3
"""Generate publication-quality PDF figures for the risky human capital paper.

Produces three figures used in risky_human_capital.tex:
  1. figures/beta_sensitivity.pdf  -- allocation vs beta for multiple H/W ratios
  2. figures/balance_sheet_comparison.pdf -- side-by-side balance sheets
  3. figures/glide_paths.pdf -- allocation vs age for different betas

Usage:
    python generate_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the package is importable when running from the papers/ directory.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from lifecycle_allocation import (  # noqa: E402
    HumanCapitalSpec,
    InvestorProfile,
    MarketAssumptions,
    recommended_stock_share,
)

# ---------------------------------------------------------------------------
# Publication-quality matplotlib settings
# ---------------------------------------------------------------------------
mpl.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman", "Times New Roman", "DejaVu Serif"],
        "text.usetex": False,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.figsize": (7, 4.5),
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "lines.linewidth": 1.8,
    }
)

FIGURES_DIR = Path(__file__).resolve().parent / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Shared market assumptions
MARKET = MarketAssumptions(mu=0.05, r=0.02, sigma=0.18)
GAMMA = 4.0
ALPHA_STAR = (MARKET.mu - MARKET.r) / (GAMMA * MARKET.sigma**2)

# Colors
C_BLUE = "#2166ac"
C_ORANGE = "#d6604d"
C_GREEN = "#4dac26"
C_PURPLE = "#7b3294"
C_GREY = "#878787"


# ---------------------------------------------------------------------------
# Helper: compute recommended allocation for a given beta and H/W ratio
# ---------------------------------------------------------------------------
def _alloc_for_beta_hw(beta_h: float, hw_ratio: float) -> float:
    """Compute clamped allocation from the beta-adjusted formula."""
    raw = ALPHA_STAR * (1.0 + (1.0 - beta_h) * hw_ratio)
    return float(np.clip(raw, 0.0, 1.0))


def _alloc_from_library(
    age: int,
    wealth: float,
    income: float,
    beta_h: float,
    retirement_age: int = 65,
) -> float:
    """Use the lifecycle_allocation library to compute allocation."""
    profile = InvestorProfile(
        age=age,
        retirement_age=retirement_age,
        investable_wealth=wealth,
        after_tax_income=income,
        risk_aversion=GAMMA,
        human_capital_model=HumanCapitalSpec(beta=beta_h),
    )
    result = recommended_stock_share(profile, MARKET)
    return result.alpha_recommended


# ---------------------------------------------------------------------------
# Figure 1: Allocation vs beta for several H/W ratios
# ---------------------------------------------------------------------------
def figure_beta_sensitivity() -> None:
    betas = np.linspace(0.0, 1.0, 200)
    hw_ratios = [1.0, 3.0, 5.0]
    labels = ["H/W = 1 (near retirement)", "H/W = 3 (mid-career)", "H/W = 5 (young worker)"]
    colors = [C_GREEN, C_ORANGE, C_BLUE]
    styles = ["--", "-.", "-"]

    fig, ax = plt.subplots()
    for hw, label, color, ls in zip(hw_ratios, labels, colors, styles):
        allocs = [_alloc_for_beta_hw(b, hw) for b in betas]
        ax.plot(betas, allocs, label=label, color=color, linestyle=ls)

    ax.set_xlabel(r"Human Capital Beta ($\beta_H$)")
    ax.set_ylabel("Recommended Equity Allocation")
    ax.set_title(r"Equity Allocation vs. Human Capital Beta")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(xmax=1.0))
    ax.legend(loc="upper right", framealpha=0.9)
    ax.axhline(ALPHA_STAR, color=C_GREY, linewidth=1.0, linestyle=":", label=None)
    ax.annotate(
        rf"$\alpha^* = {ALPHA_STAR:.2f}$",
        xy=(0.85, ALPHA_STAR + 0.02),
        fontsize=9,
        color=C_GREY,
    )

    fig.tight_layout()
    out = FIGURES_DIR / "beta_sensitivity.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# Figure 2: Balance sheet comparison (beta=0 vs beta=0.6)
# ---------------------------------------------------------------------------
def figure_balance_sheet() -> None:
    W = 100_000
    H = 500_000
    beta_0 = 0.0
    beta_06 = 0.6

    fig, axes = plt.subplots(1, 2, figsize=(9, 5), sharey=True)

    for ax, beta, title in zip(
        axes,
        [beta_0, beta_06],
        [r"$\beta_H = 0$ (Government)", r"$\beta_H = 0.6$ (Tech, RSUs)"],
    ):
        h_bond = (1.0 - beta) * H
        h_equity = beta * H

        # Stacked bar: financial wealth | H bond-like | H equity-like
        bar_width = 0.5
        ax.bar(0, W, bar_width, color=C_BLUE, label="Financial Wealth (W)")
        ax.bar(1, h_bond, bar_width, color=C_GREEN, label="HC, Bond-like")
        ax.bar(
            1,
            h_equity,
            bar_width,
            bottom=h_bond,
            color=C_ORANGE,
            label="HC, Equity-like",
        )

        # Allocation annotation
        alloc = _alloc_for_beta_hw(beta, H / W)
        ax.set_title(title, fontsize=11)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Financial\nWealth", "Human\nCapital"])
        ax.set_ylim(0, 650_000)
        ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))

        # Annotation box
        ax.annotate(
            f"Rec. equity: {alloc:.0%}",
            xy=(0.5, 580_000),
            fontsize=11,
            fontweight="bold",
            ha="center",
            bbox=dict(boxstyle="round,pad=0.3", fc="wheat", alpha=0.8),
        )

    axes[0].set_ylabel("Value ($)")
    axes[0].legend(loc="upper left", fontsize=9, framealpha=0.9)
    fig.suptitle("Total Wealth Balance Sheet Decomposition", fontsize=13, y=1.01)
    fig.tight_layout()
    out = FIGURES_DIR / "balance_sheet_comparison.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# Figure 3: Glide paths for different betas
# ---------------------------------------------------------------------------
def figure_glide_paths() -> None:
    ages = list(range(25, 66))
    betas = [0.0, 0.30, 0.60]
    labels = [
        r"$\beta_H = 0$ (Bond-like HC)",
        r"$\beta_H = 0.3$ (Moderate)",
        r"$\beta_H = 0.6$ (Tech, RSUs)",
    ]
    colors = [C_BLUE, C_ORANGE, C_PURPLE]
    styles = ["-", "-.", "--"]

    initial_wealth = 50_000
    income = 80_000
    annual_saving = 15_000  # approximate annual savings for wealth accumulation

    fig, ax = plt.subplots()

    for beta, label, color, ls in zip(betas, labels, colors, styles):
        allocs = []
        for age in ages:
            # Approximate wealth accumulation: grows with age
            years_from_start = age - 25
            wealth = initial_wealth + annual_saving * years_from_start
            # Use the library to get the full computation including HC PV
            a = _alloc_from_library(age=age, wealth=wealth, income=income, beta_h=beta)
            allocs.append(a)
        ax.plot(ages, allocs, label=label, color=color, linestyle=ls)

    ax.set_xlabel("Age")
    ax.set_ylabel("Recommended Equity Allocation")
    ax.set_title("Lifecycle Glide Paths by Human Capital Beta")
    ax.set_xlim(25, 65)
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(xmax=1.0))
    ax.legend(loc="upper right", framealpha=0.9)

    # Reference line at alpha*
    ax.axhline(ALPHA_STAR, color=C_GREY, linewidth=1.0, linestyle=":")
    ax.annotate(
        rf"$\alpha^* = {ALPHA_STAR:.2f}$",
        xy=(60, ALPHA_STAR + 0.02),
        fontsize=9,
        color=C_GREY,
    )

    fig.tight_layout()
    out = FIGURES_DIR / "glide_paths.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"Alpha* (Merton ratio): {ALPHA_STAR:.4f}")
    print(f"Output directory: {FIGURES_DIR}\n")

    figure_beta_sensitivity()
    figure_balance_sheet()
    figure_glide_paths()

    print("\nAll figures generated successfully.")


if __name__ == "__main__":
    main()
