# Quick Start

## Installation

```bash
pip install lifecycle-allocation
```

For development:

```bash
git clone https://github.com/engineerinvestor/lifecycle-allocation.git
cd lifecycle-allocation
pip install -e ".[dev]"
```

## Python API

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
```

## CLI

```bash
lifecycle-allocation alloc \
    --profile examples/profiles/young_saver.yaml \
    --out ./output \
    --report
```

This produces `allocation.json`, `summary.md`, and charts in `output/charts/`.

## YAML Profiles

Define investor profiles as YAML files:

```yaml
age: 30
retirement_age: 67
investable_wealth: 100000
after_tax_income: 70000
risk_tolerance: 5
```

See `examples/profiles/` for more examples.
