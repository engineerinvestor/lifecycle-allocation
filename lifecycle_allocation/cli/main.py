"""CLI entry point for lifecycle-allocation."""

from __future__ import annotations

import json
from pathlib import Path

import click

from lifecycle_allocation.core.allocation import recommended_stock_share
from lifecycle_allocation.core.models import ConstraintsSpec, MarketAssumptions
from lifecycle_allocation.core.strategies import compare_strategies
from lifecycle_allocation.io.loaders import load_profile
from lifecycle_allocation.viz.charts import plot_balance_sheet, plot_strategy_bars


@click.group()
def cli() -> None:
    """lifecycle-allocation: Lifecycle portfolio allocation framework."""


@cli.command()
@click.option("--profile", "profile_path", required=True, type=click.Path(exists=True))
@click.option("--out", "out_dir", required=True, type=click.Path())
@click.option("--report", is_flag=True, default=False, help="Generate charts")
@click.option("--mu", type=float, default=None, help="Expected stock return")
@click.option("--r", "risk_free", type=float, default=None, help="Risk-free rate")
@click.option("--sigma", type=float, default=None, help="Stock volatility")
@click.option("--tmax", type=int, default=100, help="Maximum age for computation")
@click.option("--allow-leverage", is_flag=True, default=False)
@click.option("--max-leverage", type=float, default=1.0)
@click.option("--borrowing-spread", type=float, default=None)
@click.option("--format", "img_format", type=click.Choice(["png", "svg"]), default="png")
@click.option("--real/--nominal", default=True)
def alloc(
    profile_path: str,
    out_dir: str,
    report: bool,
    mu: float | None,
    risk_free: float | None,
    sigma: float | None,
    tmax: int,
    allow_leverage: bool,
    max_leverage: float,
    borrowing_spread: float | None,
    img_format: str,
    real: bool,
) -> None:
    """Compute lifecycle allocation from a profile.

    Loads an investor profile from YAML, applies any CLI flag overrides to
    market assumptions and constraints, computes the allocation, and writes
    results to the output directory.

    CLI flags (--mu, --r, --sigma, --borrowing-spread, --real/--nominal)
    override the corresponding values from the YAML profile. The
    --allow-leverage and --max-leverage flags merge with YAML constraints.

    Output files: allocation.json, summary.md, and optionally charts/.
    """
    profile, market, curve, constraints = load_profile(profile_path)

    # Apply CLI overrides to market assumptions. Each flag, if provided,
    # replaces the corresponding value from the YAML profile.
    if mu is not None:
        market = MarketAssumptions(
            mu=mu,
            r=market.r,
            sigma=market.sigma,
            real=market.real,
            borrowing_spread=market.borrowing_spread,
        )
    if risk_free is not None:
        market = MarketAssumptions(
            mu=market.mu,
            r=risk_free,
            sigma=market.sigma,
            real=market.real,
            borrowing_spread=market.borrowing_spread,
        )
    if sigma is not None:
        market = MarketAssumptions(
            mu=market.mu,
            r=market.r,
            sigma=sigma,
            real=market.real,
            borrowing_spread=market.borrowing_spread,
        )
    if borrowing_spread is not None:
        market = MarketAssumptions(
            mu=market.mu,
            r=market.r,
            sigma=market.sigma,
            real=market.real,
            borrowing_spread=borrowing_spread,
        )
    market = MarketAssumptions(
        mu=market.mu,
        r=market.r,
        sigma=market.sigma,
        real=real,
        borrowing_spread=market.borrowing_spread,
    )

    # Merge leverage constraints from CLI flags and YAML profile
    if allow_leverage or constraints.allow_leverage:
        constraints = ConstraintsSpec(
            allow_leverage=True,
            max_leverage=max_leverage if max_leverage > 1.0 else constraints.max_leverage,
            allow_short=constraints.allow_short,
            min_allocation=constraints.min_allocation,
        )

    # Compute
    result = recommended_stock_share(profile, market, curve, constraints, t_max=tmax)
    comparison_df = compare_strategies(profile, market, curve, constraints)

    # Create output directory
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Write allocation.json -- filter components to JSON-serializable scalars only
    alloc_data = {
        "alpha_star": result.alpha_star,
        "alpha_unconstrained": result.alpha_unconstrained,
        "alpha_recommended": result.alpha_recommended,
        "human_capital": result.human_capital,
        "leverage_applied": result.leverage_applied,
        "borrowing_cost_drag": result.borrowing_cost_drag,
        "components": {
            k: v for k, v in result.components.items() if isinstance(v, (int, float, bool, str))
        },
    }
    with open(out / "allocation.json", "w") as f:
        json.dump(alloc_data, f, indent=2)

    # Write summary.md
    with open(out / "summary.md", "w") as f:
        f.write("# Lifecycle Allocation Summary\n\n")
        f.write(result.explain)
        f.write("\n\n## Strategy Comparison\n\n")
        f.write("| Strategy | Allocation |\n|---|---|\n")
        for _, row in comparison_df.iterrows():
            f.write(f"| {row['strategy']} | {row['allocation']:.1%} |\n")

    click.echo(f"Recommended stock allocation: {result.alpha_recommended:.1%}")
    click.echo(f"Results written to {out}")

    if report:
        charts_dir = out / "charts"
        charts_dir.mkdir(exist_ok=True)
        plot_balance_sheet(result, profile, save_path=charts_dir / f"balance_sheet.{img_format}")
        plot_strategy_bars(comparison_df, save_path=charts_dir / f"strategy_bars.{img_format}")
        click.echo(f"Charts written to {charts_dir}")
