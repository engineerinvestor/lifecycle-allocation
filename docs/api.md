# API Reference

*Full API documentation is forthcoming. Below is a summary of the main public interface.*

## Core Models

- `InvestorProfile` -- Investor demographics, income, and preferences
- `MarketAssumptions` -- Expected returns, volatility, risk-free rate
- `AllocationResult` -- Output of allocation computation

## Core Functions

- `recommended_stock_share(profile, market, ...)` -- Compute recommended equity allocation
- `human_capital_pv(profile, market, ...)` -- Compute present value of human capital
- `alpha_star(market, gamma, ...)` -- Compute Merton optimal risky share
- `compare_strategies(profile, market, ...)` -- Compare against heuristic strategies

## Visualization

- `plot_balance_sheet(result)` -- Balance sheet waterfall chart
- `plot_glide_path(results)` -- Allocation over time
- `plot_sensitivity(result)` -- Sensitivity tornado chart
- `plot_strategy_comparison(df)` -- Strategy comparison bar chart

## CLI

```bash
lifecycle-allocation alloc --profile <path> --out <dir> [--report]
```

See `lifecycle-allocation alloc --help` for all options.
