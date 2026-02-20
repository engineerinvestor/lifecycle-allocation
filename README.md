# lifecycle-allocation

A Python library implementing a practical lifecycle portfolio choice framework inspired by [Choi et al.](https://www.nber.org/papers/w34166) It combines human capital analysis with visual analytics to produce data-driven stock/bond allocation recommendations.

[![CI](https://github.com/engineerinvestor/lifecycle-allocation/actions/workflows/ci.yml/badge.svg)](https://github.com/engineerinvestor/lifecycle-allocation/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/lifecycle-allocation)](https://pypi.org/project/lifecycle-allocation/)
[![Python](https://img.shields.io/pypi/pyversions/lifecycle-allocation)](https://pypi.org/project/lifecycle-allocation/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://engineerinvestor.github.io/lifecycle-allocation)

## Why This Matters

Most portfolio allocation "rules" are single-variable heuristics: 60/40, 100-minus-age, target-date funds. They ignore the biggest asset most people own, their future earning power. A 30-year-old software engineer with $100k in savings and 35 years of income ahead is in a fundamentally different position than a 30-year-old retiree with the same $100k.

This library takes a **balance-sheet** view of your finances. Your investable portfolio is only part of your total wealth. Future earnings (human capital) act like a bond-like asset, and accounting for them changes how much stock risk you should take. The result is a theoretically grounded, personalized allocation that evolves naturally over your lifecycle, no arbitrary rules required.

## Features

- **Core allocation engine**: Merton-style optimal risky share adjusted for human capital
- **4 income models**: flat, constant-growth, age-profile, and CSV-based
- **Strategy comparison**: benchmark against 60/40, 100-minus-age, and target-date funds
- **Visualization suite**: balance sheet waterfall, glide paths, sensitivity tornado, heatmaps
- **CLI interface**: generate full reports from YAML/JSON profiles
- **YAML/JSON profiles**: declarative investor configuration
- **Leverage support**: two-tier borrowing rate model with configurable constraints
- **Mortality adjustment**: survival probability discounting for human capital

## Install

```bash
pip install lifecycle-allocation
```

For development:

```bash
git clone https://github.com/engineerinvestor/lifecycle-allocation.git
cd lifecycle-allocation
pip install -e ".[dev]"
```

Requires Python 3.10+.

## Quick Start (Python)

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

See the [full quickstart](https://engineerinvestor.github.io/lifecycle-allocation/quickstart/) for a detailed walkthrough covering YAML profiles, CLI usage, and chart generation.

## Quick Start (CLI)

```bash
lifecycle-allocation alloc \
    --profile examples/profiles/young_saver.yaml \
    --out ./output \
    --report
```

This produces `allocation.json`, `summary.md`, and charts in `output/charts/`.

## How It Works

1. Compute a **baseline risky share** (Merton-style): `alpha* = (mu - r) / (gamma * sigma^2)`
2. Estimate **human capital** H as the present value of future earnings + retirement benefits, discounted by survival probability and a term structure
3. Adjust: `alpha = alpha* x (1 + H/W)`, clamped to [0, 1] (or [0, L_max] with leverage)

Young workers with high H/W ratios get higher equity allocations. As you age and accumulate financial wealth, H shrinks relative to W and the allocation naturally declines, producing a lifecycle glide path from first principles rather than arbitrary rules.

## Example Output

| Archetype | Age | Income | Wealth | H/W Ratio | Recommended Equity |
|---|---|---|---|---|---|
| Young saver | 25 | $70k | $25k | ~115x | 100% |
| Mid-career | 45 | $120k | $500k | ~4x | ~96% |
| Near-retirement | 60 | $150k | $1M | ~0.8x | ~24% |

*Values computed from the example YAML profiles with default market assumptions (mu=5%, r=2%, sigma=18%). Results vary with risk tolerance and assumptions.*

## Tutorial

Explore the interactive tutorial notebook for a guided walkthrough:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/engineerinvestor/lifecycle-allocation/blob/main/examples/notebooks/tutorial.ipynb)

Or run locally:

```bash
jupyter notebook examples/notebooks/tutorial.ipynb
```

## Documentation

Full documentation is available at [engineerinvestor.github.io/lifecycle-allocation](https://engineerinvestor.github.io/lifecycle-allocation).

## Roadmap

| Version | Milestone |
|---|---|
| **v0.1** | Core allocation engine, CLI, YAML profiles, strategy comparison, charts |
| **v0.5** | Monte Carlo simulation, CRRA utility evaluation, Social Security modeling |
| **v1.0** | Full documentation, tax-aware optimization, couples modeling |

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style, and PR guidelines.

## Citation

If you use this library in academic work, please cite both the underlying research and the software:

```bibtex
@techreport{choi2025practical,
  title={Practical Finance: An Approximate Solution to Lifecycle Portfolio Choice},
  author={Choi, James J. and Liu, Canyao and Liu, Pengcheng},
  year={2025},
  institution={National Bureau of Economic Research},
  type={Working Paper},
  number={34166},
  doi={10.3386/w34166},
  url={https://www.nber.org/papers/w34166}
}

@software{engineerinvestor2025lifecycle,
  title={lifecycle-allocation: A Lifecycle Portfolio Choice Framework},
  author={{Engineer Investor}},
  year={2025},
  url={https://github.com/engineerinvestor/lifecycle-allocation},
  version={0.1.0},
  license={MIT}
}
```

## Disclaimer

**This library is for education and research purposes only. It is not investment advice.** The authors are not financial advisors. Consult a qualified professional before making investment decisions. Past performance and model outputs do not guarantee future results.

## License

[MIT](LICENSE)
