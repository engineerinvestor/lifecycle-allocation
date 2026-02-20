# Quick Start

This guide walks through a complete workflow: installing the library, creating a profile, computing an allocation, comparing strategies, and generating charts.

For the README's condensed version, see the [project homepage](https://github.com/engineerinvestor/lifecycle-allocation). For the interactive notebook version, open the [tutorial in Colab](https://colab.research.google.com/github/engineerinvestor/lifecycle-allocation/blob/main/examples/notebooks/tutorial.ipynb).

## 1. Installation

```bash
pip install lifecycle-allocation
```

For development (linting, testing, docs):

```bash
git clone https://github.com/engineerinvestor/lifecycle-allocation.git
cd lifecycle-allocation
pip install -e ".[dev]"
```

Requires Python 3.10+.

## 2. Create a YAML Profile

A YAML profile defines everything the model needs. Create a file called `my_profile.yaml`:

```yaml
age: 35                      # Current age
retirement_age: 67           # When you plan to retire
investable_wealth: 200000    # Current investable portfolio ($)
after_tax_income: 90000      # Annual after-tax income ($)
risk_tolerance: 5            # 1-10 scale (1=conservative, 10=aggressive)

income_model:
  type: growth               # "flat", "growth", "profile", or "csv"
  g: 0.01                    # 1% annual real income growth

benefit_model:
  type: none                 # "none", "flat", or "schedule"

mortality_model:
  type: none                 # "none", "parametric", or "table"

discount_curve:
  type: constant             # Discount rate for human capital PV
  rate: 0.02                 # 2% real

market:
  mu: 0.05                   # Expected stock return (real)
  r: 0.02                    # Risk-free rate (real)
  sigma: 0.18                # Stock volatility
  real: true
  borrowing_spread: 0.015    # Only used when leverage is enabled
```

Each field is documented in the [Configuration](configuration.md) reference.

## 3. Compute an Allocation via Python

```python
from lifecycle_allocation import (
    InvestorProfile,
    MarketAssumptions,
    recommended_stock_share,
)

profile = InvestorProfile(
    age=35,
    retirement_age=67,
    investable_wealth=200_000,
    after_tax_income=90_000,
    risk_tolerance=5,
)
market = MarketAssumptions(mu=0.05, r=0.02, sigma=0.18)

result = recommended_stock_share(profile, market)
```

The `AllocationResult` contains:

| Field | Description |
|---|---|
| `alpha_recommended` | Final recommended equity allocation (e.g., 0.95 = 95%) |
| `alpha_star` | Baseline risky share before human capital adjustment |
| `human_capital` | Present value of future earnings ($) |
| `alpha_unconstrained` | Raw allocation before clamping to [0, 1] |
| `explain` | Human-readable explanation of the result |
| `components` | Dict of all intermediate values |

```python
print(f"Recommended: {result.alpha_recommended:.1%}")
print(f"Human capital: ${result.human_capital:,.0f}")
print(f"H/W ratio: {result.human_capital / profile.investable_wealth:.1f}x")
print()
print(result.explain)
```

## 4. Run via CLI

The CLI loads a YAML profile and writes results to a directory:

```bash
lifecycle-allocation alloc \
    --profile my_profile.yaml \
    --out ./output \
    --report
```

Output directory contents:

| File | Description |
|---|---|
| `allocation.json` | Machine-readable allocation result and components |
| `summary.md` | Markdown report with explanation and strategy comparison |
| `charts/balance_sheet.png` | Personal balance sheet waterfall chart |
| `charts/strategy_bars.png` | Strategy comparison bar chart |

CLI flags can override YAML values:

```bash
lifecycle-allocation alloc \
    --profile my_profile.yaml \
    --out ./output \
    --mu 0.06 --sigma 0.20 \
    --allow-leverage --max-leverage 1.5 \
    --report --format svg
```

Run `lifecycle-allocation alloc --help` for all options.

## 5. Compare Strategies

Benchmark the lifecycle allocation against common heuristics:

```python
from lifecycle_allocation import compare_strategies

df = compare_strategies(profile, market)
print(df.to_string(index=False))
```

This returns a DataFrame comparing the Choi lifecycle allocation against 60/40, 100-minus-age, and a parametric target-date fund.

## 6. Generate Charts

```python
from lifecycle_allocation.viz.charts import plot_balance_sheet, plot_strategy_bars

# Balance sheet waterfall (W, H, W+H)
fig = plot_balance_sheet(result, profile, save_path="balance_sheet.png")

# Strategy comparison bars
df = compare_strategies(profile, market)
fig = plot_strategy_bars(df, save_path="strategy_bars.png")
```

Both functions return a matplotlib `Figure` and optionally save to disk.

## Next Steps

- [Configuration](configuration.md) -- full reference for all YAML/JSON profile fields
- [Methodology](methodology.md) -- the math behind the model
- [API Reference](api.md) -- complete Python API documentation
- [Examples](examples.md) -- three archetype profiles with interpretation
