# Risky Human Capital

The standard lifecycle model treats human capital as a bond-like asset: stable, predictable cash flows that provide portfolio diversification. This assumption works well for government employees, tenured academics, and others with highly stable income. But it fails for workers whose compensation is significantly tied to equity markets.

## Motivation

Consider a 30-year-old software engineer at a large tech company:

- Base salary: $180,000/year
- RSU grants: $120,000/year (vesting over 4 years)
- Total compensation: $300,000/year

Over 60% of this engineer's compensation is in restricted stock units (RSUs) that move with the stock market. If tech stocks drop 40%, their unvested RSUs lose 40% of their value, and layoff risk increases. Their human capital is not bond-like; it is partly equity-like.

The standard model would recommend maximum equity for this worker because of their high H/W ratio. But that ignores the fact that their career is already a large, concentrated equity bet.

## The Beta-Adjusted Formula

We introduce a single parameter, **human capital beta** (`beta_H`), that captures the fraction of human capital behaving like equity:

```
H_bond = (1 - beta_H) x H      (bond-like, provides diversification)
H_equity = beta_H x H           (equity-like, does not diversify)
```

The modified allocation formula:

```
alpha = alpha* x (1 + (1 - beta_H) x H / W)
```

### Key Properties

- **beta_H = 0** (default): Recovers the standard model. All human capital is bond-like.
- **beta_H = 1**: Allocation reduces to `alpha*`. Human capital provides no diversification.
- **Monotonicity**: Higher beta always produces a lower or equal equity allocation.

## Industry Beta Calibration

Betas are calibrated from labor economics literature (Davis & Willen, 2000; Benzoni et al., 2007) and compensation structure analysis:

| Industry | Beta | Rationale |
|---|---|---|
| Government | 0.00 | Extremely stable employment and compensation |
| Education (tenured) | 0.00 | Tenure provides near-complete income security |
| Healthcare | 0.10 | Relatively recession-resistant demand |
| Utilities | 0.10 | Regulated, stable revenues |
| Consumer staples | 0.15 | Non-cyclical demand |
| Education (non-tenured) | 0.20 | Some job insecurity, but low market correlation |
| Manufacturing | 0.25 | Moderate cyclicality |
| Professional services | 0.30 | Some business cycle sensitivity |
| General private sector | 0.30 | Baseline for typical private employment |
| Media/entertainment | 0.35 | Advertising-driven revenue is cyclical |
| Real estate | 0.40 | Correlated with interest rates and economy |
| Tech (salaried) | 0.40 | Layoff cycles, but cash-heavy compensation |
| Construction | 0.45 | Highly cyclical |
| Finance/banking | 0.45 | Bonuses tied to market performance |
| Oil & gas | 0.50 | Commodity price exposure |
| Finance (trading) | 0.55 | Compensation directly tied to market performance |
| Tech with RSUs | 0.60 | 40-60% of comp in employer stock |
| Commission sales | 0.70 | Revenue-dependent compensation |
| Tech startup | 0.75 | Equity-heavy comp, high failure rate |
| Startup (equity-heavy) | 0.85 | Compensation is almost entirely equity |

## Embedded Options Perspective

Human capital contains embedded financial options that affect its risk profile:

- **RSU vesting**: Equivalent to call options on employer stock. Value increases with stock price, worthless if company fails.
- **Layoff risk**: Equivalent to a short put on employment. Losses are triggered by economic downturns (procyclical risk).
- **Career mobility**: A real option to switch industries or employers. Increases with skills breadth, decreases with specialization.
- **Non-competes / golden handcuffs**: Reduce optionality, making human capital more concentrated and risky.

## Concentration Risk: What Beta Does Not Capture

The beta parameter captures the *systematic* correlation between your income and the broad stock market. It does not account for the additional risks of holding a concentrated position in a single company's stock. If a significant portion of your compensation is in employer RSUs or startup equity, several risks go beyond what beta reflects:

### Single-stock volatility vs. market volatility

The `sigma` used in the Merton ratio is broad market volatility, typically around 18%. Individual stocks have much higher volatility, often 40-60%+. Beta maps your income to market-correlated risk, but the remaining firm-specific volatility (which can be enormous for a single stock) is not captured in the allocation formula.

### Skewness and left-tail risk

