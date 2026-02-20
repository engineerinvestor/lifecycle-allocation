# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**lifecycle-allocation** is an open-source Python library implementing a practical lifecycle portfolio choice framework inspired by James Choi et al. It combines human capital analysis with visual analytics to produce data-driven stock/bond allocation recommendations.

**Status:** v0.1.0 published on PyPI. See `SPEC.md` for the full specification. The reference paper is `w34166.pdf`.

**Disclaimer:** Educational/research software, not investment advice.

## Build & Development Commands

```bash
# Install
pip install -e ".[dev]"

# Testing
pytest tests/
pytest tests/test_allocation.py          # single test file
pytest tests/test_allocation.py::test_name  # single test

# Linting & formatting
ruff check .
black .
mypy lifecycle_allocation/

# CLI
lifecycle-allocation alloc --profile profile.yaml --out ./output --report
```

## Core Mathematical Framework

Three key formulas drive the entire library, with a two-tier borrowing rate model for leverage:

1. **Baseline risky share (Merton-style, two-tier):**
   - Lending regime (alpha ≤ 1): `alpha_unlev = (mu - r) / (gamma * sigma^2)`
   - Borrowing regime (alpha > 1): `alpha_lev = (mu - r_b) / (gamma * sigma^2)` where `r_b = r + borrowing_spread`
   - Algorithm: if `alpha_unlev > 1` and leverage allowed, use `min(alpha_lev, L_max)` if `alpha_lev > 1`, else `1.0`
2. **Human capital PV:** `H_t = sum_{s=t+1..T_max} E[CF_s] * S(t→s) / D(t→s)`
3. **Recommended stock share:** `alpha_t = clamp(alpha_star_adj * (1 + H_t / W_t), 0, L_max)` (leverage enabled) or `clamp(..., 0, 1)` (default)

Where W = financial wealth, H = human capital, gamma = risk aversion, mu = expected stock return, r = risk-free rate, r_b = borrowing rate, sigma = stock volatility, S = survival probability, D = discount factor.

## Architecture

The Python package is `lifecycle_allocation` (import name) / `lifecycle-allocation` (install name), with this module structure:

- **`core/`** — All computation lives here
  - `models.py` — Dataclasses: `InvestorProfile`, `MarketAssumptions` (includes `borrowing_spread`), `DiscountCurveSpec`, `ConstraintsSpec`, `AllocationResult` (includes `alpha_unconstrained`, `leverage_applied`, `borrowing_cost_drag`)
  - `allocation.py` — `alpha_star()`, `recommended_stock_share()`, clamping/constraints
  - `human_capital.py` — PV calculation combining income, benefits, discounting, mortality
  - `income_models.py` — Pluggable income processes (flat, growth, profile-based, CSV)
  - `mortality.py` — Survival probability models (none, parametric, user-supplied)
  - `discounting.py` — Discount curve abstractions (constant, term structure)
  - `strategies.py` — Reference strategies: 60/40, 100-minus-age, parametric TDF, user CSV
  - `explain.py` — Human-readable explanation text generation
- **`viz/`** — Visualization (matplotlib/plotly): balance sheet waterfall, strategy bars, glide path, sensitivity tornado, heatmaps
- **`sim/`** — Optional Monte Carlo simulation and CRRA utility evaluation
- **`io/`** — YAML/JSON/CSV profile loading
- **`cli/`** — CLI entry point (`lifecycle-allocation alloc`)

## Key Data Flow

1. User provides an `InvestorProfile` (age, income, wealth, risk tolerance) + `MarketAssumptions` via YAML/JSON or Python API
2. `human_capital_pv()` computes H from income model + benefits + mortality + discount curve
3. `alpha_star()` computes the Merton baseline using the two-tier borrowing rate model (uses `r_b` when leverage is allowed and optimal)
4. `recommended_stock_share()` combines them: `alpha_star_adj * (1 + H/W)`, clamped to [0, L_max] or [0, 1]
5. `compare_strategies()` benchmarks against heuristic strategies
6. `viz/` generates charts; `export_report()` produces a full output directory

## Engineering Standards

- Python 3.10+
- Type hints on all functions
- `ruff` + `black` for formatting, `mypy` for type checking
- `pytest` for testing with coverage
- Semantic versioning (v0.1 MVP → v0.5 → v1.0)

## Git Configuration

- **Remote:** https://github.com/engineerinvestor/lifecycle-allocation
- **Commit as:** Engineer Investor (`egr.investor@gmail.com`)
- Always use `git -c user.name="Engineer Investor" -c user.email="egr.investor@gmail.com" commit` when committing

## Writing Style

- **No em-dashes or double-dashes.** Never use `—` or `--` as punctuation in prose, markdown, or notebooks. Use a comma, period, colon, or semicolon instead.

## Edge Cases to Handle

- `W <= 0`: default to raising an error with guidance
- `H = 0`: allocation reduces to `alpha_star`
- Risk tolerance can be provided as 1-10 scale OR direct gamma coefficient
- All return assumptions must be consistently real or nominal
- Leverage enabled but `mu <= r_b`: leverage is never beneficial, fall back to alpha=1.0
- `borrowing_spread = 0`: frictionless leverage (theoretical only, should be documented as such)
- Very high `max_leverage`: warn about unrealistic assumptions in explain text
