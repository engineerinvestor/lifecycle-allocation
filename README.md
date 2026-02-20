# lifecycle-allocation

A Python library implementing a practical lifecycle portfolio choice framework inspired by [Choi et al.](https://www.nber.org/papers/w34166) It combines human capital analysis with visual analytics to produce data-driven stock/bond allocation recommendations.

Most allocation "rules" are single-variable heuristics (60/40, 100-minus-age, target-date funds). This library takes a **balance-sheet** view: your investable portfolio is only part of your total wealth. Your future earning power (human capital) acts like a bond, and accounting for it changes how much stock risk you should take.

**Disclaimer:** This library is for education and research. It is not investment advice.

## Install

```bash
pip install -e ".[dev]"
```

Requires Python 3.10+.

## Quickstart (Python)

```python
from lifecycle_allocation import (
    InvestorProfile,
    MarketAssumptions,
    recommended_stock_share,
    compare_strategies,
)

profile = InvestorProfile(
    age=30,
    retirement_age=67,
    investable_wealth=100_000,
    after_tax_income=70_000,
    risk_tolerance=5,
)
market = MarketAssumptions(mu=0.05, r=0.02, sigma=0.18)

result = recommended_stock_share(profile, market)
print(f"Recommended stock allocation: {result.alpha_recommended:.1%}")
print(f"Human capital: ${result.human_capital:,.0f}")
print(result.explain)

# Compare against heuristic strategies
df = compare_strategies(profile, market)
print(df.to_string(index=False))
```

## Quickstart (CLI)

```bash
lifecycle-allocation alloc \
    --profile examples/profiles/young_saver.yaml \
    --out ./output \
    --report
```

This produces `allocation.json`, `summary.md`, and charts in `output/charts/`.

## How It Works

1. Compute a **baseline risky share** (Merton-style): `alpha* = (mu - r) / (gamma * sigma^2)`
2. Estimate **human capital** H as the present value of future earnings + retirement benefits
3. Adjust: `alpha = alpha* x (1 + H/W)`, clamped to [0, 1] (or [0, L_max] with leverage)

Young workers with high H/W ratios get higher equity allocations. As you age and accumulate financial wealth, H shrinks relative to W and the allocation naturally declines.

## License

MIT