A diversified stock market cannot go to zero; a single company can. The CRRA/Merton framework assumes log-normal returns, which understates the catastrophic downside of concentrated positions. For someone whose human capital is tied to one stock, the distribution of total-wealth outcomes is highly skewed, with severe downside scenarios that a normal distribution underestimates.

### Uncompensated risk

Diversified market exposure earns the equity risk premium. Single-stock exposure carries idiosyncratic risk that is *not compensated* by higher expected returns in equilibrium. The beta framework treats the equity-like portion of human capital as if it earned the market premium, but concentrated positions bear extra risk without extra reward.

### The "double whammy"

In downturns, the correlation between your employer's stock price, layoff probability, and RSU forfeiture all spike simultaneously. A single scalar beta captures average correlation but misses this regime-dependent, asymmetric tail dependence. The practical consequence is that the worst outcomes (stock crashes, layoffs, and forfeiture) tend to cluster together.

### Practical guidance

- **Treat the model's allocation as a floor.** If you hold concentrated equity, the appropriate reduction in your portfolio's stock allocation is likely *larger* than what beta alone suggests.
- **Diversify vested RSUs.** As shares vest, consider selling and reinvesting in a diversified portfolio. A 10b5-1 trading plan can automate this on a pre-set schedule.
- **Evaluate combined risk.** Look at your unvested RSUs, vested but unsold employer stock, and your investment portfolio as a single balance sheet. The total equity exposure may be much higher than your brokerage account alone suggests.
- **Do not change the formula.** The right tool for concentration risk is diversification advice, not a different allocation model. Adding a concentration penalty or skew adjustment would undermine the parsimony that makes the framework useful.

## Worked Example

### Standard Model (beta = 0)

A 30-year-old tech worker with $150k income and $100k wealth:

- H ≈ $4,000,000 (PV of future earnings)
- H/W = 40x
- alpha* = 46.3% (risk tolerance 5)
- Unconstrained allocation: 46.3% x (1 + 40) = ~1,900%
- Clamped: **100%**

### Beta-Adjusted (beta = 0.6)

Same worker, acknowledging 60% equity-like human capital:

- H_bond = 0.4 x $4,000,000 = $1,600,000
- H_equity = 0.6 x $4,000,000 = $2,400,000
- Unconstrained: 46.3% x (1 + 16) = ~787%
- Clamped: **100%**

For investors with lower H/W ratios (mid-career, higher wealth), the difference becomes more pronounced. A mid-career tech worker with H/W = 4x would see their allocation drop from ~96% to ~72% when accounting for beta = 0.6.

## Python Usage

```python
from lifecycle_allocation import (
    HumanCapitalSpec,
    InvestorProfile,
    MarketAssumptions,
    recommended_stock_share,
    suggested_beta,
)

# Using explicit beta
profile = InvestorProfile(
    age=30, retirement_age=67,
    investable_wealth=150_000,
    after_tax_income=120_000,
    risk_tolerance=6,
    human_capital_model=HumanCapitalSpec(beta=0.6),
)

# Or using industry lookup
beta = suggested_beta("tech_with_rsus")  # returns 0.6
profile = InvestorProfile(
    age=30, retirement_age=67,
    investable_wealth=150_000,
    after_tax_income=120_000,
    risk_tolerance=6,
    human_capital_model=HumanCapitalSpec(beta=beta, industry="tech_with_rsus"),
)

market = MarketAssumptions(mu=0.05, r=0.02, sigma=0.18)
result = recommended_stock_share(profile, market)
print(result.components["human_capital_beta"])        # 0.6
print(result.components["human_capital_bond_like"])    # bond-like portion
print(result.components["human_capital_equity_like"])  # equity-like portion
```

## YAML Configuration

```yaml
human_capital_model:
  industry: tech_with_rsus   # resolves to beta=0.60
```

Or with an explicit beta:

```yaml
human_capital_model:
  beta: 0.55
```

## Further Reading

- [Full academic paper (PDF)](https://github.com/engineerinvestor/lifecycle-allocation/blob/main/papers/risky_human_capital.pdf)
- [One-page explainer (PDF)](https://github.com/engineerinvestor/lifecycle-allocation/blob/main/papers/risky_human_capital_explainer.pdf)
- [Tutorial notebook](https://colab.research.google.com/github/engineerinvestor/lifecycle-allocation/blob/main/examples/notebooks/risky_human_capital.ipynb)
